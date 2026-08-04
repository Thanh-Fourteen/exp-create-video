# P1.S3 — Remotion render trên tony

**Ngày đo: 2026-08-04** · **Kết quả: ✅ PASS** — pass với biên rất rộng (24× dưới ngưỡng)

| | |
|---|---|
| Tiêu chí | render 60s 1080×1920 **< 15 phút**, **VRAM = 0** |
| Đo được | **37,0s** (mặc định) · **33,9s** (`--concurrency=12`) · **VRAM +2 MiB** |
| Kết luận | **Không bật `tris`.** `configs/machines.yaml` giữ nguyên `tris.enabled: false` |

---

## Cấu hình đo

| | |
|---|---|
| Máy | tony — RTX 2060 6GB, 12 core, RAM 31GB |
| Remotion | **4.0.505** (`npx remotion versions`) · Node **v25.8.2** |
| Cài đặt | `npm install` — 250 package, **17 giây**, 0 vulnerability |
| Composition | `remotion/src/ProbeVideo.tsx` — 1800 frame @30fps = 60,0s, 1080×1920 |
| Nội dung | ảnh Ken Burns (scale+translate mỗi frame) + phụ đề karaoke 15 từ + hook 3s |
| Đo bằng | `/usr/bin/time -v` (RAM đỉnh) · `date +%s.%N` (wall) · `nvidia-smi` 0,5s/mẫu (VRAM) |
| Script | `exp/probes/p1s3_render_bench.sh` · `exp/probes/p1s3_vram_watch.sh` |

Composition cố ý làm **gần giống tải thật** (ba khối nặng nhất của video thật), không phải
nền màu trơn — probe nhẹ hơn thực tế thì số đo vô nghĩa.

## Số đo — bỏ lần đầu, lấy lần 2 và 3

Load lúc bắt đầu: **1,88** (script tự chờ load < 2,0 trước khi đo).

| Lần | Concurrency | Wall (s) | RAM đỉnh (KB) | CPU% | User (s) | Sys (s) |
|---|---|---|---|---|---|---|
| warmup — **bỏ** | 6x | 37,09 | 806.268 | 162% | 57,84 | 2,28 |
| default-2 | 6x | **37,46** | 800.116 | 162% | 58,39 | 2,36 |
| default-3 | 6x | **36,55** | 799.952 | 163% | 57,47 | 2,27 |
| conc12-2 | 12x | **33,82** | 813.504 | 188% | 61,35 | 2,46 |
| conc12-3 | 12x | **34,00** | 807.104 | 187% | 61,20 | 2,51 |

**Trung bình mặc định: 37,0s** · **`--concurrency=12`: 33,9s**

Warmup chỉ chậm hơn 1% — vì Chrome Headless Shell và bundle đã có cache từ lần chạy hỏng
trước đó. Vẫn bỏ theo đúng kỷ luật.

### VRAM

```
VRAM nền trước render : 1146 MiB   (Xorg + VS Code + Firefox của desktop)
VRAM đỉnh khi render  : 1148 MiB   (71 mẫu, 0,5s/mẫu)
TĂNG do render        :    2 MiB
```

**2 MiB nằm trong biên nhiễu của desktop.** Xác nhận **VRAM = 0** — đúng như lý do đã chọn
Remotion ở `research/05-decision.md`. Chuyển "render bằng headless Chrome nên không tranh
VRAM" từ *reported* thành **verified**.

## Ba phát hiện đáng lưu

### 1. Concurrency mặc định là **6x**, không phải 12 — nhưng nâng lên gần như vô ích

Đúng cái bẫy step cảnh báo. Nhưng số đo cho thấy nâng lên **không đáng**:

- `--concurrency=12` nhanh hơn **8,4%** (37,0s → 33,9s)
- CPU% chỉ lên 162% → 188%, tức **~1,9 core trên 12**
- User time **tăng** (57,9s → 61,3s) — thêm overhead điều phối

→ **Nút thắt không phải số core.** Nếu nút thắt là core thì CPU% phải tiến tới 1200%.
Nó nằm ở chuỗi tuần tự: Chrome vẽ frame → chụp JPEG → đẩy vào ffmpeg encode.

**Hệ quả cho P2.S2:** đừng phí công tinh chỉnh concurrency. Nếu sau này render chậm đi
thì tìm nguyên nhân ở độ phức tạp composition, không ở số worker.

### 2. Remotion tự thêm **audio track AAC** dù composition không có audio

```
codec_name=h264 / codec_name=aac / duration=60.053333 / 1080x1920 / 30fps
```

**Quan trọng cho P2.S3 (QC tầng 1).** `configs/thresholds.yaml` có
`audio.max_silence_sec: 2.0`. Video không có giọng đọc vẫn **có** audio track — im lặng
hoàn toàn. T1 sẽ báo fail đúng, nhưng khi debug rất dễ tưởng lỗi TTS. Phân biệt sẵn hai ca:
*không có audio stream* ≠ *có audio stream nhưng im lặng*.

### 3. `pix_fmt` ra **`yuvj420p`**, không phải `yuv420p` như đặt trong config

`remotion.config.ts` đặt `setPixelFormat("yuv420p")` nhưng output là `yuvj420p` (JPEG full
range), do `setVideoImageFormat("jpeg")`. Chưa rõ TikTok có kén không.
**Việc cho P2.S3:** nếu T1 kiểm pix_fmt thì kiểm cả hai giá trị, hoặc đổi sang PNG
intermediate và đo lại tốc độ (PNG chậm hơn — phải đo, đừng đoán).

## Ngoại suy — có căn cứ, nhưng vẫn là ngoại suy

`configs/thresholds.yaml` đặt `operational.max_wall_time_min: 40` cho **toàn** pipeline.
Render chiếm **37 giây** của ngân sách đó, tức **1,5%**. Nút thắt wall_time nằm ở khối
sinh ảnh (SDXL ~10s/ảnh, Flux ~2 phút/ảnh — *reported*), không ở render.

⚠️ Con số 37s đo trên **một** composition. Video thật sẽ có 8 shot, nhiều transition, ảnh
thật nặng hơn. Đừng coi 37s là hằng số. Nhưng biên 24× rất rộng — kể cả chậm hơn 10 lần
vẫn dưới ngưỡng.

## Nợ kỹ thuật ghi lại

1. **Font `Be Vietnam Pro` chưa cài trên tony.** `configs/style.yaml` yêu cầu nó
   ("font Việt, có đủ dấu — KHÔNG dùng Inter/Roboto"). Probe dùng `sans-serif` hệ thống.
   Chữ tiếng Việt có dấu hiện đúng, nhưng **không phải font đã chốt**. P2.S2 phải nhúng
   font qua `@remotion/google-fonts` hoặc tự host — **đừng dựa vào font hệ thống**, vì
   render sẽ khác máy khác kết quả.
2. **Ảnh probe là gradient sinh bằng ffmpeg**, không phải ảnh thật từ SDXL. Ảnh thật nặng
   hơn khi decode → thời gian render sẽ tăng. Đo lại ở P2.S2 với asset thật.
3. `.gitignore` ignore **cả `exp/*`** → hai script probe không vào git. Tony tự quyết có
   thêm ngoại lệ `!exp/probes/` không.

## Lỗi đo đã mắc và đã sửa — ghi lại để không lặp

Hai lần đo đầu **bị hỏng**, số phải bỏ:

1. Chạy `nohup ... &` **kèm** background của harness → tiến trình `npx` bị giết giữa chừng
   (frame 518/1800) nhưng **bash cha vẫn sống và chạy tiếp** các lần sau.
2. Rồi chạy lại → **hai script bench chạy chồng nhau**, tranh CPU. Bằng chứng:
   CPU% tụt 153% → 128%, wall vọt lên **55,9s** thay vì 37s (**+51%**).

Đã sửa trong `p1s3_render_bench.sh`: **lock file** (`mkdir` atomic) chặn chạy chồng, và
**vòng chờ load < 2,0** trước khi đo.

**Bài học:** số đo cao bất thường mà lại *nhất quán* rất dễ bị nhận nhầm là số thật.
Thứ lộ ra vấn đề là **CPU% giảm** — wall tăng mà CPU% giảm thì gần như chắc chắn có kẻ
khác đang tranh máy. Kiểm `ps` trước khi tin bất kỳ số nào.
