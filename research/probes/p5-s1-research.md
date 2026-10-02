# P5.S1 — BƯỚC 0 research: trend scout — 2026-10-02

Một lượt paper-scout kiểm từng endpoint (sống? rate limit? lọc theo ngày được không?) + model
embedding + trafilatura; nền là research/10 §3 (2026-10-01). Mọi endpoint fetch 2026-10-02.
**V** verified · **R** reported · **A** assumed.

## 1. Nguồn

| Nguồn | Loại (`kind`) | Sống | Rate limit / ToS | Backfill theo ngày | Mức |
|---|---|---|---|---|---|
| HF `api/daily_papers?date=` | paper | ✓ | ẩn danh 500 req / 5 phút / IP [HF docs, "Sep '25"] | **có** | V |
| arXiv `export.arxiv.org/api/query` `submittedDate:[..]` (cs.AI, cs.CL, cs.CV, cs.LG) | paper | ✓ (487 bài / 2 ngày cs.AI) | 1 req / 3s, 1 kết nối [info.arxiv.org tou] | **có** | V |
| HN Algolia `search?tags=story&numericFilters=created_at_i>..,points>..` | forum | ✓ | 10.000 req/giờ/IP | **có** | V (endpoint) / R (limit) |
| GitHub `search/repositories?q=created:>D topic:..&sort=stars` | repo | ✓ | không token 10 req/phút | **có** — nhưng số sao là HIỆN TẠI | V |
| HF `api/models?sort=trendingScore` | model | ✓ | như HF trên | **không** (chỉ hiện tại) | V |
| RSS: openai.com/news/rss.xml · deepmind.google/blog/rss.xml · research.google/blog/rss/ · blog.google/technology/ai/rss/ · huggingface.co/blog/feed.xml · Olshansk/rss-feeds `feed_anthropic_news.xml` (MIT) | blog | ✓ cả 6 | — | lọc theo `pubDate` (feed giữ 25–50 bài) | V |
| genk.vn/**rss/ai.rss** (genk.vn/ai.rss = 404) · vnexpress.net/rss/so-hoa.rss | news_vn | ✓ | ghi nguồn khi dùng | `pubDate` | V |
| Google Trends RSS `geo=VN` | vn_pulse | ✓ — toàn từ khoá đại chúng | — | không | V |

**Loại giữ nguyên research/10 §3:** TikTok, X API, Reddit, Product Hunt, scrape github.com/trending,
OSS Insight. `configs/sources.yaml` (2026-08) còn `github_trending` scrape + `reddit_localllama`
→ viết lại.

## 2. Embedding để gom cụm (tiêu đề Việt + Anh chung không gian)

| Model | License | Cỡ | Ghi chú | Kết luận |
|---|---|---|---|---|
| **intfloat/multilingual-e5-base** | MIT | 278M, 768 chiều, 512 token | transformers thuần, mean pooling, prefix "query: "; fp16 nhẹ / CPU đủ | **Chọn** |
| Qwen3-Embedding-0.6B | Apache-2.0 | 0,6B | MTEB đa ngôn ngữ 64,33 (card) | dự phòng nếu cụm Việt–Anh kém |
| BAAI/bge-m3 | MIT | 568M | todos gợi ý | nặng gấp đôi e5-base cho tiêu đề ngắn — không cần |
| paraphrase-multilingual-MiniLM-L12-v2 | Apache | 118M | trần 128 token | loại — cắt summary |
| jina-embeddings-v3 | **CC-BY-NC** | — | — | loại (NC) |
| EmbeddingGemma-300m | Gemma | 300M | card: không hỗ trợ fp16 | loại |

## 3. Trích text

trafilatura 2.2.0 (2026-07) Apache-2.0 [PyPI, V] — dùng cho trang bài viết (blog, báo VN, bài HN
dẫn tới) vì `html.parser` stdlib kéo theo menu/footer; API có cấu trúc (HF/arXiv/GitHub) giữ đường
cũ của `team/snapshot.py`. Snapshot trend scout cho phép domain NGOÀI allowlist của fact-checker
(bài HN dẫn đi khắp nơi) nhưng đánh dấu `kind=article`.

## 4. Thiết kế — VIẾT TRƯỚC KHI CHẠY (2026-10-02)

1. **Thu (code):** mỗi nguồn → item `{url, title, summary, source, kind, published_at, metrics}`;
   bỏ item cũ hơn **14 ngày** so với ngày chạy; dedupe URL chuẩn hoá (bỏ query utm, `/abs/` vs `/pdf/`).
   HN: lọc từ khoá AI (danh sách trong `configs/sources.yaml`). arXiv: chỉ lấy để làm **bằng chứng
   xác nhận** cụm, không tự đứng thành topic (≈ 500 bài/ngày, toàn ngách) — trừ khi được HF daily
   papers / HN nhắc tới.
2. **Velocity (code), chuẩn hoá theo percentile trong từng nguồn:** HN điểm/giờ · daily papers
   upvote · HF models trendingScore · GitHub sao/ngày tuổi · blog/news_vn = 0,5 cố định.
   **Suy giảm** `exp(−Δh/48)`.
3. **Gom cụm:** e5-base, cosine; nối hai item khi cos ≥ **0,86** (union-find), cụm ≤ 12 item.
   Ngưỡng này là tham số gom cụm, đặt trước; thấy cụm dính/vỡ thì ghi lại và đổi có lý do.
4. **Điểm cụm (code):** `hot = Σ w_kind · v · decay` + `0,5 · (số kind khác nhau − 1)` + `vn_fit`
   (0,5 nếu có item news_vn; +0,25 nếu khớp từ khoá Google Trends VN) − trùng video đã làm 30
   ngày (cos ≥ 0,86 với `topic`/hook các `out/*/script.json` → ×0,3). Trọng số `w_kind` ở
   `configs/sources.yaml`.
5. **LLM (`run_role` "trend_judge", 1 lần/ngày, context mới)** cho top 12 cụm, kèm text snapshot
   (≤ 3.000 ký tự/nguồn, 2 nguồn/cụm): `label_vi`, `vn_fit_reason`, `explainable_40s` (bool + lý do),
   `claims[] {text, quote, url}`. **Code** giữ claim khi `quote` có nguyên văn trong snapshot của
   `url`; LLM không đổi `hot`, chỉ `explainable_40s=false` → xếp sau.
6. **Snapshot:** mọi URL của top cụm qua `team/snapshot.py` (sha256) — fact-checker P4.S3 đọc lại.
7. **Output:** `team/trends/<YYYY-MM-DD>-<am|pm>.json` + `state.json` cạnh đó ghi llm_calls.

## 4b. Đổi sau lần chạy thử đầu — 2026-10-02, TRƯỚC khi đo tiêu chí

Lần chạy thử hôm nay (`out/p5-s1-trend/try/`, `--no-judge`) cho thấy ba lỗi thiết kế, không phải
kết quả tiêu chí:

1. **Gom cụm bằng cosine 0,86 nối bừa.** Đo trên 90 tiêu đề hôm nay: cosine e5-base giữa cặp bất kỳ
   trung vị **0,78**, p90 0,83, p99 **0,87** — nền quá cao (cụm "Identity Management for Agentic AI"
   dính "Introducing SynthID Bio" và một repo phân tích học tập). Cặp đúng thì chung **tên riêng**
   (GPT-6.1 Sol 0,98; Muse 0,88; Qwen-Image 2.1 0,90). → nối khi cos ≥ **0,93**, hoặc cos ≥ **0,82**
   VÀ chung khoá tên riêng (`entity_keys`: token có số / CamelCase / viết hoa giữa câu, bỏ tên hãng
   và từ chung; tiêu đề Title Case chỉ xét token có số/CamelCase). Luật "trùng video đã làm" dùng cùng luật nối.
2. **Điểm cộng dồn theo item**: cụm 6 model HF (bản GGUF/quantize) được base 5,5 — gấp 5 lần cụm có
   tin từ 4 loại nguồn. → base = tổng theo **nguồn** của item mạnh nhất mỗi nguồn.
3. arXiv trả **429** sau lần chạy bị `timeout` giết giữa chừng → retry theo `Retry-After` (≤ 60s, 2 lần).

4. Lần chạy thử thứ hai (có LLM, `out/p5-s1-trend/try2/`) — top-10 đã có nghĩa (Gemini 4 Argon vs
   GPT-6.1 Sol, Janus/OpenDLSS, ChatGPT Pro 500 USD…), nhưng union-find **nối chuỗi**: repo GitHub lạc
   vào cụm Barclays/Claude Code, tin startup lạc vào cụm ChatGPT Pro — và item lạc thổi phồng chính
   tiêu chí "≥ 2 nguồn khác loại". → gom kiểu **leader**: item mạnh nhất làm hạt nhân, item khác chỉ
   vào cụm khi nối TRỰC TIẾP với hạt nhân. arXiv timeout 30s → 90s.

Cũng giới hạn output/snapshot 6 item/cụm và tải song song 8 luồng (lần đầu tuần tự > 15 phút).

## 5. Probe — tiêu chí

"Xong khi" của todos (viết 2026-10-01) **giữ nguyên**. Cách đo thay đổi một chỗ, ghi trước:
"chạy thử 7 ngày" không xong được trong một phiên → **backfill 7 ngày** (2026-09-26 … 10-02) bằng
các nguồn lọc được theo ngày (daily papers, HN, arXiv, GitHub `created:`; RSS lọc `pubDate`) để đo
các tiêu chí MÁY; HF trending models chỉ có ở ngày hôm nay. Giới hạn đã biết của backfill: snapshot
và số sao GitHub là của hôm nay, không phải của ngày D. **Tiêu chí Tony chấm mù top-10 + chạy thật
2 lần/ngày** để lại → step ở trạng thái `[~]` tới khi có.

| # | Tiêu chí (todos) | Đo |
|---|---|---|
| 1 | 100% item có url sống + ngày ≤ 14 ngày | url sống = snapshot tải được (HTTP 2xx); ngày từ nguồn |
| 2 | ≥ 80% top-5 mỗi ngày có ≥ 2 nguồn khác loại | đếm `kind` khác nhau mỗi cụm, 7 ngày × 5 = 35 cụm |
| 3 | 100% `claims[].quote` có nguyên văn trong snapshot | code kiểm (claim trượt bị bỏ — đếm cả số bị bỏ) |
| 4 | Tony chấm mù top-10 ≥ 50% "đáng làm" | **chờ Tony** — file chấm mù sinh sẵn |
