# Kaggle / Lightning AI (GPU miễn phí) và Pexels / Unsplash (stock) — có làm video hay hơn không — 2026-10-05

**Tony (2026-10-05):** *"research thử nếu tôi có api của kaggle, api của lightning thì có gen được video, hình ảnh, nhân vật
cho video không? nếu tôi có api của pexel và unsplash thì video hay hơn không?"*

2 paper-scout + đọc nguyên văn điều khoản Kaggle bằng trình duyệt tự động (trang render JS). **V** verified · **R** reported
· **A** assumed. Bản lưu điều khoản: `out/tham-khao/kaggle-terms.txt`, `kaggle-aup.txt`.

## 1. Kaggle — kỹ thuật làm được, **điều khoản cấm dùng cho kênh kiếm tiền**

| | |
|---|---|
| GPU | 2×T4 16GB, ~30 giờ/tuần, phiên 9–12 giờ (R — trang quota render JS) |
| Điều khiển từ xa | `kaggle kernels push --accelerator NvidiaTeslaT4` → `kernels status` → `kernels output` (V, docs CLI 2026-09) |
| Tạo được gì trên T4 | ảnh Z-Image 18s/ảnh 768² (fp16 vẫn đen — T4 cùng đời Turing với 2060; V) · clip Wan2.2-TI2V-5B 5s 480p ~8 phút (R) · nhân vật biết nói: EchoMimicV3-Flash (Apache, ≥12GB, V), MuseTalk 1.5 (weights cho thương mại, V), InfiniteTalk (Apache, chế độ low-VRAM, V) — chưa ai đo trên T4 |
| Ước tính | ~1,5–2 giờ GPU/video có b-roll động + nhân vật → ~15–20 video/tuần trong 30 giờ (A) |
| **Điều khoản** | *"You will only use the Services for your own internal, personal, **non-commercial** use"* (kaggle.com/terms, V 2026-10-05). AUP cấm "abuse resources… server farming" (V) |

→ Dùng Kaggle làm máy sinh nội dung cho kênh TikTok **có kiếm tiền** (affiliate, LIVE, quảng cáo) là **vi phạm điều khoản**;
hậu quả là mất tài khoản. **Không tích hợp.**

## 2. Lightning AI — hết miễn phí bền vững

- Đợt đổi giá 2026-09-21: bỏ credit miễn phí hằng tháng → cấp một lần (5 credit, +25 nếu gắn thẻ, hết hạn 12 tháng); T4
  $0.19 → $0.55/giờ (R, usagepricing). 5 credit ≈ 9 giờ T4 — đủ thử, không đủ chạy.
- ToS: chỉ "internal business purposes"; "commercial activities… advertising" cần đồng ý bằng văn bản (V).
- SDK điều khiển từ xa đầy đủ (`Studio.start(Machine.T4)`, `Job.run`) (V) — nhưng trái "chi phí 0đ" + ToS. **Không tích hợp.**

## 3. Pexels / Unsplash / Pixabay

| | Pexels | Unsplash | Pixabay |
|---|---|---|---|
| Lấy key | **Đang dừng cấp key mới** (V 2026-10-05; một dự án khác 2026-10-02 không kích hoạt được key) | key demo 50 req/giờ, production cần duyệt (V) | key miễn phí, ~6.000 req/giờ (V) |
| Video | có, lọc dọc (V) | **không, chỉ ảnh** (V) | có, không lọc dọc — lọc bằng kích thước (V) |
| Điều khoản API | xin link + ghi công (V) | **bắt hotlink ảnh**, gọi endpoint download, ghi công, "non-automated experience" — không hợp video đã render (V) | cache 24h, không hotlink vĩnh viễn (V) |
| Thương mại | được; cấm đặt người nhận diện được vào hình ảnh xấu, cấm ngụ ý thương hiệu (V) | được (V) | được; cấm thương hiệu, người trong ngữ cảnh xấu (V) |
| Cảnh Việt Nam | "vietnam" 7,9K video, đa số ngang (V) | "vietnamese food" 3,1K ảnh (V) | "vietnam" 918+, chủ yếu du lịch (V) |

**Có làm video hay hơn không:** không có nghiên cứu so stock với ảnh AI trong video ngắn (chỉ số vendor, R). Bằng chứng gián
tiếp: Getty 2024 (n > 30.000) — ảnh AI về **người/sản phẩm** bị thấy là đánh lừa hơn; tài chính/sức khoẻ bị đòi hỏi chặt
hơn (V). Khảo sát của mình (research/15): kênh mẹo top dùng cảnh thật quay tay hoặc nhân vật AI rõ ràng là hoạt hình — không
dùng ảnh "giả như thật" về người.

→ **Có lợi cho kênh Sống Khéo** ở đúng loại cảnh mà ảnh AI dễ trông giả: thực phẩm, chợ, bếp, tay cầm điện thoại/ATM, thời
tiết, nhà cửa. Kênh AI lợi ít (hình chính là ảnh chụp trang + thẻ). Stock chỉ làm b-roll dưới giọng/phụ đề/thẻ riêng — cả
video bằng stock thì dính luật "không nguyên bản" (R).

## 4. Quyết định

| | Quyết định | Vì sao |
|---|---|---|
| Kaggle | **Không** | điều khoản: non-commercial (V) |
| Lightning AI | **Không** | hết free tháng; ToS cần đồng ý cho quảng cáo |
| Pexels | Chờ — mở lại khi Pexels cấp key | đang dừng cấp |
| Unsplash | **Không** | chỉ ảnh, bắt hotlink, không hợp video |
| **Pixabay** | **Có, cho kênh mẹo** — khối visual `stock`: tìm theo prompt shot, lọc clip dọc ≥ 1080 cao, ≤ 2 clip/video, ghi nguồn vào caption; probe 20 mô tả shot thật trước khi bật | key miễn phí, thương mại được, có video |
| Nhân vật AI biết nói | Chưa — không có GPU hợp lệ đủ mạnh. Mở lại nếu có GPU ≥ 12GB tự sở hữu hoặc thuê | MuseTalk/EchoMimicV3 cần ≥ 12GB |

## 5. Cập nhật 2026-10-05 — Tony: kênh **cá nhân, không kiếm tiền** → dùng Kaggle

Tony: *"Dùng kaggle up video tiktok cá nhân, chứ đâu có làm thương mại."* Với mục đích cá nhân, phi thương mại, điều khoản
Kaggle ("internal, personal, non-commercial use", V) cho phép → **dùng Kaggle làm GPU ngoài** cho việc máy 6GB không làm
nổi (clip động image-to-video, nhân vật AI biết nói).

Điều kiện giữ đúng điều khoản (ghi vào code + docs):
1. MỘT tài khoản Kaggle của Tony, trong hạn mức GPU miễn phí (~30 giờ/tuần), không lách giới hạn, không nhiều tài khoản.
2. **Kênh bắt đầu kiếm tiền** (affiliate, quà LIVE, Creator Rewards, quảng cáo) → **ngừng Kaggle**, chuyển GPU thuê.
3. Model vẫn chọn license cho phép thương mại (Apache/MIT) — để lúc chuyển sang kiếm tiền không phải làm lại.
Lightning AI: vẫn không dùng (hết free hằng tháng).
