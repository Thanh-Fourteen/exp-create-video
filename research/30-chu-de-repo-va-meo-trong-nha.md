# Đổi hướng chủ đề: kênh AI → repo AI hot tuần · kênh mẹo → thân quen trong nhà — 2026-10-12

Tony: *"Kênh AI sửa thành gợi các repo hay, các kiến thức repo AI mới, hot trong tuần. Repo mẹo thì topic phải thân quen
trong nhà, thân thuộc. Research thêm về các topic này"*. Hai agent research song song; dữ liệu thô ở scratchpad phiên
(không lưu repo). **V** = tự đo · **R** = thứ cấp · **A** = suy luận.

## 1. Kênh AI — repo

**Nguồn (V, 2026-10-12, đã chạy thử):**

| Nguồn | Dùng | Ghi chú |
|---|---|---|
| github.com/trending/<lang>?since=weekly (HTML) | **chính** | có "sao tuần"; 12–15 repo/trang → gộp 7 ngôn ngữ |
| mshibanami.github.io/GitHubTrendingRSS (RSS) | dự phòng | không có sao tuần |
| api.github.com/search (created:>7 ngày, sort stars) | phụ | repo mới tinh; 10 lần/phút không token |
| trendshift.io (ld+json) | không | không có số sao |
| HF trending | không | chủ yếu model/"uncensored" cho dev |
| OSS Insight trends | không | đã chết (unavailable_since 2026-03-01) |

Lần chạy đầu: 51 repo AI. **~80% là đồ nghề dev** (agent, CLI, inference engine); chỉ ~5 repo/tuần hợp người phổ thông
(chấm tay — A): OpenCut (thay CapCut, có web), PixelBoard (gõ giọng nói Android), aurelio-finance, doory, DigUp.

**Khảo sát kênh Việt (V, yt-dlp, video ≥ 3 ngày):** chỉ @ainius.net làm repo đều (168 video repo, trung vị ×1,51 kênh);
@aidev.news ×1,15 (n=47); @ai5phut ×0,78 (n=8). Mẫu tiêu đề trên 215 video repo (× = view/trung vị kênh, có vs không):
"chạy local/offline/trên điện thoại" **×2,40** vs ×1,16 (n=22) · chữ kỹ thuật (agent, cli, npm, backend) ×0,98 vs ×2,22
(n=113) · bảo mật/lộ ×0,79 · "N sao" ×0,57 · "Top N GitHub tuần" ×0,93 (chập chờn 2K–84K). Kênh mình: 3 video repo
(ReelMimic 505, Strata 524, robot-heads 90) — n quá nhỏ.

**Đã làm:**
- `team/repo_feed.py` — code lấy danh sách (không LLM), cache `team/repo_feed/<ngày>.json` (gitignore).
- `idea_gen`: kênh có `trend.repo_feed: true` → chèn khối "ỨNG VIÊN REPO AI HOT TUẦN NÀY" vào đề bài + cho WebFetch kiểm
  README. Luật 4 ("rải đều pillar") giờ đọc từ `prompts.idea_mix` của kênh.
- `channel.yaml` AI: pillar mới `repo_hay`, `kien_thuc_repo`; `idea_search`/`idea_scope` viết lại: 1 repo/video, nỗi khổ/lợi
  ích trước, tên repo sau ":"; ưu tiên offline/điện thoại/thay app trả phí; chỉ repo ≥ 1.000 sao, license rõ, có demo, dùng
  không cần gõ lệnh; cấm đồ nghề dev, hack/uncensored, "N sao"/"Top GitHub"/chữ "repo" ở đầu tiêu đề; ≥ 3/4 ý tưởng là repo,
  1 ý/tuần dạng "3 app AI mã nguồn mở thay app trả phí".
- Researcher và snapshot fact-check đã nhận github.com (README + metadata API) — không phải sửa.

**Rủi ro (A):** nguồn hợp khán giả mỏng (~5/tuần) so với 2 bài/ngày → phần còn lại là `kien_thuc_repo` và dạng cũ; chữ
"GitHub" làm người phổ thông lướt đi; repo lỗi/malware (chặn bằng ≥ 1K sao + license + trang chủ).

## 2. Kênh mẹo — thân quen trong nhà

**Kênh mình (V, số 12/10 12:29):** bài trong nhà (5, đều bếp) trung vị 114 — tính bài ≥ 24h: **303**; ngoài nhà (12: lừa
đảo, luật, lũ, app, sale) 82,5. Hai bài cao nhất kênh là bếp (cơm nguội 1.053, đồ ăn thừa 510). n nhỏ — tín hiệu.

**7 kênh mẹo Việt (V, 851 video, nhãn gán tay theo caption):** gộp trong nhà bùng 18%, ngoài nhà 23% — chủ đề trong nhà
**không tự làm bùng**; dạng bùng nhất là tổng hợp nhiều mẹo có demo tay thật (37%) — kênh mình không quay được. Theo chủ
đề: bếp/sơ chế 29% (n=42), đồ dùng/sắp xếp 25% (n=40), dọn/khử mùi 16%, giặt 7% (n=14), bảo quản 0% (n=11, đều nhưng
không bùng). Mẫu tiêu đề bùng: "[việc nhà] + siêu tốc / siêu rẻ / cực nhàn", "Công dụng của [đồ sắp bỏ]", "N mẹo…".
Mùa: nồm là T2–T4 (R, FPT Shop) — T10–T11 là gió mùa đầu đông + hanh khô miền Bắc, mưa lũ miền Trung, 20/10, 11/11, 20/11.

**Đã làm:**
- Pillar mới `bao_quan`, `giat_don`, `do_dien`; `phap_luat`, `giao_tiep` → `mix: 0` (tạm dừng, giữ khoá cho video cũ);
  `tien_bac` 5% chỉ tiền điện nước/đi chợ, `dien_thoai` 5% chỉ việc nhà.
- `idea_search` bỏ lừa đảo/app/pháp luật; `idea_scope` thêm luật 1b "THÂN QUEN TRONG NHÀ".
- `idea_scout`: pillar `mix: 0` không được gợi ý; ý tưởng gốc có `disabled` bị bỏ qua (11 ý lừa đảo/ngân hàng/app trong
  `ideas.yaml` — khoá `off` ban đầu bị YAML 1.1 đọc thành `False`, đổi thành `disabled`).
- `calendar.yaml`: mùa mới "Gió mùa đầu đông" (10/10–30/11: chăn bông, bình nóng lạnh, điều hoà sưởi) đặt đầu danh sách;
  mùa mưa và mùa sale thay ý ngoài đường/lừa đảo bằng ý trong nhà.

## 3. Ngưỡng — viết trước khi có số

Đọc sau 14 ngày (26/10). Kênh AI: trung vị view 24h của video `repo_hay`/`kien_thuc_repo` ≥ trung vị view 24h kênh AI
trong cùng kỳ **và** lưu/view ≥ 0,6%. Kênh mẹo: trung vị view 24h ≥ 150 (mốc §1 research/29: 76–160 khi đăng 3–4 bài/ngày).
Trùng thời điểm với giảm tần suất + tiêu đề to (research/29 §6) → không tách được nguyên nhân; metric thật vẫn là view +
approve_rate.

## 4. Làm mới 2 trang ý tưởng — 2026-10-12 13:40–14:05 (Tony: "Đổi mới lại 2 trang ý tưởng")

- Mẹo: 16 ý mới, đều trong nhà (bếp, tủ lạnh, giặt, đồ điện, đầu đông) — $1,45.
- AI: hai lần đầu **vượt trần $1,5** (lượt thường đã $1,42–1,46; thêm 30 ứng viên + WebFetch README là vượt). Sửa:
  `repo_feed` loại đồ nghề dev bằng code (`DEV_RE`), nhận cả app cho người dùng không có chữ "AI" (`APP_RE` — OpenCut, DigUp
  từng bị loại), rút còn 15 ứng viên và **code lấy sẵn** license/trang chủ/README/có demo (`enrich`, GitHub API) → bỏ WebFetch,
  WebSearch ≤ 3. Lần 3: 10 ý (6 `repo_hay`: OpenCut, Ollama, DigUp, Aurelio, VoiceStudio, ai-engineering-from-scratch) — **$0,74**.
- 41 ý cũ kênh AI + 37 ý cũ kênh mẹo (máy sinh, chưa dùng) → `skip` kèm ghi chú "hướng cũ" (đảo lại được trên DB).

## 5. Kênh AI = TIN AI trong ngày/tuần + REPO MỚI — 2026-10-12 14:30 (Tony: "trang /ideas có repo AI, tin tức AI nào mới
đâu? Tôi cần là ý tưởng về tin tức AI mới trong ngày, trong tuần")

Lô §4 sai yêu cầu: OpenCut (93K sao), Ollama là repo cũ đang trending, không phải "mới"; không có tin. Sửa:
- **`team/news_feed.py`** (mới): RSS genk AI, Dân trí công nghệ (lọc từ khoá AI), The Verge AI, TechCrunch AI, OpenAI,
  Anthropic (RSS cộng đồng), DeepMind + Hacker News Algolia (≥ 150 điểm, tiêu đề AI). Kiểm sống 12/10 (V); VnExpress Số hoá
  và blog.google trả 0 mục với bot → bỏ. Lần đầu: 82 tin/7 ngày. Cache theo giờ (`team/news_feed/`, gitignore).
- **`repo_feed` viết lại**: bỏ scrape github.com/trending — `configs/sources.yaml` đã ghi cấm (Acceptable Use), bản §1 vi
  phạm, đã gỡ cùng RSS mirror. Giờ = GitHub Search API: repo **tạo trong 14 ngày**, 5 truy vấn (stars, topic ai/llm/
  generative-ai, "ai app"), repo AI xếp trước, mỗi chủ ≤ 2, lọc thêm pentest chữ CJK.
- `channel.yaml` AI: `trend.news_feed: true`; `idea_scope` "CHỈ CHUYỆN MỚI" — tin ≤ 7 ngày (ưu tiên 48h) hoặc repo ≤ 14 ngày,
  `why` mở bằng ngày sự kiện, tin kể bằng hệ quả cho người Việt, bỏ gọi vốn/nhân sự/hội nghị/benchmark; `idea_mix` 6/10 tin
  (≥ 3 tin trong 48h) + 4/10 repo.
- Chạy lại: 10 ý (6 tin 09–12/10, 4 repo tạo 01–06/10) — **$0,58**. 10 ý lô §4 → `skip` ("không phải tin/repo mới").
