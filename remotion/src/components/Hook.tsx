import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontStack } from "../fonts";
import type { TextStyle, VideoSpec } from "../types";

/**
 * Ba giây đầu — animation mạnh nhất video.
 *
 * `configs/thresholds.yaml` chấm hook nặng nhất trong T3 (weight 0,40, ngưỡng
 * riêng 8/10) vì người xem quyết định ở lại hay lướt trong khoảng này. Ở đây
 * không tiết chế: chữ to hơn phụ đề thường, vào bằng spring, có nhấn màu.
 */
export const Hook: React.FC<{
  text: string;
  style: TextStyle;
  safe: VideoSpec["style"]["safe_area_pct"];
  accent: string;
}> = ({ text, style, safe, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Frame 0 CHÍNH LÀ thumbnail và là thứ người lướt feed thấy đầu tiên — chữ
  // phải đọc được ngay, không được mờ dần vào. Trước đây opacity chạy từ 0 nên
  // frame 0 là chữ bán trong suốt đè ảnh rối (research/08 §1). Giờ: opacity luôn
  // 1, chỉ "đập" scale từ to về đúng cỡ — có lực mà không mất chữ ở frame nào.
  const punch = spring({ frame, fps, config: { damping: 14, mass: 0.5 } });
  const scale = 1.12 - punch * 0.12;

  return (
    <AbsoluteFill>
      {/* Dải tối phía trên: ảnh SDXL thường sáng/rối đúng vùng chữ hook, viền đen
          8px không đủ cứu. Gradient chứ không phải khối đặc để không thành "banner". */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.55) 32%, rgba(0,0,0,0) 52%)",
        }}
      />
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "flex-start",
          paddingTop: `${safe.top + 10}%`,
          paddingLeft: `${safe.left}%`,
          paddingRight: `${safe.right}%`,
        }}
      >
        <div
          style={{
            fontFamily: fontStack(style.font),
            fontWeight: style.weight ?? 400,
            fontSize: style.size_px,
            lineHeight: 1.1,
            textAlign: "center",
            color: style.color,
            WebkitTextStroke: `${style.stroke_px ?? 8}px #000`,
            paintOrder: "stroke fill",
            transform: `scale(${scale})`,
            textShadow: `0 0 40px ${accent}55`,
          }}
        >
          {text}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
