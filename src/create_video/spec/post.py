"""`video-spec.json` → `post.json` — metadata để dán thẳng vào app TikTok.

Tách khỏi `build.py` vì đây không phải ranh giới Python ↔ Remotion (Remotion
không đọc file này); nó là output cho Tony/bot Telegram (P5.S2), nên đứng riêng.

`requires_ai_label` LUÔN `true`: pipeline này dùng giọng tổng hợp + ảnh AI, và
theo `research/07-len-xu-huong.md` mục 4, tự bật nhãn không giảm phân phối,
nhưng bị hệ thống tự gắn thì không gỡ được. Không có nhánh nào khác.
"""

from __future__ import annotations

import json
from pathlib import Path


def write_post(*, spec: dict, out_dir: Path, mp4_name: str = "video.mp4") -> Path:
    """Đọc `caption`/`hashtags`/`keywords` từ `spec["meta"]`, ghi `out_dir/post.json`."""
    meta = spec["meta"]
    caption = meta.get("caption", "")
    hashtags = meta.get("hashtags", [])
    keywords = meta.get("keywords", [])

    tags_line = " ".join(f"#{h}" for h in hashtags)
    post = {
        "id": meta["id"],
        "topic": meta["topic"],
        "caption": caption,
        "hashtags": [f"#{h}" for h in hashtags],
        "keywords": keywords,
        "requires_ai_label": True,
        "mp4": mp4_name,
        # dán thẳng vào ô caption của app — khỏi phải ghép tay caption + hashtag
        "paste_text": f"{caption}\n\n{tags_line}".strip(),
    }

    post_path = Path(out_dir) / "post.json"
    post_path.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return post_path
