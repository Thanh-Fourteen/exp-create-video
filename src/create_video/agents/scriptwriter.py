"""Agent viết kịch bản: chủ đề → `script.json`.

Dùng `claude-agent-sdk` (`query()`), **không** phải `client.beta.messages.tool_runner`
của SDK `anthropic` — hai package khác nhau và rất hay bị lẫn. Chạy bằng auth sẵn
có của Claude Code nên chi phí LLM là 0đ, đúng ràng buộc của dự án.

Ba điều đóng khung prompt ở đây, cả ba đều có lý do đo được:

1. **Nhét nguyên `configs/rubric.md` vào prompt hệ thống.** Producer biết trước
   critic T3 sẽ chấm bằng gì thì viết đúng ngay từ vòng đầu — đây là cách rẻ nhất
   để kéo `qc_rounds` xuống dưới 1,5.
2. **Cấm số và ký hiệu trong lời đọc.** exp-echo chuẩn hoá trước khi đọc: "15%" →
   "mười lăm phần trăm", "2060" → "hai nghìn không trăm sáu mươi". Khi đó số token
   đọc lệch số token hiển thị và phụ đề karaoke phải chia lại thời gian thay vì
   dùng số đo (`spec/captions.py`). Viết sẵn bằng chữ thì giữ được đường "exact".
3. **Prompt ảnh viết bằng tiếng Anh.** SDXL hiểu tiếng Anh tốt hơn hẳn, và
   `visual/sdxl.py` đã nối sẵn đuôi phong cách + negative prompt.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..team import State

REPO_ROOT = Path(__file__).resolve().parents[3]

# Lời đọc: mỗi câu là MỘT caption trên màn hình. Dài quá thì chữ tràn xuống vùng
# UI TikTok che (T1 kiểm chỗ này), ngắn quá thì phụ đề nhấp nháy.
# 2026-08-14 sáng: hạ trần 16 -> 12 từ cho nhịp nhanh hơn.
# 2026-08-14 chiều: TRẢ VỀ 5-16. Đây là thay đổi có ảnh hưởng lớn nhất tới việc
# giọng đọc nghe có tự nhiên không, và lúc đầu tôi không lường: mỗi câu là MỘT
# lần gọi TTS riêng rồi ghép lại kèm 0,28s lặng. Câu càng ngắn thì càng nhiều
# mối ghép, và mỗi mối ghép là một chỗ ngắt hơi không giống người nói. Tony nghe
# demo-02 và nhận ra ngay: "không tự nhiên như người nói".
# 2026-10-05 (research/19): 5–16 → 2–26. Giới hạn cũ có từ thời đọc TỪNG câu rồi ghép (câu ngắn = nhiều mối ghép); giờ
# đọc cả đoạn một lần (`paragraph`) nên lý do đó hết, còn trần 16 ép mọi câu dài như nhau → nghe như đọc gạch đầu dòng.
MIN_WORDS, MAX_WORDS = 2, 26

# Phase V3 (2026-10-02): 20 khuôn hook ở research/11 §4.2 gom thành nhãn để sau 20 video
# đếm được loại nào giữ người xem — không phải để ép LLM viết theo khuôn.
HOOK_TYPES = (
    "con_so_soc", "mau_thuan", "ket_qua_truoc", "demo_truoc", "truoc_sau", "cau_hoi_co_so",
    "canh_bao", "bi_mat", "boc_tin_don", "tu_do", "that_bai", "so_sanh_gia", "in_medias_res",
    "danh_sach", "ban_dang_sai", "thoi_gian", "pha_tuong_4", "doi_dau", "context_snapback",
    "he_qua_nguoi_viet",
)
HOOK_TEXT_MAX_WORDS = 7
# Từ khung chung của prompt ảnh (ánh sáng, nền) — không tính khi so hai ảnh có trùng chủ thể không.
_STOP = {"dark", "light", "lighting", "background", "shadow", "shadows", "deep", "single", "soft", "cool",
         "warm", "blue", "teal", "from", "side", "with", "desk", "table", "surface", "alone", "glowing",
         "cinematic", "photo", "photograph", "realistic", "close", "closeup", "lying", "resting", "standing",
         "wooden", "black", "empty", "room", "objects", "only", "blank", "text", "letters", "writing", "high",
         "detail", "detailed", "sharp", "focus", "subject", "bright", "rich", "color", "colors", "minimal"}
# Từ chỉ người trong prompt ảnh — kênh không dùng mặt/dáng người AI (Tony 2026-10-02, research/11 §5).
_PEOPLE = re.compile(
    r"\b(person|people|man|men|woman|women|girl|boy|guy|face|faces|portrait|human|student|students|"
    r"worker|developer|engineer|child|kid|hand|hands|selfie|crowd|someone|businessman|teen|lady)\b", re.I)
# "no people", "without hands", "no human figures" là lời DẶN tránh người, không phải có người (2026-10-07: mẹo v10 chết ở
# cổng kịch bản vì bản sửa viết "…, no people" — kiểm cứng bắt nhầm).
_NEGATED = re.compile(r"\b(no|without|zero|not any)\s+(\w+\s+){0,2}?(person|people|man|men|woman|women|girl|boy|guy|faces?|"
                      r"portrait|humans?|students?|workers?|developers?|engineers?|child|kids?|hands?|selfie|crowd|"
                      r"someone|businessman|teen|lady)\b(\s+figures?)?", re.I)


def _people_in(prompt: str) -> re.Match | None:
    return _PEOPLE.search(_NEGATED.sub(" ", prompt or ""))


OVERLAY_MAX_CHARS = 24  # khớp maxLength ở spec/schema.json


@dataclass
class Shot:
    prompt: str           # tiếng Anh, cho SDXL (kind=image; với kind khác là b-roll dự phòng)
    duration_sec: float = 5.0
    motion: str = "ken_burns"
    # Kiểu cũ (trước 2026-10-01): overlay gắn vào shot. Vẫn đọc để không vỡ
    # script.json cũ, nhưng pipeline KHÔNG dùng nữa — shot và câu không tương
    # ứng 1-1 nên overlay hiện sai lúc. Dùng `Script.overlays`.
    overlay: str | None = None
    # P3b.S4: shot neo vào CÂU (chỉ số trong `lines`) + loại hình. `line=None` là
    # script cũ → router xoay vòng prompt như trước.
    kind: str = "image"   # image | stat | chart | code | screenshot | chat | list (chat/list: kênh mẹo 2026-10-04)
    line: int | None = None
    stat: dict | None = None      # {value, unit?, label, decimals?, prefix?}
    chart: dict | None = None     # {title, unit?, bars: [{label, value, highlight?}]}
    code: dict | None = None      # {lang, title?, lines: [...]}
    url: str | None = None        # screenshot
    highlight: str | None = None  # screenshot: chữ cần tô vàng trên trang
    chat: dict | None = None      # {title?, messages: [{from: me|them, text, mark?: ok|no}]}
    list: dict | None = None      # {title?, items: [{text, mark?: num|ok|no}]}
    query: str | None = None      # stock (2026-10-05): từ khoá tiếng Anh tìm cảnh quay thật Pexels/Pixabay


@dataclass
class Script:
    topic: str
    hook: str
    sections: list[str] = field(default_factory=list)
    cta: str = ""
    shots: list[Shot] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    caption: str = ""                          # TikTok cắt hiển thị ở 150 ký tự
    hashtags: list[str] = field(default_factory=list)   # 3-5, ngách, không #fyp #viral
    keywords: list[str] = field(default_factory=list)   # keywords[0] = từ khoá chính
    # Chữ dán trên hình, gắn vào CÂU: [{"line": chỉ số trong `lines`, "text": "16-bit"}].
    # line 0 = hook, 1..n = sections, cuối = cta. Overlay hiện đúng lúc câu đó được đọc.
    overlays: list[dict] = field(default_factory=list)
    # P3b.S5: cụm trong LỜI ĐỌC cần nhấn màu trên phụ đề (con số, tên model) —
    # viết nguyên văn như trong câu ("tám phẩy hai giây", "SDXL-Lightning").
    emphasis: list[str] = field(default_factory=list)
    # Phase V3 (2026-10-02, research/11 §4.1–4.2): chữ tiêu đề frame 0 (≤ 7 từ, KHÁC lời hook,
    # cùng ý) · loại hook (để học sau 20 video) · pillar nội dung.
    hook_text: str = ""
    hook_type: str = ""
    pillar: str = ""
    # Bộ đăng (2026-10-02, research/probes/bo-dang-research.md): bình luận Tony ghim sau khi đăng.
    pin_comment: str = ""
    # 2026-10-06 (research/21 §4): kiểu kết do CODE chọn xoay vòng (angles.END_STYLES) — T3 chấm CTA theo kiểu này.
    end_style: str = ""

    @property
    def lines(self) -> list[str]:
        """Toàn bộ lời đọc theo thứ tự: hook → thân → CTA."""
        return [self.hook, *self.sections, self.cta]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict, topic: str | None = None) -> "Script":
        """Một chỗ duy nhất đọc JSON → Script: cho cả output agent lẫn script.json cache."""
        return cls(
            topic=topic or d.get("topic", ""),
            hook=d["hook"].strip(),
            sections=[x.strip() for x in d.get("sections", [])],
            cta=d.get("cta", "").strip(),
            shots=[
                Shot(
                    prompt=x.get("prompt") or "",
                    duration_sec=float(x.get("duration_sec") or 5),
                    motion=x.get("motion") or "ken_burns",
                    overlay=x.get("overlay"),
                    kind=x.get("kind") or "image",
                    line=x.get("line"),
                    stat=_clean_stat(x.get("stat")), chart=x.get("chart"), code=x.get("code"),
                    url=x.get("url"), highlight=x.get("highlight"),
                    chat=x.get("chat"), list=x.get("list"), query=x.get("query"),
                )
                for x in d.get("shots", [])
            ],
            sources=d.get("sources", []),
            caption=d.get("caption", "").strip(),
            hashtags=[str(h).lstrip("#").strip() for h in d.get("hashtags", [])],
            keywords=[str(k).strip() for k in d.get("keywords", [])],
            overlays=[
                {"line": int(o["line"]), "text": str(o["text"]).strip()}
                for o in d.get("overlays", [])
            ],
            emphasis=[str(x).strip() for x in d.get("emphasis") or [] if str(x).strip()],
            hook_text=str(d.get("hook_text") or "").strip(),
            hook_type=str(d.get("hook_type") or "").strip(),
            pillar=str(d.get("pillar") or "").strip(),
            pin_comment=str(d.get("pin_comment") or "").strip(),
            end_style=str(d.get("end_style") or "").strip(),
        )


def _clean_stat(st: dict | None) -> dict | None:
    """Thẻ số: schema spec cho `decimals` 0–2 (2026-10-10: video ngọc trai bị chặn vì decimals=3) → kẹp 0–2, làm tròn
    `value` theo đó. Áp cả cho script.json cũ đã lưu (đọc qua from_dict)."""
    if not isinstance(st, dict) or st.get("decimals") is None:
        return st
    try:
        d = max(0, min(2, int(st["decimals"])))
    except (TypeError, ValueError):
        d = 0
    out = {**st, "decimals": d}
    if isinstance(st.get("value"), (int, float)):
        out["value"] = round(float(st["value"]), d)
    return out


def _avoid_rule() -> str:
    """Từ TTS đọc hỏng (configs/pronounce.yaml: avoid, đo bằng ASR ở P3b.S3) → dặn tránh."""
    import yaml

    p = REPO_ROOT / "configs" / "pronounce.yaml"
    d = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("avoid") if p.exists() else None
    pairs = [f'"{k}" → "{v}"' for k, v in (d or {}).items() if k != v]
    if not pairs:
        return ""
    return (
        "   NGOẠI LỆ — giọng đọc phát âm hỏng các từ sau, dùng từ Việt thay khi câu vẫn tự\n"
        "   nhiên: " + ", ".join(pairs) + "."
    )


def _min_evidence_hint(duration_sec: int) -> int:
    """Số shot bằng chứng tối thiểu — cùng công thức với `_check` (≈ 1/3 số shot)."""
    return max(2, -(-(duration_sec // 5) // 3))


# Mặc định của code = kênh AI. Kênh khác ghi đè từng đoạn ở `configs/channels/<kênh>/channel.yaml: prompts`
# (2026-10-04, research/13 §5). Kênh AI không khai gì → prompt giống hệt trước khi tách.
INTRO_AI = """Bạn viết kịch bản video TikTok tiếng Việt về AI cho khán giả Việt Nam PHỔ THÔNG (sinh viên,
dân văn phòng, người làm nội dung — không chỉ dev)."""
HOOK_EXAMPLE_AI = 'hook "Gemini vừa cho sinh viên Việt Nam dùng bản Pro miễn phí một năm" →\n    hook_text "Gemini Pro: 0 đồng"'
IMAGE_EXAMPLES_AI = "điện thoại hiện khung chat, laptop, sách vở, ví\n   tiền, đồng hồ, chip, bản đồ Việt Nam…"
TERMS_AI = """1. Số trong lời văn phải viết BẰNG CHỮ: "sáu GB", "ba mươi bảy giây", "mười lăm
   phần trăm" — không viết "6GB", "37 giây", "15%". Lý do: TTS đọc chữ số thành
   nhiều từ hơn số từ hiện trên màn hình, làm phụ đề karaoke mất mốc thời gian.
   NGOẠI LỆ: tên riêng thì giữ NGUYÊN dạng thật của nó — "Qwen3-VL", "GPT-5",
   "Claude Opus 5", "SDXL". Đổi tên model thành chữ là sai tên, tệ hơn nhiều so
   với lệch phụ đề vài chục mili giây.
2. Tên model, tên hãng, thuật ngữ tiếng Anh thì GIỮ NGUYÊN (model, benchmark,
   fine-tune, inference, prompt, open-source, hook, retention)."""
CODE_KIND_AI = """   - `code`: đoạn code ≤ 12 dòng × 40 ký tự — {"lang": "python", "lines": [...]}.
     CHỈ TRÍCH code có sẵn trong đề bài (được cắt dòng cho vừa, giữ nguyên tên hàm/
     tham số). Đề bài không có code thì KHÔNG dùng kind này — code tự viết trông như
     bằng chứng mà sai là tệ hơn không có.
"""
SCREENSHOT_AI = """   - `screenshot`: chụp trang thật — `url` là một trang trong "TRANG CHỤP ĐƯỢC" của đề bài,
     hoặc trang model Hugging Face (huggingface.co/<org>/<model>), repo GitHub
     (github.com/<owner>/<repo>), arxiv.org/abs/<id>; `highlight` (nên có) là cụm chữ CÓ
     NGUYÊN VĂN TRÊN trang cần tô vàng — video cuộn tới đúng chỗ đó. Không bịa URL."""
SCREENSHOT_TIP_AI = """   - `screenshot`: ưu tiên trang model Hugging Face và abstract arXiv (chữ to, đọc được). KHÔNG chụp
     README GitHub dài — chữ tiếng Anh nhỏ, đang cuộn, trên điện thoại không đọc nổi.
"""
STOCK_KIND = """   - `stock`: CẢNH QUAY THẬT (video) từ kho Pexels/Pixabay — `query` tiếng Anh 2–6 từ, hành động/đồ vật CỤ THỂ
     quay được ngoài đời, VẬT CHÍNH ĐỨNG ĐẦU ("smartphone held in hands", "vegetables washed in sink", "street flooded with
     motorbikes").
     Dùng cho cảnh đời thực (bếp, chợ, phố, điện thoại, tiền, thời tiết) — thật hơn ảnh AI. Chủ đề lừa đảo/tiêu cực:
     query KHÔNG có người lộ mặt (dùng "hands", "phone screen", "close up"). Không tìm chữ/logo/thương hiệu.
     Cảnh ĐỦ SÁNG: không dùng "dark", "night", "dim" trong query — clip tối thành dải đen trên điện thoại (code loại).
     TỪ ĐẦU TIÊN của `query` là VẬT CHÍNH phải thấy trong cảnh ("refrigerator door opened by hand", "rice cooked in
     container") — code loại clip thiếu vật chính (clip "mở cửa nhà" cho câu về tủ lạnh, 2026-10-06).
     `query` tả ĐÚNG vật/hành động mà CÂU ĐÓ nói, không tả chủ đề chung của video: câu "Mũi không phải máy đo" → "person
     sniffing food container", KHÔNG "cooked pork bowl" (video thử 2026-10-06: query theo chủ đề → clip bát mì cho câu về
     cái mũi — research/21 §8 C5). Câu trừu tượng không quay được → dùng thẻ bằng chứng của kênh, không ép `stock`."""
ICON_HINT = """   - `icon` (tuỳ chọn, NÊN có ở `stat` và từng mục `list`): MỘT emoji Unicode minh hoạ đúng đồ vật/ý (📱 💰 🥩 ⚠️ 🔒
     🧊 🤖) — code vẽ thành hình 3D cạnh chữ. Không dùng emoji mặt người/cờ."""
H4_AI = """H4. Shot ở câu 0 NÊN là bằng chứng mang CHỦ ĐỀ (screenshot trang thật, hoặc stat có con số của hook) —
    người xem phải nhận ra video nói về cái gì ngay frame đầu. Ảnh AI ở câu 0 chỉ khi không có bằng chứng."""
H4_HEADLINE = """H4. Shot ở câu 0 là ẢNH BÌA: dùng `stock` (cảnh quay thật gây chú ý, đúng chủ đề) hoặc `stat` có con số sốc
    của hook. KHÔNG dùng `screenshot` ở câu 0 — trang chụp chữ nhỏ không kéo được người đang lướt (tiêu đề cố định phía
    trên đã nói chủ đề). Hình câu 0 phải là ĐÚNG VẬT/CẢNH mà lời hook nhắc tới (danh từ cụ thể trong hook: "cục sạc cắm
    qua đêm", "tin nhắn báo hoàn học phí") — không cảnh chung chung cùng chủ đề (2026-10-06, research/21: 2/5 video kênh mở
    bằng hình lệch hook — đồng hồ trên gạch cho câu về sạc pin; tay xào bài cho chiêu lừa học phí)."""
SPEECH_EXAMPLES_AI = """- @ai5phut (340K view): "Có một bài toán mà loài người giải suốt một trăm sáu mươi bảy năm mà không xong, trao giải
  một triệu đô mà không ai lấy được. Bài toán đấy tên là giả thuyết Riemann. Nói gọn ra thì như này nhé: mọi con số trên
  đời đều xây từ số nguyên tố, như xây nhà từ những viên gạch."
- @aidev.news (248K): "Việt Nam vừa mất gần một phần ba đường ra internet quốc tế. Tối hai lăm tháng tám, hai tuyến cáp
  cùng lúc gặp sự cố, trong khi hai tuyến kia còn chưa sửa xong. Với dân AI thì giờ cao điểm gọi API sẽ chậm thấy rõ."
- @hieuanca (1,2M): "Nếu bạn gõ gạch chéo ba trăm sáu mươi view vào ChatGPT, nó sẽ tạo ra góc nhìn ba trăm sáu mươi độ
  cho sản phẩm của bạn. Còn gõ gạch chéo x-ray thì nó vẽ luôn bên trong sản phẩm."
"""
HASHTAG_EXAMPLE_AI = '"sdxl", "aiopensource", "rtx2060"'
STAT_EXAMPLE_AI = '{"value": 6, "unit": "GB", "label": "VRAM của RTX 2060"}'


def _indent(text: str, n: int) -> str:
    return "\n".join((" " * n + ln) if ln.strip() else ln for ln in text.splitlines())


def _pillars() -> tuple[str, ...]:
    from ..channel import current

    return tuple(current().pillars)


def evidence_kinds() -> tuple[str, ...]:
    """Loại shot tính là bằng chứng ở kênh đang chạy (chat/list chỉ kênh có khai)."""
    from ..channel import current

    return tuple(k for k in current().shot_kinds if k in EVIDENCE_KINDS)


# 2026-10-06 (research/21 §8 D1): ngân sách số từ theo độ dài. Đo: 226 từ → 56,5s (4,0 từ/giây, giọng Tony + pace). Video
# thử v2 xin 55s, kịch bản 162 từ → 41s — prompt chỉ nói "khoảng N giây", không có số từ.
WORDS_PER_SEC = 4.0


def _word_budget(duration_sec: int) -> tuple[int, int]:
    # v2 2026-10-07: trần 1,0 (không 1,1) — giọng đo 3,57–4,37 từ/giây theo kịch bản; 236 từ ra 66s (> 65s)
    n = duration_sec * WORDS_PER_SEC
    return int(n * 0.9), int(n * 0.98)   # v3: 0,98 — lô cuối 226 từ đọc 3,47 từ/giây = 65,2s (> 65)


def _check_length(script: Script, duration_sec: int) -> list[str]:
    """Kiểm MỀM: tổng số từ lời đọc lệch ngân sách quá 15% (research/21 §8 D1)."""
    n = sum(len(x.split()) for x in script.lines)
    target = duration_sec * WORDS_PER_SEC
    if n < 0.85 * target or n > 1.02 * target:
        lo, hi = _word_budget(duration_sec)
        return [f"lời đọc {n} từ ≈ {n / WORDS_PER_SEC:.0f}s — video cần ~{duration_sec}s = {lo}–{hi} từ; "
                + ("thêm ý/ví dụ cụ thể, KHÔNG thêm câu đệm" if n < target else "cắt câu ít thông tin nhất")]
    return []


# 2026-10-08 (research/25): luật dễ hiểu + thân thuộc D1–D18. BẬT MẶC ĐỊNH từ 2026-10-09 theo lệnh Tony ("deploy phiên
# bản tốt nhất hiện có") dù probe kb-de-hieu chưa đạt ngưỡng giảm ½ — tốt hơn bản cũ ở mọi mục đo (research/probes/
# kb-de-hieu.md, lượt 2). Tắt: CV_SCRIPT_DE_HIEU=0. Worker web chạy pipeline bằng subprocess nên áp ngay cho job sau.
DE_HIEU = """DỄ HIỂU KHI NGHE MỘT LẦN — ƯU TIÊN CAO NHẤT, trên mọi luật nhịp/cuốn bên dưới (Tony 2026-10-08: "kịch bản khó hiểu cho
người nghe khi họ theo dõi hết video"; research/25-kich-ban-de-hieu.md). Người nghe: người Việt ~40 tuổi, dùng điện thoại
hằng ngày nhưng KHÔNG rành công nghệ, không đọc tiếng Anh, nghe một lần ~4 từ/giây, không tua lại. Hai luật đụng nhau thì
luật DỄ HIỂU thắng.
D1. MỘT THÔNG ĐIỆP: cả video mang về đúng MỘT điều (+ việc phải làm). Nói rõ nó trong 3 câu đầu sau hook và nhắc lại ở gần
    cuối bằng chữ khác. Video nhiều mục thì các mục cùng phục vụ thông điệp đó.
D2. KHÔNG LẠC ĐỀ: câu nào không giúp hiểu hoặc làm theo thông điệp thì bỏ, kể cả khi nó thú vị (chi tiết hấp dẫn mà lạc đề
    làm người xem nhớ kém đi — meta-analysis 58 nghiên cứu). Không ghép hai câu chuyện vào một video.
D3. KHÔNG TỪ LẠ KHÔNG GIẢI THÍCH: tên vi khuẩn/chất/bệnh, tên công ty hay cơ quan nước ngoài ít người Việt biết, tính năng
    tiếng Anh, từ Hán Việt chuyên ngành ("nha bào", "sinh khí", "cookie phiên", "định danh mức hai") → nói bằng lời thường
    ("con vi khuẩn trong hộp", "công ty bảo mật Proofpoint", "cái vé giữ bạn đăng nhập"). Thật cần giữ tên thì kèm 3–6 từ
    giải thích NGAY lần đầu nhắc. Tối đa 2 từ cần giải thích trong cả video. Thuật ngữ giữ tiếng Anh của kênh vẫn giữ,
    nhưng lần đầu nhắc phải kèm nghĩa. Tên công ty/cơ quan: chỉ nói tên mà KHÁN GIẢ KÊNH chắc chắn biết (Google, Facebook,
    Zalo, TikTok, ChatGPT, Công an, Bộ Y tế); tên khác nói bằng vai trò ("công ty làm ra Claude", "cảnh sát Mỹ", "cơ quan
    an toàn thực phẩm của Bộ Y tế").
D4. NGUỒN NÓI RA TỐI ĐA HAI LẦN cả video, chọn tên người Việt nhận ra (Bộ Y tế, Công an, Google, Apple). Nguồn lạ → nói
    loại ("cơ quan y tế Mỹ", "một công ty bảo mật"). Các nguồn còn lại chỉ nằm trong `sources` — không mở mỗi câu bằng
    "X nói", "Y ghi rõ".
D5. ÍT SỐ: lời đọc chứa TỐI ĐA BA con số cả video (người nghe nhớ được ~4 thứ một lúc), mỗi câu tối đa một số, làm tròn
    ("gần ba mươi phần trăm", không "hai mươi bảy phẩy tám"). Con số chính nhắc lại một lần. Số phụ → lên hình (`stat`/`chart`)
    hoặc bỏ. Đề bài có NHIỀU NGƯỠNG cho cùng một việc (mười lăm phút / một tiếng; hai giờ / một giờ; hai ngày / ba ngày) →
    chọn MỘT ngưỡng dẫn tới hành động an toàn nhất và chỉ nói ngưỡng đó; ngưỡng còn lại bỏ, kể cả khi nó đúng.
D6. GỌI TÊN, ĐỪNG "NÓ": "nó / họ / chúng / cái đó / số đó / nút kia" chỉ dùng khi thứ đó vừa được gọi tên ở ĐÚNG câu trước
    và không có thứ thứ hai dễ lẫn. Còn lại gọi tên lại ("con vi khuẩn", "kẻ lừa").
D7. KHÔNG ĐẢO CHIỀU LỜI KHUYÊN: không nói một cách làm rồi vài câu sau bảo cách đó không được ("đun mười lăm phút" rồi "thật
    ra phải bỏ") — người nghe nhớ nhầm câu đầu. Nói kết luận đúng TRƯỚC, sau đó mới nói vì sao cách người ta hay làm không đủ.
    Chỗ ngoặt (luật J) THÊM điều mới cùng hướng (nguy hiểm hơn, lỗi phổ biến hơn), không lật lời khuyên, và NÓI THẲNG điều
    đó ngay trong câu — KHÔNG câu nhử kiểu "Nhưng đây mới là chỗ…", "Nhưng có một điều…", "chỗ nhiều nhà bỏ sót" (người
    nghe thấy bị nhử hoặc bị trách). "Nhưng" chỉ dùng khi câu sau thật sự ngược câu trước. Vòng tò mò (luật B) đóng bằng
    một câu NÓI THẲNG đáp án.
D8. DANH SÁCH ĐẾM ĐÚNG: báo trước có mấy mục, gọi "cách một / cách hai…" đúng thứ tự, không có "cách hai" khi chưa có
    "cách một".
D9. KHÔNG RÀO ĐÓN GIỮA CHỪNG: không chèn câu kiểu "tương quan thôi nhé", "mà công bằng nhé, X không nói…", "số đó ở nước
    ngoài" — nguồn yếu tới mức phải rào thì BỎ hẳn ý đó; ý giữ lại thì nói chắc theo đúng mức nguồn nói.
D10. MỖI CÂU TỰ ĐỨNG ĐƯỢC: câu mang thông tin mới phải có chủ ngữ rõ ("Họ hỏi số căn cước để đánh cắp danh tính", không
    "Để đánh cắp danh tính thôi."). Câu cụt chỉ để chốt cảm xúc ("Mất sạch.", "Thế là xong.").

THÂN THUỘC, DỄ CHỊU, CUỐN — cùng mức ưu tiên với D1–D10 (Tony 2026-10-08: "không những dễ hiểu mà còn thân thuộc với người
xem, giúp họ dễ chịu, bị cuốn hút khi nghe"; nguồn ở research/25):
D11. CẢNH QUEN TRƯỚC: trong 3 câu đầu có MỘT cảnh đời thường cụ thể người Việt từng gặp (bữa cơm, đi chợ, tin nhắn Zalo của
    con, cuộc gọi "bên ngân hàng", ông bà lướt điện thoại tối) — người xem phải thấy "chuyện nhà mình". Cảnh giả định thì nói
    "Giả sử…", "Thử nghĩ…" — KHÔNG bịa nhân vật, câu chuyện hay số liệu như chuyện có thật.
D12. ĐỨNG CÙNG PHÍA NGƯỜI XEM: không chê người xem ("Sai rồi.", "bạn đang làm sai", "bạn sẽ bị lừa"). Nói thói quen chung
    ("nhiều nhà hay…", "ai cũng từng nghĩ thế"). Đính chính theo thứ tự: điều ĐÚNG → nhắc điều hiểu sai đúng MỘT lần → một
    câu thông cảm vì sao ai cũng nghĩ vậy ("nghe hợp lý lắm, vì…") → nhắc lại điều đúng (Debunking Handbook 2020).
D13. KHÔNG RA LỆNH, KHÔNG DOẠ: tránh "phải", "tuyệt đối", "cấm", "đừng bao giờ", "nhất định", "chết người", dấu "!" — người
    nghe bị ra lệnh thì cãi lại trong đầu. Dùng "nên", "thử", "nhà mình cứ…". Thân bài tối đa MỘT câu khuyên mạnh, kèm một câu
    để người xem tự quyết ("tuỳ nhà mình"). Hook dạng "Đừng…" theo luật H vẫn được, một lần. KHÔNG câu mệnh lệnh trần
    ("Bỏ luôn.", "Hộp phồng là bỏ.", "Nên chia việc ra nhé") — viết thành lời người nhà ("Nhà mình cứ bỏ cho yên tâm").
    CÂU KẾT cũng theo luật này: theo KIỂU KẾT nhưng là lời RỦ có lý do, không ra lệnh ("Lưu lại…", "Chọn giúp mình"),
    không ép làm ngay ("tối nay", "ngay bây giờ").
D14. NGUY CƠ ĐI KÈM CÁCH LÀM: nói một nguy cơ thì trong 2 câu sau phải có việc cụ thể làm được ngay (dưới một phút). Mức
    nghiêm trọng nói một câu bình tĩnh ("hiếm thôi, nhưng có"); không lấy cái chết/thương tật làm cao trào, không nhắc chết
    chóc trong 2 câu đầu.
D15. VIDEO LỪA ĐẢO: dạy THỦ ĐOẠN (tạo gấp gáp, giả danh, đòi giữ bí mật, đòi mã) + một CÂU KIỂM TRA ngắn người xem nhắc lại
    được ("Cứ đòi chuyển tiền gấp là cúp máy gọi lại số mình lưu"); không kể chi tiết thiệt hại của nạn nhân.
D16. ẤM NHƯ NGƯỜI NHÀ: không từ bài giảng/công văn ("cần lưu ý", "khuyến cáo", "như vậy có thể thấy", "người dân"); gọi
    người xem như người nhà ("bạn", "nhà mình", "bố mẹ mình"). Người kể KHÔNG tự nhận đã trải qua chuyện chưa có thật (luật C).
D18. CÁCH LÀM PHẢI LÀM THEO ĐƯỢC: khuyên bật/dùng một tính năng thì nói CHỖ BẤM bằng chữ đúng như trên máy ("vào Cài
    đặt, chọn Mật khẩu, bật Passkey") hoặc thay bằng việc làm được mà không cần tìm; không khuyên thứ người xem không biết
    tìm ở đâu. Một video tối đa HAI việc phải làm.
LƯU & CHIA SẺ (2026-10-11, research/28 — 645 video 13 kênh Việt: video bùng được chia sẻ ×2; kênh cùng ngách bùng nổ có
lưu/view 2,25% so với kênh mình 0,22%; dạng "N mẹo/lệnh/bước" bùng ×1,64):
S1. Phần giá trị chính là 2–5 BƯỚC hoặc MỤC đánh số, báo trước số mục ("Ba bước thôi:"), mỗi mục một câu làm được ngay.
S2. Ngay SAU mục giá trị chính (không phải câu cuối) có ĐÚNG MỘT câu rủ lưu kèm lý do, viết như lời người nhà (D13):
    "Lưu lại, lúc cần mở ra làm theo là xong." Không xin like/follow.
S3. Shot ở câu CUỐI là thẻ `list` TÓM TẮT các bước (≤ 4 mục, mỗi mục ≤ 30 ký tự, `title` nói lợi ích) — người xem dừng video
    là chụp được, đủ để làm theo mà không cần xem lại.
S4. Cho thấy CÔNG SỨC THẬT: kết quả cụ thể (con số đo, câu lệnh nguyên văn, ảnh chụp đúng trang công cụ) thay vì mô tả chung
    — nhãn AI làm người xem nghĩ "ít công sức", bằng chứng làm thật bù lại (Carney et al., JCR 2026).
D17. VUI ĐÚNG CHỖ: kênh AI được đùa nhẹ bằng so sánh đời thường; chủ đề an toàn, thực phẩm, lừa đảo KHÔNG đùa về chính mối
    nguy — chỉ nhẹ nhàng ở cảnh mở hoặc lúc chỉ cách làm.

"""


def _system_prompt(duration_sec: int) -> str:
    from ..channel import current

    ch = current()
    rubric = ch.rubric_path.read_text(encoding="utf-8")
    kinds = ch.shot_kinds
    code_kind = CODE_KIND_AI if "code" in kinds else ""
    shot_rule = _indent(ch.text("screenshot_rule"), 3) if ch.text("screenshot_rule") else SCREENSHOT_AI
    extra = ch.text("extra_kinds", "")
    extra = ("\n" + _indent(extra, 3)) if extra else ""
    if "stock" in kinds:
        extra += "\n" + STOCK_KIND
    extra += "\n" + ICON_HINT
    shot_tip = SCREENSHOT_TIP_AI if "screenshot_rule" not in (ch.raw.get("prompts") or {}) else ""
    ev = "/".join(k for k in kinds if k in EVIDENCE_KINDS)
    stat_ex = ch.text("json_stat_example", STAT_EXAMPLE_AI)
    # 2026-10-05: bố cục headline đã có tiêu đề cố định nói chủ đề → khung đầu (= ảnh bìa) cần HÌNH gây chú ý, không phải
    # trang chụp chữ nhỏ (demo v3 kênh mẹo; Zack D. Films: hình gây sốc trước chữ đầu tiên — research/15).
    h4 = H4_HEADLINE if ch.style.get("layout") else H4_AI
    # Bố cục headline (ảnh TRÀN màn hình, research/18): nền đen trơn thành dải đen phẳng ở mép → T1 "viền đen" chặn
    # (bản xem trước 2026-10-05). Bố cục cũ (ảnh trong khung) giữ "nền tối".
    img_bg = ("cảnh có chiều sâu, ánh sáng tự nhiên ấm, NỀN CÓ CHI TIẾT phủ kín khung (bàn, tường, phòng) — không nền đen trơn"
              if ch.style.get("layout") else "chủ thể sáng rõ trên NỀN TỐI")
    r_img = float(ch.flag("image_min_ratio", 0) or 0)
    img_rule = (f"\n   LUẬT KÊNH: ≥ {r_img:.0%} số shot là `image` (ảnh cảnh thật, đẹp như ảnh chụp) — video không được thành "
                "\n   trình chiếu thẻ chữ.") if r_img else ""
    r_real = float(ch.flag("real_min_ratio", 0) or 0)
    if r_real and "stock" in kinds:
        img_rule += (f"\n   LUẬT KÊNH: ≥ {r_real:.0%} số shot là `stock` (CẢNH QUAY/ẢNH CHỤP THẬT) — người xem chán ảnh AI. "
                     "\n   `image` (ảnh AI) chỉ cho cảnh KHÔNG quay được ngoài đời (khái niệm, đồ vật tưởng tượng).")
    lo_w, hi_w = _word_budget(duration_sec)
    de_hieu = "" if os.environ.get("CV_SCRIPT_DE_HIEU") == "0" else DE_HIEU
    return f"""{ch.text("script_intro", INTRO_AI)} Video dọc 1080×1920, dài khoảng {duration_sec} giây
(= TỔNG lời đọc {lo_w}–{hi_w} từ, giọng đọc ~4 từ/giây — đếm cả hook và câu kết),
giọng đọc nam, kênh KHÔNG lộ mặt người dẫn.

ĐỀ BÀI thường kèm "SỰ THẬT ĐÃ KIỂM" (F1, F2…) do researcher tìm và code đã đối chiếu nguồn. Khi có:
CHỈ dùng sự thật trong đó, `sources[].url` lấy đúng url của sự thật đã dùng. Không thêm số ngoài danh sách.

{de_hieu}5 GIÂY ĐẦU QUYẾT ĐỊNH TẤT CẢ (research/11: phần lớn người xem lướt đi trong 5s đầu):
H1. `hook` (lời đọc, ≤ 12 từ) đưa THÔNG TIN CỤ THỂ ngay — con số, kết quả, mâu thuẫn. Không chào, không
    bối cảnh, không định nghĩa.
H2. `hook_text` (chữ to trên frame 0, 2–7 từ) KHÁC lời hook nhưng CÙNG MỘT Ý — kiểu tiêu đề báo, đọc
    trong 1 giây. Ví dụ {ch.text("hook_example", HOOK_EXAMPLE_AI)}. Được dùng chữ số trong hook_text (code vẽ, không đọc).
H3. `hook_type` chọn MỘT: {", ".join(HOOK_TYPES)}.
{h4}
H5. `pillar` chọn MỘT: {", ".join(ch.pillars)} (đề bài có PILLAR thì dùng đúng nó).

Nhịp là thứ quan trọng thứ hai sau hook: không có câu THỪA (câu không mang thông tin). Nhưng từ nối của văn nói không
phải câu thừa — nó là thứ làm lời nghe như người thật.

VĂN NÓI — viết như một người thật đang KỂ bằng miệng, không phải đọc bản tin gạch đầu dòng:
V1. Độ dài câu XEN KẼ mạnh: có câu 2–5 từ chốt ý ("Thế thôi.", "Xong."), có câu 18–25 từ chảy liền một hơi bằng
    "thì", "mà", "nên", "rồi", "là". Không để ba câu liền nhau dài xấp xỉ nhau.
V2. Câu sau NỐI vào câu trước như lúc nói: "Mà khoan,", "Nói gọn là", "Thế là", "Vấn đề là", "Đấy,", "Còn nữa,",
    "Để ý nhé:". Đừng để câu nào cũng mở một mệnh đề mới toanh.
V3. Tiểu từ cuối câu tự nhiên — nhé, nha, đấy, đó, à, luôn, thôi, mà — khoảng 1 trong 3 câu, không dồn một chỗ.
V4. 1–2 chỗ hỏi rồi tự trả lời ngay ("Vì sao? Vì…").
V5. Từ đời thường, cụ thể ("lấy điện thoại ra", "bấm vào", "mất tiền oan") — không danh từ hoá ("việc thực hiện",
    "sự gia tăng").
V6. NHẤN bằng cấu trúc: chữ quan trọng đặt ở CUỐI câu ngắn; trước con số/ý chốt dùng "…" ("mất… một trăm triệu");
    dấu phẩy đặt đúng chỗ người nói lấy hơi — code ngắt giọng theo đúng dấu câu bạn viết.
V7. Dấu hiệu văn AI người xem nhận ra ngay — viết cách khác: gạch ngang "—" giữa câu, liệt kê đúng ba vế, "không chỉ… mà
    còn", "Hơn nữa", "Thêm vào đó", "Đáng chú ý", "Bạn có biết", "Hãy cùng", "Tóm lại", "Trong bối cảnh", "đóng vai trò".
CÁCH NÓI THAM KHẢO — lời thật của kênh top (học NHỊP và từ nối, KHÔNG chép nội dung, KHÔNG bắt chước từ ngữ suồng sã):
{ch.text("speech_examples", SPEECH_EXAMPLES_AI)}

RUBRIC — đây chính là thứ critic sẽ dùng để chấm bạn. Đọc kỹ, viết đúng ngay từ đầu:

{rubric}

CUỐN NGƯỜI XEM — thêm 2026-10-02 sau khi Tony xem demo: "video chưa hấp dẫn". Mỗi luật có
bằng chứng ở research/probes/cuon-hon-2026-10-02.md:

A. Hook VÀO GIỮA CHUYỆN, kiểu "khoan, cái gì?": câu đầu là sự thật gây bất ngờ, mâu thuẫn, hoặc
   câu hỏi có con số — người xem phải muốn biết câu trả lời. Không giới thiệu, không dẫn dắt.
B. MỞ MỘT VÒNG TÒ MÒ ở hook, TRẢ LỜI ở khoảng 2/3 video (không để tới câu cuối) — kèm một chỗ
   ngoặt ("nhưng có một điều…") ở giữa.
C. Nói như kể cho bạn: ngôi "mình" – "bạn"/"mọi người", được dùng 1–2 câu hỏi tu từ. NHƯNG chỉ nói "mình thử / mình
   đo / mình vào / mình chạy" khi đề bài có số đo của chính kênh (`research/probes/`) — thông tin từ trang
   help/công bố thì nói "bạn vào…", "Google ghi…" (2026-10-02: tự nhận đã làm mà chưa làm là nói dối). Năng lượng cao, chắc
   chắn — không rào đón "có thể", "dường như" trừ khi nguồn nói vậy.
D. KẾT: đề bài có "KIỂU KẾT" thì câu cuối theo ĐÚNG kiểu đó (code xoay vòng giữa các video — research/21 §4); không có
   thì câu cuối móc lại ý của hook, để người xem muốn xem lại từ đầu.
E. Ảnh minh hoạ (`kind=image`): MỘT chủ thể, ≤ 2 mệnh đề, {img_bg}. KHÔNG tả
   đèn trần, cửa sổ, ngược sáng ở phía trên (mảng trắng chói ở mép trên khung bị QC tầng 1 đọc nhầm
   thành chữ trong vùng UI che — demo-03, 2026-10-02). Prompt ẩn
   dụ nhiều chi tiết làm SDXL hỏng ~nửa số ảnh (P4.S1, P4.S4). **KHÔNG CÓ NGƯỜI** (không mặt, không
   tay, không dáng người — 2026-10-02: mặt người AI là dấu hiệu "AI slop" dễ nhận nhất, và kênh không
   lộ mặt). Dùng đồ vật/biểu tượng cụ thể của chủ đề: {ch.text("image_examples", IMAGE_EXAMPLES_AI)} Ảnh AI là phương án CUỐI — có bằng chứng thì dùng bằng chứng.
   Bề mặt có thể mang chữ (giấy, màn hình, biển, sách) phải ghi rõ TRỐNG: "blank paper", "blank glowing
   screen" — model ảnh vẽ chữ méo lên đó (v2, 2026-10-02: QC tầng 2 bắt 4/6 ảnh có chữ méo).
   KHÔNG vẽ bằng `image` những vật mà bản chất là CHỮ/SỐ: nhiệt kế, đồng hồ, lịch, sách báo, thực đơn, bảng hiệu, hoá
   đơn, bàn phím, cân điện tử — "blank dial" không cứu được (2026-10-06: nhiệt kế mặt số méo sau 2 lần vẽ lại, research/21
   §8 C6). Vật đó → `stock` (ảnh chụp thật) hoặc thẻ `stat` mang con số.
F. KẾT Ở ĐỈNH: câu cuối không chào tạm biệt, không "hẹn gặp lại", không "cảm ơn đã xem".

HỌC TỪ VIDEO VIRAL — 2026-10-06, xem từng nhịp 45 video viral (19 AI · 19 mẹo VN · 7 quốc tế) và 5 video của kênh
(research/21-hoc-tu-video-viral.md; x/n = số video viral có mẫu đó):
G. GIÁ TRỊ ĐẾN SỚM: thứ đáng giá đầu tiên (mục 1 / bước 1 / con số chính / cách kiểm) bắt đầu ở câu thứ 2 hoặc 3 — trước
   ~15% thời lượng (≈ 8 giây). Bối cảnh, nguồn, "ai công bố" TỐI ĐA MỘT câu trước đó. (Listicle mẹo viral: mục 1 trước giây
   5 ở 6/10; video của kênh: mục đầu tới muộn ở 15–23% thời lượng — vùng người xem bỏ đi.)
H0. NỖI KHỔ TRƯỚC, GIẢI PHÁP SAU (2026-10-11, research/27 — cùng một kênh AI Việt: mở bằng tên công cụ/kỹ thuật 292–973
    view; mở bằng nỗi khổ quen "Họp xong là quên sạch." / "Nhờ AI làm PPT?" 2,9K–17,3K, lưu/view ×10): câu đầu và `hook_text`
    nói TÌNH HUỐNG/NỖI KHỔ người xem đang gặp, KHÔNG mở bằng tên công cụ, tên model, thuật ngữ. Tên công cụ đến ở câu 2–3.
H. HOOK CÓ NGƯỜI HOẶC CÓ SỐ: câu hook BẮT BUỘC chứa (a) "bạn" hoặc một nhóm người cụ thể ("phụ huynh", "ai đang dùng
   iPhone"), hoặc (b) một con số; nói trước kết quả thì vẫn kèm (a) hoặc (b) (AI: "bạn" 8/19, số 9/19, kết quả trước 8/19;
   code kiểm). Khung hook đã
   thấy viral (học KHUNG, không chép chữ): "Nếu bạn [làm X với vật quen thuộc], [điều lạ xảy ra]" · "Đừng [X] nữa / nếu
   chưa biết [Y]" · "Những [X] mà [người trong nghề] sẽ không nói cho bạn" · "[Thói quen phổ biến] à? [hậu quả]" ·
   "[Ai làm X, ai làm Y] thì ai [sai / bị phạt]?" · "[Điểm mạnh] lại khiến [hậu quả ngược]".
   Hook đọc MỘT HƠI: tối đa một dấu phẩy, KHÔNG mở bằng một từ đơn rồi ngắt ("Thơm, ngon mắt, …" — TTS đọc từ đứng một
   mình đầu câu thành từ khác, và mỗi dấu phẩy là một khoảng lặng trong 3 giây quý nhất; research/21 §8).
I. MỖI MỤC KẾT BẰNG KẾT QUẢ THẤY ĐƯỢC: video nhiều mục/bước thì mỗi mục khép bằng một câu kết quả ("thế là…", "từ giờ khỏi
   phải… nữa", "… là xong") (9/10 listicle mẹo viral).
J. CHỖ NGOẶT ở 40–75% thời lượng bắt đầu bằng "Nhưng…" / "Nhưng thực tế…" / "Nguy hiểm hơn là…" (mẹo dạng độc thoại 5/7;
   quốc tế 3/7). Video tin/cảnh báo thêm MỘT câu phá niềm tin sớm ("Đừng nghĩ…", "Nhiều người tưởng…") trong 20% đầu.
G2. NÓI THẲNG ĐÁP ÁN BẰNG LỜI: con số / mốc / câu trả lời phải được ĐỌC RA. Cấm đẩy sang hình kiểu "mình để nguyên lên
   hình, bạn đọc là xong", "mình chụp trang lên cho bạn so" — người xem nghe trước, ảnh chụp chữ nhỏ trên điện thoại
   không đọc nổi (video thử v3 2026-10-07: hai câu liền nói về trang nguồn mà không nói con số). Hình chỉ MINH HOẠ lời.
K. LỜI HỨA NGẮN ngay sau hook — CHỈ khi đúng sự thật: "chỉ cần ba bước", "mất đúng ba mươi giây", "miễn phí" (AI 8/19).
L. LỜI ĐỌC KHÔNG CHỨA CHUỖI KỸ THUẬT KHÓ ĐỌC: tên file, phiên bản dài có gạch/chấm ("Qwen3.8-Flash-Next", "start-r.bat"),
   mã số dài — TTS đọc thành "gạch nối flash gạch nối next" (4/5 video của kênh dính lỗi phát âm). Nói tên NGẮN ("bản Qwen
   mới nhất") và để tên đầy đủ trên HÌNH (stat/overlay/screenshot). Viết tắt quen (VNeID, CCCD, iPhone) giữ nguyên.

RÀNG BUỘC KỸ THUẬT — vi phạm là hỏng pipeline, không phải hỏng thẩm mỹ:

{ch.text("terms_rule", TERMS_AI)}
{_avoid_rule()}
3. Mỗi câu lời đọc {MIN_WORDS}-{MAX_WORDS} từ, mỗi câu MỘT ý (một câu = một mục trong `sections`). Độ dài XEN KẼ
   theo V1 — code đo độ chênh độ dài câu và trả lại kịch bản đều tăm tắp.
4. `hook` là MỘT câu, tối đa 12 từ — đọc lên phải xong trong 3 giây.
5. `shots[].prompt` viết bằng TIẾNG ANH, tả cảnh cụ thể, KHÔNG chứa chữ hay logo
   trong ảnh (ảnh sinh ra chữ luôn méo, QC tầng 2 chặn).
6. `overlays` (không bắt buộc, nên có 2-4 cái) là chữ NGẮN (≤ {OVERLAY_MAX_CHARS} ký tự)
   dán lên hình — chỗ duy nhất được viết chữ số, vì nó do code vẽ. Mỗi overlay gắn
   vào MỘT CÂU qua `line` = chỉ số câu (0 = hook, 1 = sections[0], …, cuối = cta)
   và hiện ra đúng lúc câu đó được đọc — nên chữ phải khớp ĐÚNG điều câu đó nói
   ("mười sáu bit" → "16-bit"). Tối đa một overlay mỗi câu.
7. `shots`: mỗi shot NEO VÀO MỘT CÂU qua `line` (cùng cách đánh số với overlays) —
   hình đổi đúng lúc câu đó bắt đầu được đọc. Khoảng {duration_sec // 4} shot, mỗi
   shot một HÌNH KHÁC HẲN shot trước. `kind` là loại hình:
   - `image`: ảnh minh hoạ sinh bằng AI — chỉ là b-roll, KHÔNG mang thông tin.
   - `stat`: một con số lớn đếm lên — {{"value": 6, "unit": "GB", "label": "VRAM tối đa"}}.
     `label` tiếng Việt ≤ 40 ký tự, `unit` ≤ 8 ký tự.
   - `chart`: bar chart so sánh 2-6 cột — {{"title": "...", "unit": "%", "bars":
     [{{"label": "...", "value": 71.2, "highlight": true}}]}}. Đúng MỘT cột highlight
     = thứ video đang nói tới. Nhãn cột ≤ 18 ký tự.
{code_kind}{shot_rule}{extra}
   Rút từ lần tự xem lại demo-03 (2026-10-02):
   - `stat` chỉ cho câu có ĐÚNG MỘT con số. Câu có hai số (giá vào/ra, trước/sau) → dùng `chart`,
     không thì thẻ đứng yên hiện một số trong khi giọng đã đọc sang số khác.
{shot_tip}   - Shot ở câu CTA (câu cuối) là khung người xem thấy ngay trước khi video lặp lại → dùng thẻ
     `stat`/`chart` tóm lại con số chính, hoặc ảnh MỘT chủ thể thật đơn giản.
   Mọi chữ tiếng Việt trên hình (`label`, `title`, nhãn cột) viết CÓ DẤU đầy đủ —
   chỉ hashtag mới viết không dấu.
   LUẬT: ít nhất {_min_evidence_hint(duration_sec)} shot (và ≥ 1/3 số shot) là
   {ev} — hình phải CHỨNG MINH lời nói, không chỉ minh hoạ.{img_rule}
   Shot bằng chứng NÊN đặt ở câu 0 (luật H4). Mọi shot vẫn phải có
   `prompt` tiếng Anh — với shot bằng chứng đó là ảnh dự phòng nếu dựng hỏng.
   Số trong stat/chart phải có trong `sources` — đây là chữ số do code vẽ, nên
   được viết bằng chữ số, nhưng KHÔNG được bịa.
8. Không bịa số liệu. Số nào nói ra phải kèm nguồn trong `sources`; không chắc
   thì đừng nói. Nội dung sai bị bóc rất nhanh và QC tầng 4 chặn cứng.

NHẤN TỪ KHOÁ TRÊN PHỤ ĐỀ — phụ đề hiện từng cụm 1-3 từ, từ được nhấn đổi màu:

9a. `emphasis`: 2-6 cụm NGUYÊN VĂN có trong lời đọc cần đập vào mắt — con số (viết
    bằng chữ đúng như câu: "tám phẩy hai giây"), tên model ("SDXL-Lightning"). Nhấn
    nhiều quá thì không còn gì nổi bật.

METADATA ĐĂNG BÀI — TikTok index cả caption, hashtag, chữ trên hình lẫn lời nói
(hơn 3 tỉ lượt tìm/ngày); bỏ trắng phần này là bỏ nửa tín hiệu tìm kiếm:

9. `keywords`: 2-5 từ khoá hoặc tên riêng, xếp từ QUAN TRỌNG NHẤT lên đầu
   (`keywords[0]` là từ khoá chính). Dùng để chèn vào caption và overlay. `keywords[0]` là CỤM TỪ NGƯỜI VIỆT GÕ TÌM
   (tiếng Việt, kiểu "cách tóm tắt biên bản họp bằng AI", "mẹo luộc rau xanh"), không phải tên công cụ tiếng Anh
   (research/28: mô tả mở bằng tên riêng tiếng Anh bùng ×0,71).
10. `caption`: tối đa 150 ký tự (TikTok cắt hiển thị ở đó) — chứa `keywords[0]`
    trong 100 ký tự đầu. Viết như caption TikTok thật, không phải câu văn trang
    trọng; được chêm 1 emoji hợp ngữ cảnh nếu muốn.
10b. `pin_comment` (≤ 150 ký tự): bình luận Tony GHIM ngay sau khi đăng — một câu hỏi mở để người xem trả lời
    ("Bạn đã thử chưa, ra bao nhiêu?") hoặc nguồn chính ("Nguồn: trang hỗ trợ Google, link ở bio"). Không xin like.
11. `hashtags`: 3-5 hashtag NGÁCH bám sát nội dung video, KHÔNG dùng #fyp #viral
    (quá chung, TikTok hạ ưu tiên). Viết không dấu #, chữ thường liền không dấu
    cách, ví dụ: {ch.text("hashtag_example", HASHTAG_EXAMPLE_AI)}.

Output là JSON theo schema đã cho, ý nghĩa từng trường:

{{
  "hook": "một câu",
  "hook_text": "2-7 từ trên frame 0",
  "hook_type": "con_so_soc",
  "pillar": "{"cong_cu" if "cong_cu" in ch.pillars else next(iter(ch.pillars), "")}",
  "sections": ["câu", "câu", "..."],
  "cta": "một câu kêu gọi cụ thể",
  "shots": [{{"line": 0, "kind": "image", "prompt": "english scene description"}},
            {{"line": 3, "kind": "stat", "prompt": "fallback scene",
              "stat": {stat_ex}}}],
  "overlays": [{{"line": 2, "text": "16-bit"}}],
  "sources": [{{"claim": "điều đã nói", "url": "nguồn", "confidence": "verified|reported"}}],
  "keywords": ["từ khoá chính", "..."],
  "caption": "caption ngắn chứa từ khoá chính",
  "pin_comment": "câu hỏi mở hoặc nguồn để ghim",
  "hashtags": ["ngach1", "ngach2", "ngach3"]
}}"""


class _StatOut(BaseModel):
    icon: str | None = None   # emoji Unicode → ảnh 3D Fluent (2026-10-05)
    value: float
    unit: str | None = None
    label: str
    decimals: int | None = None
    prefix: str | None = None


class _BarOut(BaseModel):
    label: str
    value: float
    highlight: bool | None = None


class _ChartOut(BaseModel):
    title: str
    unit: str | None = None
    bars: list[_BarOut]


class _CodeOut(BaseModel):
    lang: Literal["python", "bash", "typescript", "javascript", "json", "yaml", "text"]
    title: str | None = None
    lines: list[str]


class _ChatMsgOut(BaseModel):
    # `from` là từ khoá Python → alias; schema LLM thấy đúng tên "from"
    sender: Literal["me", "them"] = Field(alias="from")
    text: str
    mark: Literal["ok", "no"] | None = None

    model_config = {"populate_by_name": True}


class _ChatOut(BaseModel):
    title: str | None = None
    messages: list[_ChatMsgOut]


class _ListItemOut(BaseModel):
    icon: str | None = None   # emoji Unicode → ảnh 3D Fluent (2026-10-05)
    text: str
    mark: Literal["num", "ok", "no"] | None = None


class _ListOut(BaseModel):
    title: str | None = None
    items: list[_ListItemOut]


class _SourceOut(BaseModel):
    claim: str
    url: str
    confidence: Literal["verified", "reported", "assumed"] | None = None


class _ShotOut(BaseModel):
    line: int
    kind: Literal["image", "stat", "chart", "code", "screenshot", "chat", "list", "stock"]
    prompt: str
    query: str | None = None
    stat: _StatOut | None = None
    chart: _ChartOut | None = None
    code: _CodeOut | None = None
    chat: _ChatOut | None = None
    list: _ListOut | None = None
    url: str | None = None
    highlight: str | None = None


class _OverlayOut(BaseModel):
    line: int
    text: str


class ScriptOut(BaseModel):
    """Schema output của vai scriptwriter — SDK ép LLM trả đúng hình này
    (`output_format`), nên không còn bóc JSON khỏi văn bản bằng regex.

    Chỉ ràng buộc HÌNH. Ràng buộc nội dung (đếm từ, cấm số trần, caption ≤ 150…)
    vẫn ở `_check` — code, không để schema/LLM tự chấm.
    """

    hook: str
    hook_text: str
    hook_type: Literal[HOOK_TYPES]  # type: ignore[valid-type]
    pillar: str           # Literal theo kênh — `_script_model()`
    sections: list[str]
    cta: str
    shots: list[_ShotOut]
    overlays: list[_OverlayOut] = []
    # Khai đủ trường: dict tự do để LLM thêm "note" → spec schema từ chối (2026-10-02).
    sources: list[_SourceOut] = []
    keywords: list[str]
    caption: str
    hashtags: list[str]
    emphasis: list[str] = []
    pin_comment: str = ""


def _script_model() -> type[ScriptOut]:
    """ScriptOut với pillar + kind là Literal CỦA KÊNH đang chạy (SDK ép LLM chọn trong danh sách)."""
    from pydantic import create_model

    from ..channel import current

    kinds = current().shot_kinds
    shot = create_model("_ShotOut", __base__=_ShotOut, kind=(Literal[kinds], ...))  # type: ignore[valid-type]
    return create_model("ScriptOut", __base__=ScriptOut,
                        pillar=(Literal[_pillars()], ...),  # type: ignore[valid-type]
                        shots=(list[shot], ...))


def _bare_numbers(line: str) -> list[str]:
    """Số viết bằng chữ số mà KHÔNG thuộc tên riêng.

    Hai dạng được tha, vì cả hai đều là tên thật của thứ đang nói tới:

    - dính vào chữ: `Qwen3-VL`, `GPT-5`, `SDXL`
    - đứng sau một từ viết hoa: `Claude Opus 5`, `Gemini 3 Pro`

    Còn `"Nó nhanh hơn 15 lần"` thì bị bắt — đó là số trong lời văn, và TTS sẽ
    đọc thành "mười lăm" (một token thành hai), làm phụ đề mất mốc đo được.
    """
    out: list[str] = []
    toks = line.split()
    for j, tok in enumerate(toks):
        core = tok.strip(".,!?:;()\"'")
        if not core or not core.replace(",", "").replace(".", "").isdigit():
            continue
        prev = toks[j - 1].strip(".,!?:;()\"'") if j else ""
        if j >= 1 and prev[:1].isupper():
            # tên riêng: "Opus 5", "Gemini 3 Pro". Nhận cả khi tên đứng đầu câu
            # ("Gemini 3 Pro cũng vậy") — đổi lại là thỉnh thoảng tha nhầm
            # ("Card 6 GB"). Chọn lệch về phía THA có chủ ý: bắt oan tốn nguyên
            # một vòng gọi LLM (~5 phút), còn tha nhầm chỉ làm một câu phụ đề
            # rơi về đường "redistributed".
            continue
        out.append(core)
    return out


def _check(script: Script) -> list[str]:
    """Kiểm ràng buộc kỹ thuật bằng CODE, không hỏi lại LLM.

    Cùng tinh thần với QC tầng 1: cái gì đo được thì đừng để model tự chấm.
    """
    problems: list[str] = []
    # Cấm số ĐỨNG MỘT MÌNH ("15", "2060", "6") và ký hiệu %, nhưng CHO PHÉP số
    # nằm trong tên riêng ("Qwen3-VL", "GPT-5", "Claude Opus 5"). Cấm tuốt là
    # cấm luôn việc gọi đúng tên model — mà đó chính là nội dung của kênh.
    # Cái giá phải trả: những câu có tên model sẽ rơi vào đường "redistributed"
    # của spec/captions.py. Đã cân nhắc, chấp nhận.
    for i, line in enumerate(script.lines):
        n = len(line.split())
        if "%" in line:
            problems.append(f"câu {i} có ký hiệu %, viết thành 'phần trăm': {line!r}")
        for tok in _bare_numbers(line):
            problems.append(f"câu {i} có số {tok!r} viết bằng chữ số: {line!r}")
        if not (MIN_WORDS <= n <= MAX_WORDS):
            problems.append(f"câu {i} dài {n} từ, ngoài khoảng {MIN_WORDS}-{MAX_WORDS}: {line!r}")
    if len(script.hook.split()) > 12:
        problems.append(f"hook {len(script.hook.split())} từ — quá dài cho 3 giây")
    if script.hook_text or script.pillar:   # script kiểu Phase V (cũ không có các trường này)
        n_ht = len(script.hook_text.split())
        if not (2 <= n_ht <= HOOK_TEXT_MAX_WORDS):
            problems.append(f"hook_text {script.hook_text!r} có {n_ht} từ — cần 2-{HOOK_TEXT_MAX_WORDS}")
        if script.hook_text.strip().lower() == script.hook.strip().lower():
            problems.append("hook_text trùng lời hook — phải là tiêu đề ngắn KHÁC lời, cùng ý")
    if re.search(r"(tạm biệt|hẹn gặp lại|cảm ơn (các bạn )?đã xem|bye)", script.cta, re.I):
        problems.append(f"CTA chào tạm biệt — kết ở đỉnh, nối lại hook: {script.cta!r}")
    # Ảnh AI gần trùng nhau: chuyển sang `_check_visual_soft` (2026-10-06) — xem ở đó.
    for j, sh in enumerate(script.shots):
        if sh.kind == "image" and _people_in(sh.prompt):
            problems.append(f"shot {j} (image): prompt có người ({_people_in(sh.prompt).group(0)!r}) — "
                            "kênh không dùng mặt/dáng người AI, dùng đồ vật/biểu tượng")
    if not script.shots:
        problems.append("không có shot nào")
    seen: set[int] = set()
    for o in script.overlays:
        i, t = o["line"], o["text"]
        if not (0 <= i < len(script.lines)):
            problems.append(f"overlay {t!r} trỏ tới câu {i}, ngoài khoảng 0-{len(script.lines) - 1}")
        if i in seen:
            problems.append(f"câu {i} có hơn một overlay")
        seen.add(i)
        if not t or len(t) > OVERLAY_MAX_CHARS:
            problems.append(f"overlay {t!r} dài {len(t)} ký tự, trần {OVERLAY_MAX_CHARS}")
    problems.extend(_check_metadata(script))
    problems.extend(_check_shots(script))
    problems.extend(_check_speech(script))
    problems.extend(_check_visual_soft(script))
    problems.extend(_check_emphasis(script))
    return problems


def _check_emphasis(script: Script) -> list[str]:
    """P3b.S5: cụm nhấn phải có NGUYÊN VĂN trong lời đọc — không thì không nhấn được
    gì (khớp theo từ trên phụ đề), và LLM nhấn thứ nó tưởng là đã viết."""
    import re

    def norm(x: str) -> str:
        return " ".join(re.sub(r"[^\w\s-]", " ", x.lower()).split())

    spoken = norm(" ".join(script.lines))
    problems = [f"emphasis {e!r} không có nguyên văn trong lời đọc" for e in script.emphasis
                if norm(e) and f" {norm(e)} " not in f" {spoken} "]
    if len(script.emphasis) > 6:
        problems.append(f"{len(script.emphasis)} cụm emphasis — tối đa 6, nhấn nhiều thì không gì nổi bật")
    return problems


EVIDENCE_KINDS = ("stat", "chart", "code", "screenshot", "chat", "list")
CHAT_MAX_CHARS, LIST_MAX_CHARS, CARD_TITLE_MAX = 60, 34, 32   # khớp spec/schema.json

# Từ tiếng Việt hay gặp khi bị viết mất dấu. Demo P3b.S4 đầu tiên (2026-10-01) ra
# "VRAM dinh so voi dung luong card", "Khi chay offload" — LLM lây kiểu không dấu
# của hashtag sang chữ trên hình.
_UNACCENTED = {
    "dinh", "so", "voi", "dung", "luong", "mot", "dong", "doi", "tat", "ca", "khi", "chay",
    "cua", "cho", "nhanh", "cham", "giay", "anh", "trung", "binh", "moi", "bo", "nho", "toc",
    "do", "nguoi", "duoc", "khong", "thay", "the", "nay", "tren", "duoi", "hon", "lan", "sau",
}


def _screen_texts(sh: "Shot") -> list[str]:
    out: list[str] = []
    if sh.stat:
        out.append(str(sh.stat.get("label", "")))
    if sh.chart:
        out.append(str(sh.chart.get("title", "")))
        out += [str(b.get("label", "")) for b in sh.chart.get("bars", [])]
    if sh.code and " " in str(sh.code.get("title") or ""):
        out.append(str(sh.code["title"]))
    for blk, key in ((sh.chat, "messages"), (sh.list, "items")):
        if blk:
            out += [str(blk.get("title") or "")] + [str(x.get("text", "")) for x in blk.get(key) or []]
    return out


def _looks_unaccented(text: str) -> bool:
    """Chuỗi toàn ASCII có ≥ 2 từ nằm trong `_UNACCENTED` → nhiều khả năng mất dấu.

    Tên riêng/thuật ngữ Anh ("RTX 2060", "SDXL base") không chạm danh sách nên lọt.
    """
    if not text.isascii():
        return False
    words = [w.strip(".,:;()").lower() for w in text.split()]
    return sum(w in _UNACCENTED for w in words) >= 2


def _check_shots(script: Script) -> list[str]:
    """P3b.S4: shot bằng chứng — kiểm bằng code, cùng giới hạn với spec/schema.json.

    Chỉ áp cho script kiểu mới (shot có `line`). Script cũ vẫn qua cổng như trước,
    để `out/` cũ dựng lại được.
    """
    from ..visual.screenshot import target_for

    if not any(sh.line is not None for sh in script.shots):
        return []
    problems: list[str] = []
    n_lines = len(script.lines)
    seen: set[int] = set()
    for j, sh in enumerate(script.shots):
        tag = f"shot {j} ({sh.kind}, câu {sh.line})"
        if sh.line is None or not (0 <= sh.line < n_lines):
            problems.append(f"{tag}: `line` phải trong 0-{n_lines - 1}")
            continue
        if sh.line in seen:
            problems.append(f"{tag}: câu {sh.line} đã có shot khác — mỗi câu tối đa một shot")
        seen.add(sh.line)
        if not sh.prompt.strip():
            problems.append(f"{tag}: thiếu `prompt` (shot bằng chứng cũng cần, làm ảnh dự phòng)")
        if sh.kind == "stat":
            st = sh.stat or {}
            if "value" not in st or not st.get("label"):
                problems.append(f"{tag}: stat cần `value` và `label`")
            elif len(st["label"]) > 40 or len(st.get("unit") or "") > 8:
                problems.append(f"{tag}: label ≤ 40, unit ≤ 8 ký tự")
        elif sh.kind == "chart":
            bars = (sh.chart or {}).get("bars") or []
            if not (sh.chart or {}).get("title") or not (2 <= len(bars) <= 6):
                problems.append(f"{tag}: chart cần `title` và 2-6 cột, có {len(bars)}")
            if sum(bool(b.get("highlight")) for b in bars) != 1:
                problems.append(f"{tag}: chart cần đúng MỘT cột highlight")
            for b in bars:
                if len(str(b.get("label", ""))) > 18 or float(b.get("value", -1)) < 0:
                    problems.append(f"{tag}: cột {b.get('label')!r} — nhãn ≤ 18 ký tự, giá trị ≥ 0")
        elif sh.kind == "code":
            lines = (sh.code or {}).get("lines") or []
            if not (1 <= len(lines) <= 12) or any(len(x) > 40 for x in lines):
                problems.append(f"{tag}: code 1-12 dòng × ≤ 40 ký tự (đọc được ở 1080px)")
        elif sh.kind == "screenshot":
            if not sh.url or target_for(sh.url) is None:
                problems.append(
                    f"{tag}: url {sh.url!r} ngoài danh sách cho phép (trang trong đề bài · "
                    "huggingface.co/<org>/<model> · github.com/<owner>/<repo> · arxiv.org/abs/<id>)"
                )
        elif sh.kind == "chat":
            msgs = (sh.chat or {}).get("messages") or []
            if not (2 <= len(msgs) <= 5):
                problems.append(f"{tag}: chat cần 2-5 tin nhắn, có {len(msgs)}")
            for m in msgs:
                if m.get("from") not in ("me", "them") or not str(m.get("text", "")).strip():
                    problems.append(f"{tag}: tin nhắn cần `from` me|them và `text`")
                elif len(m["text"]) > CHAT_MAX_CHARS:
                    problems.append(f"{tag}: tin {m['text']!r} dài {len(m['text'])} ký tự, trần {CHAT_MAX_CHARS}")
            if len(str((sh.chat or {}).get("title") or "")) > CARD_TITLE_MAX:
                problems.append(f"{tag}: title ≤ {CARD_TITLE_MAX} ký tự")
        elif sh.kind == "list":
            items = (sh.list or {}).get("items") or []
            if not (2 <= len(items) <= 5):
                problems.append(f"{tag}: list cần 2-5 mục, có {len(items)}")
            for it in items:
                t = str(it.get("text", ""))
                if not t.strip() or len(t) > LIST_MAX_CHARS:
                    problems.append(f"{tag}: mục {t!r} — 1-{LIST_MAX_CHARS} ký tự")
            if len(str((sh.list or {}).get("title") or "")) > CARD_TITLE_MAX:
                problems.append(f"{tag}: title ≤ {CARD_TITLE_MAX} ký tự")
        elif sh.kind == "stock":
            q = (sh.query or "").strip()
            if not (2 <= len(q.split()) <= 8) or not q.isascii():
                problems.append(f"{tag}: stock cần `query` tiếng Anh 2–8 từ, có {q!r}")
        if sh.kind not in ("image", "stock", *evidence_kinds()):
            problems.append(f"{tag}: kênh này không dùng kind {sh.kind!r}")
        for txt in _screen_texts(sh):
            if _looks_unaccented(txt):
                problems.append(f"{tag}: {txt!r} trông như tiếng Việt KHÔNG DẤU — chữ trên hình phải có dấu")
    n_ev = sum(sh.kind in EVIDENCE_KINDS for sh in script.shots)
    need = max(2, -(-len(script.shots) // 3))
    if n_ev < need:
        problems.append(
            f"chỉ {n_ev} shot bằng chứng ({'/'.join(evidence_kinds())}) trên {len(script.shots)} "
            f"shot — cần ≥ {need} (≥ 1/3)"
        )
    # Chụp trùng trang (≤ 2 lần, không liền nhau — 2026-10-05): chuyển sang `_check_visual_soft` + tự vá (2026-10-08).
    # R4 (2026-10-04): kênh khai `rules.image_min_ratio` → đủ ảnh/cảnh thật, không thành "trình chiếu thẻ chữ"
    # (demo kênh mẹo: 83% thời lượng là thẻ — research/14 §0).
    from ..channel import current

    r_img = float(current().flag("image_min_ratio", 0) or 0)
    n_img = sum(sh.kind in ("image", "stock") for sh in script.shots)   # cảnh quay thật cũng là "cảnh thật"
    if r_img and n_img < r_img * len(script.shots) - 1e-9:
        problems.append(f"chỉ {n_img} shot ảnh trên {len(script.shots)} — kênh này cần ≥ {r_img:.0%} là ảnh cảnh thật "
                        "(thẻ chữ chỉ ở chỗ cần số/danh sách/hội thoại)")
    r_real = float(current().flag("real_min_ratio", 0) or 0)
    n_real = sum(sh.kind == "stock" for sh in script.shots)
    if r_real and "stock" in current().shot_kinds and n_real < r_real * len(script.shots) - 1e-9:
        problems.append(f"chỉ {n_real} shot `stock` trên {len(script.shots)} — kênh này cần ≥ {r_real:.0%} là cảnh quay/ảnh "
                        "chụp THẬT; đổi các shot `image` tả cảnh đời thực sang `stock` (query tiếng Anh)")
    # Chụp trùng trang (≤ 2 lần, không liền nhau — 2026-10-05): chuyển sang `_check_visual_soft` + tự vá (2026-10-08).
    return problems


# V7 (2026-10-05, research/19): dấu hiệu văn AI — Wikipedia "Signs of AI writing" (2026-08), Brands Vietnam (2025-09),
# Russell et al. 2025 (người dùng ChatGPT nhiều nhận ra qua từ vựng + cấu trúc "không chỉ… mà còn", liệt kê 3 vế).
AI_TELLS = ("không chỉ", "hơn nữa", "thêm vào đó", "đáng chú ý", "bạn có biết", "hãy cùng", "tóm lại", "trong bối cảnh",
            "đóng vai trò", "vô cùng quan trọng", "không thể phủ nhận")
SPOKEN_MARKERS = ("nhé", "nha", "đấy", "đó", " à", "luôn", "thôi", " mà", "thì", "nói gọn", "thế là", "để ý",
                  "vấn đề là", "khoan", "còn nữa", "này")
MIN_LEN_CV = 0.35   # độ lệch chuẩn / trung bình số từ mỗi câu thân bài; 2 kịch bản 2026-10-05 đo được 0,09 (đều tăm tắp)


# chỉ mẫu "đẩy đáp án sang hình" — không bắt "trên màn hình" (mẹo điện thoại dùng hợp lệ)
META_SCREEN = re.compile(r"(lên hình|trên hình (đây|này|kia)|bạn (tự )?đọc (là|một|hai|trên)|chụp (nguyên )?trang|"
                         r"để nguyên lên|nhìn hình)")
HOOK_WHO = re.compile(r"\b(bạn|mọi người|ai|phụ huynh|bố mẹ|cha mẹ|người|dân|sinh viên|chị em|anh em|nhà mình|nhà bạn)\b")
HOOK_NUM = re.compile(r"\d|\b(một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười|trăm|nghìn|ngàn|triệu|tỉ|tỷ)\b")
# Vật bản chất là chữ/số — ảnh AI vẽ méo dù ghi "blank" (research/21 §8 C6).
TEXTY = re.compile(r"\b(thermometers?|clocks?|watch(es)?|calendars?|books?|newspapers?|menus?|signs?|signboards?|"
                   r"receipts?|keyboards?|dials?|gauges?|rulers?|price tags?|posters?|scoreboards?|"
                   # v9 2026-10-07: vẽ lại 2 vòng vẫn chữ méo — màn hình có giao diện, giấy tờ, con dấu
                   r"message list|messages|browser|website|web page|chat window|app interface|notifications?|"
                   r"documents?|forms?|certificates?|letters?|stamps?|seals?|invoices?|contracts?)\b", re.I)
CARD_KINDS = ("stat", "chart", "list", "chat", "code")
CARD_MAX_WORDS = 15


def _card_spans(script: Script) -> list[tuple[int, int, int]]:
    """(chỉ số shot thẻ, câu kế tiếp KHÔNG có shot, tổng số từ thẻ phải phủ) — thẻ phủ cả các câu sau nó cho tới shot kế."""
    lines = list(script.lines)
    anchored = {sh.line for sh in script.shots if sh.line is not None}
    out = []
    for j, sh in enumerate(script.shots):
        if sh.kind not in CARD_KINDS or sh.line is None or not (0 <= sh.line < len(lines)):
            continue
        k, words = sh.line, len(lines[sh.line].split())
        while k + 1 < len(lines) and (k + 1) not in anchored:
            k += 1
            words += len(lines[k].split())
        # 15 từ (v2 2026-10-08): thẻ phủ 15–18 từ vẫn đứng 6,4s khi đọc chậm (3,4 từ/giây) — 15 từ ≈ 4,4s ở tốc độ chậm nhất
        if words > CARD_MAX_WORDS and k > sh.line:
            out.append((j, sh.line + 1, words))
        elif words > CARD_MAX_WORDS:
            out.append((j, -1, words))
    return out


def _dup_screens(script: Script) -> list[int]:
    """Chỉ số shot screenshot THỪA: cùng URL với shot liền trước, hoặc lần chụp thứ 3+ của một URL."""
    order = sorted(range(len(script.shots)), key=lambda j: (script.shots[j].line if script.shots[j].line is not None else 0))
    seen: dict[str, int] = {}
    prev = (None, None)
    out = []
    for j in order:
        sh = script.shots[j]
        if sh.kind == "screenshot" and sh.url:
            seen[sh.url] = seen.get(sh.url, 0) + 1
            if prev == ("screenshot", sh.url) or seen[sh.url] > 2:
                out.append(j)
        prev = (sh.kind, sh.url)
    return out


def _autofix_visual(script: Script) -> list[str]:
    """Lần thử cuối vẫn còn lỗi hình MỀM → code tự vá (2026-10-07, research/21 §8 C3/C6), trả danh sách đã vá.
    - thẻ phủ đoạn lời > 18 từ: thêm shot ảnh ở câu kế (prompt dự phòng của chính thẻ) — thẻ không zoom được (vùng an toàn);
    - ảnh AI vẽ vật bản chất là chữ: đổi sang `stock` (ảnh chụp thật — chữ là chữ thật), query lấy từ prompt."""
    done = []
    for j in _dup_screens(script):
        sh = script.shots[j]
        sh.kind = "image" if not (TEXTY.search(sh.prompt or "") or _people_in(sh.prompt)) else "stock"
        if sh.kind == "stock":
            sh.query = " ".join(re.findall(r"[a-zA-Z]+", sh.prompt)[:6])
        done.append(f"shot {j}: chụp trùng trang → {sh.kind}")
    for j, nxt, words in _card_spans(script):
        if nxt >= 0:
            card = script.shots[j]
            script.shots.append(Shot(prompt=card.prompt, kind="image", line=nxt))
            done.append(f"thẻ shot {j} phủ {words} từ → thêm ảnh ở câu {nxt}")
    for j, sh in enumerate(script.shots):
        if sh.kind == "image" and TEXTY.search(sh.prompt or ""):
            sh.kind, sh.query = "stock", " ".join(re.findall(r"[a-zA-Z]+", sh.prompt)[:6])
            done.append(f"shot {j}: ảnh AI vật có chữ → stock «{sh.query}»")
    script.shots.sort(key=lambda x: (x.line if x.line is not None else 10**6))
    return done


def _check_visual_soft(script: Script) -> list[str]:
    """Kiểm hình loại MỀM — vẫn bắt sửa, nhưng lần thử cuối không làm hỏng cả video (research/21 §8)."""
    problems = [f"shot {j} (image): vẽ vật bản chất là chữ/số ({TEXTY.search(sh.prompt).group(0)!r}) — model ảnh vẽ chữ "
                "méo; đổi sang `stock` hoặc thẻ `stat`"
                for j, sh in enumerate(script.shots) if sh.kind == "image" and TEXTY.search(sh.prompt or "")]
    # `prompt` của shot KHÔNG phải image (stock, thẻ) là ảnh AI DỰ PHÒNG — vẽ ra khi không tìm được cảnh quay / dựng hỏng.
    # Nó cũng phải an toàn cho ảnh AI (v10 2026-10-07: stock "document stack flipped hand" không có clip → vẽ "printed paper
    # documents… by a hand" → chữ méo, còn sót sau QC; research/21 §8 C6).
    for j, sh in enumerate(script.shots):
        if sh.kind != "image" and (TEXTY.search(sh.prompt or "") or _people_in(sh.prompt)):
            what = (TEXTY.search(sh.prompt or "") or _people_in(sh.prompt)).group(0)
            problems.append(f"shot {j} ({sh.kind}): `prompt` (ảnh AI dự phòng) có {what!r} — prompt dự phòng phải không người, "
                            "không vật có chữ (query stock thì được có tay/người)")
    # Thẻ phủ đoạn lời dài → một khung đứng > 6s (v6/v9 2026-10-07: thẻ stat 9,5s / 7,7s — thẻ phủ cả câu sau không có shot).
    for j, nxt, words in _card_spans(script):
        problems.append(f"shot {j} ({script.shots[j].kind}) phải phủ {words} từ lời đọc (> {CARD_MAX_WORDS}) — thẻ đứng một khung quá lâu; "
                        + (f"thêm shot ảnh ở câu {nxt}" if nxt >= 0 else "gắn thẻ vào câu ngắn hơn hoặc tách câu"))
    # Chụp trùng trang: 2026-10-05 (demo v2 AI: 7/14 shot cùng một trang). Cứng → mềm + tự vá 2026-10-08 (AI-2 lô 2 CHẾT ở cổng
    # kịch bản vì "hai shot liền nhau cùng chụp" — lỗi bố cục code vá được, không đáng bỏ cả video).
    for j in _dup_screens(script):
        problems.append(f"shot {j} (screenshot) chụp lại trang {script.shots[j].url} (liền shot trước hoặc quá 2 lần) — "
                        "thay bằng thẻ list/stat/ảnh minh hoạ ý đó")
    # v2 (2026-10-02): ba shot liền nhau cùng "giấy trắng trên bàn" — hình lặp là slop. Prompt ảnh AI trùng ≥ 60% từ nội
    # dung với một ảnh AI khác → bắt viết lại. Cứng → mềm 2026-10-06: video thử v2 CHẾT ở cổng kịch bản vì 2 prompt hộp
    # đựng na ná sau lần sửa T3 — lỗi thẩm mỹ không đáng bỏ cả video (QC T2 còn bắt ảnh trùng bằng dhash).
    imgs = [(j, set(re.findall(r"[a-z]{4,}", (sh.prompt or "").lower())) - _STOP)
            for j, sh in enumerate(script.shots) if sh.kind == "image"]
    for (a_j, a_w), (b_j, b_w) in ((x, y) for i, x in enumerate(imgs) for y in imgs[i + 1:]):
        if a_w and b_w and len(a_w & b_w) / min(len(a_w), len(b_w)) >= 0.6:
            problems.append(f"shot {a_j} và shot {b_j} (image): prompt gần trùng nhau — mỗi ảnh một vật/cảnh khác hẳn")
    return problems


# token có ≥ 2 dấu gạch/chấm nối chữ-số ("Qwen3.8-Flash-Next", "a.b.c") hoặc đuôi tên file (".bat", ".py") — research/21 §4
TECH_TOKEN = re.compile(r"\b\w+(?:[-.]\w+){2,}\b|\b\w+\.(?:bat|exe|py|sh|json|yaml|txt|zip|apk|gguf|safetensors)\b")


def _check_speech(script: Script) -> list[str]:
    """Văn nói (V1–V7) — đo bằng code: dấu hiệu văn AI, độ chênh độ dài câu, từ nối/tiểu từ văn nói."""
    import statistics as _st

    problems: list[str] = []
    lines = list(script.lines)
    for i, ln in enumerate(lines):
        low = ln.lower()
        hit = [t for t in AI_TELLS if t in low]
        if hit or "—" in ln:
            problems.append(f"câu {i} có dấu hiệu văn AI ({', '.join(hit + (['gạch ngang —'] if '—' in ln else []))}) — "
                            f"nói lại như người kể: {ln!r}")
    body = [len(x.split()) for x in script.sections]
    if len(body) >= 5:
        cv = _st.pstdev(body) / max(_st.mean(body), 1)
        if cv < MIN_LEN_CV:
            problems.append(f"độ dài câu đều tăm tắp ({min(body)}–{max(body)} từ, độ chênh {cv:.2f} < {MIN_LEN_CV}) — "
                            "nghe như đọc gạch đầu dòng; xen câu 2–5 từ chốt ý với câu 18–25 từ nối bằng thì/mà/nên/rồi (V1)")
    spoken = sum(any(m in f" {x.lower()}" for m in SPOKEN_MARKERS) for x in lines)
    need = max(2, len(lines) // 4)
    if spoken < need:
        problems.append(f"chỉ {spoken} câu có từ nối/tiểu từ văn nói (nhé, đấy, thì, mà, thế là…) — cần ≥ {need} (V2–V3)")
    # 2026-10-06 (research/21 §4) — hai lỗi thấy ở 5 video của kênh:
    # chữ bìa chép lại lời hook → cùng một câu hiện 3 lần trong 3s đầu (tiêu đề, phụ đề, giọng), phí chỗ cho ý thứ hai.
    hw = set(re.findall(r"\w+", script.hook_text.lower()))
    if len(hw) >= 3 and len(hw & set(re.findall(r"\w+", script.hook.lower()))) / len(hw) >= 0.8:
        problems.append(f"hook_text {script.hook_text!r} gần như chép lời hook — chữ bìa phải BỔ SUNG một ý (con số, "
                        "lợi ích, câu hỏi), không lặp lại câu đang được đọc (H2)")
    # hook đọc một hơi (research/21 §8 B3/B6): ≤ 1 dấu phẩy, không mở bằng từ đơn + dấu phẩy.
    if script.hook.count(",") > 1 or re.match(r"\s*\w+\s*,", script.hook):
        problems.append(f"hook {script.hook!r} bị ngắt vụn — tối đa một dấu phẩy, không mở bằng một từ đơn rồi ngắt (H)")
    # hook có người hoặc số (research/21 §8 A1 — video thử v2 "Chờ nồi canh nguội hẳn mới cất tủ lạnh là sai rồi" thiếu cả hai)
    if not (HOOK_WHO.search(script.hook.lower()) or HOOK_NUM.search(script.hook.lower())):
        problems.append(f"hook {script.hook!r} không có người xem/nhóm người cũng không có con số — thêm 'bạn' hoặc đối "
                        "tượng cụ thể, hoặc một con số (H)")
    # chỗ ngoặt "Nhưng…" ở 40–75% lời đọc (J) — v4 2026-10-07 không có câu nào dù luật có trong prompt (§8 A4)
    if len(lines) >= 6:
        tot = sum(len(x.split()) for x in lines)
        pos, ok = 0, False
        for ln in lines:
            # rà soát 2026-10-10: D7/J cho phép ngoặt CÙNG HƯỚNG ("Nguy hiểm hơn là…") — code từng chỉ nhận "Nhưng"
            if re.match(r"\s*(nhưng|nguy hiểm hơn|thực ra|thật ra|còn đáng lo hơn|điều ít ai biết)\b", ln.lower()) \
                    and 0.40 <= pos / max(tot, 1) <= 0.75:
                ok = True
            pos += len(ln.split())
        if not ok:
            problems.append("không có chỗ ngoặt (\"Nhưng…\", \"Nguy hiểm hơn là…\", \"Thật ra…\") ở khoảng 40–75% lời đọc — thêm ở giữa video (J)")
    # đẩy đáp án sang hình (G2)
    for i, ln in enumerate(lines):
        if META_SCREEN.search(ln.lower()):
            problems.append(f"câu {i} bắt người xem tự đọc trên hình ({META_SCREEN.search(ln.lower()).group(0)!r}) — "
                            "đọc thẳng con số/đáp án ra (G2)")
    # chuỗi kỹ thuật trong LỜI ĐỌC → TTS đọc "gạch nối flash gạch nối next" (4/5 video dính lỗi phát âm).
    for i, ln in enumerate(lines):
        bad = [t for t in TECH_TOKEN.findall(ln) if not re.fullmatch(r"[\d.,]+", t)]
        if bad:
            problems.append(f"câu {i} đọc chuỗi kỹ thuật {', '.join(bad)!s} — nói tên ngắn, để tên đầy đủ trên hình (L)")
    return problems


def _check_metadata(script: Script) -> list[str]:
    """P3.S5: caption/hashtag/keywords — cùng nguyên tắc với `_check`, đo bằng
    code chứ không hỏi lại LLM có "ổn" không."""
    problems: list[str] = []
    if not script.caption:
        problems.append("thiếu caption")
    elif len(script.caption) > 150:
        problems.append(f"caption dài {len(script.caption)} ký tự, vượt trần 150")

    if not (3 <= len(script.hashtags) <= 5):
        problems.append(f"có {len(script.hashtags)} hashtag, cần đúng 3-5")
    for h in script.hashtags:
        bare = h.lstrip("#").lower()
        if bare in {"fyp", "viral"}:
            problems.append(f"hashtag {h!r} bị cấm — #fyp/#viral quá chung, TikTok hạ ưu tiên")
        if not re.fullmatch(r"[a-z0-9_]+", bare):
            problems.append(f"hashtag {h!r} sai định dạng — chỉ chữ thường/số/gạch dưới, không khoảng trắng")

    if not script.keywords:
        problems.append("thiếu keywords")
    elif script.caption and script.keywords[0].lower() not in script.caption[:100].lower():
        problems.append(
            f"từ khoá chính {script.keywords[0]!r} không nằm trong 100 ký tự đầu của caption"
        )
    return problems


async def write_script(
    topic: str,
    *,
    brief: str | None = None,
    duration_sec: int = 45,
    model: str | None = None,
    max_retry: int = 1,
    state: "State | None" = None,
    artifact: Path | None = None,
    end_style: str = "",
) -> Script:
    """Chạy vai scriptwriter qua `run_role` (P4.S0) rồi qua cổng `_check` bằng code.

    Không tool: đây là việc viết, không phải việc tra. Cho tool vào chỉ làm agent
    đi đọc file lung tung và tốn vòng.
    """
    prompt = f"Viết kịch bản cho chủ đề: {topic}"
    if brief:
        # Phase V2: sự thật đã qua cổng code của researcher (agents/researcher.py).
        prompt = f"Viết kịch bản theo ĐỀ BÀI dưới đây.\n\n{brief}"
    return await _write(
        topic, prompt, role="scriptwriter",
        duration_sec=duration_sec, model=model, max_retry=max_retry, state=state, artifact=artifact,
        end_style=end_style,
    )


async def revise_script(
    script: Script,
    notes: list[str],
    *,
    duration_sec: int = 45,
    model: str | None = None,
    max_retry: int = 1,
    state: "State | None" = None,
    artifact: Path | None = None,
) -> Script:
    """P4.S2: sửa kịch bản theo lỗi CỤ THỂ của critic (`qc.t3_appeal.revision_notes`).

    Producer sửa, critic chỉ chỉ chỗ — tách vai đúng nguyên tắc 1 của P4. Gửi NGUYÊN
    bản cũ (context mới không nhớ gì) và chỉ những lỗi đã nêu: "tự sửa không có tín
    hiệu ngoài làm tệ đi" (research/10 §5), nên tuyệt đối không "viết hay hơn".
    """
    if not notes:
        return script
    data = json.loads(script.to_json())
    data.pop("topic", None)
    data.pop("end_style", None)
    prompt = (
        f"Chủ đề: {script.topic}\n\nBiên tập viên chỉ ra các lỗi CÁCH KỂ dưới đây trong kịch bản:\n"
        + "\n".join(f"- {n}" for n in notes)
        + "\n\nSửa ĐÚNG những chỗ đó. Giữ nguyên mọi câu, shot, nguồn không bị nêu — kể cả "
        "khi bạn nghĩ viết khác sẽ hay hơn. Đổi câu nào thì cập nhật `line` của shot/overlay "
        "và `emphasis` cho khớp. Không thêm số liệu mới.\n\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
    )
    return await _write(
        script.topic, prompt, role="scriptwriter_revise",
        duration_sec=duration_sec, model=model, max_retry=max_retry, state=state, artifact=artifact,
        end_style=script.end_style,
    )


async def _write(
    topic: str, prompt: str, *, role: str, duration_sec: int, model: str | None,
    max_retry: int, state: "State | None", artifact: Path | None, end_style: str = "",
) -> Script:
    from ..team import arun_role

    system = _system_prompt(duration_sec)
    last_problems: list[str] = []

    for attempt in range(max_retry + 1):
        out = await arun_role(
            role, prompt, _script_model(),
            system_prompt=system, tools=[], max_turns=6, max_budget_usd=2.0,
            model=model, state=state,
        )
        data = out.model_dump(by_alias=True)
        script = Script.from_dict(data, topic=topic)
        script.end_style = end_style
        problems = _check(script) + _check_length(script, duration_sec)
        soft = set(_check_speech(script)) | set(_check_visual_soft(script)) | set(_check_length(script, duration_sec))
        if problems and attempt == max_retry and set(problems) <= soft:
            patched = Script.from_dict(json.loads(script.to_json()))
            patched.end_style = script.end_style
            fixed = _autofix_visual(patched)
            if fixed:
                left = _check(patched) + _check_length(patched, duration_sec)
                soft2 = set(_check_speech(patched)) | set(_check_visual_soft(patched)) | set(_check_length(patched, duration_sec))
                if set(left) <= soft2:          # vá không sinh lỗi CỨNG mới (vd. tỉ lệ shot bằng chứng) → nhận
                    print("  🔧 tự vá hình: " + " | ".join(fixed), flush=True)
                    script, problems = patched, left
                else:
                    print("  ⚠ tự vá hình sinh lỗi cứng — giữ bản chưa vá: " + " | ".join(set(left) - soft2), flush=True)
            # Văn nói (V1–V7) là tiêu chí chất lượng, không phải ràng buộc kỹ thuật → lần cuối không làm hỏng cả video.
            print("  ⚠ văn nói chưa đạt sau khi thử lại: " + " | ".join(p[:90] for p in problems), flush=True)
            problems = []
        if not problems:
            if artifact is not None:
                artifact.write_text(script.to_json() + "\n", encoding="utf-8")
            return script
        last_problems = problems
        if attempt < max_retry:
            # Mỗi lần gọi là context MỚI, nên phải kèm nguyên kịch bản cũ — bản
            # trước 2026-10-01 chỉ gửi danh sách lỗi, model không thấy bài cũ và
            # thực chất viết lại mù. Nói đúng lỗi, không nói "viết lại cho hay
            # hơn" — sửa mù thì vòng sau hỏng chỗ khác (research/10 §5).
            prompt = (
                f"Chủ đề: {topic}\n\nKịch bản dưới đây vi phạm ràng buộc kỹ thuật:\n"
                + "\n".join(f"- {p}" for p in problems)
                + "\n\nSửa ĐÚNG những chỗ đó, giữ nguyên phần còn lại.\n\n"
                + json.dumps(data, ensure_ascii=False, indent=2)
            )

    raise ValueError(
        "kịch bản vẫn vi phạm ràng buộc sau khi thử lại:\n"
        + "\n".join(f"  - {p}" for p in last_problems)
    )


def write_script_sync(topic: str, **kw) -> Script:
    return asyncio.run(write_script(topic, **kw))


def revise_script_sync(script: Script, notes: list[str], **kw) -> Script:
    return asyncio.run(revise_script(script, notes, **kw))


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="chủ đề → script.json")
    ap.add_argument("topic")
    ap.add_argument("--duration", type=int, default=45)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--model", default=None)
    a = ap.parse_args(argv)

    script = write_script_sync(a.topic, duration_sec=a.duration, model=a.model)
    out = a.out or REPO_ROOT / "out" / "script.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(script.to_json() + "\n", encoding="utf-8")

    print(f"✓ {out}")
    print(f"  hook: {script.hook}")
    for s in script.sections:
        print(f"       {s}")
    print(f"  cta : {script.cta}")
    print(f"  {len(script.shots)} shot · {sum(s.duration_sec for s in script.shots):.0f}s")
    print(f"  caption: {script.caption}")
    print(f"  hashtags: {' '.join('#' + h for h in script.hashtags)}")
    print(f"  keywords: {', '.join(script.keywords)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
