"""Tô màu code bằng Pygments ở PHÍA PYTHON (P3b.S4).

Vì sao không để Remotion tự highlight: thư viện JS (Code Hike, Shiki) chạy async
hoặc kéo theo React 19 + vài MB grammar; Pygments (BSD-2) đã có sẵn trong .venv.
Python tách token một lần, spec mang LOẠI token (`kw`, `str`…) — Remotion chỉ việc
tô màu theo loại. Render tất định, 0 dependency npm, và đúng tinh thần ranh giới:
spec mô tả CÁI GÌ, không mô tả LÀM THẾ NÀO.
"""

from __future__ import annotations

from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Comment, Keyword, Name, Number, Operator, Punctuation, String

_LEXER = {"python": "python", "bash": "bash", "typescript": "typescript",
          "javascript": "javascript", "json": "json", "yaml": "yaml", "text": "text"}

# Thứ tự quan trọng: Name.Builtin phải xét trước Name chung.
_MAP = [
    (Comment, "com"), (String, "str"), (Number, "num"), (Keyword, "kw"),
    (Name.Builtin, "bi"), (Name.Function, "fn"), (Name.Class, "fn"),
    (Operator, "op"), (Punctuation, "op"),
]


def _cat(tok) -> str:
    for base, cat in _MAP:
        if tok in base:
            return cat
    return "txt"


def tokenize(lang: str, lines: list[str]) -> list[list[dict]]:
    """`lines` → mỗi dòng một dãy `{t, v}`. Gộp token liền nhau cùng loại cho spec gọn."""
    lexer = get_lexer_by_name(_LEXER.get(lang, "text"), stripnl=False, ensurenl=False)
    out: list[list[dict]] = [[]]
    for tok, val in lex("\n".join(lines), lexer):
        cat = _cat(tok)
        for k, part in enumerate(val.split("\n")):
            if k:
                out.append([])
            if not part:
                continue
            row = out[-1]
            if row and row[-1]["t"] == cat:
                row[-1]["v"] += part
            else:
                row.append({"t": cat, "v": part})
    return out[: len(lines)]
