"""Vai **researcher** (Phase V2, 2026-10-02): chủ đề bất kỳ → `brief.json` gồm sự thật ĐÃ KIỂM.

    python -m create_video.agents.researcher "Gemini miễn phí cho sinh viên" --out out/x/brief.json

Vì sao có vai này: trước đây scriptwriter viết từ chủ đề trần, không tool — sự thật đến từ trí nhớ
model hoặc từ brief Tony dán tay (demo-03). Tony mở rộng kênh ra ngoài mạch dev (2026-10-02) → chủ
đề phổ thông ("mẹo ChatGPT", "AI làm slide") không có model card để T4 đối chiếu. Researcher đi tìm
nguồn THẬT, còn **code là cổng**:

1. LLM (WebSearch + WebFetch, context mới) trả về sự thật + url + trích NGUYÊN VĂN.
2. Code tải lại từng url vào `team/snapshots/` (`snapshot.fetch(allow_any=True)`) và tìm câu trích
   trong đó. Không tìm thấy → thử khớp câu gần nhất (≥ 80% token, cùng mọi con số) → vẫn không →
   **bỏ sự thật đó**. WebFetch của SDK trả bản tóm tắt nên LLM hay trích "gần đúng" — chính vì vậy
   cổng phải là code.
3. T4 đọc lại đúng các snapshot này (index cache theo url) — kiểm độc lập lần nữa sau khi viết.

research/11-audit-tiktok-ai.md §6 (#7 pillar mở rộng) · §7 (stage "Chọn topic" + "Fact-check").
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..team import State

REPO_ROOT = Path(__file__).resolve().parents[3]

MIN_FACTS = 4            # dưới mức này thì không đủ chất cho 30-60s — viết trước khi chạy (2026-10-02)
FUZZY_MIN = 0.8          # tỉ lệ token của câu trích phải có trong câu nguồn khi khớp mềm

def _pillars() -> dict[str, str]:
    """{key: mô tả} của kênh đang chạy — nguồn duy nhất: configs/channels/<kênh>/channel.yaml (2026-10-04)."""
    from ..channel import current

    return {k: v.get("desc", "") for k, v in current().pillars.items()}


class Fact(BaseModel):
    fact: str            # tiếng Việt, một sự thật tự đứng được
    url: str             # trang chứa sự thật — ưu tiên trang chính chủ
    quote: str           # NGUYÊN VĂN từ trang (ngôn ngữ gốc), ≤ 300 ký tự
    kind: Literal["number", "date", "price", "feature", "how_to", "other"] = "other"


class VisualRef(BaseModel):
    url: str             # trang nên CHỤP làm hình bằng chứng (trang sản phẩm, bài công bố, model card…)
    highlight: str = ""  # cụm chữ NGUYÊN VĂN có trên trang để tô vàng
    what: str = ""       # người xem sẽ thấy gì (tiếng Việt)


class BriefOut(BaseModel):
    topic: str
    pillar: str          # schema LLM ép Literal theo kênh — xem `_brief_model`
    angle: str           # góc kể cho người Việt — vì sao người lướt TikTok phải quan tâm
    audience: str        # ai xem (sinh viên, dân văn phòng, dev…)
    facts: list[Fact]
    visuals: list[VisualRef] = []
    hook_ideas: list[str] = []
    caveats: list[str] = []   # điều chưa chắc / nguồn tự công bố — scriptwriter phải nói rõ


INTRO_AI = "Bạn là RESEARCHER của một kênh TikTok tiếng Việt về AI (khán giả phổ thông Việt Nam, không chỉ dev)."

SYSTEM = f"""{{intro}}
Hôm nay là {{today}}. Nhiệm vụ: với chủ đề được giao, tìm SỰ THẬT KIỂM CHỨNG ĐƯỢC để viết video 30–60 giây.

Quy trình: WebSearch để tìm → WebFetch đọc TRANG GỐC → chép sự thật kèm trích dẫn.

LUẬT NGUỒN
{{sources}}
2. `quote` CHÉP NGUYÊN VĂN một câu/đoạn ngắn (≤ 300 ký tự) từ trang đó, ĐÚNG ngôn ngữ gốc. Code sẽ tải
   lại trang và tìm đúng chuỗi này — trích sai là sự thật bị loại. Đừng dịch, đừng tóm tắt trong quote.
3. Mỗi sự thật MỘT ý. Ưu tiên: con số (giá, tốc độ, giới hạn, ngày), điều làm được/không làm được,
   bước làm cụ thể. Cần ít nhất {MIN_FACTS + 2} sự thật để còn ≥ {MIN_FACTS} sau khi code kiểm.
4. Không chắc → ghi vào `caveats`, không đưa vào `facts`. Số do hãng tự công bố → ghi caveat "hãng tự công bố".

GÓC KỂ
5. `pillar` chọn MỘT: {{pillars}}.
6. `angle`: vì sao một người Việt đang lướt TikTok phải dừng lại — lợi ích cụ thể (tiết kiệm tiền, làm
   nhanh hơn, biết trước người khác, tránh bị lừa). Không viết kiểu thông cáo báo chí.
7. `hook_ideas`: 3 câu hook ≤ 12 từ, mỗi câu một kiểu (con số sốc · mâu thuẫn niềm tin · kết quả trước ·
   câu hỏi có số · cảnh báo), DỰA TRÊN sự thật đã tìm.

HÌNH
8. `visuals`: 2–4 trang nên chụp làm hình bằng chứng — trang hiển thị được KHÔNG cần đăng nhập, có
   chữ/số người xem đọc được ({{visual_examples}}). `highlight` = cụm chữ
   NGUYÊN VĂN ngắn (≤ 60 ký tự) có trên trang cần tô vàng.
"""

SOURCES_AI = """1. Ưu tiên trang CHÍNH CHỦ: blog/help/docs của hãng (openai.com, help.openai.com, blog.google,
   support.google.com, anthropic.com, microsoft.com…), model card Hugging Face, repo GitHub, arXiv.
   Báo lớn (vnexpress.net, tuoitre.vn, theverge.com, techcrunch.com, reuters.com) chỉ khi không có chính chủ.
   KHÔNG dùng: mạng xã hội, diễn đàn, trang tổng hợp SEO, trang cần đăng nhập, video."""
VISUALS_AI = "trang giá, bảng tính năng, bài công bố, model card"


def _system() -> str:
    from ..channel import current

    ch = current()
    pillars = ", ".join(f"{k} ({v})" for k, v in _pillars().items())
    return (SYSTEM.replace("{intro}", ch.text("research_intro", INTRO_AI))
            .replace("{sources}", ch.text("research_sources", SOURCES_AI))
            .replace("{pillars}", pillars)
            .replace("{visual_examples}", ch.text("research_visuals", VISUALS_AI))
            .replace("{today}", time.strftime("%Y-%m-%d")))


def _brief_model() -> type[BriefOut]:
    """BriefOut với `pillar` là Literal các pillar CỦA KÊNH — SDK ép LLM chọn đúng danh sách."""
    from pydantic import create_model

    keys = tuple(_pillars())
    return create_model("BriefOut", __base__=BriefOut, pillar=(Literal[keys], ...))  # type: ignore[valid-type]


def _toks(s: str) -> list[str]:
    from ..qc.t4_facts import _norm

    return re.findall(r"\w+", _norm(s))


def _nums(s: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)?", s))


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。])\s+|\n+", text)
    return [p.strip() for p in parts if 20 <= len(p.strip()) <= 600]


def match_quote(quote: str, text: str) -> str | None:
    """Câu trích có trong nguồn không. Trả về chuỗi NGUYÊN VĂN từ nguồn (để T4 dùng), hoặc None.

    Khớp cứng trước (chuẩn hoá khoảng trắng/dấu nháy như T4), rồi khớp mềm: câu nguồn chứa
    ≥ FUZZY_MIN token của trích dẫn VÀ đủ mọi con số trong trích dẫn — con số là thứ không được lệch.
    """
    from ..qc.t4_facts import quote_in

    if quote_in(quote, text):
        return quote
    q = _toks(quote)
    if len(q) < 4:
        return None
    qn = _nums(quote)
    qs = set(q)
    best, score = None, 0.0
    for sent in _sentences(text):
        st = set(_toks(sent))
        if not st:
            continue
        sc = len(qs & st) / len(qs)
        if sc > score and qn <= _nums(sent):
            best, score = sent, sc
    return best if score >= FUZZY_MIN else None


def verify(brief: BriefOut, *, fetch=None) -> tuple[BriefOut, list[dict]]:
    """Cổng code: tải từng url, giữ sự thật có trích dẫn tìm được trong trang. → (brief đã lọc, log)."""
    if fetch is None:
        from ..team.snapshot import fetch as _f

        def fetch(url):
            return _f(url, allow_any=True)

    cache: dict[str, object] = {}
    log: list[dict] = []

    def page(url: str):
        if url not in cache:
            try:
                cache[url] = fetch(url)
            except Exception as e:  # mạng, 403, trang JS rỗng — sự thật đó coi như không kiểm được
                cache[url] = e
        return cache[url]

    kept: list[Fact] = []
    for f in brief.facts:
        snap = page(f.url)
        if isinstance(snap, Exception):
            log.append({"fact": f.fact, "url": f.url, "ok": False, "why": f"tải hỏng: {type(snap).__name__}: {snap}"[:200]})
            continue
        if len(getattr(snap, "text", "")) < 200:
            log.append({"fact": f.fact, "url": f.url, "ok": False, "why": "trang gần rỗng (JS/chặn bot)"})
            continue
        m = match_quote(f.quote, snap.text)
        if m is None:
            log.append({"fact": f.fact, "url": f.url, "ok": False, "why": "không tìm thấy câu trích trong trang"})
            continue
        log.append({"fact": f.fact, "url": f.url, "ok": True, "exact": m == f.quote})
        kept.append(f.model_copy(update={"quote": m}))

    vis: list[VisualRef] = []
    for v in brief.visuals:
        snap = page(v.url)
        if isinstance(snap, Exception) or len(getattr(snap, "text", "")) < 200:
            log.append({"visual": v.url, "ok": False, "why": "trang không tải được"})
            continue
        from ..qc.t4_facts import quote_in

        if v.highlight and not quote_in(v.highlight, snap.text):
            v = v.model_copy(update={"highlight": ""})
        vis.append(v)
    return brief.model_copy(update={"facts": kept, "visuals": vis}), log


def brief_for_script(brief: BriefOut | dict) -> str:
    """Brief → đoạn "ĐỀ BÀI" nhét vào prompt scriptwriter."""
    b = brief if isinstance(brief, BriefOut) else BriefOut.model_validate(brief)
    out = [f"CHỦ ĐỀ: {b.topic}", f"PILLAR: {b.pillar} — {_pillars().get(b.pillar, '')}",
           f"GÓC KỂ: {b.angle}", f"NGƯỜI XEM: {b.audience}", "",
           "SỰ THẬT ĐÃ KIỂM (chỉ được dùng những điều này; số nào nói ra phải nằm ở đây, "
           "`sources[].url` lấy đúng url kèm theo):"]
    for i, f in enumerate(b.facts, 1):
        out.append(f"  F{i}. {f.fact}\n      url: {f.url}\n      trích: \"{f.quote}\"")
    if b.caveats:
        out += ["", "LƯU Ý (nói rõ trong video nếu dùng):"] + [f"  - {c}" for c in b.caveats]
    if b.visuals:
        out += ["", "TRANG CHỤP ĐƯỢC LÀM HÌNH BẰNG CHỨNG (kind=screenshot, dùng đúng url, highlight là "
                "cụm có trên trang):"]
        out += [f"  - {v.url}  highlight={v.highlight!r}  — {v.what}" for v in b.visuals]
    if b.hook_ideas:
        out += ["", "GỢI Ý HOOK (được viết khác hay hơn):"] + [f"  - {h}" for h in b.hook_ideas]
    return "\n".join(out)


async def research(topic: str, *, state: "State | None" = None, artifact: Path | None = None,
                   model: str | None = None, max_retry: int = 1, pillar: str | None = None) -> BriefOut:
    from ..team import arun_role

    system = _system()
    schema = _brief_model()
    # Kênh mẹo (2026-10-04): ý tưởng trong kho đã gắn pillar → researcher giữ đúng pillar đó.
    want = f"\nPILLAR BẮT BUỘC: {pillar}." if pillar and pillar in _pillars() else ""
    prompt = f"Chủ đề: {topic}{want}\n\nTìm nguồn và trả về brief theo schema."
    last_log: list[dict] = []
    for attempt in range(max_retry + 1):
        out = await arun_role(
            "researcher", prompt, schema, system_prompt=system,
            tools=["WebSearch", "WebFetch"], max_turns=40, max_budget_usd=5.0,
            model=model, state=state,
        )
        brief, log = verify(out)
        last_log = log
        ok = [x for x in log if x.get("ok") and "fact" in x]
        print(f"  researcher: {len(ok)}/{len(out.facts)} sự thật qua cổng code · "
              f"{len(brief.visuals)} trang hình", flush=True)
        if len(brief.facts) >= MIN_FACTS:
            if artifact is not None:
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(json.dumps({**brief.model_dump(), "verify_log": log},
                                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return brief
        bad = [x for x in log if not x.get("ok") and "fact" in x]
        prompt = (f"Chủ đề: {topic}\n\nLần trước chỉ {len(brief.facts)} sự thật qua kiểm — cần ≥ {MIN_FACTS}. "
                  "Các sự thật bị loại (trích dẫn không có nguyên văn trên trang, hoặc trang không tải được "
                  "bằng HTTP thường):\n" + "\n".join(f"- {x['fact']} ({x['url']}): {x['why']}" for x in bad)
                  + "\n\nTìm lại: dùng trang tải được không cần JS, chép quote NGUYÊN VĂN từng ký tự." + want)
    raise ValueError(f"researcher không đủ {MIN_FACTS} sự thật kiểm được:\n"
                     + "\n".join(f"  - {x}" for x in last_log))


def research_sync(topic: str, **kw) -> BriefOut:
    return asyncio.run(research(topic, **kw))


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="chủ đề → brief.json (sự thật đã kiểm)")
    ap.add_argument("topic")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "out" / "brief.json")
    a = ap.parse_args(argv)
    b = research_sync(a.topic, artifact=a.out)
    print(f"✓ {a.out}\n")
    print(brief_for_script(b))
    return 0


if __name__ == "__main__":
    sys.exit(main())
