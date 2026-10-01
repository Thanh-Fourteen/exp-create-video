# P3.S4 — Một lệnh đầu-cuối: chủ đề → mp4

**Ngày: 2026-08-14** · **Kết quả: ✅ chạy trọn, T1 đạt 10/10**

Lệnh:

```bash
.venv/bin/python -m create_video.pipeline \
  "Vì sao model AI open-source chạy được trên card đồ hoạ cũ" --id demo-01 --duration 40
```

Kết quả: `out/demo-01/video.mp4` — 51,69s · 1080×1920 · 47,9 MB · 9 shot · 16 caption.

## Ngân sách wall_time — 6,9 phút / 40 phút (17%)

| Bước | Thời gian | Chiếm |
|---|---:|---:|
| Kịch bản (claude-agent-sdk) | 67,8s | 16% |
| TTS + forced align | 85,8s | 21% |
| Sinh 9 ảnh (SDXL-Lightning) | 173,5s | 42% |
| Dựng spec | 0,2s | 0% |
| Render (Remotion) | 77,2s | 19% |
| QC tầng 1 | 10,7s | 3% |
| **Tổng** | **415s** | |

Nút thắt là **sinh ảnh**, không phải render — ngược hẳn với lo ngại lúc lập kế hoạch,
và khớp với P1.S3 (render rẻ). Trong 173,5s đó, ~100s là nạp model một lần; 9 ảnh chỉ
tốn ~70s. Muốn nhanh hơn thì gộp nhiều video vào một lần nạp, đừng tối ưu từng ảnh.

## QC tầng 1: 10/10

Đáng chú ý: `vùng an toàn (pixel)` đo được **0,22%** trên ngưỡng 0,4% — tức là có
tín hiệu "giống chữ" trong dải bị UI che nhưng chưa tới ngưỡng. Với video nền tối
và phụ đề đặt đúng chỗ thì con số này là nhiễu từ chính ảnh nền. Cần theo dõi qua
20 video: nếu nó thường xuyên bò lên gần 0,4% thì ngưỡng đang quá sát và phải xem
lại **bằng cách ghi lý do vào research/**, không sửa lặng lẽ.

## Ba lỗi đã gặp và đã sửa

1. **`max_turns=1` của claude-agent-sdk** ném `Reached maximum number of turns (1)`
   ngay cả khi agent trả lời xong đúng ý. Chặn vòng lặp bằng `allowed_tools=[]`,
   để `max_turns` làm lưới an toàn ở mức 4.
2. **Cấm chữ số quá tay.** Ràng buộc "viết số bằng chữ" ban đầu bắt luôn cả
   `Qwen2.5-Coder` → agent phải viết lại và vẫn fail. Nay chỉ cấm **số đứng một
   mình**; số trong tên riêng thì tha. Bắt oan tốn nguyên một vòng LLM (~1-5 phút),
   tha nhầm chỉ làm một câu phụ đề rơi về đường `redistributed`.
3. **Caption chồng nhau.** Aligner kéo từ cuối câu lấn sang khoảng lặng trước câu
   sau; validator bắt được ngay lần chạy đầu. Cắt tại điểm giữa hai câu.

## Điều pipeline CHƯA làm

- **Chưa kiểm sự thật.** `sources` do chính agent khai, chưa ai đối chiếu — đó là
  T4 (P4.S3). Kịch bản demo-01 nói về quantization và MoE nghe hợp lý, nhưng
  "nghe hợp lý" không phải là đã kiểm.
- **Chưa có T2/T3**, nên chưa có vòng sửa nào. `qc_rounds` hiện luôn bằng 0.
- **Chưa có nhạc nền** — `audio.music` để trống (nợ kỹ thuật, chưa quyết).
- **Chưa gửi duyệt, chưa đăng.** P5.
