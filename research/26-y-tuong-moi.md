# Ý tưởng mới cho 2 kênh — 2026-10-10

Tony 2026-10-10: *"ý tưởng của 2 kênh quá dở. xóa hết ý tưởng đi tạo lại ý tưởng mới cho 2 kênh. ý tưởng mới, kênh mẹo thì
phải có các mẹo hay. research trước rồi làm"*. **V** verified · **R** reported · **A** assumed.

## 1. Vì sao ý tưởng cũ dở (đọc code, V)

- Kênh mẹo: prompt `idea_gen` CẤM đúng dạng mẹo hay — "KHÔNG: lau chùi trước/sau, DIY, làm đẹp, kỹ thuật nấu" (luật thời
  chưa có cảnh quay thật, 2026-10-04); pillar bếp ghi "dạng BIẾT/TRÁNH, KHÔNG dạy kỹ thuật nấu". Kết quả: kho toàn cảnh báo,
  tin tức, "vì sao/sự thật" — không có việc gì để làm theo.
- Kênh AI: gợi ý trang Tạo video lấy từ `trend_scout` (Hugging Face, arXiv, GitHub) → "Laya model…", "EmbeddingGemma…" —
  model/benchmark cho dân kỹ thuật, không phải khán giả phổ thông của kênh.

## 2. Thứ gì bùng nổ ở kênh Việt cùng ngách (V, yt-dlp 2026-10-09, 60 video gần nhất/kênh, × = lần trung vị kênh)

**Mẹo/đời sống:** "Mẹo rán cá, luộc ốc, xào mực" ×47 (4,4M) · loạt "mẹo hay đời sống/mỗi ngày" ×17–654 (1,1–2,9M) ·
"Đừng uống nước dừa nếu chưa biết 3 tuyệt chiêu…" ×29 · "Tất cả những ai dùng Zalo phải xem…" ×14 (1,3M) · VNeID ×10–13 ·
"Bị đánh, đánh lại có phạm tội không?" ×9 · "lãi suất thả nổi xe trả góp lên 18%" ×32 · "sự thật tâm lý học về người ít nói" ×26.
→ mẹo bếp/nhà cửa LÀM NGAY, app đời thường, pháp luật đời thường, tiền tính cụ thể.

**AI:** "Các lệnh ngắn cực chất lượng trên ChatGPT ít người biết" ×87 (1,3M) · Google Form tạo đề trắc nghiệm ×32 · viết sáng
kiến kinh nghiệm bằng AI ×29 · CapCut AI video quảng cáo ×20 · "trang web bổ ích nên biết" ×12–18 · làm video AI đang trend
×13–17 · tin cáp biển (ảnh hưởng thẳng người Việt) ×116 · "98,5% token…" ×52. Ra mắt model/benchmark gần như không có trong top.
→ DÙNG AI LÀM MỘT VIỆC CỤ THỂ, miễn phí; tin chỉ khi đổi được việc người Việt làm.

Giới hạn: 12 kênh, 60 video/kênh, quan sát (không biết vì sao từng video bùng nổ); dạng "mẹo bếp" bùng nổ một phần nhờ
cảnh quay tay thật — kênh mình dùng cảnh quay kho (Pexels) + thẻ, có thể kém hơn (A).

## 3. Quyết định

- Kênh mẹo: `prompts.idea_search/idea_scope` mới (mỗi ý = MỘT mẹo làm được ngay, tiêu đề nói luôn mẹo; cấm chữa bệnh/
  "thần dược", trộn hoá chất, làm đẹp, mẹo nguy hiểm); pillar lại: Mẹo bếp 0,30 · Nhà cửa 0,20 · Điện thoại 0,20 · Tiền bạc
  0,15 · Pháp luật 0,10 · Giao tiếp 0,05 (giữ khoá cũ để video cũ không lệch); nguồn tier2 thêm bachhoaxanh.com,
  dienmayxanh.com, cooky.vn, thegioididong.com CHỈ cho mẹo bếp/nhà cửa — claim sức khoẻ/an toàn thực phẩm vẫn bắt tier1 (T4).
- Kênh AI: `idea_search/idea_scope` mới (dùng AI làm việc cụ thể: văn phòng, học sinh–giáo viên, bán hàng online, video
  AI, web/app hay; cấm model/benchmark/paper/repo); `trend.scout: idea_scout` → gợi ý trang Tạo video lấy từ kho.
- Xoá kho cũ: mọi ý tưởng CHƯA dùng của 2 kênh (máy sinh + seed `ideas.yaml` + ý theo mùa) → bỏ; giữ ý đã dùng (lịch sử).
  Sinh lại 20 ý tưởng/kênh bằng `idea_gen` (1 lần gọi Claude + WebSearch mỗi kênh).
- Kiểm thật: tỉ lệ Tony bấm tạo video từ gợi ý mới + `approve_rate` các video từ ý tưởng mới.
