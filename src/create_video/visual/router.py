"""Chọn hình cho từng shot theo `kind` do scriptwriter khai (P3b.S4).

Trước P3b.S4 mọi shot là ảnh SDXL, prompt xoay vòng theo chỉ số — "khối phát sáng"
không mang thông tin (research/08 §1). Giờ scriptwriter khai shot "bằng chứng"
(`stat` · `chart` · `code` · `screenshot`) NEO VÀO CÂU nói tới nó; SDXL lùi về làm
b-roll cho những đoạn còn lại.

Hai quyết định:

1. **Neo theo câu, không theo thứ tự shot.** Số shot do nhịp audio quyết định
   (`spec.build._group_spans`), còn scriptwriter không biết trước nhịp. Đúng lỗi này
   từng làm overlay "14 GB" hiện lúc giọng đọc "mười sáu bit" (P3b.S1). Nên mỗi câu
   có shot bằng chứng là một **điểm cắt bắt buộc**: thẻ hiện đúng lúc câu bắt đầu.
2. **Hỏng thì lùi, không chết.** Screenshot timeout / URL ngoài danh sách → shot đó
   thành b-roll SDXL, ghi lý do. Một ảnh chụp hỏng không đáng mất cả video.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

EVIDENCE_KINDS = ("stat", "chart", "code", "screenshot")


@dataclass
class Visual:
    """Hình của MỘT shot (một nhóm câu)."""

    kind: str                  # image | stat | chart | code | screenshot
    prompt: str = ""           # image: prompt SDXL
    data: dict = field(default_factory=dict)   # stat/chart/code: payload đúng schema
    url: str = ""              # screenshot
    highlight: str = ""        # screenshot: chữ cần tô vàng
    line: int | None = None    # câu (chỉ số trong script.lines) đã neo shot này
    note: str = ""             # vì sao lùi về b-roll, nếu có


def anchored(shots) -> bool:
    """Script kiểu mới (có `line`) hay kiểu cũ (xoay vòng theo chỉ số)."""
    return any(getattr(s, "line", None) is not None for s in shots)


def breaks(shots, kept: Sequence[int]) -> set[int]:
    """Chỉ số (trong danh sách câu ĐÃ BỎ câu rỗng) phải mở shot mới: câu có shot bằng chứng."""
    pos = {orig: k for k, orig in enumerate(kept)}
    return {pos[s.line] for s in shots
            if s.kind in EVIDENCE_KINDS and s.line is not None and s.line in pos and pos[s.line] > 0}


def plan(shots, groups: Sequence[Sequence[int]], kept: Sequence[int]) -> list[Visual]:
    """Mỗi nhóm câu → một `Visual`.

    `groups` chứa chỉ số trong danh sách câu đã bỏ câu rỗng; `kept[k]` đưa về chỉ
    số gốc trong `script.lines` — chỗ `shot.line` trỏ tới.
    """
    if not shots:
        return [Visual("image") for _ in groups]
    if not anchored(shots):
        # Script trước P3b.S4: giữ NGUYÊN hành vi cũ để script.json cũ dựng ra như cũ.
        return [Visual("image", prompt=shots[k % len(shots)].prompt) for k in range(len(groups))]

    by_line: dict[int, list] = {}
    for s in shots:
        if s.line is not None:
            by_line.setdefault(s.line, []).append(s)
    images = sorted((s for s in shots if s.kind == "image" and s.prompt),
                    key=lambda s: (s.line if s.line is not None else 10**6))
    used: set[int] = set()
    out: list[Visual] = []
    for g in groups:
        cands = [s for k in g for s in by_line.get(kept[k], [])]
        ev = next((s for s in cands if s.kind in EVIDENCE_KINDS), None)
        if ev is not None and kept[g[0]] == ev.line:
            out.append(Visual(ev.kind, prompt=ev.prompt, data=_payload(ev), url=ev.url or "",
                              highlight=ev.highlight or "", line=ev.line))
            continue
        img = next((s for s in cands if s.kind == "image" and s.prompt), None)
        if img is None:
            # Nhóm không có shot neo: lấy b-roll chưa dùng kế tiếp, hết thì xoay vòng.
            free = [s for s in images if id(s) not in used]
            img = free[0] if free else (images[len(out) % len(images)] if images else None)
        if img is not None:
            used.add(id(img))
        prompt = img.prompt if img else ""
        # Phase V (2026-10-02, v2): câu dài bị chia thành 2+ shot dùng CHUNG prompt → 2 ảnh gần y hệt
        # liền nhau (giấy trắng ×3). Lần dùng lại thứ n đổi góc máy, cùng chủ thể.
        n_used = sum(1 for v in out if v.kind == "image" and v.prompt.split(" | ")[0] == prompt)
        if prompt and n_used:
            prompt = f"{prompt} | {REFRAME[(n_used - 1) % len(REFRAME)]}"
        out.append(Visual("image", prompt=prompt, line=kept[g[0]]))
    return out


REFRAME = (
    "extreme close-up macro detail of the main object, shallow depth of field",
    "top-down overhead view of the same scene",
    "low angle side view, object large in frame",
    "wide shot, object small in the lower third, lots of dark negative space",
)


def fallback_prompt(visuals: Sequence[Visual], i: int, shots) -> str:
    """Prompt b-roll cho shot bằng chứng bị hỏng: prompt riêng của nó nếu có, rồi
    prompt ảnh gần nhất phía trước/sau, cuối cùng là prompt ảnh đầu tiên của script."""
    if visuals[i].prompt:
        return visuals[i].prompt
    order = sorted(range(len(visuals)), key=lambda j: abs(j - i))
    for j in order:
        if visuals[j].kind == "image" and visuals[j].prompt:
            return visuals[j].prompt
    return next((s.prompt for s in shots if s.prompt), "")


def evidence_ratio(visuals: Sequence[Visual]) -> float:
    return sum(v.kind in EVIDENCE_KINDS for v in visuals) / max(len(visuals), 1)


def _payload(s) -> dict:
    if s.kind == "stat":
        return dict(s.stat or {})
    if s.kind == "chart":
        return dict(s.chart or {})
    if s.kind == "code":
        return dict(s.code or {})
    return {}
