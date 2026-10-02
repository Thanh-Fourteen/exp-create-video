# V6 — Chạy đầu-cuối chủ đề → mp4 — 2026-10-02

Lệnh: `pipeline "<chủ đề>" --visual flux2 --duration 45 --qc`. Giọng: Tony clone + LavaSR. Số đo **verified** (state.json).

| Video | Chủ đề (pillar) | Researcher | QC | Vòng sửa | Tổng | Can tay? |
|---|---|---|---|---|---|---|
| v1 `out/V1-notebooklm.mp4` | NotebookLM → podcast tiếng Việt (cong_cu) | 11/12 sự thật | T1 15/15 · T3 9,38 · T4 21 claim, 0 mâu thuẫn (vòng 0 bắt 1 câu sai → sửa) · T2 1 lệch prompt (warn) | 1 | ~29 phút | CÓ — sửa layout thẻ/hook frame 0, số đếm sai ở thumbnail |
| v2 `out/V2-chatbot-rieng-tu.mp4` | Không dán gì vào chatbot (canh_bao) | 12/12 | T1 pass · T2 regen 4 ảnh chữ méo → còn 1 | 2 (trần) | ~32 phút (+ nhạc seed mới 561s) | CÓ — punch-in đẩy thẻ lấn lề trái |
| v3 `out/V3-chatgpt-vs-gemini.mp4` | ChatGPT free vs Gemini free (so_sanh) | 11/11 | **PASS** cả 4 tầng + 6 proxy giữ chân | 0 | **25,5 phút** | **KHÔNG** — chủ đề trần → mp4 |

Lỗi tìm ra khi chạy thật (đã sửa, có test/kiểm tra): chữ hook đè thẻ frame 0 · gradient hook thành "viền đen" ·
thẻ lấn lề an toàn 4% (push-in, punch-in) · số đếm lên ở frame 0 hiện sai (185.020 cho 500.000) · thẻ mờ ở frame 0 ·
"tôi vào Settings" (nhận đã làm khi chưa làm) · FLUX vẽ chữ méo lên giấy/màn hình · câu dài chia 2 shot dùng chung
prompt → ảnh lặp · nhạc ACE sinh lại mỗi video (cache, 256–561s → ~3s).

Thời gian từng stage (v3): researcher 231s · kịch bản 71s · TTS+align+BWE 228s · ảnh FLUX 5 tấm 249s · nhạc (seed mới) 298s ·
render 263s · QC 169s. Với cache nhạc đầy: ước ~21 phút (assumed).

**Chưa đạt tiêu chí "2 lần liên tiếp không can tay"**: mới 1 (v3); router đổi sau v3 → cần thêm 1 lần.
