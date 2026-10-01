# todos.md — toàn bộ phase/step của `exp-create-video`

**Cách dùng file này.** Mỗi step là một khối **tự chứa**: đọc một khối là đủ làm, không
cần đọc khối khác. Mở step cần làm, đọc từ **Mục tiêu** tới **Bẫy**, rồi làm. Khi xong,
đánh dấu `[x]` và ghi số đo vào file mà mục **Xong khi** chỉ định.

Thứ tự các phase xếp theo **rủi ro**, không theo kỷ luật quy trình. Ba thứ có thể giết
dự án nằm ở P1 — làm P1 trước khi viết bất kỳ dòng code pipeline nào.

---

## Ngữ cảnh chung — mọi step đều cần

Đọc một lần, không lặp lại ở từng step.

| | |
|---|---|
| **Repo thật** | `/mnt/data1tb/exp-create-video` (symlink `~/DTG/exp-create-video`) |
| **Máy chạy** | `tony` — RTX 2060 **6GB**, 12 core, RAM 31GB. `tris` mặc định **tắt** |
| **Chi phí** | **0đ**. Chỉ model open-weight local + free tier. Không API trả tiền |
| **Ngôn ngữ video** | Tiếng Việt, khán giả VN. Video dọc 1080×1920, 15–60s, TikTok |
| **Quyết định gốc** | `research/05-decision.md` — đọc trước khi đổi bất cứ lựa chọn nào |
| **Bài toán & metric** | `research/00-problem.md` |
| **Nguồn + độ tin** | `research/02-sources.md` |
| **Kỷ luật đo** | `.claude/rules/eval-discipline.md` |
| **Chiến lược nội dung** | `research/07-len-xu-huong.md` — completion 70%, nhãn AI, SEO, chống AI slop |
| **Quyết định phong cách** | `research/06-nhip-va-font.md` — font Anton, giọng Thanh Bình, nhịp 3-8s |

**Ba ràng buộc dễ quên nhất:**

1. **6GB không cho chạy song song.** Khối `visual/` (~5–6GB) và VLM chấm ảnh (~4GB)
   **không được nạp cùng lúc**. Phải giải phóng model trước khi sang bước sau. Quên →
   OOM ngẫu nhiên giữa chừng render, rất khó truy.
2. **`video-spec.json` là ranh giới duy nhất** giữa Python và TypeScript. Python sinh
   ra, Remotion tiêu thụ. Không viết code Python gọi thẳng vào Remotion hay ngược lại.
3. **Ngưỡng viết trước, không sửa sau khi thấy kết quả.** Ngưỡng nằm ở
   `configs/thresholds.yaml`, đã viết sẵn từ lúc dựng repo.

**Claude Agent SDK — chống nhầm:** package là `claude-agent-sdk`
(`pip install claude-agent-sdk`, gọi `query(prompt, options)`). Đây **không phải**
`client.beta.messages.tool_runner` của SDK `anthropic` — hai thứ khác nhau và rất hay
bị lẫn. Docs: `code.claude.com/docs/en/agent-sdk`.

---

## Chạy song song bằng git worktree

Nhiều step độc lập nhau hoàn toàn. Chạy song song bằng `git worktree` — mỗi worktree là
một thư mục riêng, một branch riêng, nhưng **chung một repo `.git`**, nên không tốn dung
lượng nhân đôi và merge lại rất gọn.

**Điều kiện tiên quyết:** `git worktree` cần repo có **ít nhất 1 commit**. Repo hiện chưa
commit lần nào (Tony tự quản git). Commit lần đầu trước khi dùng worktree.

### Lệnh tạo

```bash
cd /mnt/data1tb/exp-create-video
git worktree add ../wt-<tên-step> -b <tên-step>
cd ../wt-<tên-step>
# ... làm việc ...
```

### Prompt mở phiên Claude Code song song

Mở mỗi worktree trong một terminal riêng, chạy `claude`, dán prompt này:

```
Dự án: exp-create-video — hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI.
Tôi đang ở WORKTREE /mnt/data1tb/wt-<tên-step>, branch <tên-step>.
Repo gốc: /mnt/data1tb/exp-create-video

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/05-decision.md — mọi lựa chọn kiến trúc và lý do
  3. research/00-problem.md  — metric và "đủ tốt" bằng số

VIỆC: làm đúng step <mã step> trong todos.md và CHỈ step đó.
Không đụng file ngoài phạm vi step đó nêu.

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB, 12 core, RAM 31GB. tris mặc định TẮT.
  - 6GB không cho nạp visual (~5-6GB) và VLM (~4GB) cùng lúc. Phải
    torch.cuda.empty_cache() trước khi sang bước sau.
  - Chi phí 0đ. Chỉ model open-weight chạy local. Không API trả tiền.
  - video-spec.json là ranh giới DUY NHẤT giữa Python và Remotion.
  - Ngưỡng ở configs/thresholds.yaml viết TRƯỚC, không sửa sau khi thấy kết quả.
  - Agent SDK là `claude-agent-sdk` (pip install claude-agent-sdk, gọi query()).
    KHÔNG phải client.beta.messages.tool_runner của SDK `anthropic` — hay bị lẫn.
  - Tony tự quản git. KHÔNG commit hộ, kể cả khi thấy tiện.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

RÀNG BUỘC RIÊNG CỦA CHẾ ĐỘ SONG SONG:
Có <N> phiên Claude Code khác đang chạy CÙNG LÚC trên CÙNG MÁY tony.
  - Nếu step của tôi chiếm GPU: chạy `nvidia-smi` TRƯỚC khi nạp model.
    VRAM trống < 5GB thì CHỜ, đừng chạy — cả máy chỉ có 6GB.
  - KHÔNG sửa file dùng chung: configs/, todos.md, research/05-decision.md.
    Cần đổi gì thì ghi vào cuối file kết quả của step, Tony merge tay sau.
  - Chỉ tạo/sửa file thuộc phạm vi step này, để merge branch không xung đột.
```

### Gộp lại

```bash
cd /mnt/data1tb/exp-create-video
git merge <tên-step>          # lặp cho từng branch
git worktree remove ../wt-<tên-step>
```

### Prompt của từng phase đã đầy đủ, copy thẳng

Mỗi phase bên dưới có một khối **📋 Prompt mở phiên** — copy nguyên khối trong ```
là dùng được ngay, không phải ghép thêm gì. Mỗi khối đã chứa sẵn đường dẫn repo, danh
sách file phải đọc, và toàn bộ ràng buộc cứng, nên **dùng được cả khi context đã bị nén
hoặc khi mở phiên hoàn toàn mới**.

Chỉ cần sửa một chỗ: thay `P<n>.S<n>` bằng mã step muốn làm.

### Bảng song song hoá

⚠️ **Cột "GPU" là ràng buộc thật.** Worktree chạy song song trên **cùng một máy tony**
với **một GPU 6GB**. Hai step cùng chiếm GPU **không** chạy song song được, dù nằm khác
worktree.

| Phase | Step chạy song song được | GPU | Ghi chú |
|---|---|---|---|
| **P1** | S1 (TikTok) ∥ S3 (Remotion) | không | ✅ song song thoải mái |
| **P1** | S2 (TTS) → S4 (LTX) | **có** | ❌ **nối đuôi**, không song song |
| **P2** | S1 (schema) ∥ S3 (T1 QC) | không | S2 phụ thuộc S1 |
| **P3** | S1 (scriptwriter) ∥ S2 (voice adapter) | không | S3 (visual) cần GPU, chạy riêng |
| **P4** | S2 (T3 sức hút) ∥ S3 (T4 sự thật) | không | S1 (T2 VLM) cần GPU, chạy riêng |
| **P5** | S1 (trend-scout) ∥ S2 (Telegram) ∥ S3 (TikTok publish) | không | ✅ ba worktree cùng lúc |
| **P3b** | S1 (lỗi dựng) ∥ S2 (giọng) ∥ S4 (shot bằng chứng) | không* | *S8 (model ảnh) chiếm GPU, chạy riêng |

**Nhịp gợi ý:** P1 mở 2 worktree (S1, S3) + làm S2→S4 tuần tự ở worktree chính.
P5 mở 3 worktree — đây là phase song song hoá tốt nhất.

---

# P0 — Nền quyết định ✅ ĐÃ XONG

Đã làm lúc dựng repo. Ghi lại để biết đã có gì.

- [x] `research/00-problem.md` — input/output, metric, "đủ tốt" bằng số
- [x] `research/05-decision.md` — ma trận lựa chọn, stack, tiêu chí dừng
- [x] `research/02-sources.md` — nhật ký nguồn, phân verified/reported
- [x] `configs/*.yaml` + `configs/rubric.md` + `configs/thresholds.yaml`
- [x] `CLAUDE.md`, `README.md`, `.claude/rules/eval-discipline.md`

---

# P1 — Bốn probe giết-hoặc-sống ⚠️ QUAN TRỌNG NHẤT

**Vì sao phase này đứng đầu:** ba trong bốn probe, nếu fail, buộc phải đổi kiến trúc.
Viết code pipeline trước khi biết kết quả là xây trên nền chưa kiểm.

**Nguyên tắc chung của P1:** tiêu chí pass/fail viết **trước** khi chạy. Kết quả ghi
vào `research/probes/<mã>.md` kèm ngày và số đo thật, kể cả khi fail — probe fail là
thông tin có giá trị, không phải thất bại.

### 📋 Prompt mở phiên — P1

```
Dự án: exp-create-video — hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/05-decision.md — mọi lựa chọn kiến trúc và lý do
  3. research/00-problem.md  — metric và "đủ tốt" bằng số

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB, 12 core, RAM 31GB. tris mặc định TẮT.
  - 6GB không cho nạp visual (~5-6GB) và VLM (~4GB) cùng lúc. Phải
    torch.cuda.empty_cache() trước khi sang bước sau.
  - Chi phí 0đ. Chỉ model open-weight chạy local. Không API trả tiền.
  - video-spec.json là ranh giới DUY NHẤT giữa Python và Remotion.
    Không viết code Python gọi thẳng Remotion hay ngược lại.
  - Ngưỡng ở configs/thresholds.yaml viết TRƯỚC, không sửa sau khi thấy kết quả.
  - Agent SDK là `claude-agent-sdk` (pip install claude-agent-sdk, gọi query()).
    KHÔNG phải client.beta.messages.tool_runner của SDK `anthropic` — hay bị lẫn.
  - Tony tự quản git. KHÔNG commit hộ, kể cả khi thấy tiện.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

VIỆC LẦN NÀY: Phase 1 — bốn probe giết-hoặc-sống.

Vì sao phase này đứng đầu: ba trong bốn probe, nếu fail, buộc phải đổi kiến trúc.
Viết code pipeline trước khi biết kết quả là xây trên nền chưa kiểm. Mọi con số tốc
độ trong research/ hiện là "reported" (đọc từ nguồn thứ cấp) — P1 chuyển chúng thành
"verified" (tự đo).

Làm step: P1.S<n>. Mở todos.md, đọc đúng khối step đó — nó có đủ mục tiêu, file phải
đọc trước, việc cụ thể, tiêu chí xong bằng số, và cái bẫy đã biết.

QUY TẮC RIÊNG CỦA P1:
  - Tiêu chí pass/fail đã viết sẵn trong step. KHÔNG nới ngưỡng khi thấy kết quả xấu.
  - Ghi kết quả vào research/probes/<mã step>.md kèm NGÀY và SỐ ĐO THẬT,
    kể cả khi fail. Probe fail là thông tin, không phải thất bại.
  - Mỗi step có mục "Nếu fail" — làm đúng theo đó, đừng tự nghĩ phương án mới.
  - Đo lần chạy thứ 2 và 3, bỏ lần đầu (lần đầu gồm compile kernel + tải model).

RÀNG BUỘC GPU: P1.S2 (TTS) và P1.S4 (LTX) đều chiếm GPU — chạy NỐI ĐUÔI, không song
song. P1.S1 (TikTok) và P1.S3 (Remotion) không đụng GPU, chạy song song thoải mái.
```

---

### [~] P1.S1 — TikTok draft API — *code xong, chờ Tony làm phần tay (2026-08-04)*

**Mục tiêu:** đẩy được một file mp4 vào hộp draft của tài khoản TikTok thật.

**Ngữ cảnh:** Content Posting API cho client **chưa qua audit** thì mọi direct post bị
ép `SELF_ONLY` — chỉ mình chủ tài khoản thấy. Vì vậy phase đầu dùng chế độ **draft/inbox**:
API đẩy video vào hộp draft, Tony mở app bấm đăng. Hợp ToS, không cần audit, và ăn khớp
luôn với luồng duyệt qua Telegram. Audit direct-post để tới P6. Nguồn:
`research/02-sources.md` mục "TikTok API".

**Đọc trước:** `research/02-sources.md` (mục TikTok) · `research/05-decision.md`
(ma trận "đăng TikTok")

**Việc:**
1. Đăng ký TikTok developer app, xin scope `video.upload` (draft) — **ghi lại xem có
   bắt buộc Business account không**, đây là câu hỏi còn mở
2. Chạy OAuth lấy access token + refresh token, lưu vào `.env` (đã gitignore)
3. Viết script probe `exp/probes/tiktok_draft.py`: upload 1 mp4 mẫu bất kỳ vào draft
4. Mở app TikTok trên điện thoại, kiểm video có trong hộp draft không

**Xong khi:** video xuất hiện trong draft và đăng tay được. Ghi vào
`research/probes/p1s1-tiktok.md`: có cần Business account không, scope nào được cấp,
token sống bao lâu, giới hạn kích thước/độ dài file.

**Nếu fail:** publisher chuyển sang chỉ lưu local + báo Telegram; audit ở P6 thành
**bắt buộc** chứ không còn là tuỳ chọn. Ghi rõ lý do fail vào file kết quả.

**Bẫy:** đừng nhầm draft (`inbox`) với direct post. Direct post chưa audit sẽ "thành
công" nhưng video ở chế độ `SELF_ONLY` — nhìn như chạy được nhưng thực chất không ai xem
được. Kiểm bằng cách mở app xem video nằm ở đâu.

**Song song:** ✅ chạy cùng P1.S3 được — không đụng GPU, không đụng file chung.

---

### [x] P1.S2 — VieNeu-TTS thành HTTP service — ✅ **PASS** (2026-08-04, qua ForcedAligner)

**Mục tiêu:** một endpoint `POST /tts` nhận text tiếng Việt, trả wav **+ timestamp từng từ**.

**Ngữ cảnh:** Tony đang tự phát triển model TTS; đây là bản tạm để thông pipeline. Model
đã chốt ở repo `voice`: **VieNeu-TTS-v2, Apache-2.0, chưa đo bao giờ** (xem
`/mnt/data1tb/voice/CLAUDE.md`). Timestamp từng từ là **bắt buộc** — phụ đề karaoke của
Remotion ăn trực tiếp từ đó; không có timestamp thì không có phụ đề động, mà phụ đề động
là một trong ba thứ tạo nên "video hay" ở đây. Khi model của Tony xong thì chỉ đổi
endpoint trong `configs/models.yaml`, không sửa pipeline.

**Đọc trước:** `/mnt/data1tb/voice/CLAUDE.md` · `/mnt/data1tb/voice/research/06-market.md`
· `configs/models.yaml`

**Việc:**
1. Tạo venv **riêng** trong `exp/tts/` — đừng dùng chung venv của repo `voice`, môi
   trường hai bên sẽ xung đột dependency
2. Viết `exp/tts/serve.py`: FastAPI, load model **một lần** lúc khởi động,
   `POST /tts {text, speaker} → {wav_path, words: [{w, start, end}]}`
3. Nếu VieNeu không trả timestamp: dùng **ForcedAligner của Qwen3-ASR** ở repo `voice`
   để align wav với text — đây là phương án dự phòng đã chốt
4. Định nghĩa interface `TTSBackend` trong `src/create_video/voice/base.py`, rồi
   implement `VieNeuBackend` trong `src/create_video/voice/vieneu.py`

**Xong khi:** câu tiếng Việt 15 từ → wav nghe được + JSON timestamp khớp khi phát.
VRAM đỉnh **< 3GB**. Số đo ghi vào `research/probes/p1s2-tts.md` kèm ngày.

**Nếu fail:** dùng ForcedAligner (đã ở bước 3). Nếu cả hai fail thì phụ đề chuyển sang
chia đều theo độ dài câu — xấu hơn nhiều, ghi thành nợ kỹ thuật.

**Bẫy:** repo `voice` phải **ép cứng `language="Vietnamese"`** cho ASR, vì để tự nhận
thì ~2% số đoạn ra chữ Thái/Quảng Đông/Bồ Đào Nha. Kiểm xem VieNeu có bẫy tương tự
không **trước khi tin output** — nghe thử vài câu, đừng chỉ nhìn file có tồn tại.

**Song song:** ❌ chiếm GPU — **không** chạy cùng P1.S4. Làm S2 xong rồi mới tới S4.

---

### [x] P1.S3 — Remotion render trên tony — ✅ **PASS** (2026-08-04, 37s so ngưỡng 15 phút)

**Mục tiêu:** biết render một video 1080×1920 dài 60s trên 12 core mất bao lâu.

**Ngữ cảnh:** Remotion render bằng **headless Chrome** — ăn CPU và RAM, **không ăn VRAM**.
Đây là lý do nó không tranh tài nguyên với khối sinh ảnh, và là một phần lý do được chọn
(xem ma trận ở `research/05-decision.md`). Cần biết con số thật để quyết định có phải
bật `tris` không. ⚠️ Remotion license là **NOASSERTION** — miễn phí cho cá nhân và công
ty ≤3 người; nếu DTG dùng thương mại thì phải mua. Ghi điều kiện chính xác vào repo-card.

**Đọc trước:** `research/05-decision.md` (ma trận "khối dựng video") · `remotion/package.json`

**Việc:**
1. `cd remotion && npm install` (lần đầu — chưa cài lúc dựng repo)
2. Viết một composition tối giản: nền màu + text chạy + 1 ảnh Ken Burns, 60s, 1080×1920
3. `npx remotion render` — **đo thời gian thật** bằng `time`
4. Đo cả RAM đỉnh (`/usr/bin/time -v`) — 31GB có thể là nút thắt trước cả CPU
5. Đọc file `LICENSE` gốc của Remotion, ghi điều kiện thương mại chính xác vào
   `research/repo-cards/remotion.md`

**Xong khi:** render xong, **< 15 phút**, VRAM = 0. Số đo (thời gian, RAM đỉnh, số core
thực dùng) ghi vào `research/probes/p1s3-remotion.md`.

**Nếu fail (> 15 phút):** bật `tris` trong `configs/machines.yaml` (32 core, RAM 123GB).
Đây là **lần duy nhất** trong dự án được đụng tris.

**Bẫy:** Remotion mặc định có thể dùng ít core hơn số core thật. Kiểm `--concurrency` —
đo với thiết lập mặc định trước, rồi đo lại với `--concurrency=12`, ghi cả hai số.

**Song song:** ✅ chạy cùng P1.S1 được — không đụng GPU.

---

### [x] P1.S4 — LTX-Video 2B trên Turing — ❌ **FAIL** (2026-08-04, OOM mọi cấu hình → đã loại)

**Mục tiêu:** biết LTX-Video 2B có chạy nổi trên RTX 2060 6GB không.

**Ngữ cảnh:** LTX-Video 2B theo tài liệu cần **6–8GB + tiling**, và các hướng dẫn tối ưu
đều dựa vào **FP8** — mà **Turing sm_75 không có FP8 native**. Đây là lý do phải probe
chứ không tin bảng: con số trên mạng đo trên Ada/Blackwell. LTX-2 (bản lớn) cần ~20GB —
ngoài tầm hoàn toàn, đừng thử. Repo `Lightricks/LTX-Video` push cuối **2026-01-05**
(7 tháng) — đang chậm lại, ghi vào rủi ro.

**Đọc trước:** `research/02-sources.md` (mục model sinh video) ·
`research/05-decision.md` (ma trận "sinh hình ảnh")

**Việc:**
1. Venv riêng `exp/ltx/`, cài LTX-Video theo repo gốc
2. Thử **image-to-video** (không phải text-to-video): 1 ảnh tĩnh → clip 5s @512p
3. Nếu OOM: bật tiling, giảm độ phân giải, thử fp16 thay vì fp8 (Turing không có fp8)
4. Đo: thời gian, VRAM đỉnh, chất lượng chuyển động có dùng được không (xem bằng mắt)
5. Chạy `.claude/skills/repo-audit/scripts/repo-health.sh Lightricks/LTX-Video`,
   ghi card vào `research/repo-cards/`

**Xong khi:** clip i2v 5s @512p **< 5 phút**, **không OOM**, chuyển động không méo mó.
Ghi vào `research/probes/p1s4-ltx.md`.

**Nếu fail:** **bỏ hẳn sinh video local.** Khối `visual/` chỉ sinh ảnh tĩnh, chuyển
động do Remotion lo (Ken Burns, parallax, zoom, transition). **Điều này không giết dự
án** — với Remotion làm khối dựng, ảnh tĩnh + animation code vốn đã đủ cho format này.
Cập nhật `research/05-decision.md` mục "sinh hình ảnh".

**Bẫy:** đừng đo lần chạy đầu — lần đầu gồm cả thời gian compile kernel và tải model.
Chạy 3 lần, lấy số của lần 2 và 3.

**Song song:** ❌ chiếm GPU — chạy **sau** P1.S2, không cùng lúc.

---

### [x] P1.S5 — Audit các repo sắp phụ thuộc — ✅ **xong** (2026-08-04, 4 card)

**Mục tiêu:** biết mình sắp dựa vào cái gì, và làm gì nếu nó chết trong 12 tháng.

**Ngữ cảnh:** dự án phụ thuộc vào 4 repo bên ngoài. Hai cái đã có tín hiệu đáng lo:
Remotion license NOASSERTION, LTX-Video 7 tháng không push. Skill `repo-audit` dùng
**CHAOSS + OpenSSF Scorecard** — chuẩn ngành, không phải tiêu chí tự chế.

**Đọc trước:** `.claude/skills/repo-audit/SKILL.md` · `research/02-sources.md`

**Việc:** chạy `/repo-audit` cho từng repo, mỗi cái ghi một card vào
`research/repo-cards/`:

| Repo | Dùng để làm gì | Điều đặc biệt phải kiểm |
|---|---|---|
| `remotion-dev/remotion` | Khối dựng video | **License NOASSERTION — ghi chính xác điều kiện thương mại cho DTG** |
| `Lightricks/LTX-Video` | Sinh video ngắn | 7 tháng không push — bus factor, issue tracker có ai trả lời không |
| VieNeu-TTS | TTS tiếng Việt tạm | License weights (khác license code), có công thức fine-tune không |
| Thư viện TikTok API client | Đăng bài | Có theo kịp thay đổi API TikTok không |

**Xong khi:** 4 card trong `research/repo-cards/`, mỗi card có verdict
(adopt/vendor/fork/reimplement/drop) **và exit plan** — làm gì nếu repo chết.

**Bẫy:** phân biệt **license code** với **license weights** — với repo ML hai cái khác
nhau rất thường xuyên (Apache-2.0 code kèm weights non-commercial là chuyện phổ biến).

**Song song:** ✅ chạy cùng bất cứ step nào — chỉ đọc, không đụng GPU.

---

# P2 — Xương sống render

**Nguyên tắc:** làm **ngược từ đầu ra**. Có mp4 xem được trước, rồi mới nhét nội dung
thật vào. Cách này lúc nào cũng có thứ xem được, và bắt lỗi khối dựng sớm — mà khối
dựng mới là thứ quyết định video hay hay dở.

### 📋 Prompt mở phiên — P2

```
Dự án: exp-create-video — hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/05-decision.md — mọi lựa chọn kiến trúc và lý do
  3. research/00-problem.md  — metric và "đủ tốt" bằng số

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB, 12 core, RAM 31GB. tris mặc định TẮT.
  - 6GB không cho nạp visual (~5-6GB) và VLM (~4GB) cùng lúc. Phải
    torch.cuda.empty_cache() trước khi sang bước sau.
  - Chi phí 0đ. Chỉ model open-weight chạy local. Không API trả tiền.
  - video-spec.json là ranh giới DUY NHẤT giữa Python và Remotion.
    Không viết code Python gọi thẳng Remotion hay ngược lại.
  - Ngưỡng ở configs/thresholds.yaml viết TRƯỚC, không sửa sau khi thấy kết quả.
  - Agent SDK là `claude-agent-sdk` (pip install claude-agent-sdk, gọi query()).
    KHÔNG phải client.beta.messages.tool_runner của SDK `anthropic` — hay bị lẫn.
  - Tony tự quản git. KHÔNG commit hộ, kể cả khi thấy tiện.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

VIỆC LẦN NÀY: Phase 2 — xương sống render.

Mục tiêu phase: từ một file video-spec.json ra được mp4 1080x1920 hoàn chỉnh, và có
cổng kiểm kỹ thuật chặn được video hỏng. Chưa cần nội dung thật — dùng spec mẫu tay.

Vì sao làm ngược từ đầu ra: khối dựng (Remotion) là thứ quyết định video hay hay dở,
vì trần chất lượng hình ảnh do RTX 2060 đặt ra rất thấp. Mọi sức hút phải đến từ nhịp
dựng, hook và phụ đề động — nên khối này phải chạy được và xem được trước tiên.

Làm step: P2.S<n>. Mở todos.md, đọc đúng khối step đó.

QUY TẮC RIÊNG CỦA P2:
  - video-spec.json là ranh giới kiến trúc quan trọng nhất của dự án. Schema mô tả
    CÁI GÌ, không mô tả LÀM THẾ NÀO. "Ken Burns trái sang phải, 4 giây" là dữ liệu;
    "gọi hàm kenBurns()" là code — không nhét code vào schema.
  - QC tầng 1 chạy bằng ffprobe + OpenCV, TUYỆT ĐỐI KHÔNG LLM. Đây là điểm tựa duy
    nhất không bị ảo của cả vòng QC; nhét LLM vào là mất tính chất đó.
  - Vùng an toàn TikTok: UI che mép dưới và mép phải. Chữ tràn vào đó thì trên máy
    nhìn ổn, trên app bị che. Số cụ thể ở configs/thresholds.yaml (safe_area_pct).

PHỤ THUỘC: P2.S2 cần P2.S1 xong trước. P2.S1 và P2.S3 chạy song song được.
```

---

### [x] P2.S1 — Schema `video-spec.json` — ✅ **xong** (2026-08-14, schema + validator ngữ nghĩa)

**Mục tiêu:** định nghĩa ranh giới duy nhất giữa Python và TypeScript.

**Ngữ cảnh:** đây là **file quan trọng nhất về mặt kiến trúc**. Python sinh ra,
Remotion tiêu thụ; không có chỗ nào khác gọi chéo. Chính ranh giới này cho phép đổi
Remotion → Revideo (nếu license thành vấn đề) mà không đụng phần còn lại. Thiết kế sai
ở đây thì mọi thứ sau đều lệch.

**Đọc trước:** `research/05-decision.md` (mục "Ranh giới kiến trúc") · `configs/style.yaml`

**Việc:**
1. Thiết kế schema, tối thiểu có: `duration`, `resolution`, `shots[]` (mỗi shot: asset
   path, thời điểm vào/ra, kiểu chuyển động, transition), `captions[]` (word-level
   timestamp), `audio` (voice track + nhạc nền), `meta` (chủ đề, nguồn, video id)
2. Viết JSON Schema ở `src/create_video/spec/schema.json`
3. Viết validator `src/create_video/spec/validate.py` — **fail sớm, thông báo rõ**
4. Viết 1 file mẫu tay `eval/scripts/01-spec.json` để P2.S2 có cái mà render

**Xong khi:** `python -m create_video.spec.validate eval/scripts/01-spec.json` chạy
sạch; sửa hỏng một trường thì báo lỗi chỉ đúng chỗ.

**Bẫy:** đừng nhét logic vào schema. Schema mô tả **cái gì**, không mô tả **làm thế
nào**. "Ken Burns từ trái sang phải, 4 giây" là dữ liệu; "gọi hàm kenBurns()" là code.

**Song song:** ✅ chạy cùng P2.S3 được. P2.S2 **phụ thuộc** step này.

---

### [x] P2.S2 — Remotion composition đọc spec — ✅ **xong** (2026-08-14, karaoke chạy trên mp4 thật)

**Mục tiêu:** `video-spec.json` → mp4 1080×1920 hoàn chỉnh.

**Ngữ cảnh:** đây là khối quyết định video "hay" hay không — vì trần chất lượng hình
ảnh do 2060 đặt ra rất thấp, mọi sức hút phải đến từ **nhịp dựng, hook và phụ đề động**.
Đầu tư ở đây nhiều hơn ở khối sinh ảnh là có chủ ý.

**Đọc trước:** `src/create_video/spec/schema.json` · `configs/style.yaml` ·
`research/probes/p1s3-remotion.md` (số đo render)

**Việc:**
1. `remotion/src/Video.tsx` — composition đọc `video-spec.json` qua `inputProps`
2. `remotion/src/components/KenBurns.tsx` — zoom/pan ảnh tĩnh, hướng và tốc độ từ spec
3. `remotion/src/components/KaraokeCaption.tsx` — phụ đề sáng từng từ theo timestamp;
   **chữ phải nằm trong vùng an toàn TikTok** (tránh UI che), ngưỡng ở `configs/thresholds.yaml`
4. `remotion/src/components/Hook.tsx` — 3 giây đầu, animation mạnh nhất video
5. `remotion/src/components/Transition.tsx` — chuyển cảnh giữa các shot
6. Script `scripts/render.sh` gói lại thành một lệnh

**Xong khi:** `bash scripts/render.sh eval/scripts/01-spec.json` ra mp4 mở được;
`ffprobe` báo đúng 1080×1920; phụ đề khớp audio khi xem.

**Bẫy:** vùng an toàn TikTok — UI (nút like/share/caption) che mất mép dưới và mép phải.
Chữ tràn vào đó thì trên máy nhìn ổn, trên app bị che. Số cụ thể ở `configs/thresholds.yaml`.

**Song song:** ❌ phụ thuộc P2.S1.

---

### [x] P2.S3 — Cổng QC tầng 1 (kỹ thuật) — ✅ **xong** (2026-08-14, 10 kiểm, đã thử 3 ca fail có chủ ý)

**Mục tiêu:** kiểm mp4 bằng **code, không LLM**.

**Ngữ cảnh:** T1 là tầng duy nhất được **chặn cứng**. Nguyên tắc lấy từ đồng thuận 2026
(nguồn ở `02-sources.md`): critic phải neo vào **tín hiệu đo được**, không tự chấm cảm
tính — CRITIC (ICLR 2024) cho thấy self-correct chỉ đáng tin khi có tín hiệu ngoài. Ở
đây tín hiệu ngoài là `ffprobe` và OpenCV. Tầng này **không tốn token, không bị ảo**.

**Đọc trước:** `configs/thresholds.yaml` · `research/05-decision.md` (mục "Vòng lặp QC")

**Việc:** viết `src/create_video/qc/t1_technical.py`, mỗi kiểm là một hàm riêng trả
`(pass: bool, detail: str)`:

| Kiểm | Bằng |
|---|---|
| Độ dài 15–60s | `ffprobe` |
| Đúng 1080×1920 | `ffprobe` |
| Audio không clip, không im quá 2s | `ffmpeg` volumedetect / `silencedetect` |
| Không frame đen quá 0,5s | `ffmpeg blackdetect` |
| Phụ đề khớp timestamp trong spec | so spec với `words[]` |
| Chữ trong vùng an toàn TikTok | OpenCV, kiểm bbox chữ so ngưỡng |

**Xong khi:** chạy trên mp4 của P2.S2 → pass hết. Cố tình làm hỏng một điều kiện (cắt
video còn 5s) → fail đúng điều kiện đó, thông báo rõ.

**Bẫy:** **không** dùng LLM ở tầng này, kể cả khi thấy tiện. Đây là điểm tựa duy nhất
không bị ảo của cả vòng QC; nhét LLM vào là mất luôn tính chất đó.

**Song song:** ✅ chạy cùng P2.S1 được (dùng mp4 mẫu bất kỳ để test).

---

# P3 — Nội dung: ra được một video hoàn chỉnh

**Mục tiêu phase:** gõ **một lệnh**, ra một video tiếng Việt hoàn chỉnh có nội dung thật.

### 📋 Prompt mở phiên — P3

```
Dự án: exp-create-video — hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/05-decision.md — mọi lựa chọn kiến trúc và lý do
  3. research/00-problem.md  — metric và "đủ tốt" bằng số

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB, 12 core, RAM 31GB. tris mặc định TẮT.
  - 6GB không cho nạp visual (~5-6GB) và VLM (~4GB) cùng lúc. Phải
    torch.cuda.empty_cache() trước khi sang bước sau.
  - Chi phí 0đ. Chỉ model open-weight chạy local. Không API trả tiền.
  - video-spec.json là ranh giới DUY NHẤT giữa Python và Remotion.
    Không viết code Python gọi thẳng Remotion hay ngược lại.
  - Ngưỡng ở configs/thresholds.yaml viết TRƯỚC, không sửa sau khi thấy kết quả.
  - Agent SDK là `claude-agent-sdk` (pip install claude-agent-sdk, gọi query()).
    KHÔNG phải client.beta.messages.tool_runner của SDK `anthropic` — hay bị lẫn.
  - Tony tự quản git. KHÔNG commit hộ, kể cả khi thấy tiện.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

VIỆC LẦN NÀY: Phase 3 — nội dung thật.

Mục tiêu phase: gõ MỘT lệnh, ra MỘT video tiếng Việt hoàn chỉnh có nội dung thật.
P2 đã có khối dựng chạy được với spec mẫu tay; P3 thay spec mẫu bằng nội dung do
agent sinh ra.

Làm step: P3.S<n>. Mở todos.md, đọc đúng khối step đó.

QUY TẮC RIÊNG CỦA P3:
  - scriptwriter phải nhét nguyên configs/rubric.md vào prompt hệ thống. Producer
    biết trước critic chấm bằng gì thì viết đúng ngay từ đầu, giảm số vòng sửa.
  - Tiếng Việt: giữ nguyên thuật ngữ tiếng Anh (model, benchmark, fine-tune,
    inference, prompt, open-source). Dịch ra nghe còn lạ hơn.
  - Hook 3 giây đầu là phần quan trọng nhất. LLM rất hay viết kiểu bài báo — dài,
    đều đều, mở bằng "Hôm nay chúng ta sẽ tìm hiểu về...". Rubric có danh sách
    hook hỏng, đọc kỹ.
  - Ghép wav nhiều đoạn: timestamp của đoạn thứ 2 trở đi PHẢI cộng offset. Quên là
    phụ đề lệch dần về cuối — lỗi này không nhìn ra khi test đoạn ngắn.
  - Khối visual: gọi torch.cuda.empty_cache() sau mỗi backend. Quên -> OOM ở shot
    thứ 3-4, lỗi trông như ngẫu nhiên nên rất khó truy.
  - State phải nằm trên ĐĨA, không trong RAM. Render mất hàng chục phút và sẽ chết
    giữa chừng — đó là lý do tồn tại của cả khối queue/.

RÀNG BUỘC GPU: P3.S3 (visual) chiếm GPU, chạy MỘT MÌNH.
P3.S1 (scriptwriter) và P3.S2 (voice adapter) không đụng GPU, song song được.
```

---

### [x] P3.S1 — Agent scriptwriter — ✅ **xong** (2026-08-14, claude-agent-sdk + rubric trong prompt)

**Mục tiêu:** chủ đề → `script.json` (hook + body + CTA + shot list + prompt ảnh).

**Ngữ cảnh:** viết bằng `claude-agent-sdk`. Kịch bản tiếng Việt, khán giả VN. Cấu trúc
TikTok: **3 giây đầu quyết định người xem ở lại hay lướt** — hook là phần quan trọng
nhất. Script phải sinh luôn prompt ảnh cho từng shot, vì khối `visual/` ăn thẳng từ đó.

**Đọc trước:** `configs/rubric.md` (tiêu chí T3 sẽ chấm chính script này) ·
`src/create_video/spec/schema.json` · `research/00-problem.md`

**Việc:**
1. `src/create_video/agents/scriptwriter.py` — dùng `query()` của `claude-agent-sdk`
2. Output có schema cố định: `{hook, sections[], cta, shots[{prompt, duration, motion}]}`
3. Prompt hệ thống nhét thẳng `configs/rubric.md` vào — **producer biết trước critic sẽ
   chấm bằng gì**, giảm số vòng sửa
4. Giữ nguyên thuật ngữ tiếng Anh (model name, benchmark) — không dịch

**Xong khi:** cho chủ đề "Claude Opus 5 vừa ra mắt" → `script.json` hợp schema, đọc lên
nghe tự nhiên tiếng Việt, hook dưới 3 giây khi đọc.

**Bẫy:** LLM rất hay viết kịch bản kiểu bài báo — dài, đều đều, không có hook. Rubric
phải nói rõ "3 giây đầu phải có một câu khiến người ta dừng lướt", và **cho ví dụ**,
vì ví dụ mạnh hơn mô tả rất nhiều.

**Song song:** ✅ chạy cùng P3.S2 được.

---

### [x] P3.S2 — Cắm voice vào pipeline — ✅ **xong** (2026-08-14, exp-echo v3-Turbo, `research/probes/p3s2-voice-echo.md`)

**Mục tiêu:** `script.json` → wav + word timestamp, qua adapter.

**Ngữ cảnh:** P1.S2 đã dựng service và interface. Step này chỉ nối vào pipeline. Thiết
kế adapter là để khi model TTS của Tony xong thì **đổi một dòng trong
`configs/models.yaml`**, không sửa code pipeline.

**Đọc trước:** `research/probes/p1s2-tts.md` · `src/create_video/voice/base.py` ·
`configs/models.yaml`

**Việc:**
1. `src/create_video/voice/pipeline.py`: đọc `script.json` → gọi `TTSBackend` từng
   đoạn → ghép wav → xuất `voice.wav` + `words.json`
2. Xử lý câu dài: cắt theo dấu câu trước khi gửi TTS, ghép lại sau, **giữ đúng offset
   timestamp** khi ghép — đây là chỗ dễ sai nhất
3. Thêm `DummyBackend` (eSpeak) để test pipeline khi service TTS chưa bật

**Xong khi:** `script.json` 45s → `voice.wav` + `words.json`; timestamp khớp khi phát.

**Bẫy:** ghép wav thì timestamp của đoạn thứ 2 trở đi **phải cộng offset**. Quên là phụ
đề lệch dần về cuối video — lỗi này nhìn không ra lúc test đoạn ngắn.

**Song song:** ✅ chạy cùng P3.S1 được.

---

### [x] P3.S3 — Khối visual — ✅ **PASS** (2026-08-14, SDXL-Lightning 8,2s/ảnh · VRAM đỉnh 624 MiB, `research/probes/p3s3-sdxl.md`)

**Mục tiêu:** shot list → ảnh/clip cho từng shot.

**Ngữ cảnh:** chạy trên 2060 6GB. Hai tầng: **SDXL-Lightning** (~10s/ảnh) làm mặc định,
**Flux.1-schnell Q4** (~2 phút/ảnh) cho 1–2 ảnh "hero". LTX-2B chỉ dùng nếu P1.S4 pass.
Nội dung về AI rất hợp **screen-record / data-viz** — terminal, biểu đồ benchmark,
screenshot HF — loại này deterministic, miễn phí, và đúng chủ đề hơn ảnh AI generic.

**Đọc trước:** `research/probes/p1s4-ltx.md` · `configs/models.yaml` · `configs/style.yaml`

**Việc:**
1. `src/create_video/visual/sdxl.py` — mặc định
2. `src/create_video/visual/flux.py` — ảnh hero
3. `src/create_video/visual/ltx.py` — **chỉ khi P1.S4 pass**
4. `src/create_video/visual/screencast.py` — matplotlib cho biểu đồ, asciinema/playwright
   cho terminal và screenshot
5. `src/create_video/visual/router.py` — chọn backend theo `shot.kind` trong script
6. ⚠️ **Giải phóng VRAM sau mỗi backend** (`del model; torch.cuda.empty_cache()`) —
   6GB không cho giữ hai model cùng lúc

**Xong khi:** shot list 8 shot → 8 asset trong `out/<id>/shots/`; VRAM đỉnh < 6GB;
tổng thời gian < 20 phút. Ghi số đo vào `research/probes/p3s3-visual.md`.

**Bẫy:** quên `empty_cache()` giữa các backend → OOM ở shot thứ 3–4, và lỗi trông như
ngẫu nhiên nên rất khó truy. Viết test nạp lần lượt cả ba backend trong một tiến trình.

**Song song:** ❌ chiếm GPU — chạy một mình.

---

### [x] P3.S4 — Nối một lệnh đầu-cuối — ✅ **xong** (2026-08-14, ~7 phút/video, T1 11/11, `research/probes/p3s4-pipeline.md`)

> **Đã chạy 2 vòng phản hồi với Tony** (2026-08-14, `research/06-nhip-va-font.md`):
> font → **Anton**, giọng → **Thanh Bình** (nam, Bắc) — cả hai giữ.
> Nhịp nhanh (shot 2-4s, video 35s, câu 4-12 từ) đã **hoàn về cũ** (3-8s, 45s, 5-16 từ)
> vì làm giọng đọc nghe máy móc. T1 thêm kiểm thứ 11 "shot có ảnh" sau khi một video
> lọt qua 10/10 với 12 giây cuối không có hình.

**Mục tiêu:** một lệnh, một chủ đề, ra một mp4.

**Đọc trước:** tất cả step P2 và P3 phía trên

**Việc:**
1. `src/create_video/queue/` — state machine trên đĩa: mỗi video là một thư mục
   `out/<id>/` với `state.json` ghi bước hiện tại
2. **Tuần tự hoá job chiếm GPU** — đây là ràng buộc thật của 6GB, không phải tối ưu
3. `scripts/make_video.py --topic "..."` chạy hết chuỗi
4. Chạy lại được từ đúng bước hỏng, không render lại từ đầu

**Xong khi:** `python scripts/make_video.py --topic "Claude Opus 5"` → mp4 qua được T1.
Giết tiến trình giữa chừng rồi chạy lại → tiếp đúng chỗ dừng.

**Bẫy:** đừng để state trong RAM. Render mất hàng chục phút và sẽ chết giữa chừng —
state trên đĩa là lý do tồn tại của cả khối `queue/`.

**Song song:** ❌ phụ thuộc mọi step trên.

---

### [x] P3.S5 — Metadata cho TikTok: caption, hashtag, nhãn AI — ✅ **xong** (2026-08-21, `out/test-p3s5/post.json`)

**Mục tiêu:** mỗi video kèm caption có từ khoá, 3–5 hashtag ngách, và cờ "cần bật nhãn AI".

**Ngữ cảnh:** TikTok index **caption, hashtag, chữ trên hình VÀ lời nói** (hơn 3 tỉ lượt
tìm/ngày, `research/07-len-xu-huong.md`). Pipeline hiện sinh video nhưng **không sinh
caption, không sinh hashtag** — bỏ trắng một nửa tín hiệu tìm kiếm. Đây là việc có tỉ lệ
lợi/công cao nhất trong mọi việc còn lại: agent đã viết kịch bản thì viết thêm caption
gần như miễn phí.

**Đọc trước:** `research/07-len-xu-huong.md` (mục 4 và 5) · `src/create_video/agents/scriptwriter.py`

**Việc:**
1. `Script` có thêm `caption` (≤ 150 ký tự cho câu đầu — TikTok cắt ở đó), `hashtags`
   (3–5, ngách, **không** `#fyp` `#viral`), `keywords` (để nhét vào caption và overlay)
2. Ghi vào `video-spec.json` ở `meta` (schema phải nới) và ra `out/<id>/post.json`
3. `post.json` có cờ `requires_ai_label: true` — **luôn true** với pipeline này vì có
   giọng tổng hợp và ảnh AI
4. Bot Telegram (P5.S2) hiện caption + hashtag để Tony copy, kèm **một dòng nhắc bật
   nhãn AI trong app**

**Xong khi:** một video ra kèm `post.json` dán được thẳng vào app; caption chứa từ khoá
chính trong 100 ký tự đầu.

**Bẫy:** tự bật nhãn AI **không** làm giảm phân phối (TikTok nói rõ), nhưng bị hệ thống
tự gắn nhãn thì **không gỡ được** và nội dung AI không nhãn có thể mất suất For You.
Rủi ro lệch hẳn về một phía — đừng để Tony phải nhớ, phải in ra màn hình mỗi lần.

**Song song:** ✅ chạy độc lập, không đụng khối render.

> **Đã chạy 2026-08-21:** `Script` có thêm `caption`/`hashtags`/`keywords`,
> scriptwriter tự kiểm bằng code (`_check_metadata` — caption ≤150 ký tự, từ
> khoá chính trong 100 ký tự đầu, 3-5 hashtag, cấm `#fyp`/`#viral`), y hệt tinh
> thần `_check` sẵn có. `spec/schema.json` nới thêm 3 trường optional ở `meta`.
> `spec/post.py` (module riêng — post.json không phải ranh giới Remotion) đọc
> `spec["meta"]` ra `out/<id>/post.json` kèm `requires_ai_label: true` luôn
> `true` và `paste_text` dán thẳng. Test thật: `out/test-p3s5/` (T1 11/11, caption
> 76 ký tự, 4 hashtag). Nhắc bật nhãn AI in ra console mỗi lần chạy pipeline —
> bot Telegram (P5.S2) sẽ lặp lại nhắc này khi gửi Tony duyệt.

---

# P3b — Nâng chất lượng ⭐ CHÈN TRƯỚC P4 *(thêm 2026-10-01)*

**Ngữ cảnh phase:** audit + quét lại thị trường ngày 2026-10-01
(`research/08-nang-cap-chat-luong.md`) cho thấy trần chất lượng hiện tại **không nằm ở
model** mà ở: lỗi dựng nhìn thấy được (khung đen khi chuyển cảnh, overlay sai số), giọng
ghép từng câu (27% thời lượng là lặng), và hình ảnh không mang thông tin. Cả ba sửa được
**không thêm VRAM**. Làm phase này trước P4 vì chấm QC 4 tầng trên video đã biết hỏng
là tốn công vô ích.

**Cách đo chung cho cả phase:** sau mỗi step đổi khối render, render lại 3 fixture
`eval/scripts/` → `eval/results/<ngày>-p3b-sN.md` (không ghi đè) + một video thật cùng
chủ đề với `out/demo-02` để Tony xem/nghe so trước-sau. Ngưỡng mới viết sẵn ở
`research/08` §6 — **đã viết trước khi chạy**.

### 📋 Prompt mở phiên — P3b

```
Dự án: exp-create-video — hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/08-nang-cap-chat-luong.md — audit + quét thị trường 2026-10-01,
     lý do của cả phase này
  3. research/05-decision.md — lựa chọn kiến trúc gốc

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB (Turing, fp16, KHÔNG FP8/bf16), RAM 31GB. GPU dùng
    chung với dự án khác — chạy nvidia-smi trước mọi bước GPU, không kill job lạ.
  - Chi phí 0đ. Chỉ model open-weight chạy local. Không API trả tiền.
  - video-spec.json là ranh giới DUY NHẤT giữa Python và Remotion. Thêm kind/trường
    mới thì sửa CẢ schema.json lẫn remotion/src/types.ts.
  - Ngưỡng ở configs/thresholds.yaml viết TRƯỚC, không sửa sau khi thấy kết quả.
    Kiểm mới thì ngưỡng phải có trong research/ trước khi chạy.
  - QC tầng 1 KHÔNG dùng LLM.
  - Đổi khối render → render lại 3 fixture eval/scripts/, ghi
    eval/results/<ngày>-<tên>.md, KHÔNG ghi đè, KHÔNG sửa fixture.
  - Agent SDK là `claude-agent-sdk` (gọi query()), KHÔNG phải tool_runner của `anthropic`.
  - Tony tự quản git. KHÔNG commit hộ.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

VIỆC LẦN NÀY: Phase 3b — nâng chất lượng video.

Mục tiêu phase: video Tony muốn bấm Đăng. Trần chất lượng nằm ở dựng, giọng và
hình không mang thông tin — không ở model (research/08).

Làm step: P3b.S<n>. Mở todos.md, đọc đúng khối step đó.

QUY TẮC RIÊNG CỦA P3b:
  - Giọng tự nhiên > nhịp nhanh (Tony đã bác nhịp nhanh 2026-08-14). Mọi thay đổi
    làm TĂNG số mối ghép audio đều phải hỏi lại.
  - Phán xử thẩm mỹ là việc của Tony: luôn dựng mẫu thật để Tony xem/nghe, so với
    out/demo-02 (bản "trước"). Nghe so thì làm mù (xem out/p3b-nghe-mu/).
  - Kết đợt: cập nhật todos.md, liệt kê 2-3 hướng tiếp kèm khuyến nghị, rồi DỪNG.

RÀNG BUỘC GPU: S8 (model ảnh) chiếm GPU, chạy MỘT MÌNH. S1/S4/S5/S7 không GPU.
```

**Đã cắt khỏi lộ trình (2026-10-01, Tony chốt "bỏ phase không cần thiết"):**
- **P6 cả phase** — luồng 2 (footage của Tony) là sản phẩm khác, không phục vụ "tự tạo
  video"; audit direct-post chỉ bỏ một chạm tay, không thêm chất lượng. Đăng giữ **draft**.
  Bản cũ: `git show HEAD:todos.md` hoặc backup ngày 2026-10-01.
- **P3b.S9 (LTX offload)** — cơ hội thấp (`research/08` §4); video local đóng hẳn.

### [x] P3b.S1 — Sửa lỗi dựng hiển nhiên — ✅ **xong** (2026-10-01, `eval/results/2026-10-01-p3b-s1.md`)

> Pixel đen trong transition 58% → **4%**; viền đen 24–32px → **0** trên cả 3 fixture
> (không sửa fixture); overlay đúng câu 5/5 (demo-02: 3/5 sai/mất). T1 thêm 3 kiểm
> (loudness, viền đen, đứng hình) — đã chạy trên video cũ để chắc nó **bắt được**
> lỗi đã biết, và hiệu chỉnh detector viền sau một lần báo nhầm mặt bàn tối (độ lệch
> < 1,0 thay vì < 3). Overlay giờ là `overlays[]` có thời gian riêng (schema 1.1),
> scriptwriter gắn overlay theo **câu**. Còn sót: từ karaoke tô sáng ăn mất khoảng
> trắng → P3b.S5.

**Mục tiêu:** không còn frame đen, overlay đúng chỗ, frame 0 dùng được làm thumbnail.

**Đọc trước:** `research/08-nang-cap-chat-luong.md` §1 · `remotion/src/Video.tsx` ·
`components/{KenBurns,Transition,Hook,Overlay}.tsx` · `spec/build.py` · `pipeline.py`

**Việc:**
1. Ken Burns: scale tối thiểu ≥ `1 + 2·|x_pct|/100` (`build.py:139-143`); thêm easing
   (`KenBurns.tsx:29`); đa dạng chuyển động (push-in, pull-out, pan dọc) thay xoay vòng
2. Transition: cho Sequence **chồng nhau** `duration_frames` để shot cũ còn nằm dưới
   (`Video.tsx:43`, `Transition.tsx`)
3. Overlay: script gắn `line_idx` cho mỗi overlay; map theo **thời điểm câu chứa con số**,
   không theo chỉ số shot; cho nhiều overlay/shot (`pipeline.py:176-179`, `build.py:239-245`)
4. Hook: frame 0 opacity = 1, có band tương phản sau chữ, punch-zoom nhẹ (`Hook.tsx`)
5. Lặt vặt: `Overlay.tsx:49` weight 800→400 (Anton chỉ có 400); `remotion.config.ts`
   JPEG quality 95 + đặt CRF; `pyproject.toml` `testpaths=["tests"]`; chạy lại `_check`
   khi dùng lại `script.json` cache (`pipeline.py:85`); dọn chữ "Be Vietnam Pro" sót
6. T1 thêm 2 kiểm (code, không LLM): **dải viền đen > 4px** ngoài transition, và **đoạn
   tĩnh > 2,0s**. Ngưỡng ở `research/08` §6 → thêm vào `thresholds.yaml` kèm comment ngày

**Xong khi:** 3 fixture + demo render lại: 0 frame có viền đen (kiểm mới), overlay đúng
câu ở 100% trường hợp trên demo, T1 pass. Test đơn vị cho mapping overlay.

**Bẫy:** chồng Sequence làm tổng frame dài ra nếu cộng duration ngây thơ — tổng thời
lượng phải vẫn bằng audio. T1 `check_caption_timing` sẽ báo nếu lệch.

**Song song:** ✅ không GPU.

---

### [~] P3b.S2 — Giọng: đọc cả đoạn, nghỉ theo dấu câu, chuẩn loudness — *code xong, chờ Tony nghe mù (2026-10-01)*

> Ba biến thể dựng xong: `out/p3b-{a,b,c}/video.mp4`; nghe mù `out/p3b-nghe-mu/X,Y,Z.wav`.
> Loudnorm −14 LUFS chạy trong pipeline (demo-02: −20). B (`grouped`) ít lặng nhất
> (7,4s so với 9,5s) và nhanh nhất. **Phát hiện phụ:** TTS lặp nguyên câu ở seed 7 →
> thêm chốt đọc lại tự động. Số đo: `research/probes/p3b-s2-giong.md`. Tony chọn xong
> thì đặt `tts.echo.join.mode` trong `configs/models.yaml` và đóng step.

**Mục tiêu:** đóng nợ "giọng chưa tự nhiên" (ưu tiên cao từ 2026-08-14).

**Ngữ cảnh:** đo demo-02: 21 khoảng lặng, 9,9s/36,2s. VieNeu v3 Turbo vẫn ngang nhóm đầu
các model dùng thương mại được (WER 3,3% [ViTTS-Bench, 2026-09]) → **đổi cách gọi trước,
chưa đổi model**.

**Đọc trước:** `voice/echo.py` · `spec/captions.py` · `research/06-nhip-va-font.md` ·
memory "giọng tự nhiên > nhịp nhanh"

**Việc:** dựng 3 biến thể cùng kịch bản trên 3 fixture:
- **A** hiện tại (từng câu + 0,28s)
- **B** gộp 2–3 câu / một lần gọi (hoặc cả đoạn), cắt lại span câu từ timestamp aligner
- **C** từng câu, trim đệm đầu/đuôi, nghỉ theo dấu câu (phẩy 0,12s · chấm 0,35s) + crossfade 30ms
Sau đó: `loudnorm` 2-pass `I=-14:TP=-1.5` lên voice; T1 thêm kiểm LUFS (ngưỡng `research/08` §6);
`split_spoken_by_lines` phải chịu được aligner tách token khác (fallback, không raise).

**Xong khi (viết trước):** Tony nghe mù chọn B hoặc C hơn A ở ≥ 2/3 fixture; aligner khớp
100% từ trên biến thể thắng; wall-time TTS ≤ 1,5× A. Fail = Tony không nghe ra khác →
vấn đề ở model/giọng, mở probe VoxCPM2 Q8. Ghi `research/probes/p3b-s2-giong.md`.

**Bẫy:** gộp câu làm câu TTS dài → nhớ memory: kiểm số mối ghép **giảm**, không tăng.
`seed=None` → cố định seed để so công bằng.

**Song song:** ✅ CPU (VieNeu ONNX) — nhưng aligner chiếm ~1,9GB GPU.

---

### [~] P3b.S3 — Phát âm thuật ngữ tiếng Anh — *máy đo xong, chờ Tony nghe 12 từ (2026-10-01)*

> Đọc thô tốt nhất (ASR 18/30), phiên âm Việt 8/30, `<en>` vô dụng/hại. Đã có
> `configs/pronounce.yaml` (thay chuỗi đọc, chữ hiển thị giữ gốc) + danh sách `avoid`
> đưa vào prompt scriptwriter. Tony nghe `out/p3b-phat-am/NGHE.md`. Số đo:
> `research/probes/p3b-s3-phat-am.md`.

**Mục tiêu:** "model", "fine-tune", "benchmark"… đọc đúng (rủi ro mở #6 của `05-decision`).

**Việc:** 30 thuật ngữ trong câu tiếng Việt × 3 biến thể: chữ thô · `<en>…</en>` (sea-g2p) ·
respelling từ `configs/pronounce.csv` (định dạng kiểu VietNormalizer). Tony duyệt từng mục
CSV; tiền xử lý chạy trong `voice/` trước khi gọi TTS, **caption vẫn hiện chữ gốc**.

**Xong khi (viết trước):** ≥ 25/30 Tony chấp nhận ở ít nhất một biến thể, không làm sai âm
tiết Việt liền kề (bug sea-g2p #23). Ghi `research/probes/p3b-s3-phat-am.md`.

**Bẫy:** respelling làm lệch aligner (lời đọc ≠ chữ hiển thị) — align theo **chữ đã
respell**, rồi map ngược về chữ gốc theo vị trí.

**Song song:** ✅ sau S2 (cùng file `echo.py`).

---

### [ ] P3b.S4 — Shot "bằng chứng": stat / chart / screenshot / code

**Mục tiêu:** hình ảnh mang thông tin thật thay ảnh AI chung chung — trả nợ việc 4–5 của
P3.S3 (đánh PASS nhưng `screencast.py`, `router.py` chưa từng được viết).

**Ngữ cảnh:** Relevance + Density là predictor "slop" mạnh nhất [Shaib, 2026-01]; chữ-khác-
lời là factor 9,1% [Gupta, 2025-12]. 0 VRAM.

**Việc:**
1. `schema.json` + `types.ts`: `asset.kind` thêm `stat` (`{value, unit, label}` — số đếm lên,
   scale-pop) · `chart` (bar benchmark từ dữ liệu) · `screenshot` · `code`
2. Component Remotion cho từng kind (theo ranh giới spec — Python không gọi Remotion)
3. `visual/screenshot.py` — Playwright chụp **element** trên trang model card HF, README
   GitHub, abs arXiv; cache theo URL
4. `visual/router.py` — chọn backend theo `shot.kind` do scriptwriter chỉ định; SDXL thành
   nền/b-roll, không còn là mặc định cho mọi shot
5. Scriptwriter: mỗi shot khai `kind` + dữ liệu; luật: ≥ 1/3 shot là kind "bằng chứng"

**Xong khi (viết trước):** Playwright chụp ≥ 18/20 URL thật, < 10s/URL, không dính cookie
banner/login wall, chữ đọc được ở bề rộng 1080px. Một video demo có ≥ 3 kind khác nhau,
Tony xem so với demo-02. Ghi `research/probes/p3b-s4-bang-chung.md`.

**Bẫy:** pháp lý — figure arXiv mặc định **không** được dùng lại (chỉ bài CC); logo là
trademark, chỉ để nhận diện. Chụp trang abs/metadata thì an toàn hơn.

**Song song:** ✅ không GPU.

---

### [ ] P3b.S5 — Caption theo cụm + nhấn từ khoá

**Việc:** chia `captions[]` theo cụm 1–3 từ (xem `createTikTokStyleCaptions` của
`@remotion/captions`, `breakOnSilenceAfterMilliseconds`), cụm lớn giữa khung, pop-in, bỏ
làm mờ từ đã đọc; trường `emphasis[]` do scriptwriter gắn (con số, tên model) → đổi màu.

**Xong khi:** 3 fixture T1 pass (vùng an toàn cả hai kiểm); render không chậm hơn mốc
2026-08-14 quá 30% (mốc ghi nhận chi phí nằm ở số phần tử chữ). Tony xem so.

**Bẫy:** cụm ngắn đổi nhanh có thể vượt 10 từ/s ở đoạn đọc nhanh — giữ mỗi cụm ≥ 0,3s.

**Song song:** ✅ không GPU, nhưng đụng `KaraokeCaption.tsx` + `build.py` như S1 → làm sau S1.

---

### [ ] P3b.S6 — Sound design: SFX + nhạc + ducking

**Ngữ cảnh:** audio energy là factor số 1 (12,4%) [Gupta, 2025-12]. Nợ "nhạc nền" chưa
quyết — **Tony chọn**: (a) ACE-Step 1.5 sinh tại chỗ (MIT, output thương mại được),
(b) thư viện tĩnh CC0, (c) để trống, Tony thêm nhạc trend trong app (draft cho phép).

**Việc:** SFX CC0 (Kenney) vào `assets/sfx/` (có trong repo); spec thêm `sfx[]`
`{at_ms, kind}` — whoosh ở transition, pop ở stat; nhạc theo lựa chọn trên; ducking theo
`words[]` (gain theo frame) hoặc `sidechaincompress` phía Python.

**Xong khi (viết trước):** mix cuối −14 ±1,5 LUFS, TP ≤ −1,0 dBTP; Tony không thấy nhạc
lấn giọng ở cả 3 fixture. Nếu chọn (a): VRAM đỉnh ≤ 5,5GB, ≤ 180s cho 45s nhạc (lần 2–3);
fail thì lùi về (b). Ghi `research/probes/p3b-s6-am-thanh.md`.

**Song song:** (a) ❌ chiếm GPU · (b)(c) ✅

---

### [ ] P3b.S7 — Kịch bản có nguồn + cấu trúc beat

**Mục tiêu:** kịch bản cụ thể, đúng, không giọng "AI" — đòn bẩy lớn nhất cho `approve_rate`.

**Việc:**
1. "Source pack": trước khi viết, gom trích dẫn thô (model card, README, abs) vào
   `out/<id>/sources/` — cùng Playwright của S4; scriptwriter chỉ được dùng số có trong pack
2. Luật cứng (code-checked trong `_check`): ≥ 1 câu quan sát trực tiếp lấy từ
   `research/probes/` (`research/07` §3); mọi con số trên màn hình có nguồn trong pack
3. Script xuất `beats[]` có `role` (hook/setup/reveal/twist/loop); câu cuối nối về hook
4. Danh sách cụm "tic" tiếng Việt cấm dùng (kiểu Antislop), sinh trong context mới

**Xong khi:** 5 chủ đề thật, Tony đọc kịch bản (chưa cần render) và chấm ≥ 4/5 "đăng được
về nội dung". Không phải T4 — T4 vẫn ở P4.S3.

**Bẫy:** đừng cho scriptwriter WebSearch tự do — nguồn không kiểm soát là đúng thứ T4 phải bắt.

**Song song:** ✅

---

### [~] P3b.S10 — Ảnh "sống": parallax 2.5D + nhấn chuyển động theo từ khoá *(thêm 2026-10-01)* — *parallax xong, chờ Tony so p3b-d với p3b-b*

> Depth 0,48s/ảnh · 211 MiB · render +34% · T1 14/14 — mọi ngưỡng máy đo PASS.
> Bật mặc định (`style.yaml motion.parallax: true`). Phần zoom-punch/light leak chưa
> làm — chờ Tony xem parallax trước. `research/probes/p3b-s10-chuyen-dong.md`.

**Mục tiêu:** Tony: "ảnh chưa sinh động". Ken Burns trên ảnh tĩnh là toàn bộ chuyển
động hiện có; S4/S8 làm ảnh *đúng* và *đẹp* hơn nhưng không làm ảnh *động*.

**Ngữ cảnh:** research `research/09-chuyen-dong.md`. Sinh video vẫn ngoài tầm 6GB.
Rẻ nhất mà "sống" nhất: depth map (Depth Anything V2-**Small**, Apache — Base/Large là
NC, cấm) + shader dịch pixel theo độ sâu ngay trong Remotion. Cộng nhấn theo word
timestamp đã có (zoom-punch vào con số/tên riêng) và light leak ở chỗ chuyển shot.
Bằng chứng: motion/frame variance 10,7% SHAP [Gupta, 2025-12] — tương quan, không nhân quả.

**Việc:**
1. `visual/depth.py` — DA-V2-Small, ảnh → `depth/NN.png` (16-bit gray), nhả VRAM sau
2. Spec: `asset.depth_path` (optional), `motion.type: "parallax"` (đã có trong enum)
3. `components/DepthParallax.tsx` — WebGL canvas: dịch uv theo (depth − focus) × biên độ
   nhỏ, quỹ đạo dolly/orbit; lùi về Ken Burns nếu không có depth
4. Nhấn: zoom-punch ảnh 0,25s tại từ có trong `overlays`/số/tên riêng; light leak ở cut

**Xong khi (VIẾT TRƯỚC KHI CHẠY, 2026-10-01):**
- depth ≤ 10s/ảnh, VRAM đỉnh ≤ 1,5GB (lần 2–3)
- render 3 fixture ≤ +50% so với `eval/results/2026-10-01-p3b-s1.md`, T1 không fail thêm
- shot có rách/kéo giãn mép thấy rõ khi xem 1× ≤ 1/3 (Tony hoặc soi frame)
- Tony chọn bản mới hơn Ken Burns ở ≥ 2/3 cặp so sánh
Ghi `research/probes/p3b-s10-chuyen-dong.md`.

**Bẫy:** biên độ lớn → mép vật bị kéo như kẹo; giữ ≤ 2–3% bề rộng. WebGL trong Chrome
headless cần `--gl` đúng (angle/swangle). Shake/punch chỉ áp lên lớp ảnh, KHÔNG lên phụ đề.

**Song song:** depth chiếm GPU (nhỏ); phần Remotion không GPU.

---

### [ ] P3b.S8 — Probe model ảnh: Nunchaku INT4 (FLUX.1-schnell / Z-Image-Turbo)

**Mục tiêu:** ảnh nền nét hơn, đúng chủ đề hơn SDXL-Lightning. **Làm sau S4** — khi shot
"bằng chứng" đã gánh phần thông tin, ảnh AI chỉ còn là nền.

**Ngữ cảnh:** Nunchaku hỗ trợ Turing chính thức (FLUX chạy trên 2080S, issue #801).
Z-Image-Turbo có báo NaN fp16 trên 2060 (issue #15, đang mở). Qwen-Image INT4 crash sm_75 → loại.

**Xong khi (viết trước):** 0/10 ảnh đen/NaN ở 768×1344; VRAM đỉnh < 5,6GB, RAM < 24GB;
≤ 30s/ảnh (lần 2–3); Tony so mù với SDXL trên 3 fixture và chọn model mới ở ≥ 2/3.
Fail: > 60s/ảnh hoặc NaN. Kèm: seed ngẫu nhiên theo video (ghi vào spec), style theo
"archetype" thay `STYLE_SUFFIX` cố định. Ghi `research/probes/p3b-s8-anh.md`.

**Bẫy:** kiểm `nvidia-smi` trước khi chạy — GPU dùng chung với dự án khác.

**Song song:** ❌ chiếm GPU.

---

# P4 — Vòng lặp QC đầy đủ

**Ngữ cảnh phase:** T1 đã có từ P2.S3. Phase này thêm T2/T3/T4 và vòng lặp sửa.
Bốn nguyên tắc thiết kế (nguồn ở `02-sources.md`):

1. **Tách hẳn Producer/Critic** — critic là agent riêng, prompt là *"tìm cái sai"*,
   không phải *"làm lại"*. Không để scriptwriter tự chấm bài mình
2. **Neo vào tín hiệu đo được** — T1 là code, và là tầng duy nhất chặn cứng được
3. **Chặn 2 vòng** — vòng 1 bắt lỗi hiển nhiên, vòng 2 bắt lỗi tinh, vòng 3 hiếm khi
   đáng tiền. Thiếu điều kiện dừng là nguồn đốt token lớn nhất trong hệ multi-agent
4. **Ghi vết** — sau 20 video mới biết tầng nào thật sự có ích

### 📋 Prompt mở phiên — P4

```
Dự án: exp-create-video — hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/05-decision.md — mọi lựa chọn kiến trúc và lý do
  3. research/00-problem.md  — metric và "đủ tốt" bằng số

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB, 12 core, RAM 31GB. tris mặc định TẮT.
  - 6GB không cho nạp visual (~5-6GB) và VLM (~4GB) cùng lúc. Phải
    torch.cuda.empty_cache() trước khi sang bước sau.
  - Chi phí 0đ. Chỉ model open-weight chạy local. Không API trả tiền.
  - video-spec.json là ranh giới DUY NHẤT giữa Python và Remotion.
    Không viết code Python gọi thẳng Remotion hay ngược lại.
  - Ngưỡng ở configs/thresholds.yaml viết TRƯỚC, không sửa sau khi thấy kết quả.
  - Agent SDK là `claude-agent-sdk` (pip install claude-agent-sdk, gọi query()).
    KHÔNG phải client.beta.messages.tool_runner của SDK `anthropic` — hay bị lẫn.
  - Tony tự quản git. KHÔNG commit hộ, kể cả khi thấy tiện.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

VIỆC LẦN NÀY: Phase 4 — vòng lặp QC đầy đủ.

Mục tiêu phase: agent tự chấm video và sửa tối đa 2 vòng trước khi gửi Tony duyệt.
QC tầng 1 (kỹ thuật, bằng code) đã có từ P2.S3. Phase này thêm tầng 2/3/4 và vòng lặp.

BỐN NGUYÊN TẮC THIẾT KẾ — đây là phần dễ làm sai nhất, đọc kỹ:
  1. TÁCH HẲN Producer/Critic. Critic là agent riêng, prompt là "TÌM CÁI SAI",
     không phải "làm lại cho hay hơn". Không để scriptwriter tự chấm bài mình —
     đó là thiên lệch có cấu trúc.
  2. NEO VÀO TÍN HIỆU ĐO ĐƯỢC. Tầng 1 là code (ffprobe/OpenCV), và là tầng duy nhất
     chặn cứng được bằng số. Tầng 4 neo vào raw_quote trong trends.jsonl, không để
     LLM tự nhớ.
  3. CHẶN 2 VÒNG — hằng số CỨNG trong code, không chỉ nằm ở config. Vòng 1 bắt lỗi
     hiển nhiên, vòng 2 bắt lỗi tinh, vòng 3 hiếm khi đáng tiền. Vòng lặp không có
     trần là nguồn đốt token lớn nhất trong hệ multi-agent production.
  4. GHI VẾT vào out/<id>/qc/round-<n>.json. Sau 20 video mới biết tầng nào thật sự
     bắt được lỗi, tầng nào chỉ đốt token.

QUYỀN CỦA TỪNG TẦNG (đừng nhầm):
  T1 kỹ thuật  -> CHẶN CỨNG        (code, 0 LLM)
  T2 hình ảnh  -> đề xuất render lại đúng shot đó, không render lại cả video
  T3 sức hút   -> đề xuất sửa script, KHÔNG chặn
  T4 sự thật   -> CHẶN CỨNG nếu mâu thuẫn trực tiếp với nguồn
Hết 2 vòng mà chưa đạt thì VẪN gửi Tony kèm danh sách lỗi còn lại.
Critic đề xuất, không quyết định.

Làm step: P4.S<n>. Mở todos.md, đọc đúng khối step đó.

BẪY LỚN NHẤT: VLM và LLM đều hay "chê lấy lệ" — chấm gì cũng tìm ra lỗi. Ngưỡng ở
configs/thresholds.yaml đặt CAO có chủ ý. Chỉnh ngưỡng bằng cách chạy trên mẫu TỐT
đã biết, xem có bị chê oan không — đừng chỉnh bằng cảm giác.

RÀNG BUỘC GPU: P4.S1 (T2 VLM) chiếm GPU, chạy một mình.
P4.S2 (T3) và P4.S3 (T4) không đụng GPU, song song được.
```

---

### [ ] P4.S1 — T2: chất lượng hình ảnh bằng VLM

**Mục tiêu:** phát hiện shot hỏng trước khi Tony phải xem.

**Ngữ cảnh:** Qwen3-VL local (~4GB). ⚠️ **Chạy sau khi khối visual đã nhả VRAM** — 6GB
không cho hai model cùng lúc. Chấm từng shot, không chấm cả video.

**Đọc trước:** `configs/thresholds.yaml` · `src/create_video/visual/router.py`

**Việc:**
1. `src/create_video/qc/t2_vlm.py` — cho VLM xem từng shot kèm câu thoại tương ứng
2. Chấm 4 điều: lỗi giải phẫu (tay, mặt) · chữ trong ảnh bị bóp méo · ảnh có khớp câu
   thoại không · chuyển cảnh có giật không
3. Output: `{shot_id, pass, issues[], suggested_prompt_fix}`
4. Fail → gửi patch về `visual/` render lại **đúng shot đó**, không render lại cả video

**Xong khi:** cố tình nhét một ảnh sai chủ đề vào → T2 bắt được và chỉ đúng shot.

**Bẫy:** VLM rất hay "chê lấy lệ" — chấm gì cũng tìm ra lỗi. Ngưỡng phải đủ cao để chỉ
bắt lỗi thật, nếu không mọi video đều tốn 2 vòng sửa vô ích. Chỉnh ngưỡng bằng cách chạy
trên 5 shot **tốt** đã biết, xem có bị chê oan không.

**Song song:** ❌ chiếm GPU.

---

### [ ] P4.S2 — T3: sức hút nội dung

**Mục tiêu:** chấm hook, nhịp, chất lượng tiếng Việt, CTA.

**Ngữ cảnh:** **tầng chủ quan nhất** trong bốn tầng — vì vậy phải có rubric viết sẵn ở
`configs/rubric.md`, không để LLM tự nghĩ ra tiêu chí. Critic **đề xuất, không quyết
định**: fail ở đây không chặn video, chỉ gửi patch về scriptwriter.

**Đọc trước:** `configs/rubric.md` · `src/create_video/agents/scriptwriter.py`

**Việc:**
1. `src/create_video/qc/t3_appeal.py` — prompt là *"tìm cái sai"*, tuyệt đối không phải
   *"viết lại cho hay hơn"*
2. Chấm theo rubric: hook 3 giây có giữ được không · câu tiếng Việt có lủng củng /
   dịch máy không · nhịp có đều đều buồn ngủ không · CTA có rõ không
3. Output: `{score, issues[{where, why, suggested_fix}]}`
4. Fail → patch về `scriptwriter`, render lại từ bước script

**Xong khi:** cho một script cố tình dở (mở đầu bằng "Hôm nay chúng ta sẽ tìm hiểu về…")
→ T3 bắt đúng lỗi hook.

**Hai luật cần thêm vào `configs/rubric.md` khi làm step này** (rút từ
`research/07-len-xu-huong.md`, 2026-08-14):

1. **CTA phải xin LƯU hoặc CHIA SẺ, không xin like.** 2026 TikTok ưu tiên save/share;
   like vô thức gần như không còn giá trị. Rubric hiện chỉ đòi "hành động cụ thể".
2. **Mỗi video phải có ít nhất một câu quan sát TRỰC TIẾP** — "tôi chạy thử", "tôi đo
   được" — và nguồn phải là `research/probes/`, không phải web. Đây là thứ duy nhất
   phân biệt kênh này với AI slop, mà AI slop thì đang bị người xem phản ứng thật
   (90% người nghe muốn nội dung do người làm). Dự án này có lợi thế hiếm: nó **thật sự**
   có số đo của chính Tony trên con 2060.

**Bẫy:** đừng để T3 tự viết lại script — đó là việc của producer. Critic vừa chấm vừa
sửa thì mất luôn tính độc lập, và đó chính là thiên lệch có cấu trúc mà nguyên tắc 1
muốn tránh.

**Song song:** ✅ chạy cùng P4.S3 được.

---

### [ ] P4.S3 — T4: độ chính xác sự thật

**Mục tiêu:** không để video sai tên model, sai con số, sai ngày.

**Ngữ cảnh:** nội dung về AI **rất dễ sai** — tên model, benchmark, ngày phát hành đổi
liên tục. Sai sự thật trên TikTok bị bóc rất nhanh, và mất uy tín khó lấy lại. Vì vậy
T4 **chặn cứng** như T1. Đối chiếu với `trends.jsonl` mà trend-scout đã lưu — đây là
tín hiệu ngoài, không phải LLM tự nhớ.

**Đọc trước:** `research/00-problem.md` (metric `fact_error_rate` = 0) ·
`src/create_video/agents/trend_scout.py` (nếu P5.S1 xong trước)

**Việc:**
1. `src/create_video/qc/t4_facts.py` — bóc mọi khẳng định có thể kiểm được: tên model,
   con số, ngày tháng, tên tổ chức
2. Đối chiếu từng cái với nguồn gốc trong `trends.jsonl`
3. Không đối chiếu được → đánh dấu `unverified`, **không** đoán
4. **Chặn cứng** nếu có mâu thuẫn trực tiếp với nguồn

**Xong khi:** nhét vào script một câu sai (ví dụ sai ngày ra mắt) → T4 chặn và chỉ đúng
câu đó.

**Bẫy:** phân biệt **sai** với **chưa kiểm được**. Chặn cái sai; cái chưa kiểm được thì
gắn cờ cho Tony xem, đừng chặn — nếu không mọi video có nhận định đều bị chặn.

**Song song:** ✅ chạy cùng P4.S2 được.

---

### [ ] P4.S4 — Vòng lặp và ghi vết

**Mục tiêu:** ghép 4 tầng thành vòng lặp có trần cứng và có nhật ký.

**Đọc trước:** cả bốn step P4 trên · `research/05-decision.md` (mục "Vòng lặp QC")

**Việc:**
1. `src/create_video/qc/loop.py`: chạy T1→T4, gom lỗi, gửi patch về đúng agent gây lỗi
   (T2→visual, T3→scriptwriter, T4→scriptwriter), render lại, chấm lại
2. **Trần cứng 2 vòng.** Hết vòng thì **vẫn gửi Tony** kèm danh sách lỗi còn lại
3. Mỗi vòng ghi `out/<id>/qc/round-<n>.json`: điểm từng tầng, lỗi, patch đã gửi
4. `scripts/qc_report.py` — tổng hợp qua nhiều video: tầng nào bắt được lỗi thật, tầng
   nào chỉ đốt token

**Xong khi:** một video đi hết vòng lặp, `out/<id>/qc/` có đủ nhật ký, không bao giờ
quá 2 vòng.

**Bẫy:** vòng lặp không có trần là nguồn đốt token lớn nhất trong hệ multi-agent
production. Trần phải là **hằng số cứng trong code**, không phải config có thể vô tình
đặt thành 99.

**Song song:** ❌ phụ thuộc mọi step P4.

---

### [ ] P4.S5 — Xem lại QC sau 20 video

**Mục tiêu:** biết tầng nào đáng giữ.

**Ngữ cảnh:** đây là step **có chủ ý hoãn** — chỉ làm được sau khi đã có 20 video thật.
Ghi ở đây để không quên.

**Việc:**
1. Chạy `scripts/qc_report.py` trên toàn bộ video đã làm
2. Với mỗi tầng: bao nhiêu lần bắt được lỗi mà Tony cũng thấy là lỗi? Bao nhiêu lần chê oan?
3. Đối chiếu điểm QC với quyết định thật của Tony (`approve_rate`)
4. Tầng nào không tương quan với quyết định của Tony → **bỏ hoặc sửa rubric**

**Xong khi:** `research/04-qc-review.md` có bảng: tầng · số lần bắt đúng · số lần chê oan
· tương quan với `approve_rate` · giữ hay bỏ.

**Bẫy:** cám dỗ lớn nhất là thêm tầng thứ 5 khi thấy chưa đủ. Trước khi thêm, phải chứng
minh 4 tầng hiện có đều đang tương quan với quyết định của Tony.

---

### [ ] P4.S6 — Đo độ dài video nào giữ chân tốt nhất

**Mục tiêu:** trả lời bằng số: 20s, 30s hay 45s?

**Ngữ cảnh:** ngưỡng completion 2026 (reported) là **70%** mới được đẩy mạnh. Video 45
giây phải giữ người xem **31,5 giây**; cắt còn 25 giây thì chỉ cần 17,5 giây. Nhưng ngắn
quá thì không nói đủ ý, và Tony đã bác nhịp nhanh vì nó làm giọng đọc nghe máy móc
(`research/06-nhip-va-font.md`). **Độ dài video** và **nhịp cắt shot** là hai tham số
KHÁC NHAU — có thể cắt ngắn video mà vẫn giữ nhịp thong thả.

**Đọc trước:** `research/07-len-xu-huong.md` (mục 1 và 2) · `.claude/rules/eval-discipline.md`

**Việc:**
1. Cùng **một chủ đề**, dựng 3 bản: `target_duration_sec` = 20 / 30 / 45, nhịp giữ nguyên
2. Đăng cả ba (cách nhau vài ngày, cùng khung giờ) và ghi lại từ TikTok Analytics:
   completion rate, average watch time, save, share, rewatch
3. Ghi vào `eval/results/<ngày>-do-dai.md` — **số thật của TikTok**, không phải cảm nhận

**Xong khi:** có bảng 3 dòng với completion rate thật, và `configs/style.yaml` được đặt
theo bản thắng — kèm lý do ghi vào `research/`.

**Bẫy:** n=3 video **không** đủ để kết luận chắc chắn; TikTok phân phối rất nhiễu. Coi
đây là tín hiệu định hướng, và chỉ đổi khi chênh lệch rõ rệt (>15 điểm completion). Đừng
đổi độ dài mỗi tuần theo video mới nhất — đó là đuổi theo nhiễu.

**Song số phụ thuộc:** cần P5.S3 (đăng được) mới lấy được số.

---

# P5 — Tự động hoá

**Phase song song hoá tốt nhất** — ba step đầu độc lập hoàn toàn, không đụng GPU.
Mở 3 worktree cùng lúc.

### 📋 Prompt mở phiên — P5

```
Dự án: exp-create-video — hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/05-decision.md — mọi lựa chọn kiến trúc và lý do
  3. research/00-problem.md  — metric và "đủ tốt" bằng số

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB, 12 core, RAM 31GB. tris mặc định TẮT.
  - 6GB không cho nạp visual (~5-6GB) và VLM (~4GB) cùng lúc. Phải
    torch.cuda.empty_cache() trước khi sang bước sau.
  - Chi phí 0đ. Chỉ model open-weight chạy local. Không API trả tiền.
  - video-spec.json là ranh giới DUY NHẤT giữa Python và Remotion.
    Không viết code Python gọi thẳng Remotion hay ngược lại.
  - Ngưỡng ở configs/thresholds.yaml viết TRƯỚC, không sửa sau khi thấy kết quả.
  - Agent SDK là `claude-agent-sdk` (pip install claude-agent-sdk, gọi query()).
    KHÔNG phải client.beta.messages.tool_runner của SDK `anthropic` — hay bị lẫn.
  - Tony tự quản git. KHÔNG commit hộ, kể cả khi thấy tiện.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

VIỆC LẦN NÀY: Phase 5 — tự động hoá.

Mục tiêu phase: hệ tự chạy mỗi ngày, Tony chỉ bấm hai nút — chọn chủ đề (sáng) và
duyệt video (tối). P3 đã ra được video bằng một lệnh tay; P5 thay lệnh tay bằng cron
và hai điểm duyệt qua Telegram.

Làm step: P5.S<n>. Mở todos.md, đọc đúng khối step đó.

QUY TẮC RIÊNG CỦA P5:
  - KHÔNG ĐỤNG TIKTOK làm nguồn trend. Research API của TikTok đã siết còn tổ chức
    học thuật, và Creative Center CẤM harvest tự động trong ToS. Trend cần ở đây là
    trend LĨNH VỰC AI (arXiv/HN/GitHub/HF/Reddit — xem configs/sources.yaml),
    không phải trend TikTok.
  - trend-scout PHẢI lưu raw_quote + url cho mỗi mục. Đó là tín hiệu ngoài cho QC
    tầng 4; mất nó thì T4 thành "LLM tự nhớ" — đúng thứ thiết kế QC muốn tránh.
  - Đăng ở chế độ draft (configs/schedule.yaml, publish.mode). Client chưa qua audit
    thì direct post bị ép SELF_ONLY — "thành công" nhưng không ai xem được.
    Giữ draft — audit direct-post đã bỏ khỏi lộ trình (2026-10-01).
  - Cron phải có lock file. Render mất hàng chục phút; hai job cùng lúc trên 6GB
    VRAM là OOM chắc chắn.
  - Token TikTok hết hạn IM LẶNG. Phải có cảnh báo Telegram, nếu không một sáng nào
    đó pipeline chạy xong mà không đăng được, và không ai biết.

SONG SONG: P5.S1 (trend-scout), P5.S2 (Telegram), P5.S3 (TikTok publisher) độc lập
hoàn toàn, không đụng GPU — mở 3 worktree cùng lúc, xem mục "Chạy song song bằng git
worktree" ở đầu todos.md. P5.S4 (cron) phụ thuộc cả ba, làm sau cùng.
```

---

### [ ] P5.S1 — Agent trend-scout

**Mục tiêu:** mỗi sáng có danh sách chủ đề AI đáng làm video.

**Ngữ cảnh:** ⚠️ **Không đụng TikTok.** Research API của TikTok đã siết còn tổ chức học
thuật, và Creative Center **cấm harvest tự động** trong ToS. Trend cần ở đây là trend
**lĩnh vực AI**, không phải trend TikTok — nguồn arXiv/HN/GitHub/HF/Reddit vừa hợp lệ
vừa giàu hơn.

**Đọc trước:** `configs/sources.yaml` · `research/02-sources.md` (mục TikTok API)

**Việc:**
1. `src/create_video/agents/trend_scout.py` — dùng WebSearch/WebFetch của `claude-agent-sdk`
2. Nguồn (đã liệt kê ở `configs/sources.yaml`): arXiv cs.AI/cs.CL mới, HN front page,
   GitHub Trending (Python/AI topic), HuggingFace Papers, r/LocalLLaMA, X từ vài tài khoản
3. Output `out/trends/<date>.jsonl`, mỗi dòng: `{title, url, source, date, summary,
   why_interesting, raw_quote}`
4. **`raw_quote` bắt buộc** — T4 sẽ đối chiếu với nó, không có thì T4 vô dụng

**Xong khi:** chạy một lần → ≥ 20 mục có URL sống, ngày trong 7 ngày gần nhất.

**Bẫy:** đừng để agent tóm tắt rồi vứt nguồn gốc. `raw_quote` + `url` là **tín hiệu ngoài**
cho T4; mất nó thì T4 thành LLM tự nhớ, đúng thứ mà thiết kế QC muốn tránh.

**Song song:** ✅ worktree riêng.

---

### [ ] P5.S2 — Bot Telegram

**Mục tiêu:** hai điểm duyệt của Tony.

**Ngữ cảnh:** Tony duyệt **hai chỗ**: chọn chủ đề (sáng) và duyệt video (tối). Bot phải
gửi được video và nhận nút bấm.

**Đọc trước:** `research/00-problem.md` (mục ràng buộc "Người duyệt")

**Việc:**
1. `src/create_video/publish/telegram_bot.py` — `python-telegram-bot`
2. Điểm duyệt 1: gửi 5 chủ đề kèm lý do → inline keyboard chọn 1
3. Điểm duyệt 2: gửi video + điểm QC + lỗi còn lại → nút
   `[Đăng]` `[Hẹn giờ]` `[Làm lại]` `[Lưu]`
4. `[Làm lại]` cho phép Tony nhắn thêm chỉ dẫn, đẩy lại vào vòng QC
5. Trạng thái lưu trên đĩa — bot chết rồi bật lại vẫn nhớ đang chờ duyệt cái gì

**Xong khi:** gửi được video 1080×1920 qua Telegram, bấm nút đổi được `state.json`.

**Bẫy:** Telegram giới hạn kích thước file bot gửi (~50MB). Video 60s 1080×1920 có thể
vượt — kiểm sớm, nếu vượt thì gửi bản nén để xem duyệt, giữ bản gốc để đăng.

**Song song:** ✅ worktree riêng.

---

### [ ] P5.S3 — Publisher TikTok

**Mục tiêu:** đẩy video đã duyệt vào draft TikTok, hoặc hẹn lịch.

**Đọc trước:** `research/probes/p1s1-tiktok.md` (kết quả probe)

**Việc:**
1. `src/create_video/publish/tiktok.py` — dùng lại code probe P1.S1
2. Sinh caption + hashtag từ `script.json`
3. `[Hẹn giờ]` → ghi vào `out/scheduled.jsonl`, cron kiểm mỗi giờ
4. Refresh token tự động, báo Telegram khi hết hạn

**Xong khi:** bấm `[Đăng]` trên Telegram → video vào draft TikTok trong 2 phút.

**Bắt buộc — nhãn AI:** video của pipeline này có giọng tổng hợp và ảnh do AI sinh, nên
phải bật "AI-generated content". Ở chế độ draft thao tác nằm trong app, do Tony bấm →
**bot Telegram phải in dòng nhắc này mỗi lần gửi duyệt** (P3.S5). Tự bật nhãn KHÔNG giảm
phân phối; bị hệ thống tự gắn thì không gỡ được và có thể mất suất For You.
Chi tiết: `research/07-len-xu-huong.md` mục 4.

**Bẫy:** access token TikTok hết hạn im lặng. Không có cảnh báo thì một sáng nào đó
pipeline chạy xong nhưng không đăng được, mà không ai biết.

**Song song:** ✅ worktree riêng.

---

### [ ] P5.S4 — Cron và nhịp chạy

**Mục tiêu:** hệ tự chạy mỗi ngày, Tony chỉ bấm hai nút.

**Đọc trước:** `configs/schedule.yaml` · mọi step P5 trên

**Việc:**
1. Cron 07:00 → trend-scout → topic-picker → Telegram đề xuất
2. Tony chọn → hàng đợi render nền (chạy ban ngày, không cần vội)
3. Render + QC xong → Telegram gửi duyệt
4. Sổ ghi `out/journal.jsonl`: chủ đề, thời gian render, số vòng QC, quyết định của Tony
5. Cảnh báo Telegram khi job chết

**Xong khi:** chạy cron thủ công một lần → nhận đề xuất → chọn → nhận video, không đụng
tay bước nào khác.

**Bẫy:** đừng để cron chạy chồng job. Render mất hàng chục phút; hai job cùng lúc trên
6GB VRAM là OOM chắc chắn. Dùng lock file.

**Song song:** ❌ phụ thuộc P5.S1–S3.

---

## Nợ kỹ thuật đã biết

Ghi ở đây để không quên, chưa lên lịch:

- [ ] **Nhạc nền** — dùng nhạc CC0 (Pixabay / Free Music Archive) hay để trống rồi Tony
      thêm nhạc trending trong app? Cái sau hợp thuật toán TikTok hơn nhưng phá luồng
      tự động. **Chưa quyết.**
- [ ] **Tài khoản TikTok** — đã có chưa, có phải Business account không? P1.S1 sẽ trả lời.
- [ ] **Tần suất** — 1 video/ngày hay vài video/tuần? Ảnh hưởng tới việc có cần hàng đợi
      render qua đêm không.
- [ ] **Remotion license** — theo dõi ở `research/repo-cards/remotion.md`. Nếu thành vấn
      đề thì chuyển Revideo (MIT); `video-spec.json` giữ nguyên nên đổi được.
- [x] **`eval/scripts/`** — đã có 3 fixture (`scripts/make_eval_fixtures.py` suy ra từ
      một video thật). Cách dùng ở `eval/README.md`.
- [ ] **Font phụ đề không nằm trong repo** *(mới 2026-08-14)* — đang dùng **Anton**
      (`~/.fonts/tiktok/`). Máy khác render sẽ rơi về font hệ thống mà **không báo lỗi**
      — chữ vẫn đủ dấu nên chỉ so hai frame mới thấy. `scripts/setup.sh` tải hộ nhưng
      vẫn phụ thuộc mạng. (Bảng so 5 font `out/font-compare.png` đã chuyển vào thùng
      rác ngày 2026-10-01 — xem mục dọn repo bên dưới.)
      Bebas Neue và Archivo Black **không có** subset vietnamese — đừng thử lại.
- [x] **Ràng buộc "visual chiếm 5-6GB" rộng hơn thực tế** *(đóng 2026-10-01: `machines.yaml`
      và `models.yaml` ghi số đo thật 624 MiB; CLAUDE.md vẫn giữ câu cảnh báo chung)*
      *(mới 2026-08-14)* — đo thật
      P3.S3: SDXL sequential offload chỉ đỉnh **624 MiB**. `configs/machines.yaml` và
      `CLAUDE.md` vẫn ghi theo giả định cũ. Chưa sửa vì con số đó gắn với đúng một cấu
      hình; để P4.S1 (VLM) quyết dựa trên số đo của chính nó.
- [ ] **Giọng đọc nghe chưa tự nhiên** *(mới 2026-08-14, ưu tiên cao)* — Tony nghe
      `out/demo-02`: "không tự nhiên như người nói". Nghi phạm số một là **cách ghép**,
      không phải model: mỗi câu là một lần gọi TTS riêng rồi nối lại kèm 0,28s lặng
      (`voice/echo.py: synth_lines`), nên mọi chỗ nối đều là một lần "lấy hơi" giả và
      ngữ điệu không chảy qua được ranh giới câu. Ba đường thử, theo thứ tự rẻ→đắt:
      1. Gộp 2-3 câu liền nhau thành MỘT lần gọi TTS, rồi cắt caption lại theo kết quả
         align (aligner vốn đã trả timestamp từng từ nên cắt lại không mất gì).
      2. Thử `style: doc_truyen` thay `tu_nhien` — kể chuyện có ngữ điệu mềm hơn.
      3. Chỉnh `gap_sec` theo dấu câu: dấu chấm nghỉ dài, dấu phẩy nghỉ ngắn, thay vì
         một hằng số 0,28s cho mọi chỗ.
      **Cách đo:** đường 1 và 2 làm được mà không đụng phần còn lại của pipeline; dựng
      3 bản cùng kịch bản rồi nghe so — đây là loại chỉ tai người phân xử được.
- [ ] **Kịch bản chưa được kiểm sự thật** *(mới 2026-08-14)* — scriptwriter tự khai
      `sources` nhưng chưa ai đối chiếu. Đây đúng là việc của T4 (P4.S3); tới đó mới
      đóng được.
- [ ] **License giọng VieNeu có thể đã đổi** *(mới 2026-10-01)* — card HF hôm nay ghi
      **Apache-2.0 cho cả preset voice**, cho phép nội dung kiếm tiền (commit 2026-06-30,
      23 preset); `exp-echo` local ghi CC-BY-NC-4.0, 14 preset → nhiều khả năng revision
      cũ. Tony kiểm revision trong exp-echo trước khi kênh kiếm tiền. `research/08` §3.
- [ ] **Tài liệu nói nhiều hơn code** *(mới 2026-10-01, audit)* — P3.S3 đánh PASS nhưng
      `visual/flux.py`, `screencast.py`, `router.py` chưa có (→ P3b.S4/S8); P3.S4 hứa
      `queue/state.json` + `scripts/make_video.py` chưa có; `qc/t2_vlm.py` đã viết nhưng
      không ai gọi, và `research/probes/p4s1-vlm.md` được 3 nơi trỏ tới nhưng không tồn
      tại; `models.yaml: tts.backend` bị bỏ qua (pipeline hardcode `EchoBackend`).
- [x] **Dọn repo** *(2026-10-01, Tony yêu cầu)* — chuyển (KHÔNG `rm`) sang
      `/mnt/data1tb/_trash-exp-create-video-2026-10-01/` (8,2GB, giữ nguyên đường dẫn
      tương đối): `exp/ltx` (LTX đã loại), `exp/tts` (service VieNeu-v2 của P1.S2, đã
      thay bằng exp-echo), `exp/visual` (probe P3.S3 xong), bản trùng Qwen3-ForcedAligner
      trong `exp/hf-cache`, `voice/vieneu.py` (+ DummyBackend chưa từng chạy được),
      package rỗng `queue/` `publish/`, `remotion/src/ProbeVideo.tsx` (mốc đo giờ là 3
      fixture eval), `data/footage` + `notebooks` (P6 đã bỏ), và output cũ trong `out/`:
      `demo-01 p1s2 p1s3 p1s4 p3s3 p4s1 test-p3s5 test-p4s1-sdxl tts voice-compare
      font-compare.png`. Một số probe cũ (`p1s2-tts.md`, `p1-summary.md`, `06-nhip-va-font.md`)
      còn trỏ tới các file đó — đường dẫn vẫn đúng **trong thư mục rác**. Giữ lại:
      `out/demo-02` (mốc "trước"), `out/p3b-*` (chờ nghe), `out/eval-*` (output thô của
      eval), `out/smoke-01` (test dùng), `exp/hf-cache` (trọng số SDXL đang dùng),
      `exp/probes` (`tiktok_draft.py` cho P1.S1), `exp/qc` (probe P4.S1), `exp/tiktok-legal`.
      Tony xem lại rồi tự `rm -rf` thư mục rác khi chắc.
- [x] **HF cache của SDXL không được khai báo ở đâu** *(sửa 2026-10-01)* — trọng số 6,8GB
      ở `exp/hf-cache` nhưng không chỗ nào trong repo trỏ tới; chạy từ terminal mới thì
      tải lại về `~/.cache`. `visual/sdxl.py` và `qc/t2_vlm.py` giờ `setdefault(HF_HOME)`.
