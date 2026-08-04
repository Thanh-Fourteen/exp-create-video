# Nhật ký nguồn

Mọi con số trong `05-decision.md` truy ngược về đây. Quy ước: **verified** = đã đọc
nguồn gốc / tự chạy lệnh · **reported** = nguồn thứ cấp · **assumed** = suy đoán.

Khảo sát ngày **2026-08-04**. Lĩnh vực này đổi theo tháng — đọc lại trước khi tin.

---

## Đo trên máy — verified

| Nguồn | Nội dung | Ngày |
|---|---|---|
| `nvidia-smi` trên `tony` | RTX 2060, 6144 MiB, driver 580.173.02 | 2026-08-04 |
| `nproc` / `free -g` trên `tony` | 12 core, RAM 31GB | 2026-08-04 |
| `df -h` trên `tony` | `/` còn 53GB, `/mnt/data1tb` còn 605GB | 2026-08-04 |
| `ssh tris nvidia-smi` | 2× RTX 5090 32607 MiB, **used 29966 / 28882 MiB** | 2026-08-04 |
| `ssh tris` `nproc`/`free` | 32 core, RAM 123GB, `/` còn 315GB | 2026-08-04 |
| `ffmpeg -version` trên `tony` | ffmpeg 8.0 | 2026-08-04 |

## GitHub API — verified

`gh api repos/<owner>/<repo>` ngày **2026-08-04**:

| Repo | ★ | License | Push cuối | Đọc ra gì |
|---|---|---|---|---|
| `harry0703/MoneyPrinterTurbo` | 101.436 | MIT | 2026-08-02 | Sống khoẻ. **Kiến trúc pipeline đáng học** — đọc cách nó tách script/asset/voice/subtitle/BGM |
| `remotion-dev/remotion` | 55.436 | **NOASSERTION** ⚠️ | 2026-08-03 | Sống khoẻ nhưng license không chuẩn — **phải đọc kỹ điều kiện thương mại** |
| `Lightricks/LTX-Video` | 10.801 | Apache-2.0 | 2026-01-05 | 7 tháng không push — đang chậm lại, ghi vào rủi ro |
| `RayVentura/ShortGPT` | 7.757 | MIT | **2025-02-10** | **18 tháng chết** — chỉ đọc để tham khảo ý tưởng, **không phụ thuộc** |
| `redotvideo/revideo` → `midrender/revideo` | 3.952 | MIT | 2026-07-15 | Đã đổi tên owner. Fork MIT của Remotion — **đường thoát nếu license Remotion thành vấn đề** |

## Phần cứng & model sinh ảnh/video — reported

Chưa tự đo. P1 sẽ chuyển sang verified.

| Nguồn | Nội dung |
|---|---|
| [localaimaster.com/blog/local-text-to-video-low-vram](https://localaimaster.com/blog/local-text-to-video-low-vram) | Wan2.2 14B GGUF Q4 xuống 6GB @480p nhưng cần 24–32GB RAM, 10–15 phút/clip |
| [willitrunai.com/blog/video-generation-gpu-guide-2026](https://willitrunai.com/blog/video-generation-gpu-guide-2026) | Bảng VRAM theo model; LTX-Video 2B FP8+tiling cần 6–8GB, tối đa 720p |
| [willitrunai.com/video-models/ltx-video-2-3](https://willitrunai.com/video-models/ltx-video-2-3) | LTX-Video 2B: tối đa 1280×720, 161 frame @24fps |
| [localaimaster.com/blog/flux-local-image-generation](https://localaimaster.com/blog/flux-local-image-generation) | Flux.1-schnell GGUF Q4_0 = 6,88GB; trên GPU 6GB chạy được nhưng **~2+ phút/ảnh** |
| [localaimaster.com/blog/sdxl-vs-flux-local](https://localaimaster.com/blog/sdxl-vs-flux-local) | SDXL-Turbo nhanh hơn ở 1–2 step, đổi lại chất lượng thấp hơn Flux |
| [nvidia.com — Quick Start LTX-2 ComfyUI](https://www.nvidia.com/en-sg/geforce/news/rtx-ai-video-generation-guide/) | LTX-2 trên 5090 (32GB): 720p 24fps 4s ≈ 25s |
| [zenn.dev — LTX-2.3 vs Wan 2.2 I2V benchmark RTX5090](https://zenn.dev/toki_mwc/articles/ltx23-vs-wan22-i2v-benchmark-rtx5090?locale=en) | LTX-2.3 distilled 22,1s warmed-up trên 5090 — **nhanh hơn Wan2.2 5,7 lần** |
| [spheron.network — Deploy Wan 2.1/2.2](https://www.spheron.network/blog/deploy-wan-2-1-ai-video-generation-gpu-setup/) | Wan 14B cần **65–80GB @720p** → 5090 32GB **không chạy được** |
| [hostrunway.com — AI Video Generation 2026 GPU guide](https://www.hostrunway.com/blog/ai-video-generation-2026-best-gpus-vram-guide-and-smart-setups-that-work/) | Xác nhận lại ngưỡng VRAM theo dòng GPU |

⚠️ **Cảnh báo đọc bảng:** các số trên đến từ nhiều harness khác nhau, **không so chéo
giữa các bảng**. Chúng chỉ dùng để loại ứng viên rõ ràng ngoài tầm (Wan2.2 14B), không
dùng để xếp hạng giữa hai ứng viên gần nhau.

## TikTok API — reported

| Nguồn | Nội dung |
|---|---|
| [developers.tiktok.com — Content Posting API](https://developers.tiktok.com/doc/content-posting-api-get-started) | Tài liệu gốc của flow đăng bài |
| [netrows.com — TikTok Content Posting API 2026](https://www.netrows.com/blog/tiktok-content-posting-api-guide-2026) | Client **chưa audit → mọi direct post ép `SELF_ONLY`** |
| [timetopost.co — How to Post to TikTok via API 2026](https://timetopost.co/blog/how-to-post-to-tiktok-api/) | Audit cần **demo quay màn hình toàn luồng + privacy policy URL + sản phẩm hoàn chỉnh**; 2–4 tuần, nhiều vòng phản hồi |
| [postpeer.dev — Direct Post, Audit, Alternatives](https://www.postpeer.dev/blog/best-tiktok-posting-api) | Bên thứ ba thực chất là "thuê" client đã audit sẵn |
| [netrows.com — Best TikTok Data APIs 2026](https://www.netrows.com/blog/best-tiktok-data-apis-2026) | **Research API siết còn tổ chức học thuật**; thương mại phải chuyển sang endpoint khác |
| [admapix.com — Creative Center guide](https://www.admapix.com/blog/ad-intelligence/tiktok-creative-center-tutorial) | Creative Center công khai một phần nhưng **ToS cấm harvest tự động** |

**Hệ quả:** trend agent **không đụng TikTok**. Lấy trend từ nguồn AI công khai.

## Vòng lặp QC / multi-agent — reported

| Nguồn | Rút ra gì |
|---|---|
| [Building a Critic-Agent Loop (Towards AI, 2026-07)](https://pub.towardsai.net/building-a-critic-agent-loop-scores-refinement-and-guardrails-9e0ceaf69da4) | Critic **đề xuất, không quyết định**; chặn 2–3 vòng; "ground the critic, cap the loop, surface the trail" |
| [LLM-as-Judge in Production (Zylos, 2026-04)](https://zylos.ai/research/2026-04-10-llm-as-judge-production-agent-verification-2026/) | CRITIC (ICLR 2024): self-correct đáng tin **khi có tín hiệu ngoài** (test runner), không phải tự chấm → **T1 phải là code, không LLM** |
| [Multi-Agent Orchestration Patterns 2026](https://www.digitalapplied.com/blog/multi-agent-orchestration-patterns-producer-consumer) | Generator–Critic–Reviewer; **thiếu điều kiện dừng là nguồn đốt token lớn nhất** trong hệ multi-agent production |
| [MAR: Multi-Agent Reflexion (arXiv 2512.20845)](https://arxiv.org/html/2512.20845) | Nhiều critic với góc nhìn **khác nhau** cho reflection giàu hơn một critic tự soi → cơ sở cho 4 tầng T1–T4 |
| [Judging with Many Minds (arXiv 2505.19477)](https://arxiv.org/pdf/2505.19477) | Cảnh báo ngược: nhiều judge có thể **khuếch đại thiên lệch**, không phải cứ thêm là tốt |
| [Self-Improving AI Agents: The Reflection Loop (Taskade, 2026)](https://www.taskade.com/blog/self-improving-ai-agents-reflection) | Tách Producer/Critic loại bỏ thiên lệch có cấu trúc; critic cần prompt **"tìm cái sai"**, không phải "làm lại" |

## Chưa kiểm — việc phải làm

- [ ] Đọc `LICENSE` gốc của Remotion, ghi chính xác điều kiện thương mại → `repo-cards/remotion.md`
- [ ] Chạy `.claude/skills/repo-audit/scripts/repo-health.sh` cho 4 repo sắp phụ thuộc
- [ ] Xác minh model card VieNeu-TTS-v2 còn sống + có timestamp không
- [ ] Đọc code MoneyPrinterTurbo xem nó tách pipeline thế nào (chỉ học kiến trúc, không copy)
- [ ] Kiểm điều kiện đăng ký TikTok developer app: có cần Business account không
