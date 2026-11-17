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
CACHE_VER = "v2|"     # đổi khi đổi cách chụp — ảnh cache cũ (chữ chưa phóng) không bị dùng lại cho video mới
# 2026-11-16 (AUDIT #7): chữ thân trang báo VN 12–16px → 27–36px trên khung, khó đọc trên điện thoại. Thử viewport 320px:
# thoibaonganhang (min-width 360) bị cắt mép, bachhoaxanh ra trang trống → bỏ. Phóng CHỮ thân bài (như nút phóng chữ của
# trình duyệt — cùng nội dung, chỉ to hơn) tới ≥ READ_CSS_PX: 18px → 54px ảnh → 41px trên khung.
READ_CSS_PX = 18
# Bề rộng thẻ trong video (px khung 1080) — PHẢI khớp CARD_W ở remotion Evidence.tsx.
DISPLAY_W = 812   # khớp CARD_W ở remotion Evidence.tsx (Phase V, 2026-10-02)
MIN_READABLE_PX = 28  # research/probes/p3b-s4-research.md §7, viết trước khi chạy — từ 2026-11-16 là CỔNG (trước chỉ đo)


def display_font_px(body_font_css: float) -> float:
    """Cỡ chữ thân trên khung 1080×1920 sau khi thẻ thu ảnh 1080px về DISPLAY_W."""
    return body_font_css * DPR * DISPLAY_W / 1080
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
    # 2026-11-16 (AUDIT #7): quảng cáo lọt vào ảnh chụp (ảnh QC giữa bài lsvn.vn, dải voucher bachhoaxanh).
    " ins, iframe, [id*=google_ads i], [class*=adsbygoogle i], [class*=advert i], [id*=advert i],"
    " [class*=sponsor i], [class*=quangcao i], [class*=quang-cao i],"  # KHÔNG [class*=banner]: chinhphu.vn bọc nội dung trong .ContentBanner
    " [class*=voucher i], [class*=coupon i], [class~=ads i], [class*=ads-box i], [class*=box-ads i]"
    " { display:none !important }"
    f" p, li, blockquote, td, dd {{ font-size: max(1em, {READ_CSS_PX}px) !important; line-height: 1.5 !important }}"
    # trang có min-width > viewport (thoibaonganhang): ép đoạn văn xuống dòng trong khung, không tràn phải
    " p, li, blockquote, h1, h2, h3 { max-width: calc(100vw - 24px) !important; overflow-wrap: anywhere }"
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


def canon(url: str) -> str:
    """README GitHub dạng `raw.githubusercontent.com/<o>/<r>/…` hoặc `github.com/<o>/<r>/blob/…` → trang repo (có tên, sao,
    README đã render). 2026-10-18 (research/33): researcher hay đưa link raw → ngoài danh sách → mọi video repo mất hình repo."""
    u = urlparse(url.strip())
    host = (u.hostname or "").removeprefix("www.")
    parts = [x for x in u.path.split("/") if x]
    if host == "raw.githubusercontent.com" and len(parts) >= 2:
        return f"https://github.com/{parts[0]}/{parts[1]}"
    if host == "github.com" and len(parts) >= 4 and parts[2] in ("blob", "tree") and \
            (len(parts) == 4 or parts[-1].lower().startswith("readme")):
        return f"https://github.com/{parts[0]}/{parts[1]}"
    return url.strip()


def target_for(url: str) -> Target | None:
    """Trang này chụp vùng nào. None = ngoài danh sách cho phép → không chụp."""
    if canon(url) != url.strip():
        return target_for_known(canon(url))
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
    return hashlib.sha256((CACHE_VER + url).encode()).hexdigest()[:16]


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
        todo.append((len(out) - 1, canon(url), tgt))

    if not todo:
        return out
    # 2026-10-05: MỖI URL một process con, trần cứng PER_URL_SEC. Demo kênh mẹo treo 1 giờ 35 phút ở bước này —
    # `page.evaluate` của Playwright không có timeout, trang có script đơ luồng chính là treo vĩnh viễn.
    for i, url, tgt in todo:
        orig = out[i].url
        out[i] = _capture_isolated(url, tgt, cache_dir, highlight.get(orig, ""), timeout_ms)
        out[i].url = orig   # router khớp shot theo url kịch bản khai
    return out


PER_URL_SEC = 60


def _capture_isolated(url: str, tgt: Target, cache_dir: Path, hl: str, timeout_ms: int) -> Shot:
    import signal
    import subprocess
    import sys

    cmd = [sys.executable, "-m", "create_video.visual.screenshot", "--one", url, "--host", tgt.host,
           "--selector", tgt.selector, "--pad-top", str(tgt.pad_top), "--cache", str(cache_dir),
           "--timeout-ms", str(timeout_ms)] + (["--highlight", hl] if hl else [])
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    try:
        so, _ = p.communicate(timeout=PER_URL_SEC)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)   # cả Chromium con
        p.communicate()
        return Shot(url=url, sec=round(time.time() - t0, 1), error=f"Timeout: quá {PER_URL_SEC}s (trang treo)")
    try:
        return Shot(**json.loads(so.strip().splitlines()[-1]))
    except (json.JSONDecodeError, IndexError, TypeError):
        return Shot(url=url, sec=round(time.time() - t0, 1), error=f"process chụp hỏng (rc={p.returncode})")


def _capture_inproc(todo: list[tuple[int, str, Target]], out: list[Shot], cache_dir: Path,
                    highlight: dict[str, str], timeout_ms: int) -> list[Shot]:
    from playwright.sync_api import sync_playwright

    global _last_arxiv
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
                page.wait_for_timeout(1000)   # challenge Cloudflare chèn bằng JS sau domcontentloaded (đo canva.com)
                if wall := _bot_wall(page):
                    raise RuntimeError(f"trang chặn bot ({wall})")
                page.add_style_tag(content=_HIDE.get(tgt.host, _HIDE_GENERIC
                                                      if tgt.selector == GENERIC_SELECTOR else ""))
                if tgt.selector == GENERIC_SELECTOR:
                    try:   # bài báo tải nội dung trễ/khi cuộn tới (bachhoaxanh: khung xương) — cuộn một lượt, chờ mạng yên
                        page.evaluate("async () => { for (let y = 0; y < document.body.scrollHeight && y < 30000;"
                                      " y += innerHeight) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }"
                                      " scrollTo(0, 0); }")
                        page.wait_for_load_state("networkidle", timeout=4000)
                    except Exception:
                        pass
                    _hide_clutter(page)
                loc = page.locator(tgt.selector).first
                loc.wait_for(state="visible", timeout=timeout_ms)
                if url in highlight:
                    _mark(page, tgt.selector, highlight[url])
                page.wait_for_timeout(300)   # font/ảnh nhỏ trong vùng chụp
                box = loc.bounding_box()
                if not box or box["height"] < 40:
                    raise RuntimeError(f"vùng {tgt.selector!r} rỗng ({box})")
                mk = page.locator(f"{tgt.selector} mark")   # chữ tô NẰM TRONG vùng chụp (GitHub có bản sao ẩn)
                has_mk = url in highlight and mk.count() > 0 and mk.first.is_visible()
                if box["y"] - tgt.pad_top + 40 > VIEW_H or has_mk:
                    # 2026-10-18 (research/33): README GitHub ở y≈1236 > viewport 1200 (danh sách file đứng trên) →
                    # `clip` (tính theo VIEWPORT) rơi ra ngoài ảnh, hỏng 11/11 URL. Cuộn vùng chụp (hoặc chữ được tô) lên.
                    (mk if has_mk else loc).first.evaluate("e => e.scrollIntoView({block: 'start'})")
                    page.wait_for_timeout(200)
                    box = loc.bounding_box() or box
                    a = mk.first.bounding_box() if has_mk else None
                    if a and a["height"] > 0:
                        y0 = max(box["y"], a["y"] - CLIP_H * 0.25)
                        box = {**box, "y": y0, "height": box["y"] + box["height"] - y0}
                top = max(0.0, box["y"] - tgt.pad_top)
                h = min(CLIP_H, box["y"] + box["height"] - top, VIEW_H - top)
                if h < 40:   # vùng tính ra rỗng (chữ tô ở cuối trang…) → về đầu vùng chụp
                    loc.evaluate("e => e.scrollIntoView({block: 'start'})")
                    page.wait_for_timeout(200)
                    box = loc.bounding_box() or box
                    top = max(0.0, box["y"] - tgt.pad_top)
                    h = min(CLIP_H, box["y"] + box["height"] - top, VIEW_H - top)
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
                # scrollIntoView cuộn cả NGANG khi trang tràn bề rộng → `clip` x=0 cắt mất mép trái chữ
                # (thoibaonganhang, shot s12 video AI 1116 — AUDIT #7). Đưa về mép trái, giữ vị trí dọc.
                page.evaluate("() => window.scrollTo(0, window.scrollY)")
                page.screenshot(path=str(png), clip={"x": 0, "y": top, "width": VIEW_W, "height": h})
                from PIL import Image, ImageStat

                if max(ImageStat.Stat(Image.open(png).convert("L")).stddev) < 4:   # 2026-10-18: khung trơn một màu
                    png.unlink(missing_ok=True)
                    raise RuntimeError("ảnh chụp trống (một màu) — vùng chụp lệch khỏi nội dung")
                s.body_font_px = float(page.evaluate(
                    "sel => { const e = document.querySelector(sel); const p = e.querySelector('p') || e;"
                    " return parseFloat(getComputedStyle(p).fontSize) }", tgt.selector))
                shown = display_font_px(s.body_font_px)
                if 0 < shown < MIN_READABLE_PX:
                    png.unlink(missing_ok=True)
                    raise RuntimeError(f"chữ thân {s.body_font_px:.0f}px → {shown:.0f}px trên khung < {MIN_READABLE_PX}px "
                                       "— không đọc được trên điện thoại")
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


def _hide_clutter(page) -> None:
    """Trang báo chung: giấu phần tử dính (header/thanh chia sẻ/QC trôi) và ảnh/khung trỏ ra domain khác (QC dạng ảnh) —
    AUDIT #7 (2026-11-16). Không đụng ảnh của chính bài viết (cùng domain)."""
    page.evaluate(
        """() => {
          const host = location.hostname.replace(/^www\\./, '');
          for (const e of document.querySelectorAll('body *')) {
            const p = getComputedStyle(e).position;
            // chỉ THANH/POPUP dính (nhỏ) — vài trang bọc cả nội dung trong khung fixed (chinhphu.vn → timeout)
            if ((p === 'fixed' || p === 'sticky') && e.getBoundingClientRect().height < innerHeight * 0.4)
              e.style.setProperty('display', 'none', 'important');
          }
          for (const a of document.querySelectorAll('a[href]')) {
            let h = ''; try { h = new URL(a.href).hostname.replace(/^www\\./, ''); } catch (_) { continue; }
            if (h && !h.endsWith(host) && !host.endsWith(h) && a.querySelector('img, picture, video'))
              a.style.setProperty('display', 'none', 'important');
          }
        }"""
    )


def _bot_wall(page) -> str | None:
    """Trang chặn bot (Cloudflare challenge, captcha, 'Access denied') → lý do; trang thật → None.
    2026-10-23: canva.com trả trang "Verify you are human" — chụp/quay nguyên trang đó vào video AI (s2, s7).
    Dựa DOM + tiêu đề; chữ thân trang chỉ xét khi trang rất ngắn — bài báo VIẾT VỀ captcha không bị bắt nhầm."""
    return page.evaluate(
        """() => {
          if (document.querySelector('iframe[src*="challenges.cloudflare.com"], script[src*="challenges.cloudflare.com"],'
              + ' #challenge-form, #cf-challenge-running, .cf-turnstile, iframe[src*="recaptcha"], iframe[src*="hcaptcha"]'))
            return 'challenge trong DOM';
          const t = document.title.toLowerCase();
          if (/just a moment|attention required|access denied|verify you are human|are you a robot/.test(t))
            return 'tiêu đề: ' + document.title;
          const b = (document.body && document.body.innerText || '').toLowerCase();
          if (b.length < 1500 && /verify you are human|checking your browser|enable javascript and cookies|access denied/.test(b))
            return 'thân trang ngắn chứa câu chặn bot';
          return null;
        }"""
    )


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
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--one", help="(nội bộ) chụp đúng 1 URL trong process này, in JSON Shot")
    ap.add_argument("--host"); ap.add_argument("--selector"); ap.add_argument("--pad-top", type=int, default=0)
    ap.add_argument("--cache", type=Path, default=CACHE_DIR); ap.add_argument("--timeout-ms", type=int, default=12000)
    ap.add_argument("--highlight", default="")
    a = ap.parse_args(argv)
    if a.one:
        out = [Shot(url=a.one)]
        a.cache.mkdir(parents=True, exist_ok=True)
        _capture_inproc([(0, a.one, Target(a.host, a.selector, a.pad_top))], out, a.cache,
                        {a.one: a.highlight} if a.highlight else {}, a.timeout_ms)
        print(json.dumps(asdict(out[0]), ensure_ascii=False))
        return 0
    for s in capture(a.urls):
        flag = "✓" if s.ok else "✗"
        print(f"{flag} {s.sec:5.1f}s {'(cache) ' if s.cached else ''}{s.url}\n    {s.path or s.error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
