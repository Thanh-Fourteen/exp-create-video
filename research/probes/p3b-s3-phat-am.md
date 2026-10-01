# P3b.S3 — Phát âm thuật ngữ tiếng Anh — 2026-10-01

**Câu hỏi:** Tony: "các từ tiếng Anh chưa phù hợp". Đọc thô, bọc `<en>`, hay phiên âm Việt?
**Tiêu chí viết trước** (todos.md): ≥ 25/30 Tony chấp nhận ở ít nhất một biến thể.
**Trạng thái: ⏳ phần máy đo xong; chờ Tony nghe 12 từ khó** (`out/p3b-phat-am/NGHE.md`).

## Cách đo

30 thuật ngữ trong câu mang *"Hôm nay mình thử ___ trên máy cũ."*, giọng Thanh Bình seed 7.
**Proxy:** ASR round-trip bằng Qwen3-ASR của exp-echo — ASR nghe ra đúng từ tiếng Anh
nghĩa là âm đủ giống tiếng Anh. Proxy này **không** đo được "người Việt nghe có tự
nhiên không", và ASR tiếng Việt có xu hướng nghe phiên âm Việt thành từ Việt khác
→ thiên vị chống phiên âm. Script: `exp/probes/p3b_s3_phat_am.py`, `p3b_s3_vong2.py`.
Số thô: `out/p3b-phat-am/result.json`, `vong2/result.json`; wav cạnh đó.

## Kết quả (verified)

| Biến thể | ASR nghe ra đúng |
|---|---:|
| Đọc thô (hiện tại) | **18/30** |
| `<en>…</en>` | 13/30 |
| Phiên âm Việt (vòng 1) | 8/30 |

- **`<en>` vô dụng với từ thường:** wav giống hệt **từng byte** bản thô (sea-g2p tự nhận
  từ tiếng Anh). Với chữ viết tắt thì **hại**: "API" thô → norm "a p i" → ASR "api" ✓;
  `<en>API</en>` → đọc như một từ → ASR "ip" ✗. Tương tự "AI" → "á".
- **Chữ viết tắt đọc thô đã ổn theo ASR:** GPU, GB, LLM, AI, API, OpenAI.
- **12 từ thô bị nghe sai:** prompt ("prom" — gần đúng), token, agent, weights ("quay"),
  open-weight, dataset ("đã tô xét"), code ("cốt"), Claude ("clone"), Hugging Face
  ("hacking face"), GitHub ("kít hắp"), RTX ("atx"), context ("còn tách").
- **Vòng 2** (3 phiên âm/từ cho 12 từ đó): chỉ **dataset → "đa ta sét"** được ASR nghe
  ra đúng. Context → "con tếch" cho "con tech" (gần). Còn lại ASR nghe thành từ Việt
  khác — không kết luận được, cần tai người.

## Đã áp dụng

`configs/pronounce.yaml` + `voice/echo.py: apply_pronounce` — thay nguyên từ trong
chuỗi gửi TTS, chữ trên màn hình giữ gốc. Mục khởi đầu: `dataset`, `context`. Mặc định
không thay gì (đọc thô là tốt nhất theo số đo).

## Chưa làm

- Tony nghe 12 từ khó → thêm mục vào `pronounce.yaml`.
- Hướng nếu phiên âm vẫn không ổn: chọn **cách viết kịch bản tránh từ khó** (scriptwriter
  được dặn dùng "trọng số" thay "weights", "mã" thay "code" khi tự nhiên) — đổi ở prompt,
  không ở TTS. Hoặc thử model TTS khác code-switch tốt hơn (VoxCPM2 Q8, `research/08` §3).
