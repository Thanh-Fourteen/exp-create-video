// Biểu đồ trang Thống kê (2026-10-08, research/24). SVG thuần, không thư viện.
// Luật (skill dataviz + research/24): trục log cho view · 1 màu nhấn (accent kênh) + xám cho ngữ cảnh · nét 2px, chấm ≥ 8px
// có viền nền 2px · lưới 1px liền · chữ dùng màu chữ, không dùng màu dữ liệu · tooltip chỉ bổ sung (bảng có đủ số).
(() => {
  if (window.__charts) { window.__charts(); return; }   // htmx điều hướng nạp lại script → chỉ vẽ lại
  const NS = 'http://www.w3.org/2000/svg';
  const css = (n, f) => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || f;
  const C = () => ({
    accent: css('--color-primary', '#7FA6FF'), ink: css('--color-base-content', '#ddd'),
    grid: css('--color-base-300', '#333'), surf: css('--color-base-200', '#111'),
  });
  const el = (tag, attrs = {}, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (parent) parent.appendChild(e);
    return e;
  };
  const fmt = (n) => n == null ? '–' : n >= 10000 ? (n / 1000).toFixed(1).replace('.0', '').replace('.', ',') + 'k'
    : Math.round(n).toLocaleString('vi-VN');
  const date = (t) => new Date(t * 1000).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
  const lg = (v) => Math.log10(Math.max(v, 0) + 1);
  const LOG_TICKS = [0, 1, 10, 100, 1000, 10000, 100000];

  // một tooltip dùng chung — nội dung bằng textContent (tiêu đề video là dữ liệu ngoài)
  let tip;
  const tooltip = (x, y, lines) => {
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'fixed z-50 pointer-events-none rounded-field border border-base-300 bg-base-100 px-3 py-2 text-[12.5px] shadow-lg max-w-[280px]';
      document.body.appendChild(tip);
    }
    tip.replaceChildren(...lines.map(([t, strong], i) => {
      const d = document.createElement('div');
      d.textContent = t;
      if (strong) d.className = 'font-semibold text-[14px]';
      else if (i) d.className = 'text-muted';
      return d;
    }));
    tip.style.display = 'block';
    const r = tip.getBoundingClientRect();
    tip.style.left = Math.min(x + 14, innerWidth - r.width - 8) + 'px';
    tip.style.top = Math.max(8, y - r.height - 10) + 'px';
  };
  const hide = () => { if (tip) tip.style.display = 'none'; };

  const frame = (host, h) => {
    const w = Math.max(280, host.clientWidth);
    const svg = el('svg', { viewBox: `0 0 ${w} ${h}`, width: '100%', height: h, role: 'img' });
    host.replaceChildren(svg);
    return { svg, w, h };
  };
  // miền log: [0 hoặc 10^a, 10^b] bao trọn dữ liệu — vạch trên cùng luôn là luỹ thừa 10 kế tiếp
  const logDom = (vals) => {
    const vs = vals.filter(v => v != null), mn = Math.min(...vs), mx = Math.max(10, ...vs);
    const hi = Math.pow(10, Math.ceil(Math.log10(mx + 1)));
    const lo = mn < 1 ? 0 : Math.pow(10, Math.floor(Math.log10(mn)));
    return { lo, hi, a: lg(lo), b: lg(hi), ticks: LOG_TICKS.filter(t => t >= lo && t <= hi) };
  };
  const unit = (dom, v) => (lg(v) - dom.a) / (dom.b - dom.a);
  const yLogAxis = (svg, x0, x1, y, dom, c) => {
    for (const t of dom.ticks) {
      const yy = y(t);
      el('line', { x1: x0, x2: x1, y1: yy, y2: yy, stroke: c.grid, 'stroke-width': 1 }, svg);
      el('text', { x: x0 - 6, y: yy + 4, 'text-anchor': 'end', 'font-size': 11, fill: c.ink, opacity: .6 }, svg).textContent = fmt(t);
    }
  };
  const dot = (svg, x, y, color, c, r = 4.5) =>
    el('circle', { cx: x, cy: y, r, fill: color, stroke: c.surf, 'stroke-width': 2 }, svg);
  const hit = (svg, x, y, lines, href) => {
    const a = el('circle', { cx: x, cy: y, r: 12, fill: 'transparent', tabindex: 0, style: 'cursor:pointer;outline:none' }, svg);
    const show = (e) => { const b = a.getBoundingClientRect(); tooltip(e.clientX ?? b.x + 12, e.clientY ?? b.y, lines); };
    a.addEventListener('pointermove', show); a.addEventListener('focus', show);
    a.addEventListener('pointerleave', hide); a.addEventListener('blur', hide);
    if (href) a.addEventListener('click', () => { location.href = href; });
  };

  // 1) View từng video theo ngày đăng — dot plot, trục log, vạch trung vị, video "vượt typical" nhấn màu
  function dotTime(host, d) {
    const c = C(), { svg, w, h } = frame(host, 240), L = 44, R = 12, T = 12, B = 26;
    const pts = d.points.filter(p => p.v != null);
    if (!pts.length) return;
    const tmin = Math.min(...pts.map(p => p.t)), pad = Math.max(6 * 3600, (d.now - tmin) * .04);
    const t0 = tmin - pad, t1 = d.now;          // trục theo dữ liệu, không theo cả kỳ (video dồn về một góc)
    const dom = logDom(pts.map(p => p.v));
    const x = (t) => L + (t - t0) / Math.max(1, t1 - t0) * (w - L - R);
    const y = (v) => T + (1 - unit(dom, v)) * (h - T - B);
    yLogAxis(svg, L, w - R, y, dom, c);
    for (const t of [t0, (t0 + t1) / 2, t1])
      el('text', { x: x(t), y: h - 6, 'text-anchor': t === t0 ? 'start' : t === t1 ? 'end' : 'middle', 'font-size': 11, fill: c.ink, opacity: .6 }, svg).textContent = date(t);
    if (d.median != null) {
      el('line', { x1: L, x2: w - R, y1: y(d.median), y2: y(d.median), stroke: c.ink, 'stroke-width': 1, opacity: .45 }, svg);
      el('text', { x: L + 4, y: y(d.median) - 5, 'font-size': 11, fill: c.ink, opacity: .7 }, svg).textContent = `trung vị ${fmt(d.median)}`;
    }
    for (const p of pts) {
      dot(svg, x(p.t), y(p.v), p.hot ? c.accent : c.ink, c, p.hot ? 5 : 4).setAttribute('opacity', p.hot ? 1 : .55);
      hit(svg, x(p.t), y(p.v), [[fmt(p.v) + ' view', true], [p.title], [date(p.t)]], p.href);
    }
  }

  // 2) Đường tăng view theo giờ kể từ lúc đăng — 10 video gần nhất; mới nhất nhấn màu, còn lại xám (emphasis)
  function curves(host, d) {
    const c = C(), { svg, w, h } = frame(host, 240), L = 44, R = 64, T = 12, B = 26;
    const ss = d.series.filter(s => s.pts.length);
    if (!ss.length) return;
    const maxH = Math.max(6, ...ss.flatMap(s => s.pts.map(p => p[0])));
    const dom = logDom([0, ...ss.flatMap(s => s.pts.map(p => p[1]))]);
    const x = (hh) => L + hh / maxH * (w - L - R);
    const y = (v) => T + (1 - unit(dom, v)) * (h - T - B);
    yLogAxis(svg, L, w - R, y, dom, c);
    const step = maxH > 240 ? 72 : maxH > 72 ? 24 : maxH > 24 ? 12 : 6;
    for (let hh = 0; hh <= maxH; hh += step)
      el('text', { x: x(hh), y: h - 6, 'text-anchor': 'middle', 'font-size': 11, fill: c.ink, opacity: .6 }, svg).textContent = hh + 'h';
    ss.forEach((s, i) => {
      const last = i === ss.length - 1;
      // chỉ nối từ gốc (0 giờ, 0 view) khi mốc đo đầu ≤ 3 giờ — không vẽ đoạn đoán qua quãng chưa theo dõi
      const pts = s.pts[0][0] <= 3 ? [[0, 0], ...s.pts] : s.pts;
      if (pts.length === 1) dot(svg, x(pts[0][0]), y(pts[0][1]), last ? c.accent : c.ink, c, 3).setAttribute('opacity', last ? 1 : .35);
      el('polyline', { points: pts.map(p => `${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join(' '), fill: 'none',
        stroke: last ? c.accent : c.ink, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', opacity: last ? 1 : .22 }, svg);
      const e = s.pts[s.pts.length - 1];
      if (last) {
        dot(svg, x(e[0]), y(e[1]), c.accent, c);
        el('text', { x: x(e[0]) + 8, y: y(e[1]) + 4, 'font-size': 12, fill: c.ink }, svg).textContent = fmt(e[1]);
      }
      for (const p of s.pts) hit(svg, x(p[0]), y(p[1]), [[fmt(p[1]) + ' view', true], [s.title], [`${p[0].toFixed(0)} giờ sau khi đăng`]]);
    });
  }

  // 3) So nhóm — mỗi nhóm một hàng: chấm từng video (trục log), vạch trung vị, n; n < 5 mờ
  function groups(host, d) {
    const c = C(), rows = d.rows;
    if (!rows.length) return;
    const rowH = 34, L = Math.min(170, host.clientWidth * .38), R = 54, T = 6, B = 22;
    const { svg, w, h } = frame(host, T + rows.length * rowH + B);
    const dom = logDom(rows.flatMap(r => r.points.map(p => p.v)));
    const x = (v) => L + unit(dom, v) * (w - L - R);
    for (const t of dom.ticks) {
      el('line', { x1: x(t), x2: x(t), y1: T, y2: h - B, stroke: c.grid, 'stroke-width': 1 }, svg);
      el('text', { x: x(t), y: h - 6, 'text-anchor': 'middle', 'font-size': 11, fill: c.ink, opacity: .6 }, svg).textContent = fmt(t);
    }
    rows.forEach((r, i) => {
      const cy = T + i * rowH + rowH / 2, g = el('g', { opacity: r.weak ? .45 : 1 }, svg);
      const lab = el('text', { x: 0, y: cy + 4, 'font-size': 13, fill: c.ink }, g);
      lab.textContent = r.name.length > 22 ? r.name.slice(0, 21) + '…' : r.name;
      el('text', { x: w, y: cy + 4, 'text-anchor': 'end', 'font-size': 11.5, fill: c.ink, opacity: .65 }, g).textContent = `n=${r.n}`;
      if (r.median != null) el('line', { x1: x(r.median), x2: x(r.median), y1: cy - 10, y2: cy + 10, stroke: c.accent, 'stroke-width': 3, 'stroke-linecap': 'round' }, g);
      for (const p of r.points) {
        if (p.v == null) continue;
        dot(g, x(p.v), cy, c.ink, c, 4).setAttribute('opacity', .5);
        hit(svg, x(p.v), cy, [[fmt(p.v) + ' view', true], [p.t], [r.name + (r.weak ? ' · chưa đủ dữ liệu' : '')]]);
      }
    });
  }

  // 4) Sparkline follower
  function spark(host, d) {
    const c = C(), pts = d.points;
    if (pts.length < 2) return;
    const { svg, w, h } = frame(host, 36);
    const t0 = pts[0][0], t1 = pts[pts.length - 1][0], lo = Math.min(...pts.map(p => p[1])), hi = Math.max(...pts.map(p => p[1]));
    const x = (t) => 2 + (t - t0) / Math.max(1, t1 - t0) * (w - 8), y = (v) => 4 + (1 - (v - lo) / Math.max(1, hi - lo)) * (h - 8);
    el('polyline', { points: pts.map(p => `${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join(' '), fill: 'none', stroke: c.ink, opacity: .45, 'stroke-width': 2 }, svg);
    const e = pts[pts.length - 1];
    dot(svg, x(e[0]), y(e[1]), c.accent, c, 3.5);
  }

  const KINDS = { dotTime, curves, groups, spark };
  const render = () => document.querySelectorAll('[data-chart]').forEach(host => {
    try { KINDS[host.dataset.chart](host, JSON.parse(host.querySelector('script[type="application/json"]')?.textContent || host.dataset.json || '{}')); }
    catch (e) { console.error(e); }
  });
  // giữ dữ liệu trong <script type=application/json> con — render thay nội dung nên cache trước
  const prep = () => document.querySelectorAll('[data-chart]').forEach(h => {
    const s = h.querySelector('script[type="application/json"]');
    if (s) h.dataset.json = s.textContent;
  });
  const go = () => { prep(); render(); };
  window.__charts = go;
  window.addEventListener('resize', () => { clearTimeout(window.__chartT); window.__chartT = setTimeout(render, 150); });
  document.addEventListener('DOMContentLoaded', go);
  document.body?.addEventListener?.('htmx:afterSettle', go);
  new MutationObserver(() => { if (document.documentElement.dataset.theme !== window.__chartTheme) { window.__chartTheme = document.documentElement.dataset.theme; render(); } })
    .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  if (document.readyState !== 'loading') go();
})();
