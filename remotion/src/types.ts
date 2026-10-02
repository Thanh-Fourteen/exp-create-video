/**
 * Kiểu TypeScript của `video-spec.json` — bản dịch 1-1 của
 * `src/create_video/spec/schema.json`.
 *
 * ⚠️ Hai file này phải đi cùng nhau. Nguồn chân lý là schema.json (Python sinh
 * spec, validate bằng nó); file này chỉ để TypeScript biết mình đang cầm gì.
 * Sửa schema mà quên sửa đây thì lỗi hiện ra lúc render, không lúc compile.
 *
 * Mọi `path` trong spec là **tương đối so với thư mục chứa chính file spec**.
 * Đó là lý do render.sh truyền `--public-dir` bằng đúng thư mục đó: một video =
 * một thư mục tự chứa, Remotion không với ra ngoài nó.
 */

export type Hex = string;

export interface FrameState {
  scale?: number;
  x_pct?: number;
  y_pct?: number;
}

/** P3b.S4 — shot "bằng chứng" vẽ từ dữ liệu. Chữ số ở đây do code vẽ. */
export interface StatData {
  value: number;
  decimals?: number;
  prefix?: string;
  unit?: string;
  label: string;
}

export interface ChartData {
  title: string;
  unit?: string;
  bars: { label: string; value: number; highlight?: boolean }[];
}

export interface CodeToken {
  t: "kw" | "str" | "num" | "com" | "fn" | "op" | "bi" | "txt";
  v: string;
}

export interface CodeData {
  lang: "python" | "bash" | "typescript" | "javascript" | "json" | "yaml" | "text";
  title?: string;
  lines: string[];
  /** Python (Pygments) sinh; mỗi dòng một dãy token. Thiếu thì vẽ trơn. */
  tokens?: CodeToken[][];
}

export type AssetKind = "image" | "video" | "color" | "stat" | "chart" | "screenshot" | "code";

export interface Shot {
  id: string;
  start_sec: number;
  end_sec: number;
  asset: {
    kind: AssetKind;
    /** Có với image/video/color/screenshot; KHÔNG có với stat/chart/code. */
    path?: string;
    alt?: string;
    depth_path?: string;
    source_url?: string;
    stat?: StatData;
    chart?: ChartData;
    code?: CodeData;
  };
  motion?: {
    type: "none" | "ken_burns" | "parallax";
    from?: FrameState;
    to?: FrameState;
  };
  transition_in?: {
    type: "cut" | "fade" | "whip-pan" | "slide-up";
    duration_frames?: number;
  };
  overlay?: {
    text: string;
    position?: "top" | "center" | "bottom";
    emphasis?: boolean;
  };
}

export interface CaptionWord {
  w: string;
  start: number;
  end: number;
  /** P3b.S5: từ cần nhấn (con số, tên model) — đổi màu. */
  emph?: boolean;
}

/** P3b.S5: một cụm 1-3 từ; `from`/`to` là chỉ số trong `words` (to không gồm). */
export interface CaptionChunk {
  start_sec: number;
  end_sec: number;
  from: number;
  to: number;
  /** Hệ số thu chữ riêng cụm này cho vừa một dòng (Python đo bằng file font). */
  fit?: number;
}

export interface Caption {
  start_sec: number;
  end_sec: number;
  text: string;
  style?: "caption" | "hook";
  /** Phase V3: chữ tiêu đề frame 0 (≤ 7 từ) khác lời đọc. */
  display_text?: string;
  words: CaptionWord[];
  chunks?: CaptionChunk[];
}

/** Overlay có thời gian riêng (schema 1.1) — hiện đúng lúc câu chứa nó được đọc. */
export interface TimedOverlay {
  start_sec: number;
  end_sec: number;
  text: string;
  position?: "top" | "center" | "bottom";
  emphasis?: boolean;
}

export interface TextStyle {
  font: string;
  weight?: number;
  size_px: number;
  chunk_size_px?: number;
  stroke_px?: number;
  color: Hex;
  highlight_color?: Hex;
  position?: "top" | "center" | "center-lower" | "bottom";
}

export interface VideoSpec {
  version: string;
  meta: {
    id: string;
    topic: string;
    created_at: string;
    sources?: { claim: string; url: string; confidence?: string }[];
    script_ref?: string;
    qc_round?: number;
  };
  format: { width: number; height: number; fps: number; duration_sec: number };
  shots: Shot[];
  captions: Caption[];
  overlays?: TimedOverlay[];
  audio: {
    voice: {
      path: string;
      duration_sec: number;
      gain_db?: number;
      backend?: string;
      voice_id?: string;
      timestamp_source?: string;
    };
    music?: { path: string; gain_db?: number; ducking?: boolean } | null;
  };
  style: {
    palette: { bg: Hex; fg: Hex; accent: Hex; warn?: Hex };
    caption: TextStyle;
    hook: TextStyle;
    safe_area_pct: { top: number; bottom: number; left: number; right: number };
  };
}

/** dB → hệ số nhân biên độ. Remotion `<Audio volume>` nhận hệ số, không nhận dB. */
export const dbToGain = (db: number | undefined): number =>
  db === undefined ? 1 : Math.pow(10, db / 20);
