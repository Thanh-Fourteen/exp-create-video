"""Repo AI MỚI hot — nguồn ứng viên cho kho ý tưởng kênh AI (2026-10-12, research/30 §1, §5).

    .venv/bin/python -m create_video.team.repo_feed            # in danh sách (cache theo ngày)
    .venv/bin/python -m create_video.team.repo_feed --fresh    # bỏ cache

Tony 2026-10-12: kênh AI "gợi các repo hay, kiến thức repo AI mới, hot trong tuần" — rồi: lô đầu (OpenCut 93K sao, Ollama)
"không có repo nào mới". Nên chỉ lấy repo TẠO trong `WINDOW_DAYS` ngày, xếp theo sao — bằng GitHub Search API không token
(10 lần/phút). KHÔNG scrape github.com/trending (Acceptable Use — configs/sources.yaml; bản đầu 12/10 có scrape, đã gỡ).
Lọc bằng code: repo AI hoặc app cho người dùng cuối, bỏ đồ nghề dev; `enrich` lấy sẵn license/trang chủ/README để LLM
khỏi WebFetch (đọc README đốt trần $1,5 của idea_gen).
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = REPO_ROOT / "team" / "repo_feed"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) exp-create-video repo_feed"}
AI_RE = re.compile(r"\b(ai|llms?|agents?|agentic|gpt|claude|gemini|openai|diffusion|models?|ocr|tts|stt|speech|voice|"
                   r"whisper|transcri\w*|rag|chatbot|copilot|mcp|neural|vision|image gen\w*|video gen\w*|ml)\b", re.I)


def _get(url: str, timeout: int = 30) -> str:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _int(s: str | None) -> int | None:
    return int(s.replace(",", "")) if s else None


WINDOW_DAYS = 14
# Mỗi truy vấn ≤ 100 kết quả; gộp vài truy vấn để không sót repo AI ít sao hơn repo dev đình đám.
QUERIES = ["created:>{d} stars:>200", "created:>{d} stars:>50 topic:ai", "created:>{d} stars:>50 topic:llm",
           "created:>{d} stars:>50 topic:generative-ai", "created:>{d} stars:>50 ai app in:description"]
SEARCH_GAP_SEC = 6.5        # 10 lần/phút không token
# 2026-10-19 (exp/khao-sat/2026-10-19-ai/KET-QUA.md, 130 transcript 12 kênh AI Việt): repo bùng với người THƯỜNG là repo CŨ
# làm việc quen (@ai.unbox0026: LocalSend 82K, Meetily 58K), không phải repo mới tinh. → nguồn thứ hai: repo đã có tiếng,
# mọi tuổi, còn được cập nhật. Cache theo tuần (ít đổi).
EST_QUERIES = ["stars:>5000 pushed:>{p} topic:desktop-app", "stars:>5000 pushed:>{p} topic:android", "stars:>3000 pushed:>{p} "
               "alternative in:description", "stars:>5000 pushed:>{p} offline in:description", "stars:>5000 pushed:>{p} "
               "topic:self-hosted", "stars:>3000 pushed:>{p} topic:ai app in:description"]


def search(q: str) -> list[dict]:
    url = "https://api.github.com/search/repositories?q=" + urllib.request.quote(q, safe=":>") + "&sort=stars&order=desc&per_page=100"
    try:
        items = json.loads(_get(url)).get("items") or []
    except Exception:
        return []
    return [{"repo": i["full_name"], "desc": i.get("description") or "", "lang": i.get("language"),
             "stars": i.get("stargazers_count"), "created": (i.get("created_at") or "")[:10], "topics": i.get("topics") or [],
             "homepage": i.get("homepage") or "", "license": (i.get("license") or {}).get("spdx_id")} for i in items]


# Đồ nghề dev — khán giả phổ thông không dùng (research/30: ~80% repo hot tuần là loại này; chữ kỹ thuật ×0,98 vs ×2,22).
# Lọc bằng code trước khi đưa LLM: lần chạy 2026-10-12 với 30 ứng viên chưa lọc đốt hết ngân sách $1,5 vì đọc README.
DEV_RE = re.compile(r"\b(cli|terminal|sdk|frameworks?|toolkit|library|api keys?|apis?|skills?|mcp|servers?|inference|"
                    r"engine|kubernetes|k8s|sre|backend|npm|benchmarks?|cookbook|tutorials?|notebooks?|handbook|router|"
                    r"orchestrat\w*|developers?|coding agents?|claude code|codex|devops|ssh|production|fine-?tun\w*|"
                    r"rag|prompts? optimi\w*|raider|hack\w*|pentest\w*|uncensored|jailbreak|censorship|harness|headless|runtime|"
                    r"endpoints?|for agents|your (ai )?agents?|agent builder|vps|渗透)\b", re.I)
# Repo dạng APP cho người dùng cuối — nhận cả khi mô tả không có chữ "AI" (OpenCut "open-source CapCut alternative",
# PixelBoard bàn phím Android: research/30 chấm hợp khán giả nhất tuần 12/10 nhưng bị AI_RE loại).
APP_RE = re.compile(r"\b(app|desktop|android|ios|iphone|mac|windows|editor|alternative|offline|privacy-first|"
                    r"self-hosted|keyboard|browser extension|personal)\b", re.I)


CJK_DEV_RE = re.compile(r"渗透|攻防|침투|penetration|安全精选")   # \b không chạy với chữ CJK


def for_everyone(r: dict) -> bool:
    t = f"{r.get('repo', '')} {r.get('desc', '')}"
    return not DEV_RE.search(t) and not CJK_DEV_RE.search(t)


def is_ai(r: dict) -> bool:
    return bool(AI_RE.search(f"{r.get('repo', '')} {r.get('desc', '')} {' '.join(r.get('topics') or [])}"))


def fetch(fresh: bool = False) -> list[dict]:
    """Repo tạo trong WINDOW_DAYS ngày, là AI hoặc app cho người dùng, xếp theo sao. Cache 1 file/ngày."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    f = CACHE_DIR / f"{date.today().isoformat()}.json"
    if f.exists() and not fresh:
        return json.loads(f.read_text(encoding="utf-8"))
    since = (date.today() - timedelta(days=WINDOW_DAYS)).isoformat()
    rows: dict[str, dict] = {}
    for k, q in enumerate(QUERIES):
        if k:
            time.sleep(SEARCH_GAP_SEC)
        for r in search(q.format(d=since)):
            rows.setdefault(r["repo"], r)
    out = sorted((r for r in rows.values() if is_ai(r) or APP_RE.search(r.get("desc", ""))),
                 key=lambda r: -(r.get("stars") or 0))
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def used_repos() -> set[str]:
    """owner/repo kênh AI đã làm video (topic/nguồn trong videos/ai/*/result.json) — không gợi lại."""
    from ..paths import VIDEOS

    out: set[str] = set()
    for f in (VIDEOS / "ai").glob("*/result.json"):
        try:
            t = f.read_text(encoding="utf-8")
        except OSError:
            continue
        out.update(m.lower() for m in re.findall(r"github\.com/([\w.-]+/[\w.-]+)", t))
    return out


def fetch_established(fresh: bool = False) -> list[dict]:
    """Repo ĐÃ CÓ TIẾNG (mọi tuổi, push trong 60 ngày), dạng app cho người dùng, xếp theo sao. Cache theo tuần."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    y, w, _ = date.today().isocalendar()
    f = CACHE_DIR / f"est-{y}-W{w:02d}.json"
    if f.exists() and not fresh:
        return json.loads(f.read_text(encoding="utf-8"))
    pushed = (date.today() - timedelta(days=60)).isoformat()
    rows: dict[str, dict] = {}
    for k, q in enumerate(EST_QUERIES):
        if k:
            time.sleep(SEARCH_GAP_SEC)
        for r in search(q.format(p=pushed)):
            rows.setdefault(r["repo"], r)
    out = sorted((r for r in rows.values() if for_everyone(r) and (is_ai(r) or APP_RE.search(r.get("desc", "")))),
                 key=lambda r: -(r.get("stars") or 0))
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def enrich(r: dict) -> dict:
    """Đoạn đầu README + có demo không (license/trang chủ/topics đã có từ Search) — code lấy sẵn để LLM KHỎI WebFetch (2026-10-12: idea_gen kênh AI vượt
    trần $1,5 hai lần khi tự đọc README). raw.githubusercontent.com; cache cùng file ngày."""
    if r.get("readme") is not None:
        return r
    text = ""
    try:
        md = _get(f"https://raw.githubusercontent.com/{r['repo']}/HEAD/README.md", timeout=20)
        md = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)|\[([^\]]*)\]\([^)]*\)|[#*`>|_-]{2,}", r"\1", md)
        text = " ".join(md.split())[:350]
        r["has_demo_media"] = bool(re.search(r"\.(gif|mp4|webm)|youtu|demo", md, re.I))
    except Exception:
        pass
    r["readme"] = text
    return r


def _lines(rows: list[dict]) -> list[str]:
    return [f"- github.com/{r['repo']} — {r.get('desc', '')[:140]} | tạo {r.get('created') or '?'}, "
            f"{r.get('stars') or '?'} sao | license {r.get('license') or '?'} | trang chủ {r.get('homepage') or '—'} | "
            f"demo ảnh/video trong README: {'có' if r.get('has_demo_media') else 'không thấy'}\n"
            f"  README: {r.get('readme') or '—'}" for r in rows]


def established_block(limit: int = 10) -> str:
    """Khối "repo đã có tiếng" — xoay theo ngày trong tuần để mỗi sáng thấy một phần khác, bỏ repo kênh đã làm."""
    try:
        used = used_repos()
        pool = [r for r in fetch_established() if r["repo"].lower() not in used]
        if not pool:
            return ""
        k = (date.today().weekday() * limit) % len(pool)
        rows = [enrich(r) for r in (pool[k:] + pool[:k])[:limit]]
    except Exception:
        return ""
    return ("REPO ĐÃ CÓ TIẾNG (mọi tuổi, vẫn được cập nhật, ≥ 3–5 nghìn sao — code lấy từ GitHub Search, đã bỏ repo kênh từng làm). "
            "Video repo bùng nhất với người thường là loại này: app quen việc (gửi file, ghi biên bản, chỉnh ảnh) — kể như "
            "'có app miễn phí làm X', KHÔNG kể như tin mới:\n" + "\n".join(_lines(rows)))


def prompt_block(limit: int = 15) -> str:
    """Khối chèn vào prompt idea_gen. Rỗng nếu không lấy được gì (idea_gen vẫn chạy bằng WebSearch)."""
    try:
        all_rows = fetch()
        # repo AI trước, app thường sau; mỗi chủ tối đa 2 (12/10: "storytold/*craft" chiếm 7/15 chỗ)
        pool = sorted((r for r in all_rows if for_everyone(r)), key=lambda r: (not is_ai(r), -(r.get("stars") or 0)))
        per: dict[str, int] = {}
        rows = []
        for r in pool:
            owner = r["repo"].split("/")[0]
            if per.get(owner, 0) < 2 and len(rows) < limit:
                per[owner] = per.get(owner, 0) + 1
                rows.append(enrich(r))
        (CACHE_DIR / f"{date.today().isoformat()}.json").write_text(json.dumps(all_rows, ensure_ascii=False, indent=1) + "\n",
                                                                   encoding="utf-8")   # enrich sửa tại chỗ → lưu lại cache
    except Exception:
        return ""
    if not rows:
        return ""
    lines = _lines(rows)
    return (f"ỨNG VIÊN REPO MỚI (tạo trong {WINDOW_DAYS} ngày) — AI hoặc app mã nguồn mở cho người dùng (code lấy từ GitHub Search, "
            f"{date.today().isoformat()}, code đã loại đồ nghề dev và lấy sẵn license/trang chủ/README — KHÔNG cần WebFetch). "
            "Chọn repo hợp khán giả từ đây; không đủ thì bổ sung bằng ý tưởng dạng khác:\n" + "\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    rows = fetch(fresh="--fresh" in argv)
    for r in rows:
        print(f"{r.get('stars_week') or 0:>6}  {r['repo']:<45} {r.get('desc', '')[:80]}")
    print(f"\n{len(rows)} repo AI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
