"""Phụ đề theo CỤM 1-3 từ + nhấn từ khoá (P3b.S5).

Trước P3b.S5 cả câu (≤ 16 từ, 2-4 dòng) hiện cùng lúc. Format TikTok mạnh là cụm ngắn,
chữ to giữa khung, đổi theo nhịp đọc (research/08 §1). Python chia cụm và ghi vào spec
(`captions[].chunks`); Remotion chỉ vẽ cụm đang đọc. Chia ở Python chứ không ở Remotion
vì T1 đo vùng an toàn TỪ SPEC — nó phải thấy đúng cái được vẽ.

Tiếng Việt: mỗi "từ" trong `words` là một ÂM TIẾT ("bộ", "nhớ"). Chưa dùng bộ tách từ
(pyvi MIT / underthesea Apache-2.0 — license trọng số chưa kiểm, thêm dependency + model),
nên cụm dựa vào thứ đo được: dấu câu, khoảng lặng trong audio, số ký tự. Tách từ là
hướng tiếp (research/probes/p3b-s5-research.md §5). Tham số ở `configs/style.yaml:
captions` — lý do từng số ở `research/probes/p3b-s5-research.md`.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Callable, Sequence

DEFAULTS = {
    "max_tokens": 3,      # âm tiết mỗi cụm
    "max_chars": 14,      # vừa MỘT dòng ở chunk_size_px trong hộp an toàn
    "min_sec": 0.3,       # bẫy của step: cụm ngắn đổi nhanh vượt 10 từ/s
    "gap_sec": 0.25,      # lặng dài hơn → luôn cắt cụm ở đó
    "max_emph_tokens": 6, # cụm nhấn (con số đọc bằng chữ) giữ liền tới chừng này âm tiết
}

_PUNCT_END = re.compile(r"[,.!?:;…]$")


def _chars(words: Sequence[dict], a: int, b: int) -> int:
    return sum(len(w["w"]) for w in words[a:b]) + max(b - a - 1, 0)


def split_chunks(
    words: Sequence[dict], cap_start: float, cap_end: float, cfg: dict | None = None,
    fits: Callable[[str], bool] | None = None,
    width: Callable[[str], float] | None = None,
) -> list[dict]:
    """Chia `words` (của MỘT caption) thành cụm phủ kín [cap_start, cap_end].

    Luật, theo thứ tự ưu tiên:
    1. Luôn cắt SAU dấu câu và tại khoảng lặng > `gap_sec` (chỗ người đọc ngắt hơi).
    2. Không vượt `max_tokens` âm tiết, `max_chars` ký tự, và — nếu có `fits` — phải
       vừa MỘT dòng đo bằng file font thật (một từ dài như "SDXL-Lightning" đứng một
       mình). Đếm ký tự không đủ: "Không card sáu" 14 ký tự vẫn xuống 2 dòng ở Anton
       116px (fixture 2026-10-01) — chữ hoa có dấu rộng hơn trung bình.
    3. Không để một âm tiết mồ côi ở cuối câu: nhập vào cụm trước, hoặc chia lại 2 + 2.
    4. Cụm ngắn hơn `min_sec` nhập vào cụm kế (hoặc cụm trước nếu là cụm cuối) —
       luật duy nhất được phép vượt `max_tokens`: đọc kịp quan trọng hơn trần 3 từ.
    """
    c = {**DEFAULTS, **(cfg or {})}
    n = len(words)
    if n == 0:
        return []

    # 1-2: cắt tham lam
    bounds: list[tuple[int, int]] = []
    hard_after: set[int] = set()   # chỉ số cụm kết thúc ở điểm cắt cứng (dấu câu / lặng)
    a = 0
    for i in range(n):
        last = i == n - 1
        size_next = (i + 2 - a) if not last else 0
        hard = bool(_PUNCT_END.search(words[i]["w"])) or (
            not last and words[i + 1]["start"] - words[i]["end"] > c["gap_sec"]
        )
        full = not last and (
            size_next > c["max_tokens"] or _chars(words, a, i + 2) > c["max_chars"]
            or (fits is not None and not fits(" ".join(w["w"] for w in words[a:i + 2])))
        )
        # Không xé cụm nhấn: demo P3b.S5 (2026-10-02) cắt "sáu trăm hai mươi bốn MiB"
        # thành 3 cụm — con số đắt nhất video vụn ra. Giữ liền tới `max_emph_tokens`
        # âm tiết; quá rộng thì `fit` thu chữ cho vừa một dòng.
        if full and words[i].get("emph") and words[i + 1].get("emph") and size_next <= c["max_emph_tokens"]:
            full = False
        # Cụm nhấn sắp bắt đầu mà không chung được với phần đang gom → cắt NGAY TRƯỚC
        # nó, để nó đứng thành cụm riêng (không bị chia đôi ở giữa).
        if not last and not words[i].get("emph") and words[i + 1].get("emph"):
            r = 0
            while i + 1 + r < n and words[i + 1 + r].get("emph"):
                r += 1
            if (i + 1 - a) + r > c["max_tokens"]:
                full = True
        if last or hard or full:
            if hard:
                hard_after.add(len(bounds))
            bounds.append((a, i + 1))
            a = i + 1

    def t0(k: int) -> float:
        return cap_start if k == 0 else words[bounds[k][0]]["start"]

    def dur(k: int) -> float:
        end = cap_end if k == len(bounds) - 1 else words[bounds[k + 1][0]]["start"]
        return end - t0(k)

    # 3: mồ côi cuối câu (TRƯỚC luật min_sec — nếu không cụm 1 âm tiết bị nhập thành 4) — chỉ khi giữa hai cụm KHÔNG phải chỗ ngắt hơi thật.
    # Cụm trước ≤ 2 âm tiết → nhập (vẫn ≤ 3); cụm trước 3 âm tiết → chia lại 2 + 2,
    # không nhập thành 4 (trần của step là 1-3 từ).
    if len(bounds) > 1 and (len(bounds) - 2) not in hard_after:
        a, b = bounds[-1]
        pa, pb = bounds[-2]
        if b - a == 1:
            joined = " ".join(w["w"] for w in words[pa:b])
            if pb - pa < c["max_tokens"] and _chars(words, pa, b) <= c["max_chars"] and (fits is None or fits(joined)):
                bounds[-2] = (pa, b)
                del bounds[-1]
            elif pb - pa >= 3 and not (words[pb - 1].get("emph") and words[pb - 2].get("emph")):
                # chỉ chia lại khi cụm trước đủ 3: 2 + 1 → 1 + 2 chẳng đỡ gì, mà tạo
                # cụm 1 âm tiết rất ngắn để luật min_sec nhập ngược thành cụm quá rộng
                # ("kiến trúc MoE." — fixture 01, 2026-10-01).
                bounds[-2], bounds[-1] = (pa, pb - 1), (pb - 1, b)

    # 4: cụm quá ngắn → nhập. Cho phép vượt max_tokens/max_chars một chút: đọc kịp
    # quan trọng hơn vừa khít một dòng (T1 hình học sẽ bắt nếu tràn thật).
    k = 0
    while k < len(bounds) and len(bounds) > 1:
        if dur(k) >= c["min_sec"]:
            k += 1
            continue
        def ok(x: int, y: int) -> bool:
            return fits is None or fits(" ".join(w["w"] for w in words[x:y]))

        nxt_ok = k < len(bounds) - 1 and ok(bounds[k][0], bounds[k + 1][1])
        prv_ok = k > 0 and ok(bounds[k - 1][0], bounds[k][1])
        # Ưu tiên phía nhập xong vẫn vừa một dòng; không phía nào vừa thì vẫn nhập
        # (đọc kịp là luật của step) — `fit` bên dưới sẽ thu nhỏ chữ cụm đó.
        if k < len(bounds) - 1 and (nxt_ok or not prv_ok):
            bounds[k] = (bounds[k][0], bounds[k + 1][1])
            del bounds[k + 1]
        else:
            bounds[k - 1] = (bounds[k - 1][0], bounds[k][1])
            del bounds[k]
            k -= 1

    out = []
    for k, (a, b) in enumerate(bounds):
        start = t0(k)
        end = cap_end if k == len(bounds) - 1 else words[bounds[k + 1][0]]["start"]
        ch = {"start_sec": round(start, 3), "end_sec": round(max(end, start + 0.001), 3),
              "from": a, "to": b}
        if width is not None:
            # Cụm vẫn rộng hơn hộp (một từ dài "Qwen3-30B-A3B", hoặc nhập vì min_sec)
            # → thu nhỏ RIÊNG cụm đó cho vừa một dòng, thay vì để nó xuống dòng.
            f = width(" ".join(w["w"] for w in words[a:b]))
            if f < 1.0:
                ch["fit"] = round(max(f, 0.5), 3)
        out.append(ch)
    return out


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s).lower()
    return re.sub(r"^[^\w]+|[^\w]+$", "", s)


def mark_emphasis(words: list[dict], phrases: Sequence[str] = ()) -> int:
    """Gắn `emph: True` cho từ có chữ số và cho mọi lần xuất hiện của `phrases`
    (scriptwriter khai: tên model, con số viết bằng chữ…). Trả số từ được nhấn."""
    toks = [_norm(w["w"]) for w in words]
    hit = [any(ch.isdigit() for ch in w["w"]) for w in words]
    for ph in phrases:
        seq = [_norm(x) for x in ph.split() if _norm(x)]
        if not seq:
            continue
        for i in range(len(toks) - len(seq) + 1):
            if toks[i:i + len(seq)] == seq:
                for j in range(i, i + len(seq)):
                    hit[j] = True
    n = 0
    for w, h in zip(words, hit):
        if h:
            w["emph"] = True
            n += 1
        else:
            w.pop("emph", None)
    return n


def _measurer(spec: dict, size: int) -> tuple[Callable[[str], bool], Callable[[str], float]] | None:
    """`fits(text)`: vừa một dòng trong hộp an toàn, đo bằng ĐÚNG file font Chrome sẽ
    dùng (cùng `_font_file` với T1). 92% bề ngang: chừa viền chữ + khoảng cách từ."""
    from ..qc.t1_technical import _font_file

    st, safe = spec["style"], spec["style"]["safe_area_pct"]
    path = _font_file(st["caption"]["font"])
    if not path:
        return None
    from PIL import ImageFont

    font = ImageFont.truetype(path, size)
    box_w = spec["format"]["width"] * (100 - safe["left"] - safe["right"]) / 100 * 0.92
    # (vừa một dòng?, hệ số cần thu để vừa: box / bề rộng)
    return (lambda t: font.getlength(t) <= box_w), (lambda t: box_w / max(font.getlength(t), 1.0))


def add_chunks(spec: dict, cfg: dict | None = None, emphasis: Sequence[str] = ()) -> dict:
    """Thêm `chunks` + `emph` vào mọi caption thường (hook giữ nguyên cả câu — nó là
    thumbnail ở frame 0). Dùng cho cả spec mới (build) lẫn spec cũ (`upgrade`)."""
    st = spec["style"]["caption"]
    if (cfg or {}).get("chunk_size_px"):
        st["chunk_size_px"] = int(cfg["chunk_size_px"])
    st.setdefault("chunk_size_px", int(round(st["size_px"] * 1.35)))
    m = _measurer(spec, st["chunk_size_px"]) if "format" in spec else None
    fits, width = m if m else (None, None)
    for cap in spec["captions"]:
        if cap.get("style") == "hook" and not cap.get("display_text"):
            continue
        mark_emphasis(cap["words"], emphasis)
        cap["chunks"] = split_chunks(cap["words"], cap["start_sec"], cap["end_sec"], cfg, fits, width)
    return spec
