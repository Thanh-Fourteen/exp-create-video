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

- [x] Shot "bằng chứng": stat / chart / screenshot / code

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

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

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

- [x] Caption theo cụm + nhấn từ khoá

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

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

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

## P4.S0 — Xương sống team: `state.json` + bộ chạy vai *(thêm 2026-10-01)*

- [x] Xương sống team: `state.json` + bộ chạy vai *(thêm 2026-10-01)*

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

KIẾN TRÚC TEAM (research/10-team.md §1): mỗi vai = một lần query() context mới +
output_format JSON schema, ghi artifact ra file; cổng giữa các vai là CODE. Không để
một LLM tự sinh subagent điều phối. Làm P4.S0 (xương sống team) TRƯỚC các step khác.

Làm step: P4.S0. Mở todos.md, tìm khối "### [ ] P4.S0 — Xương sống team: `state.json` + bộ chạy vai *(thêm 2026-10-01)*" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

BẪY LỚN NHẤT: VLM và LLM đều hay "chê lấy lệ" — chấm gì cũng tìm ra lỗi. Ngưỡng ở
configs/thresholds.yaml đặt CAO có chủ ý. Chỉnh ngưỡng bằng cách chạy trên mẫu TỐT
đã biết, xem có bị chê oan không — đừng chỉnh bằng cảm giác.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P4.S0" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P4.S0" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P4.S1 — T2: chất lượng hình ảnh bằng VLM

- [x] T2: chất lượng hình ảnh bằng VLM

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

KIẾN TRÚC TEAM (research/10-team.md §1): mỗi vai = một lần query() context mới +
output_format JSON schema, ghi artifact ra file; cổng giữa các vai là CODE. Không để
một LLM tự sinh subagent điều phối. Làm P4.S0 (xương sống team) TRƯỚC các step khác.

Làm step: P4.S1. Mở todos.md, tìm khối "### [ ] P4.S1 — T2: chất lượng hình ảnh bằng VLM" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

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

- [x] T3: sức hút nội dung

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

KIẾN TRÚC TEAM (research/10-team.md §1): mỗi vai = một lần query() context mới +
output_format JSON schema, ghi artifact ra file; cổng giữa các vai là CODE. Không để
một LLM tự sinh subagent điều phối. Làm P4.S0 (xương sống team) TRƯỚC các step khác.

Làm step: P4.S2. Mở todos.md, tìm khối "### [ ] P4.S2 — T3: sức hút nội dung" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

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

## P4.S3 — T4: độ chính xác sự thật (vai **fact-checker**)

- [x] T4: độ chính xác sự thật (vai **fact-checker**)

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

KIẾN TRÚC TEAM (research/10-team.md §1): mỗi vai = một lần query() context mới +
output_format JSON schema, ghi artifact ra file; cổng giữa các vai là CODE. Không để
một LLM tự sinh subagent điều phối. Làm P4.S0 (xương sống team) TRƯỚC các step khác.

Làm step: P4.S3. Mở todos.md, tìm khối "### [ ] P4.S3 — T4: độ chính xác sự thật (vai **fact-checker**)" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

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

- [x] Vòng lặp và ghi vết

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

KIẾN TRÚC TEAM (research/10-team.md §1): mỗi vai = một lần query() context mới +
output_format JSON schema, ghi artifact ra file; cổng giữa các vai là CODE. Không để
một LLM tự sinh subagent điều phối. Làm P4.S0 (xương sống team) TRƯỚC các step khác.

Làm step: P4.S4. Mở todos.md, tìm khối "### [ ] P4.S4 — Vòng lặp và ghi vết" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

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

## P5.S1 — Trend scout: topic hot hôm nay

- [x] Trend scout: topic hot hôm nay

```
Dự án: exp-create-video — team nhiều agent tự tạo video TikTok tiếng Việt về AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/10-team.md — vai, cách nối, bằng chứng (đọc §1 trước)
  3. research/05-decision.md — lựa chọn kiến trúc gốc

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB (Turing, fp16, KHÔNG FP8/bf16), RAM 31GB. GPU dùng
    chung với dự án khác — nvidia-smi trước mọi bước GPU, không kill job lạ.
  - Chi phí 0đ. Model open-weight local + Claude qua claude-agent-sdk (query()),
    KHÔNG phải tool_runner của `anthropic`. Không API trả tiền (X API, v.v.).
  - Trend KHÔNG lấy từ TikTok (Research API chỉ cho học thuật, Creative Center cấm
    scrape). Đăng ở chế độ DRAFT.
  - Ngưỡng ở configs/thresholds.yaml / "Xong khi" viết TRƯỚC, không sửa sau khi
    thấy kết quả. QC tầng 1 không LLM. Vòng QC trần cứng 2.
  - video-spec.json là ranh giới DUY NHẤT Python ↔ Remotion.
  - Tony tự quản git — chỉ commit/push khi Tony bảo.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

KIẾN TRÚC TEAM (research/10-team.md §1 — đừng phá):
  - Mỗi VAI = một hàm Python gọi query() với context MỚI + output_format JSON
    schema, ghi artifact ra file (out/<id>/ hoặc team/). Cổng giữa các vai là CODE.
  - KHÔNG để một LLM tự sinh subagent điều phối cả chuỗi (multi-agent tự do tốn
    ~15× token và kém trên việc tuần tự — bằng chứng ở research/10).
  - Mọi lần gọi LLM: max_turns + max_budget_usd; ghi số lần gọi/token vào state.json.
  - structured_output == None là FAIL, kể cả khi subtype "success".

VIỆC LẦN NÀY: Phase 5 — phòng tin (trend scout, showrunner, brief).

Mục tiêu phase: mỗi ngày có danh sách chủ đề AI đáng làm, có nguồn snapshot; mỗi tuần có lịch
video theo series/pillar; mỗi video bắt đầu từ một brief.json rõ ràng.

Làm step: P5.S1. Mở todos.md, tìm khối "### [ ] P5.S1 — Trend scout: topic hot hôm nay" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), ToS/rate limit của API, và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

QUY TẮC RIÊNG CỦA P5:
  - Nguồn đã kiểm 2026-10-01 ở research/10 §3. ĐÃ LOẠI: TikTok, X API (trả
    tiền), Reddit (phải xin duyệt), Product Hunt (cấm thương mại), scrape
    github.com/trending (Acceptable Use), OSS Insight (rỗng từ 2026-03).
  - Velocity/điểm tính bằng CODE. LLM chỉ chấm cái code không chấm được
    ("hợp khán giả VN?", "giải thích được trong 40s?").
  - Mọi claim phải trỏ về snapshot (sha256) — fact-checker (P4.S3) cần nó.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P5.S1" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P5.S1" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P5.S2 — Showrunner: series + lịch tuần

- [ ] Showrunner: series + lịch tuần

```
Dự án: exp-create-video — team nhiều agent tự tạo video TikTok tiếng Việt về AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/10-team.md — vai, cách nối, bằng chứng (đọc §1 trước)
  3. research/05-decision.md — lựa chọn kiến trúc gốc

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB (Turing, fp16, KHÔNG FP8/bf16), RAM 31GB. GPU dùng
    chung với dự án khác — nvidia-smi trước mọi bước GPU, không kill job lạ.
  - Chi phí 0đ. Model open-weight local + Claude qua claude-agent-sdk (query()),
    KHÔNG phải tool_runner của `anthropic`. Không API trả tiền (X API, v.v.).
  - Trend KHÔNG lấy từ TikTok (Research API chỉ cho học thuật, Creative Center cấm
    scrape). Đăng ở chế độ DRAFT.
  - Ngưỡng ở configs/thresholds.yaml / "Xong khi" viết TRƯỚC, không sửa sau khi
    thấy kết quả. QC tầng 1 không LLM. Vòng QC trần cứng 2.
  - video-spec.json là ranh giới DUY NHẤT Python ↔ Remotion.
  - Tony tự quản git — chỉ commit/push khi Tony bảo.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

KIẾN TRÚC TEAM (research/10-team.md §1 — đừng phá):
  - Mỗi VAI = một hàm Python gọi query() với context MỚI + output_format JSON
    schema, ghi artifact ra file (out/<id>/ hoặc team/). Cổng giữa các vai là CODE.
  - KHÔNG để một LLM tự sinh subagent điều phối cả chuỗi (multi-agent tự do tốn
    ~15× token và kém trên việc tuần tự — bằng chứng ở research/10).
  - Mọi lần gọi LLM: max_turns + max_budget_usd; ghi số lần gọi/token vào state.json.
  - structured_output == None là FAIL, kể cả khi subtype "success".

VIỆC LẦN NÀY: Phase 5 — phòng tin (trend scout, showrunner, brief).

Mục tiêu phase: mỗi ngày có danh sách chủ đề AI đáng làm, có nguồn snapshot; mỗi tuần có lịch
video theo series/pillar; mỗi video bắt đầu từ một brief.json rõ ràng.

Làm step: P5.S2. Mở todos.md, tìm khối "### [ ] P5.S2 — Showrunner: series + lịch tuần" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), ToS/rate limit của API, và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

QUY TẮC RIÊNG CỦA P5:
  - Nguồn đã kiểm 2026-10-01 ở research/10 §3. ĐÃ LOẠI: TikTok, X API (trả
    tiền), Reddit (phải xin duyệt), Product Hunt (cấm thương mại), scrape
    github.com/trending (Acceptable Use), OSS Insight (rỗng từ 2026-03).
  - Velocity/điểm tính bằng CODE. LLM chỉ chấm cái code không chấm được
    ("hợp khán giả VN?", "giải thích được trong 40s?").
  - Mọi claim phải trỏ về snapshot (sha256) — fact-checker (P4.S3) cần nó.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P5.S2" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P5.S2" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P5.S3 — Brief → scriptwriter có nguồn

- [ ] Brief → scriptwriter có nguồn

```
Dự án: exp-create-video — team nhiều agent tự tạo video TikTok tiếng Việt về AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/10-team.md — vai, cách nối, bằng chứng (đọc §1 trước)
  3. research/05-decision.md — lựa chọn kiến trúc gốc

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB (Turing, fp16, KHÔNG FP8/bf16), RAM 31GB. GPU dùng
    chung với dự án khác — nvidia-smi trước mọi bước GPU, không kill job lạ.
  - Chi phí 0đ. Model open-weight local + Claude qua claude-agent-sdk (query()),
    KHÔNG phải tool_runner của `anthropic`. Không API trả tiền (X API, v.v.).
  - Trend KHÔNG lấy từ TikTok (Research API chỉ cho học thuật, Creative Center cấm
    scrape). Đăng ở chế độ DRAFT.
  - Ngưỡng ở configs/thresholds.yaml / "Xong khi" viết TRƯỚC, không sửa sau khi
    thấy kết quả. QC tầng 1 không LLM. Vòng QC trần cứng 2.
  - video-spec.json là ranh giới DUY NHẤT Python ↔ Remotion.
  - Tony tự quản git — chỉ commit/push khi Tony bảo.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

KIẾN TRÚC TEAM (research/10-team.md §1 — đừng phá):
  - Mỗi VAI = một hàm Python gọi query() với context MỚI + output_format JSON
    schema, ghi artifact ra file (out/<id>/ hoặc team/). Cổng giữa các vai là CODE.
  - KHÔNG để một LLM tự sinh subagent điều phối cả chuỗi (multi-agent tự do tốn
    ~15× token và kém trên việc tuần tự — bằng chứng ở research/10).
  - Mọi lần gọi LLM: max_turns + max_budget_usd; ghi số lần gọi/token vào state.json.
  - structured_output == None là FAIL, kể cả khi subtype "success".

VIỆC LẦN NÀY: Phase 5 — phòng tin (trend scout, showrunner, brief).

Mục tiêu phase: mỗi ngày có danh sách chủ đề AI đáng làm, có nguồn snapshot; mỗi tuần có lịch
video theo series/pillar; mỗi video bắt đầu từ một brief.json rõ ràng.

Làm step: P5.S3. Mở todos.md, tìm khối "### [ ] P5.S3 — Brief → scriptwriter có nguồn" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), ToS/rate limit của API, và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

QUY TẮC RIÊNG CỦA P5:
  - Nguồn đã kiểm 2026-10-01 ở research/10 §3. ĐÃ LOẠI: TikTok, X API (trả
    tiền), Reddit (phải xin duyệt), Product Hunt (cấm thương mại), scrape
    github.com/trending (Acceptable Use), OSS Insight (rỗng từ 2026-03).
  - Velocity/điểm tính bằng CODE. LLM chỉ chấm cái code không chấm được
    ("hợp khán giả VN?", "giải thích được trong 40s?").
  - Mọi claim phải trỏ về snapshot (sha256) — fact-checker (P4.S3) cần nó.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P5.S3" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P5.S3" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P6.S1 — Caption/SEO writer: gói copy-dán

- [ ] Caption/SEO writer: gói copy-dán

```
Dự án: exp-create-video — team nhiều agent tự tạo video TikTok tiếng Việt về AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/10-team.md — vai, cách nối, bằng chứng (đọc §1 trước)
  3. research/05-decision.md — lựa chọn kiến trúc gốc

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB (Turing, fp16, KHÔNG FP8/bf16), RAM 31GB. GPU dùng
    chung với dự án khác — nvidia-smi trước mọi bước GPU, không kill job lạ.
  - Chi phí 0đ. Model open-weight local + Claude qua claude-agent-sdk (query()),
    KHÔNG phải tool_runner của `anthropic`. Không API trả tiền (X API, v.v.).
  - Trend KHÔNG lấy từ TikTok (Research API chỉ cho học thuật, Creative Center cấm
    scrape). Đăng ở chế độ DRAFT.
  - Ngưỡng ở configs/thresholds.yaml / "Xong khi" viết TRƯỚC, không sửa sau khi
    thấy kết quả. QC tầng 1 không LLM. Vòng QC trần cứng 2.
  - video-spec.json là ranh giới DUY NHẤT Python ↔ Remotion.
  - Tony tự quản git — chỉ commit/push khi Tony bảo.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

KIẾN TRÚC TEAM (research/10-team.md §1 — đừng phá):
  - Mỗi VAI = một hàm Python gọi query() với context MỚI + output_format JSON
    schema, ghi artifact ra file (out/<id>/ hoặc team/). Cổng giữa các vai là CODE.
  - KHÔNG để một LLM tự sinh subagent điều phối cả chuỗi (multi-agent tự do tốn
    ~15× token và kém trên việc tuần tự — bằng chứng ở research/10).
  - Mọi lần gọi LLM: max_turns + max_budget_usd; ghi số lần gọi/token vào state.json.
  - structured_output == None là FAIL, kể cả khi subtype "success".

VIỆC LẦN NÀY: Phase 6 — phân phối (caption/SEO, Telegram, publisher, cron).

Mục tiêu phase: video đã qua QC → Tony nhận trên Telegram kèm gói caption copy-dán → bấm duyệt
→ video vào inbox TikTok → Tony dán caption, bật nhãn AI, bấm đăng.

Làm step: P6.S1. Mở todos.md, tìm khối "### [ ] P6.S1 — Caption/SEO writer: gói copy-dán" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), ToS/rate limit của API, và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

QUY TẮC RIÊNG CỦA P6:
  - Mọi nút bấm của Tony ghi ra file (approval.json) — bot chết bật lại vẫn nhớ.
  - Kiểm bằng code trước khi gửi: video ≤ 50 MB (giới hạn Bot API), ≤ 5 bài chờ
    inbox/24h, token TikTok còn hạn.
  - Nhãn AI bật cho MỌI video (ảnh diffusion + giọng TTS) — nhắc mỗi lần gửi duyệt.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P6.S1" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P6.S1" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P6.S2 — Bot Telegram (chuyển từ P5.S2)

- [ ] Bot Telegram (chuyển từ P5.S2)

```
Dự án: exp-create-video — team nhiều agent tự tạo video TikTok tiếng Việt về AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/10-team.md — vai, cách nối, bằng chứng (đọc §1 trước)
  3. research/05-decision.md — lựa chọn kiến trúc gốc

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB (Turing, fp16, KHÔNG FP8/bf16), RAM 31GB. GPU dùng
    chung với dự án khác — nvidia-smi trước mọi bước GPU, không kill job lạ.
  - Chi phí 0đ. Model open-weight local + Claude qua claude-agent-sdk (query()),
    KHÔNG phải tool_runner của `anthropic`. Không API trả tiền (X API, v.v.).
  - Trend KHÔNG lấy từ TikTok (Research API chỉ cho học thuật, Creative Center cấm
    scrape). Đăng ở chế độ DRAFT.
  - Ngưỡng ở configs/thresholds.yaml / "Xong khi" viết TRƯỚC, không sửa sau khi
    thấy kết quả. QC tầng 1 không LLM. Vòng QC trần cứng 2.
  - video-spec.json là ranh giới DUY NHẤT Python ↔ Remotion.
  - Tony tự quản git — chỉ commit/push khi Tony bảo.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

KIẾN TRÚC TEAM (research/10-team.md §1 — đừng phá):
  - Mỗi VAI = một hàm Python gọi query() với context MỚI + output_format JSON
    schema, ghi artifact ra file (out/<id>/ hoặc team/). Cổng giữa các vai là CODE.
  - KHÔNG để một LLM tự sinh subagent điều phối cả chuỗi (multi-agent tự do tốn
    ~15× token và kém trên việc tuần tự — bằng chứng ở research/10).
  - Mọi lần gọi LLM: max_turns + max_budget_usd; ghi số lần gọi/token vào state.json.
  - structured_output == None là FAIL, kể cả khi subtype "success".

VIỆC LẦN NÀY: Phase 6 — phân phối (caption/SEO, Telegram, publisher, cron).

Mục tiêu phase: video đã qua QC → Tony nhận trên Telegram kèm gói caption copy-dán → bấm duyệt
→ video vào inbox TikTok → Tony dán caption, bật nhãn AI, bấm đăng.

Làm step: P6.S2. Mở todos.md, tìm khối "### [ ] P6.S2 — Bot Telegram (chuyển từ P5.S2)" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), ToS/rate limit của API, và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

QUY TẮC RIÊNG CỦA P6:
  - Mọi nút bấm của Tony ghi ra file (approval.json) — bot chết bật lại vẫn nhớ.
  - Kiểm bằng code trước khi gửi: video ≤ 50 MB (giới hạn Bot API), ≤ 5 bài chờ
    inbox/24h, token TikTok còn hạn.
  - Nhãn AI bật cho MỌI video (ảnh diffusion + giọng TTS) — nhắc mỗi lần gửi duyệt.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P6.S2" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P6.S2" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P6.S3 — Publisher TikTok (chuyển từ P5.S3)

- [ ] Publisher TikTok (chuyển từ P5.S3)

```
Dự án: exp-create-video — team nhiều agent tự tạo video TikTok tiếng Việt về AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/10-team.md — vai, cách nối, bằng chứng (đọc §1 trước)
  3. research/05-decision.md — lựa chọn kiến trúc gốc

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB (Turing, fp16, KHÔNG FP8/bf16), RAM 31GB. GPU dùng
    chung với dự án khác — nvidia-smi trước mọi bước GPU, không kill job lạ.
  - Chi phí 0đ. Model open-weight local + Claude qua claude-agent-sdk (query()),
    KHÔNG phải tool_runner của `anthropic`. Không API trả tiền (X API, v.v.).
  - Trend KHÔNG lấy từ TikTok (Research API chỉ cho học thuật, Creative Center cấm
    scrape). Đăng ở chế độ DRAFT.
  - Ngưỡng ở configs/thresholds.yaml / "Xong khi" viết TRƯỚC, không sửa sau khi
    thấy kết quả. QC tầng 1 không LLM. Vòng QC trần cứng 2.
  - video-spec.json là ranh giới DUY NHẤT Python ↔ Remotion.
  - Tony tự quản git — chỉ commit/push khi Tony bảo.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

KIẾN TRÚC TEAM (research/10-team.md §1 — đừng phá):
  - Mỗi VAI = một hàm Python gọi query() với context MỚI + output_format JSON
    schema, ghi artifact ra file (out/<id>/ hoặc team/). Cổng giữa các vai là CODE.
  - KHÔNG để một LLM tự sinh subagent điều phối cả chuỗi (multi-agent tự do tốn
    ~15× token và kém trên việc tuần tự — bằng chứng ở research/10).
  - Mọi lần gọi LLM: max_turns + max_budget_usd; ghi số lần gọi/token vào state.json.
  - structured_output == None là FAIL, kể cả khi subtype "success".

VIỆC LẦN NÀY: Phase 6 — phân phối (caption/SEO, Telegram, publisher, cron).

Mục tiêu phase: video đã qua QC → Tony nhận trên Telegram kèm gói caption copy-dán → bấm duyệt
→ video vào inbox TikTok → Tony dán caption, bật nhãn AI, bấm đăng.

Làm step: P6.S3. Mở todos.md, tìm khối "### [ ] P6.S3 — Publisher TikTok (chuyển từ P5.S3)" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), ToS/rate limit của API, và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

QUY TẮC RIÊNG CỦA P6:
  - Mọi nút bấm của Tony ghi ra file (approval.json) — bot chết bật lại vẫn nhớ.
  - Kiểm bằng code trước khi gửi: video ≤ 50 MB (giới hạn Bot API), ≤ 5 bài chờ
    inbox/24h, token TikTok còn hạn.
  - Nhãn AI bật cho MỌI video (ảnh diffusion + giọng TTS) — nhắc mỗi lần gửi duyệt.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P6.S3" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P6.S3" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P6.S4 — Cron và nhịp chạy (chuyển từ P5.S4)

- [ ] Cron và nhịp chạy (chuyển từ P5.S4)

```
Dự án: exp-create-video — team nhiều agent tự tạo video TikTok tiếng Việt về AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/10-team.md — vai, cách nối, bằng chứng (đọc §1 trước)
  3. research/05-decision.md — lựa chọn kiến trúc gốc

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB (Turing, fp16, KHÔNG FP8/bf16), RAM 31GB. GPU dùng
    chung với dự án khác — nvidia-smi trước mọi bước GPU, không kill job lạ.
  - Chi phí 0đ. Model open-weight local + Claude qua claude-agent-sdk (query()),
    KHÔNG phải tool_runner của `anthropic`. Không API trả tiền (X API, v.v.).
  - Trend KHÔNG lấy từ TikTok (Research API chỉ cho học thuật, Creative Center cấm
    scrape). Đăng ở chế độ DRAFT.
  - Ngưỡng ở configs/thresholds.yaml / "Xong khi" viết TRƯỚC, không sửa sau khi
    thấy kết quả. QC tầng 1 không LLM. Vòng QC trần cứng 2.
  - video-spec.json là ranh giới DUY NHẤT Python ↔ Remotion.
  - Tony tự quản git — chỉ commit/push khi Tony bảo.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

KIẾN TRÚC TEAM (research/10-team.md §1 — đừng phá):
  - Mỗi VAI = một hàm Python gọi query() với context MỚI + output_format JSON
    schema, ghi artifact ra file (out/<id>/ hoặc team/). Cổng giữa các vai là CODE.
  - KHÔNG để một LLM tự sinh subagent điều phối cả chuỗi (multi-agent tự do tốn
    ~15× token và kém trên việc tuần tự — bằng chứng ở research/10).
  - Mọi lần gọi LLM: max_turns + max_budget_usd; ghi số lần gọi/token vào state.json.
  - structured_output == None là FAIL, kể cả khi subtype "success".

VIỆC LẦN NÀY: Phase 6 — phân phối (caption/SEO, Telegram, publisher, cron).

Mục tiêu phase: video đã qua QC → Tony nhận trên Telegram kèm gói caption copy-dán → bấm duyệt
→ video vào inbox TikTok → Tony dán caption, bật nhãn AI, bấm đăng.

Làm step: P6.S4. Mở todos.md, tìm khối "### [ ] P6.S4 — Cron và nhịp chạy (chuyển từ P5.S4)" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), ToS/rate limit của API, và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

QUY TẮC RIÊNG CỦA P6:
  - Mọi nút bấm của Tony ghi ra file (approval.json) — bot chết bật lại vẫn nhớ.
  - Kiểm bằng code trước khi gửi: video ≤ 50 MB (giới hạn Bot API), ≤ 5 bài chờ
    inbox/24h, token TikTok còn hạn.
  - Nhãn AI bật cho MỌI video (ảnh diffusion + giọng TTS) — nhắc mỗi lần gửi duyệt.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P6.S4" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P6.S4" trong todos.md
nữa thì tốt, để hai file khỏi lệch nhau.
```

---

## P7.S1 — Analyst: thu số + báo cáo tuần

- [ ] Analyst: thu số + báo cáo tuần

```
Dự án: exp-create-video — team nhiều agent tự tạo video TikTok tiếng Việt về AI.
Repo: /mnt/data1tb/exp-create-video  (symlink: ~/DTG/exp-create-video)

ĐỌC TRƯỚC KHI LÀM, theo đúng thứ tự:
  1. todos.md  — mục "Ngữ cảnh chung" ở đầu file
  2. research/10-team.md — vai, cách nối, bằng chứng (đọc §1 trước)
  3. research/05-decision.md — lựa chọn kiến trúc gốc

RÀNG BUỘC KHÔNG ĐƯỢC PHÁ:
  - Máy: tony, RTX 2060 6GB (Turing, fp16, KHÔNG FP8/bf16), RAM 31GB. GPU dùng
    chung với dự án khác — nvidia-smi trước mọi bước GPU, không kill job lạ.
  - Chi phí 0đ. Model open-weight local + Claude qua claude-agent-sdk (query()),
    KHÔNG phải tool_runner của `anthropic`. Không API trả tiền (X API, v.v.).
  - Trend KHÔNG lấy từ TikTok (Research API chỉ cho học thuật, Creative Center cấm
    scrape). Đăng ở chế độ DRAFT.
  - Ngưỡng ở configs/thresholds.yaml / "Xong khi" viết TRƯỚC, không sửa sau khi
    thấy kết quả. QC tầng 1 không LLM. Vòng QC trần cứng 2.
  - video-spec.json là ranh giới DUY NHẤT Python ↔ Remotion.
  - Tony tự quản git — chỉ commit/push khi Tony bảo.
  - Trả lời tiếng Việt, giữ nguyên thuật ngữ tiếng Anh.

KIẾN TRÚC TEAM (research/10-team.md §1 — đừng phá):
  - Mỗi VAI = một hàm Python gọi query() với context MỚI + output_format JSON
    schema, ghi artifact ra file (out/<id>/ hoặc team/). Cổng giữa các vai là CODE.
  - KHÔNG để một LLM tự sinh subagent điều phối cả chuỗi (multi-agent tự do tốn
    ~15× token và kém trên việc tuần tự — bằng chứng ở research/10).
  - Mọi lần gọi LLM: max_turns + max_budget_usd; ghi số lần gọi/token vào state.json.
  - structured_output == None là FAIL, kể cả khi subtype "success".

VIỆC LẦN NÀY: Phase 7 — vòng phản hồi (analyst, thử format, xem lại QC).

Mục tiêu phase: số liệu thật quay về showrunner và rubric QC — team biết cái gì Tony duyệt và
cái gì người xem giữ lại, và bỏ những tầng/vai không giúp gì.

Làm step: P7.S1. Mở todos.md, tìm khối "### [ ] P7.S1 — Analyst: thu số + báo cáo tuần" và làm đúng theo các mục Mục tiêu / Ngữ cảnh / Đọc trước / Việc / Xong khi / Bẫy trong đó.

BƯỚC 0 — RESEARCH TRƯỚC KHI CODE (bắt buộc, Tony yêu cầu 2026-10-01):
  1. Đọc research/ liên quan (08 chất lượng, 09 chuyển động, 10 team) và probe cũ
     của step này trong research/probes/.
  2. Quét lại cho ĐÚNG step này — cái gì mới nhất, tốt nhất, chạy được ở đây:
     model / thư viện / API / kỹ thuật / bằng chứng. Dùng agent paper-scout hoặc
     skill /research-topic; repo sắp phụ thuộc thì /repo-audit; dataset thì
     /dataset-hunt. Kiểm license (kênh có kiếm tiền → cấm NC), VRAM trên 2060 6GB
     Turing (fp16, không FP8/bf16), ToS/rate limit của API, và link còn sống.
  3. Ghi research/probes/<mã-step>-research.md: ứng viên · nguồn [nguồn, YYYY-MM] ·
     verified/reported/assumed · lựa chọn + lý do · cái đã loại và vì sao.
  4. Research đổi tiêu chí "Xong khi"? Ghi lý do + ngày vào todos TRƯỚC khi code.
     Sửa tiêu chí sau khi thấy kết quả = không còn là tiêu chí.
  5. Research không thay được đo: chọn xong vẫn phải probe trên máy tony.

QUY TẮC RIÊNG CỦA P7:
  - Không kết luận từ ít mẫu: một nhánh chỉ "thắng" khi mỗi nhánh ≥ 10 video và
    P(tốt hơn) ≥ 0,9 (Thompson sampling Beta-Bernoulli trên approve). Trước đó
    báo cáo ghi "chưa đủ dữ liệu".
  - Lưu số thô append-only (t+24h/72h/7d), không ghi đè.
  - Mọi đề xuất đổi rubric/format phải dẫn ≥ 3 video cụ thể.

CÁCH CHẠY LẦN NÀY: một phiên Claude Code duy nhất, làm TUẦN TỰ từng step, do
tool autoclick gửi prompt vào. KHÔNG mở git worktree, KHÔNG chạy song song — mục
"Chạy song song bằng git worktree" trong todos.md không áp dụng ở đây.

XONG THÌ TICK: mở plan-autoclick.md, tìm mục "## P7.S1" và đổi checkbox trong
mục đó thành [x]. Đây là file autoclick đọc để biết step đã xong — tick vào
todos.md KHÔNG có tác dụng với tool. Tick nốt "### [ ] P7.S1" trong todos.md
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
- **P3b.S10** — Parallax: Tony so p3b-d với p3b-b (phần zoom-punch làm sau khi Tony chọn).
- **P7.S2** — Thử format/độ dài: cần video đã đăng + số thật.
- **P7.S3** — Xem lại QC + các vai sau 20 video: phải có 20 video thật đã.

Mục **Nợ kỹ thuật đã biết** ở cuối todos.md cũng để nguyên đó — phần lớn là câu hỏi
chưa quyết, không phải việc giao được.
