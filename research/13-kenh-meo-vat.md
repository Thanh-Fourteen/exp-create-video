# Kênh thứ 2 "Mẹo vặt cuộc sống" — tuyến nội dung + nâng web thành nhiều kênh — 2026-10-04

**Yêu cầu Tony (2026-10-04):** lập thêm 1 kênh mẹo vặt đời sống (thực phẩm, cuộc sống, giao tiếp…). Research:
kênh nên phát triển tuyến nội dung gì · web nên update thế nào cho kênh mới · layout · nội dung.

3 paper-scout song song (tuyến nội dung + rủi ro · nguồn trend/kiểm chứng/hình ảnh/luật · UX nhiều kênh) + 1 Explore
rà code. Link fetch 2026-10-04. **V** verified · **R** reported · **A** assumed.

---

## 0. Năm sự thật đổi cách làm — đọc trước

| # | Sự thật | Hệ quả | Nguồn |
|---|---|---|---|
| 1 | Kênh mẹo vặt lớn (5-Minute Crafts 80,5M sub YT, Blossom) **quay thật** cảnh tay + đồ vật | Mẹo "làm bằng tay" (lau chùi trước/sau, kỹ thuật nấu, gấp, cắt) **không làm được** khi pipeline không quay. Dùng ảnh AI cho loại này thì nhìn giả, mà đây chính là loại hay bị bóc mẽ | Wikipedia 5-Minute_Crafts (V, 2026-07); Futurism 2026-03-27: video công thức AI-gen nấu thử thất bại (V) |
| 2 | TikTok CG 2025-09-13: thông tin sức khoẻ sai gây hại vừa phải hoặc "claim phóng đại về ăn kiêng" thì bị **loại khỏi For You**. Mẹo nguy hiểm thì bị gỡ. Nội dung "chỉnh sửa tối thiểu / không nguyên bản" cũng bị loại khỏi For You | Tuyến sức khoẻ/thực phẩm phải có fact-check **gắt hơn** kênh AI | OpenTermsArchive mirror TikTok CG (V) |
| 3 | **NĐ 174/2026** (hiệu lực 2026-07-01): phạt 30–50 triệu nếu chia sẻ tin sai gây hoang mang. **NĐ 142/2026** (hiệu lực 2026-05-01): phải gắn nhãn nội dung AI nếu nó có thể làm người xem nhầm là thật, **kể cả giọng mô phỏng** | Ghi rõ "Nội dung do AI tạo" (checklist đã có) + bật nhãn AIGC của TikTok. Giọng clone của Tony: nên gắn nhãn cho chắc | VnExpress 2026-05-22 (V, bài báo, chưa đọc văn bản gốc); VOH (V) |
| 4 | **Creator Rewards Program chưa mở ở VN**. Hiện chỉ có 8 nước, yêu cầu video ≥ 1 phút | Ở VN, kiếm tiền là **TikTok Shop affiliate / LIVE**. Mẹo bếp và nhà cửa rất hợp gắn affiliate, nhưng khi nhắc sản phẩm thì **Luật QC 75/2025** (hiệu lực 2026-01-01) bắt người đăng chịu trách nhiệm về độ trung thực | quasa.io 2026-07-27 (R), ai-hay.vn (R), luatvietnam (R) |
| 5 | **Không có API trend mẹo vặt nào free + hợp lệ cho VN.** Reddit API thương mại phải xin riêng. Pinterest Trends không có VN. YouTube `mostPopular` từ 2025-07 chỉ còn Music/Movies/Gaming. RSS báo VN chỉ cho dùng "cá nhân/phi lợi nhuận" | Trend scout của kênh mẹo **không thể** là bản sao trend scout AI. Phải dựa vào **lịch mùa + kho ý tưởng evergreen + Google Trends VN** | xem §3 |

Hai hệ quả lớn: (a) chọn tuyến nội dung theo tiêu chí **"làm được không cần quay"**, không phải "cái gì đang hot";
(b) tuyến sức khoẻ/thực phẩm chỉ làm khi T4 có allowlist nguồn y tế.

---

## 1. Tuyến nội dung (content pillars) — đề xuất

Tiêu chí lọc: (1) làm được bằng thẻ chữ, ảnh AI đồ vật (không người), stock video, ảnh chụp màn hình thật;
(2) có nguồn kiểm chứng được; (3) hợp khán giả phổ thông VN; (4) rủi ro chính sách thấp. (A, suy từ §0)

| Pillar | Ví dụ chủ đề | Làm hình bằng gì | Nguồn kiểm | Rủi ro | Đề xuất |
|---|---|---|---|---|---|
| **giao_tiep** — giao tiếp & ứng xử | "3 câu nên nói khi bị sếp phê bình" · "cách từ chối cho vay mà không mất lòng" · "đừng nói câu này khi đi đám" | thẻ chữ/hội thoại kiểu chat, ảnh AI bối cảnh không người | sách/bài tâm lý có tác giả; dễ thành ý kiến → cần khung "gợi ý", không khẳng định khoa học | thấp | **Có — trụ chính** (có kênh mặt tương tự ~439K follower: @tamlyhocthanhcong, R) |
| **tien_bac** — tiền & tiết kiệm | "quy tắc 50/30/20" · "phí ẩn khi rút tiền thẻ tín dụng" · "dấu hiệu tin nhắn lừa đảo ngân hàng" | thẻ số, bảng so sánh, **chụp trang thật** (biểu phí ngân hàng, cảnh báo NHNN) — tận dụng thế mạnh hiện có | trang ngân hàng, sbv.gov.vn, Bộ Công an cảnh báo lừa đảo | thấp-vừa (số phải đúng ngày) | **Có — trụ chính** |
| **dien_thoai** — điện thoại & công nghệ đời thường | "tắt cài đặt này để pin trâu hơn" · "Zalo có tính năng ẩn…" · "kiểm tra app nào đang theo dõi vị trí" | **quay màn hình / chụp màn hình thật** | trang hỗ trợ Apple/Google/Samsung/Zalo | thấp | **Có** — gần kênh AI nhất, pipeline làm tốt nhất |
| **bep_an_toan** — thực phẩm: chọn, bảo quản, an toàn | "thịt rã đông để được bao lâu" · "4 thứ đừng cho vào tủ lạnh" · "cách nhận biết giá đỗ ngâm hoá chất" | ảnh AI thực phẩm (FLUX làm đồ vật tốt), thẻ số, stock video | **Cục ATTP, Viện Dinh dưỡng, USDA FoodKeeper** | vừa — phải có nguồn T1 | **Có**, nhưng chỉ dạng "biết/tránh", **không** dạy kỹ thuật nấu |
| **theo_mua** — nhà cửa theo mùa | nồm ẩm (đỉnh tháng 3–4 miền Bắc, V VOV) · mùa mưa · nắng nóng tiết kiệm điện · Tết dọn nhà | checklist thẻ chữ, ảnh AI, stock | EVN, NCHMF, Bộ Công Thương | thấp | **Có** — nhóm lịch (§3) |
| **suc_khoe_thoi_quen** — thói quen sức khoẻ | ngủ, ngồi, mắt màn hình, uống nước | thẻ chữ | **chỉ T1**: Bộ Y tế, WHO, CDC, Mayo | **cao** (CG + NĐ 174) | **Để sau** — chỉ mở khi T4 kênh mẹo chạy đủ 20 video không lỗi |
| ~~lau chùi trước/sau, DIY, làm đẹp, pha hoá chất, kỹ thuật nấu~~ | | cần quay thật | | cao (bleach + giấm → khí clo, Forbes 2025-08, R) | **Không làm** |

**Tỉ lệ pha (A):** không có nguồn nào cho con số chuẩn. Con số "40/30/20/10" hay thấy trên mạng không tìm được gốc;
Hootsuite chỉ có quy tắc 80/20 cho nội dung giá trị/quảng bá (R). Đề xuất khởi đầu: giao_tiep 30 · tien_bac 25 ·
dien_thoai 20 · bep_an_toan 15 · theo_mua 10 (lấy chỗ khi tới mùa). Sau 20 video thì đổi theo `approve_rate`
từng pillar. Trang Thống kê đã nhóm "Theo pillar".

### Format (cách kể) — dùng chung cho mọi pillar

| Format | Mẫu hook | Bằng chứng |
|---|---|---|
| **"Bạn đang làm sai"** (myth vs fact) | "Đa số người Việt rã đông thịt sai cách" | blog vendor nói ~3× bình luận — **R yếu** |
| **Danh sách 3 mẹo** | "3 câu giúp bạn từ chối khéo" | A |
| **Series đánh số** "Mẹo #12" | số lớn ở góc → người xem lướt hồ sơ | A; playlist cần ≥10K follower (SocialBee 2024-12, R) |
| **Cảnh báo** "Đừng làm X" | "Đừng bấm vào link này dù là ngân hàng gửi" | A |
| **Checklist theo mùa** | "Nồm ẩm: 5 việc làm ngay hôm nay" | A |

Bằng chứng cứng duy nhất là từ **quảng cáo**, không phải video tự nhiên: >63% quảng cáo CTR cao nhất nói thông
điệp chính trong 3s đầu; 40% dùng chữ overlay ngắn (TikTok for Business PDF, V). Rubric hook hiện tại (≤ 7 từ,
frame 0 là bằng chứng) vẫn dùng được, chỉ phải thay ví dụ.

**Nhịp đăng:** 2–5 video/tuần là điểm hiệu quả; đăng nhiều hơn chủ yếu tăng cơ hội có 1 video bùng (Buffer, 11,4M
bài, 2025-10, V). Hai kênh × 3 video/tuần = 6 video/tuần ≈ 2,5 giờ máy, vừa sức worker 1 job/lần.

---

## 2. Hình ảnh khi không quay

| Cách | Dùng cho | License / giới hạn | Trạng thái |
|---|---|---|---|
| FLUX.2-klein-4B (đang có) — đồ vật, thực phẩm, bối cảnh **không người** | bep, theo_mua, giao_tiep (bối cảnh) | Apache-2.0 (V) | có sẵn; cần probe chất lượng ảnh thực phẩm VN (rau muống, giá đỗ…) |
| **Stock video Pexels API** | b-roll thật: bếp, mưa, đường phố | thương mại OK, không bắt ghi công. Dùng **qua API** thì yêu cầu ghi "Video by X on Pexels" khi có thể → đưa vào caption/nguồn. 200 req/giờ, 20k/tháng (V) | **mới — khối visual `stock`** |
| Stock Pixabay API | dự phòng | thương mại OK; **bắt buộc cache 24h, cấm hotlink**; có `lang` (V) | mới |
| Coverr | dự phòng | thương mại OK, có API, **cấm dùng để train AI** (V) | tuỳ |
| Chụp/quay màn hình thật (Playwright, đang có) | tien_bac, dien_thoai | trang công khai | có sẵn; mở rộng allowlist domain |
| Thẻ chữ / hội thoại kiểu chat (Remotion) | giao_tiep | — | **mới — kiểu shot `chat`** (bong bóng tin nhắn, hợp "nói câu này") |
| ~~Text-to-video local~~ | | Wan2.1-1.3B cần 8,19GB (V); LTX-2 cần 6GB + 44GB RAM (R, máy chỉ 31GB); license LTX không phải Apache | **Loại** trên máy hiện tại |

Quy tắc "không người" giữ nguyên ở kênh mẹo: FLUX vẽ tay hay hỏng, và NĐ 142 + TikTok CG bắt gắn nhãn cảnh người
giống thật (V). Stock video có người thật là **người quay thật**, không phải AI → được dùng, nhưng phải tránh ngụ ý
họ xác nhận sản phẩm (Pexels license, V). → cờ theo kênh `people: none | stock_only`.

---

## 3. Gợi ý chủ đề (trend scout kênh mẹo)

Không có "trend hôm nay" kiểu HF/arXiv cho mẹo vặt. Đề xuất 3 nguồn, xếp theo trọng số (A):

1. **Lịch mùa VN** (`configs/channels/meo/calendar.yaml`): nồm ẩm T3–T4 (V) · nắng nóng T4–T7 · mùa mưa miền Nam
   T5–T11 · khai giảng 5/9 · Trung thu · Tết · mùa thuế/quyết toán · Black Friday/11.11 (lừa đảo mua sắm). Mỗi mục có
   cửa sổ ngày + 5–10 chủ đề gốc. Ngày các mùa trừ nồm ẩm là **A**, cần kiểm trước khi dùng.
2. **Kho ý tưởng evergreen theo pillar** (idea bank). Claude sinh 30 ý tưởng/pillar → Tony gạch bỏ trên web → máy
   lấy dần, cân theo tỉ lệ pha. Ý tưởng đã làm thì loại theo **từng kênh** (hiện `done_topics` quét mọi `out/*`, phải
   tách theo kênh).
3. **Google Trends VN**: RSS "Trending now" `geo=VN` còn chạy (V) nhưng chủ yếu thể thao/xổ số → chỉ để bắt tin nóng
   (vd. lừa đảo kiểu mới). Thư viện `trendspyg` 1.9.0 (MIT, 2026-10-01, V) lấy **related queries** cho từ gốc
   ("cách", "mẹo", "làm sao để") → biết người Việt đang tìm gì. `pytrends` đã archive (R).
4. Tiêu đề RSS báo VN (VnExpress Sức khỏe/Gia đình, Dân trí Đời sống, Tuổi Trẻ — V) **chỉ làm tín hiệu chủ đề**.
   Không chép nội dung: điều khoản chỉ cho "cá nhân/phi lợi nhuận" (V).

Loại: Reddit (dùng thương mại phải xin riêng, R) · Pinterest (không có VN, R) · YouTube trending (đã bỏ, V/R) ·
TikTok (luật của dự án).

---

## 4. Kiểm sự thật kênh mẹo — allowlist theo tầng

| Tầng | Domain | Được làm gì |
|---|---|---|
| **T1** — căn cứ cho claim sức khoẻ/thực phẩm | vfa.gov.vn (Cục ATTP) · viendinhduong.vn · moh.gov.vn · who.int · fsis.usda.gov (FoodKeeper) · fda.gov · cdc.gov | duy nhất được dùng cho claim loại `health` / `food_safety` |
| **T2** — đối chiếu | mayoclinic.org · health.harvard.edu · suckhoedoisong.vn (báo của Bộ Y tế) · sbv.gov.vn · trang ngân hàng · trang hỗ trợ Apple/Google/Samsung/Zalo · evn.com.vn | claim tiền, điện thoại, nhà cửa |
| **T3** — chỉ là lead | vnexpress · dantri · tuoitre · kenh14 · afamily | **không** được làm căn cứ cho claim sức khoẻ |
| **Danh sách đen** | mẹo đã bị bóc mẽ (How To Cook That / Ann Reardon, MIT Tech Review 2022, R) | researcher phải loại |

Domain đều đã fetch 2026-10-04 (V), trừ who.int, fda/cdc/mayo/harvard (chưa fetch hoặc bị 403 → A).
Loại claim T4 mới cho kênh mẹo: `health_claim`, `food_safety`, `money_number` (phí, lãi suất — **kèm ngày**),
`legal` (mức phạt). Claim `health_claim` không có nguồn T1 → **chặn**, giống mâu thuẫn ở kênh AI.
Thêm câu disclaimer cố định trong caption cho bep/suc_khoe: "Thông tin tham khảo, không thay lời khuyên bác sĩ" (A).

---

## 5. Pipeline — từ "một kênh AI" thành "nhiều kênh"

Explore rà được ~40 chỗ gắn cứng kênh AI. Phần lớn dễ đổi. Bốn chỗ khó: danh sách pillar (định nghĩa **3 lần**:
`agents/researcher.py:40`, `agents/scriptwriter.py:55`, `web/library.py:25`), collector của trend scout, allowlist
`team/snapshot.py:43`, allowlist chụp màn hình `visual/screenshot.py`.

**Thiết kế (A):** một thư mục cấu hình mỗi kênh, code đọc theo `--channel`.

```
configs/channels/
  ai/    channel.yaml  rubric.md                (chuyển nguyên trạng từ chỗ cũ → kênh AI không đổi hành vi)
  meo/   channel.yaml  rubric.md  calendar.yaml  ideas.yaml
```

```yaml
# configs/channels/meo/channel.yaml (phác)
id: meo
name: "Mẹo vặt mỗi ngày"          # Tony đặt
accent: "#F2B544"                  # màu nhận diện trên web + bìa
audience: "người Việt 18–45, phổ thông"
pillars:                           # NGUỒN DUY NHẤT — researcher/scriptwriter/web đọc từ đây
  giao_tiep:  {vi: "Giao tiếp",       mix: 0.30}
  tien_bac:   {vi: "Tiền bạc",         mix: 0.25}
  dien_thoai: {vi: "Điện thoại",       mix: 0.20}
  bep_an_toan:{vi: "Bếp & thực phẩm",  mix: 0.15}
  theo_mua:   {vi: "Theo mùa",         mix: 0.10}
sources: {tier1: [...], tier2: [...], lead_only: [...], screenshot_domains: [...]}
t4: {require_tier1_for: [health_claim, food_safety], block_unsourced: true}
people: stock_only
keep_english_terms: false          # kênh AI: true (model, fine-tune…)
style: {palette: {...}, flux_suffix: "bright clean kitchen, soft daylight", music: "warm acoustic ukulele"}
voice: tony                        # hoặc 1 giọng preset riêng để 2 kênh nghe khác nhau
caption: {disclaimer: "...", hashtags_base: ["meovat", "meohay"]}
trend: {collectors: [calendar, ideas, gtrends_vn], schedule: "06:30"}
series: {prefix: "Mẹo #"}
```

| Chỗ đổi | Việc | Công |
|---|---|---|
| `pipeline.py` CLI | thêm `--channel` (mặc định `ai`); ghi vào `job.json` + `result.json` | dễ |
| researcher / scriptwriter | SYSTEM, ví dụ hook, pillar `Literal` → đọc từ channel.yaml (chuyển sang `str` + kiểm hợp lệ) | vừa |
| `scriptwriter._check` | luật "không người", luật giữ thuật ngữ tiếng Anh → bật/tắt theo kênh | vừa |
| QC T3 `t3_appeal.py` | V_TERMS, "kênh về AI", A_FIRSTHAND → theo kênh | dễ |
| QC T4 `t4_facts.py` + `snapshot.py` | ClaimType + allowlist theo tầng của kênh | vừa |
| visual | allowlist chụp màn hình theo kênh · STYLE_SUFFIX FLUX · **khối `stock` mới** (Pexels) · **shot `chat` mới** (Remotion) | vừa–lớn |
| sound | caption nhạc ACE-Step theo kênh (cache theo seed + kênh) | dễ |
| cover.py, style.yaml, remotion placeholder | palette theo kênh | dễ |
| trend_scout | collector cắm theo kênh: `calendar`, `ideas`, `gtrends_vn` mới; `done_topics` lọc theo kênh; `team/trends/<kênh>/` | **lớn** |
| `configs/pronounce.yaml` | thêm từ khó đọc của kênh mẹo | dễ |
| eval | **3 spec cố định riêng cho kênh mẹo** ở `eval/scripts/meo/` (luật eval-discipline) | dễ |

Ranh giới cũ giữ nguyên: Remotion vẫn chỉ đọc `video-spec.json`. Kênh chỉ đổi dữ liệu trong spec (palette, kiểu
shot), không gọi chéo.

---

## 6. Web — cập nhật cho nhiều kênh

### 6.1 Nguyên tắc (từ research UX)

| Nguyên tắc | Nguồn |
|---|---|
| Mỗi kênh là một **không gian riêng** (lịch, thống kê, tài khoản riêng), chuyển bằng **1 bộ chọn toàn cục ở góc trên-trái** | Metricool (V), Linear (V), Planable (V) |
| Chọn sai chế độ là lỗi chính → phải có **≥ 2 dấu hiệu dư thừa** cho kênh đang chọn (màu + tên), ghi tên ngay trên nút hành động quan trọng | NN/g "Modes" (V) |
| Cần **1 góc nhìn "Tất cả"** để thấy tổng khối lượng việc | Planable (V) |
| Pillar làm **nhãn màu**, lọc báo cáo theo nhãn | Planable, Hootsuite (V/R) |
| Hồ sơ kênh lưu: tên, logo, màu, font, kiểu phụ đề, giọng/tone, hashtag mặc định | OpusClip brand template (V), Canva brand voice ≤ 500 ký tự (R) |
| Trên điện thoại, bộ chọn workspace nằm ở **thanh trên**, kèm icon dễ nhận | Slack Android (R) |
| Mô hình kho ý tưởng → Kanban (Ý tưởng → Đang làm → Chờ duyệt → Đã đăng) | template Notion (R) |

### 6.2 Bố trí cụ thể (A, dựa trên bảng trên + layout chốt ở `research/12` §9)

| Chỗ | Laptop (≥1024px) | Điện thoại |
|---|---|---|
| **Bộ chọn kênh** | đỉnh menu trái: chấm màu + tên kênh + ▾ → danh sách kênh + "Tất cả kênh". Phím tắt `g k` | thanh trên: viên tròn màu + tên ngắn, chạm để mở sheet chọn kênh |
| **Dấu hiệu kênh** (≥ 2) | (1) dải màu accent 3px ở mép trên trang + viền mục menu đang chọn; (2) tên kênh trong tiêu đề trang ("Tạo video · Mẹo vặt") | dải màu trên thanh trên + tên trên nút Tạo |
| **Tạo video** | luôn theo **1 kênh**, không có "Tất cả". Gợi ý = lịch mùa + kho ý tưởng của kênh. Chip pillar chọn trước (hoặc "để máy chọn theo tỉ lệ"). Giọng mặc định theo kênh. Nút: **"Tạo video cho Mẹo vặt"** | như cũ, nút dính đáy có tên kênh |
| **Ý tưởng** (trang mới, thay "Gợi ý chủ đề") | Kanban 3 cột Ý tưởng · Đã xếp hàng · Đã làm, nhãn màu pillar; thanh **cân pillar** "4 tuần qua: Giao tiếp 5 · Tiền 1 · …" so với tỉ lệ mục tiêu | danh sách, vuốt để Bỏ/Làm |
| **Hàng đợi / Thư viện** | theo kênh đang chọn; mục "Tất cả kênh" hiện **huy hiệu màu kênh** trên mỗi thẻ. Lọc thêm theo pillar | lưới 2 cột, huy hiệu ở góc thẻ |
| **Thống kê** | `approve_rate` **riêng từng kênh** (2 kênh khác khán giả, gộp lại thì mất nghĩa) + bảng so sánh các kênh ở "Tất cả" + theo pillar | thẻ dọc |
| **Cài đặt → Kênh** (trang mới) | hồ sơ kênh: tên, handle TikTok, màu, logo/avatar, giọng, tone (≤ 500 ký tự), hashtag mặc định, disclaimer, tỉ lệ pillar, lịch gợi ý. Lưu vào `channel.yaml` | 1 cột |
| **Menu** | Tạo · Ý tưởng · Hàng đợi · Thư viện · Thống kê · Cài đặt (6 mục: menu trái OK) | thanh đáy vẫn **4 mục**: Tạo · Ý tưởng · Thư viện · Thêm (Hàng đợi vào "viên tiến độ" ở thanh trên, như research/12) |
| URL | `/k/<kênh>/tao`, `/k/<kênh>/thu-vien`… (link chia sẻ/bookmark giữ đúng kênh; cookie nhớ kênh cuối) | |

Màu kênh: AI giữ sapphire `#7FA6FF` hiện tại. Mẹo dùng **vàng mật ong `#F2B544`** (ấm, "đời sống"), tương phản
tốt trên nền `#0A1020` (A, chưa đo contrast). Nền, chữ và font giữ nguyên → vẫn một sản phẩm, chỉ đổi điểm nhấn.

### 6.3 Dữ liệu

`jobs` thêm cột `channel TEXT NOT NULL DEFAULT 'ai'` qua `_MIGRATE` (`web/db.py:83`). `result.json` thêm `channel`
+ `series_no`. Video cũ tự thành kênh `ai`. `out/<id>/` giữ phẳng, không đổi đường dẫn.

---

## 7. Kế hoạch đề xuất (chưa làm — chờ Tony chọn)

| Bước | Việc | Xong khi | Ước công (A) |
|---|---|---|---|
| **K1** | Tách cấu hình kênh: `configs/channels/ai/` + `--channel`, pillar 1 nguồn | toàn bộ test cũ pass, 3 spec eval AI render giống hệt trước | 0,5 ngày |
| **K2** | Web nhiều kênh: bộ chọn, dải màu, cột `channel`, thống kê theo kênh, trang Kênh | tạo job kênh `meo` từ điện thoại, thẻ thư viện có huy hiệu | 1 ngày |
| **K3** | Nội dung kênh mẹo: rubric.md, pillar, allowlist tầng, claim T4 mới, kho ý tưởng + lịch mùa | 5 kịch bản (1/pillar) qua T4 không lỗi; Tony đọc duyệt | 1 ngày |
| **K4** | Hình: khối `stock` (Pexels) + shot `chat` + probe FLUX ảnh thực phẩm VN | 3 spec eval kênh mẹo render, T1 pass | 1–1,5 ngày |
| **K5** | 5 video demo kênh mẹo → Tony xem | Tony chấm trên web | ~2 giờ máy |

Ngưỡng **viết trước** cho kênh mẹo (đề xuất, ghi vào `configs/thresholds.yaml` khi K3 bắt đầu): `approve_rate` ≥ 0,5
trên 20 video đầu **của riêng kênh** · `fact_error_rate` = 0 · claim `health_claim` không nguồn T1 = 0.

## 8. Tony cần quyết

1. **Tên kênh + handle TikTok.** Tài khoản TikTok thứ 2 phải xác thực bằng SĐT VN (NĐ 147/2024, V). 1 SĐT dùng được
   cho mấy tài khoản thì chưa kiểm.
2. **Giọng:** dùng giọng Tony cho cả hai kênh, hay 1 giọng preset Apache riêng để hai kênh nghe khác nhau?
3. **Bộ pillar khởi đầu:** 5 pillar ở §1 (sức khoẻ để sau) — hay bớt/thêm?
4. **Thứ tự:** K1→K2 trước (web có kênh), hay K3 trước (ra 5 kịch bản mẫu, đọc thử nội dung rồi mới đụng web)?
5. **Affiliate TikTok Shop** có định làm không? Có thì thêm luật Luật QC 75/2025 vào rubric ngay từ đầu.

## 9. Còn hở (chưa research đủ)

- Chưa tìm được kênh mẹo **không lộ mặt** nào ở VN có số follower kiểm chứng được (profile TikTok fetch về rỗng).
- Chưa đọc toàn văn NĐ 174/2026, NĐ 142/2026, Luật QC 75/2025 — chỉ qua báo.
- Chưa tìm được bằng chứng định lượng về retention của format danh sách/series/quiz cho video tự nhiên.
- Ngày các mùa trong lịch (trừ nồm ẩm) là A.
- FLUX.2-klein vẽ thực phẩm VN chưa probe.

## 10. Nguồn chính

nngroup.com/articles/modes · help.metricool.com (account structure) · linear.app/docs/workspaces ·
planable.io/guides/planable-workspaces · planable.io/blog/social-media-content-pillars · help.opus.pro (brand template) ·
support.buffer.com (channel groups, switching organizations) · blog.hootsuite.com/content-planning ·
github.com/OpenTermsArchive/contrib-versions (TikTok Community Guidelines) · newsroom.tiktok.com (AIGC labels) ·
quasa.io (CRP countries 2026) · voh.com.vn (NĐ 142/2026) · vnexpress.net (NĐ 174/2026) · mst.gov.vn (NĐ 147/2024) ·
luatvietnam.vn (Luật QC 75/2025) · buffer.com/resources/how-often-should-you-post-on-tiktok ·
fanpagekarma.com (carousel vs video) · ads.tiktok.com Creative Tips PDF · en.wikipedia.org/wiki/5-Minute_Crafts ·
technologyreview.com 2022-09-23 · futurism.com 2026-03-27 · vov.vn (nồm ẩm) · trends.google.com/trending/rss?geo=VN ·
pypi.org/project/trendspyg · developers.google.com/youtube/v3 · pexels.com/license + /api/documentation ·
pixabay.com/service/license-summary + /api/docs · coverr.co/license · huggingface.co/Wan-AI/Wan2.1-T2V-1.3B ·
huggingface.co/Lightricks/LTX-2 · vfa.gov.vn · viendinhduong.vn · catalog.data.gov (FoodKeeper) ·
vnexpress.net/rss · dantri.com.vn/rss.htm · tuoitre.vn/rss.htm

---

## 11. Đã dựng — 2026-10-04 (Tony: "Dựng kênh 2 đi, research trước khi làm")

Chốt theo mặc định đề xuất (Tony chưa trả lời §8 từng câu, giao dựng luôn): tên **Sống Khéo · Mẹo mỗi ngày**, avatar
mẫu A (`out/kenh-meo/avatar/`), **giọng Tony** cả hai kênh, **5 pillar** §1 (sức khoẻ để sau), làm **K1→K5 liền**,
**chưa affiliate**. TikTok ID chưa có (`songkheo.meo` đã có người dùng).

Research BƯỚC 0: `research/probes/k-research.md`. Đổi so với kế hoạch §5–§7:
- **Khối stock (Pexels) để sau**: Pexels đang **dừng cấp API key mới** (V 2026-10-04); Pixabay cần key Tony đăng ký.
- **Gợi ý chủ đề không chạy theo lịch**: `team/idea_scout.py` tính tại chỗ mỗi lần mở trang (code thuần, không LLM).
- **URL**: cookie `kenh` + `/k/<id>` thay vì tiền tố `/k/<id>/…` (lý do ở k-research §5).
- Thanh đáy điện thoại: Tạo · Ý tưởng · Hàng đợi · Thư viện · Thống kê; Cài đặt lên thanh trên.

Kết quả đo ghi ở `research/probes/k5-demo.md`.
