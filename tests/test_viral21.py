"""research/21 (2026-10-06): nhịp theo câu, đổi khung trong shot dài, xoay vòng kiểu kết, kiểm lời đọc."""

from create_video.agents.angles import END_STYLES, RECENT_ENDS, pick_end_style
from create_video.agents.scriptwriter import TECH_TOKEN, Script, _check_speech
from create_video.spec.build import _reframe
from create_video.voice.echo import pace_factors

PACE = {"hook": 1.12, "cta": 1.10, "short": 0.92, "short_max_words": 5, "long": 1.06, "long_min_words": 18}


def test_pace_theo_vi_tri_va_do_dai():
    texts = ["hook một hai ba", "Sai rồi.", "câu thường có khoảng mười từ thôi nhé bạn ơi", " ".join(["từ"] * 20), "kết"]
    assert pace_factors(texts, {**PACE, "normalize": False}) == [1.12, 0.92, 1.0, 1.06, 1.10]
    f = pace_factors(texts, PACE)                                  # chuẩn hoá THÂN BÀI: trung bình theo số từ = 1
    w = [len(t.split()) for t in texts]
    assert abs(sum(a * b for a, b in zip(f[1:-1], w[1:-1])) / sum(w[1:-1]) - 1) < 1e-3
    assert f[0] == 1.12 and f[-1] == 1.10 and f[2] > f[1]       # hook/câu kết giữ tuyệt đối


def test_reframe_chia_shot_dai():
    m = {"type": "ken_burns", "from": {"scale": 1.0}, "to": {"scale": 1.1}}
    assert "segments" not in _reframe(m, 0.0, 3.5, 0)             # ≤ 4s trong 15s đầu → giữ nguyên
    early = _reframe(m, 0.0, 9.0, 0)["segments"]                  # 9s / 4s → 3 khung
    assert len(early) == 3 and early[0]["from"] == {"scale": 1.0}
    assert len(_reframe(m, 20.0, 29.0, 0)["segments"]) == 2       # sau 15s: trần 6s
    for s in early[1:]:                                           # khung cận không lộ mép: scale ≥ 1 + 2|pan|/100
        for st in (s["from"], s["to"]):
            assert st["scale"] >= 1 + 2 * max(abs(st["x_pct"]), abs(st["y_pct"])) / 100
    assert _reframe({"type": "none"}, 0.0, 9.0, 0) == {"type": "none"}


def test_kieu_ket_xoay_du_vong_khong_lap_lien():
    h: list[str] = []
    for _ in range(2 * len(END_STYLES)):
        e = pick_end_style(h[:RECENT_ENDS])
        assert not h or e != h[0]
        h.insert(0, e)
    assert set(h) == set(END_STYLES)


def test_chuoi_ky_thuat_va_chu_bia_chep_hook():
    assert TECH_TOKEN.findall("chạy Qwen3.8-Flash-Next") == ["Qwen3.8-Flash-Next"]
    assert TECH_TOKEN.findall("GPT-5 và bản 3.5") == []           # một dấu gạch/chấm: tên đọc được, không bắt
    s = Script(topic="t", hook="VNeID có thể bị khoá nếu SIM không chính chủ", hook_text="VNeID có thể bị khoá",
               sections=["Mở fast-start-r.bat nhé"], cta="Thế thôi.")
    p = " ".join(_check_speech(s))
    assert "chép lời hook" in p and "fast-start-r.bat" in p


def test_regen_thay_stock_lech_chu_de(tmp_path):
    import json

    from create_video.qc.loop import plan_patches
    from create_video.visual.regen import is_stock, plan

    spec = {"shots": [{"id": "s4", "asset": {"kind": "video", "path": "stock/03.mp4", "alt": "food container lid"}},
                      {"id": "s5", "asset": {"kind": "image", "path": "stock/04.ai.png", "alt": "x"}}]}
    (tmp_path / "video-spec.json").write_text(json.dumps(spec))
    j = plan(tmp_path, ["s4"])[0]
    assert j["img"] == "stock/03.ai.png" and j["prompt"] == "food container lid" and j["stock"]
    assert is_stock(spec["shots"][0]["asset"]) and not is_stock(spec["shots"][1]["asset"])
    t = {"t1": {"blocking": []}, "t3": {"summary": {}}, "t4": {"summary": {}},
         "t2": {"suggestions": [{"shot_id": "s4", "issues": ["topic_mismatch"], "stock": True},
                                {"shot_id": "s9", "issues": ["topic_mismatch"]},          # ảnh AI: luật cũ, không vẽ lại
                                {"shot_id": "s7", "issues": ["garbled_text_in_image"], "stock": True}]}}  # chữ thật
    p = plan_patches({"tiers": t, "blocking": [], "suggestions": []})
    assert p["visual"]["shot_ids"] == ["s4"]


def test_pace_bac_giua():
    cfg = {**PACE, "mid_short": 0.95, "mid_short_max_words": 9, "mid_long": 1.05, "mid_long_min_words": 13}
    t = ["h", " ".join(["a"] * 7), " ".join(["a"] * 11), " ".join(["a"] * 15), "k"]
    assert pace_factors(t, {**cfg, "normalize": False})[1:4] == [0.95, 1.0, 1.05]


def test_tu_va_hinh():
    from create_video.agents.scriptwriter import Shot, _autofix_visual, _card_spans

    long = " ".join(["từ"] * 12)
    s = Script(topic="t", hook="hook có bạn", hook_text="x y z", sections=[long, long, "ngắn thôi"], cta="kết",
               shots=[Shot(prompt="pot on stove", kind="stat", line=1),
                      Shot(prompt="a paper wall calendar on a wall", kind="image", line=3)])
    assert _card_spans(s) == [(0, 2, 24)]   # 12 + 12 từ > 15
    done = _autofix_visual(s)
    assert len(done) == 2
    assert any(sh.line == 2 and sh.kind == "image" and sh.prompt == "pot on stove" for sh in s.shots)
    assert [sh.kind for sh in s.shots if sh.line == 3] == ["stock"]


def test_tu_va_chup_trung_trang():
    from create_video.agents.scriptwriter import Shot, _autofix_visual, _dup_screens

    u = "https://example.com/a"
    s = Script(topic="t", hook="hook có bạn", hook_text="x y z", sections=["a b c d e f", "g h i j k l"], cta="kết",
               shots=[Shot(prompt="laptop on desk", kind="screenshot", line=1, url=u),
                      Shot(prompt="phone on table", kind="screenshot", line=2, url=u)])
    assert _dup_screens(s) == [1]
    _autofix_visual(s)
    assert s.shots[1].kind == "image" and _dup_screens(s) == []
