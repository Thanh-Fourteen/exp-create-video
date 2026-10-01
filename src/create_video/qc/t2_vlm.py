"""QC tầng 2 — chất lượng hình ảnh, bằng VLM (Qwen3-VL-2B-Instruct).

Khác T1: đây là tầng **đề xuất**, chấm TỪNG SHOT chứ không chấm cả video — patch
sửa trỏ đúng `shot_id` để `visual/` chỉ render lại đúng chỗ đó, không render lại
cả video (nguyên tắc P4, "QUYỀN CỦA TỪNG TẦNG"). Chỉ các mã lỗi liệt trong
`t2_visual.block_on` (`configs/thresholds.yaml`) mới làm một shot "fail"; các mã
còn lại chỉ ghi vết. Producer/Critic tách hẳn: prompt bên dưới là *"tìm cái sai"*,
không phải *"sinh ảnh khác"* — sinh ảnh lại là việc của `visual/`.

⚠️ Nạp model SAU khi khối visual (SDXL) đã `close()` — 6GB không cho hai model
cùng lúc. Dùng như context manager, cùng hợp đồng với `visual.base.ImageBackend`.

    python -m create_video.qc.t2_vlm out/<id>/video-spec.json
"""

from __future__ import annotations

import gc
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Sequence

import yaml

# Cùng cache với khối visual (exp/hf-cache) — xem lý do ở visual/sdxl.py.
import os as _os

_os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parents[3] / "exp" / "hf-cache"))

REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"

# Ảnh shot là 1080×1920 (2 megapixel). Đo thật 2026-08-21: đưa thẳng độ phân
# giải đó vào vision encoder tốn ~4GB attention cho MỘT ảnh — vượt cả phần
# VRAM còn lại sau khi nạp model 4-bit. Cần chi tiết mức pixel để chấm giải
# phẫu/chữ méo, không cần độ nét gốc; hạ cạnh dài xuống mốc này trước khi đưa
# vào processor cắt VRAM encoder xuống còn vài trăm MiB.
MAX_SIDE_PX = 768

# Bốn tiêu chí chính thức của T2 (todos.md P4.S1). `harsh_cut` chỉ chấm được khi
# có ảnh shot trước để so; shot đầu tiên của video bỏ qua tiêu chí này.
PROMPT_TMPL = """Bạn là critic chấm ẢNH cho một video TikTok tiếng Việt về AI.
Chủ đề video: {topic}
Câu thoại đọc khi ảnh NÀY (ảnh {img_label}) hiện trên màn hình: "{caption}"

Chấm các tiêu chí sau, CHỈ báo lỗi khi thấy rõ ràng — không đoán, không chê lấy
lệ. Ngưỡng pass là 6/10, phần lớn ảnh sinh bình thường phải qua được:

1. anatomy_error — lỗi giải phẫu: tay sai số ngón, mặt méo, tỉ lệ cơ thể sai
2. garbled_text_in_image — chữ trong ảnh bị bóp thành ký tự vô nghĩa (bỏ qua
   nếu ảnh vốn không có chữ)
3. topic_mismatch — ảnh KHÔNG minh hoạ được câu thoại ở trên, lạc chủ đề hẳn
   (không tính khác biệt nhỏ về góc máy/bối cảnh)
4. low_contrast — ảnh quá tối hoặc bệt màu, khó nhìn trên màn hình điện thoại
{harsh_cut_criterion}
Bạn là critic TÌM CÁI SAI, không phải người vẽ lại ảnh. Trả về DUY NHẤT một khối
JSON, không lời dẫn:

{{"score": 0-10, "issues": ["mã lỗi mắc phải ở trên, có thể là mảng rỗng"],
  "detail": "một câu giải thích ngắn bằng tiếng Việt",
  "suggested_prompt_fix": "gợi ý sửa prompt sinh ảnh nếu có lỗi, hoặc null"}}"""

HARSH_CUT_CRITERION = """5. harsh_cut — so với ẢNH TRƯỚC (ảnh thứ nhất): hai ảnh gần như giống hệt nhau
   (cùng góc máy, cùng bố cục) khiến chuyển cảnh trông như giật/lỗi, thay vì một
   cú cắt cảnh có chủ ý
"""


def _thresholds() -> dict:
    with open(REPO_ROOT / "configs" / "thresholds.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["t2_visual"]


@dataclass
class ShotVerdict:
    shot_id: str
    ok: bool
    score: int
    issues: list[str] = field(default_factory=list)
    detail: str = ""
    suggested_prompt_fix: str | None = None

    def __str__(self) -> str:
        mark = "✓" if self.ok else "✗"
        issues = f" [{', '.join(self.issues)}]" if self.issues else ""
        return f"{mark} {self.shot_id}: {self.score}/10{issues} — {self.detail}"


def _captions_for_shot(shot: dict, captions: Sequence[dict]) -> str:
    """Câu thoại rơi vào khoảng thời gian của shot — VLM cần biết ảnh PHẢI minh
    hoạ ý gì, không chỉ chấm ảnh "đẹp/xấu" chung chung."""
    lo, hi = shot["start_sec"], shot["end_sec"]
    mid = [c["text"] for c in captions if lo <= (c["start_sec"] + c["end_sec"]) / 2 < hi]
    return " ".join(mid) if mid else "(không có câu thoại ở shot này)"


def _load_downscaled(path: Path, max_side: int = MAX_SIDE_PX):
    from PIL import Image

    img = Image.open(path).convert("RGB")
    scale = max_side / max(img.size)
    if scale < 1.0:
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    return img


def _extract_json(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    raw = fenced.group(1) if fenced else None
    if raw is None:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError(f"VLM không trả JSON:\n{text[:400]}")
        raw = text[start : end + 1]
    return json.loads(raw)


class Qwen3VL:
    """Wrap Qwen3-VL-2B-Instruct. `close()` nhả VRAM — bắt buộc trước khi
    khối visual nạp lại ở video kế tiếp."""

    name = "qwen3_vl"

    def __init__(self, model_id: str = MODEL_ID) -> None:
        self.model_id = model_id
        self._model = None
        self._processor = None
        self.peak_vram_mib: float = 0.0

    def _load(self):
        if self._model is not None:
            return
        import torch
        from transformers import (
            BitsAndBytesConfig,
            Qwen3VLForConditionalGeneration,
            Qwen3VLProcessor,
        )

        self._processor = Qwen3VLProcessor.from_pretrained(self.model_id)
        # 4-bit (nf4), không bf16 đủ. Đo thật 2026-08-21: bf16 cần nạp một khối
        # ~4,0GB liên tục (`caching_allocator_warmup`) và OOM ngay khi có tiến
        # trình khác giữ GPU — mà đó là trạng thái BÌNH THƯỜNG của máy `tony`,
        # không phải ca hiếm (xem research/probes/p4s1-vlm.md). 4-bit hạ trọng
        # số xuống ~1,3GB, để lại khoảng đệm cho tiến trình khác thay vì chỉ
        # vừa khít trần 6GB.
        quant = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4"
        )
        self._model = Qwen3VLForConditionalGeneration.from_pretrained(
            self.model_id, quantization_config=quant, device_map="cuda"
        )
        self._model.eval()

    def judge_shot(
        self,
        image_path: Path,
        *,
        topic: str,
        caption: str,
        prev_image_path: Path | None = None,
    ) -> ShotVerdict:
        import torch

        self._load()
        torch.cuda.reset_peak_memory_stats()

        content: list[dict] = []
        img_label = "thứ hai" if prev_image_path is not None else "duy nhất"
        if prev_image_path is not None:
            content.append({"type": "image", "image": _load_downscaled(prev_image_path)})
        content.append({"type": "image", "image": _load_downscaled(image_path)})
        prompt = PROMPT_TMPL.format(
            topic=topic,
            caption=caption,
            img_label=img_label,
            harsh_cut_criterion=HARSH_CUT_CRITERION if prev_image_path is not None else "",
        )
        content.append({"type": "text", "text": prompt})
        messages = [{"role": "user", "content": content}]

        inputs = self._processor.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True,
            return_dict=True, return_tensors="pt",
        ).to(self._model.device)

        with torch.no_grad():
            out = self._model.generate(**inputs, max_new_tokens=300, do_sample=False)
        text = self._processor.batch_decode(
            out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )[0]
        self.peak_vram_mib = max(self.peak_vram_mib, torch.cuda.max_memory_allocated() / 1024**2)

        data = _extract_json(text)
        thr = _thresholds()
        issues = [str(i) for i in data.get("issues", [])]
        ok = int(data.get("score", 0)) >= thr["min_shot_score"] and not any(
            i in thr["block_on"] for i in issues
        )
        return ShotVerdict(
            shot_id="", ok=ok, score=int(data.get("score", 0)), issues=issues,
            detail=str(data.get("detail", "")),
            suggested_prompt_fix=data.get("suggested_prompt_fix"),
        )

    def close(self) -> None:
        if self._model is None:
            return
        import torch

        del self._model, self._processor
        self._model = None
        self._processor = None
        gc.collect()
        torch.cuda.empty_cache()

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def run(spec_path: Path) -> list[ShotVerdict]:
    """Chấm mọi shot có ảnh thật trong một `video-spec.json` (bỏ qua kind=color:
    nền phẳng không có gì để VLM chấm)."""
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    root = Path(spec_path).resolve().parent
    topic = spec["meta"]["topic"]
    captions = spec["captions"]

    verdicts: list[ShotVerdict] = []
    prev_path: Path | None = None
    with Qwen3VL() as vlm:
        for shot in spec["shots"]:
            if shot["asset"]["kind"] != "image":
                prev_path = None
                continue
            img_path = root / shot["asset"]["path"]
            v = vlm.judge_shot(
                img_path, topic=topic,
                caption=_captions_for_shot(shot, captions),
                prev_image_path=prev_path,
            )
            v.shot_id = shot["id"]
            verdicts.append(v)
            prev_path = img_path
    return verdicts


def summarize(verdicts: Sequence[ShotVerdict]) -> dict:
    thr = _thresholds()
    failing = [v for v in verdicts if not v.ok]
    pct = round(100 * len(failing) / len(verdicts), 1) if verdicts else 0.0
    return {
        "tier": "t2",
        "shots": [asdict(v) for v in verdicts],
        "failing_shot_ids": [v.shot_id for v in failing],
        "failing_pct": pct,
        # Đề xuất, không chặn: quá 1/4 shot hỏng thì đáng render lại cả loạt
        # thay vì vá từng ảnh; dưới ngưỡng đó thì patch đúng shot lỗi.
        "suggest_rerender_all": pct > thr["max_failing_shots_pct"],
    }


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("dùng: python -m create_video.qc.t2_vlm <video-spec.json>", file=sys.stderr)
        return 2
    verdicts = run(Path(argv[0]))
    for v in verdicts:
        print(v)
    summary = summarize(verdicts)
    print(
        f"\n{len(verdicts) - len(summary['failing_shot_ids'])}/{len(verdicts)} shot pass · "
        f"{summary['failing_pct']}% hỏng"
        + (" · ĐỀ XUẤT render lại cả loạt" if summary["suggest_rerender_all"] else "")
    )
    return 1 if summary["failing_shot_ids"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
