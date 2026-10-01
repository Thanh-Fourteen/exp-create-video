import { Composition } from "remotion";
import { PLACEHOLDER_SPEC } from "./placeholder";
import { VideoFromSpec } from "./Video";
import type { VideoSpec } from "./types";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Composition thật. Kích thước/độ dài lấy từ spec truyền qua --props,
          KHÔNG hằng số hoá ở đây: spec là nguồn chân lý duy nhất. */}
      {/* Cast: Remotion gõ props của Composition là Record<string, unknown>,
          còn spec là một kiểu cụ thể. Cách tránh cast là bọc spec vào một prop
          ({spec: ...}) — nhưng như thế file Python ghi ra sẽ KHÁC file Remotion
          đọc vào, và ranh giới duy nhất mất tính "một file, hai bên dùng chung".
          Đổi một cast lấy điều đó là đáng. */}
      <Composition
        id="Video"
        component={VideoFromSpec as unknown as React.FC<Record<string, unknown>>}
        defaultProps={PLACEHOLDER_SPEC as unknown as Record<string, unknown>}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={({ props }) => {
          const spec = props as unknown as VideoSpec;
          return {
            durationInFrames: Math.round(spec.format.duration_sec * spec.format.fps),
            fps: spec.format.fps,
            width: spec.format.width,
            height: spec.format.height,
          };
        }}
      />

      {/* Composition "Probe" của P1.S3 đã bỏ 2026-10-01: mốc đo khối render giờ là
          3 fixture ở eval/scripts/ (eval/README.md), sát video thật hơn nhiều. */}
    </>
  );
};
