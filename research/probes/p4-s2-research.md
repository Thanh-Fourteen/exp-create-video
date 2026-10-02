# P4.S2 — BƯỚC 0 research: T3 chấm sức hút kịch bản — 2026-10-02

Một lượt paper-scout (LLM-as-judge checklist, bias critic, hook/CTA TikTok, dịch máy tiếng
Việt) + đọc `configs/rubric.md`, `research/10-team.md` §5, `research/07` §3. Mọi link fetch
2026-10-02. Nhãn: **V** verified · **R** reported · **A** assumed.

## 1. Bằng chứng

| Điều | Nguồn | Mức |
|---|---|---|
| Thay Likert bằng câu hỏi nhị phân: agreement giữa các judge +0,45, variance giảm (12 judge) | CheckEval arXiv 2403.18771 [v3 2025-10] | V |
| Checklist: exact agreement với người 46,4% → 52,2% so với chấm trực tiếp | TICK arXiv 2410.03608 [2024-10] | V |
| Judge 2B theo checklist tương quan 0,965 với người, ngang GPT-4o | RocketEval arXiv 2503.05142 [2025-03] | V |
| Checklist chấm bằng AI **kết hợp verifier programs** (code) tốt hơn reward model: InFoBench +6, Arena-Hard +3 | RLCF arXiv 2507.18624 [2025-12] | V |
| Thang 0–10 kém nhất trong các thang số (ICC 0,805 vs 0–5 0,853) | arXiv 2601.03444 [2026-01] | V |
| LLM ưu ái output của chính nó, tỉ lệ với khả năng tự nhận ra | arXiv 2404.13076 [2024-04] | V |
| Judge pass/fail dễ dãi: TPR > 96% nhưng **TNR < 25%** | arXiv 2510.11822 [2025-10] | V |
| Critic được bảo "tìm lỗi" thì bịa lỗi (nitpick) | CriticGPT arXiv 2407.00215 [2024-06] | V |
| LLM chấm "sáng tạo" tương quan ~0 với chuyên gia | Chakrabarty CHI 2024 (research/10 §5) | V |
| Judge tiếng Việt aspect-based κ=0,792; model chuyên Việt cỡ nhỏ (VinaLLaMA-7B) rất yếu | VIVID arXiv 2608.03095 [2026-08] | V |
| "Content proposition trong 3 giây đầu, hook trong 6 giây đầu" — tài liệu **quảng cáo**, không phải organic | ads.tiktok.com creative-best-practices [2025-06] | V (nguồn) / A (áp cho organic) |
| Share/save nặng hơn like — các blog mâu thuẫn trọng số (share×10/save×5 vs share×7/save×10) | posteverywhere, fanpagekarma [2025–26] | R |
| Danh sách dấu hiệu dịch máy tiếng Việt ("được…bởi", "một cách + adj", "việc + V") | rubric.md, không tìm được nguồn học thuật | A |

**Hai lực ngược nhau** (#critic bịa lỗi vs #judge dễ dãi): hướng lệch phụ thuộc cách hỏi.
→ thiết kế phải chặn CẢ HAI: mặc định đạt + bắt trích nguyên văn (chống bịa), và mục đo
được thì để code chấm (chống dễ dãi — regex không "nể").

## 2. Ứng viên và lựa chọn

| Ứng viên | Kết luận |
|---|---|
| **Claude qua `run_role` (claude-agent-sdk), context mới, checklist nhị phân** | **Chọn.** Đã có trong team (P4.S0), 0đ, tiếng Việt tốt |
| LLM chấm 0–10 từng nhóm như JSON mẫu cũ ở rubric.md | Loại — thang 0–10 kém nhất (#2601.03444), đúng kiểu "chấm sáng tạo" mà research/10 §5 cấm |
| Model open-weight local chấm tiếng Việt (Vistral, VinaLLaMA, Qwen3 nhỏ) | Loại — không có bằng chứng hơn regex; VIVID: model Việt nhỏ rất yếu; lại tranh GPU với T2 |
| Pairwise (so với bản cũ) | Loại — lật kết luận ~35% (research/10 §5); T3 chấm pointwise |
| Critic khác họ model để tránh self-preference | Không có — chi phí 0đ chỉ có Claude. Giảm bằng: không nói nguồn gốc kịch bản, critic không thấy system prompt của scriptwriter, điểm do CODE tính từ mục đạt/trượt |

## 3. Thiết kế — VIẾT TRƯỚC KHI CHẠY (2026-10-02)

**Mục checklist** (đạt = câu trả lời mong muốn). Code chấm mục đo được; critic chỉ chấm 6
mục ngữ nghĩa. Mã + câu hỏi đầy đủ ở `qc/t3_appeal.py: ITEMS`.

| Nhóm (trọng số thresholds.yaml) | Code | Critic |
|---|---|---|
| hook 0,40 | `H_OPENER` câu đầu không chào/bối cảnh/định nghĩa/hứa hẹn (regex) | `H_INFO` lời trong 3 giây đầu có thông tin cụ thể |
| pacing 0,25 | `P_VARIETY` dài nhất − ngắn nhất thân bài ≥ **4** từ · `P_FILLER` câu mở bằng từ chuyển tiếp thừa · `P_LIST` ≥ 2 lần "thứ nhất/hai/ba" | `P_STALL` ý kéo > 3 câu · `P_TURN` có chỗ ngoặt giữa video |
| vietnamese_quality 0,25 | `V_MARKERS` 4 dấu hiệu dịch máy · `V_TERMS` thuật ngữ bị dịch | `V_NATURAL` câu lủng củng · `V_ADDRESS` xưng hô lẫn |
| cta 0,10 | `C_GENERIC` xin like/follow · `C_SAVE_SHARE` có xin lưu/chia sẻ | `C_SPECIFIC` hành động cụ thể gắn nội dung |
| (ghi vết, 0 trọng số) | `A_FIRSTHAND` câu quan sát ngôi thứ nhất · `A_PROBE_SOURCE` nguồn trỏ `research/probes/` | — |

**Điểm** (định nghĩa thang, KHÔNG đổi ngưỡng): nhóm = 10 × tỉ lệ mục đạt; trượt bất kỳ
mục hook nào → hook ≤ **3** (rubric: "bắt được là fail ngay"). `total` = Σ trọng số.
`verdict = pass` khi `total ≥ 7` **và** `hook ≥ 8` — cả hai ngưỡng có từ 2026-08-04.
Hệ quả có chủ ý: lỗi lẻ ở pacing/tiếng Việt/CTA không đủ kéo `revise` (mỗi mục chỉ trừ
0,5–0,83 điểm total) — chỉ hook hỏng hoặc ≥ 4 mục trượt mới gửi về scriptwriter.

**Chống chê lấy lệ:** critic mặc định ĐẠT; trượt phải có `quote` nguyên văn — code đối
chiếu sau chuẩn hoá, không khớp → bỏ lời chê, ghi `dropped`. Critic không thấy điểm.

**"3 giây" đo thế nào** — đổi cách hiểu, ghi lý do: rubric §1 có câu "đọc to câu đầu, bấm
giờ, quá 3 giây → fail", nhưng scriptwriter cho hook ≤ 12 từ (2026-08-14) và giọng đọc đo
~2,1 từ/s (`out/p3b-s5-demo`: hook 11 từ = 5,3s) → mọi hook hợp lệ đều "quá 3 giây". Lấy
ý chính của rubric: **3 giây đầu phải đã "vào việc"** — `H_INFO` chấm đúng phần lời đọc
có `start < 3,0s` theo phụ đề karaoke trong `video-spec.json` (đo được); chưa có spec thì
ước 6 từ đầu. Khớp tài liệu TikTok "content proposition trong 3 giây đầu" (#ads, A cho organic).

**Hai luật mới vào `configs/rubric.md`** (todos P4.S2, từ research/07 2026-08-14):
1. CTA xin LƯU hoặc CHIA SẺ, không xin like → `C_SAVE_SHARE` (code). Bằng chứng trọng số chỉ R.
2. Ít nhất một câu quan sát trực tiếp, nguồn `research/probes/` → `A_*` **chỉ ghi vết**:
   scriptwriter hiện không được cấp số đo probe (brief có nguồn là P5.S3) — kéo verdict vì
   điều producer không làm được là đốt một vòng sửa vô ích. Bật thành mục chấm khi P5.S3 xong.

**Patch về scriptwriter:** `revision_notes(report)` → mỗi lỗi một dòng (mã · câu · trích ·
lý do · hướng sửa) → `scriptwriter.revise_script()` gửi kèm NGUYÊN script cũ, dặn "sửa
đúng những chỗ này, giữ nguyên phần còn lại", rồi qua lại `_check` bằng code. Nối vào vòng
lặp + dựng lại từ bước script là P4.S4.

## 4. Probe — tiêu chí viết trước khi chạy (2026-10-02)

Bộ mẫu chọn trước: **tốt đã biết** = 4 script khác nhau đã dựng thành video và qua mắt
Tony/demo: `demo-02`, `p3b-s4-demo`, `p3b-s5-demo`, `p4s0-resume` (p3b-a..d trùng script
demo-02). **Dở cố ý** = `bad-hook` (mở "Hôm nay chúng ta sẽ tìm hiểu về…", phần còn lại
lấy nguyên p3b-s5-demo) + `bad-many` (gài 5 lỗi: hook chào hỏi, "được … bởi", "một cách",
"mô hình ngôn ngữ lớn", CTA "like và follow"). Mỗi script chạy critic **3 lần**.

| # | Tiêu chí | Pass khi |
|---|---|---|
| 1 | **Xong khi (todos):** `bad-hook` → T3 bắt đúng lỗi hook | `verdict=revise`, có issue ở `hook (câu 0)`, **3/3 lần** |
| 1b | Critic tự bắt (không nhờ regex): `H_INFO` trượt trên `bad-hook` | ghi số — ≥ 2/3 lần thì tốt; không đạt không fail step (regex đã chặn) |
| 2 | `bad-many` → bắt từng lỗi gài | mỗi lỗi gài xuất hiện trong issues **3/3 lần** (cả 5 đều là mục code → phải tất định) |
| 3 | **Bẫy:** 4 script tốt không bị chê oan ở hook | `hook ≥ 8` ở **12/12** lượt (4 × 3) |
| 4 | Script tốt không bị gửi sửa vô ích | `verdict=pass` ở ≥ **10/12** lượt |
| 5 | Lời chê của critic trên script tốt | đọc từng cái, phân loại đúng/oan; ghi tỉ lệ `dropped` |
| 6 | Ổn định | verdict của cùng một script giống nhau ≥ 2/3 lần ở mọi script |
| 7 | Ghi vết | 100% lần gọi critic có token + thời gian trong `state.json` |

Nếu 3 hoặc 4 fail: KHÔNG sửa ngưỡng; ghi số, xem lời chê nào oan, sửa **câu hỏi checklist**
(định nghĩa mục) ở lần probe sau và ghi lý do + ngày.
