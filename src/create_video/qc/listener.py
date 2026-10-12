"""Người nghe thử (2026-10-08, research/25-kich-ban-de-hieu.md): kịch bản có HIỂU được khi nghe MỘT lần không?

    python -m create_video.qc.listener videos/meo/<id>/script.json [...] [--out eval/results/x.jsonl]

Hai vai, tách nhau để người nghe không nhìn thấy "đáp án":
1. `listener` — đóng vai người Việt phổ thông nghe một lần (chỉ có lời đọc, không có hình), kể lại thông điệp chính + việc
   phải làm, chỉ ra cụm KHÔNG HIỂU và chỗ RỐI (trích nguyên văn — code đối chiếu, trích sai bị bỏ).
2. `listen_judge` — có cả kịch bản: ý người nghe kể lại có ĐÚNG ý chính kịch bản muốn nói không, việc phải làm có đúng không.

Đây là proxy LLM (giống T3), KHÔNG phải tầng 1. Chưa kiểm với người thật — xem research/25 §4.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..agents.scriptwriter import Script


class Spot(BaseModel):
    quote: str          # NGUYÊN VĂN trong lời đọc
    why: str            # một câu


class ListenerOut(BaseModel):
    main_message: str           # một câu: video muốn nói gì
    actions: list[str]          # việc người nghe sẽ làm sau khi xem (rỗng nếu không có)
    unclear: list[Spot]         # từ/cụm không hiểu nghĩa hoặc không biết là ai/cái gì
    confusing: list[Spot]       # chỗ mất mạch: không biết "nó/họ/cái đó" là gì, ý trước sau ngược nhau, nhảy chủ đề
    # 2026-10-08 (Tony: "thân thuộc… dễ chịu, bị cuốn hút khi nghe")
    relatable: bool             # thấy đúng chuyện của mình / nhà mình
    off_putting: list[Spot]     # chỗ thấy bị mắng, doạ, giảng đạo, ra lệnh, hoặc giọng xa lạ/khó chịu
    bored: list[Spot]           # chỗ muốn lướt đi
    keep_watching: bool         # nghe hết 3 câu đầu có muốn nghe tiếp tới cuối không


class JudgeOut(BaseModel):
    intended: str               # ý chính kịch bản muốn người xem mang về (một câu)
    message_ok: bool            # người nghe kể lại đúng ý chính
    actions_ok: bool            # việc người nghe định làm đúng việc kịch bản khuyên (không có việc → đúng nếu rỗng)
    why: str


# v3 (2026-10-08, research/probes/kb-de-hieu.md lượt 2): persona theo KHÁN GIẢ CỦA KÊNH (`channel.yaml: audience`) —
# persona cố định "40 tuổi không rành công nghệ" chấm kênh AI như kênh mẹo (không biết ChatGPT do ai làm, CV là gì).
PERSONA_DEFAULT = ("40 tuổi, học hết cấp ba, dùng điện thoại hằng ngày (Zalo, Facebook, TikTok, app ngân hàng) nhưng KHÔNG "
                   "rành công nghệ, không đọc tiếng Anh, không biết tên các công ty nước ngoài trừ Google, Apple, Facebook, "
                   "Samsung, Microsoft")


def persona() -> str:
    from ..channel import current

    aud = (current().raw.get("audience") or "").strip()
    return (f"thuộc đúng nhóm khán giả của kênh này: {aud}. Bạn là người BÌNH THƯỜNG trong nhóm đó — không phải chuyên gia, "
            "không làm IT, không đọc tài liệu tiếng Anh") if aud else PERSONA_DEFAULT


LISTENER_SYS = """Bạn đóng vai MỘT NGƯỜI XEM TIKTOK VIỆT NAM {persona}. Bạn đang lướt TikTok và NGHE lời đọc của một video
đúng MỘT LẦN, tốc độ ~4 từ/giây, không tua lại được. Bạn không nhìn thấy hình.

Trả lời trung thực như người đó — không giả vờ hiểu:
- `main_message`: một câu, video này muốn nói với bạn điều gì (bằng lời của bạn).
- `actions`: những việc bạn sẽ làm sau khi xem (mỗi việc một câu ngắn). Không định làm gì → rỗng.
- `unclear`: từ / cụm / tên mà người như bạn KHÔNG hiểu nghĩa hoặc không biết là ai, là cái gì, khi chỉ nghe một lần.
- `confusing`: chỗ bạn MẤT MẠCH: không biết "nó / họ / cái đó / số đó" chỉ cái gì; câu sau nói ngược câu trước làm bạn
  không biết nên tin câu nào; đang nói chuyện này nhảy sang chuyện khác; nhiều con số quá không nhớ nổi số nào quan trọng.
- `relatable`: bạn có thấy đây là chuyện của chính mình / nhà mình / người quen không (true/false).
- `off_putting`: chỗ bạn thấy KHÓ CHỊU khi nghe: bị mắng, bị doạ, bị giảng đạo, bị ra lệnh, giọng như đọc công văn hay
  như người lạ dạy đời.
- `bored`: chỗ bạn thấy chán, muốn lướt sang video khác.
- `keep_watching`: nghe xong 3 câu đầu, bạn có muốn nghe tiếp tới cuối không (true/false).
`quote` phải CHÉP NGUYÊN VĂN một đoạn trong lời đọc (code đối chiếu). Không có thì để danh sách rỗng — đừng bịa lỗi."""

JUDGE_SYS = """Bạn là biên tập viên. Bạn có KỊCH BẢN đầy đủ của một video TikTok và phần KỂ LẠI của một người nghe phổ thông
vừa nghe video đó một lần. Việc của bạn:
1. `intended`: ý chính kịch bản muốn người xem mang về — một câu, rút từ toàn bộ kịch bản (hook + thân + kết).
2. `message_ok`: người nghe kể lại có ĐÚNG ý chính đó không (cùng ý, khác chữ vẫn được; chỉ nhớ một chi tiết phụ → sai).
3. `actions_ok`: việc người nghe định làm có đúng việc kịch bản khuyên không; làm SAI hướng (vd. định đun lại đồ hộp phồng
   trong khi kịch bản khuyên bỏ) → false. Kịch bản không khuyên việc gì và người nghe cũng không định làm gì → true.
4. `why`: một câu."""


def _norm(s: str) -> str:
    return " ".join(s.lower().replace("…", "...").split())


def _found(quote: str, text: str) -> bool:
    q = _norm(quote).strip(" .,!?\"'")
    return bool(q) and q in _norm(text)


async def alisten(script: "Script", *, model: str | None = None) -> dict:
    from ..team import arun_role

    text = " ".join(script.lines)
    lo = await arun_role("listener", f"LỜI ĐỌC CỦA VIDEO (bạn nghe một lần):\n\n{text}", ListenerOut,
                         system_prompt=LISTENER_SYS.replace("{persona}", persona()), tools=[], max_turns=4, max_budget_usd=1.5, model=model,
                         timeout_sec=300)
    numbered = "\n".join(f"[{i}] {t}" for i, t in enumerate(script.lines))
    jo = await arun_role("listen_judge",
                         f"KỊCH BẢN (chủ đề: {script.topic}):\n{numbered}\n\nNGƯỜI NGHE KỂ LẠI:\n"
                         f"- Thông điệp: {lo.main_message}\n- Sẽ làm: {lo.actions or '(không)'}",
                         JudgeOut, system_prompt=JUDGE_SYS, tools=[], max_turns=4, max_budget_usd=1.5, model=model,
                         timeout_sec=300)
    keep = lambda xs: [x.model_dump() for x in xs if _found(x.quote, text)]   # noqa: E731
    unclear, confusing = keep(lo.unclear), keep(lo.confusing)
    off, bored = keep(lo.off_putting), keep(lo.bored)
    return {"topic": script.topic, "words": len(text.split()), "main_message": lo.main_message, "actions": lo.actions,
            "intended": jo.intended, "message_ok": jo.message_ok, "actions_ok": jo.actions_ok, "judge_why": jo.why,
            "unclear": unclear, "confusing": confusing, "n_issues": len(unclear) + len(confusing),
            "relatable": lo.relatable, "keep_watching": lo.keep_watching, "off_putting": off, "bored": bored,
            "n_appeal_issues": len(off) + len(bored),
            "dropped": (len(lo.unclear) + len(lo.confusing) + len(lo.off_putting) + len(lo.bored)
                        - len(unclear) - len(confusing) - len(off) - len(bored))}


# ── cổng kịch bản (2026-10-08, research/probes/kb-de-hieu.md): chỗ vướng → ghi chú sửa cho scriptwriter ─────────────
GATE_MAX_ISSUES = 4       # ≤ 4 chỗ khó hiểu/mất mạch (mốc "giảm một nửa" của probe, bộ trước trung vị 8)
GATE_MAX_APPEAL = 2       # ≤ 2 chỗ khó chịu/chán (bộ trước trung vị 3,5)


async def alisten_gate(script: "Script", *, model: str | None = None) -> dict:
    """Chỉ vai người nghe (không giám khảo) → {ok, n_issues, n_appeal, notes}. Ghi chú trích nguyên văn để người viết sửa
    đúng câu — critic đề xuất, không quyết định (scriptwriter tự sửa theo luật D1–D18)."""
    from ..team import arun_role

    text = " ".join(script.lines)
    lo = await arun_role("listener", f"LỜI ĐỌC CỦA VIDEO (bạn nghe một lần):\n\n{text}", ListenerOut,
                         system_prompt=LISTENER_SYS.replace("{persona}", persona()), tools=[], max_turns=4,
                         max_budget_usd=1.5, model=model, timeout_sec=300)
    keep = lambda xs: [x for x in xs if _found(x.quote, text)]   # noqa: E731
    issues, appeal = keep(lo.unclear) + keep(lo.confusing), keep(lo.off_putting) + keep(lo.bored)
    lab = {"unclear": "không hiểu", "confusing": "mất mạch", "off_putting": "khó chịu", "bored": "chán, muốn lướt"}
    notes = [f'Người nghe thử ({lab[k]}) ở "{x.quote}": {x.why} → sửa theo luật DỄ HIỂU/THÂN THUỘC (D1–D18), đừng chỉ thay chữ.'
             for k in ("confusing", "unclear", "off_putting", "bored") for x in keep(getattr(lo, k))]
    return {"ok": len(issues) <= GATE_MAX_ISSUES and len(appeal) <= GATE_MAX_APPEAL,
            "n_issues": len(issues), "n_appeal": len(appeal), "notes": notes[:8]}


def listen_gate(script: "Script") -> dict:
    return asyncio.run(alisten_gate(script))


def main(argv: list[str]) -> int:
    from ..agents.scriptwriter import Script
    from ..channel import activate

    out, model = None, None
    if "--model" in argv:   # lượt 3 probe: chấm bằng model KHÁC model đã chạy cổng (chống Goodhart)
        i = argv.index("--model")
        model, argv = argv[i + 1], argv[:i] + argv[i + 2:]
    if "--out" in argv:
        i = argv.index("--out")
        out, argv = Path(argv[i + 1]), argv[:i] + argv[i + 2:]
    for p in map(Path, argv):
        res_p = p.parent / "result.json"
        ch = json.loads(res_p.read_text(encoding="utf-8")).get("channel") if res_p.exists() else None
        activate(ch)   # đặt CV_CHANNEL — persona theo khán giả kênh
        s = Script.from_dict(json.loads(p.read_text(encoding="utf-8")))
        try:
            r = {"path": str(p), "model": model or "mặc định", **asyncio.run(alisten(s, model=model))}
        except Exception as e:   # một kịch bản lỗi không được bỏ cả lượt đo
            r = {"path": str(p), "error": f"{type(e).__name__}: {str(e)[:300]}"}
        line = json.dumps(r, ensure_ascii=False)
        print(line, flush=True)
        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
