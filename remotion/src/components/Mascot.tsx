import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { VideoSpec } from "../types";

/**
 * Nhân vật hoạt hình của kênh (2026-10-05, research/19 — Tony: "thêm nhân vật animation").
 *
 * Vẽ hoàn toàn bằng SVG trong code: 0 GPU, giống hệt nhau mọi video, không chờ Kaggle. Miệng mở theo `mouth[]` (RMS giọng
 * đọc mỗi frame, Python tính sẵn trong spec — Remotion không đọc audio), chớp mắt và nhún đầu theo thời gian.
 * Chỉ hiện trong `windows` (câu hook + câu chốt), ở góc dưới-phải vùng hình: trên phụ đề (65%), trong lề phải 18%.
 */

type Mascot = NonNullable<VideoSpec["style"]["mascot"]>;

const BOX_W = 380;
const RIGHT_EDGE = 1080 * 0.82 - 12; // lề UI phải 18%
const BOTTOM_PCT = 0.635;            // đáy nhân vật ngay trên phụ đề

const Eyes: React.FC<{ blink: number; y: number; dx: number; color: string; r: number }> = ({ blink, y, dx, color, r }) => (
  <g>
    {[-dx, dx].map((x) => (
      <g key={x} transform={`translate(${100 + x} ${y}) scale(1 ${blink})`}>
        <ellipse rx={r} ry={r * 1.25} fill={color} />
        <circle cx={r * 0.35} cy={-r * 0.45} r={r * 0.38} fill="#FFFFFF" />
      </g>
    ))}
  </g>
);

/** Miệng: khép = đường cười; mở = hình bầu dục tối có lưỡi, cao theo `m`. */
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

const Kheo: React.FC<{ m: number; blink: number; accent: string }> = ({ m, blink, accent }) => (
  <svg viewBox="0 0 200 220" width="100%" height="100%">
    <ellipse cx={100} cy={212} rx={62} ry={7} fill="rgba(0,0,0,0.35)" />
    {/* mầm lá trên đầu */}
    <path d="M100 42 C 98 26, 104 16, 112 10" stroke="#5E9E4B" strokeWidth={5} fill="none" strokeLinecap="round" />
    <path d="M110 12 C 126 2, 142 10, 140 22 C 128 26, 116 22, 110 12 Z" fill="#7CC36A" />
    <path d="M104 22 C 90 10, 74 14, 74 26 C 86 32, 98 30, 104 22 Z" fill="#8FD47C" />
    {/* thân tròn */}
    <path d="M100 40 C 160 40, 182 92, 180 140 C 178 188, 146 208, 100 208 C 54 208, 22 188, 20 140 C 18 92, 40 40, 100 40 Z"
          fill="#FFF1D6" stroke="#E7C98F" strokeWidth={4} />
    {/* khăn quàng màu kênh */}
    <path d="M38 170 C 70 186, 130 186, 162 170 L 158 186 C 126 200, 74 200, 42 186 Z" fill={accent} />
    <circle cx={142} cy={186} r={9} fill={accent} stroke="#C98E1E" strokeWidth={3} />
    {/* má hồng */}
    <ellipse cx={58} cy={128} rx={14} ry={8} fill="#F6A6A0" opacity={0.75} />
    <ellipse cx={142} cy={128} rx={14} ry={8} fill="#F6A6A0" opacity={0.75} />
    <Eyes blink={blink} y={104} dx={30} color="#2B1E16" r={11} />
    <Mouth m={m} y={134} w={34} dark="#5A2A22" />
  </svg>
);

const Robot: React.FC<{ m: number; blink: number; accent: string }> = ({ m, blink, accent }) => (
  <svg viewBox="0 0 200 220" width="100%" height="100%">
    <ellipse cx={100} cy={212} rx={62} ry={7} fill="rgba(0,0,0,0.35)" />
    <line x1={100} y1={44} x2={100} y2={18} stroke="#9FB3D9" strokeWidth={5} strokeLinecap="round" />
    <circle cx={100} cy={14} r={9} fill={accent} />
    {/* đầu */}
    <rect x={24} y={44} width={152} height={124} rx={34} fill="#DCE6F7" stroke="#9FB3D9" strokeWidth={4} />
    <rect x={16} y={88} width={12} height={36} rx={5} fill="#9FB3D9" />
    <rect x={172} y={88} width={12} height={36} rx={5} fill="#9FB3D9" />
    {/* màn hình mặt */}
    <rect x={40} y={60} width={120} height={92} rx={22} fill="#0D1830" />
    <g opacity={0.95}>
      <Eyes blink={blink} y={96} dx={26} color={accent} r={10} />
    </g>
    {/* miệng dạng cột sóng âm */}
    {[-24, -12, 0, 12, 24].map((x, i) => {
      const k = [0.55, 0.85, 1, 0.85, 0.55][i];
      const h = 4 + m * 30 * k;
      return <rect key={x} x={100 + x - 4} y={130 - h / 2} width={8} height={h} rx={4} fill={accent} />;
    })}
    {/* thân */}
    <rect x={58} y={170} width={84} height={38} rx={16} fill="#DCE6F7" stroke="#9FB3D9" strokeWidth={4} />
    <circle cx={100} cy={189} r={8} fill={accent} />
  </svg>
);

export const MascotLayer: React.FC<{ spec: VideoSpec }> = ({ spec }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const m = spec.style.mascot as Mascot | undefined;
  if (!m) return null;
  const t = frame / fps;
  const win = m.windows.find((w) => t >= w.start_sec && t < w.end_sec);
  if (!win) return null;
  const local = frame - Math.round(win.start_sec * fps);
  const total = Math.max(1, Math.round((win.end_sec - win.start_sec) * fps));
  const enter = spring({ frame: local, fps, config: { damping: 12, mass: 0.6 } });
  const exit = interpolate(local, [total - 6, total], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const mouth = win.mouth[Math.min(Math.max(local, 0), win.mouth.length - 1)] ?? 0;
  // chớp mắt ~mỗi 2,8s, 4 frame
  const blink = local % Math.round(fps * 2.8) < 4 ? 0.12 : 1;
  const bob = Math.sin((local / fps) * Math.PI * 2 * 1.1) * 5 - mouth * 6;
  const tilt = Math.sin((local / fps) * Math.PI * 2 * 0.6) * 3;
  const accent = spec.style.palette.accent;
  const size = BOX_W * (0.7 + 0.3 * enter);
  return (
    <div style={{ position: "absolute", left: RIGHT_EDGE - size, top: height * BOTTOM_PCT - size * 1.1 + bob,
                  width: size, height: size * 1.1, opacity: Math.min(enter, exit),
                  transform: `rotate(${tilt}deg)`, transformOrigin: "50% 100%",
                  filter: "drop-shadow(0 18px 30px rgba(0,0,0,0.45))" }}>
      {m.kind === "robot" ? <Robot m={mouth} blink={blink} accent={accent} /> : <Kheo m={mouth} blink={blink} accent={accent} />}
    </div>
  );
};
