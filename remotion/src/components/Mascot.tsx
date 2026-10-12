import React, { useMemo } from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { VideoSpec } from "../types";

/**
 * Nhân vật hoạt hình của kênh (2026-10-05, research/19 — Tony: "thêm nhân vật animation" → "xuất hiện nhiều hơn" →
 * "có các hành động khác nhau, nhảy nhảy các chỗ trong khung hình").
 *
 * Vẽ hoàn toàn bằng SVG trong code: 0 GPU, giống hệt nhau mọi video, render tất định theo frame.
 * - Có mặt SUỐT video, cỡ theo `mode` của cửa sổ (Python chọn theo loại shot): big = người dẫn chuyện ở câu hook ·
 *   dock = cảnh quay/ảnh, luân phiên góc trái/phải (`side`) · peek = nhỏ, ló ở góc khi đang chiếu thẻ.
 * - Đổi chỗ bằng CÚ NHẢY vòng cung (không trượt), đổi cỡ bằng spring.
 * - `actions[]` (Python chọn theo nghĩa câu, đúng lúc câu được đọc): wave · jump · point · nod · shake · surprise ·
 *   think · celebrate. Mỗi hành động có lấy đà / co dãn / nảy (nguyên lý hoạt hình: anticipation, squash & stretch).
 * - Miệng theo `mouth[]` (RMS giọng mỗi frame, Python tính sẵn — Remotion không đọc audio); chớp mắt; nhún nhẹ.
 * Mép phải ≤ lề UI phải 18%; đáy trên phụ đề (65%).
 */

type Mascot = NonNullable<VideoSpec["style"]["mascot"]>;
type Mode = "big" | "dock" | "peek";
type Action = "wave" | "jump" | "point" | "nod" | "shake" | "surprise" | "think" | "celebrate";

const RIGHT_EDGE = 1080 * 0.82 - 10;
const LEFT_EDGE = 44;
const GEO: Record<Mode, { w: number; bottom: number }> = {
  big: { w: 560, bottom: 0.635 },
  dock: { w: 340, bottom: 0.635 },
  peek: { w: 190, bottom: 0.65 },
};
// thời lượng mỗi hành động (giây)
const DUR: Record<Action, number> = {
  wave: 1.4, jump: 0.8, point: 1.2, nod: 0.9, shake: 0.9, surprise: 1.0, think: 1.6, celebrate: 1.6,
};

const geo = (m: Mode, side: string | undefined) => {
  const g = GEO[m];
  const left = m === "big" ? 540 - g.w / 2 : side === "l" ? LEFT_EDGE : RIGHT_EDGE - g.w;
  return { w: g.w, left, bottom: g.bottom };
};

const ease = (x: number) => 1 - Math.pow(1 - Math.min(Math.max(x, 0), 1), 3);

/** Một cú nhảy trong [0,1]: lấy đà (co) → bay (dãn, cao `hgt`) → chạm đất (co) → hồi. */
const hop = (p: number, hgt: number) => {
  if (p < 0.15) { const q = p / 0.15; return { y: 0, sx: 1 + 0.12 * q, sy: 1 - 0.15 * q }; }
  if (p < 0.75) { const q = (p - 0.15) / 0.6; return { y: -Math.sin(Math.PI * q) * hgt, sx: 0.94, sy: 1.08 }; }
  const q = (p - 0.75) / 0.25;
  const sq = Math.sin(Math.PI * q);
  return { y: 0, sx: 1 + 0.1 * sq, sy: 1 - 0.12 * sq };
};

type Pose = {
  m: number; blink: number; accent: string; armL: number; armR: number; look: number; eye: number;
  mark: "!" | "?" | null; sparkle: number;
};

const Eyes: React.FC<{ blink: number; y: number; dx: number; color: string; r: number; look: number }> = (
  { blink, y, dx, color, r, look },
) => (
  <g>
    {[-dx, dx].map((x) => (
      <g key={x} transform={`translate(${100 + x + look} ${y}) scale(1 ${blink})`}>
        <ellipse rx={r} ry={r * 1.25} fill={color} />
        <circle cx={r * 0.35} cy={-r * 0.45} r={r * 0.38} fill="#FFFFFF" />
      </g>
    ))}
  </g>
);

const Mouth: React.FC<{ m: number; y: number; w: number; dark: string }> = ({ m, y, w, dark }) => {
  if (m < 0.06) {
    return <path d={`M ${100 - w / 2} ${y} Q 100 ${y + w * 0.32} ${100 + w / 2} ${y}`} stroke={dark} strokeWidth={5}
                 strokeLinecap="round" fill="none" />;
  }
  const h = 6 + m * w * 0.75;
  return (
    <g>
      <ellipse cx={100} cy={y + h / 2 - 2} rx={w / 2} ry={h / 2} fill={dark} />
      <ellipse cx={100} cy={y + h - 4} rx={w * 0.28} ry={Math.max(2, h * 0.22)} fill="#E8737A" />
    </g>
  );
};

const Arm: React.FC<{ sx: number; sy: number; deg: number; len: number; fill: string; stroke: string; flip?: boolean }> = (
  { sx, sy, deg, len, fill, stroke, flip },
) => (
  <g transform={`translate(${sx} ${sy}) rotate(${flip ? -deg : deg})`}>
    <rect x={-9} y={0} width={18} height={len} rx={9} fill={fill} stroke={stroke} strokeWidth={3} />
    <circle cx={0} cy={len} r={12} fill={fill} stroke={stroke} strokeWidth={3} />
  </g>
);

/** Dấu "!" / "?" trên đầu + lấp lánh khi ăn mừng. */
const Marks: React.FC<{ mark: Pose["mark"]; sparkle: number; accent: string }> = ({ mark, sparkle, accent }) => (
  <g>
    {mark ? (
      <g transform="translate(168 -6)">
        <circle r={22} fill="#FFFFFF" stroke={accent} strokeWidth={4} />
        <text textAnchor="middle" y={11} fontSize={32} fontWeight={900} fill="#1A1A1A"
              fontFamily='"Be Vietnam Pro", sans-serif'>{mark}</text>
      </g>
    ) : null}
    {sparkle > 0
      ? [[-6, 30], [206, 40], [20, -18], [186, -20]].map(([x, y], i) => (
          <path key={i} transform={`translate(${x} ${y}) scale(${sparkle * (0.7 + 0.3 * ((i % 2) + 0.5))})`}
                d="M0 -14 L4 -4 L14 0 L4 4 L0 14 L-4 4 L-14 0 L-4 -4 Z" fill={accent} />
        ))
      : null}
  </g>
);

const Kheo: React.FC<Pose> = (p) => (
  <svg viewBox="-20 -40 240 260" width="100%" height="100%" overflow="visible">
    <ellipse cx={100} cy={212} rx={62} ry={7} fill="rgba(0,0,0,0.35)" />
    <Arm sx={30} sy={140} deg={p.armL} len={44} fill="#FFF1D6" stroke="#E7C98F" />
    <Arm sx={170} sy={140} deg={p.armR} len={44} fill="#FFF1D6" stroke="#E7C98F" flip />
    <path d="M100 42 C 98 26, 104 16, 112 10" stroke="#5E9E4B" strokeWidth={5} fill="none" strokeLinecap="round" />
    <path d="M110 12 C 126 2, 142 10, 140 22 C 128 26, 116 22, 110 12 Z" fill="#7CC36A" />
    <path d="M104 22 C 90 10, 74 14, 74 26 C 86 32, 98 30, 104 22 Z" fill="#8FD47C" />
    <path d="M100 40 C 160 40, 182 92, 180 140 C 178 188, 146 208, 100 208 C 54 208, 22 188, 20 140 C 18 92, 40 40, 100 40 Z"
          fill="#FFF1D6" stroke="#E7C98F" strokeWidth={4} />
    <path d="M38 170 C 70 186, 130 186, 162 170 L 158 186 C 126 200, 74 200, 42 186 Z" fill={p.accent} />
    <circle cx={142} cy={186} r={9} fill={p.accent} stroke="#C98E1E" strokeWidth={3} />
    <ellipse cx={58} cy={128} rx={14} ry={8} fill="#F6A6A0" opacity={0.75} />
    <ellipse cx={142} cy={128} rx={14} ry={8} fill="#F6A6A0" opacity={0.75} />
    <Eyes blink={p.blink} y={104} dx={30} color="#2B1E16" r={11 * p.eye} look={p.look} />
    <Mouth m={p.m} y={134} w={34} dark="#5A2A22" />
    <Marks mark={p.mark} sparkle={p.sparkle} accent={p.accent} />
  </svg>
);

const Robot: React.FC<Pose> = (p) => (
  <svg viewBox="-20 -40 240 260" width="100%" height="100%" overflow="visible">
    <ellipse cx={100} cy={212} rx={62} ry={7} fill="rgba(0,0,0,0.35)" />
    <Arm sx={58} sy={178} deg={p.armL} len={30} fill="#DCE6F7" stroke="#9FB3D9" />
    <Arm sx={142} sy={178} deg={p.armR} len={30} fill="#DCE6F7" stroke="#9FB3D9" flip />
    <line x1={100} y1={44} x2={100} y2={18} stroke="#9FB3D9" strokeWidth={5} strokeLinecap="round" />
    <circle cx={100} cy={14} r={9} fill={p.accent} />
    <rect x={24} y={44} width={152} height={124} rx={34} fill="#DCE6F7" stroke="#9FB3D9" strokeWidth={4} />
    <rect x={16} y={88} width={12} height={36} rx={5} fill="#9FB3D9" />
    <rect x={172} y={88} width={12} height={36} rx={5} fill="#9FB3D9" />
    <rect x={40} y={60} width={120} height={92} rx={22} fill="#0D1830" />
    <g opacity={0.95}>
      <Eyes blink={p.blink} y={96} dx={26} color={p.accent} r={10 * p.eye} look={p.look} />
    </g>
    {[-24, -12, 0, 12, 24].map((x, i) => {
      const k = [0.55, 0.85, 1, 0.85, 0.55][i];
      const h = 4 + p.m * 30 * k;
      return <rect key={x} x={100 + x - 4} y={130 - h / 2} width={8} height={h} rx={4} fill={p.accent} />;
    })}
    <rect x={58} y={170} width={84} height={38} rx={16} fill="#DCE6F7" stroke="#9FB3D9" strokeWidth={4} />
    <circle cx={100} cy={189} r={8} fill={p.accent} />
    <Marks mark={p.mark} sparkle={p.sparkle} accent={p.accent} />
  </svg>
);

/** Nhịp đọc (Tony 2026-10-05: "nhảy theo từng nhịp đọc"): mốc đầu từ trong phụ đề, cách nhau ≥ 0,35s (nhảy mỗi từ thì
 * rung giật — giọng ~3–4 từ/giây); từ được nhấn (`emph`) nảy cao hơn. Đọc từ spec, không đọc audio. */
const BEAT_GAP = 0.35;
const BEAT_LEN = 0.28;
const beatsOf = (spec: VideoSpec) => {
  const out: { t: number; strong: boolean }[] = [];
  for (const c of spec.captions) {
    for (const w of c.words) {
      const strong = Boolean((w as { emph?: boolean }).emph);
      if (!out.length || w.start - out[out.length - 1].t >= BEAT_GAP) out.push({ t: w.start, strong });
      else if (strong) out[out.length - 1].strong = true;
    }
  }
  return out;
};

export const MascotLayer: React.FC<{ spec: VideoSpec }> = ({ spec }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const beats = useMemo(() => beatsOf(spec), [spec]);
  const m = spec.style.mascot as Mascot | undefined;
  if (!m || !m.windows.length) return null;
  const t = frame / fps;
  const idx = m.windows.findIndex((w) => t >= w.start_sec && t < w.end_sec);
  if (idx < 0) return null;
  const win = m.windows[idx];
  const mode = (win.mode ?? "dock") as Mode;
  const prevWin = idx > 0 && Math.abs(m.windows[idx - 1].end_sec - win.start_sec) < 0.1 ? m.windows[idx - 1] : null;
  const local = frame - Math.round(win.start_sec * fps);
  const last = idx === m.windows.length - 1;
  const total = Math.max(1, Math.round((win.end_sec - win.start_sec) * fps));

  // ── vị trí: nhảy vòng cung sang chỗ mới (khác chỗ) hoặc spring đổi cỡ (cùng chỗ) ──────────────────────────────
  const to = geo(mode, win.side);
  const from = prevWin ? geo((prevWin.mode ?? "dock") as Mode, prevWin.side)
    : win.start_sec < 0.05 ? to : { ...to, w: to.w * 0.4, left: to.left + to.w * 0.3 };
  const moving = prevWin !== null && Math.abs(from.left + from.w / 2 - (to.left + to.w / 2)) > 60;
  const travel = Math.round(fps * 0.55);
  const k = moving ? ease(local / travel) : spring({ frame: local, fps, config: { damping: 15, mass: 0.7 } });
  const w = interpolate(k, [0, 1], [from.w, to.w]);
  const left = interpolate(k, [0, 1], [from.left, to.left]);
  const bottom = interpolate(k, [0, 1], [from.bottom, to.bottom]);
  const hopMove = moving && local < travel ? hop(local / travel, 0.55 * to.w) : { y: 0, sx: 1, sy: 1 };
  // 2026-10-06 (research/21 §3): cửa sổ đầu video hiện ĐỦ từ frame 0 — frame 0 là bìa dự phòng, mờ = "chưa tải xong".
  const appear = prevWin || win.start_sec < 0.05 ? 1 : Math.min(1, k * 1.4);
  const exit = last ? interpolate(local, [total - 6, total], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1;

  // ── hành động theo câu ──────────────────────────────────────────────────────────────────────────────────────────
  const acts = (m.actions ?? []) as { start_sec: number; action: Action }[];
  let act: Action | null = null;
  let p = 0;
  for (let i = acts.length - 1; i >= 0; i--) {
    const a = acts[i];
    if (t >= a.start_sec) {
      const d = DUR[a.action] ?? 1;
      if (t - a.start_sec < d) { act = a.action; p = (t - a.start_sec) / d; }
      break;
    }
  }
  const mouth = win.mouth[Math.min(Math.max(local, 0), win.mouth.length - 1)] ?? 0;
  const sec = t;
  const swing = Math.sin(sec * Math.PI * 2 * 0.9);
  let armL = mode === "peek" ? 120 + swing * 8 : 22 + mouth * 30 + swing * 10;
  let armR = 22 + mouth * 24 - swing * 10;
  let look = mode === "peek" ? -5 : 0;
  let eye = 1;
  let rot = Math.sin(sec * Math.PI * 2 * 0.6) * 3;
  let y = Math.sin(sec * Math.PI * 2 * 1.1) * 5 - mouth * 6;
  let sx = 1;
  let sy = 1;
  let mark: Pose["mark"] = null;
  let sparkle = 0;
  const bell = Math.sin(Math.PI * Math.min(p, 1));          // 0→1→0 trong suốt hành động
  const ph = w;                                              // biên độ theo cỡ hiện tại
  if (act === "wave") {
    armR = 140 + Math.sin(sec * Math.PI * 2 * 2.4) * 28 * bell;
  } else if (act === "jump" && !(moving && local < travel)) {   // đang nhảy sang góc kia thì cú nhảy đó là đủ
    const h = hop(p, 0.35 * ph); y += h.y; sx = h.sx; sy = h.sy;
  } else if (act === "point") {
    const toCard = win.side === "l" ? 1 : -1;             // chỉ về phía giữa khung
    if (toCard < 0) armL = 110 + Math.sin(sec * Math.PI * 6) * 6 * bell; else armR = 110 + Math.sin(sec * Math.PI * 6) * 6 * bell;
    look = 6 * toCard * bell;
  } else if (act === "nod") {
    y += Math.abs(Math.sin(p * Math.PI * 3)) * 0.04 * ph * (1 - p);
  } else if (act === "shake") {
    rot += Math.sin(p * Math.PI * 6) * 9 * (1 - p);
    look = Math.sin(p * Math.PI * 6) * 6 * (1 - p);
  } else if (act === "surprise") {
    const pop = p < 0.25 ? p / 0.25 : 1 - (p - 0.25) / 0.75;
    sx = sy = 1 + 0.12 * pop; eye = 1 + 0.35 * bell; y -= 0.08 * ph * pop; mark = p < 0.9 ? "!" : null;
    armL = armR = 60 + 50 * bell;
  } else if (act === "think") {
    rot += 9 * bell; look = 4 * bell; mark = p > 0.1 && p < 0.92 ? "?" : null;
    armR = 150 * bell + 22 * (1 - bell);
  } else if (act === "celebrate") {
    const h = hop((p * 2) % 1, 0.3 * ph); y += h.y; sx = h.sx; sy = h.sy;
    armL = armR = 150 + Math.sin(sec * Math.PI * 8) * 15; sparkle = bell;
  }
  // Nảy theo nhịp đọc — chỉ khi không đang làm hành động lớn (nhảy/ăn mừng/đổi chỗ) để khỏi chồng chuyển động.
  const busy = act === "jump" || act === "celebrate" || act === "surprise" || (moving && local < travel);
  if (!busy) {
    let lo = 0, hi = beats.length - 1, bi = -1;
    while (lo <= hi) { const mid = (lo + hi) >> 1; if (beats[mid].t <= t) { bi = mid; lo = mid + 1; } else hi = mid - 1; }
    if (bi >= 0 && t - beats[bi].t < BEAT_LEN) {
      const q = (t - beats[bi].t) / BEAT_LEN;
      // peek (đang chiếu thẻ số liệu): nảy nửa biên độ — đừng giành mắt với con số mới hiện (research/19)
      const amp = (beats[bi].strong ? 0.075 : 0.035) * ph * (mode === "peek" ? 0.5 : 1);
      y -= Math.sin(Math.PI * q) * amp;
      const land = q > 0.8 ? Math.sin(Math.PI * (q - 0.8) / 0.2) : 0;
      sx *= 1 + 0.05 * land; sy *= 1 - 0.06 * land;
    }
  }
  // Lắc lư qua lại nhẹ khi đứng ở góc (không đứng im như dán).
  // chỉ lắc VỀ PHÍA GIỮA khung — lắc ra ngoài thì lấn lề UI phải 18% / mép trái
  const sway = (1 + Math.sin(sec * Math.PI * 2 * 0.35)) / 2 * 22;
  const drift = mode !== "dock" ? 0 : win.side === "l" ? sway : -sway;
  sx *= hopMove.sx; sy *= hopMove.sy; y += hopMove.y;

  const blink = frame % Math.round(fps * 2.8) < 4 ? 0.12 : 1;
  const accent = spec.style.palette.accent;
  const h = w * (260 / 240);
  const pose: Pose = { m: mouth, blink, accent, armL, armR, look, eye, mark, sparkle };
  return (
    <div style={{ position: "absolute", left: left + drift, top: height * bottom - h + y, width: w, height: h,
                  opacity: appear * exit, transform: `rotate(${rot}deg) scale(${sx}, ${sy})`, transformOrigin: "50% 100%",
                  filter: "drop-shadow(0 18px 30px rgba(0,0,0,0.45))" }}>
      {m.kind === "robot" ? <Robot {...pose} /> : <Kheo {...pose} />}
    </div>
  );
};
