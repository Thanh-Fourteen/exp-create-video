"""Snapshot nguồn: URL → text sạch, lưu theo sha256 ở `team/snapshots/`.

    python -m create_video.team.snapshot https://huggingface.co/ByteDance/SDXL-Lightning

Vì sao có file này (research/10 §3, P4.S3): fact-checker phải đối chiếu với **thứ đã
lưu**, không với trí nhớ của LLM, và trích dẫn của nó phải kiểm được bằng code
(`quote in text`). Trend scout (P5.S1) dùng lại đúng hàm này để lưu nguồn của tin.

Lấy text qua **API có cấu trúc** khi có — sạch hơn bóc HTML, và có metadata (ngày,
tổ chức, license) mà fact-check cần nhất:

- huggingface.co/<org>/<model> → `api/models/<id>` (author, createdAt, license) + raw README
- arxiv.org/abs/<id> → export API Atom (tiêu đề, tác giả, ngày nộp, abstract); ≥ 3s/lần
- github.com/<owner>/<repo> → `api.github.com/repos/...` (owner, created_at, license) + README
- `research/probes/*.md` → đọc file local (số đo của chính kênh)
- domain khác trong `ALLOWLIST` → HTML → text bằng `html.parser` stdlib

Domain ngoài `ALLOWLIST` thì KHÔNG tải — nguồn lạ là nguồn không đáng đối chiếu. Riêng trend
scout (P5.S1) gọi `fetch(url, allow_any=True)`: bài HN dẫn đi khắp nơi, vẫn phải lưu để claim
trích được — snapshot đó mang `kind=article` để fact-checker biết không phải nguồn gốc.
Trang bài viết (blog, báo, article) bóc bằng trafilatura (Apache-2.0), hỏng thì lùi về `html.parser`.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
SNAP_DIR = REPO_ROOT / "team" / "snapshots"
UA = "exp-create-video-factcheck/0.1 (personal research; contact via github.com/teamtriscec)"

# Trang gốc: model card, paper, repo, blog chính chủ. Tin tức/tổng hợp KHÔNG có ở đây —
# fact-check đối chiếu với nguồn gốc, không với bài viết lại.
ALLOWLIST = {
    "huggingface.co", "arxiv.org", "export.arxiv.org", "github.com", "api.github.com",
    "raw.githubusercontent.com", "anthropic.com", "www.anthropic.com", "docs.anthropic.com",
    "openai.com", "deepmind.google", "blog.google", "ai.google.dev", "ai.meta.com",
    "mistral.ai", "qwenlm.github.io", "qwen.ai", "api-docs.deepseek.com", "deepseek.com",
    "developer.nvidia.com", "pytorch.org", "stability.ai", "bfl.ai", "blackforestlabs.ai",
}
MAX_CHARS = 60_000         # README khổng lồ (diffusers) — đủ phần đầu, nơi có thông tin chính
ARXIV_GAP_SEC = 3.0        # điều khoản arXiv API: 1 request / 3 giây
_last_arxiv = 0.0
import threading as _threading

_ARXIV_LOCK = _threading.Lock()   # trend scout tải song song — arXiv vẫn 1 kết nối, 3s/lần
_INDEX_LOCK = _threading.Lock()


@dataclass
class Snapshot:
    url: str
    kind: str            # hf | arxiv | github | local | html
    sha256: str
    fetched_at: str
    chars: int
    path: str            # tương đối repo
    text: str = ""

    def meta(self) -> dict:
        d = asdict(self)
        d.pop("text")
        return d


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "header", "footer", "noscript", "svg"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "header", "footer", "noscript", "svg") and self._skip:
            self._skip -= 1
        if tag in ("p", "div", "li", "h1", "h2", "h3", "h4", "tr", "br", "section"):
            self.out.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.out.append(data)


def article_text(html: str, url: str = "") -> str:
    """trafilatura bỏ menu/footer/quảng cáo — `html.parser` thuần kéo theo cả trang."""
    try:
        import trafilatura

        t = trafilatura.extract(html, url=url or None, include_comments=False, include_tables=True,
                                favor_recall=True, with_metadata=True)
        if t and len(t) > 200:
            return t
    except Exception:
        pass
    return html_to_text(html)


def html_to_text(html: str) -> str:
    p = _Text()
    p.feed(html)
    t = "".join(p.out)
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()


def _legacy_ssl():
    """vfa.gov.vn (Cục ATTP — nguồn tier1 kênh mẹo) dùng khoá DH < 2048 bit → OpenSSL 3 từ chối DH_KEY_TOO_SMALL
    (demo K5 2026-10-04 mất 8/15 sự thật vì vậy). Thử lại với SECLEVEL=1: vẫn kiểm chứng chỉ + tên miền, chỉ nhận khoá
    DH ngắn hơn. Chỉ để ĐỌC trang công khai, không gửi dữ liệu gì."""
    import ssl

    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
    return ctx


def _get(url: str, timeout_s: float = 30, **kw):
    import httpx

    headers = {"User-Agent": UA, **kw.pop("headers", {})}
    try:
        r = httpx.get(url, headers=headers, timeout=timeout_s, follow_redirects=True, **kw)
    except httpx.ConnectError as e:
        if "DH_KEY_TOO_SMALL" not in str(e):
            raise
        r = httpx.get(url, headers=headers, timeout=timeout_s, follow_redirects=True, verify=_legacy_ssl(), **kw)
    r.raise_for_status()
    return r


def _fetch_hf(path: str) -> str:
    parts = [p for p in path.strip("/").split("/") if p]
    if parts and parts[0] in ("datasets", "spaces"):
        kind, rid = parts[0], "/".join(parts[1:3])
    else:
        kind, rid = "models", "/".join(parts[:2])
    api = _get(f"https://huggingface.co/api/{kind}/{rid}").json()
    meta = {k: api.get(k) for k in ("id", "author", "createdAt", "lastModified", "downloads",
                                    "likes", "pipeline_tag", "library_name") if api.get(k) is not None}
    lic = [t.split(":", 1)[1] for t in api.get("tags", []) if t.startswith("license:")]
    if lic:
        meta["license"] = lic
    prefix = "" if kind == "models" else f"{kind}/"
    try:
        readme = _get(f"https://huggingface.co/{prefix}{rid}/raw/main/README.md").text
    except Exception:
        readme = ""
    return f"[HF API metadata]\n{json.dumps(meta, ensure_ascii=False, indent=1)}\n\n[README.md]\n{readme}"


def _fetch_arxiv(path: str) -> str:
    global _last_arxiv
    m = re.search(r"(?:abs|pdf|html)/([0-9]{4}\.[0-9]{4,5}|[a-z\-]+/[0-9]{7})", path)
    if not m:
        raise ValueError(f"không nhận ra id arXiv trong {path!r}")
    aid = m.group(1)
    with _ARXIV_LOCK:
        wait = ARXIV_GAP_SEC - (time.time() - _last_arxiv)
        if wait > 0:
            time.sleep(wait)
        try:
            xml = _get(f"https://export.arxiv.org/api/query?id_list={aid}").text
        finally:
            _last_arxiv = time.time()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = ET.fromstring(xml).find("a:entry", ns)
    if e is None:
        raise ValueError(f"arXiv không trả entry cho {aid}")
    g = lambda tag: " ".join((e.findtext(f"a:{tag}", "", ns) or "").split())
    authors = [" ".join((a.findtext("a:name", "", ns) or "").split()) for a in e.findall("a:author", ns)]
    return (f"[arXiv {aid}]\nTitle: {g('title')}\nAuthors: {', '.join(authors)}\n"
            f"Submitted (v1): {g('published')}\nUpdated: {g('updated')}\n\nAbstract: {g('summary')}")


def _fetch_github(path: str) -> str:
    parts = [p for p in path.strip("/").split("/") if p][:2]
    if len(parts) < 2:
        raise ValueError(f"cần github.com/<owner>/<repo>, có {path!r}")
    repo = "/".join(parts)
    api = _get(f"https://api.github.com/repos/{repo}", headers={"Accept": "application/vnd.github+json"}).json()
    meta = {k: api.get(k) for k in ("full_name", "description", "created_at", "pushed_at",
                                    "stargazers_count", "homepage")}
    meta["owner"] = (api.get("owner") or {}).get("login")
    meta["license"] = (api.get("license") or {}).get("spdx_id")
    try:
        readme = _get(f"https://api.github.com/repos/{repo}/readme",
                      headers={"Accept": "application/vnd.github.raw"}).text
    except Exception:
        readme = ""
    return f"[GitHub API metadata]\n{json.dumps(meta, ensure_ascii=False, indent=1)}\n\n[README]\n{readme}"


def classify(url: str) -> tuple[str, str]:
    """→ (kind, host). kind = local | hf | arxiv | github | html | blocked."""
    if url.startswith("research/probes/") or url.startswith(str(REPO_ROOT / "research" / "probes")):
        return "local", ""
    u = urlparse(url)
    host = (u.hostname or "").lower()
    if host not in ALLOWLIST:
        from ..channel import current   # kênh mẹo (2026-10-04): tier1/tier2 của kênh được đối chiếu

        if host not in current().fact_domains:
            return "blocked", host
    if host == "huggingface.co":
        return "hf", host
    if host in ("arxiv.org", "export.arxiv.org"):
        return "arxiv", host
    if host == "github.com":
        return "github", host
    return "html", host


def _index_path() -> Path:
    return SNAP_DIR / "index.json"


def _load_index() -> dict:
    p = _index_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def fetch(url: str, *, refresh: bool = False, allow_any: bool = False) -> Snapshot:
    """URL → Snapshot (có cache). Raise nếu domain ngoài allowlist hoặc tải hỏng."""
    url = url.strip()
    idx = _load_index()
    if not refresh and url in idx:
        m = idx[url]
        p = REPO_ROOT / m["path"]
        if p.exists():
            return Snapshot(**m, text=p.read_text(encoding="utf-8"))

    kind, host = classify(url)
    if kind == "blocked" and allow_any and url.startswith(("http://", "https://")):
        kind = "article"
    if kind == "blocked":
        raise PermissionError(f"{host!r} ngoài ALLOWLIST nguồn gốc — không đối chiếu với nguồn lạ")
    u = urlparse(url)
    if kind == "local":
        p = Path(url) if Path(url).is_absolute() else REPO_ROOT / url
        p = p.resolve()
        if (REPO_ROOT / "research" / "probes").resolve() not in p.parents:
            raise PermissionError(f"{url!r} không nằm trong research/probes/")
        text = p.read_text(encoding="utf-8")
    elif kind == "hf":
        text = _fetch_hf(u.path)
    elif kind == "arxiv":
        text = _fetch_arxiv(u.path)
    elif kind == "github":
        text = _fetch_github(u.path)
    else:
        text = article_text(_get(url, timeout_s=12).text, url)
    text = text[:MAX_CHARS]

    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAP_DIR / f"{sha[:16]}.txt"
    path.write_text(text, encoding="utf-8")
    snap = Snapshot(url=url, kind=kind, sha256=sha, fetched_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    chars=len(text), path=str(path.relative_to(REPO_ROOT)), text=text)
    with _INDEX_LOCK:
        idx = _load_index()
        idx[url] = snap.meta()
        _index_path().write_text(json.dumps(idx, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return snap


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="URL → snapshot text ở team/snapshots/")
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    for url in a.urls:
        try:
            s = fetch(url, refresh=a.refresh)
            print(f"✓ {s.kind:6s} {s.chars:6d} ký tự  {s.path}  ← {url}")
        except Exception as e:
            print(f"✗ {url}: {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
