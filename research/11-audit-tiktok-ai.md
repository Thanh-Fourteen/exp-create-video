# Research + audit: video TikTok về AI — cái gì có bằng chứng, pipeline đang lệch ở đâu — 2026-10-02

**Yêu cầu Tony (2026-10-02):** research sâu về video TikTok AI (hook, kịch bản, giọng, hình, dựng,
phụ đề, màu, nhạc, SFX, retention), rồi audit pipeline repo này và thiết kế lại.

**Cách làm:** 4 paper-scout song song (tài liệu chính thức TikTok · nghiên cứu học thuật · dữ liệu ngành
+ creator · thị trường VN + tool local), ~260 lượt search/fetch, link fetch ngày 2026-10-02 trừ chỗ ghi.
Audit dựa trên code + `out/demo-03-argon-sol` (bản tốt nhất hiện tại, `out/DEMO-03.mp4`) + `state.json`.

**Nhãn bằng chứng** (bắt buộc đọc trước khi tin bất kỳ dòng nào):

| Nhãn | Nghĩa |
|---|---|
| **FACT** | TikTok/nền tảng/luật tự công bố, đã đọc trang gốc |
| **DATA** | số đo từ dataset/nghiên cứu (ghi cỡ mẫu + caveat) |
| **OBS** | creator/coach tự nói, không có dataset công khai |
| **HYP** | suy luận của tôi |
| **REC** | khuyến nghị (luôn kèm WHY → HOW → KPI) |

⚠ **Giới hạn lớn nhất của báo cáo này:** trang TikTok (profile, video, Creator Academy, FYF standards)
render bằng JS → **không fetch được view count của video TikTok nào**. Phần 3 (phân tích video thực tế)
vì vậy dựa trên dataset học thuật + quan sát coach, **không** phải tập mẫu video tôi tự xem. Mục 3.3
đưa quy trình để Tony làm tập mẫu đó bằng tay trong ~1 giờ — đây là việc tôi không làm hộ được.

---

## 1. Executive summary — 10 điều quan trọng nhất

1. **Chưa đăng video nào → mọi tối ưu từ đầu tới giờ là tối ưu proxy.** `approve_rate` = 0/0, retention
   thật = chưa có. demo-03 qua T3 **10/10** mà Tony vẫn thấy "chưa hấp dẫn" — bằng chứng trực tiếp rằng
   T3 không đo sức hút. Đúng với tài liệu: LLM chấm "hay" tương quan ~0 với chuyên gia (`research/10` §5).
   → **Việc có impact lớn nhất không nằm trong pipeline: đăng 10 video để có dữ liệu retention thật.**
2. **Thứ bị rời bỏ là giây 0–5, không phải giây 30.** DATA: phần lớn lượt skip xảy ra trong 5s đầu
   [Lee et al., AAAI 2025]; ~70% phiên xem kết thúc trước 20% thời lượng [Yen et al., arXiv 2603.22663,
   lab, n=50]. FACT: TikTok nói xem hết video dài được "trọng số lớn hơn" [newsroom, 2020-06].
   → Ngân sách công sức nên dồn vào **frame 0 + 5 giây đầu**, nơi pipeline hiện đầu tư ít nhất về hình.
3. **Giọng là biến mạnh nhất có bằng chứng, và nó đang là điểm yếu.** DATA: giọng nói gốc là predictor
   mạnh nhất trong 9.654 video brand TikTok [Paekivi & Karjus, 2606.16053]; giọng robot bị lướt ngay
   [PaperTok, 2601.18218]; giọng AI "generic" chỉ được nhận là người ~40% so với 58–70% của giọng
   clone và 62–81% giọng thật [Lavan et al., PLOS ONE 2025-09, n=50/thí nghiệm].
   → **REC #1: clone giọng chính Tony** (VieNeu v3 Turbo clone 3–8s, Apache, Tony có quyền với giọng
   mình) — vừa thật hơn preset, vừa là thương hiệu không chép được, vừa hợp luật.
4. **Hình đang có rủi ro "AI slop" cao nhất ở chỗ đầu video.** Frame 0 của demo-03 là mặt người AI
   "ngạc nhiên" chung chung + 4 dòng chữ; trong 40s có ~5 ảnh mặt người giả + 2 lần tủ server. FACT:
   TikTok cho người xem **tự giảm lượng AIGC** trong feed (Manage Topics, 2025-11) và đã gắn nhãn >3 tỉ
   nội dung AI [C2PA, 2026-07]. Mặt người AI biểu cảm là thứ dễ bị nhận ra nhất.
   → **REC #2: thay b-roll AI bằng "bằng chứng thật"**: quay màn hình trang/tool thật (Playwright đã có
   sẵn trong repo, quay được video), log terminal thật trên 2060, thẻ số liệu. Ảnh AI chỉ là phương án cuối.
5. **"Nhanh hơn" không có bằng chứng; "vừa phải" thì có.** DATA: engagement theo cường độ kích thích là
   **chữ U ngược** [Xue et al. 2604.19995, 14.492 video]; độ phức tạp hình tương quan **âm** với like
   [Wang & Li, PLOS ONE 2024, 2.553 video Douyin]. Không tìm được nguồn gốc nào cho "đổi cảnh mỗi
   1,5–3s" hay "+40% retention nhờ pattern interrupt" — toàn blog vendor.
   → Giữ nhịp hiện tại (shot 2,5–5s). **Đừng** làm nhanh thêm; Tony đã nghe ra cái giá ở 08-14.
6. **Độ dài: bằng chứng mâu thuẫn thật — phải tự đo.** Thí nghiệm: tối ưu ~35s (có nhạc ~44s)
   [Reichstein & Dost 2025, n=155]. Dataset 111K video TikTok 2026: ER cao nhất <30s nhưng **view TB
   tăng tới 120–180s** [Socialinsider 2026-H1]. TikTok Ads: 21–34s [2022]. → A/B hai nhánh 30s vs 60–75s.
7. **Thuật toán không có "hack".** FACT: follower count không phải yếu tố trực tiếp; TikTok tránh xếp
   2 video cùng creator/cùng sound liên tiếp [newsroom 2020-06, 2023-03]. DATA: đăng nhiều nâng **trần**
   (top post) chứ không nâng **sàn** — median ~500 view ở mọi tần suất [Buffer, 11,4M post, 2025-10].
   Giờ đăng: Buffer tự nói "không có giờ thần kỳ". → Số lượng video + biến thiên mới là đòn bẩy.
8. **Chủ đề có thể lệch khán giả.** Trend scout lấy từ HN/HF/arXiv = mạch của dev. DATA: ~87% người
   dùng online VN dùng tool AI, dẫn đầu ChatGPT/Gemini [Decision Lab Q3-2025]; lợi thế của Shorts
   **co lại ở chủ đề giáo dục** [Violot et al., WebSci'24, 16M video]. HYP: "model mới ra / giá token"
   là ngách hẹp trên TikTok VN; "dùng AI miễn phí làm X ngay hôm nay" rộng hơn nhiều. → Test bằng pillar.
9. **Pipeline chậm ở chỗ không cần chậm.** demo-03: **TTS 723s** (ONNX CPU) + **render 581s** + mỗi vòng
   QC patch ~330–380s. VieNeu v3 Turbo GPU đỉnh 1,1GB [repo card] → chuyển TTS lên GPU (tuần tự với
   các khối GPU khác) là rẻ nhất.
10. **Luật VN 2026 đã có hiệu lực**: Luật AI 134/2025/QH15 (từ 2026-03-01) + Nghị định 142/2026 (từ
    2026-05-01) **bắt buộc gắn nhãn** khi mô phỏng hình/giọng người thật hoặc tái hiện sự kiện thật
    [LuatVietnam, verified bản tóm tắt]. Clone giọng Tony + gắn nhãn AI của TikTok cho mọi video = an toàn.

---

## 2. Research findings

### 2.1 TikTok phân phối video thế nào — chỉ FACT

| Điều TikTok tự nói | Nguồn |
|---|---|
| Tín hiệu: tương tác (like, share, follow, comment, video bạn tạo), thông tin video (caption, sound, hashtag), thiết bị/tài khoản (ngôn ngữ, quốc gia — trọng số thấp) | newsroom "How TikTok recommends videos #ForYou" [2020-06] |
| "Xem hết một video dài hơn từ đầu tới cuối" được **trọng số lớn hơn** | như trên |
| **Follower count và việc từng có video hot KHÔNG phải yếu tố trực tiếp** | như trên |
| Không xếp 2 video cùng creator hoặc cùng sound liền nhau; >15 cập nhật chống lặp | newsroom refresh FYF [2023-03] |
| "Why this video": tương tác, tài khoản theo dõi, nội dung mới đăng trong khu vực, nội dung phổ biến trong khu vực | newsroom [2022-12] |
| Người xem có **thanh trượt lượng AIGC** trong Manage Topics (đang "testing") | newsroom [2025-11-19] |
| Creator Rewards: video > 1 phút, "qualified view" = xem ≥ 5s; 4 tiêu chí: originality, play duration, **search value**, engagement | newsroom [2024-03]; điều khoản CRP EEA |
| Bắt buộc gắn nhãn AIGC "trông như thật"; tự gắn qua C2PA; >1,3 tỉ video (2025-11) → >3 tỉ (2026-07) | newsroom 2023-09, 2024-05, 2025-11; c2pa.org 2026-07 |
| Search: "hàng tỉ" lượt/ngày, +40% YoY; 1/4 user (US) search trong 30s đầu mở app | newsroom [2026-03] |
| API: unaudited → SELF_ONLY; draft inbox tối đa 5 bài chờ/24h; 6 req/phút | developers.tiktok.com |
| Business account **không được** dùng thư viện nhạc chung cho mục đích thương mại, kể cả bài organic | ads.tiktok.com CML [2025-07] |

**Không verify được** (trang render JS): định nghĩa chính xác các metric trong TikTok Studio (avg watch
time, % xem hết, retention curve), câu chữ chính xác của "FYF eligibility standards" (snippet: nội dung
unoriginal, "ghép từ nhiều nguồn mà không thêm thông tin", ảnh tĩnh/clip quá ngắn → không lên FYF).

### 2.2 TikTok Ads data — DATA nhưng **cho quảng cáo**, dùng cho organic chỉ là HYP

| Số | Nguồn |
|---|---|
| >63% video CTR cao nhất đưa thông điệp chính trong 3s đầu | ads blog [2020-10] |
| 90% tác động ghi nhớ quảng cáo nằm trong 6s đầu; 2s đầu giá trị nhất cho recall | ads blog; Power Creative Elements [2022-11] |
| 93% video top dùng audio; 88% user nói âm thanh là thiết yếu (Nielsen 2020) | Creative Accelerator; ads blog [2021-12] |
| Voiceover +12% conversion; text overlay có ở 86% ads, +64% conversion; caption +58% recall | Creative Accelerator; PCE [2022-11] |
| Chữ 5–10 từ/giây → +2,1× awareness lift | PCE [2022-11]; Ads Help [2025-06] |
| 1/4 video top dài 21–34s (+1,6× impression); nhạc > 120 BPM → VTR cao hơn | ads blog [2022-03, 2020-10] |
| 1/3 ad VTR cao "phá bức tường thứ tư" (nói thẳng vào camera) | ads blog [2020-10] |

Mâu thuẫn: "hook trong 6s" (Ads Help 2025) vs "3s" (blog 2020) vs "2s" (recall 2022) — **khác metric**
(CTR / recall / VTR), khác năm. Không gộp.

### 2.3 Nghiên cứu học thuật — DATA

| Chủ đề | Phát hiện | Nguồn, cỡ mẫu | Caveat |
|---|---|---|---|
| Rời bỏ sớm | "phần lớn skip trong 5s đầu" | Lee et al. AAAI 2025, KuaiRand + MVA | đọc từ histogram |
| | ~70% phiên kết thúc trước 20% thời lượng; video giáo dục retention trung vị thấp hơn giải trí | Yen et al. 2603.22663 [2026-03] | lab, n=50, YouTube Shorts |
| | watch time thô bị độ dài video gây nhiễu → không so watch time giữa video dài/ngắn | D2Q, KDD 2022 | Kuaishou |
| Nhịp / kích thích | cảm giác tăng tuyến tính, **hành vi engagement chữ U ngược** | Xue et al. 2604.19995, 14.492 video | tương quan |
| | thời lượng mặt người, tần suất cắt, độ sáng = top-3 đặc trưng | như trên | |
| | độ sáng (+), loudness (+), **độ phức tạp hình (−)** với like | Wang & Li PLOS ONE 2024, 2.553 video Douyin | 1 ngành (ô tô) |
| | phim Hollywood: nhịp không tương quan rating (r=−0,089 n.s.) | Cutting et al. 2010, 150 phim | phim dài |
| Hook | độ cụ thể của tiêu đề là **chữ U ngược**: đối thủ mơ hồ thì cụ thể thắng; đã cụ thể thì cụ thể hơn lại thua | Le Quéré & Matias, Sci. Rep. 2025, ~9.000 A/B test | tiêu đề tin, CTR |
| | 4.983 hook TikTok: **từ vựng không tương quan** với view; sentiment có | MMI 2025 | tạp chí hạng thấp |
| | tò mò kích hoạt vùng thưởng; tò mò cao → nhớ câu trả lời lâu hơn | Kang et al. Psych Sci 2009 | lab, trivia |
| Viral | cảm xúc kích thích cao (kinh ngạc, giận, lo) + hữu ích + bất ngờ → chia sẻ nhiều hơn; buồn → ít | Berger & Milkman JMR 2012, 6.956 bài NYT | text, email |
| | follower là predictor mạnh nhất; tiếp theo: cận cảnh/trung cảnh, chữ trên hình, POV | Ling et al. 2111.02452 | n=400 |
| | 10K video brand: "phần lớn biến KHÔNG liên quan tới thành công"; giọng gốc mạnh nhất; trending sound β âm | Paekivi & Karjus 2606.16053 | brand, Estonia, R²=0,27 |
| Độ dài | chữ U ngược, tối ưu **34,7s** (có nhạc 44,1s; quảng cáo 19,8s) | Reichstein & Dost 2025 | ý định, n=155, 2 video |
| | Shorts hơn video thường về view, nhưng **lợi thế co lại ở giáo dục, chính trị** | Violot et al. WebSci'24, 16M video | YouTube |
| Giọng | nói nhanh hơn → đáng tin + thuyết phục hơn | Miller et al. 1976, N=449 | tiếng Anh, người thật |
| | nhanh có thể giúp hoặc hại, tuỳ mức người nghe xử lý | Smith & Shaffer 1991 | |
| | giọng AI generic: 39–41% bị nhầm là người; clone: 58–70%; thật: 62–81% | Lavan et al. PLOS ONE 2025-09 | UK, n=50 |
| | prosody (pitch + năng lượng) phân biệt diễn giả TED với giáo sư | Tsai, Interspeech 2015 | không nối với view |
| | tiếng Việt đọc ~**5,2 âm tiết/giây** | Coupé et al. Sci. Adv. 2019 | reported, đọc to |
| Nhạc | **giọng trên nhạc ≥ 10 LU**; trên ambience ≥ 15 LU; người thường thích hơn chuyên gia ~4 LU | Torcoli et al. JAES 2019; Resti 2023 (IQR 5,7 LU) | n=22, TV |
| Phụ đề | phụ đề cùng ngôn ngữ tăng hiểu, chú ý, nhớ | Gernsbacher 2015, >100 nghiên cứu | không đo engagement; **karaoke: 0 nghiên cứu** |
| Nhãn AI | nhãn AIGC: **+** trực tiếp với ý định xem tiếp (tò mò), **−** gián tiếp qua giảm tin cậy; người hiểu AI càng nhiều thì âm càng mạnh | Xiao et al. Behav. Sci. 2026-07, N=720 | ý định, TQ |
| | nhãn AI làm giảm độ chính xác cảm nhận + hứng thú (tin text) | Wang et al. 2506.16202, N=3.861 | text |
| Màu | gần như **không có** bằng chứng màu → performance; chỉ "độ sáng +" | Wang & Li 2024; Xue 2026 | yếu |

### 2.4 Dữ liệu ngành — DATA vendor (có phương pháp nhưng không peer-review)

| Phát hiện | Nguồn |
|---|---|
| ER TikTok 3,70% (2025) → **2,60%** (2026), tính theo view; TK < 5K follower: TB **350 view/video** (Shorts: 15.160) | Socialinsider, 69M video [2026-07] |
| ER theo độ dài: <30s 6,0% · 30–60s ~4,2–4,3% (thấp nhất) · >180s 5,8%. **View TB tăng theo độ dài**: 1.200 (<30s) → 12.000 (120–180s) | Socialinsider, 111K video [2026-H1] — confound: TK lớn đăng video dài |
| Tần suất 2–5/tuần +17% view/post, 11+/tuần +34%; **median không đổi (~500)** | Buffer, 11,4M post [2025-10] |
| Shorts: VVSA (viewed vs swiped) < 60% hiếm khi chạy, tốt nhất 70–90%; **like/share/comment không tương quan mạnh** với view | Paddy Galloway, 5.400 Shorts [2023-04] |
| ER Tech & Software giảm ở mọi kênh | Rival IQ [2025] |

**Đáng chú ý cho dự án:** dải 15–60s của `thresholds.yaml` nằm đúng vùng ER thấp nhất của Socialinsider.
Không đủ để đổi (tương quan, confound), nhưng đủ để **đưa độ dài vào thí nghiệm** thay vì cố định.

### 2.5 Quan sát creator/coach — OBS (không có dataset)

- **Kallaway** (46M view video Ironman): thứ tự quan trọng trong hook = **chữ tiêu đề > hình > lời**, vì
  đọc/nhìn nhanh hơn nghe; 3 lớp phải **cùng chỉ một ý** ("hook alignment"). Hook 3 bước: context lean
  (nói rõ chủ đề) → scroll-stop interjection ("nhưng…") → contrarian snapback (bẻ ngược).
- **Jenny Hoyos** (~10M view TB/Short): nhắm ~34s; Hook → Foreshadow → Narrative → Ending có twist; viết
  trình độ lớp 5; **kết ở đỉnh, không chào**, câu kết nối lại câu mở → loop.
- **Rowan Cheung** (The Rundown): avatar AI + giọng clone của chính anh → 160K follower IG/~1 năm; "người
  xem không quan tâm là AI" — nhưng nội dung là bài viết **của chính anh** (con người thật đứng sau).
- **Thương hiệu AI-news lớn bên IG/X không chắc bám được TikTok**: @chatgptricks 2,7M IG nhưng ~557 trên
  TikTok; @evolving.ai ~2,6K TikTok (reported, snippet). HYP: TikTok thưởng format/cá nhân, không thưởng
  thương hiệu chuyển kênh.
- YouTube (2025-07, FACT): nội dung "thay cho nhau được từ video này sang video khác", "AI dùng template
  chung chung" → không được kiếm tiền. Đây là định nghĩa slop chính thức gần nhất hiện có.
- Creator AI tiếng Việt: **không verify được kênh nào** (TikTok không render). Creator VN được TikTok vinh
  danh Q2-2026 (Simon Review, Anh Chân Gỗ…) đều là người thật kể chuyện — không ai là kênh AI.

### 2.6 Khán giả Việt Nam

| | Nguồn |
|---|---|
| TikTok ad reach **76,1M** người 18+ (88,8% người dùng internet); 53/47 nam/nữ | DataReportal 2026 [2025-11] |
| TikTok ~58 phút/ngày (YouTube dài 70, OTT 120) | Appota qua VietNamNet [2025] |
| ~87% người dùng online dùng tool AI — ChatGPT, Gemini, Meta AI dẫn | Decision Lab Q3-2025 |
| TikTok dùng 77% (Facebook 94%, YouTube 87%); Gen Y "mỏi nội dung" giảm dùng TikTok | Decision Lab Q2/Q4-2025 (Q4 reported) |
| Giọng Nam hợp quảng cáo/giải trí, Bắc hợp tin tức/giáo dục | **chỉ ý kiến vendor** (vnvoice), không có nghiên cứu |
| Luật AI 134/2025 (2026-03-01) + NĐ 142/2026 Điều 18 (2026-05-01): bắt buộc nhãn khi mô phỏng hình/giọng **người thật** hoặc tái hiện **sự kiện thật**; nhãn đặt trên nội dung/caption/UI/âm thanh | Tilleke & Gibbins; LuatVietnam |
| NĐ 147/2024: chỉ TK xác thực SĐT VN mới được đăng/bình luận | chinhphu.vn |

### 2.7 Myths và lời khuyên không có bằng chứng

| Lời khuyên phổ biến | Đánh giá |
|---|---|
| "Video càng nhanh càng viral", "đổi cảnh mỗi 1,5–3s" | **Không có bằng chứng**; bằng chứng tốt nhất nói chữ U ngược |
| "Phụ đề kiểu Hormozi +50–80% completion" | Trang vendor bán tool caption; 0 nghiên cứu cho karaoke |
| "#fyp/#viral giúp lên xu hướng" | Không có bằng chứng; TikTok nói hashtag là một tín hiệu nội dung, không nói trọng số |
| "Giờ vàng đăng bài" | Buffer (7,1M post) tự nói không có giờ thần kỳ; không có dataset VN |
| "Đăng nhiều bị phạt", "xoá video hại tài khoản", "shadowban giờ đầu" | Không tìm được dữ liệu; Buffer: đăng nhiều không làm giảm median |
| "Trending sound luôn giúp" | Brand: β **âm** [Paekivi 2026]; organic không có số nhân quả; API không gắn được sound app |
| "Cần follower mới lên" | FACT: follower không phải yếu tố trực tiếp (nhưng DATA: tương quan mạnh với view — vì TK lớn làm tốt hơn) |
| "Like là tín hiệu quan trọng" | Paddy: like/comment/share tương quan yếu với view trên Shorts; TikTok không công bố trọng số |
| "Completion ≥ 70% mới được đẩy" (`research/07`) | **reported, không truy được nguồn gốc** — giữ làm mục tiêu nội bộ, đừng gọi là luật |
| "Màu X tăng tương tác" | Không có bằng chứng ngoài "sáng hơn tương quan dương" |

**Có công thức viral cố định không?** Không. Mô hình tốt nhất trên 10K video giải thích R²=0,27 và hầu
hết biến không liên quan [Paekivi 2026]; view TikTok đuôi rất dày [Guinaudeau 2022, `research/10`].
**Kiểm soát được:** chủ đề, 5s đầu, giọng, hình, độ dài, CTA, số lượng + độ đa dạng video, tính nguyên
bản. **Không kiểm soát được:** seed audience ban đầu, cạnh tranh cùng lúc, độ "hot" của topic, thay đổi
thuật toán, thanh trượt AIGC của người xem.

---

## 3. Viral / retention framework

### 3.1 Mô hình 4 cửa (HYP, dựng từ FACT + DATA ở trên)

| Cửa | Thời điểm | Người xem đang hỏi | Lý do bỏ đi | Đòn bẩy có bằng chứng |
|---|---|---|---|---|
| **1. Dừng lướt** | 0–1s | "Cái này có cho mình không?" | frame 0 chung chung, chữ quá dài để đọc, không có chủ đề rõ | chữ tiêu đề ngắn > hình > lời (OBS Kallaway); mặt người/cận cảnh (DATA Ling, Xue); độ sáng (DATA) |
| **2. Cam kết** | 1–5s | "Có đáng 40s không?" | lời chào/bối cảnh, giọng máy, lời hứa mơ hồ | đưa giá trị trong 3s (Ads DATA); giọng tự nhiên (DATA Paekivi, Lavan); khoảng tò mò **cụ thể** (DATA Le Quéré) |
| **3. Giữ** | 5s–80% | "Còn gì mới không?" | ý dậm chân, liệt kê, hình lặp, kích thích quá mức | mỗi beat một thông tin mới; chỗ ngoặt giữa video; nhịp vừa phải (DATA Xue U ngược) |
| **4. Kết + vòng** | 20% cuối | "Xong rồi" | trả lời câu hỏi quá sớm, chào tạm biệt, CTA chung chung | payoff ở ~2/3 rồi một twist; kết nối lại hook (OBS Hoyos); xin lưu/chia sẻ cụ thể |

**Metric từng cửa** (đo từ TikTok Studio, Tony export tay): cửa 1–2 = **% còn lại ở giây 2 và 5**
(đường retention); cửa 3 = avg watch time / thời lượng; cửa 4 = % xem hết + tỉ lệ replay (nếu Studio
có). Share/save = chất lượng giá trị. **So log(view+1) ở t+72h**, không so trung bình thô.

### 3.2 Các yếu tố theo mức bằng chứng

| Có bằng chứng (DATA/FACT) | Quy ước nghề (OBS) | Chưa có gì |
|---|---|---|
| giây đầu là nơi rời bỏ nhiều nhất · xem hết video dài được thưởng · giọng tự nhiên · nhịp vừa phải (U ngược) · hình đơn giản · độ sáng · loudness · cảm xúc kích thích cao + hữu ích · có audio · giọng ≥ 10 LU trên nhạc | chữ > hình > lời ở hook · hook alignment · loop · Hook→Foreshadow→Narrative→Twist · ~34s · viết dễ hiểu · CTA comment-keyword | karaoke caption · SFX · BPM cho organic · màu · giọng nam/nữ · giờ đăng VN · hashtag count |

### 3.3 Phân tích video thực tế — quy trình cho Tony (vì tôi không fetch được TikTok)

Đây là việc **không làm hộ được** và có giá trị hơn mọi blog: ~1 giờ, làm một lần.

1. Trên app, search 8 từ khoá: `chatgpt mẹo`, `AI miễn phí`, `gemini`, `công cụ AI`, `tin AI`,
   `AI làm video`, `prompt`, `AI học tập` — mỗi từ lấy 4 video (2 nhiều view, **2 ít view** cùng kênh
   — để thấy cái gì khác nhau trong cùng một creator).
2. Điền bảng `eval/tiktok-mau/2026-10.csv`: link · view · ngày · độ dài · loại hook (bảng 4.2) · có mặt
   người thật? · giọng thật/AI · loại hình chính · có nhạc? · CTA · giây mình muốn lướt.
3. Tôi gom lại thành bảng pattern theo 8 nhóm (news, tools, tutorial, hacks, workflow, storytelling,
   entertainment, business). **Không** xếp hạng bằng view tuyệt đối — so trong cùng kênh.

### 3.4 Pattern theo nhóm — HYP từ OBS + DATA, **chưa có tập mẫu**, cần 3.3 để xác nhận

| Nhóm | Hook điển hình | Dài | Hình chính | Cơ chế giữ chân (HYP) | Share/save |
|---|---|---|---|---|---|
| AI news | "X vừa ra, và nó làm được Y" / con số sốc | 20–40s | logo/trang công bố, demo chính hãng, mặt creator | mới + bất ngờ (Berger: surprise) | share > save |
| AI tools | "Tool miễn phí này thay được Z" | 30–60s | **quay màn hình thật** | demonstration-first, kết quả trước | **save cao** |
| Tutorial | "Làm X trong 3 bước" | 45–90s | màn hình + zoom vào nút | lời hứa rõ, tiến độ thấy được | **save cao nhất** |
| Hacks | "99% người dùng ChatGPT không biết…" | 15–30s | màn hình | khoảng tò mò hẹp, payoff nhanh | save + share |
| Workflow | "Tôi để AI làm X, kết quả:" | 45–90s | before/after, timelapse | kết quả trước, cách làm sau | save |
| Storytelling | in medias res, nhân vật | 45–90s | hình sinh / B-roll | open loop + twist (Hoyos) | share |
| Entertainment | phản ứng/meme với AI | 10–30s | mặt người phản ứng | cảm xúc cao, loop | share |
| Business | "Công ty X tiết kiệm Y nhờ AI" | 30–60s | số liệu, talking head | hữu ích + con số | share (LinkedIn-ish) |

**Pattern chung** (HYP): (1) bằng chứng nhìn thấy được trong 3s đầu; (2) **một** lời hứa cụ thể;
(3) người thật (mặt hoặc giọng) đứng sau; (4) kết ở đỉnh thông tin. Kênh này hiện mạnh ở (2), yếu ở
(1) và (3).

---

## 4. AI TikTok Video Formula

### 4.1 Công thức sản xuất (REC — heuristic, không đảm bảo viral)

```
[0.0s]  FRAME 0: hình BẰNG CHỨNG cụ thể của chủ đề (trang/tool/số liệu thật), sáng, 1 chủ thể
        + chữ tiêu đề ≤ 7 từ (KHÁC lời đọc, cùng ý), đốt sẵn vào frame (draft API không nhận cover)
[0–3s]  Lời hook: kết quả/con số/mâu thuẫn — giọng THẬT (clone Tony), không chào
[3–6s]  Lời hứa + mở vòng: "…nhưng có một điều không ai nói" — hình đổi lần 1
[6s–⅔]  2–4 beat, mỗi beat = 1 sự thật mới + 1 hình chứng minh nó; 1 chỗ ngoặt ở giữa
[⅔]     Payoff: trả lời vòng tò mò
[cuối]  Twist/hệ quả cho người xem + CTA lưu/chia sẻ cụ thể, câu cuối nối lại hook → loop
        KHÔNG chào tạm biệt, KHÔNG màn hình đen/logo kết
Âm thanh: giọng −14 LUFS · nhạc ≥ 10–15 LU dưới giọng · SFX ≤ 1 cái / 5s, chỉ ở chỗ có nghĩa
Hình: ≥ 50% thời lượng là bằng chứng thật (màn hình/thẻ số/log) · ảnh AI ≤ 25% · mặt người AI 0–1
```

### 4.2 Hook frameworks (20) — viết cho ngách AI tiếng Việt

Cột "loại" để tag trong `script.json` → sau 20 video biết loại nào thắng.

| # | Loại | Khuôn | Ví dụ |
|---|---|---|---|
| 1 | Con số sốc | [số] + [hệ quả bất ngờ] | "Sáu GB VRAM. Đủ chạy model vẽ ảnh đẹp hơn Midjourney bản cũ." |
| 2 | Mâu thuẫn niềm tin | "Ai cũng nghĩ X. Sai." | "Ai cũng nghĩ AI chạy local cần card khủng. Tôi chạy trên 2060." |
| 3 | Kết quả trước | "Đây là [kết quả]. Làm bằng [cái không ngờ]." | "Video này không ai quay, không ai đọc. Giải thích ngay." |
| 4 | Demonstration-first | (hình demo chạy ngay frame 0) + "Xem nó làm gì." | quay màn hình tool đang chạy |
| 5 | Before → after | "Trái: [trước]. Phải: [sau]. Khác nhau đúng một câu prompt." | so sánh 2 ảnh |
| 6 | Câu hỏi có số | "Vì sao model [X] rẻ hơn năm lần mà điểm gần bằng?" | |
| 7 | Cảnh báo / mất mát | "Nếu bạn đang trả tiền cho [X], dừng lại." | |
| 8 | Bí mật trong tầm tay | "Gemini có một nút miễn phí mà 9/10 người không bấm." | (chỉ khi số có nguồn) |
| 9 | Bóc tin đồn | "Tin [X] đang lan. Tôi kiểm rồi — sai một nửa." | |
| 10 | Thử thách tự đo | "Tôi cho hai model cùng làm một việc. Kết quả lệch xa." | |
| 11 | Ngôi thứ nhất thất bại | "Tôi làm hỏng [X] ba lần trước khi hiểu điều này." | log OOM thật |
| 12 | So sánh giá | "Cùng một việc: [A] tốn 10 USD, [B] tốn 0 đồng." | |
| 13 | In medias res | "…và đó là lúc con AI tự sửa lỗi của chính nó." | |
| 14 | Danh sách có hứa hẹn | "Ba tool AI miễn phí thay được cả bộ Office." (lưu lại) | save-bait có giá trị thật |
| 15 | "Bạn đang làm sai" | "Bạn đang viết prompt kiểu hỏi Google. Đây là lý do nó trả lời dở." | |
| 16 | Thời gian | "Năm phút trước nó chưa tồn tại. Giờ nó đứng top Hugging Face." | |
| 17 | Phá bức tường thứ 4 | "Đừng lướt — câu thứ ba sẽ tiết kiệm cho bạn một tháng tiền ChatGPT." | DATA ads: 1/3 ad VTR cao |
| 18 | Người nổi tiếng/hãng đối đầu | "Google vừa đáp trả OpenAI — bằng một con số." | |
| 19 | Context lean + snapback (Kallaway) | "[Chủ đề rõ]. Nhưng [bẻ ngược]." | "Model mới của Google mạnh nhất. Nhưng bạn không dùng được." |
| 20 | Hệ quả cho người Việt | "Từ hôm nay, sinh viên Việt Nam dùng [X] miễn phí." | vn_fit |

Luật chung (DATA Le Quéré): hook phải **cụ thể hơn** đối thủ trong feed, nhưng đừng cụ thể tới mức
không còn gì để tò mò — nói **cái gì** xảy ra, giữ lại **vì sao/thế nào**.

### 4.3 Template kịch bản theo độ dài

Âm tiết/giây: lời đọc TTS hiện ~4,1 từ (âm tiết)/s (đo `giong-moi`), dưới mức đọc tự nhiên 5,2
[Coupé 2019] — hợp với ưu tiên "tự nhiên" của Tony.

| Dài | Âm tiết | Cấu trúc |
|---|---|---|
| **15s** | ~60 | Hook(kết quả) 3s → 1 bằng chứng 8s → twist + CTA 4s. Một ý duy nhất. Hợp: hacks, tin nóng |
| **30s** | ~125 | Hook 3s → hứa/mở vòng 4s → 2 beat × 7s → payoff 5s → CTA-loop 4s |
| **45s** | ~185 | Hook 3s → mở vòng 4s → beat 1–2 (14s) → **ngoặt** 5s → beat 3 (7s) → payoff 6s → CTA 5s |
| **60s** | ~250 | như 45s + 1 beat demo; payoff ở ~40s; twist 50s; CTA. Đủ điều kiện CRP nếu > 60s |
| **90s** | ~370 | Tutorial/workflow: hook kết quả → "3 bước" (đánh số trên màn hình — tiến độ thấy được) → mỗi bước 20s với màn hình thật → kết quả cuối → CTA lưu. Chỉ cho nội dung có hành động làm theo |

Chống "exposition dump": mỗi câu phải trả lời được "người xem biết thêm gì?". Không có → xoá (đã có
luật này trong prompt; giữ).

### 4.4 Giọng — REC

| Thông số | Đích | Cơ sở |
|---|---|---|
| Nguồn giọng | **clone Tony** > preset VieNeu tốt nhất > preset | DATA Lavan (clone ≈ thật hơn generic), Paekivi (giọng gốc) |
| Tốc độ | 4,0–4,8 âm tiết/s; hook có thể nhanh hơn 10% | DATA Miller (nhanh → tin hơn) vs Tony 08-14 (tự nhiên) — đo cả hai |
| Prosody | F0 std ≥ 3 bán cung (đo sẵn được bằng librosa) | DATA Tsai (TED); proxy, không thay tai Tony |
| Ngắt | nghỉ theo dấu câu, ghép cả đoạn (P3b.S2) | Tony 08-14 |
| Nam/nữ, Bắc/Nam | **không có bằng chứng** → giữ Bắc nam (nhất quán thương hiệu); nếu muốn, test | — |

### 4.5 Hình — khi nào dùng loại nào

| Loại | Dùng khi | Không dùng khi | Pipeline có? |
|---|---|---|---|
| Quay màn hình tool/trang thật | **mặc định** cho tool/tutorial/news | trang chữ nhỏ không zoom được | chỉ ảnh chụp tĩnh — **thiếu video** |
| Thẻ số/biểu đồ | câu có số | câu không có số | ✅ (mạnh) |
| Log/terminal thật trên 2060 | ngôi thứ nhất "tôi đo" | — | ❌ |
| Ảnh AI 1 chủ thể | ý trừu tượng không có bằng chứng | thay cho bằng chứng; mặt người giả biểu cảm | ✅ (đang lạm dụng) |
| Mặt người | giữ chân (DATA) | mặt **AI** → rủi ro slop + nhãn | ❌ người thật |
| Talking head / avatar | khi Tony muốn lộ mặt | — | ❌ (ngoài phạm vi 0đ tự động) |
| Video AI (Wan/LTX) | — | 2060 OOM/quá chậm (P1.S4 FAIL) | ❌ đúng |
| Meme/reaction | entertainment | news nghiêm túc; bản quyền | ❌ |

### 4.6 Dựng, phụ đề, màu, âm thanh — thông số

| Mục | Đích | Mức bằng chứng |
|---|---|---|
| Shot | 2,5–5s (giữ); không dưới 2s | DATA U ngược |
| Zoom/punch-in | chỉ ở từ nhấn, ≤ 1/1,2s (giữ) | OBS |
| Phụ đề | cụm 1–3 từ, Anton, giữa-dưới, highlight 1 màu (giữ) | DATA hiểu (Gernsbacher); karaoke OBS |
| Chữ trên màn hình | ≤ 5–10 từ/giây; hook ≤ 7 từ | DATA ads |
| Safe zone | giữ % hiện tại (trên 8 · dưới 20 · phải 18) — pixel bên thứ ba khác nhau, TikTok không công bố | reported |
| Màu | nền tối + 1 accent nhất quán (giữ `#4DE1C1`) là **quy ước thương hiệu**, không phải bằng chứng; **độ sáng** chủ thể mới là thứ có DATA | DATA (sáng) / OBS (palette) |
| Nhạc | giọng trên nhạc 12–18 LU (đang 15 — giữ); BPM không quan trọng cho organic | DATA Torcoli ≥ 10 |
| SFX | ≤ 1/5s, chỉ khi có sự kiện hình (thẻ số hiện, chuyển ý lớn); im lặng 0,3–0,5s trước payoff | không có DATA — đi nhẹ là an toàn |
| Kết | không chào, khung cuối = thẻ số chính hoặc hình hook → loop | OBS Hoyos |

---

## 5. Audit pipeline hiện tại

Chấm theo demo-03 + code (2026-10-02). Thang 1–10 **là đánh giá của tôi (HYP)**, không phải số đo.
Q=Quality · R=Retention potential · S=Scalability · A=Automation · C=Cost · P=Production speed · T=TikTok optimization.

| # | Stage | Hiện trạng | Q | R | S | A | C | P | T |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Research topic / trend | `team/trend_scout.py`: HF, HN, arXiv, RSS, GenK/VnExpress, Google Trends VN | 7 | 5 | 8 | 8 | 10 | 9 | 4 |
| 2 | Idea / series | chưa có (P5.S2 showrunner) | – | – | – | – | – | – | – |
| 3 | Script | `scriptwriter.py`: rubric trong prompt, luật "cuốn", claims+nguồn, overlays | 8 | 6 | 9 | 9 | 9 | 9 | 6 |
| 4 | Hook | 1 câu ≤ 12 từ, chữ to frame 0 trên ảnh AI | 6 | 4 | 9 | 10 | 10 | 10 | 4 |
| 5 | Voice | VieNeu preset Thiện Minh, ONNX CPU, 723s | 6 | 5 | 7 | 10 | 10 | **2** | 5 |
| 6 | Visual gen | FLUX.2-klein / SDXL + depth parallax | 7 | 4 | 7 | 9 | 10 | 7 | 4 |
| 7 | B-roll / bằng chứng | thẻ stat/chart/code, screenshot HF/arXiv tĩnh | 8 | 7 | 8 | 9 | 10 | 9 | 7 |
| 8 | Editing | Remotion: cut + whip-pan, Ken Burns, punch-in, 581s render | 8 | 6 | 8 | 10 | 10 | 4 | 7 |
| 9 | Caption (phụ đề) | karaoke cụm 1–3 từ, nhấn từ khoá, drift ≤ 120ms | 9 | 7 | 10 | 10 | 10 | 10 | 8 |
| 10 | Music | ACE-Step 1.5 CPU ~85s, ducking 15 LU | 7 | 6 | 9 | 10 | 10 | 8 | 6 |
| 11 | Sound design | SFX numpy tự tổng hợp | 5 | 5 | 10 | 10 | 10 | 10 | 5 |
| 12 | QA | T1 code 15 kiểm · T2 VLM · T3 LLM checklist · T4 fact-check · trần 2 vòng | 8 | **3** | 7 | 9 | 7 | 4 | 3 |
| 13 | Export | mp4 1080×1920, −14 LUFS | 9 | – | 10 | 10 | 10 | 9 | 9 |
| 14 | Upload | draft API code xong, chờ phần tay (P1.S1) | – | – | 6 | 6 | 10 | – | – |
| 15 | Analytics | chưa có (P7) | 0 | 0 | 0 | 0 | – | – | 0 |
| 16 | Iteration | chưa có vòng nào vì chưa đăng | 0 | 0 | 0 | 0 | – | – | 0 |

### 5.1 Chi tiết theo stage

**1. Trend scout.**
- *Mạnh:* nguồn hợp pháp, có snapshot, gom cụm, `vn_fit`.
- *Yếu:* mọi nguồn đều là nơi dev đọc. "Hot trên HN" ≠ "người Việt lướt TikTok quan tâm". Google Trends VN mới chỉ được dùng làm phụ.
- *Thiếu:* tín hiệu **nhu cầu tìm kiếm** — CRP chấm "search value" (FACT). Cụ thể là gợi ý tìm kiếm trên TikTok (Tony xem tay) và Google Trends `geo=VN` theo từ khoá công cụ phổ thông (ChatGPT, Gemini, Canva AI, CapCut AI).
- *Rủi ro retention:* topic đúng kỹ thuật nhưng không ai quan tâm → hỏng ngay từ cửa 1.

**3. Script.**
- *Mạnh:* kỷ luật tốt nhất repo. Cấm số trong lời đọc, claim có nguồn, rubric trong prompt, luật vòng tò mò + kết vòng.
- *Yếu:* hook và chữ frame 0 là **cùng một câu**. Lời đọc 12 từ mà chữ trên màn hình 4 dòng, nên người xem đọc không kịp trong 1s. Theo Kallaway, chữ nên là bản rút gọn ≤ 7 từ khác lời.
- *Thiếu:*
  - trường `hook_type` để học sau 20 video
  - trường `format`/`pillar`
  - một quan sát ngôi thứ nhất bắt buộc — rubric §5 mới chỉ ghi vết, vì brief chưa có số đo probe.
- *Slop risk:* trung bình. Câu ổn, nhưng các video sẽ giống nhau nếu mọi video dùng một khuôn (đúng định nghĩa "inauthentic" của YouTube).

**4. Hook (hình).** Đây là chỗ yếu nhất so với mức quan trọng.
- Frame 0 của demo-03 là mặt người AI trong phòng tối. Nó không chứa tín hiệu nào về chủ đề (Google/OpenAI/giá), và chữ đè lên mặt.
- Mọi bằng chứng (≥ 5s đầu là nơi skip nhiều nhất) nói đây là chỗ đáng đầu tư nhất, nhưng luật hiện tại còn **cấm** shot bằng chứng ở câu 0 (`scriptwriter.py` luật 7).

**5. Voice.**
- *Mạnh:* license đã sạch (Apache), có loudnorm, có ASR kiểm phát âm.
- *Yếu:* preset là giọng của người khác → không có bản sắc. Chưa có clone giọng Tony.
- *Bottleneck:* **723s** trên CPU, chiếm ~1/3 wall time.
- *Rủi ro:* Tony đã chê giọng 2 lần (08-14, 10-02). Đây là rủi ro `approve_rate` cao nhất.

**6. Visual gen.**
- *Mạnh:* parallax, ảnh một chủ thể, luật nền tối.
- *Yếu:*
  - mặt người AI biểu cảm (3 khuôn mặt trong 40s)
  - tủ server lặp lại
  - 7 lần dựng lại vì đèn chói/ảnh sập
- *Slop risk:* **cao**. Người hiểu AI (đúng khán giả kênh này) nhận ra ảnh AI nhanh nhất, và DATA Xiao 2026 cho thấy càng hiểu AI thì phản ứng âm qua mất tin cậy càng mạnh.
- *Thừa:* đầu tư tiếp vào model ảnh (P3b.S8) là đầu tư vào loại hình nên **giảm** tỉ trọng.

**7. B-roll bằng chứng.** Đây là tài sản tốt nhất.
- *Lỗi nhìn thấy:* nhãn trùng đơn vị "Giá Gemini 4 Argon (USD/triệu token) (USD)" (`remotion/src/components/Evidence.tsx:171` luôn nối `(unit)` vào title); chart chữ nhỏ ở 1/3 trên với nhiều khoảng trống; số "10" đứng một mình.
- *Thiếu:* **quay màn hình động** (cuộn/gõ/bấm). `visual/screenshot.py` đã chạy Playwright; chỉ cần bật `record_video` của browser context (chưa dùng).

**8. Editing.**
- *Mạnh:* nhịp đúng vùng giữa của chữ U, punch-in gắn với từ nhấn.
- *Bottleneck:* render 581s. Nên kiểm `--concurrency` của Remotion và xem depth parallax có tốn không.
- *Rủi ro:* thấp.

**9. Phụ đề.** Tốt. Rủi ro duy nhất là chữ hook và phụ đề chồng nhau ở 3s đầu.

**10–11. Nhạc, SFX.**
- Mức nhạc đúng theo DATA Torcoli.
- SFX tổng hợp bằng numpy có nguy cơ nghe "máy". Whoosh ở **mọi** điểm cắt là dấu hiệu template.
- Chưa có bằng chứng SFX giúp gì. → Giảm tần suất, hoặc A/B có/không SFX.

**12. QA.** Kỹ thuật thì tốt, nhưng chưa đo đúng thứ cần đo.
- *Mạnh:* T1 code, trần 2 vòng, T4 fact-check, ghi vết. Hiếm repo nào có.
- *Yếu:*
  - (a) không tầng nào đo **cửa 1–2** (frame 0, 5s đầu) bằng code
  - (b) T3 cho 10/10 một video Tony chê → T3 không dự đoán approve
  - (c) vòng patch tốn 330–380s/vòng và đã 2 lần làm video **tệ đi** (ảnh mới chói hơn)
  - (d) T1 chặn oan vì đèn trần
- *Thiếu:* các kiểm proxy retention bằng code (mục 6.2) + **ô Tony chấm 1–5 sau mỗi video**.

**14–16. Upload, analytics, iteration.** Đây là khoảng trống lớn nhất.
- Hệ thống có đủ "Generate → Produce → QA" nhưng **không có "Publish → Measure → Learn"**. Không có vòng phản hồi thì mọi điểm số ở trên là đoán.
- Display API không trả watch time (FACT), nên cần Tony export CSV từ TikTok Studio. Việc này mất 2 phút/tuần, và đó là cái giá rẻ nhất để có metric thật.

### 5.2 Bottleneck, thừa, điểm hỏng

| Loại | Mục |
|---|---|
| **Bottleneck thời gian** | TTS CPU 723s · render 581s · QC patch 330–380s/vòng → một video có 1 vòng sửa đã ≈ 40 phút |
| **Bottleneck học** | 0 video đăng → không biết cái gì đúng |
| **Thừa / nên hoãn** | showrunner + lịch tuần (P5.S2) trước khi có 10 video đăng · thêm model ảnh mới · vòng patch T2 tự động (làm tệ 2/3 lần ở demo-03) |
| **Điểm hỏng** | exp-echo phải chạy cổng 8000 · aligner đặt nhầm từ · T1 heuristic chữ-trong-UI bắt nhầm đèn · LLM call chạy Opus cho mọi vai (cost_usd SDK ghi ~5 USD cho demo-03 — nếu gói thuê bao đổi chính sách, `research/10` §1 đã cảnh báo) |
| **AI slop risk** | mặt người AI · b-roll server chung chung · mọi video cùng khuôn hình/âm |
| **Retention risk** | frame 0 không mang chủ đề · topic dev-only · giọng preset |
| **Quality risk** | nhãn chart trùng đơn vị · chart nhỏ · ảnh sập cần dựng lại |

**Cái tôi KHÔNG đề nghị bỏ:** T1 code, T4 fact-check, trần 2 vòng, `video-spec.json`, thẻ bằng chứng, phụ đề
cụm. Đó là những thứ có bằng chứng hoặc là điểm tựa không ảo.

---

## 6. Sửa ngay — xếp theo Impact × Effort

Impact/Effort 1–5 là **HYP**. Mỗi mục: WHY → HOW → KPI.

| # | Việc | I | E | WHY | HOW | KPI |
|---|---|---|---|---|---|---|
| **1** | **Đăng 10 video, đo thật** | 5 | 2 | 0 dữ liệu = tối ưu mù; Buffer: nhiều phát bắn → nhiều cơ hội top | xong P1.S1 phần tay; đăng draft 1/ngày; Tony export CSV TikTok Studio/tuần vào `team/analytics/` | % còn lại ở 2s, 5s · avg watch % · view t+72h · approve |
| **2** | **Clone giọng Tony** | 5 | 2 | giọng = yếu tố mạnh nhất (DATA); 2 lần chê giọng; clone ≈ thật hơn generic | Tony thu 10–30s sạch (đọc 1 đoạn tin AI, phòng im) → VieNeu v3 Turbo clone → nghe mù với Thiện Minh | Tony chọn mù; ASR WER ≤ preset; approve |
| **3** | **Frame 0 = bằng chứng + chữ hook ≤ 7 từ khác lời** | 5 | 2 | cửa 1 quyết định; chữ > hình > lời (OBS); 63% CTR cao đưa thông điệp trong 3s (DATA ads) | thêm `hook_text` (≤ 7 từ) vào schema; bỏ luật cấm shot bằng chứng ở câu 0; shot 0 ưu tiên screenshot/stat | % còn lại ở 2s (Studio); T1 mới: `hook_text_words ≤ 7` |
| **4** | **TTS lên GPU** | 3 | 1 | 723s → ước ~1–2 phút (HYP từ RTF card) | VieNeu GPU 1,1GB đỉnh, chạy trước align, kiểm `nvidia-smi` | wall time TTS ≤ 120s |
| **5** | **Quay màn hình động thay ảnh AI** | 4 | 3 | bằng chứng thật chống slop; tool/tutorial = save cao (HYP) | Playwright `record_video` cuộn tới `highlight`, 3–5s, 1080 dọc, zoom vùng chữ | tỉ lệ thời lượng "bằng chứng thật" ≥ 50%; mặt AI ≤ 1 |
| **6** | **Ô chấm của Tony + lý do** | 4 | 1 | approve nhị phân không nói *vì sao*; T3 không dự đoán approve | `approval.json`: điểm 1–5 cho hook/giọng/hình/nội dung + 1 dòng | sau 20 video: tầng QC nào tương quan với điểm Tony |
| **7** | **Pillar "AI dùng ngay cho người Việt"** | 4 | 2 | 87% dùng tool AI (DATA); topic dev hẹp (HYP) | brief từ Google Trends VN + gợi ý search TikTok; 50% video thuộc pillar này trong 10 video đầu | view t+72h, save rate so pillar news |
| **8** | **A/B độ dài 30s vs 60–75s** | 3 | 1 | bằng chứng mâu thuẫn (2.4) → phải tự đo | Thompson sampling đã thiết kế ở P7.S2; xen kẽ | avg watch %, view t+72h |
| **9** | **Bỏ vòng patch T2 tự động** → chỉ cờ cho Tony | 3 | 1 | 2/3 lần làm tệ đi; 330s/vòng | T2 thành warn; regen chỉ khi `anatomy_error`/`garbled_text` | wall time; T1 pass rate |
| **10** | **SFX tiết chế** | 2 | 1 | whoosh mọi cut = dấu hiệu template; 0 bằng chứng | whoosh chỉ khi đổi ý lớn; pop khi thẻ số; ≤ 1/5s | Tony nghe mù có/không |
| **11** | Sửa chart: bỏ trùng đơn vị, chữ to hơn, căn giữa | 2 | 1 | đọc được trên điện thoại | `Evidence.tsx` | T2 low_contrast |
| **12** | Tag `hook_type`, `pillar`, `format` trong script.json | 3 | 1 | để học từ 20 video | thêm trường + scriptwriter chọn 1 trong 20 loại (bảng 4.2) | – |

**Không nên làm lúc này:** showrunner tuần, Telegram bot đẹp, model ảnh mới, talking-head avatar,
video AI — tất cả là thêm agent/khối trước khi biết vấn đề nằm ở đâu (`eval-discipline.md`: "Đừng thêm agent").

---

## 7. Pipeline mới (sau khi sửa)

Nguyên tắc: **không thêm agent**. Sửa vai có sẵn + thêm hai vòng con người rẻ (Tony chấm, Tony export số).

| Stage | Input | Process | Output | Tool (0đ) | Người | Auto | KPI | Kiểm | Failure mode |
|---|---|---|---|---|---|---|---|---|---|
| 1 Trend | RSS/API + Google Trends VN | gom cụm, chấm hot + **search demand** | `team/trends/<ngày>.json` | trend_scout, bge-m3 | Tony tick 1 topic (30s) | cao | % topic Tony chọn | snapshot nguồn | topic dev-only |
| 2 Chọn topic + pillar | trends + analytics | quota pillar, không trùng 14 ngày | `brief.json` (facts+url) | code | — | cao | đa dạng pillar | code | lặp chủ đề |
| 3 Script + hook | brief | LLM 1 lần: `hook_type`, `hook_text`, lời, shots | `script.json` | claude-agent-sdk | — | cao | approve | T3 checklist (giữ, chỉ warn) | hook chung chung |
| 4 Fact-check | script | T4 (cả số trên thẻ) | `factcheck.json` | T4 | inconclusive → Tony | cao | fact_error=0 | chặn cứng | nguồn chết |
| 5 Voice | lời | **clone Tony**, GPU, ghép đoạn | `voice.wav` | VieNeu v3 Turbo | thu mẫu 1 lần | cao | TTS ≤ 120s | ASR WER, loudness | phát âm tên riêng |
| 6 Visual plan | script | router: **màn hình động > thẻ > log > ảnh AI** | shot list | code | — | cao | % bằng chứng thật ≥ 50 | code | URL chết → fallback |
| 7 Gen | shot list | Playwright quay · FLUX/SDXL chỉ khi cần | shots/ | Playwright, FLUX.2-klein | — | cao | ảnh AI ≤ 25% | T2 warn | ảnh sập |
| 8 Edit + subtitle + audio | spec | Remotion; nhạc ACE; SFX tiết chế | mp4 | Remotion, ACE-Step | — | cao | render ≤ 5 phút | T1 | drift, OOM |
| 9 QA | mp4 | T1 + **proxy retention (6.2)** + T4; T2/T3 warn | `qc/decision.json` | code + VLM | — | cao | t1_pass ≥ 0,9 | trần 2 | chặn oan |
| 10 Duyệt | mp4 + scorecard | Tony xem trên điện thoại, chấm 4 ô | `approval.json` | file/Telegram sau | **Tony** | thấp (có chủ đích) | approve_rate | — | Tony bận → hàng đợi |
| 11 Đăng | approved | draft API → Tony bấm đăng + nhãn AI + caption dán | TikTok | P1.S1 | Tony 1 phút | trung | ≥ 5/tuần | 5 draft/24h | token hết hạn |
| 12 Đo | Studio CSV | Tony thả CSV/tuần; code tính 2s/5s/avg%/view t+72h | `team/analytics/` | pandas | Tony 2 phút | trung | — | — | quên export |
| 13 Học | analytics + approval | sau mỗi 10 video: bảng hook_type × retention; Thompson cho độ dài/pillar | `research/probes/learn-<n>.md` | code + 1 LLM | Tony đọc | trung | approve, retention ↑ | ≥ 10 video/nhánh | kết luận từ mẫu nhỏ |

**Giữ con người ở:** chọn topic (30s), nghe mẫu giọng một lần, duyệt video, bấm đăng, export số. Lý do:
approve_rate là metric chính (Tony là người dùng duy nhất); TikTok không cho direct post khi chưa audit;
và quan trọng nhất — **không có tín hiệu ngoài thì tự sửa làm tệ đi** [Huang et al., `research/10` §5].

---

## 8. Pre-Publish Scorecard

### 8.1 Cơ sở

- Đây là **heuristic**. Không có mô hình nào dự đoán viral tốt (R² ≤ 0,27). Mục tiêu của scorecard là
  **chặn video chắc chắn dở** và **ghi lại vì sao**, không phải dự đoán view.
- Trọng số theo vị trí trong 4 cửa: cửa 1–2 (5s đầu) nặng nhất vì đó là nơi rời bỏ nhiều nhất (DATA).
- Mục **code** chấm được thì code chấm (không ảo). Mục cảm nhận → **Tony** chấm, không LLM (LLM chấm
  "hay" ~0 tương quan).
- **Ngưỡng dưới đây viết 2026-10-02, trước khi có video đăng nào.** Sau 20 video: tính tương quan từng mục
  với retention 5s + approve; mục nào ~0 thì bỏ (`eval-discipline.md`). Không sửa ngưỡng lặng lẽ.

### 8.2 Bảng chấm (100 điểm)

| Mục | Max | Ai chấm | 0 điểm khi | Max khi |
|---|---|---|---|---|
| **Hook — frame 0** | 12 | code + Tony | frame 0 không liên quan chủ đề; chữ > 10 từ | hình bằng chứng của chủ đề + chữ ≤ 7 từ, sáng |
| **Hook — 3s lời** | 10 | code (T3 hiện có) + Tony | chào/bối cảnh/định nghĩa | có thông tin cụ thể trong 3s |
| Curiosity / open loop | 6 | Tony | không có câu hỏi nào mở | vòng mở ở hook, trả ở ~2/3 |
| Value (biết thêm gì) | 10 | Tony | không học được gì | ≥ 1 điều người xem dùng/kể lại được |
| Story / ngoặt | 5 | Tony | liệt kê phẳng | có ngoặt giữa video |
| Pacing | 6 | code | ý > 12s; shot < 2s liên tục | đổi ý 5–8s, shot 2,5–5s |
| Voice | 10 | Tony + code (WER, F0) | nghe như máy, đọc sai tên | nghe như người kể |
| Visual — bằng chứng thật | 8 | code | ảnh AI > 50% thời lượng | bằng chứng ≥ 50%, mặt AI ≤ 1 |
| Visual — kỹ thuật | 5 | code (T1) + T2 | lỗi giải phẫu, chữ méo, viền đen | sạch |
| Caption / phụ đề | 5 | code | drift > 120ms, lấn safe zone | cụm, nhấn đúng |
| Sound + music | 5 | code | clip, nhạc > giọng −10 LU | −14 LUFS, nhạc 12–18 LU dưới |
| Accuracy | gate | T4 | **mâu thuẫn > 0 → không đăng** | |
| Shareability | 5 | Tony | không có lý do gửi cho ai | "gửi cho đứa bạn X" có thật |
| Saveability | 5 | Tony | không có gì dùng lại | danh sách/bước/prompt dùng lại được |
| Rewatch / loop | 4 | code + Tony | kết bằng chào/màn đen | câu cuối nối hook, khung cuối ≈ hook |
| CTA | 2 | code | "like và follow" | xin lưu/chia sẻ cụ thể |
| Branding / nhất quán | 2 | code | lệch palette/font | đúng style.yaml |
| **Tổng** | **100** | | | |

### 8.3 Ngưỡng (heuristic, viết trước — 2026-10-02)

| Mức | Điều kiện | Hành động |
|---|---|---|
| **Publish** | ≥ 70 **và** Hook (frame 0 + 3s) ≥ 16/22 **và** Voice ≥ 6 **và** T4 pass | đăng |
| **Warning** | 55–69, hoặc một mục cửa 1–2 dưới ngưỡng | Tony quyết; ghi lý do |
| **Kill / rewrite** | < 55, hoặc Hook < 10/22, hoặc T4 fail | viết lại script/hook, không sửa hình |

Lý do Hook có ngưỡng riêng: video 80 điểm mà frame 0 dở thì phần còn lại không ai thấy.

### 8.4 Proxy retention bằng code — thêm vào T1 (không LLM)

| Kiểm | Ngưỡng đề xuất | Cách đo |
|---|---|---|
| `hook_text_words` | ≤ 7 | đếm chữ overlay frame 0 |
| `first_info_sec` | ≤ 3,0 | thời điểm token đầu tiên của câu có số/tên riêng (từ karaoke) |
| `frame0_brightness` | luma TB vùng chủ thể ≥ ngưỡng demo-02 | OpenCV |
| `max_idea_sec` | ≤ 12 | khoảng giữa 2 lần đổi shot/overlay |
| `ai_image_share` | ≤ 0,5 thời lượng | từ spec |
| `ending_loop` | SSIM(khung cuối, khung 0) hoặc khung cuối là thẻ số | OpenCV |
| `cta_ends_with_goodbye` | false | regex |

Những ngưỡng này **chưa có cơ sở số** ngoài suy luận ở mục 3 → bắt đầu ở chế độ **warn**, chỉ thành chặn sau
khi 20 video cho thấy tương quan.

---

## 9. Checklist mỗi ngày

**BEFORE SCRIPT**
- [ ] Topic thuộc pillar nào? Không trùng 14 ngày, ≤ 2 video liền cùng pillar
- [ ] Người xem VN **được gì**: dùng được ngay / biết trước người khác / tiết kiệm tiền?
- [ ] Có ≥ 2 nguồn gốc + 1 thứ nhìn thấy được (trang, tool, số) để làm frame 0

**SCRIPT**
- [ ] `hook_type` chọn từ bảng 4.2; chữ hook ≤ 7 từ, khác lời nhưng cùng ý
- [ ] Thông tin cụ thể trong 3s đầu; không chào
- [ ] Vòng tò mò mở ở hook, trả ở ~2/3; có 1 ngoặt
- [ ] Mỗi câu: người xem biết thêm gì? Không → xoá
- [ ] CTA xin lưu/chia sẻ cụ thể; câu cuối nối hook

**VOICE**
- [ ] Giọng clone Tony (hoặc preset đã chốt); tên riêng qua `pronounce.yaml`
- [ ] Nghe 5s đầu bằng tai — có "máy" không?

**VISUAL**
- [ ] Frame 0 là bằng chứng của chủ đề, sáng, 1 chủ thể
- [ ] ≥ 50% thời lượng là bằng chứng thật; mặt người AI ≤ 1
- [ ] Chart/thẻ đọc được trên điện thoại (thử trên máy thật)

**EDITING**
- [ ] Không ý nào > 12s; không chuỗi shot < 2s
- [ ] Khung cuối = thẻ số chính hoặc hình hook (loop)

**AUDIO**
- [ ] −14 LUFS; nhạc 12–18 LU dưới giọng
- [ ] SFX ≤ 1/5s, mỗi cái có lý do

**SUBTITLE**
- [ ] Không lấn safe zone; drift ≤ 120ms; nhấn ≤ 6 cụm

**QA**
- [ ] T1 pass · T4 0 mâu thuẫn · scorecard ≥ 70 · Hook ≥ 16/22
- [ ] Tony xem **trên điện thoại**, có tiếng và tắt tiếng

**BEFORE POST**
- [ ] Bật nhãn AI-generated trong app
- [ ] Caption ≤ 150 ký tự, từ khoá chính trong 100 ký tự đầu, 3–5 hashtag ngách
- [ ] Ghi `approval.json` (4 điểm + 1 dòng lý do)

**AFTER POST**
- [ ] t+72h: ghi view; cuối tuần: export CSV Studio vào `team/analytics/`
- [ ] Đọc retention ở 2s và 5s — rơi ở đâu, hook loại gì
- [ ] Trả lời 3 comment đầu (comment là tín hiệu tương tác FACT)

---

## 10. Recommended tools — ràng buộc 0đ, RTX 2060 6GB

Tool trả phí (ElevenLabs, HeyGen, Runway, CapCut Pro, OpusClip) **bị loại bởi ràng buộc chi phí**. Chúng
chỉ xuất hiện ở cột "nếu bỏ ràng buộc" để biết mình đang đánh đổi gì.

| Nhóm | Dùng | Giải quyết vấn đề gì | License / VRAM | Nếu bỏ ràng buộc 0đ |
|---|---|---|---|---|
| Research/trend | `trend_scout` (HF, HN Algolia, arXiv, RSS, GenK/VnExpress) + **Google Trends VN** + Tony xem gợi ý search TikTok | topic có cầu thật ở VN | 0đ, API công khai | Exploding Topics |
| Script | claude-agent-sdk (đã có) | kịch bản + JSON có schema | gói hiện có (`research/10` §1 cảnh báo) | — |
| Fact-check | T4 + snapshot trafilatura | fact_error = 0 | Apache | — |
| Voice | **VieNeu-TTS v3 Turbo clone giọng Tony** (GPU 1,1GB) | giọng thật, bản sắc | Apache-2.0; v4 đóng — đừng chờ | ElevenLabs clone |
| Voice (dự phòng) | VoxCPM2 (Apache) — probe fp16 Turing | giọng biểu cảm hơn | Apache | — |
| Loại | F5-TTS-vi, viXTTS, TangoFlux, MMAudio, YuE2 | — | **NC** | — |
| Image | FLUX.2-klein-4B (Apache, đã dùng) · SDXL-Lightning dự phòng | b-roll trừu tượng — **dùng ít đi** | Apache; 9B là NC | Midjourney |
| Screen | **Playwright `record_video`** (đã cài) | bằng chứng động, demo-first | Apache | Screen Studio |
| Video gen | **không** — Wan2.1 1,3B cần 8,2GB; LTX OOM (P1.S4) | — | — | Veo/Kling |
| Editing | Remotion (đã có) | dựng từ spec | license công ty theo dõi | CapCut |
| Subtitle | karaoke từ forced aligner (đã có) | đồng bộ ≤ 120ms | — | Submagic |
| Music | ACE-Step 1.5 turbo CPU (MIT) | nhạc nền không bản quyền bên thứ ba | MIT; README xin công khai dùng AI | Epidemic |
| SFX | Stable Audio Open Small (≤ 1M USD/năm: thương mại được) **hoặc** Freesound **CC0** · Sonniss GDC (thương mại, không cần ghi công) | SFX thật thay numpy | xem cột | — |
| QC VLM | MiniCPM-V 4.6 (1,3B, 4GB, Apache) để thử thay VLM hiện tại nếu nhanh hơn | T2 rẻ hơn | Apache | — |
| Analytics | TikTok Studio CSV (tay) + pandas · Display API (view/like, chỉ public) | retention thật | 0đ | Business API (cần Business account — mất thư viện nhạc chung) |
| Automation | Python điều phối + `state.json` + cron (đã thiết kế) | chạy lại từ stage hỏng | — | — |

---

## 11. Câu hỏi để Tony quyết (không tự làm)

1. **Clone giọng anh?** Cần 10–30s anh đọc. Nếu không, chọn preset bằng nghe mù 4 giọng (`out/demo-giong`).
2. **Khi nào đăng video đầu?** Mọi khuyến nghị ở đây chỉ được xác nhận khi có retention thật.
3. **Pillar "AI dùng ngay cho người Việt"** — có muốn kênh rộng hơn mạch dev/model mới không?
4. **Có muốn lộ mặt/giọng thật không** — đây là quyết định thương hiệu, không phải kỹ thuật.

---

## Nguồn (fetch 2026-10-02)

**TikTok/nền tảng (FACT):** newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you [2020-06] ·
…/learn-why-a-video-is-recommended-for-you [2022-12] · …/introducing-a-way-to-refresh-your-for-you-feed-on-tiktok-us [2023-03] ·
newsroom.tiktok.com/more-ways-to-spot-shape-and-understand-ai-content [2025-11] ·
newsroom.tiktok.com/introducing-the-new-creator-rewards-program [2024-03] ·
tiktok.com/legal/page/global/tiktok-creator-rewards-program-eea/en ·
newsroom.tiktok.com/en-us/new-labels-for-disclosing-ai-generated-content [2023-09] ·
c2pa.org/c2pa-welcomes-tiktok-to-steering-committee [2026-07] ·
developers.tiktok.com/doc/content-sharing-guidelines · …/content-posting-api-reference-upload-video ·
ads.tiktok.com/help/article/commercial-music-library [2025-07] ·
newsroom.tiktok.com/tiktok-for-business-introduces-watch-it-love-it-want-it [2026-03] ·
support.google.com/youtube/answer/1311392 [2025-07]

**TikTok Ads (DATA quảng cáo):** ads.tiktok.com/help/article/creative-best-practices [2025-06] ·
ads.tiktok.com/business/en-US/blog/9-creative-tips-to-drive-auction-ad-performance [2020-10] ·
…/7-ways-to-make-your-videos-tiktok-friendly [2022-03] · …/evolution-of-sound-volume-1 [2021-12] ·
ads.tiktok.com/business/creativecenter/quicktok/online/Power_Creative_Elements/pc/en [2022-11] ·
…/tiktok_creative_accelerator/pc/en

**Học thuật:** arxiv.org/abs/2504.03107 · arxiv.org/html/2603.22663v1 · arxiv.org/html/2503.20030v2 ·
arxiv.org/abs/2206.06003 · kuairand.com · arxiv.org/abs/2604.19995 · arxiv.org/abs/2606.16053 ·
arxiv.org/abs/2601.18218 · pmc.ncbi.nlm.nih.gov/articles/PMC11704130 (Le Quéré & Matias 2025) ·
neuroecon.berkeley.edu (Kang 2009) · jordandelong.com/pubs/2010/AttentionEvolution.pdf ·
pmc.ncbi.nlm.nih.gov/articles/PMC10994390 (Wang & Li 2024) ·
archives.marketing-trends-congress.com/2025/pages/PDF/060.pdf (Reichstein & Dost) ·
arxiv.org/abs/2403.00454 · experts.umn.edu (Miller 1976) ·
journals.plos.org/plosone/article?id=10.1371/journal.pone.0332692 (Lavan 2025) ·
isca-archive.org/interspeech_2015/tsai15b_interspeech.html · arxiv.org/abs/2305.19100 (Resti/Torcoli) ·
pmc.ncbi.nlm.nih.gov/articles/PMC13405702 (Xiao 2026) · arxiv.org/abs/2506.16202 ·
faculty.wharton.upenn.edu/…/Virality.pdf (Berger & Milkman) · arxiv.org/abs/2111.02452 · arxiv.org/abs/2102.01163 ·
Gernsbacher 2015 (reported) · Coupé et al. Sci. Adv. 2019 (reported)

**Ngành/creator:** socialinsider.io/blog/tiktok-vs-reels-vs-shorts · socialinsider.io/social-media-benchmarks/social-media-video-statistics ·
socialmediatoday.com/news/tiktok-post-frequency-improves-per-post-reach-report-buffer/802443 ·
buffer.com/resources/best-time-to-post-on-tiktok · opus.pro/research/tiktok-video-guide · rivaliq.com/blog/social-media-industry-benchmark-report ·
threadreaderapp.com/thread/1646898356419981315.html (Paddy Galloway) · content.game/p/visualhooks (Kallaway) ·
linkedin.com/posts/jayclouse_… (Hoyos) · eomag.io/article/the-rundown-ai-rowan-cheung · techcrunch.com/2025/11/18/…

**VN + tool:** datareportal.com/reports/digital-2026-vietnam · vietnamnet.vn/en/vietnamese-spend-2-hours-daily-… ·
decisionlab.co/blog/vietnams-digital-landscape-q3-2025 · tilleke.com/insights/a-closer-look-at-vietnams-new-ai-law-… ·
technode.global/2026/03/04/vietnam-impose-mandatory-ai-labeling · luatvietnam.vn/…-186-108836-article.html ·
xaydungchinhsach.chinhphu.vn/… (NĐ 147) · github.com/pnnbao97/VieNeu-TTS · huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo ·
github.com/yoonjae26/vietnamese-tts · huggingface.co/ACE-Step/Ace-Step1.5 · huggingface.co/stabilityai/stable-audio-open-small ·
stability.ai/license · freesound.org/help/faq · sonniss.com/gdc-bundle-license · huggingface.co/black-forest-labs/FLUX.2-klein-4B ·
github.com/Wan-Video/Wan2.1 · github.com/openbmb/MiniCPM-V

**Không fetch được (JS/403):** TikTok Creator Academy, FYF standards, profile TikTok mọi creator, X, Hootsuite,
Sagepub, ScienceDirect, science.org — mọi số từ các nguồn này trong báo cáo đều ghi *reported*.
