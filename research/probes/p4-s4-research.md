# P4.S4 — BƯỚC 0 research: vòng lặp QC + ghi vết — 2026-10-02

Một lượt paper-scout (lợi ích theo vòng, hồi quy khi sửa, chọn bản tốt nhất vs bản cuối, ghi
vết để quy lỗi cho tầng) + đọc `research/05-decision.md` "Vòng lặp QC", research/10 §5, và
bốn probe P4.S0–S3. Link fetch 2026-10-02. **V** verified · **R** reported · **A** assumed.

## 1. Bằng chứng

| Điều | Nguồn | Mức |
|---|---|---|
| Self-Refine điểm theo vòng y0→y1→y2→y3: Constrained Gen 29,0→40,3→46,7→49,7; Code Opt 22,0→27,0→27,9→28,8 — lợi ích giảm dần; với tác vụ nhiều khía cạnh KHÔNG đơn điệu, chọn bản theo điểm từng khía cạnh | arXiv 2303.17651 [2023-05] | V |
| CRITIC: "2–3 vòng sửa cho phần lớn lợi ích"; không có tool thì tự phê gần như không giúp, có khi tệ đi | arXiv 2305.11738 [2023-05] | V |
| Không có oracle, tự sửa làm tệ đi: GSM8K 95,5→91,5→89,0; đúng→sai nhiều hơn sai→đúng | arXiv 2310.01798 [2024-03] | V |
| Lặp chỉ có lợi khi tỉ lệ sửa đúng / tỉ lệ làm hỏng > Acc/(1−Acc); prompt "kiểm trước" đưa tỉ lệ làm hỏng 2% → 0% | arXiv 2604.22273 [2026-05] | V |
| Agent thị giác: thành công cộng dồn ~62→70→75→79% qua các lần thử; sau lần 3 thêm < 2% | arXiv 2601.11637 [2026-01] | V |
| Sửa nhỏ làm hỏng chương trình ĐÚNG 42,4% so với sửa được 4,1%; vòng lặp rơi vào điểm cố định / chu kỳ / thoái hoá | arXiv 2609.10123 [2026-09] | V |
| MAST: lỗi khâu kiểm chứng — dừng sớm 6,2%, kiểm thiếu 8,2%, kiểm sai 9,1%; LLM judge κ 0,77 với người | arXiv 2503.13657 [2025-10] | V |
| Validate judge bằng độ khớp với người theo từng chiều (κ dao động 0,17–0,86 giữa các chiều) | Dietz et al. 2025 | R |

**Đọc cho dự án này:** T1 (code) và T4 (trích nguồn đã lưu) là tín hiệu NGOÀI → sửa theo chúng
có cơ sở. T2/T3 là phê bình của model → có rủi ro sửa làm tệ đi. Trần 2 vòng khớp bằng chứng.

## 2. Lựa chọn

| Ứng viên | Kết luận |
|---|---|
| **Vòng lặp Python thuần trong `qc/loop.py`**, mỗi tầng là một hàm, patch là hàm, cổng là code | **Chọn** — đúng research/10 §1 (cổng giữa vai là code, không LLM điều phối) |
| LangGraph / framework orchestration | Loại — thêm tầng điều phối = thêm chỗ lệch (P4.S0 Bẫy); vòng lặp có 3 lần chấm, không cần đồ thị |
| Giữ bản CUỐI | Loại — sửa có thể hỏng chỗ khác (2609.10123, 2310.01798) → giữ **bản tốt nhất đã chấm** |
| Chỉ nhận patch nếu không tầng nào tệ đi, rồi **quay lại** bản tốt nhất trước khi sửa tiếp | Hoãn — quay lui script dễ nhưng quay lui ảnh `gen/` + TTS + spec phức tạp; chọn bản tốt nhất ở cuối đã chặn được rủi ro gửi bản tệ hơn. Xét lại nếu nhật ký 20 video cho thấy vòng 2 hay tệ hơn vòng 1 |

## 3. Thiết kế — VIẾT TRƯỚC KHI CHẠY (2026-10-02)

- **Đếm vòng:** `round-0.json` = chấm bản dựng đầu; `round-n.json` = chấm lại sau lần sửa thứ n.
  `MAX_ROUNDS = 2` **hằng số trong code**; `thresholds.yaml: qc_loop.max_rounds` chỉ được hạ
  (`min(config, 2)`). Bản sửa cuối **luôn được chấm** — tối đa 3 lần chấm, 2 lần sửa.
  `qc_rounds` = số lần sửa đã dùng (metric ≤ 1,5).
- **Mỗi lần chấm chạy lại đủ 4 tầng**; riêng T3/T4 (chỉ đọc script) dùng lại kết quả vòng trước
  khi `script.json` không đổi (sha256) — đầu vào y hệt, gọi lại LLM là đốt token.
- **Định tuyến patch:** T1 chặn → **dừng ngay**, gửi Tony (lỗi kỹ thuật tất định, dựng lại không
  sửa được). T2 → `regen.rerender` đúng shot (prompt sửa + seed khác). T3 + T4 → GỘP thành MỘT
  lần `revise_script` (một lần gọi, sửa có phạm vi, "giữ nguyên phần còn lại"). Thứ tự: ảnh
  trước (trên spec hiện tại) → script → `pipeline.run` dựng lại (cache state.json: chỉ stage có
  đầu vào đổi).
- **GPU:** `nvidia-smi` trước T2 (cần ≥ 2.500 MiB trống) và trước regen (≥ 1.500 MiB); thiếu →
  bỏ qua có ghi lý do, không OOM giữa chừng. VLM và SDXL không bao giờ cùng nạp (tuần tự, `with`).
- **Quyết định** (`qc/decision.json`): bản gửi = bản tốt nhất theo (ít lỗi chặn → ít đề xuất →
  muộn hơn). `status` pass / send_with_issues / blocked. **`send_to_tony` luôn true**; chặn cứng
  thể hiện ở `publishable: false` + danh sách lỗi còn lại.
- **Ghi vết:** `round-<n>.json` = mỗi tầng {ran/skipped/reused, ok, blocking, suggestions, tóm
  tắt điểm, wall_sec, token ra} + patch đã gửi + patch đã áp; `qc/r<n>/` giữ artifact từng tầng +
  bản sao script/spec/mp4 của vòng đó. Mỗi tầng chạy trong một stage `qc<n>_<tầng>` của
  `state.json` → token LLM quy được về tầng.
- **`scripts/qc_report.py`:** qua nhiều `out/*/qc/`: mỗi tầng — số lần chạy, số lần cờ, lỗi được
  sửa ở vòng sau (key biến mất), lỗi lì (còn sau sửa), thời gian, token; kèm `approval.json`
  (P6.S2) nếu có → bảng tầng × approve để P7.S3 tính tương quan.

## 4. Probe — tiêu chí viết trước khi chạy (2026-10-02)

| # | Tiêu chí (todos "Xong khi" + bổ sung viết trước) | Pass khi |
|---|---|---|
| 1 | Một video đi hết vòng lặp | `decision.json` có, `status` ∈ {pass, send_with_issues, blocked} |
| 2 | Đủ nhật ký | mỗi lần chấm có `round-<n>.json` (4 tầng, mỗi tầng ran hoặc lý do skipped) + `qc/r<n>/` |
| 3 | Không bao giờ quá 2 vòng | `qc_rounds ≤ 2` ở probe thật; **test**: tầng giả luôn fail → đúng 3 lần chấm, 2 lần sửa; config `max_rounds: 99` → vẫn 2 |
| 4 | Patch về đúng vai | T3/T4 → `script` (hook dở được sửa), T2 → `visual` (đúng shot_id T2 chê) |
| 5 | T1 chặn → không đốt vòng | test: T1 fail → dừng sau round-0, 0 lần sửa |
| 6 | wall_time | ghi số so với ngân sách 40 phút — chỉ báo, không pass/fail (ngưỡng ở `operational`) |

Video probe: chép `out/p3b-s5-demo` → `out/p4-s4-loop` (không đụng demo của Tony), thay hook bằng
"Hôm nay chúng ta sẽ tìm hiểu về SDXL-Lightning." rồi dựng lại cho nhất quán, sau đó chạy vòng lặp đủ 4 tầng.
