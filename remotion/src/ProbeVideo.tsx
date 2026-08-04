import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// P1.S3 — probe đo tốc độ render. Ba khối tải nặng nhất của video thật:
//   1. ảnh Ken Burns (scale + translate mỗi frame)
//   2. phụ đề karaoke (sáng từng từ theo timestamp)
//   3. hook 3 giây đầu (animation mạnh)
// Cố ý làm GẦN GIỐNG tải thật — probe nhẹ hơn thực tế thì số đo vô nghĩa.
// Số màu và biên độ zoom lấy từ configs/style.yaml.

const PALETTE = {
  bg: "#0D0D0F",
  fg: "#FFFFFF",
  accent: "#4DE1C1",
  highlight: "#FFE14D",
};

// Câu tiếng Việt CÓ DẤU — kiểm luôn xem headless Chrome dựng được dấu không.
const WORDS =
  "Con card sáu GB này vừa dựng xong một video TikTok mà không tốn một đồng nào".split(
    " ",
  );

const KenBurns: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // zoom_range [1.0, 1.15] theo configs/style.yaml — mạnh hơn thành chóng mặt
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.15]);
  const translateX = interpolate(frame, [0, durationInFrames], [0, -60]);

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img
        src={staticFile("probe-image.png")}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translateX(${translateX}px)`,
        }}
      />
    </AbsoluteFill>
  );
};

const KaraokeCaption: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Chia đều để probe — video thật lấy timestamp từ TTS (P1.S2).
  const framesPerWord = durationInFrames / WORDS.length;
  const activeIndex = Math.floor(frame / framesPerWord);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        // bottom 20% + left/right theo safe_area_pct của configs/thresholds.yaml
        paddingBottom: `${(20 / 100) * 1920}px`,
        paddingLeft: `${(4 / 100) * 1080}px`,
        paddingRight: `${(18 / 100) * 1080}px`,
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "0 18px",
          fontSize: 72,
          fontWeight: 800,
          fontFamily: "sans-serif",
          textAlign: "center",
          // stroke_px 6 — viền đen để đọc được trên mọi nền
          WebkitTextStroke: `6px ${PALETTE.bg}`,
          paintOrder: "stroke fill",
        }}
      >
        {WORDS.map((w, i) => (
          <span
            key={i}
            style={{
              color: i === activeIndex ? PALETTE.highlight : PALETTE.fg,
              transform: i === activeIndex ? "scale(1.08)" : "scale(1)",
              display: "inline-block",
            }}
          >
            {w}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const hookFrames = 3 * fps;

  if (frame > hookFrames) return null;

  const opacity = interpolate(frame, [0, 6, hookFrames - 6, hookFrames], [0, 1, 1, 0]);
  const y = interpolate(frame, [0, 12], [80, 0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity }}>
      <div
        style={{
          fontSize: 96,
          fontWeight: 900,
          fontFamily: "sans-serif",
          color: PALETTE.accent,
          transform: `translateY(${y}px)`,
          textAlign: "center",
          padding: "0 60px",
          WebkitTextStroke: `8px ${PALETTE.bg}`,
          paintOrder: "stroke fill",
        }}
      >
        Card 6GB làm được việc này
      </div>
    </AbsoluteFill>
  );
};

export const ProbeVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.bg }}>
      <KenBurns />
      <KaraokeCaption />
      <Hook />
    </AbsoluteFill>
  );
};
