import React from "react";
import { AbsoluteFill, Audio, Easing, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { EVIDENCE_KINDS, Evidence } from "./components/Evidence";
import { Hook } from "./components/Hook";
import { ChunkCaption, KaraokeCaption } from "./components/KaraokeCaption";
import { KenBurns } from "./components/KenBurns";
import { OverlayText } from "./components/Overlay";
import { Transition } from "./components/Transition";
import { dbToGain, type VideoSpec } from "./types";

/**
 * Composition chính: `video-spec.json` → mp4 1080×1920.
 *
 * Đây là phía TIÊU THỤ của ranh giới duy nhất giữa Python và TypeScript. File
 * này **không đọc YAML, không gọi Python, không tự quyết nội dung** — mọi thứ nó
 * cần đều nằm trong spec. Đó chính là thứ cho phép đổi Remotion → Revideo mà
 * không đụng phần còn lại (research/05-decision.md).
 *
 * Mọi `path` trong spec tương đối so với thư mục chứa spec, và render.sh truyền
 * đúng thư mục đó làm `--public-dir` → `staticFile(path)` giải ra file thật.
 */

const secToFrames = (sec: number, fps: number) => Math.round(sec * fps);

/**
 * Độ dài = hiệu hai mốc ĐÃ làm tròn, KHÔNG làm tròn hiệu số giây. Làm tròn riêng
 * thì đầu-cuối hai shot liền nhau có thể hở 1 frame: 2026-10-01 `out/p3b-s4-demo`
 * s4 = 11,677→15,96s ra frame 350 + 128 = 478, còn s5 bắt đầu round(478,8) = 479 →
 * frame 478 trống trơn nền. T1 "frame đen" (> 0,5s) không thấy; "viền đen" thấy.
 */
const spanFrames = (start: number, end: number, fps: number) =>
  Math.max(secToFrames(end, fps) - secToFrames(start, fps), 1);

/**
 * Punch-in: khung hình giật vào nhẹ (×1,06) đúng lúc đọc từ được NHẤN (`words[].emph`, P3b.S5),
 * rồi trả về trong ~0,5s. Thêm 2026-10-02 sau khi Tony chê "video chưa hấp dẫn": research
 * (Xue et al., arXiv 2604.19995) — nhịp kích thích thị giác là top-3 yếu tố, nhưng chữ U ngược,
 * nên chỉ bám vào từ nhấn (2–6 lần/video), không giật liên tục. Dữ liệu lấy từ spec, không tự quyết.
 */
const PUNCH = 0.06;
const PunchZoom: React.FC<{ times: number[]; children: React.ReactNode }> = ({ times, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  let s = 1;
  for (const at of times) {
    const d = t - at;
    if (d < -0.1 || d > 0.6) continue;
    const up = interpolate(d, [-0.1, 0.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const down = interpolate(d, [0.0, 0.6], [1, 0], {
      extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
    });
    s = Math.max(s, 1 + PUNCH * Math.min(up, down));
  }
  return <AbsoluteFill style={{ transform: `scale(${s})` }}>{children}</AbsoluteFill>;
};

/** Hiệu màu nhẹ cho lớp hình: sáng/bão hoà hơn — "brightness" là top-3 yếu tố (cùng nguồn trên). */
const GRADE = "saturate(1.18) contrast(1.06) brightness(1.05)";

export const VideoFromSpec: React.FC<VideoSpec> = (spec) => {
  const { fps } = useVideoConfig();
  const { palette, safe_area_pct: safe } = spec.style;

  const resolve = (p: string | undefined | null) =>
    p && p.length > 0 ? staticFile(p) : null;

  // Ducking: nhạc nền chìm hẳn khi có tiếng nói. `music_gain_db: -18` ở
  // style.yaml đã thấp, nhưng lời nói và nhạc cùng dải trung nên vẫn phải hạ
  // thêm — không thì giọng nghe "đục" trên loa điện thoại.
  const musicGain = dbToGain(spec.audio.music?.gain_db);
  const duckedGain = spec.audio.music?.ducking === false ? musicGain : musicGain * 0.45;

  // Mốc các từ được nhấn — thời gian tuyệt đối của cả video (tối đa 1 lần / 1,2s).
  const emphTimes: number[] = [];
  for (const cap of spec.captions) {
    for (const w of cap.words) {
      // Phase V (2026-10-02): KHÔNG punch-in khi hình đang là thẻ bằng chứng — thẻ lệch trái (lề phải
      // 18% > lề trái 4%) nên phóng quanh tâm khung đẩy mép trái vào vùng UI (T1 bắt ở v2, 2,17s).
      const onEvidence = spec.shots.some(
        (sh) => sh.start_sec <= w.start && w.start < sh.end_sec && EVIDENCE_KINDS.has(sh.asset.kind),
      );
      if (onEvidence) continue;
      if ((w as { emph?: boolean }).emph && (!emphTimes.length || w.start - emphTimes[emphTimes.length - 1] > 1.2)) {
        emphTimes.push(w.start);
      }
    }
  }

  return (
    <AbsoluteFill style={{ backgroundColor: palette.bg }}>
      <PunchZoom times={emphTimes}>
      <AbsoluteFill style={{ filter: GRADE }}>
      {spec.shots.map((shot, k) => {
        const from = secToFrames(shot.start_sec, fps);
        const dur = spanFrames(shot.start_sec, shot.end_sec, fps);
        // Shot cũ SỐNG THÊM đúng số frame transition của shot sau, nằm dưới nó.
        // Trước đây các Sequence nối đuôi nhau, nên whip-pan/fade trượt shot mới
        // vào trên NỀN ĐEN — đo được ~60% khung đen ở demo-02 (research/08 §1).
        // Thời điểm shot sau bắt đầu không đổi, nên phụ đề và tổng độ dài giữ nguyên;
        // Sequence sau render muộn hơn trong DOM nên tự nằm trên.
        const next = spec.shots[k + 1]?.transition_in;
        const tail = next && next.type !== "cut" ? next.duration_frames ?? 0 : 0;
        return (
          <Sequence key={shot.id} from={from} durationInFrames={dur + tail} name={`shot ${shot.id}`}>
            <Transition transition={shot.transition_in}>
              {EVIDENCE_KINDS.has(shot.asset.kind) ? (
                // P3b.S4: shot bằng chứng vẽ từ dữ liệu trong spec (stat/chart/code)
                // hoặc ảnh chụp trang thật (screenshot).
                <Evidence
                  shot={shot}
                  spec={spec}
                  durationInFrames={dur}
                  src={resolve(shot.asset.path)}
                  belowHook={k === 0 && Boolean(spec.captions[0]?.display_text)}
                />
              ) : (
                <KenBurns
                  shot={shot}
                  durationInFrames={dur}
                  src={shot.asset.kind === "color" ? null : resolve(shot.asset.path)}
                  depthSrc={resolve(shot.asset.depth_path)}
                  bg={palette.bg}
                />
              )}
              {shot.overlay ? (
                <OverlayText overlay={shot.overlay} spec={spec} durationInFrames={dur} />
              ) : null}
            </Transition>
          </Sequence>
        );
      })}

      </AbsoluteFill>
      </PunchZoom>

      {(spec.overlays ?? []).map((ov, i) => {
        const from = secToFrames(ov.start_sec, fps);
        const dur = spanFrames(ov.start_sec, ov.end_sec, fps);
        return (
          <Sequence key={`ov-${i}`} from={from} durationInFrames={dur} name={`overlay ${i}`}>
            <OverlayText overlay={ov} spec={spec} durationInFrames={dur} />
          </Sequence>
        );
      })}

      {spec.captions.map((cap, i) => {
        const from = secToFrames(cap.start_sec, fps);
        const dur = spanFrames(cap.start_sec, cap.end_sec, fps);
        // Timestamp trong spec là thời gian TUYỆT ĐỐI của cả video, còn bên
        // trong Sequence thì frame đếm lại từ 0. Trừ đi `start_sec` ở đây, một
        // lần, thay vì bắt mỗi component tự nhớ — quên chỗ này thì phụ đề tô
        // sáng lệch đúng bằng vị trí của caption trong video.
        const shifted = {
          ...cap,
          words: cap.words.map((w) => ({
            ...w,
            start: w.start - cap.start_sec,
            end: w.end - cap.start_sec,
          })),
          chunks: cap.chunks?.map((c) => ({
            ...c,
            start_sec: c.start_sec - cap.start_sec,
            end_sec: c.end_sec - cap.start_sec,
          })),
        };
        return (
          <Sequence key={`cap-${i}`} from={from} durationInFrames={dur} name={`caption ${i}`}>
            {cap.style === "hook" && cap.display_text && shifted.chunks?.length ? (
              <>
                <Hook
                  text={cap.display_text}
                  style={spec.style.hook}
                  safe={safe}
                  accent={palette.accent}
                  plain={EVIDENCE_KINDS.has(spec.shots[0]?.asset.kind ?? "")}
                />
                <ChunkCaption
                  caption={shifted}
                  style={spec.style.caption}
                  safe={safe}
                  accent={palette.accent}
                  emphColor={palette.accent}
                />
              </>
            ) : cap.style === "hook" ? (
              <Hook text={cap.text} style={spec.style.hook} safe={safe} accent={palette.accent} />
            ) : shifted.chunks?.length ? (
              <ChunkCaption
                caption={shifted}
                style={spec.style.caption}
                safe={safe}
                accent={palette.accent}
                emphColor={palette.accent}
              />
            ) : (
              <KaraokeCaption
                caption={shifted}
                style={spec.style.caption}
                safe={safe}
                accent={palette.accent}
              />
            )}
          </Sequence>
        );
      })}

      {resolve(spec.audio.voice.path) ? (
        <Audio src={resolve(spec.audio.voice.path)!} volume={dbToGain(spec.audio.voice.gain_db)} />
      ) : null}
      {spec.audio.music && resolve(spec.audio.music.path) ? (
        <Audio src={resolve(spec.audio.music.path)!} volume={duckedGain} loop />
      ) : null}
    </AbsoluteFill>
  );
};
