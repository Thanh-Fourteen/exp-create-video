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
