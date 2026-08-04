import { Composition } from "remotion";
import { ProbeVideo } from "./ProbeVideo";

// P1.S3 — composition tối giản để ĐO thời gian render, không phải để dùng thật.
// Composition thật (đọc video-spec.json qua inputProps) là việc của P2.S2.
// 60s × 30fps = 1800 frame, đúng trần trên của thresholds.yaml t1_technical.duration_sec.
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Probe"
      component={ProbeVideo}
      durationInFrames={1800}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};
