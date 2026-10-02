"""Shot "bằng chứng": chụp ĐÚNG một vùng của trang thật (P3b.S4).

    python -m create_video.visual.screenshot https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct

Vì sao có file này: ảnh SDXL "khối phát sáng" không mang thông tin; tên model,
license, lượt tải, abstract thì có — và đó là thứ phân biệt video này với AI slop
(Relevance + Density, research/08 §2). 0 VRAM.

Ba quyết định, đều có lý do ở `research/probes/p3b-s4-research.md`:

1. **Chỉ ba nhà**: huggingface.co (card model), github.com (README), arxiv.org/abs
   (metadata CC0). Figure arXiv mặc định KHÔNG được dùng lại → không chụp PDF/HTML
   bài; logo là trademark → không cắt logo làm hình chính.
2. **Viewport 360 CSS px × device_scale_factor 3 = ảnh rộng 1080px**, dark mode cho
   hợp palette. Trong video, thẻ chỉ được rộng 843px (T1 coi cột phải 18% là vùng UI
   che, suốt chiều cao) → ảnh hiển thị ở 0,78×. Chữ hiển thị = cỡ CSS × 3 × 0,78 —
   abstract arXiv 12,96px CSS ra 30px, trên ngưỡng đọc được 28px. Lần đo đầu
   (540 × 2) chỉ ra 26px ảnh (probe p3b-s4, 2026-10-01). 360px là bề rộng điện
   thoại Android phổ biến nên trang không vỡ bố cục.
3. **Cache theo URL** (sha256) — chụp lại cùng trang là phí mạng và phí lịch sự với
   arXiv (robots.txt: không tải tự động hàng loạt). arXiv còn bị giãn ≥ 15s giữa hai
   lần chụp (crawl-delay của họ).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = REPO_ROOT / "exp" / "screenshot-cache"
# ~/.cache/ms-playwright trên tony là symlink gãy (2026-10-01) — giữ browser trong
# repo như exp/hf-cache, khỏi phụ thuộc thứ ngoài repo.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(REPO_ROOT / "exp" / "playwright"))

VIEW_W = 360          # CSS px; × DPR 3 = 1080px ảnh
DPR = 3
VIEW_H = 1200
CLIP_H = 480          # CSS px tối đa → 1440px ảnh; dài hơn thì Remotion trượt dọc
# Bề rộng thẻ trong video (px khung 1080) — PHẢI khớp CARD_W ở remotion Evidence.tsx.
DISPLAY_W = 812   # khớp CARD_W ở remotion Evidence.tsx (Phase V, 2026-10-02)
MIN_READABLE_PX = 28  # research/probes/p3b-s4-research.md §7, viết trước khi chạy
ARXIV_GAP_SEC = 15.0  # arxiv.org/robots.txt Crawl-delay

# CSS tiêm vào lúc chụp: giấu thứ không phải nội dung. Selector đo trên DOM thật
# 2026-10-01; trang đổi giao diện thì `probe` (ở cuối file) sẽ báo.
_HIDE = {
    # CHỈ thanh điều hướng site (header đầu tiên, nằm ngoài <main>). Lần đầu viết
    # `header {…}` — giấu luôn khối tên model vì nó cũng là <header> (probe 2026-10-01).
    "huggingface.co": "body > div > header:first-child { display:none !important }",
    "github.com": "header.AppHeader, .js-header-wrapper, #ghcc, .flash { display:none !important }",
    "arxiv.org": "header, .search-block, .extra-services, .bib-sidebar { display:none !important }",
}


# Trang chung: giấu banner cookie / thanh điều hướng dính / popup — không phải nội dung.
_HIDE_GENERIC = (
    "[id*=cookie i], [class*=cookie i], [id*=consent i], [class*=consent i], [class*=banner i][class*=top i],"
    " [role=dialog], [aria-modal=true], nav { display:none !important }"
)


@dataclass(frozen=True)
class Target:
    host: str
    selector: str
    # Bao nhiêu CSS px TRƯỚC phần tử cũng lấy vào (vd. HF: lấy cả tên model phía trên card).
    pad_top: int = 0


# Phase V4 (2026-10-02): trang mà researcher đã tải + kiểm (brief.visuals / facts) cũng được chụp —
# kênh mở rộng ra ngoài mạch dev (trang giá, help center, bài công bố). Pipeline đăng ký trước khi
# kiểm kịch bản; url lạ không qua brief vẫn bị từ chối.
EXTRA_ALLOWED: set[str] = set()
GENERIC_SELECTOR = "main, article, [role=main], body"


def allow(urls) -> None:
    EXTRA_ALLOWED.update(u.strip() for u in urls if u and u.strip())


def target_for(url: str) -> Target | None:
    """Trang này chụp vùng nào. None = ngoài danh sách cho phép → không chụp."""
    if url.strip() in EXTRA_ALLOWED and target_for_known(url) is None:
        u = urlparse(url)
        return Target((u.hostname or "").removeprefix("www."), GENERIC_SELECTOR)
    return target_for_known(url)


def target_for_known(url: str) -> Target | None:
    u = urlparse(url)
    host = (u.hostname or "").removeprefix("www.")
    path = u.path.strip("/")
    if host == "huggingface.co" and path.count("/") == 1 and not path.startswith(("papers", "spaces", "datasets", "docs", "blog")):
        # Đầu trang model: tên + tag + license + lượt tải. Card markdown ở dưới
        # thường dài 6000px — chụp nó thì chỉ ra mấy dòng giới thiệu chung chung.
        return Target(host, "main", pad_top=0)
    if host == "github.com" and path.count("/") == 1:
        return Target(host, "article.markdown-body")
    if host == "arxiv.org" and re.fullmatch(r"abs/\d{4}\.\d{4,5}(v\d+)?", path):
        return Target(host, "#abs")
    return None


@dataclass
class Shot:
    url: str
    path: str = ""
    ok: bool = False
    sec: float = 0.0
    cached: bool = False
    width: int = 0
    height: int = 0
    body_font_px: float = 0.0     # cỡ chữ thân ĐO trên trang (CSS px), × DPR = px ảnh
    error: str = ""


def _key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


_last_arxiv = 0.0


def capture(urls: list[str], cache_dir: Path = CACHE_DIR, highlight: dict[str, str] | None = None,
            timeout_ms: int = 12000) -> list[Shot]:
    """Chụp từng URL → PNG rộng 1080px. Không ném lỗi: shot hỏng có `ok=False` +
    `error`, để router lùi về b-roll thay vì làm chết cả video."""
    from playwright.sync_api import sync_playwright

    global _last_arxiv
    cache_dir.mkdir(parents=True, exist_ok=True)
    highlight = highlight or {}
    out: list[Shot] = []
    todo: list[tuple[int, str, Target]] = []
    for url in urls:
        s = Shot(url=url)
        out.append(s)
        tgt = target_for(url)
        if tgt is None:
            s.error = "ngoài danh sách cho phép (huggingface.co model · github.com repo · arxiv.org/abs)"
            continue
        png = cache_dir / f"{_key(url + highlight.get(url, ''))}.png"
        meta = png.with_suffix(".json")
        if png.exists() and meta.exists():
            s.__dict__.update(json.loads(meta.read_text()), cached=True, sec=0.0)
            continue
        todo.append((len(out) - 1, url, tgt))

    if not todo:
        return out

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": VIEW_W, "height": VIEW_H}, device_scale_factor=DPR,
            color_scheme="dark", locale="en-US",
        )
        for i, url, tgt in todo:
            s = out[i]
            if tgt.host == "arxiv.org":
                wait = ARXIV_GAP_SEC - (time.time() - _last_arxiv)
                if wait > 0:
                    time.sleep(wait)
                _last_arxiv = time.time()
            t0 = time.time()
            page = ctx.new_page()
            try:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                except Exception:
                    # Một lần thử lại: lần đo đầu github.com timeout 20s rồi
                    # ngay sau đó tải 1,4s — mạng chập chờn, không phải trang hỏng.
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.add_style_tag(content=_HIDE.get(tgt.host, _HIDE_GENERIC
                                                      if tgt.selector == GENERIC_SELECTOR else ""))
                loc = page.locator(tgt.selector).first
                loc.wait_for(state="visible", timeout=timeout_ms)
                if url in highlight:
                    _mark(page, tgt.selector, highlight[url])
                page.wait_for_timeout(300)   # font/ảnh nhỏ trong vùng chụp
                box = loc.bounding_box()
                if not box or box["height"] < 40:
                    raise RuntimeError(f"vùng {tgt.selector!r} rỗng ({box})")
                top = max(0.0, box["y"] - tgt.pad_top)
                h = min(CLIP_H, box["y"] + box["height"] - top)
                if tgt.selector == GENERIC_SELECTOR:
                    # Trang chung dài: lấy vùng QUANH chữ được tô (đúng thứ lời đọc nói tới), không thì
                    # quanh h1 đầu tiên. `clip` tính theo VIEWPORT → cuộn mốc vào giữa màn hình trước.
                    sel = "mark" if url in highlight and page.locator("mark").count() else "h1"
                    top, h = 0.0, CLIP_H
                    if page.locator(sel).count():
                        page.locator(sel).first.evaluate("e => e.scrollIntoView({block: 'center'})")
                        page.wait_for_timeout(200)
                        anchor = page.locator(sel).first.bounding_box()
                        if anchor:
                            top = max(0.0, min(anchor["y"] - CLIP_H * 0.35, VIEW_H - CLIP_H))
                png = Path(cache_dir) / f"{_key(url + highlight.get(url, ''))}.png"
                page.screenshot(path=str(png), clip={"x": 0, "y": top, "width": VIEW_W, "height": h})
                s.body_font_px = float(page.evaluate(
                    "sel => { const e = document.querySelector(sel); const p = e.querySelector('p') || e;"
                    " return parseFloat(getComputedStyle(p).fontSize) }", tgt.selector))
                s.path, s.ok = str(png), True
                s.width, s.height = round(VIEW_W * DPR), round(h * DPR)
            except Exception as e:  # mạng, selector đổi, timeout — đều lùi về b-roll
                s.error = f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
            finally:
                page.close()
                s.sec = round(time.time() - t0, 2)
            if s.ok:
                d = {k: v for k, v in asdict(s).items() if k not in ("cached", "sec")}
                Path(s.path).with_suffix(".json").write_text(json.dumps(d, ensure_ascii=False))
        browser.close()
    return out


def _mark(page, selector: str, text: str) -> None:
    """Tô vàng lần xuất hiện ĐẦU của `text` trong vùng chụp — mắt người xem đi
    thẳng vào đúng con số/câu mà lời đọc đang nói."""
    page.evaluate(
        """([sel, needle]) => {
          const root = document.querySelector(sel); if (!root) return;
          const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
          let n; while ((n = w.nextNode())) {
            const i = n.data.toLowerCase().indexOf(needle.toLowerCase());
            if (i < 0) continue;
            const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + needle.length);
            const m = document.createElement('mark');
            m.style.cssText = 'background:#FFE14D;color:#0D0D0F;padding:0 2px;border-radius:3px';
            r.surroundContents(m); return;
          }
        }""",
        [selector, text],
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="URL → PNG bằng chứng 1080px")
    ap.add_argument("urls", nargs="+")
    a = ap.parse_args(argv)
    for s in capture(a.urls):
        flag = "✓" if s.ok else "✗"
        print(f"{flag} {s.sec:5.1f}s {'(cache) ' if s.cached else ''}{s.url}\n    {s.path or s.error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
