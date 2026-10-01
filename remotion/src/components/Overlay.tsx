import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { fontStack } from "../fonts";
import type { Shot, VideoSpec } from "../types";

/**
 * Chữ dán trên shot: tên model, con số, mốc thời gian.
 *
 * KHÁC phụ đề karaoke — cái này không theo audio, nó là nhãn cho thứ đang xem.
 * Nội dung AI đầy tên riêng và con số mà tai người Việt nghe một lần không kịp
 * bắt ("Qwen3-VL", "6,34GB"); chữ trên hình là chỗ chúng bám lại được.
 */
export const OverlayText: React.FC<{
  overlay: NonNullable<Shot["overlay"]>;
  spec: VideoSpec;
  durationInFrames: number;
}> = ({ overlay, spec, durationInFrames }) => {
  const frame = useCurrentFrame();
  const safe = spec.style.safe_area_pct;
  const { accent, warn, fg } = spec.style.palette;

  const enter = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exit = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const justify =
    overlay.position === "center" ? "center" : overlay.position === "bottom" ? "flex-end" : "flex-start";

  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: justify,
        paddingTop: `${safe.top + 3}%`,
        paddingBottom: `${safe.bottom + 3}%`,
        paddingLeft: `${safe.left}%`,
        paddingRight: `${safe.right}%`,
        opacity: Math.min(enter, exit),
      }}
    >
      <div
        style={{
          fontFamily: fontStack(spec.style.caption.font),
          // Anton chỉ có weight 400; xin 800 thì Chrome tự "giả đậm" làm nhoè nét.
          fontWeight: spec.style.caption.weight ?? 400,
          fontSize: Math.round(spec.style.caption.size_px * 0.62),
          color: overlay.emphasis ? warn ?? accent : fg,
          background: "rgba(13,13,15,0.72)",
          border: `3px solid ${overlay.emphasis ? warn ?? accent : accent}`,
          borderRadius: 18,
          padding: "14px 26px",
          transform: `translateY(${(1 - enter) * 24}px)`,
        }}
      >
        {overlay.text}
      </div>
    </AbsoluteFill>
  );
};
