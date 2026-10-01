"""Ghép chữ HIỂN THỊ với timestamp của chữ ĐƯỢC ĐỌC.

Vì sao cần cả file này: exp-echo chuẩn hoá text trước khi đọc, và chuẩn hoá
tiếng Việt thì không nhẹ tay. Đo thật 2026-08-14:

    text     : "Con card RTX 2060 sáu GB … không tốn 15% chi phí."
    norm_text: "con card r t x hai nghìn không trăm sáu mươi sáu g b … mười lăm phần trăm chi phí."

Forced aligner phải align theo `norm_text` — đó mới là thứ audio đang đọc. Nhưng
phụ đề thì **không thể** hiện "r t x hai nghìn không trăm sáu mươi": người xem đọc
"RTX 2060". Nên timestamp đến từ chuỗi này, còn chữ hiện lên đến từ chuỗi kia.

Hai đường:

- **exact** — số token khớp nhau, ghép 1-1. Timestamp giữ nguyên độ chính xác của
  aligner. Đây là đường mong muốn, và là lý do agent scriptwriter được dặn viết
  số bằng chữ, tránh ký hiệu.
- **redistributed** — số token lệch (có số/ký hiệu bị bung ra). Chia lại thời gian
  của cả câu cho các token hiển thị theo độ dài chữ. Timestamp lúc này **không
  còn là số đo** trong phạm vi câu đó, chỉ còn đúng ở hai đầu câu.

Đường thứ hai phải được **ghi lại**, không được im lặng: người truy lỗi phụ đề
lệch cần biết mình đang cầm số đo hay số chia.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ..voice.base import Word

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def _key(tok: str) -> str:
    """Chuẩn hoá để SO SÁNH token, không phải để hiển thị."""
    t = unicodedata.normalize("NFC", tok).lower()
    return _PUNCT.sub("", t)


@dataclass
class MappedLine:
    words: list[Word]
    mapping: str  # "exact" | "redistributed"


def map_line(display_text: str, spoken: list[Word]) -> MappedLine:
    """Gán timestamp của `spoken` cho các token của `display_text`."""
    display = display_text.split()
    if not display:
        raise ValueError("câu hiển thị rỗng")
    if not spoken:
        raise ValueError(f"không có timestamp nào cho câu {display_text!r}")

    if len(display) == len(spoken):
        return MappedLine(
            words=[Word(w=d, start=s.start, end=s.end) for d, s in zip(display, spoken)],
            mapping="exact",
        )

    # Số token lệch → chia lại theo độ dài chữ. Dùng độ dài chứ không chia đều
    # vì "Qwen3-VL" tốn nhiều thời gian đọc hơn "và"; chia đều làm từ dài bị
    # tô sáng hụt ngay khi vừa bắt đầu đọc.
    t0, t1 = spoken[0].start, spoken[-1].end
    total = max(t1 - t0, 1e-6)
    weights = [max(len(_key(d)), 1) for d in display]
    wsum = sum(weights)

    out: list[Word] = []
    cursor = t0
    for d, w in zip(display, weights):
        dt = total * w / wsum
        out.append(Word(w=d, start=round(cursor, 3), end=round(cursor + dt, 3)))
        cursor += dt
    out[-1] = Word(w=out[-1].w, start=out[-1].start, end=round(t1, 3))
    return MappedLine(words=out, mapping="redistributed")


def split_spoken_by_lines(
    words: list[Word], spoken_lines: list[str]
) -> list[list[Word]]:
    """Cắt danh sách từ đã align thành từng câu theo `spoken_lines`.

    Aligner nhận nguyên wav đã ghép nên trả một mạch từ; ranh giới câu phải suy
    lại từ chính chuỗi đã gửi đi.

    Đường nhanh: tổng số token khớp → cắt theo chỉ số. Đường lùi (2026-10-01):
    aligner tách/gộp token khác cách tách bằng khoảng trắng → so khớp NỘI DUNG
    bằng difflib trên token đã chuẩn hoá, rồi cắt tại token đầu tiên của mỗi câu.
    Trước đây đường này raise và giết cả pipeline sau khi đã trả tiền TTS.
    """
    counts = [len(line.split()) for line in spoken_lines]
    if sum(counts) == len(words):
        out, i = [], 0
        for n in counts:
            out.append(words[i : i + n])
            i += n
        return out
    return _split_by_content(words, spoken_lines)


def _split_by_content(words: list[Word], spoken_lines: list[str]) -> list[list[Word]]:
    import difflib

    exp_keys: list[str] = []
    owner: list[int] = []  # token kỳ vọng thứ k thuộc câu nào
    for li, line in enumerate(spoken_lines):
        for tok in line.split():
            exp_keys.append(_key(tok))
            owner.append(li)
    got_keys = [_key(w.w) for w in words]

    # Với mỗi token aligner, câu của nó = câu của token kỳ vọng khớp gần nhất.
    sm = difflib.SequenceMatcher(a=exp_keys, b=got_keys, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    if matched < 0.8 * len(exp_keys):
        # Lệch cách tách token thì vẫn khớp được phần lớn; khớp dưới 80% nghĩa là
        # aligner MẤT từ (hoặc chuỗi gửi đi sai) — cắt tiếp là gắn sai mốc âm thầm.
        raise ValueError(
            f"hụt timestamp: chỉ khớp {matched}/{len(exp_keys)} token giữa kịch bản và "
            f"aligner — kiểm lại chuỗi gửi cho aligner có đúng là norm_text đã ghép không."
        )
    line_of: list[int | None] = [None] * len(words)
    for blk in sm.get_matching_blocks():
        for d in range(blk.size):
            line_of[blk.b + d] = owner[blk.a + d]
    # Token không khớp: thừa hưởng câu của token đứng trước (không tiến lùi).
    cur = 0
    for j in range(len(words)):
        if line_of[j] is None:
            line_of[j] = cur
        else:
            cur = max(cur, line_of[j])  # đơn điệu: câu không được quay lui
            line_of[j] = cur

    out: list[list[Word]] = [[] for _ in spoken_lines]
    for w, li in zip(words, line_of):
        out[li].append(w)
    empty = [i for i, ch in enumerate(out) if not ch]
    if empty:
        raise ValueError(
            f"không gán được từ nào cho câu {[spoken_lines[i] for i in empty]!r} — "
            f"aligner trả {len(words)} token, kịch bản có {len(exp_keys)}"
        )
    return out
