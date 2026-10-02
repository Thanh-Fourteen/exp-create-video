"""QC tầng 2 — ảnh SDXL từng shot, bằng VLM (Qwen3-VL-2B-Instruct) + một kiểm bằng code.

    python -m create_video.qc.t2_vlm out/<id>/video-spec.json

Tầng **đề xuất**: chấm TỪNG SHOT ảnh, patch trỏ đúng `shot_id` để `visual/regen.py` chỉ
sinh lại đúng ảnh đó. Chỉ mã lỗi trong `t2_visual.block_on` (`configs/thresholds.yaml`)
làm shot "fail"; mã `warn_only` chỉ ghi vết.

Cách chấm — viết lại 2026-10-02 (`research/probes/p4-s1-research.md`). Bản 2026-08-21 xin
VLM sinh JSON điểm 0–10: đúng kiểu "chấm điểm" yếu nhất theo MLLM-as-a-Judge, và là
cửa cho "chê lấy lệ". Giờ mỗi lỗi là MỘT câu hỏi Có/Không, đọc P(Yes) từ logits ở một
bước (VQAScore, arXiv 2404.01291) — tất định, không sinh văn tự do để rồi bóc JSON:

- `topic_mismatch`: P(Yes) "Does this image show: {alt}?" — `alt` là prompt tiếng Anh đã
  sinh ra ảnh. `score = round(10·P)`, fail khi < `min_shot_score`.
- `garbled_text_in_image`: P(Yes) "có chữ trong ảnh không" ≥ 0,5. Chữ trên hình là việc
  của Remotion; SDXL sinh chữ nào cũng là chữ méo.
- `anatomy_error`: P(Yes) "tay/mặt dị dạng" ≥ 0,5. Bằng chứng nói VLM nhỏ gần như mù ở
  việc này (ArtifactLens F1 0,017) — giữ vì ngưỡng có trước, đo xem nó nói gì.
- `harsh_cut`: **code**, dHash giữa hai ảnh liền kề — không cần model để biết hai ảnh giống nhau.

⚠️ Nạp SAU khi SDXL đã `close()` — 6GB không cho hai model. Context manager như visual.
"""

from __future__ import annotations

import gc
import json
import os as _os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Sequence

import yaml

_os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parents[3] / "exp" / "hf-cache"))

REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"

# Đo 2026-08-21: ảnh 1080×1920 đưa thẳng vào vision encoder tốn ~4GB attention.
MAX_SIDE_PX = 768

# Ngưỡng viết trước khi chạy (p4-s1-research.md §3, 2026-10-02). min_shot_score nằm ở
# thresholds.yaml từ 2026-08-04; mấy ngưỡng P(Yes) dưới đây là mốc trung tính 0,5.
P_TEXT = 0.5
P_ANATOMY = 0.5
DHASH_NEAR_DUP = 8   # Hamming / 64 bit

Q_TOPIC = "Does this image show: {alt}? Answer Yes or No."
Q_TEXT = "Is there any text, letters or writing visible in this image? Answer Yes or No."
Q_ANATOMY = ("Are there deformed hands, extra fingers or distorted human faces in this image? "
             "Answer Yes or No.")
Q_LINE = 'Does this image illustrate the sentence: "{line}"? Answer Yes or No.'
Q_DESCRIBE = "Describe this image in one short sentence."

FIX_TEXT = "no text, no letters, no writing, blank screens"
FIX_ANATOMY = "no people, no hands, no faces"


def _thresholds() -> dict:
    with open(REPO_ROOT / "configs" / "thresholds.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["t2_visual"]


@dataclass
class ShotVerdict:
    shot_id: str
    ok: bool
    score: int
    issues: list[str] = field(default_factory=list)
    p: dict = field(default_factory=dict)          # P(Yes) từng câu hỏi — số thô để chấm lại sau
    detail: str = ""                               # VLM tả ảnh một câu — cho Tony đọc vết
    suggested_prompt_fix: str | None = None

    def __str__(self) -> str:
        mark = "✓" if self.ok else "✗"
        issues = f" [{', '.join(self.issues)}]" if self.issues else ""
        ps = " ".join(f"{k}={v:.2f}" for k, v in self.p.items())
        return f"{mark} {self.shot_id}: {self.score}/10{issues} · {ps} — {self.detail}"


def _captions_for_shot(shot: dict, captions: Sequence[dict]) -> str:
    lo, hi = shot["start_sec"], shot["end_sec"]
    mid = [c["text"] for c in captions if lo <= (c["start_sec"] + c["end_sec"]) / 2 < hi]
    return " ".join(mid)


def _load_downscaled(path: Path, max_side: int = MAX_SIDE_PX):
    from PIL import Image

    img = Image.open(path).convert("RGB")
    scale = max_side / max(img.size)
    if scale < 1.0:
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    return img


def dhash(path: Path, size: int = 8) -> int:
    """Difference hash 64 bit — hai ảnh gần trùng thì Hamming nhỏ. Không cần model."""
    from PIL import Image

    g = Image.open(path).convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for r in range(size):
        for c in range(size):
            bits = (bits << 1) | (px[r * (size + 1) + c] > px[r * (size + 1) + c + 1])
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def decide(p: dict, near_dup: bool, thr: dict) -> tuple[bool, int, list[str], str | None]:
    """P(Yes) → (pass, score, issues, prompt fix). Thuần — test được không cần GPU."""
    score = round(10 * p["topic"])
    issues: list[str] = []
    if score < thr["min_shot_score"]:
        issues.append("topic_mismatch")
    if p["text"] >= P_TEXT:
        issues.append("garbled_text_in_image")
    if p["anatomy"] >= P_ANATOMY:
        issues.append("anatomy_error")
    if near_dup:
        issues.append("harsh_cut")
    ok = not any(i in thr["block_on"] for i in issues)
    fixes = []
    if "garbled_text_in_image" in issues:
        fixes.append(FIX_TEXT)
    if "anatomy_error" in issues:
        fixes.append(FIX_ANATOMY)
    fix = ", ".join(fixes) if fixes else None
    return ok, score, issues, fix


class Qwen3VL:
    """Qwen3-VL-2B nf4. `close()` nhả VRAM — bắt buộc trước khi SDXL nạp lại."""

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
        from transformers import BitsAndBytesConfig, Qwen3VLForConditionalGeneration, Qwen3VLProcessor

        self._processor = Qwen3VLProcessor.from_pretrained(self.model_id)
        # nf4: bf16 đủ cần một khối ~4GB liên tục và OOM khi tiến trình khác giữ GPU
        # (đo 2026-08-21). Compute **fp16**: Turing (2060) không có bf16 — bản cũ để
        # bfloat16, chạy được nhờ giả lập nhưng sai ràng buộc fp16 của dự án.
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                                   bnb_4bit_quant_type="nf4")
        self._model = Qwen3VLForConditionalGeneration.from_pretrained(
            self.model_id, quantization_config=quant, device_map="cuda",
            dtype=torch.float16, attn_implementation="sdpa",   # Turing không có FA2
        )
        self._model.eval()
        tok = self._processor.tokenizer
        self._yes = tok.encode("Yes", add_special_tokens=False)[0]
        self._no = tok.encode("No", add_special_tokens=False)[0]

    def _inputs(self, image, text: str):
        msgs = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": text}]}]
        return self._processor.apply_chat_template(
            msgs, tokenize=True, add_generation_prompt=True, return_dict=True, return_tensors="pt",
        ).to(self._model.device)

    def p_yes(self, image, question: str) -> float:
        """P(Yes) chuẩn hoá trên {Yes, No} ở token đầu của câu trả lời."""
        import torch

        with torch.no_grad():
            logits = self._model(**self._inputs(image, question)).logits[0, -1].float()
        if not torch.isfinite(logits).all():
            # fp16 tràn trên Turing có báo cáo với Qwen2.5-VL (R) — báo to, không đoán.
            raise RuntimeError("logits có NaN/inf — fp16 tràn; xem p4-s1-research.md §1")
        two = torch.stack([logits[self._yes], logits[self._no]])
        return float(torch.softmax(two, 0)[0])

    def describe(self, image) -> str:
        import torch

        inp = self._inputs(image, Q_DESCRIBE)
        with torch.no_grad():
            out = self._model.generate(**inp, max_new_tokens=40, do_sample=False)
        return self._processor.batch_decode(out[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0].strip()

    def judge_shot(self, image_path: Path, *, alt: str, line: str = "", near_dup: bool = False,
                   describe: bool = True) -> ShotVerdict:
        import torch

        self._load()
        img = _load_downscaled(image_path)
        p = {
            "topic": self.p_yes(img, Q_TOPIC.format(alt=alt.strip().rstrip("."))),
            "text": self.p_yes(img, Q_TEXT),
            "anatomy": self.p_yes(img, Q_ANATOMY),
        }
        if line:
            p["line"] = self.p_yes(img, Q_LINE.format(line=line))   # chỉ ghi vết
        ok, score, issues, fix = decide(p, near_dup, _thresholds())
        detail = self.describe(img) if describe else ""
        self.peak_vram_mib = max(self.peak_vram_mib, torch.cuda.max_memory_allocated() / 1024**2)
        return ShotVerdict(shot_id="", ok=ok, score=score, issues=issues,
                           p={k: round(v, 3) for k, v in p.items()}, detail=detail,
                           suggested_prompt_fix=f"{alt.strip().rstrip('.')}, {fix}" if fix else None)

    def close(self) -> None:
        if self._model is None:
            return
        import torch

        del self._model, self._processor
        self._model = None
        self._processor = None
        gc.collect()
        # Đo 2026-10-02: sau khi chấm ảnh, close() cũ còn GIỮ 1.466 MiB "reserved" dù chỉ
        # 8 MiB tensor sống — workspace cuBLAS (tạo lúc generate) ghim các khối của
        # caching allocator, empty_cache() không trả được. SDXL nạp sau sẽ thiếu đúng chừng đó.
        torch._C._cuda_clearCublasWorkspaces()
        torch.cuda.empty_cache()

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def run(spec_path: Path, vlm: Qwen3VL | None = None) -> list[ShotVerdict]:
    """Chấm mọi shot `kind=image` của một spec. Shot thiếu `alt` (spec trước P4.S1) dùng
    câu thoại làm mô tả — kém hơn, ghi rõ trong detail."""
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    root = Path(spec_path).resolve().parent
    captions = spec["captions"]

    verdicts: list[ShotVerdict] = []
    prev_hash: int | None = None
    own = vlm is None
    vlm = vlm or Qwen3VL()
    try:
        for shot in spec["shots"]:
            if shot["asset"]["kind"] != "image":
                prev_hash = None   # shot bằng chứng chen giữa = có cắt cảnh thật
                continue
            img_path = root / shot["asset"]["path"]
            h = dhash(img_path)
            near = prev_hash is not None and hamming(h, prev_hash) <= DHASH_NEAR_DUP
            line = _captions_for_shot(shot, captions)
            alt = shot["asset"].get("alt") or line
            v = vlm.judge_shot(img_path, alt=alt, line=line, near_dup=near)
            if not shot["asset"].get("alt"):
                v.detail = "(spec thiếu alt — chấm theo câu thoại) " + v.detail
            v.shot_id = shot["id"]
            verdicts.append(v)
            prev_hash = h
    finally:
        if own:
            vlm.close()
    return verdicts


def summarize(verdicts: Sequence[ShotVerdict], peak_vram_mib: float = 0.0) -> dict:
    thr = _thresholds()
    failing = [v for v in verdicts if not v.ok]
    pct = round(100 * len(failing) / len(verdicts), 1) if verdicts else 0.0
    return {
        "tier": "t2",
        "model": MODEL_ID,
        "shots": [{"shot_id": v.shot_id, "pass": v.ok, "score": v.score, "issues": v.issues,
                   "p": v.p, "detail": v.detail, "suggested_prompt_fix": v.suggested_prompt_fix}
                  for v in verdicts],
        "failing_shot_ids": [v.shot_id for v in failing],
        "failing_pct": pct,
        # Đề xuất, không chặn: quá 1/4 shot hỏng thì render lại cả loạt.
        "suggest_rerender_all": pct > thr["max_failing_shots_pct"],
        "peak_vram_mib": round(peak_vram_mib),
    }


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("dùng: python -m create_video.qc.t2_vlm <video-spec.json>", file=sys.stderr)
        return 2
    spec_path = Path(argv[0])
    with Qwen3VL() as vlm:
        verdicts = run(spec_path, vlm)
        summary = summarize(verdicts, vlm.peak_vram_mib)
    for v in verdicts:
        print(v)
    out = spec_path.resolve().parent / "qc" / "t2.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(verdicts) - len(summary['failing_shot_ids'])}/{len(verdicts)} shot pass · "
          f"{summary['failing_pct']}% hỏng · VRAM đỉnh {summary['peak_vram_mib']} MiB → {out}")
    return 1 if summary["failing_shot_ids"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
