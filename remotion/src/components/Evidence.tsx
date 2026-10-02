import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fontStack } from "../fonts";
import type { ChartData, CodeData, Shot, StatData, VideoSpec } from "../types";

/**
 * Shot "bằng chứng" (P3b.S4): stat · chart · code · screenshot.
 *
 * Mọi thứ vẽ từ DỮ LIỆU trong spec — Python không gọi vào đây, đây không đọc gì
 * ngoài spec. Mọi animation chạy theo `useCurrentFrame()`; thư viện chart có
 * animation riêng theo thời gian thực sẽ nháy khi render headless (docs Remotion).
 *
 * Hình học đến từ QC tầng 1, không từ cảm giác:
 * - T1 coi cột phải 18% là vùng UI TikTok che SUỐT chiều cao → thẻ rộng tối đa
 *   CARD_W = 843px (x 43…886). `visual/screenshot.py: DISPLAY_W` phải khớp số này.
 * - Phụ đề bắt đầu ở 58% chiều cao → thẻ nằm trong y ≈ 10%…56%.
 * - T1 "viền đen" bắt dải tối PHẲNG ở mép; T1 "đứng hình" bắt > 2s không đổi.
 *   Nên nền có gradient + vệt sáng trôi liên tục — thẻ không bao giờ đứng yên hẳn.
 */

// Phase V (2026-10-02): 843/43 → 812/62. Push-in ×1,04 phình thẻ ra ~17px mỗi bên, nên mép trái
// lấn vào lề an toàn 4% (43,2px) — trang nền trắng (support.google.com) bị T1 bắt ngay. Push giờ ×1,02
// → mép 62−8 = 54px ≥ 43 · mép phải 874+8 = 882 ≤ 885 (82%). `visual/screenshot.py: DISPLAY_W` khớp.
export const CARD_W = 812;
const CARD_LEFT = 62;
const ZONE_TOP = 0.1; // × chiều cao khung
const ZONE_BOTTOM = 0.56;
// Shot 0 khi hook có chữ tiêu đề riêng (display_text): thẻ nằm DƯỚI chữ hook, không bị đè.
const HOOK_ZONE_TOP = 0.32;

const TOKEN_COLOR: Record<string, string> = {
  kw: "#C792EA",
  str: "#C3E88D",
  num: "#F78C6C",
  com: "#7F8794",
  fn: "#82AAFF",
  op: "#89DDFF",
  bi: "#FFCB6B",
  txt: "#E8E8EA",
};

const LABEL_FONT = fontStack("Be Vietnam Pro");
const MONO_FONT = '"Source Code Pro", "DejaVu Sans Mono", monospace';

/**
 * Tiến độ đếm "chốt" về 1 khi đã gần xong. `Easing.out(Easing.exp)` dừng ở
 * 1 − 2⁻¹⁰ ≈ 0,999 chứ không phải 1: bản đầu hiện "623" cho giá trị 624 — một con số
 * SAI trên màn hình, đúng loại lỗi T4 chặn (đo 2026-10-01). Số cuối phải đúng tuyệt đối.
 */
const settle = (p: number) => (p > 0.99 ? 1 : p);

const fmt = (v: number, decimals = 0) =>
  v.toLocaleString("vi-VN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });

/** Nền chung: gradient + lưới mờ + vệt sáng accent trôi chậm (chống đứng hình). */
const Backdrop: React.FC<{ spec: VideoSpec; durationInFrames: number }> = ({ spec, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { accent, bg } = spec.style.palette;
  const t = frame / Math.max(durationInFrames, 1);
  const gx = interpolate(t, [0, 1], [18, 82]);
  const gy = 30 + 10 * Math.sin(frame / 22);
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at ${gx}% ${gy}%, ${accent}38 0%, transparent 42%),
          linear-gradient(160deg, #1A1D24 0%, ${bg} 55%, #151820 100%)`,
      }}
    >
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
          backgroundSize: "54px 54px",
          backgroundPosition: `${frame * 0.8}px ${frame * 0.5}px`,
        }}
      />
    </AbsoluteFill>
  );
};

/** Khung vùng thẻ: vào bằng spring trượt lên, sau đó push-in rất chậm. */
const Zone: React.FC<{ durationInFrames: number; children: React.ReactNode; justify?: string; top?: number; instant?: boolean }> = ({
  durationInFrames,
  children,
  justify = "center",
  top = ZONE_TOP,
  instant = false,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const enter = instant ? 1 : spring({ frame, fps, config: { damping: 16, mass: 0.7 } });
  const push = interpolate(frame, [0, durationInFrames], [1, 1.02], { extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        left: CARD_LEFT,
        width: CARD_W,
        top: height * top,
        height: height * (ZONE_BOTTOM - top),
        display: "flex",
        flexDirection: "column",
        justifyContent: justify,
        opacity: enter,
        transform: `translateY(${(1 - enter) * 70}px) scale(${push})`,
        transformOrigin: "center center",
      }}
    >
      {children}
    </div>
  );
};

const Label: React.FC<{ text: string; size?: number; color?: string }> = ({ text, size = 46, color = "#E8E8EA" }) => (
  <div style={{ fontFamily: LABEL_FONT, fontWeight: 800, fontSize: size, lineHeight: 1.2, color }}>{text}</div>
);

// ── stat ───────────────────────────────────────────────────────────────────
// `instant`: shot 0 — frame 0 là thumbnail, phải hiện ĐÚNG số cuối ngay (2026-10-02: đếm lên làm frame 0
// hiện "185.020 từ" cho giá trị 500.000 — số SAI trên thumbnail).
const StatCard: React.FC<{ data: StatData; spec: VideoSpec; instant?: boolean }> = ({ data, spec, instant = false }) => {
  const f = useCurrentFrame();
  const frame = instant ? 60 : f;
  const { fps } = useVideoConfig();
  const { accent, fg } = spec.style.palette;
  const p = interpolate(frame, [4, 34], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.exp),
  });
  const pop = spring({ frame: frame - 30, fps, config: { damping: 9, stiffness: 160 } });
  const scale = 1 + 0.08 * Math.sin(Math.PI * Math.min(pop, 1));
  const shown = fmt(data.value * settle(p), data.decimals ?? 0);
  const final = `${data.prefix ?? ""}${fmt(data.value, data.decimals ?? 0)}${data.unit ?? ""}`;
  // Cỡ chữ theo chuỗi CUỐI (không theo số đang đếm) để chữ không co giãn khi đếm.
  // Anton condensed: ~0,46em mỗi ký tự.
  const size = Math.min(320, Math.floor((CARD_W * 0.92) / (0.46 * Math.max(final.length, 1))));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18, alignItems: "flex-start" }}>
      <Label text={data.label} size={50} />
      <div style={{ height: 8, width: 140, background: accent, borderRadius: 4 }} />
      <div
        style={{
          fontFamily: fontStack(spec.style.caption.font),
          fontSize: size,
          lineHeight: 1,
          color: accent,
          fontVariantNumeric: "tabular-nums",
          transform: `scale(${scale})`,
          transformOrigin: "left center",
          whiteSpace: "nowrap",
          textShadow: "0 8px 40px rgba(0,0,0,0.6)",
        }}
      >
        {data.prefix ?? ""}
        {shown}
        <span style={{ color: fg, fontSize: size * 0.42, marginLeft: 12 }}>{data.unit ?? ""}</span>
      </div>
    </div>
  );
};

// ── chart ──────────────────────────────────────────────────────────────────
const ChartCard: React.FC<{ data: ChartData; spec: VideoSpec; instant?: boolean }> = ({ data, spec, instant = false }) => {
  const f = useCurrentFrame();
  const frame = instant ? 90 : f;
  const { fps } = useVideoConfig();
  const { accent } = spec.style.palette;
  const max = Math.max(...data.bars.map((b) => b.value), 1e-9);
  const barMax = CARD_W - 190; // chừa chỗ số ở cuối cột
  const barH = data.bars.length > 4 ? 46 : 58;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
      {/* Không nối đơn vị khi tiêu đề đã có nó: demo-03 ra "Giá … (USD/triệu token) (USD)". */}
      <Label
        text={data.title + (data.unit && !data.title.includes(data.unit) ? ` (${data.unit})` : "")}
        size={48}
      />
      {data.bars.map((b, i) => {
        const g = spring({ frame: frame - 6 - i * 5, fps, config: { damping: 15, mass: 0.8 } });
        const w = Math.max(8, (b.value / max) * barMax * g);
        const col = b.highlight ? accent : "#3A3F4B";
        return (
          <div key={i} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <Label text={b.label} size={36} color={b.highlight ? "#FFFFFF" : "#B9BDC6"} />
            <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
              <div
                style={{
                  width: w,
                  height: barH,
                  borderRadius: 10,
                  background: b.highlight ? `linear-gradient(90deg, ${col}, ${col}CC)` : col,
                  boxShadow: b.highlight ? `0 0 34px ${accent}66` : "none",
                }}
              />
              <div
                style={{
                  fontFamily: fontStack(spec.style.caption.font),
                  fontSize: barH * 0.95,
                  color: b.highlight ? accent : "#D5D8DE",
                  fontVariantNumeric: "tabular-nums",
                  whiteSpace: "nowrap",
                }}
              >
                {fmt(b.value * settle(Math.min(g, 1)), Number.isInteger(b.value) ? 0 : 1)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ── code ───────────────────────────────────────────────────────────────────
const CodeCard: React.FC<{ data: CodeData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const rows = data.tokens ?? data.lines.map((l) => [{ t: "txt", v: l }]);
  const per = 5; // frame mỗi dòng hiện ra
  const shownRows = Math.min(rows.length, Math.floor(Math.max(frame - 6, 0) / per) + 1);
  const cursorOn = Math.floor(frame / 15) % 2 === 0; // nhấp nháy 0,5s — cũng là thứ chống "đứng hình"
  return (
    <div
      style={{
        background: "#14161B",
        border: "2px solid #2A2E37",
        borderRadius: 26,
        boxShadow: "0 30px 80px rgba(0,0,0,0.55)",
        overflow: "hidden",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "18px 26px", background: "#1B1E25" }}>
        {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => (
          <div key={c} style={{ width: 20, height: 20, borderRadius: 10, background: c }} />
        ))}
        <div style={{ marginLeft: 14, fontFamily: MONO_FONT, fontSize: 26, color: "#8B919C" }}>
          {data.title ?? data.lang}
        </div>
      </div>
      <div style={{ padding: "22px 30px 28px", fontFamily: MONO_FONT, fontSize: 32, lineHeight: 1.45 }}>
        {rows.slice(0, shownRows).map((row, i) => (
          <div key={i} style={{ whiteSpace: "pre", minHeight: "1.45em" }}>
            {row.map((tk, j) => (
              <span key={j} style={{ color: TOKEN_COLOR[tk.t] ?? TOKEN_COLOR.txt }}>
                {tk.v}
              </span>
            ))}
            {i === shownRows - 1 && cursorOn ? (
              <span style={{ background: "#E8E8EA", display: "inline-block", width: 16, height: 36, verticalAlign: "middle" }} />
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
};

// ── screenshot ─────────────────────────────────────────────────────────────
const ScreenshotCard: React.FC<{ src: string; sourceUrl?: string; durationInFrames: number; spec: VideoSpec; top?: number }> = ({
  src,
  sourceUrl,
  durationInFrames,
  spec,
  top = ZONE_TOP,
}) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const zoneH = height * (ZONE_BOTTOM - top) - 56; // chừa dòng nguồn
  // Ảnh rộng 1080 hiển thị ở CARD_W → cao 1440 thành ~1124px > vùng. Phần ĐẮT nhất
  // nằm ở đầu ảnh (tên model, license, title paper) — bản đầu trượt hết hành trình
  // nên tới 3/4 shot tiêu đề đã trôi khỏi khung. Giữ đầu ảnh 40% thời lượng, rồi
  // chỉ trượt nửa phần dư: đủ chuyển động (chống "đứng hình"), không mất tiêu đề.
  const imgH = (1440 * CARD_W) / 1080;
  const travel = Math.max(0, imgH - zoneH) * 0.5;
  const y = interpolate(frame, [Math.round(durationInFrames * 0.4), Math.max(durationInFrames - 6, 19)], [0, travel], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const host = sourceUrl ? sourceUrl.replace(/^https?:\/\/(www\.)?/, "") : "";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div
        style={{
          height: zoneH,
          borderRadius: 22,
          overflow: "hidden",
          border: `3px solid ${spec.style.palette.accent}88`,
          boxShadow: "0 30px 80px rgba(0,0,0,0.55)",
          background: "#0F1115",
        }}
      >
        <Img src={src} style={{ width: CARD_W - 6, display: "block", transform: `translateY(${-y}px)` }} />
      </div>
      {host ? (
        <div style={{ fontFamily: LABEL_FONT, fontWeight: 800, fontSize: 28, color: "#AEB3BD" }}>
          nguồn: {host.length > 46 ? host.slice(0, 45) + "…" : host}
        </div>
      ) : null}
    </div>
  );
};

export const EVIDENCE_KINDS = new Set(["stat", "chart", "code", "screenshot"]);

export const Evidence: React.FC<{
  shot: Shot;
  spec: VideoSpec;
  durationInFrames: number;
  src: string | null;
  belowHook?: boolean;
}> = ({ shot, spec, durationInFrames, src, belowHook = false }) => {
  const a = shot.asset;
  const top = belowHook ? HOOK_ZONE_TOP : ZONE_TOP;
  let body: React.ReactNode = null;
  if (a.kind === "stat" && a.stat) body = <StatCard data={a.stat} spec={spec} instant={belowHook} />;
  else if (a.kind === "chart" && a.chart) body = <ChartCard data={a.chart} spec={spec} instant={belowHook} />;
  else if (a.kind === "code" && a.code) body = <CodeCard data={a.code} />;
  else if (a.kind === "screenshot" && src)
    body = <ScreenshotCard src={src} sourceUrl={a.source_url} durationInFrames={durationInFrames} spec={spec} top={top} />;
  return (
    <AbsoluteFill>
      <Backdrop spec={spec} durationInFrames={durationInFrames} />
      <Zone durationInFrames={durationInFrames} justify={a.kind === "screenshot" ? "flex-start" : "center"} top={top} instant={belowHook}>
        {body}
      </Zone>
    </AbsoluteFill>
  );
};
