import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { Hook } from "./components/Hook";
import { KaraokeCaption } from "./components/KaraokeCaption";
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

  return (
    <AbsoluteFill style={{ backgroundColor: palette.bg }}>
      {spec.shots.map((shot, k) => {
        const from = secToFrames(shot.start_sec, fps);
        const dur = Math.max(secToFrames(shot.end_sec - shot.start_sec, fps), 1);
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
              <KenBurns
                shot={shot}
                durationInFrames={dur}
                src={shot.asset.kind === "color" ? null : resolve(shot.asset.path)}
                depthSrc={resolve(shot.asset.depth_path)}
                bg={palette.bg}
              />
              {shot.overlay ? (
                <OverlayText overlay={shot.overlay} spec={spec} durationInFrames={dur} />
              ) : null}
            </Transition>
          </Sequence>
        );
      })}

      {(spec.overlays ?? []).map((ov, i) => {
        const from = secToFrames(ov.start_sec, fps);
        const dur = Math.max(secToFrames(ov.end_sec - ov.start_sec, fps), 1);
        return (
          <Sequence key={`ov-${i}`} from={from} durationInFrames={dur} name={`overlay ${i}`}>
            <OverlayText overlay={ov} spec={spec} durationInFrames={dur} />
          </Sequence>
        );
      })}

      {spec.captions.map((cap, i) => {
        const from = secToFrames(cap.start_sec, fps);
        const dur = Math.max(secToFrames(cap.end_sec - cap.start_sec, fps), 1);
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
        };
        return (
          <Sequence key={`cap-${i}`} from={from} durationInFrames={dur} name={`caption ${i}`}>
            {cap.style === "hook" ? (
              <Hook text={cap.text} style={spec.style.hook} safe={safe} accent={palette.accent} />
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
