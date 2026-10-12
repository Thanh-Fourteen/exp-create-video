# Cảnh thật hơn · lời tự nhiên hơn · nhân vật hoạt hình — 2026-10-05

**Tony (2026-10-05):** *"Tôi nghĩ cần tỷ lệ hình ảnh thật, video thật nhiều hơn mới hấp dẫn người xem. Về scripts đọc đang
bị AI quá, cần tự nhiên hơn, nhấn nhả nhịp giọng cần tốt hơn. Thêm nhân vật animation."*

Ba paper-scout song song (văn nói, prosody TTS tiếng Việt, nhân vật biết nói) + đo trên kịch bản thật. **V** verified ·
**R** reported · **A** assumed.

## 1. Cảnh thật

| | Trước | Sau |
|---|---|---|
| Luật | `image_min_ratio` (ảnh AI + stock ≥ 40%, chỉ kênh mẹo) | thêm `real_min_ratio`: **stock ≥ 40% (mẹo), ≥ 25% (AI)** — code chặn, trả kịch bản |
| Không có clip | lùi về ảnh AI | **ảnh CHỤP thật** Pexels/Pixabay (`stock.fetch_photo`, cắt 1080×1920) trước, ảnh AI là đường cuối (V: 3/3 truy vấn thử ra ảnh) |
| Ảnh thật | — | Ken Burns như ảnh AI |
| Prompt | "Ảnh AI là phương án CUỐI" | + "`image` chỉ cho cảnh KHÔNG quay được ngoài đời" |

## 2. Lời tự nhiên (kịch bản)

**Chẩn đoán (V, đo 2 kịch bản 2026-10-05):** mọi câu 11–16 từ, độ chênh độ dài (σ/μ) **0,09**; gạch ngang "—"; gần như
không từ nối/tiểu từ. Gốc: prompt cũ *"Bỏ mọi câu chuyển tiếp"* + trần **5–16 từ/câu** (đặt hồi đọc từng câu rồi ghép —
nay đọc cả đoạn một lần nên lý do không còn). Lời thật kênh top (ASR `out/tham-khao/*/phan-tich.json`) chảy liền, có
"nói gọn ra thì như này nhé", "mọi người cứ để ý mà xem", hỏi rồi tự trả lời.

**Bằng chứng ngoài (V):** LLM instruction-tuned dùng mệnh đề phân từ 2–5×, danh từ hoá 1,5–2× người (Reinhart et al., PNAS
2025); người dùng ChatGPT nhiều nhận ra văn AI qua từ vựng, "không chỉ… mà còn", liệt kê 3 vế, ngữ pháp "hoàn hảo bất
thường" (Russell et al. 2025); few-shot từ mẫu thật tăng mạnh độ khớp phong cách, chọn mẫu ĐA DẠNG phong cách chứ không
giống nội dung (arXiv 2509.24930, 2509.14543); viết cho tai: câu ≤ 20 từ phần lớn, câu cụt được phép (UF IFAS). Tiếng
Việt: Brands Vietnam 2025-09 (R, ý kiến biên tập).

**Đổi:** trần 2–26 từ/câu · khối **VĂN NÓI V1–V7** (chỉ dẫn tích cực + 3 trích lời thật mỗi kênh, `speech_examples`) ·
ngôi "mình – bạn" · `_check_speech`: dấu hiệu văn AI, σ/μ độ dài câu ≥ **0,35**, ≥ ¼ câu có từ nối/tiểu từ — lỗi
văn nói là **mềm** (lần thử cuối vẫn cho qua kèm cảnh báo, không làm hỏng video).

## 3. Nhấn nhả giọng

VieNeu v3 Turbo: `style` **không còn tác dụng**, phong cách chỉ đến từ clip tham chiếu; có thẻ `[cười]` `[thở dài]` (thử
nghiệm); không SSML/thẻ ngắt (V, repo + HF card). Đo của bên thứ ba: VieNeu ngắt ở dấu phẩy **60–650 ms** (V, PR #11
srt-whiteboard-animation, 2026-10-02). Model khác: Gwen-TTS (MIT, Qwen3-TTS fine-tune trên ~1000 h audio TikTok Việt)
đáng probe; F5 zalopay (CC-BY) dự phòng; Chatterbox/CosyVoice/Qwen3/IndexTTS2 không dùng được cho tiếng Việt.

**Đổi:** `_reshape_pauses` — sau dấu câu nới khoảng lặng tới đủ (phẩy 0,20 · chấm 0,42 · hỏi 0,48 · "…" 0,55 s), giữa
cụm không dấu mà lặng > 0,30 s rút về 0,10 s; chỉ cắt mẫu ≤ −40 dBFS; mốc từ dời theo (`configs/models.yaml: tts.post.pauses`).
Kịch bản (V6) đặt dấu câu ở chỗ cần ngắt/nhấn → code ngắt đúng chỗ đó.
**Chưa làm:** clip tham chiếu sôi nổi hơn (Tony không có thời gian thu — có thể cắt đoạn sôi nổi từ bản thu cũ); probe
Gwen-TTS; quét temperature (API exp-echo chưa mở tham số).

## 4. Nhân vật hoạt hình

Nghiên cứu (V): chưa model diffusion nào có số đo trên T4 hay mặt hoạt hình + audio tiếng Việt; EchoMimicV3-Flash
(Apache, 12 GB) và HunyuanVideo-Avatar (khẳng định hỗ trợ cartoon, license cần đọc) là ứng viên Kaggle; Rhubarb Lip Sync
(MIT) cho rối 2D không GPU.

**Quyết định:** làm trước bản **0 GPU** — nhân vật SVG vẽ bằng code trong Remotion (`components/Mascot.tsx`): "bé Khéo"
(kênh mẹo, tròn, mầm lá, khăn màu kênh) và robot "Bit" (kênh AI, mặt màn hình, miệng cột sóng âm). Hiện ở câu hook +
câu chốt, góc dưới-phải vùng hình (trên phụ đề, trong lề UI phải); miệng mở theo RMS giọng mỗi frame do Python tính sẵn
vào `style.mascot` (giữ ranh giới video-spec.json), chớp mắt, nhún đầu. Vì sao trước: giống hệt mọi video, không chờ
Kaggle, không rủi ro detector mặt hỏng trên hoạt hình. **Sau:** probe EchoMimicV3-Flash trên Kaggle với ảnh nhân vật
(ngưỡng viết trước: < 3 phút Kaggle / giây video, VRAM đỉnh < 15 GB, khớp miệng tiếng Việt nghe bằng tai).

### Cập nhật 2026-10-05 (chiều) — nhân vật có mặt suốt video

Tony: *"nâng cấp pipeline để nhân vật hoạt hình xuất hiện nhiều hơn"*. Bản đầu chỉ hiện ở hook + câu chốt (~10% thời
lượng), bản 2 thêm câu "nhịp" (~27%). Bản 3: **có mặt 100% thời lượng**, đổi cỡ theo loại shot (Python chọn `mode`
mỗi cửa sổ, `spec/build.py: _mascot`):

| mode | khi nào | cỡ · chỗ |
|---|---|---|
| `big` | câu hook, nếu khung đầu là cảnh quay/ảnh | 560px, giữa, như người dẫn chuyện của kênh nhân vật top |
| `dock` | cảnh quay / ảnh | 360px, góc dưới-phải trên phụ đề |
| `peek` | thẻ số liệu / trang chụp | 190px, ló ở góc thẻ, mắt nhìn về thẻ, tay chỉ — không che nội dung |

Đổi cỡ trượt mượt (spring) giữa hai cửa sổ liền nhau, không bật/tắt. Thêm tay: đung đưa theo năng lượng giọng, vẫy ở
`big`, chỉ ở `peek`. Rủi ro đã thấy khi xem trước: `dock` có thể đè chủ thể ảnh; `peek` đè góc thẻ chụp trang —
theo dõi qua QC T2 (VLM) và Tony duyệt.

### Cập nhật 2026-10-05 (chiều, 2) — hành động + nhảy theo nhịp đọc

Tony: *"cho nhân vật có các hành động khác nhau, nhảy nhảy các chỗ trong khung hình"* · *"nhảy theo từng nhịp đọc hay di
chuyển gì đó cho sinh động"*. Paper-scout (2026-10-05):
- Remotion chỉ render tất định khi mọi chuyển động suy từ `useCurrentFrame()` (V, docs "Flickering"); Rive trong Remotion
  chỉ phát animation tuyến tính, **không state machine** (V, issue #5147); Lottie cần gói không dùng expression và không
  đổi được nhân vật của mình → giữ **SVG vẽ bằng code**, mỗi hành động là hàm thuần (frame → góc khớp/độ lệch).
- Nghiên cứu học tập có theo dõi mắt (R — paywall): cử chỉ **chỉ đúng vào thứ đang nói** tăng nhìn vào nội dung + nhớ
  (meta-analysis 83 bài, Mayer et al. 2024: g = 0,28 nhớ, 0,31 vận dụng); nhân vật động/ người dẫn làm chậm nhìn vào nội
  dung mới hiện (Learning & Instruction 2024). → chỉ tay khi có số/thẻ; ở thẻ số liệu nhân vật nhỏ + nảy nửa biên độ.
- Nhân vật thương hiệu trong quảng cáo TikTok: +57% (System1×TikTok 2025, n = 92k, chỉ số không rõ — R, quảng cáo, không
  phải giữ chân video tự nhiên). **Không có** số liệu nhân vật ↔ giữ chân cho video ngắn tự nhiên.

**Làm:** 8 hành động (vẫy · nhảy có lấy đà/co dãn/nảy · chỉ · gật · lắc · ngạc nhiên "!" · suy nghĩ "?" · ăn mừng lấp
lánh), chọn bằng luật theo nghĩa câu (`spec/build.py: _mascot_actions`), chống lặp (không 2 câu liền cùng hành động,
hành động lớn cách ≥ 6s); đổi góc trái/phải bằng cú nhảy vòng cung ở mỗi shot cảnh quay/ảnh và ở hành động "nhảy";
**nảy theo nhịp đọc** — mốc đầu từ trong phụ đề, cách ≥ 0,35s, từ nhấn nảy cao hơn; lắc lư nhẹ về phía giữa khung.
Xem trước: `out/thu-nhan-vat/robot-hanh-dong.mp4` (spec video Muse + robot Bit).
Luật ảnh AI ở bố cục headline đổi "nền tối" → "nền có chi tiết phủ kín khung": nền đen trơn tràn màn hình = dải đen phẳng
ở mép (T1 bắt trên bản xem trước).
