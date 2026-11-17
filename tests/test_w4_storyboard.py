"""W4 (UPGRADE-PLAN 2026-11-17): beats trong kịch bản, bước bấm không nguồn, router dùng beats, stock xếp theo hành động,
seed theo video, trọng tài thấy đề bài."""
from create_video.agents import scriptwriter as SW
from create_video.agents.scriptwriter import Script, Shot
from create_video.visual import router, stock


def _script(**kw):
    base = dict(topic="t", hook="Câu mở", sections=["Câu một", "Câu hai"], cta="Câu kết")
    base.update(kw)
    return Script(**base)


def test_doc_beats_va_script_cu_khong_beats():
    d = {"hook": "a", "sections": ["b"], "cta": "c", "shots": [],
         "beats": [{"line": 0, "purpose": "hook", "visual": {"subject": "cup", "action": "", "shot": "close"}}]}
    assert Script.from_dict(d).beats[0]["visual"]["shot"] == "close"
    d.pop("beats")
    assert Script.from_dict(d).beats == []


def test_schema_llm_co_beats():
    assert "beats" in SW._script_model().model_json_schema()["properties"]


def test_beat_lien_nhau_trung_chu_the_va_co_canh():
    b = lambda line, subj, shot, purpose="value": {"line": line, "purpose": purpose,  # noqa: E731
                                                   "visual": {"subject": subj, "action": "", "shot": shot}}
    s = _script(beats=[b(0, "white vinegar bottle", "close"), b(1, "White vinegar  bottle", "close"), b(2, "x", "wide")])
    assert any("cùng chủ thể" in p for p in SW._check_beats(s))
    s.beats[1]["visual"]["shot"] = "wide"
    assert not SW._check_beats(s)
    assert SW._check_beats(_script()) == []          # không beats → không kiểm


def test_canh_bao_khong_dung_anh_ai():
    s = _script(shots=[Shot(prompt="bleach bottle", kind="image", line=2)],
                beats=[{"line": 2, "purpose": "warning", "visual": {"subject": "bleach", "action": "", "shot": "close"}}])
    assert any("cảnh báo" in p for p in SW._check_beats(s))


BRIEF = "ĐỀ BÀI: từ 15/11 ngân hàng phải cho khách tạm dừng quyền chuyển tiền của AI; hạn mức do khách đặt."


def _list_script(items):
    return _script(shots=[Shot(prompt="phone", kind="list", line=1,
                               list={"title": "Cách tắt", "items": [{"text": t} for t in items]})])


def test_buoc_bam_khong_nguon_bi_bat_va_bo():
    s = _list_script(["Mở app, vào Cài đặt", "Bấm Tạm dừng quyền AI", "Đặt hạn mức mỗi ngày"])
    bad = SW.ui_unverified(s, BRIEF)
    assert [lab for _, _, lab in bad] == ["Cài đặt", "Tạm dừng quyền AI"]
    done = SW._autofix_ui(s, BRIEF)
    assert done and [it["text"] for it in s.shots[0].list["items"]] == ["Đặt hạn mức mỗi ngày"]


def test_buoc_bam_co_trong_de_bai_thi_giu():
    s = _list_script(["Vào «Tạm dừng quyền chuyển tiền»"])
    assert SW.ui_unverified(s, BRIEF.replace("tạm dừng quyền chuyển tiền", "Tạm dừng quyền chuyển tiền")) == []
    assert SW.ui_unverified(s, "") == []              # không có đề bài → không kiểm được, không đoán


def test_the_toan_buoc_bia_thanh_anh():
    s = _list_script(["Bấm Tạm dừng quyền AI"])
    SW._autofix_ui(s, BRIEF)
    assert s.shots[0].kind == "image" and s.shots[0].list is None


def test_router_dung_beat():
    shots = [Shot(prompt="woman folding a jacket", kind="image", line=0),
             Shot(prompt="pour vinegar", kind="stock", line=1, query="vinegar washing machine")]
    beats = [{"line": 0, "purpose": "hook", "visual": {"subject": "jacket", "action": "", "shot": "close"}},
             {"line": 1, "purpose": "step", "visual": {"subject": "vinegar", "action": "pouring", "shot": "close"}}]
    v = router.plan(shots, [[0], [1]], [0, 1], beats)
    assert v[0].prompt.endswith("close-up shot")
    assert v[1].kind == "stock" and v[1].data["action"] == "pouring"
    assert router.plan(shots, [[0], [1]], [0, 1])[0].prompt == "woman folding a jacket"   # không beats → như cũ


def test_stock_xep_theo_hanh_dong_khong_noi_nguong():
    a = "woman-pouring-vinegar-into-washing-machine"
    b = "vinegar-bottle-on-washing-machine"
    q = "vinegar washing machine"
    assert stock.relevance(q, a) == stock.relevance(q, b)        # ngưỡng giữ nguyên
    assert stock.action_bonus("pouring", a) == 1 and stock.action_bonus("pouring", b) == 0
    assert stock.action_bonus("", a) == 0


def test_seed_theo_video():
    from create_video.pipeline import video_seed

    assert video_seed("1116-a") == video_seed("1116-a")
    assert video_seed("1116-a") != video_seed("1116-b")


def test_trong_tai_thay_de_bai(monkeypatch):
    from create_video.agents import angles as A

    seen = {}

    class _Ang:
        def __init__(self, i):
            self.format, self.hook, self.hook_text, self.angle, self.why_finish = "f", f"hook {i}", "hai từ", "g", "w"
            self.probability = 0.5

        def model_dump(self):
            return {"format": "f", "hook": self.hook}

    class _Out:
        angles = [_Ang(0), _Ang(1)]

    def fake_run_role(role, prompt, *a, **k):
        seen[role] = prompt
        if role == "angle_gen":
            return _Out()
        return A.JudgeOut(verdicts=[])

    monkeypatch.setattr(A, "formats", lambda: {"f": {"desc": "d"}})
    monkeypatch.setattr(A, "_ok", lambda a, f: None)
    monkeypatch.setattr(A, "recent_formats", lambda: [])
    monkeypatch.setattr(A, "recent_end_styles", lambda: [])
    monkeypatch.setattr(A, "pick_end_style", lambda r: "")
    monkeypatch.setattr(A, "create_model", lambda *a, **k: object, raising=False)
    import create_video.team as T

    monkeypatch.setattr(T, "run_role", fake_run_role)
    A.choose_angle("chủ đề", "SỰ THẬT: hạn mức 5 triệu")
    assert "hạn mức 5 triệu" in seen["angle_judge"]


def test_gop_y_khong_goi_them_llm_va_tu_va(monkeypatch):
    """Góp ý W4/W5 (beats trùng, bước bấm không nguồn, thiếu demo) KHÔNG tự kích hoạt lượt sửa — code tự vá khi xong."""
    import asyncio
    import json

    import create_video.team as team

    monkeypatch.setenv("CV_CHANNEL", "ai")
    calls = []
    d = json.loads(_script(pillar="repo_hay", shots=[
        Shot(prompt="p", kind="list", line=1, list={"items": [{"text": "Bấm Tạm dừng quyền AI"}, {"text": "Đặt hạn mức"}]}),
        Shot(prompt="p", kind="screenshot", line=2, url="https://github.com/a/b"),
        Shot(prompt="p", kind="demo", line=3, url="https://github.com/a/b")],
        beats=[{"line": 0, "purpose": "hook", "visual": {"subject": "cup", "action": "", "shot": "close"}},
               {"line": 1, "purpose": "value", "visual": {"subject": "cup", "action": "", "shot": "close"}}]).to_json())
    d.pop("topic")

    class _O:
        def model_dump(self, **kw):
            return dict(d)

    async def fake(role, prompt, *a, **k):
        calls.append(role)
        return _O()

    monkeypatch.setattr(team, "arun_role", fake)
    monkeypatch.setattr(SW, "_check", lambda s: [])
    monkeypatch.setattr(SW, "_check_length", lambda s, n: [])
    monkeypatch.setattr(SW, "_check_speech", lambda s: [])
    out = asyncio.run(SW._write("t", "Viết kịch bản theo ĐỀ BÀI.\n\nhạn mức · https://github.com/a/b", role="scriptwriter",
                                duration_sec=40, model=None, max_retry=1, state=None, artifact=None))
    assert calls == ["scriptwriter"]
    assert [it["text"] for it in out.shots[0].list["items"]] == ["Đặt hạn mức"]
    assert out.shots[1].kind == "demo"
