# Nâng chất lượng video — audit repo + quét lại thị trường

**Ngày: 2026-10-01** · Câu hỏi: *từ pipeline hiện tại (P3 xong), cần đổi gì để video ra
"cực xịn" — tức Tony bấm Đăng (`approve_rate`), không phải để có thêm agent?*

Nguồn: (1) audit đọc-only toàn repo + soi frame/âm thanh thật của `out/demo-02`;
(2) ba lượt quét ngoài — hình/video trên 6GB, audio tiếng Việt, kỹ thuật dựng + repo
tham khảo. Mọi link dưới đây đã fetch ngày 2026-10-01 trừ chỗ ghi *reported*.

**Kết luận một dòng:** trần chất lượng hiện nay **không** nằm ở model — nằm ở (a) một
loạt lỗi dựng nhìn thấy được, (b) cách ghép giọng, (c) hình ảnh không mang thông tin.
Cả ba sửa được **không cần thêm VRAM**. Model mới chỉ đáng probe sau khi ba thứ đó xong.

---

## 1. Hiện trạng đo được (verified, tự đo 2026-10-01 trên `out/demo-02`)

| Khâu | Số đo / quan sát | Hệ quả |
|---|---|---|
| Giọng | 21 khoảng lặng 0,2–0,6s, **tổng 9,9s / 36,2s = 27%** là lặng; mỗi mối nối ≈0,55s (gap 0,28 + đệm đầu/đuôi TTS) | Đúng lời chê "đọc từng câu rời" của Tony |
| Loudness | Integrated **−20,0 LUFS**, true peak −5,7 dBFS | Nhỏ hơn mức phổ biến cho mobile ~6 dB |
| Chuyển cảnh | Frame 7,02s: **~60% khung đen**; 15,52s đen toàn khung | Sequence không chồng nhau → whip-pan trượt trên nền đen (`Video.tsx:43`, `Transition.tsx:31-36`) |
| Ken Burns | Dải đen ~24px mép phải đầu mỗi shot | `scale 1.0` + `x_pct ±2.5` (`build.py:142`, `KenBurns.tsx:51`) |
| Overlay số | "14 GB" hiện khi giọng đọc "mười sáu bit"; "16-bit", "4-bit" mất hẳn | Gán overlay theo chỉ số câu cho shot (`pipeline.py:176-179`, `build.py:239-245`) — **lỗi sự thật hiển thị** |
| Hook / thumbnail | Frame 0 chữ hook bán trong suốt đè ảnh rối | Spring opacity từ 0 (`Hook.tsx:22,46`) |
| Ảnh | Một look teal/amber cho mọi video; ảnh GPU mở đầu méo; ý trừu tượng → "khối phát sáng"; **0 frame mang thông tin thật** | `STYLE_SUFFIX` cố định, seed `0+i` mọi video (`sdxl.py:41,132`) |
| Caption | Cả câu ≤16 từ / 3 dòng hiện cùng lúc | Format TikTok mạnh là cụm 1–3 từ |
| Kịch bản | Không tool, không nguồn đầu vào; `sources` tự khai, chưa ai kiểm | `scriptwriter.py:246,255` |
| Test | `pytest -q tests` 19 pass; `pytest -q` trần **vỡ collect** (quét vào `exp/ltx/repo`) | thiếu `testpaths` |

Drift tài liệu: `research/probes/p4s1-vlm.md` được 3 nơi trỏ tới nhưng **không tồn tại**;
`qc/t2_vlm.py` đã viết nhưng không ai gọi; P3.S3 đánh PASS nhưng `flux.py`,
`screencast.py`, `router.py` chưa có; P3.S4 hứa `queue/state.json` chưa có;
`models.yaml: tts.backend` bị bỏ qua (pipeline hardcode `EchoBackend`).

## 2. Bằng chứng ngoài — cái gì làm short video "được xem"

Số liệu craft gần như đều là **dữ liệu quảng cáo** hoặc vendor; chỉ hai paper có cỡ mẫu.

| Phát hiện | Nguồn | Mức |
|---|---|---|
| Engagement theo **U ngược** với nhịp cắt, đỉnh ~**12 shot/60s** | Xue et al. [arXiv 2604.19995, 2026-04], 1.200 Reels + 14.492 video | verified |
| Top factor edutainment: **audio energy** 12,4%, motion/frame variance 10,7%, chữ-khác-lời 9,1% | Gupta et al. [arXiv 2512.21402, 2025-12], 11.000 Shorts | verified |
| 2 giây đầu có giá trị recall cao nhất; caption +58% recall; chữ 5–10 từ/s | TikTok/Lumen [2021, dữ liệu ad] | verified (ad) |
| Văn "AI slop": predictor mạnh nhất là **Relevance, Density, Tone** | Shaib et al. [arXiv 2509.19163, 2026-01] | verified |
| 78,6% clip dùng caption động | OpusClip [2026-04, vendor, không có số retention] | reported |

Hai paper lệch nhau về nhịp (Gupta thấy cắt nhanh tốt hơn) — khác nền tảng/ngách/biến
kết quả. Với ràng buộc **giọng tự nhiên > nhịp nhanh** của Tony, lấy hướng Xue: ~10–15
visual beat/60s, nhưng **mỗi shot phải có chuyển động phụ** (không frame tĩnh).

**Repo đáng lấy ý tưởng** (verified qua GitHub API 2026-10-01):

| Repo | ★ / license | Lấy gì |
|---|---|---|
| hassancs91/claude-faceless-shorts-creator | 271 / MIT | frame 0 = thumbnail; beat HOOK→SETUP→REVEAL→TWIST→LOOP; kết thúc loop về frame 0; render PNG cho LLM "xem" trước; thư viện SFX |
| tsensei/OpenReels | 204 / MIT | **archetype** = một khoá gói palette + kiểu caption + prompt ảnh; bước research chống bịa |
| `@remotion/captions` `createTikTokStyleCaptions` | Remotion | thay logic chia trang caption tự viết |
| remotion-dev/skills | 4.792 / — | skill best-practices cho Claude khi sinh code Remotion |
| Vincentwei1021/video-talkcraft | **PolyForm NC — chỉ đọc ý, không copy** | "frame tĩnh = lỗi" → làm thành check T1 |
| heygen-com/hyperframes | 54.962 / Apache-2.0 | đường thoát thứ hai nếu license Remotion thành vấn đề (cạnh Revideo) |
| MoneyPrinterTurbo | 127.760 / MIT | về chất lượng: **không có gì để lấy** (stock + slideshow) |

## 3. Audio

| | Phát hiện | Mức |
|---|---|---|
| VieNeu v3 Turbo | WER 3,3% (câu ngắn 6,7%), RTF 0,10 trên H200, 0,9GB [ViTTS-Bench, 2026-09] — ngang nhóm đầu trong số model dùng thương mại được | verified (1 nguồn) |
| ⚠️ License giọng | **Card HF hôm nay ghi Apache-2.0 cho cả preset voice, cho phép nội dung kiếm tiền** (commit "Clarify model license" 2026-06-30, 23 preset). `exp-echo` local ghi **CC-BY-NC-4.0, 14 preset** → nhiều khả năng đang dùng revision cũ | verified (cả hai) — **cần Tony kiểm revision** |
| Ứng viên khác | VoxCPM2 (Apache, WER vi 3,31 tự công bố, ~8GB bf16 — chỉ bản Q8 GGUF có cơ may); IndexTTS-2-vi tốt nhất (WER 1,8%) nhưng 8,9GB + phải xin phép; F5-vi, OmniVoice, viXTTS, VietTTS đều **NC** | verified |
| Thuật ngữ Anh | sea-g2p (G2P của VieNeu) có tag `<en>…</en>`; bug #23 đang mở: âm tiết Việt ngắn bị đọc kiểu Anh. Phiên âm tự động tốt nhất chỉ được chấp nhận 25–31% → **từ điển respelling do Tony duyệt** | verified |
| Nhạc sinh | **ACE-Step 1.5** MIT, output dùng thương mại; ≤6GB phải tắt LM + INT8 + offload, Turing chỉ cộng đồng hỗ trợ. MusicGen/YuE NC hoặc quá nặng | verified |
| SFX | Kenney audio packs **CC0** | verified |
| Loudness | "−14 LUFS cho TikTok" **không có nguồn chính thức** — chỉ blog | reported |

Kết luận: **chưa có lý do đổi model TTS.** Đổi cách gọi (cả đoạn / nghỉ theo dấu câu)
trước; chỉ khi Tony vẫn nghe ra máy móc mới probe model khác.

## 4. Hình ảnh trên 2060 6GB

| Ứng viên | Điểm chính | Mức |
|---|---|---|
| **Nunchaku INT4 + FLUX.1-schnell** | Turing hỗ trợ chính thức từ v0.2.0, có script `flux.1-dev-turing.py`; FLUX chạy được trên 2080S (issue #801); Apache-2.0 | verified |
| Nunchaku Z-Image-Turbo | Apache, chữ trong ảnh tốt hơn; v1.2.0 ghi "Turing compat" nhưng issue #15 (đang mở) báo **NaN/ảnh đen fp16 trên RTX 2060** | conflict — phải đo |
| Qwen-Image INT4 | crash trên sm_75 (#801, đóng không sửa) | loại |
| FLUX.2 klein 4B GGUF | Apache, Q4_K_M 2,6GB; text encoder chưa rõ | chưa đủ thông tin |
| Sana-Sprint | "exclusively bfloat16" | loại trên Turing |
| Video I2V | FramePack fork 20XX: **~40 phút/giây video** → loại; Wan2.2-5B ~9 phút/5s trên 4090 → loại; CogVideoX-2B FP16, 4GB nhưng 8fps, chỉ T2V | verified |
| LTX-2B **với offload theo layer** | P1.S4 OOM khi nạp trọn 6,34GB — chưa từng thử offload như SDXL đã làm | assumed: có cơ may, ưu tiên thấp |

**Quan trọng hơn model:** loại hình "bằng chứng" — screenshot trang model card / GitHub /
abs arXiv (Playwright, 0 VRAM), chart benchmark và thẻ số liệu vẽ bằng Remotion, đoạn
code (template Code Hike). Đây vừa là thứ chống slop (Relevance/Density), vừa là thứ
mà Gupta đo được là có ích (chữ trên hình khác lời đọc). Pháp lý: arXiv mặc định không
cấp quyền dùng lại figure → chỉ chụp trang abs/metadata; figure chỉ khi bài CC. Logo =
trademark, chỉ để nhận diện. Stock: Pexels (có video, bắt ghi nguồn khi dùng API).

## 5. Chấm tự động (cho P4)

LAION aesthetic predictor (Apache, nhẹ) chấm từng ảnh trước khi dựng; Qwen3-VL-4B 4-bit
là VLM-judge thực tế nhất; VideoScore2 làm cho video T2V chứ không phải video dựng.
UTMOS/DNSMOS **không có bằng chứng cho tiếng Việt** (ViTTS-Bench: MMS UTMOS cao nhất dù
WER tệ nhì) → không dùng làm ngưỡng giọng.

## 6. Hệ quả cho lộ trình

1. Chèn phase **P3b — Nâng chất lượng** *trước* P4: chấm QC 4 tầng trên video còn lỗi
   khung đen và overlay sai số chỉ tốn công chấm cái đã biết hỏng.
2. Thứ tự trong P3b theo (tác động)/(công): lỗi dựng → giọng → shot "bằng chứng" →
   caption → sound design → kịch bản có nguồn → model ảnh mới.
3. **Ngưỡng mới** (LUFS, shots/phút, frame tĩnh, dải đen) là *thêm kiểm*, không phải
   sửa ngưỡng cũ — nhưng vẫn ghi ở đây trước khi chạy:
   - integrated loudness **−14 ±1,5 LUFS**, true peak ≤ **−1,0 dBTP** *(chọn theo đồng
     thuận blog, reported; không có spec TikTok)*
   - **0 frame** có dải viền đen > 4px ngoài transition cố ý
   - không đoạn nào **> 2,0s** hoàn toàn tĩnh (chênh lệch frame ≈ 0)
   - visual beat **8–20 /phút** (cảnh báo, không chặn)

## Câu hỏi mở cho Tony

- Revision VieNeu trong `exp-echo` — kéo bản mới (Apache cho giọng) được không? Ảnh hưởng
  trực tiếp tới việc kênh có kiếm tiền được.
- Nhạc nền: sinh bằng ACE-Step, thư viện CC0, hay để trống cho Tony thêm nhạc trend trong
  app (đang ở chế độ draft nên làm được)?
- Có chấp nhận screenshot trang web thật (HF/GitHub/arXiv abs) trong video không?

---

## 7. Kết quả đợt 1 (cùng ngày, 2026-10-01) — Tony chốt "sửa lỗi dựng và giọng trước"

| | Trước (demo-02 / fixture cũ) | Sau | Nguồn |
|---|---|---|---|
| Pixel đen trong transition | 57–58% (max 84%) | **4%** | `eval/results/2026-10-01-p3b-s1.md` |
| Viền đen mép khung | 24–32px | **0** | như trên |
| Overlay đúng câu | 2/5 | **5/5** | `out/p3b-b/video-spec.json` |
| Loudness | −20,0 LUFS | **−14,7…−14,9** | `research/probes/p3b-s2-giong.md` |
| Lặng trong voice | 9,8s / 36,2s | 7,4s (grouped) · 8,0s (tight) | như trên |

Phát hiện ngoài dự kiến: **TTS lặp nguyên câu** (seed 7) — T1 không bắt được; đã thêm
chốt đọc lại tự động ở `voice/echo.py`. Và một **báo nhầm** của chính kiểm viền đen mới
(mặt bàn tối trong ảnh) — đã hiệu chỉnh trên số đo thật trước khi chốt, ghi trong
docstring `check_frame_edges_and_motion`.

Cùng ngày, theo yêu cầu Tony: bỏ P6 + P3b.S9, dọn repo (8,2GB chuyển sang
`/mnt/data1tb/_trash-exp-create-video-2026-10-01/`, chi tiết ở `todos.md` "Nợ kỹ thuật").
