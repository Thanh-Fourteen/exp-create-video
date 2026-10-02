# Bộ đối chứng T4 (fact-checker) — 2026-10-02

4 script **sạch** (`*.clean.json`) — mọi claim đã đối chiếu tay với snapshot nguồn ở
`team/snapshots/` ngày 2026-10-02 — và 4 bản **gài** (`*.bad.json`), mỗi bản thay 5 câu bằng
claim SAI mà nguồn mâu thuẫn trực tiếp. `seeded` = chỉ số câu bị gài. Tổng 20 claim sai:
10 số · 3 ngày · 3 license · 1 tổ chức · 3 mệnh đề chữ.

| Script | Nguồn |
|---|---|
| `a-sdxl-lightning` | HF ByteDance/SDXL-Lightning · arXiv 2402.13929 · `research/probes/p3s3-sdxl.md` |
| `b-whisper-paper` | arXiv 2212.04356 · github openai/whisper |
| `c-qwen3-vl` | HF Qwen/Qwen3-VL-2B-Instruct |
| `d-whisper-models` | github openai/whisper (bảng model trong README) |

Chạy: `.venv/bin/python out/p4-s3-t4/run_probe.py 2` · tiêu chí ở
`research/probes/p4-s3-research.md` §4.

⚠️ Không sửa fixture để "cho nó pass". Nguồn đổi (README cập nhật) thì snapshot cũ vẫn nằm
theo sha256 — ghi rõ nếu phải tải lại.
