import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { Shot } from "../types";

/**
 * Chuyển cảnh vào đầu mỗi shot.
 *
 * Mặc định là **cut** — `configs/style.yaml` chọn thế có chủ ý: cut hợp nhịp
 * TikTok hơn fade. Fade/whip-pan để dành cho chỗ muốn nhấn, đừng rải đều.
 */
export const Transition: React.FC<{
  transition: Shot["transition_in"];
  children: React.ReactNode;
}> = ({ transition, children }) => {
  const frame = useCurrentFrame();
  const type = transition?.type ?? "cut";
  const dur = transition?.duration_frames ?? 0;

  if (type === "cut" || dur <= 0) {
    return <AbsoluteFill>{children}</AbsoluteFill>;
  }

  const t = interpolate(frame, [0, dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const style: React.CSSProperties =
    type === "fade"
      ? { opacity: t }
      : type === "whip-pan"
        ? {
            transform: `translateX(${(1 - t) * 100}%)`,
            // Blur giảm dần: whip-pan không có blur trông như slide, không như whip.
            filter: `blur(${(1 - t) * 12}px)`,
          }
        : { transform: `translateY(${(1 - t) * 30}%)`, opacity: t };

  return <AbsoluteFill style={style}>{children}</AbsoluteFill>;
};
