# Biến repo thành một "team" — vai, cách nối, bằng chứng — 2026-10-01

**Yêu cầu Tony (2026-10-01):** repo thành một team hoàn chỉnh — tool research topic hot,
tool lên series, tool lập kế hoạch, tool viết caption… mỗi phase có research.
Ba lượt quét song song (kiến trúc team; trend + series; caption/đăng/phân tích). Mọi
link fetch 2026-10-01 trừ chỗ ghi *reported*. Nhãn: **V** verified · **R** reported · **A** assumed.

---

## 1. Kết luận kiến trúc — đọc cái này trước

**Team = Python điều phối + mỗi vai là MỘT lần gọi `query()` riêng, bàn giao qua file.**
KHÔNG để một LLM "tổng biên tập" tự sinh subagent cho cả chuỗi.

| Bằng chứng | Mức |
|---|---|
| Anthropic: agent ~4× token so với chat, multi-agent ~15×; multi-agent kém khi việc phụ thuộc tuần tự; subagent nên ghi output ra storage [anthropic.com/engineering/multi-agent-research-system, 2025-06] | V |
| Anthropic "Building effective agents": workflow (code định sẵn đường đi) trước, agent chỉ khi cần [2024-12] | V |
| MAST (1.642 trace, 7 framework): lỗi do thiết kế hệ 43,9% · lệch giữa các agent 31,8% · thiếu kiểm chứng 23,7%; viết rõ vai +9,4%, thêm bước kiểm +15,6% [arXiv 2503.13657, 2025-10] | V |
| Multi-agent từ +80,8% (việc chia nhỏ song song được) tới **−70%** (việc lập kế hoạch tuần tự) [Kim et al., arXiv 2512.08296, 2026-04] | V |
| Cùng ngân sách token, single-agent ngang/hơn multi-agent [arXiv 2604.02460, 2026-04]; gộp thành 1 agent + skills: −53,7% token [arXiv 2601.04748, 2026-01] | V |

Pipeline video là chuỗi **tuần tự** → đúng vùng bất lợi của multi-agent tự do. Nên:
mỗi vai là một hàm Python gọi `query()` với **context mới**, `output_format` = JSON
schema (Pydantic), ghi artifact vào `out/<id>/` hoặc `team/`; cổng kiểm giữa các vai là
**code**. Cách ly context như subagent mà quyền điều khiển nằm ở code.

**API Agent SDK đã kiểm** [code.claude.com/docs/en/agent-sdk, V]: `output_format=
{"type":"json_schema","schema":…}` → `ResultMessage.structured_output` (None = fail, kể
cả khi subtype "success"); tool tự viết `@tool` + `create_sdk_mcp_server`; hooks
`PreToolUse` chặn được Write ngoài thư mục; giới hạn `max_turns`, `max_budget_usd`,
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`. PyPI `claude-agent-sdk` 0.2.163.

⚠ **Chi phí 0đ phụ thuộc chính sách:** trang Legal nói *sản phẩm* dùng Agent SDK nên dùng
API key; bài support (2026-06-16) nói Pro/Max dùng SDK được, thay đổi credit đang tạm
hoãn. Dùng cho đúng một người (Tony) nhiều khả năng là "cá nhân" — **A, Tony tự xác nhận**.
→ ghi số lần gọi + token mỗi video vào `state.json` để biết mình tốn bao nhiêu.

## 2. Danh sách vai

| Vai | LLM hay code | Đầu vào → đầu ra | Phase |
|---|---|---|---|
| **Trend scout** (tìm topic hot) | code thu thập + 1 lần LLM chấm "hợp khán giả VN" | nguồn → `team/trends/<ngày>.json` + snapshot nguồn | P5.S1 |
| **Showrunner** (series + lịch tuần) | LLM, chạy hàng tuần | trends + analytics → `team/plan/<tuần>.json`, `out/<id>/brief.json` | P5.S2 |
| **Scriptwriter** | LLM (đã có) | brief → `script.json` có `claims[]` từng câu | P5.S3 (+P3b.S7) |
| **Fact-checker** (T4) | LLM context mới + WebFetch allowlist | script → `factcheck.json` (supported / contradicted / inconclusive + url + trích) | P4.S3 |
| Visual / voice / editor | code + model local (đã có) | → mp4 | P3/P3b |
| **QC** T1 code · T2 VLM · T3 critic | T1 code, T2/T3 model | → `qc/round-<n>.json` | P4 |
| **QC decider** | code, trần cứng 2 vòng | → `qc/decision.json` | P4.S4 |
| **Caption/SEO writer** | LLM + kiểm bằng code | → gói copy-dán `publish/` | P6.S1 |
| **Duyệt** (Tony) | code, bot Telegram | → `approval.json` | P6.S2 |
| **Publisher** | code, TikTok API draft | → `publish/upload.json` | P6.S3 |
| **Analyst** | code thu số + 1 lần LLM/tuần | → `team/analytics/` → về showrunner | P7 |

**Xương sống chung** (P4.S0): `out/<id>/state.json` do code ghi (stage, round, hash
đầu vào, số lần gọi LLM, token, lỗi) → chạy lại tiếp từ stage hỏng; mọi artifact LLM có
schema; giới hạn turns/budget mỗi lần gọi.

## 3. Trend scout + showrunner (vai đầu vào)

**Nguồn dùng được, 0đ** (V trừ chỗ ghi):
HF API `models?sort=trendingScore`, `spaces?sort=trendingScore`, `daily_papers` (không
key; 500 req/5 phút ẩn danh) · HF Papers trending (paperswithcode.com giờ 302 sang đây) ·
HN Algolia (`points>`, `created_at_i>`) · arXiv RSS cs.AI/CL/CV (1 req/3s) · RSS OpenAI,
DeepMind; Anthropic/Meta/Mistral qua repo `Olshansk/rss-feeds` (MIT, anthropic.com/rss
404) · GenK `ai.rss`, VnExpress `khoa-hoc-cong-nghe.rss` (phải ghi nguồn) · **Google
Trends RSS `geo=VN`** (chính thức, miễn phí — nhưng toàn chủ đề đại chúng, dùng đo độ
"phổ thông") · GitHub Search API `created:>D sort:stars` + tự chụp stars mỗi ngày ·
Arena leaderboard dataset (CC-BY-4.0). Qwen/DeepSeek: theo dõi qua HF `author=`.

**Loại:** TikTok (ToS) · X API (trả tiền) · Reddit (phải xin duyệt, `.json` chặn từ
2026-05, R) · Product Hunt (cấm thương mại) · scrape `github.com/trending` (Acceptable
Use không cho) · OSS Insight (rỗng từ 2026-03 vì GitHub mất event) · pytrends (archived).

**Chấm điểm:** dedupe URL → gom cụm bằng embedding đa ngôn ngữ (bge-m3, MIT — tin
Việt và Anh chung không gian) → `hot = Σ w·velocity · exp(−Δh/τ)` + số nguồn khác loại
xác nhận + `vn_fit` (có trên GenK/VnExpress/Google Trends VN) − trùng với video đã làm.
Velocity tính bằng code; LLM chỉ chấm "giải thích được trong 40s không".
**Snapshot nguồn:** HTML + text (trafilatura, Apache) lưu theo sha256 → fact-checker
đối chiếu `quote` nguyên văn, không để LLM tự nhớ.
Tham khảo kiến trúc: `duanyytop/agents-radar` (MIT) · `TrendRadar` (GPL — chỉ lấy ý).

**Showrunner:** 6 pillar khởi đầu (A): tin nhanh ~30s · demo tool ~40s · đập tin đồn
~35s · so sánh A/B ~45s · "chạy trên 2060 6GB" ngôi thứ nhất ~45s (lợi thế chống slop —
`research/07` §3) · tổng kết tuần 45–60s. **Series:** đánh số tập trong text + caption;
KHÔNG dựa vào TikTok Playlists (chưa mở cho mọi người, R; API không gắn được, V).
Backlog chấm kiểu ICE; ràng buộc ≤ 2 video cùng pillar liên tiếp, không trùng chủ đề 14
ngày. Nhịp: 2–5 video/tuần cho +17% view/post so với 1/tuần — số vendor Buffer, R.

## 4. Caption / đăng / phân tích (vai đầu ra)

Sự thật API TikTok [developers.tiktok.com, cập nhật 2026-08, V]:
- **Upload (draft/inbox) KHÔNG nhận** title, hashtag, cover, `is_aigc`, privacy → caption
  writer xuất **gói copy-dán** cho Tony; tiêu đề bìa phải **đốt sẵn vào frame 0**.
- Tối đa **5 bài chờ trong inbox / 24h**; init 6 req/phút; access token 24h, refresh 365 ngày.
- Không có tham số lên lịch → "lên lịch" = cron đẩy vào inbox trước giờ đăng.
- Display API `video.query`: view/like/comment/share, **chỉ video public**, 600 req/phút.
  **Không** có watch time / completion. Có qua Business API (`average_time_watched`,
  `full_video_watched_rate`) nhưng cần Business account — R; đổi sang Business có thể
  mất thư viện nhạc chung — R. Phương án 0đ: Tony export CSV từ TikTok Studio thả vào thư mục.
- Nhãn AI: bắt buộc với nội dung AI trông như thật; TikTok tự gắn qua C2PA [newsroom
  2023-09, 2026-03, V] → bật nhãn cho **mọi** video (ảnh diffusion + giọng TTS).
- Search: caption, hashtag, lời nói, chữ trên hình đều được dùng; nhồi keyword bị coi
  là spam [Creator Academy, R]. Tiếng Việt có/không dấu khi search: **không có số liệu**
  → probe tay. Số hashtag / giờ đăng: chỉ có vendor, mâu thuẫn nhau (Buffer vs Sprout).

**Analyst:** view TikTok đuôi rất dày, ít phụ thuộc follower [Guinaudeau et al. 2022,
~2M video, V] → so log(view+1) tại mốc cố định (t+72h), không so trung bình thô.
Metric chính vẫn `approve_rate`. Thử format/độ dài bằng Thompson sampling Beta-Bernoulli
trên approve [Russo 2017, V]; chỉ tuyên bố thắng khi mỗi nhánh ≥ 10 video và P ≥ 0,9 (A).

## 5. Kiểm chứng & giám khảo LLM — giới hạn đã biết

- **Fact-check:** kiểu VeriScore — chỉ rút claim kiểm chứng được, phán supported /
  contradicted / inconclusive trên top nguồn; cách rút claim được người chọn hơn SAFE
  93% [arXiv 2406.19276, V]. SAFE khớp người 72% [2403.18802, V]. Repo mẫu cùng thiết kế
  trần 2 vòng rồi chặn: `AlgoDr/AI-Newsroom-Studio`, `Miloop-AI/factloop-newsroom` (MIT, ít sao).
- **LLM chấm "hay/sáng tạo" yếu:** tương quan ~0 với chuyên gia [Chakrabarty, CHI 2024,
  V]; Creativity τb=0,23, Novelty không có ý nghĩa thống kê [arXiv 2608.23705, 2026-08,
  V]; LLM ưu ái output của chính nó [arXiv 2404.13076, V]. → T3 dùng **checklist nhị phân
  cụ thể**, chấm pointwise (pairwise lật kết luận ~35% [2504.14716, V]), context mới,
  và **phải tương quan với approve của Tony sau 20 video, không thì bỏ**.
- **Tự sửa không có tín hiệu ngoài làm tệ đi** [Huang et al., 2310.01798, V]; có tín
  hiệu ngoài (tool, lỗi cụ thể) thì giúp [CRITIC, Reflexion, V] → mỗi vòng sửa phải
  mang lỗi cụ thể từ T1/T2 hoặc url từ fact-check, không bao giờ "viết hay hơn".
- **Telegram:** bot gửi tối đa **50 MB** (V) → kiểm kích thước trước khi gửi; long
  polling (máy nhà, không cần HTTPS); `callback_data` ≤ 64 byte; update giữ 24h.

## 6. Hệ quả cho lộ trình (todos.md)

P4 thêm **S0 xương sống team**; P4.S3 theo kiểu VeriScore. P5 thành **phòng tin**
(trend scout · showrunner · brief→script). P6 mới = **phân phối** (caption/SEO · Telegram ·
publisher · cron). P7 mới = **vòng phản hồi** (analyst · thử format/độ dài · xem lại QC
sau 20 video — chuyển từ P4.S5/S6). Mọi phase: BƯỚC 0 research trước khi code.
