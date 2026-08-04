# Repo layout and file templates

## The tree the script creates

```
<project>/
├── CLAUDE.md               ← Claude writes: metric, constraints, skill table (<40 lines)
├── README.md               ← Claude writes: what/setup/run/status
├── .gitignore              ← script writes
├── .claude/
│   ├── settings.json       ← copied
│   ├── rules/              ← Claude writes: project rules, optionally path-scoped
│   ├── skills/             ← copied — research toolkit travels with the repo
│   └── agents/             ← copied
├── research/               ← copied verbatim — source of truth for every decision
├── data/{raw,interim,external}/   gitignored; manifests tracked, bytes never
├── eval/
│   ├── data/               gitignored
│   ├── dataset.md          ← Claude writes: stratification table + counts
│   ├── thresholds.md       ← Claude writes: pass/investigate/fail, BEFORE any run
│   └── results/            one dated file per bake-off, never overwritten
├── src/<pkg>/{io,models,pipeline}/  + metrics.py (seeded, runnable)
├── configs/                ← Claude writes: candidates.yaml
├── scripts/                runners
├── notebooks/              exploration only — nothing importable lives here
└── tests/                  test_metrics.py seeded
```

Why this shape: `research/` and `eval/` are the durable assets. Models get replaced every few months; the decision log and the frozen eval set are what survive and what make the next decision cheap.

## `CLAUDE.md` template

```markdown
# <project>

<one line: what this system does, for whom>

## Ngôn ngữ
Trả lời bằng tiếng Việt. Giữ nguyên thuật ngữ kỹ thuật tiếng Anh.

## Mục tiêu bằng số
Primary: **<metric> ≥ <target>** trên `eval/` · Secondary: <latency, $/1k, % review>
Ngưỡng đầy đủ: `eval/thresholds.md` · Cơ sở quyết định: `research/05-decision.md`

## Ràng buộc cứng
- <on-prem / license class / volume / latency>

## Skill
| Cần gì | Dùng |
|---|---|
| Nghiên cứu chủ đề mới | `/research-topic <chủ đề>` |
| Bối cảnh OCR 2026 | `/ocr-landscape` |
| Đánh giá 1 paper/model | `/paper-triage <url>` |
| Thiết kế eval / bake-off | `/bench-plan` |

## Nguyên tắc
- Không tune trên 20% held-out của `eval/`.
- Kết quả ghi vào `eval/results/<YYYY-MM-DD>-<tên>.md`, **không ghi đè** file cũ.
- Mọi con số kèm ngày và nguồn.
- Tiếng Việt: luôn báo cáo CER có dấu **và** CER bỏ dấu.

## Nơi lưu
`research/` quyết định · `eval/` bộ đo · `src/<pkg>/` code · `configs/` cấu hình chạy
```

Keep it under 40 lines. It loads every session — every line is a recurring cost. Long-form material belongs in `.claude/rules/` (path-scoped, loads on demand) or a skill reference.

## `.claude/rules/eval-discipline.md` template

No `paths:` — this one applies session-wide.

```markdown
# Kỷ luật đánh giá

- Ngưỡng viết TRƯỚC khi chạy. Sửa ngưỡng sau khi thấy kết quả = không còn là ngưỡng.
- 20% held-out của `eval/` không được nhìn tới cho đến lúc chốt quyết định.
- Mọi lần chạy lưu **output thô** ra đĩa, không chỉ số tổng hợp — sẽ cần chấm lại bằng metric khác.
- Cố định và ghi log: preprocessing, DPI, prompt, decoding params, seed.
- Mỗi bake-off có một **baseline tầm thường** và một **trần chất lượng**. Không có hai mốc này thì con số không đọc được.
- Đổi preprocessing → chạy lại toàn bộ. Preprocessing dịch chuyển điểm nhiều hơn đổi model, thường xuyên hơn người ta tưởng.
- Hai ứng viên chênh nhau trong nhiễu → chọn theo license, chi phí, failure mode. Không chọn theo điểm.
```

## Path-scoped rule example

```markdown
---
paths:
  - "src/**/metrics.py"
  - "eval/**"
---

# Quy tắc metric
- NFC-normalise cả reference lẫn hypothesis trước mọi phép đo.
- Tiếng Việt: `cer` và `cer_stripped` luôn đi cặp. Chênh lệch = diacritic error rate.
- Tổng hợp corpus phải length-weighted, không lấy trung bình per-sample.
- CER mù với layout — không chốt gì chỉ bằng CER.
```

## `configs/candidates.yaml` template

```yaml
# Shortlist from research/05-decision.md — one entry per candidate in the bake-off.
candidates:
  - name: <id>
    role: ceiling | self-host | cost-floor | structure-specialist
    kind: api | local
    model: <model id or path>
    license: <weights license>
    params: <e.g. 0.9B>
    grounding: true | false        # emits bounding boxes?
    notes: <why it is on the list>
    # api: endpoint, or local: dtype/device/max_tokens
```

`role` matters more than `name`: every bake-off needs a ceiling and a floor, otherwise the middle numbers mean nothing.

## What NOT to scaffold

License file, CI, Dockerfile, pre-commit, docs site. Each is a decision with consequences, and an unrequested one is a decision made for the user. Add them when asked.
