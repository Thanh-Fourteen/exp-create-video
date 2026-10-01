import type { VideoSpec } from "./types";

/**
 * Spec rỗng để Remotion Studio mở được khi chưa truyền `--props`.
 * KHÔNG dùng để render thật — không có asset, không có audio thật.
 */
export const PLACEHOLDER_SPEC: VideoSpec = {
  version: "1.0",
  meta: { id: "placeholder", topic: "chưa truyền --props", created_at: "" },
  format: { width: 1080, height: 1920, fps: 30, duration_sec: 15 },
  shots: [
    {
      id: "s1",
      start_sec: 0,
      end_sec: 15,
      asset: { kind: "color", path: "#0D0D0F" },
      motion: { type: "none" },
    },
  ],
  captions: [
    {
      start_sec: 0.5,
      end_sec: 4,
      text: "Chưa có spec — truyền --props",
      style: "hook",
      words: [
        { w: "Chưa", start: 0.5, end: 0.9 },
        { w: "có", start: 0.9, end: 1.2 },
        { w: "spec", start: 1.2, end: 1.7 },
        { w: "—", start: 1.7, end: 1.8 },
        { w: "truyền", start: 1.8, end: 2.3 },
        { w: "--props", start: 2.3, end: 3.2 },
      ],
    },
  ],
  audio: { voice: { path: "", duration_sec: 15 }, music: null },
  style: {
    palette: { bg: "#0D0D0F", fg: "#FFFFFF", accent: "#4DE1C1", warn: "#FF6B4D" },
    caption: {
      font: "Anton",
      weight: 400,
      size_px: 72,
      stroke_px: 6,
      color: "#FFFFFF",
      highlight_color: "#FFE14D",
      position: "center-lower",
    },
    hook: {
      font: "Anton",
      weight: 400,
      size_px: 96,
      stroke_px: 8,
      color: "#FFFFFF",
      highlight_color: "#FFE14D",
      position: "top",
    },
    safe_area_pct: { top: 8, bottom: 20, left: 4, right: 18 },
  },
};
