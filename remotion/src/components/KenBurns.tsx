import React, { useState } from "react";
import { AbsoluteFill, Easing, Img, OffthreadVideo, interpolate, useCurrentFrame } from "remotion";
import type { FrameState, Shot } from "../types";
import { DepthParallax } from "./DepthParallax";

/**
 * Ảnh tĩnh + chuyển động do code sinh.
 *
 * Vì sao khối này quan trọng hơn vẻ ngoài của nó: 2060 6GB **không sinh được
 * video** (P1.S4 — LTX OOM ở mọi cấu hình), nên mọi cảm giác "động" của video
 * phải đến từ đây. Render chỉ tốn 1,5% ngân sách wall_time (P1.S3: 37s cho 60s
 * video) — đầu tư vào chuyển động ở đây là chỗ rẻ nhất để video đỡ tĩnh.
 */

const DEFAULT_FROM: FrameState = { scale: 1.0, x_pct: 0, y_pct: 0 };
const DEFAULT_TO: FrameState = { scale: 1.12, x_pct: 0, y_pct: 0 };

export const KenBurns: React.FC<{
  shot: Shot;
  durationInFrames: number;
  src: string | null;
  depthSrc?: string | null;
  bg: string;
}> = ({ shot, durationInFrames, src, depthSrc, bg }) => {
  const frame = useCurrentFrame();
  // Parallax 2.5D khi có depth map (P3b.S10). WebGL hỏng → lùi về Ken Burns phẳng
  // thay vì ra frame đen: thà mất chiều sâu còn hơn mất hình.
  const [glFailed, setGlFailed] = useState(false);
  const motion = shot.motion?.type ?? "ken_burns";

  // 2026-10-06 (research/21 §3): `segments` = đổi khung (toàn → cận → góc khác) mỗi ≤ 4–6s trong cùng một ảnh — video
  // viral đổi hình mỗi 2–4s (mẹo không mặt 2,6 lần/10s), shot ảnh của mình đứng 5–9s. Mỗi đoạn là một cú cắt góc máy.
  const segs = shot.motion?.segments;
  const nSeg = segs && segs.length >= 2 ? segs.length : 1;
  const segLen = durationInFrames / nSeg;
  const si = Math.min(nSeg - 1, Math.floor(frame / segLen));
  const lf = nSeg > 1 ? frame - Math.round(si * segLen) : frame;
  const lDur = nSeg > 1 ? Math.round((si + 1) * segLen) - Math.round(si * segLen) : durationInFrames;
  const from = { ...DEFAULT_FROM, ...(nSeg > 1 ? segs![si].from : shot.motion?.from ?? {}) };
  const to = { ...DEFAULT_TO, ...(nSeg > 1 ? segs![si].to : shot.motion?.to ?? {}) };
  // Easing nhẹ hai đầu: nội suy tuyến tính làm ảnh "giật" lúc bắt đầu và dừng
  // khựng ở cut. Bezier gần tuyến tính ở giữa nên chuyển động vẫn đều.
  const at = (a: number, b: number) =>
    interpolate(lf, [0, Math.max(lDur - 1, 1)], [a, b], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.33, 0, 0.67, 1),
    });

  const still = motion === "none";
  const x = still ? 0 : at(from.x_pct ?? 0, to.x_pct ?? 0);
  const y = still ? 0 : at(from.y_pct ?? 0, to.y_pct ?? 0);
  // Pan x% mà scale chưa đủ thì mép ảnh lộ ra thành dải nền đen — đo được
  // ~24px ở demo-02 (research/08 §1). Scale s phủ thêm (s-1)/2 mỗi bên, nên cần
  // s ≥ 1 + 2·|pan|/100. Kẹp Ở ĐÂY chứ không chỉ ở build.py: spec cũ (kể cả 3
  // fixture eval) vẫn mang giá trị sai và không được sửa tay.
  const minScale = 1 + (2 * Math.max(Math.abs(x), Math.abs(y))) / 100 + 0.005;
  const scale = still ? 1 : Math.max(at(from.scale ?? 1, to.scale ?? 1), minScale);

  // `kind: "color"` — nền phẳng, dùng khi chưa có ảnh (khối visual tắt) hoặc khi
  // shot cố ý chỉ có chữ. Không có gì để zoom nên bỏ luôn transform.
  if (shot.asset.kind === "color" || !src) {
    return <AbsoluteFill style={{ backgroundColor: shot.asset.kind === "color" ? shot.asset.path ?? bg : bg }} />;
  }

  if (shot.motion?.type === "parallax" && depthSrc && !glFailed && shot.asset.kind === "image") {
    return (
      <DepthParallax
        shot={shot}
        src={src}
        depthSrc={depthSrc}
        durationInFrames={durationInFrames}
        bg={bg}
        onFail={() => setGlFailed(true)}
      />
    );
  }

  const inner: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    // translate TRƯỚC scale: đổi thứ tự thì biên độ pan bị nhân theo zoom và
    // ảnh trôi ra ngoài khung ở cuối shot.
    transform: `translate(${x}%, ${y}%) scale(${scale})`,
    transformOrigin: "center center",
  };

  return (
    <AbsoluteFill style={{ backgroundColor: bg, overflow: "hidden" }}>
      {shot.asset.kind === "video" ? (
        // stock (2026-10-05): OffthreadVideo trích đúng frame khi render headless (Video có thể lệch/giật).
        <OffthreadVideo src={src} style={{ ...inner, objectFit: "cover" }} muted />
      ) : (
        <Img src={src} style={inner} />
      )}
    </AbsoluteFill>
  );
};
