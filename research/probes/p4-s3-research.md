# P4.S3 — BƯỚC 0 research: T4 fact-checker — 2026-10-02

Một lượt paper-scout (pipeline factuality cấp claim, verifier nhỏ local, trích text nguồn,
bias fact-checker) + đọc research/10 §3, §5. Link fetch 2026-10-02. **V** verified · **R** reported · **A** assumed.

## 1. Bằng chứng

| Điều | Nguồn | Mức |
|---|---|---|
| VeriScore: chỉ rút claim **kiểm chứng được**; nhãn **nhị phân** supported/unsupported — gộp contradicted với inconclusive vì người chấm thấy ít mâu thuẫn; κ 0,73 | arXiv 2406.19276 [2024-06] | V |
| SAFE: 72% khớp người; lỗi lớn nhất là suy luận của LLM, rồi tới search không thấy bằng chứng; nhãn = "Google ủng hộ", không phải "đúng" | arXiv 2403.18802 [2024-03] | V |
| EAVer: verifier **chấp nhận nhầm** claim không có căn cứ — False Support Rate 89% → 42% sau khi sửa | arXiv 2609.22223 [2026-09] | V |
| VeriFastScore: rút + kiểm một lượt, r 0,80/ví dụ | arXiv 2505.16973 [2025-05] | R |
| LLM-AggreFact BAcc: Bespoke-MiniCheck-7B 77,4 · Claude-3.5 Sonnet 77,2 · MiniCheck-Flan-T5-L 75,0 — **toàn tiếng Anh** | llm-aggrefact.github.io | V |
| MiniCheck-Flan-T5-L MIT, 0,8B, `language: en` · Bespoke-MiniCheck-7B **CC BY-NC** · Granite Guardian 3.3 8B Apache nhưng ~16GB BF16, tiếng Anh | HF cards [2024–2025] | V |
| mDeBERTa-v3-base-xnli (MIT, 0,3B) có tiếng Việt, XNLI-vi 0,793, train cả cặp lệch ngôn ngữ — chưa có điểm fact-check | HF MoritzLaurer [—] | V |
| Claim số (CheckThat! 2025): macro-F1 0,945 validation → **0,424** test; lỗi do suy luận số + thiếu bằng chứng | ClaimIQ arXiv 2509.11492 [2025-09] | V |
| arXiv API: ≤ 1 request / 3s, metadata CC0 · HF `api/models/<id>` có `createdAt`, `author`, license; `/raw/main/README.md` · GitHub `repos/{o}/{r}` + `/readme` | info.arxiv.org tou; HF; docs.github.com | V |
| trafilatura Apache-2.0 từ v1.8.0 (trước đó GPL) | github adbar/trafilatura | V |

**Khoảng trống:** không paper nào đo riêng precision/recall cho **contradicted vs không tìm
thấy** — chính vì đều gộp hai thứ đó. T4 cần đúng sự phân biệt này (todos: "chặn cái sai,
gắn cờ cái chưa kiểm được") → tự đo bằng bộ đối chứng §4.

## 2. Lựa chọn

| Ứng viên | Kết luận |
|---|---|
| **Claude qua `run_role`, 2 vai: `claim_extractor` → `fact_checker`, nguồn snapshot đưa thẳng vào prompt** | **Chọn.** Rút claim KHÔNG nhìn nguồn (khỏi chỉ rút cái mình kiểm được); 0đ; đọc Việt + Anh |
| Fact-checker có tool WebFetch + hook allowlist (research/10 §5) | **Đổi:** code tải nguồn trước (`team/snapshot.py`), LLM không có tool nào. Cùng mục đích (chỉ nguồn gốc, không trí nhớ) nhưng chặt hơn: mọi thứ LLM thấy đã nằm trên đĩa theo sha256, trích dẫn kiểm được bằng `in`, không có lượt duyệt web lạc đề |
| MiniCheck / Granite local | Loại — chỉ tiếng Anh (phải dịch claim), Bespoke NC, Granite quá 6GB; điểm ngang Claude |
| mDeBERTa-xnli làm phiếu thứ hai | Hoãn — không có điểm fact-check; thêm GPU vào chuỗi đã chật. Xét lại nếu probe thấy Claude dễ dãi |
| trafilatura cho blog | Chưa cần — 3 loại nguồn chính đi qua API; blog dùng `html.parser` stdlib. Cài khi gặp blog bóc hỏng |
| `trends.jsonl` / `raw_quote` (todos gốc) | Chưa có (P5.S1). `team/snapshots/<sha>.txt` + `index.json` là đúng định dạng P5.S1 sẽ ghi |

## 3. Thiết kế — VIẾT TRƯỚC KHI CHẠY (2026-10-02)

**Nguồn** = `script.sources[].url` + `shots[].url` (screenshot), qua `team/snapshot.py`:
HF API + README · arXiv export API · GitHub API + README · file `research/probes/*.md` · blog
trong `ALLOWLIST`. Domain ngoài allowlist → không tải, claim dựa vào đó thành `inconclusive`.

**Nhãn 3 chiều**, cổng bằng code:

| LLM nói | Code kiểm | Kết quả |
|---|---|---|
| supported / contradicted | `quote` phải có NGUYÊN VĂN trong snapshot `source_id` (chuẩn hoá khoảng trắng, hoa/thường) | không có → **inconclusive** (`downgraded`) |
| claim số (`kind=number`) | `source_value` phải xuất hiện trong quote; so `claim_value` (đã đổi về đơn vị nguồn) với tolerance `max(2% · |nguồn|, 0,5 · 10^-d)` (d = số chữ số thập phân của claim) | **code quyết** supported/contradicted, ghi khi khác LLM |
| claim ngày (`kind=date`) | `source_date` phải có trong quote; so ở **độ mịn của claim** ("2024-02" chỉ so năm-tháng) | **code quyết** |
| inconclusive | — | gắn cờ, không chặn |

**Quyền:** `contradicted ≥ 1` (> `max_contradictions: 0`) → **block**. `inconclusive >
max_unverified_claims: 3` → cờ cho Tony, KHÔNG chặn. Claim loại `model_name / benchmark_number
/ release_date / org_name` (`require_source_for`) không có nguồn → inconclusive + nêu tên trong cờ.
Patch về scriptwriter: mỗi claim contradicted một dòng — câu · claim · url · trích nguồn.

## 4. Probe — tiêu chí viết trước khi chạy (2026-10-02)

Bộ đối chứng `eval/factcheck/`: 4 script nền tay viết, **chỉ claim đúng** đã đối chiếu snapshot
(SDXL-Lightning: HF card + arXiv + probe p3s3 · Whisper paper: arXiv + GitHub · Qwen3-VL-2B:
HF card · Whisper models: GitHub README) + 4 bản gài **5 claim sai mỗi bản = 20 claim sai**
(10 số, 3 ngày, 3 license, 1 tổ chức, 3 mệnh đề chữ — ghi `seeded` từng câu). Mỗi script chạy **2 lần**.

| # | Tiêu chí | Pass khi |
|---|---|---|
| 1 | **Xong khi:** câu sai ngày ra mắt (SDXL-Lightning "tháng sáu năm 2023" — thật 2024-02) → chặn và chỉ đúng câu | block + contradicted ở đúng câu đó, 2/2 |
| 2 | Recall contradicted trên 20 claim gài (todos, viết 2026-10-01) | **≥ 0,9** (gộp 2 lượt: ≥ 36/40) |
| 3 | Precision contradicted (todos) | **≥ 0,8** — contradicted đúng chỗ gài / mọi contradicted, gộp sạch + gài |
| 4 | Không chặn oan script sạch | 4 script sạch × 2 lượt: **0 block** |
| 5 | Phân biệt sai vs chưa kiểm được | câu ý kiến/không có trong nguồn → inconclusive, không contradicted (đếm trong precision) |
| 6 | Ghi vết | 100% lần gọi có token + thời gian trong `state.json` |

Fail 2/3/4: KHÔNG sửa ngưỡng; ghi số + phân loại lỗi (rút claim sót · trích sai · suy luận
sai · code so số sai), sửa đúng khâu đó ở lần sau, ghi lý do + ngày.
