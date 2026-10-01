# Đổi nhịp dựng và font phụ đề

**Ngày: 2026-08-14** · Người quyết: Tony · Trạng thái: đã áp dụng

Sau khi xem video đầu tiên (`out/demo-01`), Tony yêu cầu ba thứ: **font đẹp hơn**,
**nhịp nhanh hơn, hấp dẫn hơn**, **giọng nam**. Ghi lại ở đây vì cả ba đều đổi
`configs/*.yaml` — mà config đổi lặng lẽ thì sáu tuần sau không ai biết vì sao.

## Font: Be Vietnam Pro → Anton

Đã dựng bảng so 5 font (`out/font-compare.png`), tất cả render bằng chính file TTF
với đúng cỡ chữ và viền của phụ đề thật.

| Font | Nhận xét | Có subset vietnamese |
|---|---|---|
| Be Vietnam Pro ExtraBold | cũ; đều, hiền, không "đập" | ✅ |
| **Anton** ✅ chọn | nặng nhất, condensed nhất | ✅ |
| Oswald Bold | condensed, sạch hơn, nhẹ hơn | ✅ |
| Montserrat Black | rất đậm nhưng **rộng ngang** → tràn dòng | ✅ |
| Lexend ExtraBold | rộng ngang, hiền | ✅ |
| ~~Bebas Neue~~, ~~Archivo Black~~ | **loại** | ❌ không có |

Chọn Anton không chỉ vì thẩm mỹ: nó **condensed**, nên cùng cỡ chữ thì chứa nhiều
ký tự hơn trên một dòng. Ít xuống dòng hơn nghĩa là ít nguy cơ chữ thò vào vùng UI
TikTok che — đúng cái mà fixture `02-long-caption` đang fail.

⚠️ Anton chỉ có **một weight (400)**. Nó vốn đã rất nặng nên không cần 800, nhưng
đừng đặt weight cao trong `style.yaml` rồi tưởng chữ sẽ đậm hơn: Chrome sẽ *giả lập*
nét đậm và chữ bị nhoè viền.

## Nhịp: shot 3–8 giây → 2–4 giây

| Thông số | Cũ | Mới |
|---|---|---|
| `shot_duration_sec` | 3–8 | **2–4** |
| `ken_burns.zoom_range` | 1,00–1,15 | **1,00–1,22** |
| `transition.accent_every` | 3 | **2** |
| `target_duration_sec` | 45 | **35** |
| Câu lời đọc (scriptwriter) | 5–16 từ | **4–12 từ** |

Zoom phải tăng theo shot: shot ngắn hơn mà giữ nguyên biên độ zoom thì trong từng
shot gần như đứng yên — cắt nhanh nhưng vẫn tĩnh, tệ hơn cả trước.

**Cái giá, nói thẳng:** số shot mỗi video tăng gần gấp đôi, mà sinh ảnh đang là nút
thắt (42% wall_time, `research/probes/p3s4-pipeline.md`). Nhịp nhanh đắt hơn nhịp
chậm, và đắt ở đúng khâu vốn đã đắt nhất.

Vì vậy phần lớn cảm giác "nhanh" được đẩy sang chỗ **miễn phí**: `KaraokeCaption` nay
cho từ đang đọc nảy 1,2× kèm quầng sáng, tắt dần trong 4 frame. Chuyển động này chạy
liên tục suốt video và không tốn một giây GPU nào.

## Giọng: Mai Anh (nữ) → Thanh Bình (nam)

Tổng hợp cùng một câu bằng 4 giọng nam (`out/voice-compare/`), Tony nghe và chọn.

| Giọng | Tier | Thời gian đọc câu mẫu |
|---|---|---|
| **Thanh Bình** (nam, Bắc) ✅ | wide | **4,72s** |
| Thái Sơn (nam, giọng Nam) | wide | 5,60s |
| Phạm Tuyên (nam, Bắc) | mid | 4,88s |
| Minh Đức (nam, Bắc, tin tức) | mid | 6,16s |

Thanh Bình vừa ở tier chất lượng cao nhất vừa đọc nhanh nhất — hợp với yêu cầu nhịp.
Đổi giọng nay là sửa `configs/models.yaml: tts.echo.voice`, không đụng code.

## Ảnh hưởng tới bộ đối chứng

Ba fixture ở `eval/scripts/` **đóng băng style cũ trong chính spec của chúng** (Python
resolve `style.yaml` vào spec lúc dựng). Nên thay đổi config ở đây **không** làm hỏng
tính so sánh được của fixture — chúng vẫn đo đúng khối render. Chỉ thay đổi *component*
(như `KaraokeCaption` lần này) mới làm output fixture đổi, và đó chính là thứ fixture
sinh ra để bắt.

## Đo sau khi đổi — `out/demo-02`

Cùng chủ đề với `demo-01` để so được.

| | demo-01 (nữ, nhịp cũ) | demo-02 (nam, nhịp mới) |
|---|---:|---:|
| Độ dài video | 51,7s | **36,2s** |
| Số shot | 9 | **11** |
| Giây/shot trung bình | 5,7 | **3,3** |
| Số câu phụ đề | 16 | 15 |
| Từ mỗi câu (trung bình) | 9,4 | **7,5** |
| Sinh ảnh | 173,5s | 191,5s |
| Render | 77,2s | **65,4s** |
| T1 | 10/10 | **10/10** |
| Tổng | 6,9 phút | **5,9 phút** |

⚠️ 5,9 phút của demo-02 **không so thẳng được** với 6,9 phút của demo-01: lần chạy này
dùng lại `script.json` và wav đã cache nên khâu kịch bản tính 0 giây (lần đầu tốn 64,7s).
Cộng lại thì demo-02 tốn ~7 phút — tức nhịp nhanh **không** làm pipeline nhanh hơn;
video ngắn đi bù lại cho số shot nhiều hơn, gần như huề.

Vùng an toàn giờ rộng hơn hẳn nhờ Anton: câu dài nhất chỉ còn **3 dòng, đáy 1421px**
(trần 1536px), so với 4 dòng / 1465px của Be Vietnam Pro trên câu tương đương.

## Một lỗi im lặng lộ ra khi đổi nhịp

Lần chạy đầu sau khi đổi config sinh **7 ảnh cho 11 shot** — 4 shot cuối rơi về nền
phẳng, tức 12 giây cuối video không có hình. Không exception, không cảnh báo, và
**QC tầng 1 vẫn cho qua 10/10** (nền phẳng #0D0D0F chưa đủ tối để `blackdetect` bắt).

Nguyên nhân: `pipeline._estimate_shot_count` gọi hàm gom nhóm bằng tham số mặc định
(3–8 giây) trong khi `spec.build._plan_shots` đọc `configs/style.yaml` (2–4 giây). Hai
nơi cùng đếm một thứ nhưng đếm bằng hai bộ tham số.

Đã sửa: cả hai đọc chung config, thêm cảnh báo khi ảnh thiếu so với shot, và thêm test
hồi quy `tests/test_shot_count.py` — vì đây đúng là loại lỗi mà không có test thì lần
sau lặp lại y hệt.

**Điều đáng ghi hơn cả:** T1 không bắt được. Nó kiểm "có frame đen quá 0,5s không",
không kiểm "mỗi shot có hình không". Đó là một khoảng trống thật của tầng 1, và nó
thuộc về T2 (VLM chấm ảnh, P4.S1) — nhưng T2 chấm *chất lượng* ảnh, cũng chưa chắc bắt
được *thiếu* ảnh. Cần một kiểm rẻ ở T1: đếm tỉ lệ shot có `asset.kind == "color"`.
