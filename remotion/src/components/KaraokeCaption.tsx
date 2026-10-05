import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontStack } from "../fonts";
import type { Caption, TextStyle, VideoSpec } from "../types";

/**
 * Phụ đề tô sáng từng từ theo timestamp thật của audio.
 *
 * Đây là một trong ba thứ tạo sức hút của video ở đây (cùng hook và nhịp dựng),
 * và là lý do `words[]` trong spec là **bắt buộc**: timestamp chia đều đo được
 * lệch tới 458ms (P1.S2), quá xa ngưỡng 120ms mà người xem bắt đầu cảm nhận được.
 *
 * ⚠️ Vùng an toàn TikTok. UI của app che mép dưới (~20%) và mép phải (~18% —
 * cột like/comment/share). Chữ tràn vào đó thì **trên máy nhìn ổn, trên app bị
 * che** — không có cách nào phát hiện bằng mắt lúc render. Vì vậy hộp chữ ở đây
 * bị chặn cứng trong vùng an toàn thay vì căn giữa màn hình.
 */

const posToBox = (
  position: TextStyle["position"],
  safe: VideoSpec["style"]["safe_area_pct"],
): React.CSSProperties => {
  const common = {
    position: "absolute" as const,
    left: `${safe.left}%`,
    right: `${safe.right}%`,
  };
  switch (position) {
    case "top":
      return { ...common, top: `${safe.top + 4}%` };
    case "center":
      return { ...common, top: "42%" };
    case "bottom":
      return { ...common, bottom: `${safe.bottom + 2}%` };
    case "lower":
      // Bố cục headline v2 (ảnh tràn màn hình, research/18): vật chính của ảnh nằm quanh tâm → phụ đề xuống 65%,
      // trên dải tối mờ, vẫn trên vùng UI đáy (TikTok che ~25% dưới) và trên overlay "bottom".
      return { ...common, top: "65%" };
    case "center-lower":
    default:
      // Dưới tâm màn hình nhưng vẫn TRÊN vùng UI: mắt người xem TikTok
      // nghỉ ở khoảng này, còn mép dưới thì bị caption + thanh nhạc che.
      return { ...common, top: "58%" };
  }
};

export const KaraokeCaption: React.FC<{
  caption: Caption;
  style: TextStyle;
  safe: VideoSpec["style"]["safe_area_pct"];
  accent: string;
}> = ({ caption, style, safe, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const stroke = style.stroke_px ?? 6;
  const highlight = style.highlight_color ?? accent;

  return (
    <AbsoluteFill>
      <div
        style={{
          ...posToBox(style.position, safe),
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "0 0.28em",
          fontFamily: fontStack(style.font),
          fontWeight: style.weight ?? 800,
          fontSize: style.size_px,
          lineHeight: 1.22,
          textAlign: "center",
          // Viền đen quanh chữ: nền là ảnh sinh ra, sáng tối không đoán trước
          // được. Không có viền thì chữ trắng biến mất trên ảnh sáng.
          WebkitTextStroke: `${stroke}px #000`,
          paintOrder: "stroke fill",
          textShadow: "0 4px 18px rgba(0,0,0,0.55)",
        }}
      >
        {caption.words.map((w, i) => {
          const active = t >= w.start && t < w.end;
          const spoken = t >= w.end;
          // "Pop" của từ vừa vào: nảy trong ~4 frame rồi về 1. Đây là chuyển
          // động duy nhất chạy liên tục suốt video, nên nó gánh phần lớn cảm
          // giác "nhanh" — mạnh tay hơn ở đây rẻ hơn nhiều so với cắt shot dày
          // hơn (mỗi shot là một ảnh phải sinh, ~8 giây GPU).
          const age = t - w.start;
          const pop = active ? Math.max(0, 1 - age / 0.13) : 0;
          return (
            <span
              key={`${w.w}-${i}`}
              style={{
                color: active ? highlight : style.color,
                transform: `scale(${active ? 1.1 + pop * 0.1 : 1}) translateY(${-pop * 6}px)`,
                display: "inline-block",
                opacity: spoken ? 0.78 : 1,
                filter: active ? `drop-shadow(0 0 ${18 * pop + 6}px ${highlight}aa)` : "none",
              }}
            >
              {w.w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/**
 * P3b.S5 — phụ đề theo CỤM 1-3 từ (spec `captions[].chunks`, do Python chia).
 *
 * Khác bản cả câu ở trên ba điểm, đều có lý do:
 * - Mỗi lúc chỉ MỘT cụm, chữ to (`chunk_size_px`), nảy vào bằng spring — format
 *   TikTok mạnh (research/08 §1), và cụm ngắn nên to được mà vẫn một dòng.
 * - Không phóng to từng TỪ: bản cũ scale từ đang đọc 1,1-1,2× trong flex có gap cố
 *   định nên từ to lấn sang khoảng trắng ("Quantizationép" — eval 2026-10-01-p3b-s1).
 *   Giờ cả cụm nảy cùng nhau; từ đang đọc chỉ đổi màu.
 * - Không làm mờ từ đã đọc (cụm ngắn, không còn "phần đã qua" để mờ đi).
 * Từ `emph` (con số, tên model) luôn mang màu nhấn, kể cả khi chưa đọc tới.
 */
export const ChunkCaption: React.FC<{
  caption: Caption;
  style: TextStyle;
  safe: VideoSpec["style"]["safe_area_pct"];
  accent: string;
  emphColor: string;
}> = ({ caption, style, safe, accent, emphColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const chunks = caption.chunks ?? [];
  const k = chunks.findIndex((c) => t >= c.start_sec && t < c.end_sec);
  if (k < 0) return null;
  const ch = chunks[k];
  const sp = spring({
    frame: frame - Math.round(ch.start_sec * fps),
    fps,
    config: { damping: 12, stiffness: 230, mass: 0.6 },
  });
  const scale = 0.78 + 0.22 * sp;
  const stroke = style.stroke_px ?? 6;
  const highlight = style.highlight_color ?? accent;
  const size = (style.chunk_size_px ?? Math.round(style.size_px * 1.35)) * (ch.fit ?? 1);

  return (
    <AbsoluteFill>
      <div
        style={{
          ...posToBox(style.position, safe),
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "0 0.26em",
          fontFamily: fontStack(style.font),
          fontWeight: style.weight ?? 800,
          fontSize: size,
          lineHeight: 1.12,
          textAlign: "center",
          WebkitTextStroke: `${Math.round(stroke * 1.25)}px #000`,
          paintOrder: "stroke fill",
          textShadow: "0 6px 22px rgba(0,0,0,0.6)",
          transform: `scale(${scale})`,
          transformOrigin: "center top",
          opacity: Math.min(1, sp * 1.6),
        }}
      >
        {caption.words.slice(ch.from, ch.to).map((w, i) => {
          const active = t >= w.start && t < w.end;
          const color = w.emph ? emphColor : active ? highlight : style.color;
          return (
            <span key={`${ch.from + i}`} style={{ color, display: "inline-block" }}>
              {w.w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
