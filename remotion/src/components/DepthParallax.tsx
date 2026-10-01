import React, { useEffect, useRef, useState } from "react";
import {
  AbsoluteFill,
  Easing,
  continueRender,
  delayRender,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { FrameState, Shot } from "../types";

/**
 * Parallax 2.5D: ảnh tĩnh + depth map → camera trôi TRONG cảnh (P3b.S10).
 *
 * Vì sao: Tony "ảnh chưa sinh động". Ken Burns zoom cả ảnh như một tấm phẳng; ở đây
 * vật gần dịch nhiều hơn vật xa, nên mắt đọc ra chiều sâu. 2060 không sinh nổi video
 * (research/09), còn depth map chỉ tốn ~0,5s/ảnh (Depth Anything V2-Small).
 *
 * Kỹ thuật: shader dịch toạ độ lấy mẫu theo (depth − focus) × offset, lặp 4 lần để
 * xấp xỉ che khuất (parallax occlusion rẻ). Biên độ nhỏ (≤ ~2,5% bề rộng) — lớn hơn
 * là mép vật bị kéo như kẹo, đúng "bẫy" đã ghi ở todos.
 *
 * `motion.from/to` dùng lại FrameState: x_pct/y_pct = độ lệch camera (% bề rộng),
 * scale = zoom. Không có WebGL hoặc depth → component cha dùng Ken Burns.
 */

const VERT = `
attribute vec2 p;
varying vec2 uv;
void main() { uv = vec2(p.x * 0.5 + 0.5, 0.5 - p.y * 0.5); gl_Position = vec4(p, 0.0, 1.0); }`;

const FRAG = `
precision highp float;
varying vec2 uv;
uniform sampler2D img;
uniform sampler2D dep;
uniform vec2 offset;     // độ lệch camera, đơn vị uv
uniform float scale;     // zoom
uniform vec2 cover;      // phần ảnh hiển thị theo mỗi trục (object-fit: cover), ≤ 1
uniform float focus;     // độ sâu đứng yên (0 xa .. 1 gần)
void main() {
  vec2 base = (uv - 0.5) * cover / scale + 0.5;
  vec2 q = base;
  for (int i = 0; i < 4; i++) {
    float d = texture2D(dep, q).r;
    q = base + offset * (d - focus);
  }
  gl_FragColor = texture2D(img, clamp(q, 0.001, 0.999));
}`;

const loadImage = (src: string) =>
  new Promise<HTMLImageElement>((res, rej) => {
    const im = new Image();
    im.crossOrigin = "anonymous";
    im.onload = () => res(im);
    im.onerror = () => rej(new Error(`không nạp được ${src}`));
    im.src = src;
  });

type GLState = {
  gl: WebGLRenderingContext;
  loc: Record<string, WebGLUniformLocation | null>;
  aspect: number;
};

function setup(canvas: HTMLCanvasElement, img: HTMLImageElement, dep: HTMLImageElement): GLState | null {
  const gl = canvas.getContext("webgl", { preserveDrawingBuffer: true, antialias: false });
  if (!gl) return null;
  const sh = (type: number, src: string) => {
    const s = gl.createShader(type)!;
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s) ?? "shader");
    return s;
  };
  const prog = gl.createProgram()!;
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT));
  gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog);
  gl.useProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const p = gl.getAttribLocation(prog, "p");
  gl.enableVertexAttribArray(p);
  gl.vertexAttribPointer(p, 2, gl.FLOAT, false, 0, 0);

  const tex = (unit: number, im: HTMLImageElement) => {
    const t = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
  };
  tex(0, img);
  tex(1, dep);
  const loc: GLState["loc"] = {};
  for (const n of ["img", "dep", "offset", "scale", "cover", "focus"]) loc[n] = gl.getUniformLocation(prog, n);
  gl.uniform1i(loc.img, 0);
  gl.uniform1i(loc.dep, 1);
  return { gl, loc, aspect: img.width / img.height };
}

export const DepthParallax: React.FC<{
  shot: Shot;
  src: string;
  depthSrc: string;
  durationInFrames: number;
  bg: string;
  onFail: () => void;
}> = ({ shot, src, depthSrc, durationInFrames, bg, onFail }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const canvas = useRef<HTMLCanvasElement>(null);
  const [st, setSt] = useState<GLState | null>(null);
  const [handle] = useState(() => delayRender(`parallax ${shot.id}`));

  useEffect(() => {
    let alive = true;
    Promise.all([loadImage(src), loadImage(depthSrc)])
      .then(([img, dep]) => {
        if (!alive || !canvas.current) return;
        const s = setup(canvas.current, img, dep);
        if (!s) onFail();
        else setSt(s);
      })
      .catch(() => onFail())
      .finally(() => continueRender(handle));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src, depthSrc]);

  const from: FrameState = { scale: 1.06, x_pct: -2, y_pct: 0, ...(shot.motion?.from ?? {}) };
  const to: FrameState = { scale: 1.12, x_pct: 2, y_pct: 0, ...(shot.motion?.to ?? {}) };
  const at = (a: number, b: number) =>
    interpolate(frame, [0, Math.max(durationInFrames - 1, 1)], [a, b], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.33, 0, 0.67, 1),
    });

  if (st) {
    const { gl, loc, aspect } = st;
    const frameAspect = width / height;
    // object-fit: cover — phóng chiều dư để không lộ nền.
    const cover: [number, number] = aspect > frameAspect ? [frameAspect / aspect, 1] : [1, aspect / frameAspect];
    gl.viewport(0, 0, width, height);
    gl.uniform2f(loc.offset, at(from.x_pct ?? 0, to.x_pct ?? 0) / 100, at(from.y_pct ?? 0, to.y_pct ?? 0) / 100);
    // Kẹp như KenBurns: dịch tới 2·|offset|·(1−focus) ở mép cần zoom đủ để không lộ mép.
    gl.uniform1f(loc.scale, Math.max(at(from.scale ?? 1.06, to.scale ?? 1.12), 1.06));
    gl.uniform2f(loc.cover, cover[0], cover[1]);
    gl.uniform1f(loc.focus, 0.35);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  return (
    <AbsoluteFill style={{ backgroundColor: bg }}>
      <canvas ref={canvas} width={width} height={height} style={{ width: "100%", height: "100%" }} />
    </AbsoluteFill>
  );
};
