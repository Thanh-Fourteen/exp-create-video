import React from "react";
import { AbsoluteFill, Audio, Easing, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop, CARD_W, EVIDENCE_KINDS, Evidence } from "./components/Evidence";
import { MascotLayer } from "./components/Mascot";
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

/**
 * R4 (2026-10-04): nhãn kênh + bộ đếm cảnh "03 / 12" góc trên trái — kênh tham khảo @ainius.net (76.900 view) dùng bộ
 * đếm như thanh tiến độ ngầm: người xem biết còn bao nhiêu (research/probes/r-tham-khao-ainius.md). Đặt ngay dưới mép
 * an toàn trên (T1 safe_area top 8%) và trong lề trái 4%; chữ nhỏ, mờ — không tranh với hook.
 */
const BrandBar: React.FC<{ spec: VideoSpec }> = ({ spec }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const b = spec.style.brand ?? {};
  const n = spec.shots.length;
  const idx = Math.max(0, spec.shots.findIndex((s) => s.start_sec <= t && t < s.end_sec));
  const accent = b.accent ?? spec.style.palette.accent;
  return (
    <div
      style={{
        position: "absolute",
        left: (width * spec.style.safe_area_pct.left) / 100 + 14,
        top: (height * spec.style.safe_area_pct.top) / 100 + 18,
        display: "flex",
        alignItems: "center",
        gap: 14,
        fontFamily: '"Be Vietnam Pro", sans-serif',
        fontWeight: 800,
        fontSize: 30,
        letterSpacing: 2,
        color: "rgba(255,255,255,0.78)",
        textShadow: "0 2px 10px rgba(0,0,0,0.7)",
      }}
    >
      {b.label ? (
        <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ width: 14, height: 14, borderRadius: 7, background: accent }} />
          {b.label.toUpperCase()}
        </span>
      ) : null}
      {b.counter && n > 1 ? (
        <span style={{ fontVariantNumeric: "tabular-nums", color: accent }}>
          {String(idx + 1).padStart(2, "0")} / {String(n).padStart(2, "0")}
        </span>
      ) : null}
    </div>
  );
};

/**
 * D2/D3 (2026-10-04, research/15 §4): bố cục "headline". Video top của cả hai ngách giữ CHỦ ĐỀ luôn trên màn hình
 * (@aidev.news thẻ tin ×93, @ainius.net, @sidotech.ai, @tamlyhocthanhcong 425K) và gần như không cắt cảnh — hình đổi BÊN
 * TRONG một khung. Nhãn dạng video + tiêu đề cố định ở 12–23% chiều cao; ảnh trong khung bo góc 25–56%; phụ đề 58%+.
 */
const FRAME_LEFT = 62;   // = Evidence CARD_LEFT — mép phải 874px < lề UI phải 18% (886px)

const Headline: React.FC<{ spec: VideoSpec }> = ({ spec }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const lay = spec.style.layout!;
  const accent = spec.style.palette.accent;
  const enter = interpolate(frame, [0, Math.round(fps * 0.35)], [0, 1], { extrapolateRight: "clamp" });
  const title = lay.title ?? "";
  const size = title.length > 34 ? 66 : title.length > 22 ? 78 : 92;
  return (
    <div style={{ position: "absolute", left: FRAME_LEFT, width: CARD_W, top: height * 0.115, display: "flex",
                  flexDirection: "column", gap: 14, opacity: 0.35 + 0.65 * enter }}>
      {lay.badge ? (
        <div style={{ alignSelf: "flex-start", background: accent, color: "#0A1020", fontFamily: '"Be Vietnam Pro", sans-serif',
                      fontWeight: 900, fontSize: 30, letterSpacing: 1.5, padding: "6px 16px", borderRadius: 8 }}>
          {lay.badge.toUpperCase()}
        </div>
      ) : null}
      <div style={{ fontFamily: '"Be Vietnam Pro", sans-serif', fontWeight: 900, fontSize: size, lineHeight: 1.08,
                    color: "#FFFFFF", textShadow: "0 6px 30px rgba(0,0,0,0.6)", textWrap: "balance" as never,
                    transform: `translateY(${(1 - enter) * 24}px)` }}>
        {title}
      </div>
    </div>
  );
};

/**
 * Bố cục headline v2 (2026-10-05, research/18): ảnh/clip TRÀN TOÀN MÀN HÌNH 9:16. Bản v1 nhốt ảnh dọc trong khung
 * 812×595 ở 25–56% chiều cao → chỉ thấy ~45% ảnh, phóng to, đáy 40% trống (Tony: "bị bóp méo, khung nhỏ"). Video top
 * dùng ảnh/người thật đều phủ 89–100% chiều cao. Hai dải tối mờ giữ tiêu đề (trên) và phụ đề (dưới) đọc được.
 */
const Scrim: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none",
    // Đáy tối tối đa 0,5: bản 0,8 phủ ảnh vốn tối thành dải đen PHẲNG ở mép dưới → T1 "viền đen" bắt (video thử 2026-10-05,
    // 32px lúc 3,4s). Phụ đề có viền + bóng nên không cần nền đậm.
    background: "linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.45) 24%, rgba(0,0,0,0) 40%, " +
                "rgba(0,0,0,0) 52%, rgba(0,0,0,0.4) 68%, rgba(0,0,0,0.5) 100%)" }} />
);

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

  const lay = spec.style.layout;
  const totalFrames = Math.round(spec.format.duration_sec * fps);
  return (
    <AbsoluteFill style={{ backgroundColor: palette.bg }}>
      {lay ? <Backdrop spec={spec} durationInFrames={totalFrames} /> : null}
      <PunchZoom times={lay ? [] : emphTimes}>
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
              ) : lay ? (
                <>
                  <KenBurns
                    shot={shot}
                    durationInFrames={dur}
                    src={shot.asset.kind === "color" ? null : resolve(shot.asset.path)}
                    depthSrc={null}
                    bg={palette.bg}
                  />
                  <Scrim />
                </>
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
            {lay && shifted.chunks?.length ? (
              // Bố cục headline: tiêu đề cố định đã mang chữ hook → câu đầu chỉ là phụ đề thường.
              <ChunkCaption
                caption={shifted}
                style={{ ...spec.style.caption, position: "lower" }}
                safe={safe}
                accent={palette.accent}
                emphColor={palette.accent}
              />
            ) : cap.style === "hook" && cap.display_text && shifted.chunks?.length ? (
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

      {spec.style.mascot ? <MascotLayer spec={spec} /> : null}
      {lay ? <Headline spec={spec} /> : null}
      {spec.style.brand ? <BrandBar spec={spec} /> : null}

      {resolve(spec.audio.voice.path) ? (
        <Audio src={resolve(spec.audio.voice.path)!} volume={dbToGain(spec.audio.voice.gain_db)} />
      ) : null}
      {spec.audio.music && resolve(spec.audio.music.path) ? (
        <Audio src={resolve(spec.audio.music.path)!} volume={duckedGain} loop />
      ) : null}
    </AbsoluteFill>
  );
};
