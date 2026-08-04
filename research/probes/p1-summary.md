# P1 — tổng kết bốn probe giết-hoặc-sống

**Ngày: 2026-08-04** · Máy: tony (RTX 2060 6GB, 12 core, RAM 31GB)

| Probe | Ngưỡng viết trước | Đo được | Kết quả |
|---|---|---|---|
| **S1** TikTok draft | video vào hộp draft | *code xong, chờ Tony làm phần tay* | ⏳ **chưa xong** |
| **S2** VieNeu-TTS | wav + timestamp từ, VRAM < 3GB | wav 48kHz + 15 mốc word-level, **VRAM 1,89GB** | ✅ **PASS** |
| **S3** Remotion | 60s < 15 phút, VRAM = 0 | **37,0 giây**, VRAM **+2 MiB** | ✅ **PASS** |
| **S4** LTX-Video 2B | i2v 5s @512p < 5 phút, không OOM | **OOM cả 4 cấu hình** | ❌ **FAIL** |
| **S5** Audit repo | 4 card có verdict + exit plan | 4 card xong | ✅ **xong** |

---

## Tiêu chí dừng — đánh giá

`research/05-decision.md` đặt: **"Sau P1 · ≥ 2/4 probe fail · Xem lại kiến trúc trước khi
viết tiếp code."**

Hiện tại: **1 fail chắc chắn** (S4), **2 pass** (S2, S3), **1 chưa biết** (S1).

→ **Chưa chạm tiêu chí dừng.** Được viết tiếp P2.

⚠️ **Nhưng nếu S1 cũng fail thì thành 2/4 và tiêu chí dừng KÍCH HOẠT.** Tony chạy S1
xong phải kiểm lại điều này — đừng bỏ qua vì hai probe kia đã pass.

Ghi chú công bằng: S1 fail sẽ **không** nghiêm trọng như S4, vì mục "Nếu fail" của nó chỉ
chuyển publisher sang lưu local + báo Telegram, không đụng kiến trúc. Nhưng tiêu chí dừng
được viết **trước**, nên phải áp dụng như đã viết, không được diễn giải lại cho nhẹ đi.

---

## Ba điều P1 đổi trong kiến trúc

### 1. Không sinh video local nữa (S4)

Trọng số LTX-2B là **6,34 GB**, lớn hơn cả VRAM của card (5,60 GB PyTorch dùng được).
OOM ngay ở khâu `.to(device)`, kể cả với 256×256/25 frame. Giảm khối lượng công việc
hơn 20 lần mà VRAM đỉnh chỉ đổi **7 MiB** — nút thắt là trọng số, không phải độ phân giải.

Đã cập nhật `05-decision.md`. `configs/models.yaml` vốn đã `video.enabled: false` nên
không phải đổi gì.

**Không giết dự án** — và S3 cho thấy vì sao: render chỉ chiếm 1,5% ngân sách wall_time,
còn rất nhiều dư địa cho chuyển động do code sinh.

### 2. Timestamp phải align riêng (S2)

VieNeu **không** trả timestamp — kiểm bằng `inspect.signature`, không phải bằng README.
Phương án dự phòng đã chốt sẵn hoạt động, nhưng có hai chi tiết khác dự đoán:

- Nó là **`Qwen3-ForcedAligner-0.6B`** — model **riêng**, không phải Qwen3-ASR
- Repo `voice` **chưa có code aligner nào** — chỉ nhắc tới trong research
- Tiếng Việt **không nằm trong `support_languages`** chính thức, nhưng đo thật thì align
  đúng từng từ có dấu → dùng được, nhưng là **rủi ro mở**

Đo được `even_split` lệch tối đa **458ms** so ngưỡng 120ms → đường lùi không dùng được.

### 3. Remotion nhanh hơn nhiều so với lo ngại (S3)

37 giây cho 60s video 1080×1920. Ngưỡng là 15 phút → **dưới ngưỡng 24 lần**.
`tris` giữ nguyên trạng thái tắt.

Phát hiện phụ: concurrency mặc định là **6x** chứ không phải 12, nhưng nâng lên 12 chỉ
nhanh hơn 8,4% và CPU chỉ đạt 188% trên 1200% khả dụng → **nút thắt không phải số core**.
Đừng phí công tinh chỉnh chỗ này ở P2.

---

## Việc còn lại cho Tony — theo thứ tự ưu tiên

1. **Chạy P1.S1** — checklist từng bước ở `research/probes/p1s1-tiktok.md`.
   Câu hỏi cần đóng: có bắt buộc Business account không.
2. **Nghe `out/p1s2/probe.wav`** — round-trip ASR cho `card`→"cat", `model`→"modo".
   Chưa phân định được lỗi ở TTS hay ASR. Nội dung về AI đầy thuật ngữ tiếng Anh nên
   nếu TTS đọc sai thật thì **mọi video đều dính**. Chỉ tai người trả lời được.
3. **Quyết `configs/machines.yaml`** — `gpu_exclusive_stages` đang liệt `tts`, nhưng đo
   thật cho thấy TTS chạy CPU/ONNX (VRAM ≈ 0) còn **aligner** mới là khâu chiếm 1,89GB.
   Tôi không sửa file dùng chung.
4. **Quyết `.gitignore`** — đang ignore cả `exp/*`, nên toàn bộ script probe
   (`exp/probes/tiktok_draft.py`, `exp/tts/serve.py`, `exp/tts/align_cli.py`,
   `exp/ltx/probe_*.sh`) **không vào git**. Muốn giữ thì thêm ngoại lệ.
5. **Dọn đĩa nếu cần** — `~/.cache/huggingface/hub` đang **31GB** (phần lớn là checkpoint
   LTX đã bị loại) và `exp/ltx/` 5,5GB. Đĩa còn 567GB nên không gấp.

---

## Bài học về đo đạc — ghi để không lặp lại

Hai lần đo đầu của S3 **bị hỏng và phải bỏ**: một tiến trình bench cũ vẫn sống và chạy
chồng với tiến trình mới, làm wall tăng từ 37s lên **55,9s** (+51%).

Thứ lộ ra vấn đề **không phải** con số cao — số cao mà nhất quán rất dễ bị nhận nhầm là
số thật. Thứ lộ ra là **CPU% giảm** (153% → 128%): wall tăng mà CPU% giảm thì gần như
chắc chắn có kẻ khác đang tranh máy.

Đã chặn hẳn bằng lock file + vòng chờ load < 2,0 trong `exp/probes/p1s3_render_bench.sh`.
**Kiểm `ps` trước khi tin bất kỳ số nào.**
