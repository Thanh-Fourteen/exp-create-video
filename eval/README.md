# Bộ đối chứng

Ba spec **cố định**. Mỗi lần đổi khối render (Remotion → Revideo, đổi component,
đổi style) phải render lại đúng ba cái này và so trước/sau. Không có mốc cố định thì
"cải tiến" chỉ là cảm giác.

| Fixture | Kiểm điều gì |
|---|---|
| `01-baseline/` | ca bình thường: 8 câu, 5 shot, ảnh sinh, karaoke |
| `02-long-caption/` | câu dài nhất còn chấp nhận được — kiểm tràn vùng an toàn |
| `03-many-shots/` | nhiều shot ngắn — kiểm transition và nhịp cắt |

Mỗi thư mục **tự chứa**: `video-spec.json` + `voice.wav` + `img/`. Render bằng

    bash scripts/render.sh eval/scripts/01-baseline/video-spec.json /tmp/eval-01.mp4

Kết quả ghi vào `eval/results/<YYYY-MM-DD>-<tên>.md`, **không ghi đè** file cũ, và
kèm cả output thô (mp4 + JSON của T1), không chỉ số tổng hợp.

⚠️ **Không sửa spec trong này để "cho nó pass".** Sửa fixture sau khi nhìn kết quả
thì nó thôi là mốc đo — cùng một lý do với việc không sửa ngưỡng sau khi chạy.
