"""Tests for the seeded OCR metrics. Run: python3 -m pytest tests/ -q"""

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# The package name is set at scaffold time; import it dynamically so this file
# works whatever the repo is called.
import importlib
import pkgutil

_src = Path(__file__).resolve().parents[1] / "src"
_pkg = next(m.name for m in pkgutil.iter_modules([str(_src)]) if not m.name.startswith("_"))
m = importlib.import_module(f"{_pkg}.metrics")


def test_identical_is_zero():
    assert m.cer("Tiếng Việt", "Tiếng Việt") == 0.0


def test_nfc_nfd_are_not_errors():
    """The same string in different Unicode forms must score 0, not 1.0."""
    nfc = unicodedata.normalize("NFC", "Tiếng Việt")
    nfd = unicodedata.normalize("NFD", "Tiếng Việt")
    assert nfc != nfd  # genuinely different byte sequences
    assert m.cer(nfc, nfd) == 0.0


def test_strip_diacritics():
    assert m.strip_diacritics("Tiếng Việt") == "Tieng Viet"
    assert m.strip_diacritics("Đường Đi") == "Duong Di"  # đ/Đ need explicit mapping
    assert m.strip_diacritics("hòa bình") == "hoa binh"


def test_diacritic_only_error_is_isolated():
    """Right letters, wrong marks: cer > 0 but cer_stripped == 0."""
    ref, hyp = "Tiếng Việt", "Tiêng Viêt"
    assert m.cer(ref, hyp) > 0
    assert m.cer_stripped(ref, hyp) == 0.0
    assert m.diacritic_error_rate(ref, hyp) == m.cer(ref, hyp)


def test_base_letter_error_shows_in_both():
    ref, hyp = "Tiếng Việt", "Tiếng Việc"
    assert m.cer(ref, hyp) > 0
    assert m.cer_stripped(ref, hyp) > 0


def test_empty_reference():
    assert m.cer("", "") == 0.0
    assert m.cer("", "hallucinated") == 1.0


def test_wer_counts_words():
    assert m.wer("một hai ba", "một hai ba") == 0.0
    assert m.wer("một hai ba", "một hai") == 1 / 3


def test_corpus_is_length_weighted():
    """One short wrong line must not outweigh a long correct one."""
    pairs = [("a", "b"), ("x" * 99, "x" * 99)]
    assert m.corpus_report(pairs)["cer"] == 1 / 100  # not the 0.5 a per-sample mean gives


def test_reading_order():
    assert m.reading_order_ed(["a", "b", "c"], ["a", "b", "c"]) == 0.0
    assert m.reading_order_ed(["a", "b", "c"], ["a", "c", "b"]) > 0.0


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS {name}")
            except AssertionError as e:
                fails += 1
                print(f"  FAIL {name}: {e or 'assertion failed'}")
    print("all passed" if not fails else f"{fails} failed")
    sys.exit(1 if fails else 0)
