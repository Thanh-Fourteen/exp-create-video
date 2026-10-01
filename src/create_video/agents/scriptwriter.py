"""Agent viết kịch bản: chủ đề → `script.json`.

Dùng `claude-agent-sdk` (`query()`), **không** phải `client.beta.messages.tool_runner`
của SDK `anthropic` — hai package khác nhau và rất hay bị lẫn. Chạy bằng auth sẵn
có của Claude Code nên chi phí LLM là 0đ, đúng ràng buộc của dự án.

Ba điều đóng khung prompt ở đây, cả ba đều có lý do đo được:

1. **Nhét nguyên `configs/rubric.md` vào prompt hệ thống.** Producer biết trước
   critic T3 sẽ chấm bằng gì thì viết đúng ngay từ vòng đầu — đây là cách rẻ nhất
   để kéo `qc_rounds` xuống dưới 1,5.
2. **Cấm số và ký hiệu trong lời đọc.** exp-echo chuẩn hoá trước khi đọc: "15%" →
   "mười lăm phần trăm", "2060" → "hai nghìn không trăm sáu mươi". Khi đó số token
   đọc lệch số token hiển thị và phụ đề karaoke phải chia lại thời gian thay vì
   dùng số đo (`spec/captions.py`). Viết sẵn bằng chữ thì giữ được đường "exact".
3. **Prompt ảnh viết bằng tiếng Anh.** SDXL hiểu tiếng Anh tốt hơn hẳn, và
   `visual/sdxl.py` đã nối sẵn đuôi phong cách + negative prompt.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Lời đọc: mỗi câu là MỘT caption trên màn hình. Dài quá thì chữ tràn xuống vùng
# UI TikTok che (T1 kiểm chỗ này), ngắn quá thì phụ đề nhấp nháy.
# 2026-08-14 sáng: hạ trần 16 -> 12 từ cho nhịp nhanh hơn.
# 2026-08-14 chiều: TRẢ VỀ 5-16. Đây là thay đổi có ảnh hưởng lớn nhất tới việc
# giọng đọc nghe có tự nhiên không, và lúc đầu tôi không lường: mỗi câu là MỘT
# lần gọi TTS riêng rồi ghép lại kèm 0,28s lặng. Câu càng ngắn thì càng nhiều
# mối ghép, và mỗi mối ghép là một chỗ ngắt hơi không giống người nói. Tony nghe
# demo-02 và nhận ra ngay: "không tự nhiên như người nói".
MIN_WORDS, MAX_WORDS = 5, 16
OVERLAY_MAX_CHARS = 24  # khớp maxLength ở spec/schema.json


@dataclass
class Shot:
    prompt: str           # tiếng Anh, cho SDXL
    duration_sec: float
    motion: str = "ken_burns"
    # Kiểu cũ (trước 2026-10-01): overlay gắn vào shot. Vẫn đọc để không vỡ
    # script.json cũ, nhưng pipeline KHÔNG dùng nữa — shot và câu không tương
    # ứng 1-1 nên overlay hiện sai lúc. Dùng `Script.overlays`.
    overlay: str | None = None


@dataclass
class Script:
    topic: str
    hook: str
    sections: list[str] = field(default_factory=list)
    cta: str = ""
    shots: list[Shot] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    caption: str = ""                          # TikTok cắt hiển thị ở 150 ký tự
    hashtags: list[str] = field(default_factory=list)   # 3-5, ngách, không #fyp #viral
    keywords: list[str] = field(default_factory=list)   # keywords[0] = từ khoá chính
    # Chữ dán trên hình, gắn vào CÂU: [{"line": chỉ số trong `lines`, "text": "16-bit"}].
    # line 0 = hook, 1..n = sections, cuối = cta. Overlay hiện đúng lúc câu đó được đọc.
    overlays: list[dict] = field(default_factory=list)

    @property
    def lines(self) -> list[str]:
        """Toàn bộ lời đọc theo thứ tự: hook → thân → CTA."""
        return [self.hook, *self.sections, self.cta]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict, topic: str | None = None) -> "Script":
        """Một chỗ duy nhất đọc JSON → Script: cho cả output agent lẫn script.json cache."""
        return cls(
            topic=topic or d.get("topic", ""),
            hook=d["hook"].strip(),
            sections=[x.strip() for x in d.get("sections", [])],
            cta=d.get("cta", "").strip(),
            shots=[
                Shot(
                    prompt=x["prompt"],
                    duration_sec=float(x.get("duration_sec", 5)),
                    motion=x.get("motion", "ken_burns"),
                    overlay=x.get("overlay"),
                )
                for x in d.get("shots", [])
            ],
            sources=d.get("sources", []),
            caption=d.get("caption", "").strip(),
            hashtags=[str(h).lstrip("#").strip() for h in d.get("hashtags", [])],
            keywords=[str(k).strip() for k in d.get("keywords", [])],
            overlays=[
                {"line": int(o["line"]), "text": str(o["text"]).strip()}
                for o in d.get("overlays", [])
            ],
        )


def _avoid_rule() -> str:
    """Từ TTS đọc hỏng (configs/pronounce.yaml: avoid, đo bằng ASR ở P3b.S3) → dặn tránh."""
    import yaml

    p = REPO_ROOT / "configs" / "pronounce.yaml"
    d = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("avoid") if p.exists() else None
    pairs = [f'"{k}" → "{v}"' for k, v in (d or {}).items() if k != v]
    if not pairs:
        return ""
    return (
        "   NGOẠI LỆ — giọng đọc phát âm hỏng các từ sau, dùng từ Việt thay khi câu vẫn tự\n"
        "   nhiên: " + ", ".join(pairs) + "."
    )


def _system_prompt(duration_sec: int) -> str:
    rubric = (REPO_ROOT / "configs" / "rubric.md").read_text(encoding="utf-8")
    return f"""Bạn viết kịch bản video TikTok tiếng Việt về AI cho khán giả Việt Nam.
Video dọc 1080×1920, dài khoảng {duration_sec} giây, giọng đọc nam Bắc.

Nhịp là thứ quan trọng thứ hai sau hook: không có câu thừa. Bỏ mọi câu chuyển tiếp
kiểu "vậy thì", "như vậy là", "tiếp theo" — chúng ăn thời gian mà không mang thông
tin. Vào thẳng ý. Nhưng câu vẫn phải là câu nói được liền một hơi, không cắt vụn.

RUBRIC — đây chính là thứ critic sẽ dùng để chấm bạn. Đọc kỹ, viết đúng ngay từ đầu:

{rubric}

RÀNG BUỘC KỸ THUẬT — vi phạm là hỏng pipeline, không phải hỏng thẩm mỹ:

1. Số trong lời văn phải viết BẰNG CHỮ: "sáu GB", "ba mươi bảy giây", "mười lăm
   phần trăm" — không viết "6GB", "37 giây", "15%". Lý do: TTS đọc chữ số thành
   nhiều từ hơn số từ hiện trên màn hình, làm phụ đề karaoke mất mốc thời gian.
   NGOẠI LỆ: tên riêng thì giữ NGUYÊN dạng thật của nó — "Qwen3-VL", "GPT-5",
   "Claude Opus 5", "SDXL". Đổi tên model thành chữ là sai tên, tệ hơn nhiều so
   với lệch phụ đề vài chục mili giây.
2. Tên model, tên hãng, thuật ngữ tiếng Anh thì GIỮ NGUYÊN (model, benchmark,
   fine-tune, inference, prompt, open-source, hook, retention).
{_avoid_rule()}
3. Mỗi câu lời đọc {MIN_WORDS}-{MAX_WORDS} từ. Mỗi câu là một dòng phụ đề, và
   mỗi câu chỉ mang MỘT ý. Độ dài câu nên xen kẽ, đừng đều tăm tắp — nhưng
   ĐỪNG cắt vụn thành hàng loạt câu ba bốn từ: mỗi câu được đọc riêng rồi ghép
   lại, nên câu càng ngắn thì giọng đọc càng nhiều chỗ ngắt và càng nghe như máy.
4. `hook` là MỘT câu, tối đa 12 từ — đọc lên phải xong trong 3 giây.
5. `shots[].prompt` viết bằng TIẾNG ANH, tả cảnh cụ thể, KHÔNG chứa chữ hay logo
   trong ảnh (ảnh sinh ra chữ luôn méo, QC tầng 2 chặn).
6. `overlays` (không bắt buộc, nên có 2-4 cái) là chữ NGẮN (≤ {OVERLAY_MAX_CHARS} ký tự)
   dán lên hình — chỗ duy nhất được viết chữ số, vì nó do code vẽ. Mỗi overlay gắn
   vào MỘT CÂU qua `line` = chỉ số câu (0 = hook, 1 = sections[0], …, cuối = cta)
   và hiện ra đúng lúc câu đó được đọc — nên chữ phải khớp ĐÚNG điều câu đó nói
   ("mười sáu bit" → "16-bit"). Tối đa một overlay mỗi câu.
7. Nhịp: mỗi shot 3-8 giây, nên video {duration_sec} giây cần khoảng
   {duration_sec // 5} shot. Tổng `duration_sec` của các shot xấp xỉ {duration_sec}.
   Mỗi shot phải là một HÌNH KHÁC HẲN shot trước — đổi cảnh, đổi góc, đổi chủ
   thể. Cùng một cảnh chụp hai góc thì người xem không thấy là đã cắt.
8. Không bịa số liệu. Số nào nói ra phải kèm nguồn trong `sources`; không chắc
   thì đừng nói. Nội dung sai bị bóc rất nhanh và QC tầng 4 chặn cứng.

METADATA ĐĂNG BÀI — TikTok index cả caption, hashtag, chữ trên hình lẫn lời nói
(hơn 3 tỉ lượt tìm/ngày); bỏ trắng phần này là bỏ nửa tín hiệu tìm kiếm:

9. `keywords`: 2-5 từ khoá hoặc tên riêng, xếp từ QUAN TRỌNG NHẤT lên đầu
   (`keywords[0]` là từ khoá chính). Dùng để chèn vào caption và overlay.
10. `caption`: tối đa 150 ký tự (TikTok cắt hiển thị ở đó) — chứa `keywords[0]`
    trong 100 ký tự đầu. Viết như caption TikTok thật, không phải câu văn trang
    trọng; được chêm 1 emoji hợp ngữ cảnh nếu muốn.
11. `hashtags`: 3-5 hashtag NGÁCH bám sát nội dung video, KHÔNG dùng #fyp #viral
    (quá chung, TikTok hạ ưu tiên). Viết không dấu #, chữ thường liền không dấu
    cách, ví dụ: "sdxl", "aiopensource", "rtx2060".

Trả về DUY NHẤT một khối JSON, không lời dẫn, đúng cấu trúc:

{{
  "hook": "một câu",
  "sections": ["câu", "câu", "..."],
  "cta": "một câu kêu gọi cụ thể",
  "shots": [{{"prompt": "english scene description", "duration_sec": 5.0,
              "motion": "ken_burns"}}],
  "overlays": [{{"line": 2, "text": "16-bit"}}],
  "sources": [{{"claim": "điều đã nói", "url": "nguồn", "confidence": "verified|reported"}}],
  "keywords": ["từ khoá chính", "..."],
  "caption": "caption ngắn chứa từ khoá chính",
  "hashtags": ["ngach1", "ngach2", "ngach3"]
}}"""


def _extract_json(text: str) -> dict:
    """Lấy khối JSON ra khỏi câu trả lời, kể cả khi bị bọc trong ```json."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    raw = fenced.group(1) if fenced else None
    if raw is None:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError(f"không thấy JSON trong câu trả lời:\n{text[:600]}")
        raw = text[start : end + 1]
    return json.loads(raw)


def _bare_numbers(line: str) -> list[str]:
    """Số viết bằng chữ số mà KHÔNG thuộc tên riêng.

    Hai dạng được tha, vì cả hai đều là tên thật của thứ đang nói tới:

    - dính vào chữ: `Qwen3-VL`, `GPT-5`, `SDXL`
    - đứng sau một từ viết hoa: `Claude Opus 5`, `Gemini 3 Pro`

    Còn `"Nó nhanh hơn 15 lần"` thì bị bắt — đó là số trong lời văn, và TTS sẽ
    đọc thành "mười lăm" (một token thành hai), làm phụ đề mất mốc đo được.
    """
    out: list[str] = []
    toks = line.split()
    for j, tok in enumerate(toks):
        core = tok.strip(".,!?:;()\"'")
        if not core or not core.replace(",", "").replace(".", "").isdigit():
            continue
        prev = toks[j - 1].strip(".,!?:;()\"'") if j else ""
        if j >= 1 and prev[:1].isupper():
            # tên riêng: "Opus 5", "Gemini 3 Pro". Nhận cả khi tên đứng đầu câu
            # ("Gemini 3 Pro cũng vậy") — đổi lại là thỉnh thoảng tha nhầm
            # ("Card 6 GB"). Chọn lệch về phía THA có chủ ý: bắt oan tốn nguyên
            # một vòng gọi LLM (~5 phút), còn tha nhầm chỉ làm một câu phụ đề
            # rơi về đường "redistributed".
            continue
        out.append(core)
    return out


def _check(script: Script) -> list[str]:
    """Kiểm ràng buộc kỹ thuật bằng CODE, không hỏi lại LLM.

    Cùng tinh thần với QC tầng 1: cái gì đo được thì đừng để model tự chấm.
    """
    problems: list[str] = []
    # Cấm số ĐỨNG MỘT MÌNH ("15", "2060", "6") và ký hiệu %, nhưng CHO PHÉP số
    # nằm trong tên riêng ("Qwen3-VL", "GPT-5", "Claude Opus 5"). Cấm tuốt là
    # cấm luôn việc gọi đúng tên model — mà đó chính là nội dung của kênh.
    # Cái giá phải trả: những câu có tên model sẽ rơi vào đường "redistributed"
    # của spec/captions.py. Đã cân nhắc, chấp nhận.
    for i, line in enumerate(script.lines):
        n = len(line.split())
        if "%" in line:
            problems.append(f"câu {i} có ký hiệu %, viết thành 'phần trăm': {line!r}")
        for tok in _bare_numbers(line):
            problems.append(f"câu {i} có số {tok!r} viết bằng chữ số: {line!r}")
        if not (MIN_WORDS <= n <= MAX_WORDS):
            problems.append(f"câu {i} dài {n} từ, ngoài khoảng {MIN_WORDS}-{MAX_WORDS}: {line!r}")
    if len(script.hook.split()) > 12:
        problems.append(f"hook {len(script.hook.split())} từ — quá dài cho 3 giây")
    if not script.shots:
        problems.append("không có shot nào")
    seen: set[int] = set()
    for o in script.overlays:
        i, t = o["line"], o["text"]
        if not (0 <= i < len(script.lines)):
            problems.append(f"overlay {t!r} trỏ tới câu {i}, ngoài khoảng 0-{len(script.lines) - 1}")
        if i in seen:
            problems.append(f"câu {i} có hơn một overlay")
        seen.add(i)
        if not t or len(t) > OVERLAY_MAX_CHARS:
            problems.append(f"overlay {t!r} dài {len(t)} ký tự, trần {OVERLAY_MAX_CHARS}")
    problems.extend(_check_metadata(script))
    return problems


def _check_metadata(script: Script) -> list[str]:
    """P3.S5: caption/hashtag/keywords — cùng nguyên tắc với `_check`, đo bằng
    code chứ không hỏi lại LLM có "ổn" không."""
    problems: list[str] = []
    if not script.caption:
        problems.append("thiếu caption")
    elif len(script.caption) > 150:
        problems.append(f"caption dài {len(script.caption)} ký tự, vượt trần 150")

    if not (3 <= len(script.hashtags) <= 5):
        problems.append(f"có {len(script.hashtags)} hashtag, cần đúng 3-5")
    for h in script.hashtags:
        bare = h.lstrip("#").lower()
        if bare in {"fyp", "viral"}:
            problems.append(f"hashtag {h!r} bị cấm — #fyp/#viral quá chung, TikTok hạ ưu tiên")
        if not re.fullmatch(r"[a-z0-9_]+", bare):
            problems.append(f"hashtag {h!r} sai định dạng — chỉ chữ thường/số/gạch dưới, không khoảng trắng")

    if not script.keywords:
        problems.append("thiếu keywords")
    elif script.caption and script.keywords[0].lower() not in script.caption[:100].lower():
        problems.append(
            f"từ khoá chính {script.keywords[0]!r} không nằm trong 100 ký tự đầu của caption"
        )
    return problems


async def write_script(
    topic: str,
    *,
    duration_sec: int = 45,
    model: str | None = None,
    max_retry: int = 1,
) -> Script:
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

    options = ClaudeAgentOptions(
        system_prompt=_system_prompt(duration_sec),
        # Không tool: đây là việc viết, không phải việc tra. Cho tool vào chỉ làm
        # agent đi đọc file lung tung và tốn vòng.
        allowed_tools=[],
        # KHÔNG đặt max_turns=1: SDK coi lượt trả lời cuối là chạm trần và ném
        # "Reached maximum number of turns (1)" ngay cả khi agent đã trả lời
        # xong đúng ý. Chặn vòng lặp bằng `allowed_tools=[]` (không có tool thì
        # không có gì để lặp), còn max_turns chỉ là lưới an toàn.
        max_turns=4,
        **({"model": model} if model else {}),
    )

    prompt = f"Viết kịch bản cho chủ đề: {topic}"
    last_problems: list[str] = []

    for attempt in range(max_retry + 1):
        text = ""
        async for msg in query(prompt=prompt, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        text += block.text

        data = _extract_json(text)
        script = Script.from_dict(data, topic=topic)
        problems = _check(script)
        if not problems:
            return script
        last_problems = problems
        if attempt < max_retry:
            # Nói đúng lỗi, không nói "viết lại cho hay hơn" — sửa mù thì vòng
            # sau hỏng chỗ khác.
            prompt = (
                f"Kịch bản vừa rồi vi phạm ràng buộc kỹ thuật:\n"
                + "\n".join(f"- {p}" for p in problems)
                + "\n\nSửa đúng những chỗ đó, giữ nguyên phần còn lại. Trả lại JSON đầy đủ."
            )

    raise ValueError(
        "kịch bản vẫn vi phạm ràng buộc sau khi thử lại:\n"
        + "\n".join(f"  - {p}" for p in last_problems)
    )


def write_script_sync(topic: str, **kw) -> Script:
    return asyncio.run(write_script(topic, **kw))


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="chủ đề → script.json")
    ap.add_argument("topic")
    ap.add_argument("--duration", type=int, default=45)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--model", default=None)
    a = ap.parse_args(argv)

    script = write_script_sync(a.topic, duration_sec=a.duration, model=a.model)
    out = a.out or REPO_ROOT / "out" / "script.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(script.to_json() + "\n", encoding="utf-8")

    print(f"✓ {out}")
    print(f"  hook: {script.hook}")
    for s in script.sections:
        print(f"       {s}")
    print(f"  cta : {script.cta}")
    print(f"  {len(script.shots)} shot · {sum(s.duration_sec for s in script.shots):.0f}s")
    print(f"  caption: {script.caption}")
    print(f"  hashtags: {' '.join('#' + h for h in script.hashtags)}")
    print(f"  keywords: {', '.join(script.keywords)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
