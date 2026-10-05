"""Vai TREND SCOUT (P5.S1): hôm nay có chủ đề AI nào đáng làm video — có nguồn, điểm, snapshot.

    python -m create_video.team.trend_scout                    # chạy cho bây giờ → team/trends/<ngày>-<am|pm>.json
    python -m create_video.team.trend_scout --as-of 2026-09-28 # backfill một ngày (nguồn lọc được theo ngày)

Thiết kế — `research/probes/p5-s1-research.md` §4; nguồn + trọng số — `configs/sources.yaml`.
Chia việc đúng research/10 §1 và luật P5: **code** thu, dedupe, gom cụm, tính velocity/điểm;
**LLM** (một lần `run_role` context mới) chỉ chấm cái code không chấm được — chủ đề có hợp khán
giả VN không (lý do), giải thích được trong 40 giây không — và rút claim kèm trích. **Code** giữ
claim khi trích có nguyên văn trong snapshot sha256 (`team/snapshots/`), để fact-checker P4.S3
đối chiếu lại được.
"""

from __future__ import annotations

import email.utils
import json
import math
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import yaml
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("HF_HOME", str(REPO_ROOT / "exp" / "hf-cache"))
TRENDS_DIR = REPO_ROOT / "team" / "trends"
VN_TZ = timezone(timedelta(hours=7))
EMBED_MODEL = "intfloat/multilingual-e5-base"
GITHUB_GAP_SEC = 6.5        # không token: 10 req/phút
ARXIV_GAP_SEC = 3.1         # 1 req / 3s


def load_config() -> dict:
    return yaml.safe_load((REPO_ROOT / "configs" / "sources.yaml").read_text(encoding="utf-8"))


# ── Item ─────────────────────────────────────────────────────────────────────
@dataclass
class Item:
    url: str
    title: str
    source: str
    kind: str
    published_at: str                  # ISO UTC
    summary: str = ""
    metrics: dict = field(default_factory=dict)
    velocity_raw: float = 0.0
    velocity: float = 0.0              # percentile trong nguồn, 0–1
    decay: float = 1.0
    discussion_url: str = ""
    snapshot_sha256: str = ""


def canon_url(u: str) -> str:
    """Bỏ utm/ref, fragment, '/' cuối; arXiv pdf/html/vN → abs."""
    p = urlparse(u.strip())
    q = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith(("utm_", "ref", "source"))]
    path = p.path.rstrip("/")
    if p.netloc.endswith("arxiv.org"):
        m = re.search(r"(\d{4}\.\d{4,5})", path)
        if m:
            return f"https://arxiv.org/abs/{m.group(1)}"
    return urlunparse((p.scheme or "https", p.netloc.lower().removeprefix("www."), path, "", urlencode(q), ""))


def _dt(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        try:
            d = email.utils.parsedate_to_datetime(s)
        except Exception:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _iso(d: datetime) -> str:
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── HTTP ─────────────────────────────────────────────────────────────────────
_last: dict[str, float] = {}


def _get(url: str, *, gap: float = 0.0, key: str = "", timeout_s: float = 30, **kw):
    import httpx

    if gap:
        wait = gap - (time.time() - _last.get(key, 0.0))
        if wait > 0:
            time.sleep(wait)
    from .snapshot import UA

    headers = {"User-Agent": UA, **kw.pop("headers", {})}
    for attempt in range(3):
        try:
            r = httpx.get(url, headers=headers, timeout=timeout_s, follow_redirects=True, **kw)
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout):
            # mạng nhà chập chờn (DNS lỗi giữa chừng — probe 2026-10-02): thử lại 2 lần
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))
            continue
        _last[key] = time.time()
        if r.status_code in (429, 503) and attempt < 2:
            # arXiv/GitHub bảo chậm lại: chờ theo Retry-After (trần 60s), không dội tiếp
            time.sleep(min(60.0, float(r.headers.get("Retry-After") or 20 * (attempt + 1))))
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r


# ── Thu thập — mỗi hàm trả list[Item] cho mốc `as_of` ────────────────────────
def _is_ai(text: str, kw: list[str]) -> bool:
    t = f" {text.lower()} "
    return any(k in t for k in kw)


def collect_hf_daily(src: dict, as_of: datetime, cfg: dict) -> list[Item]:
    out = []
    for back in (0, 1):
        day = (as_of.astimezone(VN_TZ) - timedelta(days=back)).strftime("%Y-%m-%d")
        for p in _get(f"{src['url']}?date={day}").json():
            pp = p.get("paper", p)
            aid = pp.get("id")
            if not aid:
                continue
            pub = _dt(p.get("submittedOnDailyAt") or pp.get("submittedOnDailyAt") or pp.get("publishedAt"))
            out.append(Item(url=f"https://arxiv.org/abs/{aid}", title=pp.get("title", "").strip(),
                            source=src["name"], kind=src["kind"], published_at=_iso(pub or as_of),
                            summary=(pp.get("summary") or "")[:400],
                            metrics={"upvotes": pp.get("upvotes", 0)},
                            velocity_raw=float(pp.get("upvotes", 0) or 0),
                            discussion_url=f"https://huggingface.co/papers/{aid}"))
    return out


def collect_arxiv(src: dict, as_of: datetime, cfg: dict) -> list[Item]:
    end = as_of.astimezone(timezone.utc)
    start = end - timedelta(days=2)
    rng = f"[{start:%Y%m%d%H%M} TO {end:%Y%m%d%H%M}]"
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for cat in src.get("cats", ["cs.AI"]):
        q = f"cat:{cat} AND submittedDate:{rng}"
        xml = _get(src["url"], params={"search_query": q, "max_results": src.get("max_results", 100),
                                       "sortBy": "submittedDate"}, gap=ARXIV_GAP_SEC, key="arxiv", timeout_s=90).text
        for e in ET.fromstring(xml).findall("a:entry", ns):
            g = lambda t: " ".join((e.findtext(f"a:{t}", "", ns) or "").split())
            out.append(Item(url=canon_url(g("id")), title=g("title"), source=src["name"], kind=src["kind"],
                            published_at=_iso(_dt(g("published")) or end), summary=g("summary")[:400]))
    return out


def collect_hn(src: dict, as_of: datetime, cfg: dict) -> list[Item]:
    t1 = int(as_of.timestamp())
    t0 = t1 - 48 * 3600
    out = []
    for page in range(3):
        d = _get(src["url"], params={"tags": "story", "hitsPerPage": 100, "page": page,
                                     "numericFilters": f"created_at_i>{t0},created_at_i<{t1},points>{src.get('min_points', 30)}"}).json()
        for h in d.get("hits", []):
            title = h.get("title") or ""
            if not _is_ai(title, cfg["ai_keywords"]):
                continue
            created = datetime.fromtimestamp(h["created_at_i"], timezone.utc)
            age_h = max(1.0, (as_of - created).total_seconds() / 3600)
            hn = f"https://news.ycombinator.com/item?id={h['objectID']}"
            out.append(Item(url=canon_url(h.get("url") or hn), title=title, source=src["name"], kind=src["kind"],
                            published_at=_iso(created), metrics={"points": h.get("points"), "comments": h.get("num_comments")},
                            velocity_raw=(h.get("points") or 0) / age_h, discussion_url=hn))
        if page + 1 >= d.get("nbPages", 0):
            break
    return out


def collect_github(src: dict, as_of: datetime, cfg: dict) -> list[Item]:
    end = as_of.astimezone(timezone.utc).date()
    start = end - timedelta(days=src.get("window_days", 7))
    seen, out = set(), []
    for topic in src.get("topics", ["llm"]):
        q = f"topic:{topic} created:{start}..{end}"
        d = _get(src["url"], params={"q": q, "sort": "stars", "order": "desc", "per_page": 20},
                 headers={"Accept": "application/vnd.github+json"}, gap=GITHUB_GAP_SEC, key="github").json()
        for r in d.get("items", []):
            if r["html_url"] in seen:
                continue
            seen.add(r["html_url"])
            created = _dt(r["created_at"]) or as_of
            age_d = max(0.5, (as_of - created).total_seconds() / 86400)
            out.append(Item(url=canon_url(r["html_url"]), title=f"{r['full_name']}: {r.get('description') or ''}"[:300],
                            source=src["name"], kind=src["kind"], published_at=_iso(created),
                            summary=(r.get("description") or "")[:400],
                            metrics={"stars_now": r.get("stargazers_count")},
                            velocity_raw=(r.get("stargazers_count") or 0) / age_d))
    return out


def collect_hf_models(src: dict, as_of: datetime, cfg: dict) -> list[Item]:
    if (datetime.now(timezone.utc) - as_of) > timedelta(hours=12):
        return []      # không có lịch sử trending — chỉ dùng được cho hôm nay
    out = []
    for m in _get(src["url"]).json():
        mid = m.get("id") or m.get("modelId")
        out.append(Item(url=f"https://huggingface.co/{mid}", title=mid, source=src["name"], kind=src["kind"],
                        published_at=_iso(as_of),
                        metrics={"trendingScore": m.get("trendingScore"), "likes": m.get("likes"),
                                 "pipeline_tag": m.get("pipeline_tag"), "createdAt": m.get("createdAt")},
                        summary=f"{m.get('pipeline_tag') or ''} model", velocity_raw=float(m.get("trendingScore") or 0)))
    return out


_RSS_CACHE: dict[str, str] = {}


def parse_feed(xml: str) -> list[dict]:
    """RSS 2.0 / Atom → [{title, link, date, summary}] — stdlib, khỏi thêm feedparser."""
    root = ET.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    atom = "{http://www.w3.org/2005/Atom}"
    out = []
    for it in root.iter("item"):
        out.append({"title": (it.findtext("title") or "").strip(), "link": (it.findtext("link") or "").strip(),
                    "date": it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date"),
                    "summary": re.sub(r"<[^>]+>", " ", it.findtext("description") or "")[:400]})
    for e in root.iter(f"{atom}entry"):
        link = e.find(f"{atom}link")
        out.append({"title": (e.findtext(f"{atom}title") or "").strip(),
                    "link": (link.get("href") if link is not None else "") or "",
                    "date": e.findtext(f"{atom}published") or e.findtext(f"{atom}updated"),
                    "summary": re.sub(r"<[^>]+>", " ", e.findtext(f"{atom}summary") or "")[:400]})
    return out


def collect_rss(src: dict, as_of: datetime, cfg: dict) -> list[Item]:
    if src["rss"] not in _RSS_CACHE:
        _RSS_CACHE[src["rss"]] = _get(src["rss"]).text
    max_age = timedelta(days=cfg["scoring"]["max_age_days"])
    out = []
    for e in parse_feed(_RSS_CACHE[src["rss"]]):
        d = _dt(e["date"])
        if not e["link"] or d is None or d > as_of or as_of - d > max_age:
            continue
        if src["kind"] == "news_vn" and not _is_ai(f"{e['title']} {e['summary']}", cfg["ai_keywords"]):
            continue
        out.append(Item(url=canon_url(e["link"]), title=e["title"], source=src["name"], kind=src["kind"],
                        published_at=_iso(d), summary=" ".join(e["summary"].split())))
    return out


def collect_vn_pulse(src: dict, as_of: datetime, cfg: dict) -> list[str]:
    """Từ khoá Google Trends VN (hôm nay) — đo "phổ thông", không phải topic."""
    if (datetime.now(timezone.utc) - as_of) > timedelta(hours=12):
        return []
    return [e["title"].lower() for e in parse_feed(_get(src["rss"]).text) if e["title"]]


COLLECTORS = {"hf_daily_papers": collect_hf_daily, "arxiv": collect_arxiv, "hn": collect_hn,
              "github": collect_github, "hf_models": collect_hf_models}


def collect(as_of: datetime, cfg: dict) -> tuple[list[Item], list[str], dict]:
    items: list[Item] = []
    pulse: list[str] = []
    status: dict[str, Any] = {}
    for src in cfg["sources"]:
        try:
            if src["kind"] == "vn_pulse":
                pulse = collect_vn_pulse(src, as_of, cfg)
                status[src["name"]] = len(pulse)
                continue
            fn = COLLECTORS.get(src["name"]) or (collect_rss if "rss" in src else None)
            got = fn(src, as_of, cfg) if fn else []
            items += got
            status[src["name"]] = len(got)
        except Exception as e:
            status[src["name"]] = f"lỗi: {type(e).__name__}: {e}"[:200]
    max_age = timedelta(days=cfg["scoring"]["max_age_days"])
    by_url: dict[str, Item] = {}
    for it in items:
        d = _dt(it.published_at)
        if not it.title or d is None or as_of - d > max_age or d > as_of + timedelta(hours=1):
            continue
        # cùng URL từ nhiều nguồn (HF daily + arXiv) → giữ bản có velocity cao, nhớ nguồn kia
        k = it.url
        if k in by_url:
            keep = by_url[k]
            keep.metrics.setdefault("also", []).append(it.source)
            if it.velocity_raw > keep.velocity_raw:
                it.metrics["also"] = keep.metrics["also"]
                by_url[k] = it
        else:
            by_url[k] = it
    return list(by_url.values()), pulse, status


# ── Velocity, gom cụm, điểm (code) ───────────────────────────────────────────
def normalize(items: list[Item], as_of: datetime, sc: dict) -> None:
    by_src: dict[str, list[Item]] = {}
    for it in items:
        by_src.setdefault(it.source, []).append(it)
    for src, its in by_src.items():
        if all(i.velocity_raw == 0 for i in its):
            for i in its:
                i.velocity = sc["blog_news_velocity"] if i.kind in ("blog", "news_vn") else 0.2
            continue
        vals = sorted(i.velocity_raw for i in its)
        n = len(vals)
        for i in its:
            below = sum(v < i.velocity_raw for v in vals)
            i.velocity = round((below + 0.5 * vals.count(i.velocity_raw)) / n, 4)
    for it in items:
        age_h = max(0.0, (as_of - _dt(it.published_at)).total_seconds() / 3600)
        it.decay = round(math.exp(-age_h / sc["decay_hours"]), 4)


class Embedder:
    def __init__(self, model_id: str = EMBED_MODEL):
        self.model_id = model_id
        self._m = self._tok = None
        self.device = "cpu"

    def _load(self):
        import torch
        from transformers import AutoModel, AutoTokenizer

        from ..qc.loop import gpu_free_mib

        free = gpu_free_mib()
        # TREND_DEVICE=cpu: nút "Tìm chủ đề mới" trên web có thể bấm lúc worker đang dựng video — không giành GPU
        # với FLUX/aligner (CLAUDE.md: không nạp hai khối GPU cùng lúc). 2026-10-04.
        cpu_only = os.environ.get("TREND_DEVICE") == "cpu"
        self.device = "cuda" if not cpu_only and torch.cuda.is_available() and (free or 0) > 1500 else "cpu"
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self._tok = AutoTokenizer.from_pretrained(self.model_id)
        self._m = AutoModel.from_pretrained(self.model_id, torch_dtype=dtype).to(self.device).eval()

    def encode(self, texts: list[str], bs: int = 32):
        import numpy as np
        import torch

        if self._m is None:
            self._load()
        outs = []
        with torch.no_grad():
            for i in range(0, len(texts), bs):
                b = self._tok([f"query: {t}" for t in texts[i:i + bs]], padding=True, truncation=True,
                              max_length=256, return_tensors="pt").to(self.device)
                h = self._m(**b).last_hidden_state
                mask = b["attention_mask"].unsqueeze(-1).to(h.dtype)
                v = (h * mask).sum(1) / mask.sum(1)
                outs.append(torch.nn.functional.normalize(v.float(), dim=-1).cpu().numpy())
        return np.concatenate(outs) if outs else np.zeros((0, 768), dtype="float32")

    def close(self):
        import gc

        import torch

        self._m = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def _item_text(it: Item) -> str:
    return f"{it.title}. {it.summary[:300]}"


_GENERIC = {"ai", "llm", "llms", "gguf", "model", "models", "open", "local", "show", "hn", "the", "new",
            "openai", "google", "meta", "anthropic", "nvidia", "microsoft", "apple", "deepmind", "hugging",
            "face", "github", "chatgpt", "gpu", "api", "app", "agent", "agents", "trung", "quốc", "mỹ", "việt",
            "nam", "instruct", "base", "chat", "pdf", "video", "image", "bench", "benchmark", "mlx", "coder",
            "lora", "uncensored", "turbo", "flash", "pro", "mini", "large", "small", "fp8", "awq"}


def entity_keys(title: str) -> set[str]:
    """Tên riêng trong tiêu đề → khoá so khớp: 'GPT-6.1 Sol' → {gpt-6.1, sol}; 'Qwen/Qwen-Image-2.1' và
    'Local Qwen-Image 2.1 studio' → {qwen-image}. Token có chữ số, CamelCase, hoặc viết hoa giữa câu;
    bỏ tên hãng/từ chung (`_GENERIC`) — chung 'OpenAI' không làm hai tin thành một chủ đề."""
    keys: set[str] = set()
    toks = re.split(r"[\s:,;()\[\]\"'“”|]+", title)
    words = [t for t in toks if re.match(r"[^\W\d_]", t)]
    # Tiêu đề Anh kiểu Title Case: mọi từ đều hoa → "viết hoa" không còn nghĩa là tên riêng.
    title_case = len(words) >= 3 and sum(w[0].isupper() for w in words) / len(words) >= 0.6
    for k, raw in enumerate(toks):
        t = raw.split("/")[-1].strip(".!?")
        if len(t) < 3 or not re.search(r"[A-Za-z]", t):
            continue
        has_digit = bool(re.search(r"\d", t))
        camel = bool(re.search(r"[a-z][A-Z]|[A-Z]{2,}[a-z]?", t))
        proper = t[0].isupper() and k > 0 and not title_case
        if not (has_digit or camel or proper or "/" in raw):
            continue
        parts = [x for x in re.split(r"[-_]", t.lower()) if x]
        if not parts:
            continue
        key = parts[0] if re.search(r"\d", parts[0]) or len(parts) == 1 else f"{parts[0]}-{parts[1]}"
        if key not in _GENERIC and parts[0] not in _GENERIC and len(key) >= 3:
            keys.add(key)
    return keys


def linked(sim: float, ka: set[str], kb: set[str], sc: dict) -> bool:
    """Cùng chủ đề khi cosine rất cao, hoặc cosine khá + chung tên riêng (p5-s1-research.md §4b)."""
    return sim >= sc["cluster_cos_strong"] or (sim >= sc["cluster_cos"] and bool(ka & kb))


def cluster(vecs, cos: float, max_items: int, keys: list[set[str]] | None = None,
            strong: float | None = None, order: list[int] | None = None) -> list[list[int]]:
    """Gom kiểu LEADER: duyệt item theo `order` (mạnh nhất trước); item vào cụm đầu tiên mà nó
    `linked` TRỰC TIẾP với hạt nhân (item đầu cụm), không thì thành hạt nhân mới. Không nối chuỗi —
    union-find từng gộp A–B–C khi chỉ A–B và B–C giống nhau (repo lạc vào cụm Barclays, §4b).
    `keys=None` → chỉ cosine."""
    n = len(vecs)
    order = list(order) if order is not None else list(range(n))
    sc = {"cluster_cos": cos, "cluster_cos_strong": strong if strong is not None else cos}
    seeds: list[int] = []
    groups: list[list[int]] = []
    for i in order:
        placed = False
        for g, seed in zip(groups, seeds):
            if len(g) >= max_items:
                continue
            sim = float(vecs[i] @ vecs[seed])
            ok = sim >= cos if keys is None else linked(sim, keys[i], keys[seed], sc)
            if ok:
                g.append(i)
                placed = True
                break
        if not placed:
            seeds.append(i)
            groups.append([i])
    return groups


def done_topics(window_days: int) -> list[str]:
    cut = time.time() - window_days * 86400
    out = []
    for p in (REPO_ROOT / "out").glob("*/script.json"):
        if p.stat().st_mtime < cut:
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            out.append(f"{d.get('hook', '')} {str(d.get('topic', ''))[:200]}")
        except Exception:
            pass
    return out


@dataclass
class Cluster:
    id: int
    items: list[Item]
    hot: float = 0.0
    parts: dict = field(default_factory=dict)
    kinds: list[str] = field(default_factory=list)
    label_vi: str = ""
    vn_fit_reason: str = ""
    explainable_40s: bool | None = None
    explain_reason: str = ""
    claims: list[dict] = field(default_factory=list)
    rank: int = 0


def score_clusters(items: list[Item], groups: list[list[int]], vecs, done_vecs, pulse: list[str],
                   cfg: dict, done_texts: list[str] | None = None) -> list[Cluster]:
    sc = cfg["scoring"]
    done_keys = [entity_keys(t) for t in (done_texts or [])]
    if done_vecs is not None and len(done_keys) < len(done_vecs):
        done_keys += [set()] * (len(done_vecs) - len(done_keys))
    w = {s["kind"]: s["weight"] for s in cfg["sources"]}
    w_src = {s["name"]: s["weight"] for s in cfg["sources"]}
    out = []
    for cid, g in enumerate(groups):
        its = sorted((items[i] for i in g), key=lambda i: -i.velocity * i.decay)
        kinds = sorted({i.kind for i in its})
        # arXiv chỉ là bằng chứng: cụm toàn arXiv không thành topic
        if kinds == ["paper"] and all(i.source == "arxiv" for i in its):
            continue
        # Mỗi NGUỒN góp item mạnh nhất của nó — 8 bản quantize cùng một model trên HF không
        # được cộng thành 8 lần độ nóng (thấy ở lần chạy thử 2026-10-02, research §4b).
        best: dict[str, float] = {}
        for i in its:
            x = w_src.get(i.source, w.get(i.kind, 0.5)) * i.velocity * i.decay
            best[i.source] = max(best.get(i.source, 0.0), x)
        base = sum(best.values())
        multi = sc["multi_kind_bonus"] * (len(kinds) - 1)
        vn = sc["vn_news_bonus"] if "news_vn" in kinds else 0.0
        titles = " ".join(i.title.lower() for i in its)
        if pulse and any(len(p) > 3 and p in titles for p in pulse):
            vn += sc["vn_pulse_bonus"]
        hot = base + multi + vn
        dup = 0.0
        if done_vecs is not None and len(done_vecs):
            sims = vecs[g] @ done_vecs.T
            dup = float(sims.max())
            ck = set().union(*(entity_keys(i.title) for i in its))
            if any(linked(float(sims[a, b]), ck, done_keys[b], sc) for a in range(len(g)) for b in range(sims.shape[1])):
                hot *= sc["done_penalty"]
        out.append(Cluster(id=cid, items=its, hot=round(hot, 4), kinds=kinds,
                           parts={"base": round(base, 4), "multi_kind": multi, "vn_fit": vn,
                                  "dup_max_cos": round(dup, 3)}))
    out.sort(key=lambda c: -c.hot)
    return out


# ── Snapshot + LLM chấm (vai trend_judge) ────────────────────────────────────
class ClaimOut(BaseModel):
    text: str           # tiếng Việt, một sự thật kiểm được
    quote: str          # NGUYÊN VĂN từ đoạn trích của `url`
    url: str


class JudgeItem(BaseModel):
    cluster_id: int
    label_vi: str                 # tên chủ đề ngắn, tiếng Việt
    vn_fit_reason: str            # vì sao (không) hợp khán giả VN — một câu
    explainable_40s: bool
    explain_reason: str
    claims: list[ClaimOut] = []


class JudgeOut(BaseModel):
    clusters: list[JudgeItem]


JUDGE_SYSTEM = """Bạn là biên tập viên một kênh TikTok tiếng Việt về AI (khán giả Việt Nam, video 30–60 giây,
kênh có lợi thế: tự chạy model trên card RTX 2060 6GB). Code đã xếp hạng các cụm tin theo độ nóng —
bạn KHÔNG xếp hạng lại, KHÔNG chấm điểm. Với từng cụm, trả:

- label_vi: tên chủ đề ngắn bằng tiếng Việt (≤ 60 ký tự), giữ nguyên tên riêng/thuật ngữ Anh.
- vn_fit_reason: MỘT câu — người xem Việt có lý do gì để quan tâm (hoặc vì sao không).
- explainable_40s: true nếu giải thích được ý chính cho người không chuyên trong 40 giây.
  false nếu cần nhiều nền tảng toán/kỹ thuật, hoặc chỉ là tin nội bộ ngành.
- claims: 1–3 sự thật kiểm được (tên, số, ngày, tổ chức, khả năng) lấy từ ĐOẠN TRÍCH NGUỒN bên dưới.
  `quote` phải CHÉP NGUYÊN VĂN một đoạn ngắn (≤ 200 ký tự) từ đoạn trích của đúng `url` — code sẽ tìm
  chuỗi đó trong nguồn; không khớp là claim bị bỏ. Không có gì kiểm được thì để claims rỗng.
  Không dùng hiểu biết riêng."""


def judge_prompt(clusters: list[Cluster], snaps: dict[str, Any], chars: int) -> str:
    parts = []
    for c in clusters:
        lines = [f"### Cụm {c.id} · nguồn: {', '.join(c.kinds)}"]
        for it in c.items[:6]:
            lines.append(f"- [{it.source}] {it.title} — {it.url}")
        for it in c.items[:2]:
            s = snaps.get(it.url)
            if s is not None:
                lines.append(f"ĐOẠN TRÍCH NGUỒN {it.url}:\n{s.text[:chars]}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts) + "\n\nTrả JSON cho mọi cụm."


ITEMS_PER_CLUSTER = 6     # item hiện trong output + được snapshot; điểm `hot` vẫn tính trên cả cụm


def snapshot_items(clusters: list[Cluster]) -> tuple[dict, list[str]]:
    """Snapshot song song (8 luồng; arXiv tự xếp hàng 3s/lần trong snapshot.py). URL không tải
    được = chết → bỏ khỏi output (Xong khi: 100% item có url sống)."""
    from concurrent.futures import ThreadPoolExecutor

    from .snapshot import fetch

    def one(it: Item):
        try:
            s = fetch(it.url, allow_any=True)
            if s.chars < 40:
                raise ValueError("trang rỗng")
            return it, s, None
        except Exception as e:
            return it, None, f"{it.url} ({type(e).__name__})"

    todo = [it for c in clusters for it in c.items[:ITEMS_PER_CLUSTER]]
    snaps, dead = {}, []
    with ThreadPoolExecutor(8) as ex:
        for it, s, err in ex.map(one, todo):
            if s is not None:
                snaps[it.url] = s
                it.snapshot_sha256 = s.sha256
            else:
                dead.append(err)
    for c in clusters:
        c.items = [it for it in c.items[:ITEMS_PER_CLUSTER] if it.snapshot_sha256]
    return snaps, dead


def gate_claims(clusters: list[Cluster], judged: JudgeOut, snaps: dict) -> int:
    from ..qc.t4_facts import quote_in

    by = {j.cluster_id: j for j in judged.clusters}
    dropped = 0
    for c in clusters:
        j = by.get(c.id)
        if j is None:
            continue
        c.label_vi, c.vn_fit_reason = j.label_vi, j.vn_fit_reason
        c.explainable_40s, c.explain_reason = j.explainable_40s, j.explain_reason
        for cl in j.claims:
            s = snaps.get(canon_url(cl.url)) or snaps.get(cl.url)
            if s is not None and quote_in(cl.quote, s.text):
                c.claims.append({"text": cl.text, "quote": cl.quote, "url": s.url, "snapshot_sha256": s.sha256,
                                 "snapshot_path": s.path})
            else:
                dropped += 1
    return dropped


# ── Chạy ─────────────────────────────────────────────────────────────────────
def run(as_of: datetime | None = None, *, slot: str | None = None, out_dir: Path = TRENDS_DIR,
        keep: int = 20, judge: bool = True, model: str | None = None, embedder: Embedder | None = None) -> Path:
    from . import State, run_role

    cfg = load_config()
    sc = cfg["scoring"]
    now = datetime.now(timezone.utc)
    as_of = (as_of or now).astimezone(timezone.utc)
    local = as_of.astimezone(VN_TZ)
    slot = slot or ("am" if local.hour < 12 else "pm")
    if slot == "r":   # chạy tay từ web (2026-10-04) — tên sau "pm" theo thứ tự chữ nên thành file mới nhất trong ngày
        slot = f"r{local:%H%M}"
    name = f"{local:%Y-%m-%d}-{slot}"
    t0 = time.time()

    items, pulse, status = collect(as_of, cfg)
    normalize(items, as_of, sc)
    own = embedder is None
    emb = embedder or Embedder()
    try:
        vecs = emb.encode([_item_text(i) for i in items])
        done = done_topics(sc["done_window_days"])
        done_vecs = emb.encode(done) if done else None
    finally:
        if own:
            emb.close()
    keys = [entity_keys(i.title) for i in items]
    order = sorted(range(len(items)), key=lambda i: -(items[i].velocity * items[i].decay))
    groups = cluster(vecs, sc["cluster_cos"], sc["max_cluster_items"], keys, sc["cluster_cos_strong"], order)
    clusters = score_clusters(items, groups, vecs, done_vecs, pulse, cfg, done)

    # Snapshot dần cho tới khi đủ `keep` cụm còn item sống (URL chết thì cụm có thể rỗng).
    kept: list[Cluster] = []
    snaps: dict = {}
    dead: list[str] = []
    pos = 0
    while len(kept) < keep and pos < len(clusters):
        batch = clusters[pos: pos + (keep - len(kept))]
        pos += len(batch)
        s, d = snapshot_items(batch)
        snaps.update(s)
        dead += d
        kept += [c for c in batch if c.items]

    out_dir.mkdir(parents=True, exist_ok=True)
    state = State.load(out_dir / f"{name}.run", video_id=f"trends-{name}")
    dropped = 0
    if judge and kept:
        top = kept[: sc["judge_top"]]
        state.begin("trend_judge", "")
        try:
            j = run_role("trend_judge", judge_prompt(top, snaps, sc["snapshot_chars"]), JudgeOut,
                         system_prompt=JUDGE_SYSTEM, tools=[], max_turns=4, max_budget_usd=2.0,
                         model=model, state=state)
            dropped = gate_claims(top, j, snaps)
            state.done("trend_judge", [])
        except Exception as e:
            state.fail("trend_judge", e)
    # LLM không đổi `hot`; chỉ explainable_40s=false → xếp sau.
    kept.sort(key=lambda c: (c.explainable_40s is False, -c.hot))
    for r, c in enumerate(kept, 1):
        c.rank = r

    doc = {
        "date": f"{local:%Y-%m-%d}", "slot": slot, "as_of": _iso(as_of), "generated_at": _iso(now),
        "backfill": (now - as_of) > timedelta(hours=12),
        "sources_status": status, "n_items": len(items), "n_clusters": len(clusters),
        "vn_pulse_terms": pulse[:30],
        "clusters": [{
            "rank": c.rank, "id": c.id, "label_vi": c.label_vi, "hot": c.hot, "score_parts": c.parts,
            "kinds": c.kinds, "explainable_40s": c.explainable_40s, "explain_reason": c.explain_reason,
            "vn_fit_reason": c.vn_fit_reason, "claims": c.claims,
            "items": [{k: v for k, v in asdict(i).items() if k not in ("summary",)} for i in c.items],
        } for c in kept],
        "dropped_claims": dropped, "dead_urls": dead,
        "llm_calls": [{k: x.get(k) for k in ("role", "wall_sec", "input_tokens", "output_tokens", "cost_usd", "error")}
                      for x in state.llm_calls],
        "wall_sec": round(time.time() - t0, 1),
    }
    path = out_dir / f"{name}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="trend scout — chủ đề AI hot → team/trends/")
    ap.add_argument("--as-of", help="YYYY-MM-DD (backfill, mốc 20:00 giờ VN) hoặc ISO đầy đủ")
    ap.add_argument("--slot", choices=["am", "pm", "r"], help="r = chạy tay (nút trên web)")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--out", type=Path, default=TRENDS_DIR)
    a = ap.parse_args(argv)
    as_of = None
    if a.as_of:
        as_of = (datetime.fromisoformat(a.as_of + "T20:00:00+07:00") if len(a.as_of) == 10
                 else datetime.fromisoformat(a.as_of))
    p = run(as_of, slot=a.slot, out_dir=a.out, judge=not a.no_judge)
    d = json.loads(p.read_text(encoding="utf-8"))
    print(f"✓ {p}  ({d['n_items']} item → {d['n_clusters']} cụm, {d['wall_sec']}s)")
    print("  nguồn: " + " · ".join(f"{k}={v}" for k, v in d["sources_status"].items()))
    for c in d["clusters"][:10]:
        e = {True: "", False: " [khó 40s]", None: ""}[c["explainable_40s"]]
        print(f"  {c['rank']:2d}. {c['hot']:.2f} {'+'.join(c['kinds']):24s} {c['label_vi'] or c['items'][0]['title'][:60]}{e}")
    print(f"  claims bị bỏ (trích sai): {d['dropped_claims']} · url chết: {len(d['dead_urls'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
