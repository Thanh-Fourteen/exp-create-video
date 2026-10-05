"""QC tầng 4 — độ chính xác sự thật (vai **fact-checker**). CHẶN CỨNG.

    python -m create_video.qc.t4_facts out/<id>/script.json

Thiết kế — `research/probes/p4-s3-research.md`. Kiểu VeriScore nhưng giữ 3 nhãn, vì việc
của T4 chính là tách **sai** khỏi **chưa kiểm được** (todos P4.S3, Bẫy):

1. **Nguồn trước, LLM sau.** Code tải `script.sources[].url` + url screenshot vào
   `team/snapshots/` (`team/snapshot.py`: HF/arXiv/GitHub API, `research/probes/`). LLM
   không có tool nào — nó chỉ đọc đúng thứ đã lưu, không trí nhớ, không duyệt web.
2. **Hai vai, hai context:** `claim_extractor` rút claim kiểm chứng được từ lời đọc mà
   KHÔNG thấy nguồn (khỏi chỉ rút cái mình kiểm được) → `fact_checker` phán từng claim
   supported / contradicted / inconclusive kèm trích NGUYÊN VĂN nguồn.
3. **Code là cổng:** trích không có trong snapshot → inconclusive. Claim số và ngày thì
   **code so** giá trị (tolerance / độ mịn của claim) — verifier LLM hay sai suy luận số.
   `contradicted ≥ 1` → block. `inconclusive` chỉ gắn cờ cho Tony.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import yaml
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..agents.scriptwriter import Script
    from ..team import State

REPO_ROOT = Path(__file__).resolve().parents[3]

# Ngưỡng viết trước khi chạy (p4-s3-research.md §3, 2026-10-02).
NUM_REL_TOL = 0.02          # 2% của giá trị nguồn
MAX_SOURCE_CHARS = 20_000   # mỗi snapshot đưa vào prompt; README dài chỉ cần phần đầu

ClaimType = Literal["model_name", "benchmark_number", "number", "release_date", "date",
                    "org_name", "license", "other"]


def _thresholds() -> dict:
    with open(REPO_ROOT / "configs" / "thresholds.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["t4_facts"]


# ── Schema hai vai ───────────────────────────────────────────────────────────
class ExtractedClaim(BaseModel):
    line: int                 # chỉ số câu (0 = hook)
    claim: str                # mệnh đề tự đứng được, tiếng Việt, đúng ý câu nói
    type: ClaimType


class ExtractOut(BaseModel):
    claims: list[ExtractedClaim]


class Verdict(BaseModel):
    claim_id: int
    verdict: Literal["supported", "contradicted", "inconclusive"]
    source_id: str = ""       # "S1"… — snapshot chứa quote
    quote: str = ""           # NGUYÊN VĂN từ snapshot
    reason: str = ""          # một câu
    kind: Literal["number", "date", "text"] = "text"
    claim_value: float | None = None    # số trong claim, ĐÃ đổi về đơn vị của nguồn
    source_value: float | None = None   # số trong quote
    unit: str = ""
    claim_date: str = ""      # đúng độ mịn claim nói: "2024", "2024-02", "2024-02-21"
    source_date: str = ""     # ngày trong quote, dạng ISO


class CheckOut(BaseModel):
    verdicts: list[Verdict]


# ── Kết quả ──────────────────────────────────────────────────────────────────
@dataclass
class ClaimResult:
    id: int
    line: int
    claim: str
    type: str
    verdict: str              # supported | contradicted | inconclusive — SAU cổng code
    llm_verdict: str
    source_url: str = ""
    quote: str = ""
    reason: str = ""
    gate: str = ""            # code đã đổi gì và vì sao ("" = giữ nguyên lời LLM)


@dataclass
class T4Report:
    verdict: str                              # pass | block
    contradicted: list[dict]
    unverified: list[dict]
    flag_unverified: bool                     # inconclusive > max_unverified_claims → Tony xem kỹ
    claims: list[ClaimResult]
    sources: list[dict]                       # meta snapshot (url, sha256, path) hoặc lỗi tải
    issues: list[dict] = field(default_factory=list)   # [{where, line, why, suggested_fix}] — patch
    llm: list[dict] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


# ── Nguồn ────────────────────────────────────────────────────────────────────
def source_urls(script: "Script") -> list[str]:
    urls = [str(s.get("url", "")).strip() for s in script.sources]
    urls += [sh.url for sh in script.shots if getattr(sh, "url", None)]
    out: list[str] = []
    for u in urls:
        if u and u not in out:
            out.append(u)
    return out


def load_sources(urls: list[str]) -> tuple[dict[str, "object"], list[dict]]:
    """→ ({"S1": Snapshot…}, meta). Tải hỏng / ngoài allowlist → ghi lỗi, bỏ qua."""
    from ..team.snapshot import fetch

    snaps, meta = {}, []
    for u in urls:
        try:
            s = fetch(u)
        except Exception as e:
            meta.append({"url": u, "error": f"{type(e).__name__}: {e}"[:300]})
            continue
        sid = f"S{len(snaps) + 1}"
        snaps[sid] = s
        meta.append({"id": sid, **s.meta()})
    return snaps, meta


# ── Prompt ───────────────────────────────────────────────────────────────────
EXTRACT_SYSTEM = """Bạn rút CLAIM KIỂM CHỨNG ĐƯỢC từ lời đọc của một video TikTok tiếng Việt về AI.

Claim kiểm chứng được = khẳng định về sự thật có thể đối chiếu với tài liệu: tên model và
thuộc tính của nó, con số (tham số, VRAM, tốc độ, số giờ dữ liệu, điểm benchmark, số ngôn ngữ…),
ngày/tháng/năm ra mắt, tổ chức/tác giả làm ra nó, license, việc model có/không có một khả năng.

KHÔNG rút: ý kiến, cảm nhận, lời kêu gọi, câu hỏi, khuyên nhủ ("khó tin", "đáng thử", "comment nhé").

Luật:
1. Mỗi claim MỘT sự thật. Câu có hai con số → hai claim.
2. `claim` tự đứng được: thay "nó", "model này" bằng tên thật lấy từ ngữ cảnh. Giữ nguyên con
   số đúng như lời đọc (số viết bằng chữ thì giữ bằng chữ) — KHÔNG sửa, KHÔNG làm tròn,
   KHÔNG "chữa" claim mà bạn nghĩ là sai. Việc của bạn là chép, không phải phán.
3. `line` = chỉ số câu chứa claim. `type`: model_name | benchmark_number | number |
   release_date | date | org_name | license | other."""

# Kênh mẹo (2026-10-04, research/13 §4): thêm loại claim sức khoẻ / an toàn thực phẩm — loại nào nằm trong
# `channel.yaml: t4.require_tier1_for` thì chỉ đạt khi nguồn thuộc tier1 (cơ quan nhà nước / tổ chức y tế).
EXTRA_TYPES = ("health", "food_safety")


def _claim_types() -> tuple[str, ...]:
    from ..channel import current

    base = ClaimType.__args__
    return base + EXTRA_TYPES if current().t4.get("require_tier1_for") else base


def _extract_model() -> type[ExtractOut]:
    from pydantic import create_model

    claim = create_model("ExtractedClaim", __base__=ExtractedClaim,
                         type=(Literal[_claim_types()], ...))  # type: ignore[valid-type]
    return create_model("ExtractOut", __base__=ExtractOut, claims=(list[claim], ...))


def extract_system() -> str:
    from ..channel import current

    ch = current()
    if ch.id == "ai" or not ch.t4.get("require_tier1_for"):
        return EXTRACT_SYSTEM
    s = EXTRACT_SYSTEM.replace("video TikTok tiếng Việt về AI.", f"video TikTok tiếng Việt về "
                               f"{ch.text('topic_of_video', ch.name)}.")
    i, j = s.index("Claim kiểm chứng được ="), s.index("KHÔNG rút:")
    s = s[:i] + ("Claim kiểm chứng được = khẳng định về sự thật có thể đối chiếu với tài liệu: con số (thời gian bảo "
                 "quản, nhiệt độ, số tiền, phí, mức phạt, phần trăm), điều một cơ quan/ngân hàng/hãng quy định hay "
                 "khuyến cáo, việc một ứng dụng có/không có một tính năng, tác động lên sức khoẻ, an toàn thực phẩm.\n\n"
                 "KHÔNG rút thêm: lời khuyên giao tiếp mang tính gợi ý (\"nên nói…\"), trừ khi gán cho một nguồn.\n") + s[j:]
    s = s.replace("release_date | date | org_name | license | other.",
                  "release_date | date | org_name | license | health | food_safety | other.\n"
                  "4. `health` = khẳng định về tác động lên SỨC KHOẺ (gây bệnh, tốt cho tim…). `food_safety` = "
                  "khẳng định về an toàn thực phẩm (bảo quản bao lâu, nhiệt độ, vi khuẩn, hoá chất, độc tố). "
                  "Câu có con số về thực phẩm/sức khoẻ vẫn là health/food_safety, không phải number.")
    return s


CHECK_SYSTEM = """Bạn là FACT-CHECKER. Đối chiếu từng claim với các NGUỒN đã lưu bên dưới — chỉ nguồn
đó, KHÔNG dùng hiểu biết riêng, kể cả khi bạn "biết" claim đúng hay sai.

Ba nhãn:
- supported: nguồn nói ĐÚNG điều claim nói.
- contradicted: nguồn nói TRỰC TIẾP điều KHÁC (số khác, ngày khác, tổ chức khác, license khác,
  nguồn khẳng định điều ngược lại). Phải chỉ ra được câu nguồn mâu thuẫn.
- inconclusive: nguồn không nói tới, hoặc nói không đủ rõ. Không tìm thấy ≠ sai.

Luật:
1. supported/contradicted thì `quote` PHẢI chép NGUYÊN VĂN một đoạn ngắn (≤ 300 ký tự) từ đúng
   nguồn `source_id` — code sẽ tìm chuỗi đó trong nguồn; không khớp là lời phán bị hạ xuống
   inconclusive. inconclusive thì để quote rỗng.
2. Claim có CON SỐ: kind="number", `claim_value` = số trong claim ĐỔI VỀ ĐƠN VỊ CỦA NGUỒN
   (claim "một phẩy năm GB", nguồn tính MiB → 1536), `source_value` = số trong quote, `unit`.
   Số tiếng Việt: "tám phẩy hai" = 8.2, "sáu trăm hai mươi bốn" = 624, "sáu trăm tám mươi
   nghìn" = 680000, "hai trăm năm mươi sáu nghìn" = 256000, "một triệu" = 1000000.
3. Claim có NGÀY: kind="date", `claim_date` ĐÚNG độ mịn claim nói ("tháng hai năm 2024" →
   "2024-02"; "năm 2022" → "2022"), `source_date` = ngày trong quote dạng ISO.
4. Ngày phát hành model: nguồn HF/GitHub có `createdAt`/`created_at`, arXiv có `Submitted (v1)` —
   dùng được làm bằng chứng ngày ra mắt/lên arXiv/lên Hugging Face.
5. Mỗi claim một verdict, đủ mọi claim_id.
6. Claim bắt đầu bằng "[trên hình]" là con số hiện trên màn hình (thẻ số, cột biểu đồ, chữ dán) —
   phán như claim thường; đơn vị/cách viết rút gọn ("$2 vào / $10 ra", "1/5 giá Astra") là bình thường."""


def _fmt_sources(snaps: dict) -> str:
    parts = []
    for sid, s in snaps.items():
        t = s.text[:MAX_SOURCE_CHARS]
        parts.append(f"=== {sid} — {s.url} ===\n{t}")
    return "\n\n".join(parts) if parts else "(không có nguồn nào tải được)"


def extract_prompt(script: "Script") -> str:
    lines = "\n".join(f"[{i}] {t}" for i, t in enumerate(script.lines))
    return f"Chủ đề: {script.topic}\n\nLỜI ĐỌC:\n{lines}\n\nRút claim."


def check_prompt(claims: list[ExtractedClaim], snaps: dict) -> str:
    cl = "\n".join(f"#{i} (câu {c.line}, {c.type}): {c.claim}" for i, c in enumerate(claims))
    return f"NGUỒN:\n\n{_fmt_sources(snaps)}\n\nCLAIM:\n{cl}\n\nPhán từng claim."


# ── Cổng code ────────────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"[*_`]", "", s)          # markdown nhấn trong README
    return " ".join(s.split())


def quote_in(quote: str, text: str) -> bool:
    q = _norm(quote)
    return bool(q) and q in _norm(text)


def _num_forms(x: float) -> set[str]:
    """Các cách viết của một số trong văn bản nguồn: 680000 → {680000, 680,000, 680k, 680 000}."""
    forms = set()
    if float(x).is_integer():
        i = int(x)
        forms |= {str(i), f"{i:,}", f"{i:,}".replace(",", " "), f"{i:,}".replace(",", ".")}
        for div, suf in ((1_000_000_000, "b"), (1_000_000, "m"), (1_000, "k")):
            if i % div == 0 and i >= div:
                forms.add(f"{i // div}{suf}")
                forms.add(f"{i // div} {suf}")
    else:
        s = f"{x:g}"
        forms |= {s, s.replace(".", ",")}
    return forms


def number_in_quote(x: float, quote: str) -> bool:
    q = _norm(quote)
    for f in _num_forms(x):
        if re.search(rf"(?<![\d.,]){re.escape(f.lower())}(?![\d])", q):
            return True
    return False


def _decimals(x: float) -> int:
    s = f"{x:g}"
    return len(s.split(".")[1]) if "." in s and "e" not in s else 0


def numbers_match(claim: float, source: float) -> bool:
    tol = max(NUM_REL_TOL * abs(source), 0.5 * 10 ** (-_decimals(claim)))
    return abs(claim - source) <= tol


_ISO = re.compile(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?")


def dates_match(claim_date: str, source_date: str) -> bool | None:
    """So ở độ mịn của claim. None = không đọc được ngày."""
    c, s = _ISO.match(claim_date.strip()), _ISO.match(source_date.strip())
    if not c or not s:
        return None
    for a, b in zip(c.groups(), s.groups()):
        if a is None:
            break
        if b is None or a != b:
            return False
    return True


def gate(claim: ExtractedClaim, v: Verdict | None, snaps: dict) -> tuple[str, str]:
    """Lời phán của LLM → (verdict sau cổng, ghi chú cổng)."""
    if v is None:
        return "inconclusive", "fact_checker bỏ sót claim này"
    if v.verdict == "inconclusive":
        return "inconclusive", ""
    s = snaps.get(v.source_id)
    if s is None:
        return "inconclusive", f"source_id {v.source_id!r} không tồn tại"
    if not quote_in(v.quote, s.text):
        return "inconclusive", "trích không có nguyên văn trong nguồn"
    if v.kind == "number" and v.claim_value is not None and v.source_value is not None:
        if not number_in_quote(v.source_value, v.quote):
            return "inconclusive", f"source_value {v.source_value:g} không có trong trích"
        ok = numbers_match(v.claim_value, v.source_value)
        code = "supported" if ok else "contradicted"
        note = "" if code == v.verdict else f"code so số {v.claim_value:g} vs {v.source_value:g} → {code}"
        return code, note
    if v.kind == "date" and v.claim_date and v.source_date:
        if v.source_date[:4] not in v.quote:
            return "inconclusive", f"source_date {v.source_date!r} không có trong trích"
        m = dates_match(v.claim_date, v.source_date)
        if m is not None:
            code = "supported" if m else "contradicted"
            note = "" if code == v.verdict else f"code so ngày {v.claim_date} vs {v.source_date} → {code}"
            return code, note
    return v.verdict, ""


def build_report(script: "Script", claims: list[ExtractedClaim], verdicts: list[Verdict],
                 snaps: dict, sources_meta: list[dict], thr: dict | None = None,
                 llm: list[dict] | None = None) -> T4Report:
    thr = thr or _thresholds()
    by_id = {v.claim_id: v for v in verdicts}
    results: list[ClaimResult] = []
    for i, c in enumerate(claims):
        v = by_id.get(i)
        final, note = gate(c, v, snaps)
        src = snaps.get(v.source_id) if v else None
        results.append(ClaimResult(
            id=i, line=c.line, claim=c.claim, type=c.type, verdict=final,
            llm_verdict=v.verdict if v else "", source_url=src.url if src else "",
            quote=v.quote if v and final != "inconclusive" else "", reason=v.reason if v else "", gate=note,
        ))
    contra = [r for r in results if r.verdict == "contradicted"]
    unver = [r for r in results if r.verdict == "inconclusive"]
    n = len(script.lines)
    # Kênh mẹo: claim sức khoẻ/an toàn thực phẩm chỉ đạt khi nguồn tier1 — không thì CHẶN như mâu thuẫn.
    from ..channel import current

    ch = current()
    need_t1 = set(ch.t4.get("require_tier1_for") or [])
    tier_fail = [r for r in results if r.type in need_t1 and r.verdict != "contradicted"
                 and not (r.verdict == "supported" and ch.tier(r.source_url) == 1)]
    for r in tier_fail:
        r.gate = (r.gate + "; " if r.gate else "") + "cần nguồn tier1 (cơ quan nhà nước/tổ chức y tế)"

    def where(line: int) -> str:
        return "hook (câu 0)" if line == 0 else (f"CTA (câu {line})" if line == n - 1 else f"câu {line}")

    issues = [{"where": where(r.line), "line": r.line, "claim": r.claim,
               "why": f"mâu thuẫn nguồn {r.source_url}: «{r.quote}»" + (f" — {r.reason}" if r.reason else ""),
               "suggested_fix": "sửa theo đúng nguồn đã trích, hoặc bỏ câu"} for r in contra]
    issues += [{"where": where(r.line), "line": r.line, "claim": r.claim,
                "why": f"claim {r.type} không có nguồn tier1 xác nhận" + (f" (nguồn hiện có: {r.source_url})"
                                                                         if r.source_url else ""),
                "suggested_fix": "chỉ nói điều cơ quan y tế/an toàn thực phẩm nói, hoặc bỏ câu"} for r in tier_fail]
    return T4Report(
        verdict="block" if len(contra) > thr["max_contradictions"] or tier_fail else "pass",
        contradicted=[asdict(r) for r in contra],
        unverified=[asdict(r) for r in unver],
        flag_unverified=len(unver) > thr["max_unverified_claims"],
        claims=results, sources=sources_meta, issues=issues, llm=llm or [],
    )


def screen_claims(script: "Script") -> list[ExtractedClaim]:
    """Số do CODE vẽ lên hình (thẻ stat, cột chart, overlay có chữ số) → claim cho fact-checker.

    Thêm 2026-10-02 sau demo-03: `claim_extractor` chỉ đọc lời đọc, nên con số to nhất trên màn
    hình chưa từng được đối chiếu nguồn. Rút bằng code — tất định, không để LLM chọn số nào cần kiểm.
    """
    import re as _re

    out: list[ExtractedClaim] = []
    n = len(script.lines)

    def fmt(v) -> str:
        return f"{float(v):g}"

    for sh in script.shots:
        line = sh.line if sh.line is not None and 0 <= sh.line < n else 0
        if sh.kind == "stat" and sh.stat:
            st = sh.stat
            out.append(ExtractedClaim(line=line, type="number",
                                      claim=f"[trên hình] {st.get('label', '')}: {st.get('prefix') or ''}"
                                            f"{fmt(st.get('value', 0))} {st.get('unit') or ''}".strip()))
        elif sh.kind == "chart" and sh.chart:
            ch = sh.chart
            for b in ch.get("bars", []):
                out.append(ExtractedClaim(line=line, type="number",
                                          claim=f"[trên hình] {ch.get('title', '')} — {b.get('label', '')}: "
                                                f"{fmt(b.get('value', 0))} {ch.get('unit') or ''}".strip()))
        elif sh.kind == "list" and sh.list:
            # Kênh mẹo (2026-10-04): mỗi mục trên thẻ là một khẳng định ("Cà chua — đừng cho vào tủ lạnh").
            lt = sh.list
            for it in lt.get("items", []):
                out.append(ExtractedClaim(line=line, type="other",
                                          claim=f"[trên hình] {lt.get('title') or ''}: {it.get('text', '')}".strip()))
        elif sh.kind == "chat" and sh.chat:
            for m in sh.chat.get("messages", []):
                if _re.search(r"\d", m.get("text", "")):
                    out.append(ExtractedClaim(line=line, type="number", claim=f"[trên hình] {m.get('text', '')}"))
    for o in script.overlays:
        if _re.search(r"\d", o.get("text", "")):
            out.append(ExtractedClaim(line=int(o["line"]) if 0 <= int(o["line"]) < n else 0, type="number",
                                      claim=f"[trên hình] {o['text']} (câu: {script.lines[int(o['line'])][:80]})"))
    return out


def _last_call(state, n0: int) -> dict:
    if state is None or len(state.llm_calls) <= n0:
        return {}
    c = state.llm_calls[-1]
    return {k: c.get(k) for k in ("role", "wall_sec", "input_tokens", "output_tokens", "cost_usd")}


async def acheck(script: "Script", *, state: "State | None" = None, model: str | None = None,
                 artifact: Path | None = None, _query=None, _snaps: tuple | None = None) -> T4Report:
    from ..team import arun_role

    snaps, meta = _snaps if _snaps is not None else load_sources(source_urls(script))
    llm: list[dict] = []
    n0 = len(state.llm_calls) if state is not None else 0
    ext = await arun_role("claim_extractor", extract_prompt(script), _extract_model(),
                          system_prompt=extract_system(), tools=[], max_turns=4, max_budget_usd=1.0,
                          model=model, state=state, _query=_query)
    llm.append(_last_call(state, n0))
    claims = [c for c in ext.claims if 0 <= c.line < len(script.lines)] + screen_claims(script)
    verdicts: list[Verdict] = []
    if claims:
        n0 = len(state.llm_calls) if state is not None else 0
        chk = await arun_role("fact_checker", check_prompt(claims, snaps), CheckOut,
                              system_prompt=CHECK_SYSTEM, tools=[], max_turns=4, max_budget_usd=2.0,
                              model=model, state=state, _query=_query)
        llm.append(_last_call(state, n0))
        verdicts = chk.verdicts
    rep = build_report(script, claims, verdicts, snaps, meta, llm=[x for x in llm if x])
    if artifact is not None:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(rep.to_json() + "\n", encoding="utf-8")
    return rep


def check(script: "Script", **kw) -> T4Report:
    import asyncio

    return asyncio.run(acheck(script, **kw))


def revision_notes(rep: T4Report) -> list[str]:
    """Patch gửi scriptwriter: chỉ claim contradicted, kèm url + trích nguồn (tín hiệu ngoài)."""
    return [f"[T4] {i['where']}: «{i['claim']}» {i['why']} → {i['suggested_fix']}" for i in rep.issues]


def main(argv: list[str] | None = None) -> int:
    import argparse

    from ..agents.scriptwriter import Script
    from ..team import State

    ap = argparse.ArgumentParser(description="QC tầng 4 — fact-check script.json với nguồn đã lưu")
    ap.add_argument("script", type=Path)
    ap.add_argument("--out", type=Path, help="mặc định <thư mục script>/factcheck.json")
    ap.add_argument("--state-dir", type=Path)
    ap.add_argument("--model", default=None)
    a = ap.parse_args(argv)

    script = Script.from_dict(json.loads(a.script.read_text(encoding="utf-8")))
    state = State.load(a.state_dir or a.script.parent)
    out = a.out or a.script.parent / "factcheck.json"
    rep = check(script, state=state, model=a.model, artifact=out)

    print(f"T4 {rep.verdict.upper()}  claim={len(rep.claims)}  contradicted={len(rep.contradicted)}  "
          f"inconclusive={len(rep.unverified)}{'  ⚑ quá nhiều chưa kiểm được' if rep.flag_unverified else ''}")
    for s in rep.sources:
        if "error" in s:
            print(f"  ! nguồn {s['url']}: {s['error']}")
    for c in rep.claims:
        mark = {"supported": "✓", "contradicted": "✗", "inconclusive": "?"}[c.verdict]
        g = f"  [{c.gate}]" if c.gate else ""
        print(f"  {mark} câu {c.line}: {c.claim}{g}")
        if c.verdict == "contradicted":
            print(f"      ← {c.source_url}: «{c.quote}»")
    print(f"  → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
