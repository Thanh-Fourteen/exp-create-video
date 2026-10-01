# plan-autoclick.md — file cho tool autoclick đọc

> **Đây KHÔNG phải roadmap.** Roadmap thật là [todos.md](todos.md); file này chỉ là
> danh sách việc còn lại, viết theo đúng định dạng `tool-auto-click` parse được:
> mỗi step một heading `##`, một checkbox, và một khối ``` không nhãn làm prompt.
>
> Prompt bên dưới **copy nguyên văn** từ các khối `📋 Prompt mở phiên` trong todos.md,
> chỉ thay dòng `Làm step:` và bỏ phần hướng dẫn chạy song song. Sinh lại bằng
> `scripts/gen_plan_autoclick.py` nếu todos.md đổi.
>
> **Tool đọc file NÀY để biết step nào xong**, nên checkbox ở đây mới là cái đếm.

---

## P3b.S4 — Shot "bằng chứng": stat / chart / screenshot / code

- [ ] Shot "bằng chứng": stat / chart / screenshot / code

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

Làm step: P3b.S4. Mở todos.md, tìm khối "### [ ] P3b.S4 — Shot "bằng chứng": stat / chart / screenshot / code" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

QUY TẮC RIÊNG CỦA P3b:
  - Giọng tự nhiên > nhịp nhanh (Tony đã bác nhịp nhanh 2026-08-14). Mọi thay đổi
    làm TĂNG số mối ghép audio đều phải hỏi lại.
  - Phán xử thẩm mỹ là việc của Tony: luôn dựng mẫu thật để Tony xem/nghe, so với
    out/demo-02 (bản "trước"). Nghe so thì làm mù (xem out/p3b-nghe-mu/).
  - Kết đợt: cập nhật todos.md, liệt kê 2-3 hướng tiếp kèm khuyến nghị, rồi DỪNG.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P3b.S4" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P3b.S4" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P3b.S5 — Caption theo cụm + nhấn từ khoá

- [ ] Caption theo cụm + nhấn từ khoá

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

Làm step: P3b.S5. Mở todos.md, tìm khối "### [ ] P3b.S5 — Caption theo cụm + nhấn từ khoá" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

QUY TẮC RIÊNG CỦA P3b:
  - Giọng tự nhiên > nhịp nhanh (Tony đã bác nhịp nhanh 2026-08-14). Mọi thay đổi
    làm TĂNG số mối ghép audio đều phải hỏi lại.
  - Phán xử thẩm mỹ là việc của Tony: luôn dựng mẫu thật để Tony xem/nghe, so với
    out/demo-02 (bản "trước"). Nghe so thì làm mù (xem out/p3b-nghe-mu/).
  - Kết đợt: cập nhật todos.md, liệt kê 2-3 hướng tiếp kèm khuyến nghị, rồi DỪNG.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P3b.S5" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P3b.S5" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P3b.S7 — Kịch bản có nguồn + cấu trúc beat

- [ ] Kịch bản có nguồn + cấu trúc beat

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

Làm step: P3b.S7. Mở todos.md, tìm khối "### [ ] P3b.S7 — Kịch bản có nguồn + cấu trúc beat" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

QUY TẮC RIÊNG CỦA P3b:
  - Giọng tự nhiên > nhịp nhanh (Tony đã bác nhịp nhanh 2026-08-14). Mọi thay đổi
    làm TĂNG số mối ghép audio đều phải hỏi lại.
  - Phán xử thẩm mỹ là việc của Tony: luôn dựng mẫu thật để Tony xem/nghe, so với
    out/demo-02 (bản "trước"). Nghe so thì làm mù (xem out/p3b-nghe-mu/).
  - Kết đợt: cập nhật todos.md, liệt kê 2-3 hướng tiếp kèm khuyến nghị, rồi DỪNG.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P3b.S7" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P3b.S7" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P4.S1 — T2: chất lượng hình ảnh bằng VLM

- [ ] T2: chất lượng hình ảnh bằng VLM

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

Làm step: P4.S1. Mở todos.md, tìm khối "### [ ] P4.S1 — T2: chất lượng hình ảnh bằng VLM" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BẪY LỚN NHẤT: VLM và LLM đều hay "chê lấy lệ" — chấm gì cũng tìm ra lỗi. Ngưỡng ở
configs/thresholds.yaml đặt CAO có chủ ý. Chỉnh ngưỡng bằng cách chạy trên mẫu TỐT
đã biết, xem có bị chê oan không — đừng chỉnh bằng cảm giác.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P4.S1" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P4.S1" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P4.S2 — T3: sức hút nội dung

- [ ] T3: sức hút nội dung

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

Làm step: P4.S2. Mở todos.md, tìm khối "### [ ] P4.S2 — T3: sức hút nội dung" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BẪY LỚN NHẤT: VLM và LLM đều hay "chê lấy lệ" — chấm gì cũng tìm ra lỗi. Ngưỡng ở
configs/thresholds.yaml đặt CAO có chủ ý. Chỉnh ngưỡng bằng cách chạy trên mẫu TỐT
đã biết, xem có bị chê oan không — đừng chỉnh bằng cảm giác.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P4.S2" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P4.S2" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P4.S3 — T4: độ chính xác sự thật

- [ ] T4: độ chính xác sự thật

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

Làm step: P4.S3. Mở todos.md, tìm khối "### [ ] P4.S3 — T4: độ chính xác sự thật" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BẪY LỚN NHẤT: VLM và LLM đều hay "chê lấy lệ" — chấm gì cũng tìm ra lỗi. Ngưỡng ở
configs/thresholds.yaml đặt CAO có chủ ý. Chỉnh ngưỡng bằng cách chạy trên mẫu TỐT
đã biết, xem có bị chê oan không — đừng chỉnh bằng cảm giác.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P4.S3" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P4.S3" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P4.S4 — Vòng lặp và ghi vết

- [ ] Vòng lặp và ghi vết

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

Làm step: P4.S4. Mở todos.md, tìm khối "### [ ] P4.S4 — Vòng lặp và ghi vết" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BẪY LỚN NHẤT: VLM và LLM đều hay "chê lấy lệ" — chấm gì cũng tìm ra lỗi. Ngưỡng ở
configs/thresholds.yaml đặt CAO có chủ ý. Chỉnh ngưỡng bằng cách chạy trên mẫu TỐT
đã biết, xem có bị chê oan không — đừng chỉnh bằng cảm giác.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P4.S4" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P4.S4" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P5.S1 — Agent trend-scout

- [ ] Agent trend-scout

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

Làm step: P5.S1. Mở todos.md, tìm khối "### [ ] P5.S1 — Agent trend-scout" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

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

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P5.S1" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P5.S1" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P5.S2 — Bot Telegram

- [ ] Bot Telegram

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

Làm step: P5.S2. Mở todos.md, tìm khối "### [ ] P5.S2 — Bot Telegram" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

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

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P5.S2" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P5.S2" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P5.S3 — Publisher TikTok

- [ ] Publisher TikTok

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

Làm step: P5.S3. Mở todos.md, tìm khối "### [ ] P5.S3 — Publisher TikTok" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

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

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P5.S3" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P5.S3" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P5.S4 — Cron và nhịp chạy

- [ ] Cron và nhịp chạy

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

Làm step: P5.S4. Mở todos.md, tìm khối "### [ ] P5.S4 — Cron và nhịp chạy" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

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

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P5.S4" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P5.S4" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## Không đưa vào đây (tool không làm hộ được)

Những việc còn lại trong todos.md cần Tony ra tay thật, không phải việc gõ code:

- **P1.S1** — TikTok draft API: code xong, chờ phần bấm tay trong app.
- **P3b.S2** — Giọng: Tony nghe mù X/Y/Z ở out/p3b-nghe-mu/ rồi chọn cách ghép.
- **P3b.S3** — Phát âm thuật ngữ: Tony duyệt từng mục từ điển respelling.
- **P3b.S6** — Nhạc nền: Tony chọn ACE-Step / thư viện CC0 / để trống.
- **P3b.S8** — Model ảnh: so mù với SDXL, Tony chấm.
- **P4.S5** — Xem lại QC sau 20 video: phải có 20 video thật đã.
- **P4.S6** — Đo độ dài giữ chân: cần số thật từ TikTok Analytics, tức cần P5.S3 chạy
  và video đã đăng vài ngày.

Mục **Nợ kỹ thuật đã biết** ở cuối todos.md cũng để nguyên đó — phần lớn là câu hỏi
chưa quyết, không phải việc giao được.
