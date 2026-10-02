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
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

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
MIN_WORDS, MAX_WORDS = 5, 16

# Phase V3 (2026-10-02): 20 khuôn hook ở research/11 §4.2 gom thành nhãn để sau 20 video
# đếm được loại nào giữ người xem — không phải để ép LLM viết theo khuôn.
HOOK_TYPES = (
    "con_so_soc", "mau_thuan", "ket_qua_truoc", "demo_truoc", "truoc_sau", "cau_hoi_co_so",
    "canh_bao", "bi_mat", "boc_tin_don", "tu_do", "that_bai", "so_sanh_gia", "in_medias_res",
    "danh_sach", "ban_dang_sai", "thoi_gian", "pha_tuong_4", "doi_dau", "context_snapback",
    "he_qua_nguoi_viet",
)
PILLARS = ("tin_nong", "cong_cu", "meo", "so_sanh", "tu_do", "canh_bao")
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
    kind: str = "image"   # image | stat | chart | code | screenshot
    line: int | None = None
    stat: dict | None = None      # {value, unit?, label, decimals?, prefix?}
    chart: dict | None = None     # {title, unit?, bars: [{label, value, highlight?}]}
    code: dict | None = None      # {lang, title?, lines: [...]}
    url: str | None = None        # screenshot
    highlight: str | None = None  # screenshot: chữ cần tô vàng trên trang


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
                    stat=x.get("stat"), chart=x.get("chart"), code=x.get("code"),
                    url=x.get("url"), highlight=x.get("highlight"),
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
        )


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


def _system_prompt(duration_sec: int) -> str:
    rubric = (REPO_ROOT / "configs" / "rubric.md").read_text(encoding="utf-8")
    return f"""Bạn viết kịch bản video TikTok tiếng Việt về AI cho khán giả Việt Nam PHỔ THÔNG (sinh viên,
dân văn phòng, người làm nội dung — không chỉ dev). Video dọc 1080×1920, dài khoảng {duration_sec} giây,
giọng đọc nam, kênh KHÔNG lộ mặt người dẫn.

ĐỀ BÀI thường kèm "SỰ THẬT ĐÃ KIỂM" (F1, F2…) do researcher tìm và code đã đối chiếu nguồn. Khi có:
CHỈ dùng sự thật trong đó, `sources[].url` lấy đúng url của sự thật đã dùng. Không thêm số ngoài danh sách.

5 GIÂY ĐẦU QUYẾT ĐỊNH TẤT CẢ (research/11: phần lớn người xem lướt đi trong 5s đầu):
H1. `hook` (lời đọc, ≤ 12 từ) đưa THÔNG TIN CỤ THỂ ngay — con số, kết quả, mâu thuẫn. Không chào, không
    bối cảnh, không định nghĩa.
H2. `hook_text` (chữ to trên frame 0, 2–7 từ) KHÁC lời hook nhưng CÙNG MỘT Ý — kiểu tiêu đề báo, đọc
    trong 1 giây. Ví dụ hook "Gemini vừa cho sinh viên Việt Nam dùng bản Pro miễn phí một năm" →
    hook_text "Gemini Pro: 0 đồng". Được dùng chữ số trong hook_text (code vẽ, không đọc).
H3. `hook_type` chọn MỘT: {", ".join(HOOK_TYPES)}.
H4. Shot ở câu 0 NÊN là bằng chứng mang CHỦ ĐỀ (screenshot trang thật, hoặc stat có con số của hook) —
    người xem phải nhận ra video nói về cái gì ngay frame đầu. Ảnh AI ở câu 0 chỉ khi không có bằng chứng.
H5. `pillar` chọn MỘT: {", ".join(PILLARS)} (đề bài có PILLAR thì dùng đúng nó).

Nhịp là thứ quan trọng thứ hai sau hook: không có câu thừa. Bỏ mọi câu chuyển tiếp
kiểu "vậy thì", "như vậy là", "tiếp theo" — chúng ăn thời gian mà không mang thông
tin. Vào thẳng ý. Nhưng câu vẫn phải là câu nói được liền một hơi, không cắt vụn.

RUBRIC — đây chính là thứ critic sẽ dùng để chấm bạn. Đọc kỹ, viết đúng ngay từ đầu:

{rubric}

CUỐN NGƯỜI XEM — thêm 2026-10-02 sau khi Tony xem demo: "video chưa hấp dẫn". Mỗi luật có
bằng chứng ở research/probes/cuon-hon-2026-10-02.md:

A. Hook VÀO GIỮA CHUYỆN, kiểu "khoan, cái gì?": câu đầu là sự thật gây bất ngờ, mâu thuẫn, hoặc
   câu hỏi có con số — người xem phải muốn biết câu trả lời. Không giới thiệu, không dẫn dắt.
B. MỞ MỘT VÒNG TÒ MÒ ở hook, TRẢ LỜI ở khoảng 2/3 video (không để tới câu cuối) — kèm một chỗ
   ngoặt ("nhưng có một điều…") ở giữa.
C. Nói như kể cho bạn: ngôi "tôi" – "bạn", được dùng 1–2 câu hỏi tu từ. NHƯNG chỉ nói "tôi thử / tôi
   đo / tôi vào / tôi chạy" khi đề bài có số đo của chính kênh (`research/probes/`) — thông tin từ trang
   help/công bố thì nói "bạn vào…", "Google ghi…" (2026-10-02: tự nhận đã làm mà chưa làm là nói dối). Năng lượng cao, chắc
   chắn — không rào đón "có thể", "dường như" trừ khi nguồn nói vậy.
D. KẾT VÒNG: câu cuối (CTA) móc lại ý của hook, để người xem muốn xem lại từ đầu.
E. Ảnh minh hoạ (`kind=image`): MỘT chủ thể, ≤ 2 mệnh đề, chủ thể sáng rõ trên NỀN TỐI. KHÔNG tả
   đèn trần, cửa sổ, ngược sáng ở phía trên (mảng trắng chói ở mép trên khung bị QC tầng 1 đọc nhầm
   thành chữ trong vùng UI che — demo-03, 2026-10-02). Prompt ẩn
   dụ nhiều chi tiết làm SDXL hỏng ~nửa số ảnh (P4.S1, P4.S4). **KHÔNG CÓ NGƯỜI** (không mặt, không
   tay, không dáng người — 2026-10-02: mặt người AI là dấu hiệu "AI slop" dễ nhận nhất, và kênh không
   lộ mặt). Dùng đồ vật/biểu tượng cụ thể của chủ đề: điện thoại hiện khung chat, laptop, sách vở, ví
   tiền, đồng hồ, chip, bản đồ Việt Nam… Ảnh AI là phương án CUỐI — có bằng chứng thì dùng bằng chứng.
   Bề mặt có thể mang chữ (giấy, màn hình, biển, sách) phải ghi rõ TRỐNG: "blank paper", "blank glowing
   screen" — model ảnh vẽ chữ méo lên đó (v2, 2026-10-02: QC tầng 2 bắt 4/6 ảnh có chữ méo).
F. KẾT Ở ĐỈNH: câu cuối không chào tạm biệt, không "hẹn gặp lại", không "cảm ơn đã xem".

RÀNG BUỘC KỸ THUẬT — vi phạm là hỏng pipeline, không phải hỏng thẩm mỹ:

1. Số trong lời văn phải viết BẰNG CHỮ: "sáu GB", "ba mươi bảy giây", "mười lăm
   phần trăm" — không viết "6GB", "37 giây", "15%". Lý do: TTS đọc chữ số thành
   nhiều từ hơn số từ hiện trên màn hình, làm phụ đề karaoke mất mốc thời gian.
   NGOẠI LỆ: tên riêng thì giữ NGUYÊN dạng thật của nó — "Qwen3-VL", "GPT-5",
   "Claude Opus 5", "SDXL". Đổi tên model thành chữ là sai tên, tệ hơn nhiều so
   với lệch phụ đề vài chục mili giây.
2. Tên model, tên hãng, thuật ngữ tiếng Anh thì GIỮ NGUYÊN (model, benchmark,
   fine-tune, inference, prompt, open-source, hook, retention).
{_avoid_rule()}
3. Mỗi câu lời đọc {MIN_WORDS}-{MAX_WORDS} từ. Mỗi câu là một dòng phụ đề, và
   mỗi câu chỉ mang MỘT ý. Độ dài câu nên xen kẽ, đừng đều tăm tắp — nhưng
   ĐỪNG cắt vụn thành hàng loạt câu ba bốn từ: mỗi câu được đọc riêng rồi ghép
   lại, nên câu càng ngắn thì giọng đọc càng nhiều chỗ ngắt và càng nghe như máy.
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
   - `code`: đoạn code ≤ 12 dòng × 40 ký tự — {{"lang": "python", "lines": [...]}}.
     CHỈ TRÍCH code có sẵn trong đề bài (được cắt dòng cho vừa, giữ nguyên tên hàm/
     tham số). Đề bài không có code thì KHÔNG dùng kind này — code tự viết trông như
     bằng chứng mà sai là tệ hơn không có.
   - `screenshot`: chụp trang thật — `url` là một trang trong "TRANG CHỤP ĐƯỢC" của đề bài,
     hoặc trang model Hugging Face (huggingface.co/<org>/<model>), repo GitHub
     (github.com/<owner>/<repo>), arxiv.org/abs/<id>; `highlight` (nên có) là cụm chữ CÓ
     NGUYÊN VĂN TRÊN trang cần tô vàng — video cuộn tới đúng chỗ đó. Không bịa URL.
   Rút từ lần tự xem lại demo-03 (2026-10-02):
   - `stat` chỉ cho câu có ĐÚNG MỘT con số. Câu có hai số (giá vào/ra, trước/sau) → dùng `chart`,
     không thì thẻ đứng yên hiện một số trong khi giọng đã đọc sang số khác.
   - `screenshot`: ưu tiên trang model Hugging Face và abstract arXiv (chữ to, đọc được). KHÔNG chụp
     README GitHub dài — chữ tiếng Anh nhỏ, đang cuộn, trên điện thoại không đọc nổi.
   - Shot ở câu CTA (câu cuối) là khung người xem thấy ngay trước khi video lặp lại → dùng thẻ
     `stat`/`chart` tóm lại con số chính, hoặc ảnh MỘT chủ thể thật đơn giản.
   Mọi chữ tiếng Việt trên hình (`label`, `title`, nhãn cột) viết CÓ DẤU đầy đủ —
   chỉ hashtag mới viết không dấu.
   LUẬT: ít nhất {_min_evidence_hint(duration_sec)} shot (và ≥ 1/3 số shot) là
   stat/chart/code/screenshot — hình phải CHỨNG MINH lời nói, không chỉ minh hoạ.
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
   (`keywords[0]` là từ khoá chính). Dùng để chèn vào caption và overlay.
10. `caption`: tối đa 150 ký tự (TikTok cắt hiển thị ở đó) — chứa `keywords[0]`
    trong 100 ký tự đầu. Viết như caption TikTok thật, không phải câu văn trang
    trọng; được chêm 1 emoji hợp ngữ cảnh nếu muốn.
11. `hashtags`: 3-5 hashtag NGÁCH bám sát nội dung video, KHÔNG dùng #fyp #viral
    (quá chung, TikTok hạ ưu tiên). Viết không dấu #, chữ thường liền không dấu
    cách, ví dụ: "sdxl", "aiopensource", "rtx2060".

Output là JSON theo schema đã cho, ý nghĩa từng trường:

{{
  "hook": "một câu",
  "hook_text": "2-7 từ trên frame 0",
  "hook_type": "con_so_soc",
  "pillar": "cong_cu",
  "sections": ["câu", "câu", "..."],
  "cta": "một câu kêu gọi cụ thể",
  "shots": [{{"line": 0, "kind": "image", "prompt": "english scene description"}},
            {{"line": 3, "kind": "stat", "prompt": "fallback scene",
              "stat": {{"value": 6, "unit": "GB", "label": "VRAM của RTX 2060"}}}}],
  "overlays": [{{"line": 2, "text": "16-bit"}}],
  "sources": [{{"claim": "điều đã nói", "url": "nguồn", "confidence": "verified|reported"}}],
  "keywords": ["từ khoá chính", "..."],
  "caption": "caption ngắn chứa từ khoá chính",
  "hashtags": ["ngach1", "ngach2", "ngach3"]
}}"""


class _StatOut(BaseModel):
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


class _SourceOut(BaseModel):
    claim: str
    url: str
    confidence: Literal["verified", "reported", "assumed"] | None = None


class _ShotOut(BaseModel):
    line: int
    kind: Literal["image", "stat", "chart", "code", "screenshot"]
    prompt: str
    stat: _StatOut | None = None
    chart: _ChartOut | None = None
    code: _CodeOut | None = None
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
    pillar: Literal[PILLARS]  # type: ignore[valid-type]
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
    # v2 (2026-10-02): ba shot liền nhau cùng "giấy trắng trên bàn" — hình lặp là slop. Prompt ảnh AI
    # trùng ≥ 60% từ nội dung với một ảnh AI khác → bắt viết lại cho khác hẳn.
    imgs = [(j, set(re.findall(r"[a-z]{4,}", (sh.prompt or "").lower())) - _STOP)
            for j, sh in enumerate(script.shots) if sh.kind == "image"]
    for (a_j, a_w), (b_j, b_w) in ((x, y) for i, x in enumerate(imgs) for y in imgs[i + 1:]):
        if a_w and b_w and len(a_w & b_w) / min(len(a_w), len(b_w)) >= 0.6:
            problems.append(f"shot {a_j} và shot {b_j} (image): prompt gần trùng nhau — mỗi ảnh một vật/cảnh khác hẳn")
    for j, sh in enumerate(script.shots):
        if sh.kind == "image" and _PEOPLE.search(sh.prompt or ""):
            problems.append(f"shot {j} (image): prompt có người ({_PEOPLE.search(sh.prompt).group(0)!r}) — "
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


EVIDENCE_KINDS = ("stat", "chart", "code", "screenshot")

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
        for txt in _screen_texts(sh):
            if _looks_unaccented(txt):
                problems.append(f"{tag}: {txt!r} trông như tiếng Việt KHÔNG DẤU — chữ trên hình phải có dấu")
    n_ev = sum(sh.kind in EVIDENCE_KINDS for sh in script.shots)
    need = max(2, -(-len(script.shots) // 3))
    if n_ev < need:
        problems.append(
            f"chỉ {n_ev} shot bằng chứng (stat/chart/code/screenshot) trên {len(script.shots)} "
            f"shot — cần ≥ {need} (≥ 1/3)"
        )
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
    )


async def _write(
    topic: str, prompt: str, *, role: str, duration_sec: int, model: str | None,
    max_retry: int, state: "State | None", artifact: Path | None,
) -> Script:
    from ..team import arun_role

    system = _system_prompt(duration_sec)
    last_problems: list[str] = []

    for attempt in range(max_retry + 1):
        out = await arun_role(
            role, prompt, ScriptOut,
            system_prompt=system, tools=[], max_turns=6, max_budget_usd=2.0,
            model=model, state=state,
        )
        data = out.model_dump()
        script = Script.from_dict(data, topic=topic)
        problems = _check(script)
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
