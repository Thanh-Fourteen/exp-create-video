"""QC tầng 3 — sức hút của KỊCH BẢN: hook, nhịp, tiếng Việt, CTA.

    python -m create_video.qc.t3_appeal out/<id>/script.json [--spec out/<id>/video-spec.json]

Tầng **đề xuất, không chặn** (`configs/thresholds.yaml: t3_appeal`). Fail → danh sách lỗi
cụ thể gửi về scriptwriter (`revision_notes` → `scriptwriter.revise_script`), không bao
giờ "viết lại cho hay hơn".

Cách chấm — `research/probes/p4-s2-research.md`. LLM chấm "hay/sáng tạo" tương quan ~0
với chuyên gia và ưu ái output của chính nó (research/10 §5), nên T3 là **checklist nhị
phân**, mỗi mục một câu hỏi đạt/trượt:

- Mục nào đo được bằng code (câu mở đầu chào hỏi, dấu hiệu dịch máy, thuật ngữ bị dịch,
  CTA xin like, độ dài câu đều tăm tắp…) thì **code** chấm — tất định, không ảo.
- Mục chủ quan (3 giây đầu có thông tin không, câu nào lủng củng…) do **critic** chấm:
  một lần `run_role` context MỚI, prompt "tìm cái sai", mặc định ĐẠT. Trượt thì PHẢI
  trích nguyên văn câu gây lỗi; trích không có trong script → code bỏ lời chê đó
  (`dropped`) — đây là chốt chặn "chê lấy lệ".
- Điểm mỗi nhóm = 10 × tỉ lệ mục đạt; hook có mục "chết ngay" (rubric: "bắt được là
  fail ngay") → trượt một mục hook là hook ≤ 3. `total` = trọng số trong thresholds.yaml.
  Điểm do CODE tính từ các mục, critic không bao giờ tự cho điểm.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Sequence

import yaml
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..agents.scriptwriter import Script
    from ..team import State

REPO_ROOT = Path(__file__).resolve().parents[3]

# ── Ngưỡng viết TRƯỚC khi chạy (p4-s2-research.md §3, 2026-10-02) ───────────
# min_total_score / min_hook_score / weights nằm ở thresholds.yaml từ 2026-08-04.
HOOK_WINDOW_SEC = 3.0      # "vào việc trong 3 giây" — rubric §1
HOOK_FAIL_SCORE = 3        # trượt một mục hook = "fail ngay", dưới hẳn min_hook_score 8
MIN_LENGTH_RANGE = 4       # câu dài nhất − ngắn nhất (từ) trong thân bài; dưới = đều tăm tắp
WORDS_PER_SEC = 2.1        # không có spec thì ước 3 giây đầu = 6 từ đầu (đo p3b-s5: ~2,1 từ/s)

# ── Mục checklist ─────────────────────────────────────────────────────────────
# id → (nhóm, ai chấm, câu hỏi). "Đạt" = câu trả lời mong muốn.
ITEMS: dict[str, tuple[str, str, str]] = {
    # hook — cả hai mục đều "chết ngay"
    "H_OPENER": ("hook", "code", "Câu đầu KHÔNG mở bằng chào hỏi / bối cảnh chung / định nghĩa / hứa hẹn chung chung"),
    "H_INFO": ("hook", "llm", "Lời đọc trong 3 giây đầu đã mang thông tin cụ thể: con số, tên riêng, "
                              "điều trái với niềm tin phổ biến, câu hỏi người xem đang thắc mắc, hoặc kết quả"),
    # nhịp
    "P_VARIETY": ("pacing", "code", f"Độ dài câu thân bài xen kẽ (dài nhất − ngắn nhất ≥ {MIN_LENGTH_RANGE} từ)"),
    "P_FILLER": ("pacing", "code", "Không có câu mở bằng từ chuyển tiếp thừa (vậy thì, tiếp theo, như vậy là…)"),
    "P_LIST": ("pacing", "code", "Không liệt kê khô kiểu thứ nhất / thứ hai / thứ ba"),
    "P_STALL": ("pacing", "llm", "Không có ý nào kéo quá ba câu liền mà không thêm thông tin mới"),
    "P_TURN": ("pacing", "llm", "Có ít nhất một chỗ ngoặt / thông tin bất ngờ ở GIỮA video, không dồn hết vào cuối"),
    # tiếng Việt
    "V_MARKERS": ("vietnamese_quality", "code", "Không có dấu hiệu dịch máy (bị động 'được… bởi', "
                                                "'điều này có nghĩa là', 'một cách' + tính từ, 'việc' + động từ)"),
    "V_TERMS": ("vietnamese_quality", "code", "Thuật ngữ giữ tiếng Anh (model, fine-tune, inference, prompt, "
                                              "benchmark, open-source), không dịch"),
    "V_NATURAL": ("vietnamese_quality", "llm", "Mọi câu đọc to nghe như người Việt nói — không câu nào lủng "
                                               "củng hay mang cấu trúc dịch từ tiếng Anh"),
    "V_ADDRESS": ("vietnamese_quality", "llm", "Xưng hô nhất quán cả video (không lẫn tôi/mình/chúng ta cho cùng người nói)"),
    # CTA
    "C_GENERIC": ("cta", "code", "CTA không xin like / follow / subscribe / thả tim chung chung"),
    "C_SAVE_SHARE": ("cta", "code", "CTA xin LƯU hoặc CHIA SẺ (TikTok 2026 ưu tiên save/share hơn like)"),
    "C_SPECIFIC": ("cta", "llm", "CTA là MỘT hành động cụ thể gắn với nội dung vừa xem"),
    # chống AI slop — CHỈ GHI VẾT, không vào điểm (xem `WARN_ONLY`)
    "A_FIRSTHAND": ("authenticity", "code", "Có ít nhất một câu quan sát TRỰC TIẾP ngôi thứ nhất (tôi chạy thử, tôi đo…)"),
    "A_PROBE_SOURCE": ("authenticity", "code", "Có nguồn trỏ vào research/probes/ (số đo của chính kênh)"),
}
LLM_ITEMS = [k for k, v in ITEMS.items() if v[1] == "llm"]
KILL_ITEMS = {"H_OPENER", "H_INFO"}
# Ghi vết, KHÔNG vào điểm: scriptwriter chưa được cấp số đo trong research/probes/ (brief
# có nguồn là P5.S3). Kéo verdict vì điều producer không làm được = vòng sửa vô ích.
WARN_ONLY = {"A_FIRSTHAND", "A_PROBE_SOURCE"}
GROUPS = ("hook", "pacing", "vietnamese_quality", "cta")

# ── Regex của các mục code ────────────────────────────────────────────────────
# Mở đầu hỏng — rubric §1. So trên câu đầu đã bỏ dấu câu, chữ thường.
_OPENER = re.compile(
    r"^(xin chào|chào (các|mọi|cả)|hello|hi |hế lô|"
    r"hôm nay (chúng ta|mình|tôi|ta|chúng mình)|"
    r"(trong|ở) (thời đại|kỷ nguyên|bối cảnh)|ngày nay|thời gian gần đây|như (các bạn|mọi người|chúng ta) đã biết|"
    r"video (này|hôm nay)|trong video (này|hôm nay)|chắc hẳn|bạn có bao giờ nghe)"
)
_DEFINITION = re.compile(r"^[\w\s-]{1,30}? (là viết tắt của|là gì|được định nghĩa là)")
_FILLER = re.compile(r"^(vậy thì|vậy nên|như vậy là|như vậy|tiếp theo|sau đây|bây giờ chúng ta|"
                     r"tiếp đến|cuối cùng là|nói tóm lại|tóm lại)\b")
_LIST = re.compile(r"\bthứ (nhất|hai|ba|tư)\b")
# Dịch máy — bảng "dấu hiệu dịch máy" ở rubric §3.
_MARKERS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bđược [^.,;!?]{1,40}? bởi\b"), "bị động kiểu Anh 'được … bởi'", "đưa chủ thể lên đầu: 'Bên X làm …'"),
    (re.compile(r"\bđiều (này|đó) có nghĩa là\b"), "'điều này có nghĩa là'", "'nghĩa là …' hoặc bỏ hẳn"),
    (re.compile(r"\bmột cách \w+"), "'một cách' + tính từ", "bỏ 'một cách', giữ tính từ"),
    (re.compile(r"(?:^|[.,;:!?] *)việc \w+|\b(?:là|cho|của|về|với|trong) việc \w+"), "'việc' + động từ",
     "dùng thẳng động từ: 'dùng model này' thay 'việc sử dụng model này'"),
]
_TRANSLATED_TERMS = {
    "mô hình ngôn ngữ lớn": "LLM", "tinh chỉnh": "fine-tune", "suy luận": "inference",
    "lời nhắc": "prompt", "câu lệnh nhắc": "prompt", "điểm chuẩn": "benchmark",
    "bộ đánh giá chuẩn": "benchmark", "mã nguồn mở": "open-source", "trọng số mở": "open-weight",
}
_GENERIC_CTA = re.compile(r"\b(like|follow|subscribe|sub|thả tim|đăng ký kênh|nhấn theo dõi|bấm theo dõi|theo dõi kênh)\b")
_SAVE_SHARE = re.compile(r"\b(lưu|save|chia sẻ|share|gửi (video|clip|cái) này|gửi cho|tag)\b")
_FIRSTHAND = re.compile(r"\b(tôi|mình|chúng tôi)\b[^.!?]{0,30}?\b(chạy|đo|thử|test|cắm|bật|nạp|dựng|"
                        r"benchmark|ghi được|thấy|gặp)\b")


def _norm(s: str) -> str:
    """Chữ thường, NFC, bỏ dấu câu (giữ chữ có dấu tiếng Việt, số, gạch nối)."""
    s = unicodedata.normalize("NFC", s).lower()
    return " ".join(re.sub(r"[^\w\s-]", " ", s).split())


def _thresholds() -> dict:
    with open(REPO_ROOT / "configs" / "thresholds.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["t3_appeal"]


# ── Kết quả ──────────────────────────────────────────────────────────────────
@dataclass
class ItemResult:
    id: str
    group: str
    by: str                      # code | llm
    passed: bool
    line: int | None = None      # chỉ số câu (0 = hook) — `where` của issue
    quote: str = ""
    why: str = ""
    fix: str = ""
    # Các chỗ trúng KHÁC của cùng mục: điểm tính mục một lần, nhưng scriptwriter phải
    # được chỉ MỌI chỗ — probe 2026-10-02 bỏ sót "một cách" vì chỉ báo lần trúng đầu.
    more: list[dict] = field(default_factory=list)   # [{line, quote, why, fix}]


@dataclass
class T3Report:
    score: float                               # = total, khớp format `{score, issues[]}` ở todos
    verdict: str                               # pass | revise
    groups: dict[str, float]                   # điểm 0–10 từng nhóm
    issues: list[dict]                         # [{where, item, by, why, suggested_fix, quote}]
    items: list[ItemResult]
    warnings: list[dict] = field(default_factory=list)   # WARN_ONLY trượt — ghi vết
    dropped: list[dict] = field(default_factory=list)    # lời chê của critic bị bỏ (trích sai)
    hook_3s: str = ""                          # lời đọc trong 3 giây đầu — thứ H_INFO đã chấm
    hook_type: str = ""
    llm: dict = field(default_factory=dict)    # token/thời gian lần gọi critic

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


# ── Chấm bằng code ───────────────────────────────────────────────────────────
def hook_window_text(script: "Script", spec: dict | None = None, window: float = HOOK_WINDOW_SEC) -> str:
    """Lời đọc trong `window` giây đầu: lấy mốc từ phụ đề karaoke của spec nếu có (đo được),
    không thì ước bằng số từ × `WORDS_PER_SEC`."""
    if spec:
        words = [w["w"] for c in spec.get("captions", []) for w in c.get("words", [])
                 if w.get("start", 1e9) < window]
        if words:
            return " ".join(words)
    n = max(1, int(window * WORDS_PER_SEC))
    return " ".join(script.hook.split()[:n])


def code_items(script: "Script") -> list[ItemResult]:
    lines = script.lines
    body = list(enumerate(lines))[1:-1] if len(lines) > 2 else []
    out: list[ItemResult] = []

    def add(iid: str, passed: bool, line: int | None = None, quote: str = "", why: str = "", fix: str = "",
            more: list[dict] | None = None):
        g, by, _ = ITEMS[iid]
        out.append(ItemResult(iid, g, by, passed, line, quote, why, fix, more or []))

    def add_hits(iid: str, hits: list[tuple[int, str, str, str]]):
        """hits = [(câu, trích, lý do, hướng sửa)] — rỗng là đạt."""
        if not hits:
            add(iid, True)
            return
        (i, t, why, fix), rest = hits[0], hits[1:]
        add(iid, False, i, t, why, fix, [{"line": a, "quote": b, "why": c, "fix": d} for a, b, c, d in rest])

    # H_OPENER
    h = _norm(script.hook)
    if _OPENER.match(h) or _DEFINITION.match(h):
        add("H_OPENER", False, 0, script.hook, "mở bằng chào hỏi / bối cảnh / định nghĩa — người xem lướt trong 3 giây",
            "mở thẳng bằng con số, điều trái niềm tin, câu hỏi thật hoặc kết quả")
    else:
        add("H_OPENER", True)

    # P_VARIETY
    lens = [len(t.split()) for _, t in body]
    if len(lens) >= 3 and max(lens) - min(lens) < MIN_LENGTH_RANGE:
        add("P_VARIETY", False, None, "", f"câu thân bài dài {min(lens)}–{max(lens)} từ, đều tăm tắp — nghe như đọc bài",
            "xen một câu thật ngắn hoặc một câu dài hơn hẳn")
    else:
        add("P_VARIETY", True)

    # P_FILLER
    add_hits("P_FILLER", [(i, t, "câu mở bằng từ chuyển tiếp thừa — ăn thời gian, không mang tin",
                           "bỏ từ chuyển tiếp, vào thẳng ý")
                          for i, t in enumerate(lines) if _FILLER.match(_norm(t))])

    # P_LIST
    hits = [(i, t) for i, t in enumerate(lines) if _LIST.search(_norm(t))]
    if len(hits) >= 2:
        add("P_LIST", False, hits[0][0], hits[0][1], "liệt kê thứ nhất/thứ hai… không điểm nhấn",
            "giữ ý mạnh nhất, nói nó như một phát hiện thay vì đánh số")
    else:
        add("P_LIST", True)

    # V_MARKERS
    add_hits("V_MARKERS", [(i, t, f"dấu hiệu dịch máy: {why}", fix)
                           for i, t in enumerate(lines)
                           for rx, why, fix in _MARKERS if rx.search(unicodedata.normalize("NFC", t).lower())])

    # V_TERMS
    add_hits("V_TERMS", [(i, t, f"thuật ngữ bị dịch: '{vi}'", f"giữ nguyên '{en}'")
                         for i, t in enumerate(lines) for vi, en in _TRANSLATED_TERMS.items() if vi in _norm(t)])

    # CTA
    cta_i = len(lines) - 1
    c = _norm(script.cta)
    if _GENERIC_CTA.search(c):
        add("C_GENERIC", False, cta_i, script.cta, "xin like/follow chung chung — ai cũng nói, không ai làm",
            "xin một hành động gắn với nội dung vừa xem")
    else:
        add("C_GENERIC", True)
    if _SAVE_SHARE.search(c):
        add("C_SAVE_SHARE", True)
    else:
        add("C_SAVE_SHARE", False, cta_i, script.cta, "CTA không xin lưu hoặc chia sẻ — TikTok 2026 ưu tiên save/share",
            "thêm lý do để LƯU video (sẽ cần lại) hoặc CHIA SẺ (gửi cho ai đang gặp đúng vấn đề này)")

    # Chống AI slop — ghi vết
    fh = [(i, t) for i, t in enumerate(lines) if _FIRSTHAND.search(_norm(t))]
    add("A_FIRSTHAND", bool(fh), *((fh[0][0], fh[0][1]) if fh else (None, "")),
        *(("", "") if fh else ("không câu nào là quan sát trực tiếp — dễ lẫn vào AI slop",
                               "thêm một câu 'tôi chạy thử / tôi đo được' lấy số từ research/probes/")))
    has_probe = any("research/probes/" in str(s.get("url", "")) for s in script.sources)
    add("A_PROBE_SOURCE", has_probe, None, "",
        *(("", "") if has_probe else ("không nguồn nào trỏ vào research/probes/", "trích số đo của kênh kèm file probe")))
    return out


# ── Critic (LLM) ─────────────────────────────────────────────────────────────
class CriticItem(BaseModel):
    id: Literal["H_INFO", "P_STALL", "P_TURN", "V_NATURAL", "V_ADDRESS", "C_SPECIFIC"]
    passed: bool
    quote: str = ""      # trượt → NGUYÊN VĂN một đoạn trong lời đọc
    why: str = ""        # một câu
    fix: str = ""        # hướng sửa, một câu — KHÔNG viết lại câu


class CriticOut(BaseModel):
    hook_type: Literal["con_so", "mau_thuan", "cau_hoi", "ket_qua_truoc", "khong_co"]
    items: list[CriticItem]


def _rubric() -> str:
    return (REPO_ROOT / "configs" / "rubric.md").read_text(encoding="utf-8")


def critic_system_prompt() -> str:
    qs = "\n".join(f"- {k}: {ITEMS[k][2]}" for k in LLM_ITEMS)
    return f"""Bạn là CRITIC của một kênh TikTok tiếng Việt về AI. Việc của bạn là TÌM CÁI SAI
trong kịch bản theo một checklist cố định. Bạn KHÔNG viết lại kịch bản, KHÔNG chấm điểm,
KHÔNG khen, KHÔNG chấm nội dung đúng/sai (đó là việc của fact-checker).

Rubric của kênh (tham khảo tiêu chí, phần JSON trong rubric KHÔNG phải output của bạn):

{_rubric()}

CHECKLIST — trả lời đúng {len(LLM_ITEMS)} mục, mỗi mục passed true/false:

{qs}

LUẬT CHẤM — đọc kỹ:
1. Mặc định là ĐẠT (passed=true). Chỉ đánh TRƯỢT khi chỉ ra được một chỗ cụ thể mà một
   biên tập viên TikTok người Việt sẽ đồng ý ngay là lỗi. Không chắc → ĐẠT.
2. Trượt thì `quote` PHẢI là đoạn chép NGUYÊN VĂN từ lời đọc (không sửa chữ, không tóm tắt)
   — code sẽ đối chiếu, trích không khớp thì lời chê bị bỏ. `why` một câu, `fix` một câu
   chỉ hướng sửa, KHÔNG viết sẵn câu thay thế.
3. Đạt thì để quote/why/fix rỗng.
4. Không chê vì gu: câu ngắn, giọng thân mật, dùng thuật ngữ tiếng Anh (model, VRAM, OOM…)
   là CHUẨN của kênh, không phải lỗi. Số được viết bằng chữ ("tám phẩy hai giây") là ràng
   buộc kỹ thuật của giọng đọc, không phải lỗi.
5. H_INFO chỉ xét phần lời trong 3 giây đầu được đưa riêng ở dưới. `hook_type`: kiểu hook
   của câu đầu (con_so | mau_thuan | cau_hoi | ket_qua_truoc), hoặc khong_co nếu không thuộc kiểu nào."""


def critic_prompt(script: "Script", hook_3s: str) -> str:
    lines = "\n".join(f"[{i}] {t}" for i, t in enumerate(script.lines))
    return (f"Chủ đề: {script.topic}\n\nLỜI ĐỌC (câu [0] là hook, câu cuối là CTA):\n{lines}\n\n"
            f"LỜI ĐỌC TRONG 3 GIÂY ĐẦU (cho H_INFO): \"{hook_3s}\"\n\nChấm checklist.")


def _locate(quote: str, lines: Sequence[str]) -> int | None:
    """Câu chứa `quote` (so sau chuẩn hoá). None = trích không có trong script."""
    q = _norm(quote)
    if not q:
        return None
    for i, t in enumerate(lines):
        if q in _norm(t):
            return i
    return None


def apply_critic(out: CriticOut, script: "Script") -> tuple[list[ItemResult], list[dict]]:
    """Lời chê của critic → ItemResult. Trượt mà trích không khớp → coi là ĐẠT, ghi `dropped`.
    Mục critic bỏ sót → coi là ĐẠT (mặc định đạt, đúng luật 1 trong prompt)."""
    got = {it.id: it for it in out.items}
    res: list[ItemResult] = []
    dropped: list[dict] = []
    for iid in LLM_ITEMS:
        g = ITEMS[iid][0]
        it = got.get(iid)
        if it is None or it.passed:
            res.append(ItemResult(iid, g, "llm", True))
            continue
        line = _locate(it.quote, script.lines)
        if line is None:
            dropped.append({"item": iid, "quote": it.quote, "why": it.why, "reason": "trích không có trong lời đọc"})
            res.append(ItemResult(iid, g, "llm", True))
            continue
        res.append(ItemResult(iid, g, "llm", False, line, it.quote, it.why, it.fix))
    return res, dropped


# ── Gộp điểm ─────────────────────────────────────────────────────────────────
def score(items: Sequence[ItemResult], thr: dict | None = None) -> tuple[dict[str, float], float, str]:
    thr = thr or _thresholds()
    groups: dict[str, float] = {}
    for g in GROUPS:
        its = [i for i in items if i.group == g]
        s = 10.0 * sum(i.passed for i in its) / len(its) if its else 10.0
        if g == "hook" and any(not i.passed and i.id in KILL_ITEMS for i in its):
            s = min(s, HOOK_FAIL_SCORE)
        groups[g] = round(s, 2)
    w = thr["weights"]
    total = round(sum(w[g] * groups[g] for g in GROUPS), 2)
    ok = total >= thr["min_total_score"] and groups["hook"] >= thr["min_hook_score"]
    return groups, total, "pass" if ok else "revise"


def _where(line: int | None, n_lines: int) -> str:
    if line is None:
        return "toàn bài"
    if line == 0:
        return "hook (câu 0)"
    if line == n_lines - 1:
        return f"CTA (câu {line})"
    return f"câu {line}"


def build_report(script: "Script", items: list[ItemResult], *, hook_3s: str = "", hook_type: str = "",
                 dropped: list[dict] | None = None, llm: dict | None = None) -> T3Report:
    groups, total, verdict = score([i for i in items if i.id not in WARN_ONLY])
    n = len(script.lines)

    def issues(i: ItemResult) -> list[dict]:
        hits = [{"line": i.line, "quote": i.quote, "why": i.why, "fix": i.fix}, *i.more]
        return [{"where": _where(h["line"], n), "line": h["line"], "item": i.id, "by": i.by,
                 "quote": h["quote"], "why": h["why"], "suggested_fix": h["fix"]} for h in hits]

    return T3Report(
        score=total, verdict=verdict, groups=groups,
        issues=[x for i in items if not i.passed and i.id not in WARN_ONLY for x in issues(i)],
        items=items,
        warnings=[x for i in items if not i.passed and i.id in WARN_ONLY for x in issues(i)],
        dropped=dropped or [], hook_3s=hook_3s, hook_type=hook_type, llm=llm or {},
    )


async def acheck(script: "Script", *, spec: dict | None = None, state: "State | None" = None,
                 model: str | None = None, artifact: Path | None = None, _query=None) -> T3Report:
    """Chấm một script: code + một lần critic. Không bao giờ sửa script."""
    from ..team import arun_role

    hook_3s = hook_window_text(script, spec)
    items = code_items(script)
    n0 = len(state.llm_calls) if state is not None else 0
    out = await arun_role(
        "critic_t3", critic_prompt(script, hook_3s), CriticOut,
        system_prompt=critic_system_prompt(), tools=[], max_turns=4, max_budget_usd=1.0,
        model=model, state=state, _query=_query,
    )
    llm_items, dropped = apply_critic(out, script)
    llm = state.llm_calls[-1] if state is not None and len(state.llm_calls) > n0 else {}
    llm = {k: llm.get(k) for k in ("wall_sec", "input_tokens", "output_tokens", "cost_usd", "models") if k in llm}
    order = list(ITEMS)
    items = sorted(items + llm_items, key=lambda i: order.index(i.id))
    rep = build_report(script, items, hook_3s=hook_3s, hook_type=out.hook_type, dropped=dropped, llm=llm)
    if artifact is not None:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(rep.to_json() + "\n", encoding="utf-8")
    return rep


def check(script: "Script", **kw) -> T3Report:
    import asyncio

    return asyncio.run(acheck(script, **kw))


def revision_notes(rep: T3Report) -> list[str]:
    """Patch gửi scriptwriter: mỗi lỗi một dòng, CÓ chỗ + lý do + hướng sửa. Rỗng nếu pass.

    Chỉ gửi lỗi cụ thể — "tự sửa không có tín hiệu ngoài làm tệ đi" (research/10 §5).
    """
    if rep.verdict == "pass":
        return []
    out = []
    for i in rep.issues:
        q = f" «{i['quote']}»" if i["quote"] else ""
        out.append(f"[{i['item']}] {i['where']}{q}: {i['why']} → hướng sửa: {i['suggested_fix']}")
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    from ..agents.scriptwriter import Script
    from ..team import State

    ap = argparse.ArgumentParser(description="QC tầng 3 — chấm sức hút script.json")
    ap.add_argument("script", type=Path)
    ap.add_argument("--spec", type=Path, help="video-spec.json để lấy mốc 3 giây đầu thật")
    ap.add_argument("--out", type=Path, help="mặc định <thư mục script>/qc/t3.json")
    ap.add_argument("--state-dir", type=Path, help="nơi ghi state.json (mặc định thư mục script)")
    ap.add_argument("--model", default=None)
    a = ap.parse_args(argv)

    script = Script.from_dict(json.loads(a.script.read_text(encoding="utf-8")))
    spec_p = a.spec or a.script.parent / "video-spec.json"
    spec = json.loads(spec_p.read_text(encoding="utf-8")) if spec_p.exists() else None
    state = State.load(a.state_dir or a.script.parent)
    out = a.out or a.script.parent / "qc" / "t3.json"
    rep = check(script, spec=spec, state=state, model=a.model, artifact=out)

    print(f"T3 {rep.verdict.upper()}  total={rep.score}  " + "  ".join(f"{g}={s}" for g, s in rep.groups.items()))
    print(f"  3s đầu: {rep.hook_3s!r} · hook_type={rep.hook_type}")
    for i in rep.issues:
        print(f"  ✗ [{i['item']}/{i['by']}] {i['where']}: {i['why']}")
    for w in rep.warnings:
        print(f"  ! [{w['item']}] {w['why']}")
    for d in rep.dropped:
        print(f"  ~ bỏ lời chê [{d['item']}] {d['quote']!r}: {d['reason']}")
    print(f"  → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
