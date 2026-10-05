"""Vai **idea_gen** (2026-10-04): bổ sung kho ý tưởng cho kênh KHÔNG có nguồn trend (kênh mẹo).

Tony: "chủ đề gợi ý sẽ update hằng ngày hoặc 1 nút reset để gợi ý các chủ đề mới". Kho seed (`ideas.yaml`) chỉ ~30 ý
và lịch mùa đổi theo tháng → không đủ "mới mỗi ngày". Vai này chạy MỘT lần gọi Claude (context mới, WebSearch để bắt
chuyện đang xảy ra: thủ đoạn lừa đảo mới, cảnh báo an toàn thực phẩm, thời tiết tuần này), trả về N ý tưởng;
**code** lọc trùng (với kho, với video đã làm, với nhau) rồi lưu vào DB web (`ideas`, source="may").

    .venv/bin/python -m create_video.team.idea_gen --channel meo -n 12

Chạy: mỗi sáng cùng trend scout (worker) và khi bấm "Tìm chủ đề mới" trên web. research/probes/k6-goi-y-research.md.
"""

from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from pathlib import Path

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[3]
DUP_JACCARD = 0.6        # ≥ 60% từ trùng với ý đã có → coi là trùng (viết trước khi chạy, 2026-10-04)


class GenIdea(BaseModel):
    title: str           # chủ đề video tiếng Việt, ≤ 90 ký tự, cụ thể
    pillar: str
    why: str             # vì sao người Việt quan tâm LÚC NÀY (≤ 120 ký tự)
    hint: str = ""       # nguồn chính thống nên tìm (domain)


class GenOut(BaseModel):
    ideas: list[GenIdea]


def _toks(s: str) -> set[str]:
    s = unicodedata.normalize("NFC", s.lower())
    return {w for w in re.findall(r"\w+", s) if len(w) > 1}


def is_dup(title: str, others: list[str]) -> bool:
    a = _toks(title)
    if not a:
        return True
    for o in others:
        b = _toks(o)
        if b and len(a & b) / len(a | b) >= DUP_JACCARD:
            return True
    return False


def _system(ch, n: int) -> str:
    pillars = "\n".join(f"- {k}: {p.get('desc', '')}" for k, p in ch.pillars.items())
    return f"""Bạn là BIÊN TẬP VIÊN Ý TƯỞNG của kênh TikTok tiếng Việt "{ch.name}" — {ch.raw.get('audience', '')}.
Hôm nay là {time.strftime('%Y-%m-%d')}. Đề xuất {n} chủ đề video 30–60 giây MỚI, người Việt đang cần biết.

Dùng WebSearch (tin Việt Nam 7–14 ngày gần đây) để bắt chuyện ĐANG xảy ra: thủ đoạn lừa đảo mới được công an/ngân hàng
cảnh báo, cảnh báo an toàn thực phẩm, thời tiết/mùa tuần này, tính năng mới của điện thoại/ứng dụng phổ biến ở VN.
Trộn với chủ đề muôn thuở (evergreen) nhưng góc nhìn cụ thể.

PILLAR (mỗi ý tưởng đúng MỘT):
{pillars}

LUẬT
1. `title` là chủ đề CỤ THỂ, ≤ 90 ký tự, đọc lên biết ngay video nói gì ("Tin nhắn báo trúng thưởng đơn hàng 11.11:
   ba dấu hiệu lừa đảo"), không chung chung ("Mẹo hay cuộc sống").
2. Chỉ chủ đề làm được KHÔNG CẦN QUAY: giải thích được bằng chữ, thẻ hội thoại, danh sách, con số, ảnh đồ vật, ảnh
   chụp trang web chính thống. KHÔNG: lau chùi trước/sau, DIY, làm đẹp, kỹ thuật nấu, trộn hoá chất, chữa bệnh tại nhà.
3. Phải có nguồn CHÍNH THỐNG kiểm chứng được (cơ quan nhà nước, ngân hàng, hãng điện thoại, tổ chức y tế) — ghi domain
   vào `hint`. Không chắc có nguồn → đừng đề xuất.
4. Rải đều các pillar; không hai ý tưởng cùng một ý.
5. `why` ≤ 120 ký tự: vì sao LÚC NÀY người xem cần biết."""


def generate(channel_id: str = "meo", n: int = 12, *, model: str | None = None, db_path: Path | None = None) -> dict:
    from ..channel import get
    from ..web import db
    from . import State, run_role
    from .idea_scout import _videos, bank

    ch = get(channel_id)
    db.init(db_path)
    rows = db.idea_rows(ch.id, db_path)
    existing = [i["title"] for i in bank(ch, rows)] + [v["topic"] for v in _videos(ch)]
    existing += [j["topic"] for j in db.list_jobs(path=db_path) if (j.get("channel") or "ai") == ch.id]
    # Đưa vào prompt các ý gần đây để model tránh lặp; code vẫn lọc lại ở dưới (không tin LLM tự tránh trùng).
    recent = existing[-60:]
    prompt = ("Đã có các chủ đề sau (KHÔNG lặp lại, kể cả đổi cách nói):\n" + "\n".join(f"- {t}" for t in recent)
              + f"\n\nĐề xuất {n} ý tưởng mới theo schema.")
    run_dir = REPO_ROOT / "team" / "ideas" / ch.id
    run_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d-%H%M")
    state = State.load(run_dir / f"{stamp}.run", video_id=f"ideas-{ch.id}-{stamp}")
    state.begin("idea_gen", "")
    out = run_role("idea_gen", prompt, GenOut, system_prompt=_system(ch, n), tools=["WebSearch"],
                   max_turns=16, max_budget_usd=1.5, model=model, state=state)
    state.done("idea_gen", [])
    added, dropped = [], []
    seen = list(existing)
    for it in out.ideas:
        t = re.sub(r"\s+", " ", it.title).strip()
        why = "pillar lạ" if it.pillar not in ch.pillars else "quá dài/ngắn" if not (6 <= len(t) <= 120) \
            else "trùng ý đã có" if is_dup(t, seen) else ""
        if why:
            dropped.append({"title": t, "why": why})
            continue
        iid = db.add_idea(ch.id, t, it.pillar, path=db_path, source="may", note=f"{it.why} — nguồn gợi ý: {it.hint}"[:300])
        added.append({"id": iid, "title": t, "pillar": it.pillar})
        seen.append(t)
    log = {"at": stamp, "channel": ch.id, "added": added, "dropped": dropped,
           "llm": [{k: x.get(k) for k in ("role", "wall_sec", "input_tokens", "output_tokens", "cost_usd")}
                   for x in state.llm_calls]}
    (run_dir / f"{stamp}.json").write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return log


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="sinh ý tưởng mới cho kho của kênh (1 lần gọi Claude + lọc trùng bằng code)")
    ap.add_argument("--channel", default="meo")
    ap.add_argument("-n", type=int, default=12)
    a = ap.parse_args(argv)
    log = generate(a.channel, a.n)
    print(f"✓ thêm {len(log['added'])} ý tưởng · loại {len(log['dropped'])}")
    for x in log["added"]:
        print(f"  + [{x['pillar']}] {x['title']}")
    for x in log["dropped"]:
        print(f"  - {x['title']} ({x['why']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
