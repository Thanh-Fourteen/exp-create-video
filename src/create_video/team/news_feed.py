"""Tin AI trong ngày / trong tuần — nguồn ứng viên cho kho ý tưởng kênh AI (2026-10-12, research/30 §5).

    .venv/bin/python -m create_video.team.news_feed            # in tin 7 ngày (cache theo giờ)
    .venv/bin/python -m create_video.team.news_feed --fresh

Tony 2026-10-12: "Tôi cần là ý tưởng về tin tức AI mới trong ngày, trong tuần". Chỉ CODE thu (RSS + HN Algolia), không LLM;
LLM ở idea_gen chỉ chọn tin và kể lại cho người Việt. Feed kiểm sống 2026-10-12 (V): genk AI, The Verge AI, TechCrunch AI,
OpenAI, Anthropic (bản RSS cộng đồng — như configs/sources.yaml), DeepMind, Dân trí công nghệ (lọc từ khoá AI).
VnExpress Số hoá + blog.google trả 0 mục với bot → bỏ.
"""

from __future__ import annotations

import email.utils
import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = REPO_ROOT / "team" / "news_feed"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) exp-create-video news_feed"}
# (tên, url, chỉ giữ tin có từ khoá AI?) — feed chuyên AI thì không cần lọc
FEEDS = [
    ("genk AI", "https://genk.vn/rss/ai.rss", False),
    ("Dân trí", "https://dantri.com.vn/rss/cong-nghe.rss", True),
    ("The Verge", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", False),
    ("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/", False),
    ("OpenAI", "https://openai.com/news/rss.xml", False),
    ("Anthropic", "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml", False),
    ("Google DeepMind", "https://deepmind.google/blog/rss.xml", False),
]
HN = "https://hn.algolia.com/api/v1/search?tags=story&numericFilters=created_at_i>{since},points>{pts}&hitsPerPage=50"
AI_RE = re.compile(r"\b(ai|a\.i\.|trí tuệ nhân tạo|chatgpt|gpt|openai|gemini|claude|anthropic|copilot|llm|deepseek|"
                   r"qwen|grok|meta ai|chatbot|deepfake|agent|nvidia|robot)\b", re.I)


def _get(url: str, timeout: int = 25) -> str:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _ts(s: str | None) -> float | None:
    if not s:
        return None
    s = s.strip()
    try:
        return email.utils.parsedate_to_datetime(s).timestamp()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _text(x: str | None, n: int) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", " ", x or ""))
    return " ".join(t.split())[:n]


def parse(xml: str) -> list[dict]:
    """RSS 2.0 và Atom. Trả {title, link, ts, summary}."""
    root = ET.fromstring(xml)
    out = []
    for it in root.iter():
        tag = it.tag.split("}")[-1].split(":")[-1]
        if tag not in ("item", "entry"):
            continue
        g = lambda *names: next((c for c in it if c.tag.split("}")[-1].split(":")[-1] in names), None)  # noqa: E731
        t, l = g("title"), g("link")
        link = (l.get("href") or l.text or "").strip() if l is not None else ""
        d = g("pubDate", "published", "updated", "date")
        s = g("description", "summary", "content")
        out.append({"title": _text(t.text if t is not None else "", 200), "link": link,
                    "ts": _ts(d.text if d is not None else None), "summary": _text(s.text if s is not None else "", 220)})
    return out


def hacker_news(days: int, min_points: int = 150) -> list[dict]:
    since = int(time.time() - days * 86400)
    try:
        hits = json.loads(_get(HN.format(since=since, pts=min_points))).get("hits") or []
    except Exception:
        return []
    return [{"src": "Hacker News", "title": h.get("title") or "", "ts": float(h.get("created_at_i") or 0),
             "link": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
             "summary": f"{h.get('points')} điểm, {h.get('num_comments')} bình luận"}
            for h in hits if AI_RE.search(h.get("title") or "")]


def fetch(days: int = 7, fresh: bool = False) -> list[dict]:
    """Tin AI trong `days` ngày, mới nhất trước. Cache 1 file/giờ (team/news_feed/<ngày-giờ>.json)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    f = CACHE_DIR / f"{time.strftime('%Y-%m-%d-%H')}-{days}d.json"
    if f.exists() and not fresh:
        return json.loads(f.read_text(encoding="utf-8"))
    cut = time.time() - days * 86400
    out, seen = [], set()
    for name, url, need_ai in FEEDS:
        try:
            items = parse(_get(url))
        except Exception:
            continue
        for x in items:
            if not x["ts"] or x["ts"] < cut or not x["title"]:
                continue
            if need_ai and not AI_RE.search(f"{x['title']} {x['summary']}"):
                continue
            key = re.sub(r"\W+", " ", x["title"].lower()).strip()
            if key not in seen:
                seen.add(key)
                out.append({"src": name, **x})
    for x in hacker_news(days):
        key = re.sub(r"\W+", " ", x["title"].lower()).strip()
        if key not in seen:
            seen.add(key)
            out.append(x)
    out.sort(key=lambda x: -x["ts"])
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def prompt_block(days: int = 7, limit: int = 45) -> str:
    try:
        rows = fetch(days)[:limit]
    except Exception:
        return ""
    if not rows:
        return ""
    now = time.time()
    lines = []
    for x in rows:
        age = (now - x["ts"]) / 3600
        when = f"{age:.0f} giờ trước" if age < 36 else time.strftime("%d/%m", time.localtime(x["ts"]))
        lines.append(f"- [{when} · {x['src']}] {x['title']} — {x['summary'][:160]} ({x['link']})")
    return (f"TIN AI {days} NGÀY QUA (code lấy từ RSS genk/Dân trí/The Verge/TechCrunch/OpenAI/Anthropic/DeepMind + Hacker "
            f"News, {time.strftime('%Y-%m-%d %H:%M')}, mới nhất trước):\n" + "\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    rows = fetch(fresh="--fresh" in argv)
    for x in rows:
        print(time.strftime("%d/%m %H:%M", time.localtime(x["ts"])), f"{x['src']:<16}", x["title"][:90])
    print(f"\n{len(rows)} tin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
