"""Chọn GÓC KỂ trước khi viết (R3, 2026-10-04 — research/14 §2, research/15).

Vì sao có bước này: một lần gọi scriptwriter ra kịch bản "an toàn", na ná nhau giữa các video — LLM sau alignment viết
đồng phục (arXiv 2605.26492: 88% truyện có cùng 11 token). Và nền tảng phạt nội dung "theo khuôn" (YouTube YPP
2025-07, TikTok FYF). Hai thay đổi có bằng chứng:

1. **Verbalized Sampling** (arXiv 2510.01171): xin N phương án KÈM xác suất → đa dạng ×1,6–2,1, không giảm chất lượng.
   Một lần gọi `angle_gen` → 5 phương án {dạng video, hook, chữ bìa, góc, vì sao xem tới cuối}.
2. **Chấm so cặp** thay vì cho điểm (LitBench 2507.00769; 2601.08003): một lần gọi `angle_judge` phán thắng/thua cho
   mọi cặp → code tính điểm Copeland (+ phạt dạng video vừa dùng ở các video gần đây của kênh) → chọn 1.

Code là cổng: phương án hook quá dài / dạng không thuộc kênh bị loại trước khi chấm.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..team import State

REPO_ROOT = Path(__file__).resolve().parents[3]
N_ANGLES = 5
HOOK_MAX_WORDS = 14
GEN_TIMEOUT_SEC = 300      # lần chạy thường ~60s
JUDGE_TIMEOUT_SEC = 240    # 2026-10-05: lần chạy thường ~60s; treo 923s đã gặp → quá 4 phút thì bỏ trọng tài
RECENT_FORMATS = 3        # dạng đã dùng ở 3 video gần nhất của kênh → phạt khi chấm (chống "theo khuôn")


class Angle(BaseModel):
    format: str
    hook: str             # câu nói đầu tiên (lời đọc)
    hook_text: str        # chữ to frame 0
    angle: str            # góc kể: người xem được gì, vòng tò mò là gì, trả lời ở đâu
    why_finish: str       # vì sao người xem ở lại tới cuối
    probability: float    # xác suất phương án này là cách viết "thường gặp" (Verbalized Sampling)


class AnglesOut(BaseModel):
    angles: list[Angle]


class PairVerdict(BaseModel):
    a: int
    b: int
    winner: Literal["a", "b"]
    reason: str


class JudgeOut(BaseModel):
    verdicts: list[PairVerdict]


def formats() -> dict[str, dict]:
    from ..channel import current

    return current().raw.get("formats") or {}


def recent_formats(n: int = RECENT_FORMATS) -> list[str]:
    """Dạng video của n video gần nhất CÙNG KÊNH (out/*/angles.json, mới nhất trước)."""
    from ..channel import current

    cid = current().id
    rows = []
    for p in (REPO_ROOT / "out").glob("*/angles.json"):
        job = p.parent / "job.json"
        try:
            if json.loads(job.read_text()).get("channel", "ai") != cid:
                continue
            rows.append((p.stat().st_mtime, json.loads(p.read_text()).get("chosen", {}).get("format")))
        except (OSError, json.JSONDecodeError):
            continue
    return [f for _, f in sorted(rows, reverse=True)[:n] if f]


def _gen_system() -> str:
    from ..channel import current

    ch = current()
    fm = "\n".join(f"- {k}: {v.get('desc', '')}" for k, v in formats().items())
    return f"""Bạn là BIÊN TẬP VIÊN GÓC KỂ của kênh TikTok tiếng Việt "{ch.name}" ({ch.raw.get('audience', '')}).
Với chủ đề + sự thật đã kiểm, đề xuất {N_ANGLES} phương án KHÁC NHAU THẬT SỰ để kể thành video. Mỗi phương án:
- `format`: MỘT dạng video trong danh sách dưới.
- `hook`: câu nói đầu tiên ≤ {HOOK_MAX_WORDS} từ — khẳng định cụ thể HOẶC câu hỏi có khoảng trống tò mò, gợi MỘT cảm xúc
  mạnh (kinh ngạc, lo, bất ngờ, tò mò) — Berger & Milkman: cảm xúc kích thích cao + hữu ích thì được chia sẻ.
- `hook_text`: chữ to trên khung đầu, 2–7 từ, khác lời hook nhưng cùng ý.
- `angle`: 2–3 câu — người xem được gì, vòng tò mò mở ở đâu và trả lời ở đâu, chỗ ngoặt "nhưng…" là gì.
- `why_finish`: vì sao người xem ở lại tới câu cuối.
- `probability`: xác suất (0–1) một biên tập viên bình thường sẽ chọn đúng cách kể này. Đưa CẢ phương án ít gặp (xác
  suất thấp) nhưng vẫn đúng sự thật — đừng đưa năm biến thể của cùng một ý.

DẠNG VIDEO CỦA KÊNH:
{fm}

Chỉ dùng sự thật trong đề bài. Không bịa số."""


JUDGE_SYSTEM = """Bạn là GIÁM KHẢO hook TikTok tiếng Việt. Với MỖI CẶP phương án (a, b), chọn phương án khiến một người
Việt đang lướt TikTok DỪNG LẠI và XEM TỚI CUỐI nhiều hơn. Tiêu chí, theo thứ tự:
1. 3 giây đầu có thông tin cụ thể / khoảng trống tò mò rõ, không chung chung, không chào hỏi.
2. Lợi ích hoặc cảm xúc mạnh với người xem (tiền, thời gian, rủi ro, kinh ngạc) — không phải "tin cho biết".
3. Có lý do ở lại tới cuối (đếm ngược, câu trả lời để dành, chỗ ngoặt).
4. Tự nhiên như người Việt nói, không sáo rỗng.
Phán từng cặp độc lập. `reason` một câu."""


def _ok(a: Angle, fmts: dict) -> str | None:
    if a.format not in fmts:
        return f"dạng {a.format!r} không thuộc kênh"
    if len(a.hook.split()) > HOOK_MAX_WORDS:
        return f"hook {len(a.hook.split())} từ > {HOOK_MAX_WORDS}"
    if not (2 <= len(a.hook_text.split()) <= 7):
        return "hook_text phải 2–7 từ"
    return None


def choose_angle(topic: str, brief_txt: str | None, *, state: "State | None" = None, artifact: Path | None = None,
                 model: str | None = None) -> dict | None:
    """→ {"chosen": Angle-dict, "candidates": [...], "scores": {...}} hoặc None nếu kênh không khai `formats`."""
    from pydantic import create_model

    from ..team import run_role
    from ..team.role import RoleError

    fmts = formats()
    if not fmts:
        return None
    keys = tuple(fmts)
    ang = create_model("Angle", __base__=Angle, format=(Literal[keys], ...))  # type: ignore[valid-type]
    schema = create_model("AnglesOut", __base__=AnglesOut, angles=(list[ang], ...))
    recent = recent_formats()
    prompt = (f"CHỦ ĐỀ: {topic}\n\n{brief_txt or ''}\n\n"
              + (f"Ba video gần nhất của kênh đã dùng dạng: {', '.join(recent)} — ưu tiên dạng KHÁC.\n" if recent else "")
              + f"Đề xuất {N_ANGLES} phương án theo schema.")
    out = run_role("angle_gen", prompt, schema, system_prompt=_gen_system(), tools=[], max_turns=4,
                   max_budget_usd=1.0, model=model, state=state, timeout_sec=GEN_TIMEOUT_SEC)
    cands = [a for a in out.angles if _ok(a, fmts) is None][:N_ANGLES]
    dropped = [{"hook": a.hook, "why": _ok(a, fmts)} for a in out.angles if _ok(a, fmts)]
    if not cands:
        raise ValueError(f"angle_gen: không phương án nào qua cổng code: {dropped}")
    score = {i: 0.0 for i in range(len(cands))}
    verdicts: list[dict] = []
    if len(cands) > 1:
        listing = "\n".join(f"[{i}] ({c.format}) hook: {c.hook} | chữ bìa: {c.hook_text} | góc: {c.angle} | "
                            f"giữ chân: {c.why_finish}" for i, c in enumerate(cands))
        pairs = list(itertools.combinations(range(len(cands)), 2))
        jp = (f"CHỦ ĐỀ: {topic}\n\nCÁC PHƯƠNG ÁN:\n{listing}\n\nPhán đủ {len(pairs)} cặp (a, b): "
              + ", ".join(f"({a},{b})" for a, b in pairs))
        try:
            j = run_role("angle_judge", jp, JudgeOut, system_prompt=JUDGE_SYSTEM, tools=[], max_turns=4,
                         max_budget_usd=1.0, model=model, state=state, timeout_sec=JUDGE_TIMEOUT_SEC)
        except RoleError as e:
            # Trọng tài là vai PHỤ: hỏng/treo thì xếp theo probability của angle_gen + phạt dạng vừa dùng (dưới).
            print(f"  ⚠ angle_judge bỏ qua ({str(e)[:120]}) — xếp theo probability", flush=True)
            j = JudgeOut(verdicts=[])
        seen = set()
        for v in j.verdicts:
            if (v.a, v.b) not in pairs or (v.a, v.b) in seen:
                continue
            seen.add((v.a, v.b))
            score[v.a if v.winner == "a" else v.b] += 1
            verdicts.append(v.model_dump())
    # Copeland + phạt dạng vừa dùng (chống "theo khuôn" — YouTube YPP 2025-07, TikTok FYF).
    for i, c in enumerate(cands):
        if c.format in recent:
            score[i] -= 0.5 * (RECENT_FORMATS - recent.index(c.format))
    best = max(score, key=lambda i: (score[i], -cands[i].probability))
    res = {"chosen": cands[best].model_dump(), "candidates": [c.model_dump() for c in cands], "scores": score,
           "verdicts": verdicts, "dropped": dropped, "recent_formats": recent}
    if artifact is not None:
        artifact.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return res


def angle_for_script(res: dict) -> str:
    """Đoạn chèn vào ĐỀ BÀI scriptwriter."""
    from ..channel import current

    c = res["chosen"]
    f = (current().raw.get("formats") or {}).get(c["format"], {})
    return ("\n\nGÓC KỂ ĐÃ CHỌN (bắt buộc theo — đã chấm so cặp với 4 phương án khác):\n"
            f"  DẠNG: {c['format']} — {f.get('desc', '')}\n"
            + (f"  CẤU TRÚC DẠNG NÀY: {f['structure']}\n" if f.get("structure") else "")
            + f"  HOOK (giữ ý, được chỉnh chữ cho tự nhiên): {c['hook']}\n"
            f"  CHỮ BÌA: {c['hook_text']}\n  GÓC: {c['angle']}\n  GIỮ CHÂN: {c['why_finish']}")
