# Quyết định kiến trúc

Date: **2026-08-04** · Status: **đã grounded một phần** — P1 đã chạy, xem
`research/probes/`. Ba probe tự động hoá được đều xong (S2 pass, S3 pass, S4 **fail**);
S1 chờ Tony làm phần tay. Các số tốc độ dưới đây đã chuyển từ *reported* sang *verified*
ở những chỗ ghi rõ.

Phạm vi: luồng 1 (video tự sinh hoàn toàn). Luồng 2 (footage Tony) hoãn tới P6.

---

## Ràng buộc đã xác minh — nền của mọi lựa chọn bên dưới

| # | Ràng buộc | Bằng chứng | Confidence |
|---|---|---|---|
| 1 | `tony`: RTX 2060 **6GB** (Turing sm_75, **không FP8**), 12 core, RAM 31GB, `/mnt/data1tb` còn 605GB | `nvidia-smi`, `df -h` [2026-08-04] | **verified** |
| 2 | `tris`: 2× RTX 5090 32GB nhưng cả hai bận ~29GB → chỉ mượn được khe **< 2GB** | `ssh tris nvidia-smi` [2026-08-04] | **verified** |
| 3 | Flux.1-schnell Q4 (6,88GB GGUF) ~2 phút/ảnh trên GPU 6GB; SDXL-Turbo/Lightning nhanh hơn hẳn | localaimaster, willitrunai [2026-08] | reported |
| 4 | LTX-Video 2B **không chạy được trên 2060 6GB** — trọng số 6,34GB > 5,60GB PyTorch dùng được; OOM cả ở 256×256/25 frame; FP8 cần Ada trở lên | **tự đo, P1.S4** [2026-08-04] | **verified** |
| 5 | LTX-2 trên 5090 ra 720p/4s ~25s, nhưng cần ~20GB VRAM | nvidia.com, zenn.dev [2026-08] | reported |
| 6 | Wan2.2 14B cần **65–80GB** ở 720p — quá tầm cả 5090 | spheron, hostrunway [2026-08] | reported |
| 7 | TikTok Content Posting API: client chưa audit → **mọi bài ép `SELF_ONLY`**. Audit 2–4 tuần | developers.tiktok.com, netrows, timetopost [2026-08] | reported |
| 8 | TikTok Research API siết còn tổ chức học thuật; Creative Center **cấm scrape** trong ToS | netrows, admapix [2026-08] | reported |
| 9 | Remotion: 55.436★, license **NOASSERTION**, push 2026-08-03 | `gh api repos/remotion-dev/remotion` [2026-08-04] | **verified** |
| 10 | MoneyPrinterTurbo: 101.436★, **MIT**, push 2026-08-02 — kiến trúc pipeline đáng học | `gh api` [2026-08-04] | **verified** |
| 11 | ShortGPT: 7.757★, MIT, **push cuối 2025-02-10** (18 tháng) | `gh api` [2026-08-04] | **verified** |

**Hệ quả quan trọng nhất:** ràng buộc 2 làm con 5090 vô dụng cho khâu nút thắt — 2060
còn 6GB trống, nhiều gấp ba khe 2GB mượn được. Trần chất lượng hình do 2060 đặt ra.
Ràng buộc 4+5+6 nghĩa là **không có cấu hình nào ở đây sinh được video AI 1080×1920
chất lượng cao**. Kết luận: chất lượng phải đến từ **nhịp dựng, hook, phụ đề động và
audio**, không từ model sinh ảnh.

---

## Ma trận: khối dựng video

| | **Remotion** ✅ chọn | Revideo | Python + ffmpeg/MoviePy |
|---|---|---|---|
| Sao | 55.436 | 3.952 | — |
| License | **NOASSERTION** ⚠️ | MIT | LGPL/MIT |
| Push cuối | 2026-08-03 | 2026-07-15 | — |
| Ngôn ngữ | TypeScript/React | TypeScript/React | Python |
| Hiệu ứng sẵn có | Nhiều nhất | Khá | Phải tự viết hết |
| VRAM khi render | **0** (headless Chrome) | 0 | 0 |
| Thêm runtime? | Có (Node) | Có (Node) | Không |

**Chọn Remotion.** Vì kết luận ở trên: chất lượng video ở đây đến từ khối dựng, nên
khối dựng phải là thứ mạnh nhất. Remotion có hệ sinh thái lớn nhất và animation API
tốt nhất; render bằng headless Chrome nên **không tranh VRAM với khối sinh ảnh** —
điều này quan trọng khi chỉ có 6GB.

⚠️ **Rủi ro license — phải theo dõi.** `NOASSERTION` nghĩa là GitHub không nhận diện
được license chuẩn. Remotion miễn phí cho cá nhân và công ty ≤3 người; **DTG dùng
thương mại phải mua license**. Chi tiết ở `research/repo-cards/remotion.md`. Nếu điều
kiện này thành vấn đề, đường thoát là **Revideo** (fork MIT, cùng mô hình lập trình) —
đổi được vì ranh giới `video-spec.json` giữ nguyên.

## Ma trận: sinh hình ảnh

> **Cập nhật 2026-08-04 sau P1.S4: LTX-Video 2B đã bị LOẠI.** Probe fail — OOM ở cả
> 4 cấu hình, kể cả 256×256 với 25 frame. Nguyên nhân là trọng số model (6,34 GB) lớn
> hơn VRAM của card (5,60 GB PyTorch dùng được), nên giảm độ phân giải không cứu được.
> Bản FP8 vừa VRAM nhưng kernel FP8 chỉ chạy trên Ada trở lên — 2060 là Turing sm_75.
> Số đo đầy đủ: `research/probes/p1s4-ltx.md`.

| | SDXL-Lightning/Turbo | Flux.1-schnell Q4 | ~~LTX-Video 2B~~ | LTX-2 | Wan2.2 14B |
|---|---|---|---|---|---|
| VRAM | ~4–5GB ✅ | ~6GB (sát) ⚠️ | **6,34GB — OOM** ❌ | ~20GB ❌ | 65–80GB ❌ |
| Tốc độ trên 2060 | ~10s/ảnh | ~2 phút/ảnh | **không chạy được** | n/a | n/a |
| Vai trò | **mặc định**, ảnh thường | ảnh "hero" 1–2 cái/video | ~~2–3 shot nhấn~~ **loại** | loại | loại |

**Chọn:** SDXL-Lightning làm mặc định, Flux-Q4 cho ảnh hero. **Không sinh video local.**

**Hệ quả — đã lường trước, không phải sự cố:** hình ảnh thuần ảnh tĩnh + animation
Remotion. Điều này **không giết dự án**, và P1.S3 cho thấy vì sao: render 60s hết **37
giây**, VRAM = 0, chiếm 1,5% ngân sách wall_time. Có rất nhiều dư địa để đầu tư vào
chuyển động do code sinh (Ken Burns, parallax, transition, phụ đề động) — đúng hướng mà
kết luận cốt lõi ở đầu tài liệu này đã chỉ ra.

`configs/models.yaml` vốn đã đặt `video.enabled: false` — cấu hình mặc định đã đúng,
không cần đổi.

**Đường còn mở (chưa thử, để Tony quyết):** bản GGUF Q4/Q5 của 2B
(`city96/LTX-Video-0.9.6-distilled-gguf`) về lý thuyết vừa 6GB, nhưng cần thêm ComfyUI
vào hệ và vẫn dựa trên dòng model đã đóng băng — xem card repo.

## Ma trận: đăng TikTok

| | **API draft/inbox** ✅ chọn | API + audit direct-post | Bên thứ ba đã audit | Playwright |
|---|---|---|---|---|
| Hợp ToS | ✅ | ✅ | ✅ | ❌ |
| Chi phí | 0đ | 0đ | $20–50/tháng | 0đ |
| Chờ | 0 | 2–4 tuần | 0 | 0 |
| Tự động hoàn toàn | ❌ (1 chạm) | ✅ | ✅ | ✅ |
| Rủi ro | không | bị từ chối | phụ thuộc bên thứ ba | **khoá tài khoản** |

**Chọn draft trước, nộp audit song song** (P6). Playwright bị loại: vi phạm ToS TikTok
và rủi ro khoá tài khoản không đáng đánh đổi lấy một chạm tay.

## Ma trận: framework agent

| | **Claude Agent SDK** ✅ chọn | LangGraph | Python thuần |
|---|---|---|---|
| Chi phí LLM | **0đ** — dùng auth Claude Code sẵn có | cần API key riêng | tuỳ |
| Built-in tools | Read/Write/Bash/WebSearch/WebFetch, subagent | không | không |
| Khoá framework | thấp — orchestration vẫn là Python | cao | không |

**Chọn Claude Agent SDK** (`pip install claude-agent-sdk`, gọi `query(prompt, options)`).
⚠️ Đây là package **riêng biệt**, không phải `client.beta.messages.tool_runner` của SDK
`anthropic` — hai thứ rất hay bị lẫn. Docs: `code.claude.com/docs/en/agent-sdk`.

Dùng SDK **chỉ ở chỗ cần suy luận** (trend, kịch bản, critic). Nối ống bằng Python thuần
+ hàng đợi trên đĩa — vì render mất hàng chục phút và có thể chết giữa chừng.

---

## Khuyến nghị

### Stack đã chốt

| Khâu | Chọn | License | Ghi chú |
|---|---|---|---|
| Agent | Claude Agent SDK (Python) | — | 0đ, dùng auth Claude Code |
| TTS | VieNeu-TTS-v2 qua HTTP | Apache-2.0 | tạm, đổi endpoint khi model Tony xong |
| Sinh ảnh | SDXL-Lightning + Flux.1-schnell Q4 | Apache-2.0 | trên 2060 |
| Sinh video | LTX-Video 2B **(có điều kiện)** | Apache-2.0 | P1.S4 quyết định |
| VLM chấm ảnh | Qwen3-VL local | Apache-2.0 | chạy sau khi visual nhả VRAM |
| Dựng video | **Remotion** | ⚠️ NOASSERTION | 0 VRAM, CPU-bound |
| Đăng | TikTok Content Posting API (draft) | — | audit ở P6 |

### Ranh giới kiến trúc — điều quan trọng nhất

**`video-spec.json` là ranh giới duy nhất giữa Python và TypeScript.** Python sinh ra,
Remotion tiêu thụ. Không có chỗ nào khác gọi chéo. Đây là thứ cho phép đổi Remotion →
Revideo (nếu license thành vấn đề) mà không đụng phần còn lại.

**Hàng đợi job trên đĩa, không gọi lồng nhau.** Vì render mất hàng chục phút; state
trên đĩa cho phép chạy lại đúng một bước thay vì render lại từ đầu.

**6GB không cho chạy song song.** Khối visual và VLM tranh VRAM — hàng đợi phải tuần tự
hoá job chiếm GPU và giải phóng model trước khi sang bước sau.

### Vòng lặp QC

Bốn nguyên tắc, lấy từ đồng thuận 2026 (nguồn ở `02-sources.md`):

1. **Tách hẳn Producer/Critic** — critic là agent riêng, prompt là *"tìm cái sai"*
2. **Neo critic vào tín hiệu đo được** — T1 chạy `ffprobe`/OpenCV, **0 LLM**
3. **Chặn 2 vòng sửa** — vòng 3 hiếm khi đáng tiền
4. **Ghi lại vết** — sau 20 video mới biết tầng nào thật sự bắt được lỗi

| Tầng | Chạy bằng | Quyền |
|---|---|---|
| T1 kỹ thuật | ffprobe + OpenCV, 0 LLM | **chặn cứng** |
| T2 hình ảnh | Qwen3-VL local | đề xuất render lại shot |
| T3 sức hút | LLM + rubric `configs/rubric.md` | đề xuất sửa script |
| T4 sự thật | LLM + đối chiếu `trends.jsonl` | **chặn cứng** |

### Phương án dự phòng

| Nếu | Thì |
|---|---|
| Remotion license thành vấn đề | Chuyển **Revideo** (MIT) — `video-spec.json` giữ nguyên |
| ~~P1.S4 fail (LTX-2B không chạy)~~ | ✅ **ĐÃ KÍCH HOẠT 2026-08-04.** Bỏ sinh video local, thuần ảnh tĩnh + animation Remotion |
| ~~P1.S2 fail (VieNeu không có timestamp)~~ | ✅ **ĐÃ KÍCH HOẠT 2026-08-04.** VieNeu không trả timestamp → dùng **Qwen3-ForcedAligner-0.6B**. Lưu ý: đây là model **riêng**, không phải Qwen3-ASR, và tiếng Việt **không** nằm trong `support_languages` chính thức — nhưng đo thật thì align đúng từng từ |
| P1.S3 fail (render quá chậm) | ❌ không cần — render 60s hết **37 giây**, `tris` giữ nguyên trạng thái tắt |
| P1.S1 fail (TikTok draft) | ⏳ chưa biết — chờ Tony chạy phần tay |
| Khe 5090 rộng ra > 20GB | Thay khối `visual/` bằng LTX-2, không đụng phần còn lại |

---

## Tiêu chí dừng

| Kiểm khi | Dừng nếu | Làm gì |
|---|---|---|
| Sau P1 | ≥ 2/4 probe fail | Xem lại kiến trúc trước khi viết tiếp code |
| Sau 20 video | `approve_rate` < 0,3 | Vấn đề ở nội dung, không ở pipeline — xem lại rubric/format, **đừng thêm agent** |
| Sau 20 video | `qc_rounds` ≈ 2 liên tục | Producer yếu — sửa scriptwriter/visual, đừng sửa critic |
| Bất kỳ lúc nào | `wall_time` > 90 phút/video | Nhịp không chạy nổi — cắt bớt khối sinh ảnh |

## Rủi ro mở

1. **Remotion license** — điều kiện thương mại. Đã đọc nguyên văn 2026-08-04: cá nhân
   dùng thương mại **miễn phí**; tổ chức >3 người phải mua. ⚠️ **Remotion 5.0 sẽ đổi
   license** (contractor tính vào team size) — đừng nâng major version tự động.
   Chi tiết: `repo-cards/remotion-dev-remotion.md`
2. **Trần chất lượng do 2060** — chấp nhận. P1.S4 xác nhận trần này **thấp hơn** dự đoán:
   không sinh được video, chỉ ảnh tĩnh
3. **T3 chủ quan nhất** — rubric viết trước; sau 20 video phải xem lại tầng nào có ích
4. ~~LTX-Video chậm lại~~ → **đã thành hiện thực, và nặng hơn**: repo không chậm lại mà
   **bị thay thế** — README tuyên bố "LTX-2 is now the primary home for LTX development".
   Dòng model này đã đóng. Đã loại khỏi stack
5. **Dùng ForcedAligner ngoài phạm vi hỗ trợ chính thức** *(mới, 2026-08-04)* — tiếng Việt
   không có trong `support_languages` của `Qwen3-ForcedAligner-0.6B`, nhưng đo thật thì
   align đúng. Nếu Qwen siết theo danh sách ở bản sau, phụ đề karaoke mất chỗ dựa.
   Đường lùi (`even_split`) đo được lệch **458ms**, vượt ngưỡng 120ms → không dùng được
6. **Thuật ngữ tiếng Anh có thể bị TTS đọc sai** *(mới, 2026-08-04)* — round-trip cho
   `card`→"cat", `model`→"modo". Chưa phân định được lỗi ở TTS hay ở ASR.
   **Cần Tony nghe `out/p1s2/probe.wav`** — nội dung về AI đầy thuật ngữ tiếng Anh nên
   nếu sai thật thì mọi video đều dính
7. ~~Chưa grounded~~ → **đã đóng một phần**: P1.S2/S3/S4 đã tự đo. Còn P1.S1 (TikTok)
   chờ Tony
