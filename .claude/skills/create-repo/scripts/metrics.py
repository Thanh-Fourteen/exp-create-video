"""OCR metrics, with the Vietnamese diacritic split built in.

Seeded by the create-repo skill. The one non-obvious thing here: for Vietnamese
you must report CER twice — with diacritics and with them stripped. The gap
between the two is your diacritic error rate, and on degraded scans that is
usually where most of the remaining error lives.

Unicode normalisation matters as much as the model: the same Vietnamese string
can be stored as NFC ("ế") or NFD ("e" + two combining marks). Comparing across
forms invents errors that are not there. Everything below normalises to NFC
first.
"""

from __future__ import annotations

import unicodedata

# đ/Đ are distinct Vietnamese letters, not decorated d — NFD leaves them intact,
# so they need an explicit mapping when stripping diacritics.
_VI_STROKE = str.maketrans({"đ": "d", "Đ": "D"})


def normalize(s: str) -> str:
    """NFC-normalise. Apply to BOTH reference and hypothesis before any metric."""
    return unicodedata.normalize("NFC", s)


def strip_diacritics(s: str) -> str:
    """Remove Vietnamese tone and vowel marks. 'Tiếng Việt' -> 'Tieng Viet'."""
    decomposed = unicodedata.normalize("NFD", s.translate(_VI_STROKE))
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def levenshtein(a: str, b: str) -> int:
    """Edit distance. O(len(a) * len(b)) time, O(min) space."""
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(ref: str, hyp: str) -> float:
    """Character error rate. 0.0 = perfect. Can exceed 1.0 when hyp is longer."""
    ref, hyp = normalize(ref), normalize(hyp)
    if not ref:
        return 0.0 if not hyp else 1.0
    return levenshtein(ref, hyp) / len(ref)


def wer(ref: str, hyp: str) -> float:
    """Word error rate on whitespace tokens."""
    r, h = normalize(ref).split(), normalize(hyp).split()
    if not r:
        return 0.0 if not h else 1.0
    # reuse the character routine over word-index sequences
    vocab: dict[str, str] = {}

    def encode(ws: list[str]) -> str:
        return "".join(vocab.setdefault(w, chr(0xE000 + len(vocab))) for w in ws)

    return levenshtein(encode(r), encode(h)) / len(r)


def cer_stripped(ref: str, hyp: str) -> float:
    """CER ignoring diacritics — the score if tone marks did not exist."""
    return cer(strip_diacritics(normalize(ref)), strip_diacritics(normalize(hyp)))


def diacritic_error_rate(ref: str, hyp: str) -> float:
    """CER attributable to diacritics alone. Report this next to cer()."""
    return max(0.0, cer(ref, hyp) - cer_stripped(ref, hyp))


def report(ref: str, hyp: str) -> dict[str, float]:
    """The minimum honest per-sample report for Vietnamese OCR.

    A large `diacritic` value with a small `cer_stripped` means the model reads
    the letters and misses the marks — a data or resolution problem, not a
    recognition-architecture problem. Fix preprocessing before changing models.
    """
    return {
        "cer": cer(ref, hyp),
        "cer_stripped": cer_stripped(ref, hyp),
        "diacritic": diacritic_error_rate(ref, hyp),
        "wer": wer(ref, hyp),
    }


def corpus_report(pairs: list[tuple[str, str]]) -> dict[str, float]:
    """Aggregate over (reference, hypothesis) pairs.

    Length-weighted, not a mean of per-sample rates: a mean over samples lets one
    short line with a single error outweigh a whole correct page.
    """
    if not pairs:
        return {"cer": 0.0, "cer_stripped": 0.0, "diacritic": 0.0, "n": 0}
    total = sum(len(normalize(r)) for r, _ in pairs) or 1
    dist = sum(levenshtein(normalize(r), normalize(h)) for r, h in pairs)
    s_total = sum(len(strip_diacritics(normalize(r))) for r, _ in pairs) or 1
    s_dist = sum(
        levenshtein(strip_diacritics(normalize(r)), strip_diacritics(normalize(h)))
        for r, h in pairs
    )
    c, c_s = dist / total, s_dist / s_total
    return {"cer": c, "cer_stripped": c_s, "diacritic": max(0.0, c - c_s), "n": len(pairs)}


# --- structure metrics -------------------------------------------------------
# CER/WER are blind to layout. A page with perfect characters and interleaved
# columns scores well above and is useless downstream. Add these before shipping:
#
#   TEDS / TEDS-S        tables      -> use the OmniDocBench implementation
#   CDM                  formulas    -> renders and compares; robust to LaTeX rewriting
#   reading-order ED     block order -> levenshtein() over block-id sequences
#
# reading_order_ed() below is the one that needs no external dependency.


def reading_order_ed(ref_ids: list[str], hyp_ids: list[str]) -> float:
    """Normalised edit distance between block-id sequences. 0.0 = correct order."""
    if not ref_ids:
        return 0.0 if not hyp_ids else 1.0
    vocab: dict[str, str] = {}

    def encode(ids: list[str]) -> str:
        return "".join(vocab.setdefault(i, chr(0xE000 + len(vocab))) for i in ids)

    return levenshtein(encode(ref_ids), encode(hyp_ids)) / len(ref_ids)
