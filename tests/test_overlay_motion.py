"""P3b.S1 — ba lỗi dựng tìm thấy trong audit 2026-10-01 (research/08 §1)."""

from create_video.agents.scriptwriter import Script, Shot, _check
from create_video.spec.build import Line, _motion_preset, _timed_overlays
from create_video.voice.echo import LineSpan


def _spans(*pairs):
    return [LineSpan(text="x", start=a, end=b) for a, b in pairs]


def test_overlay_theo_dung_cau_khong_theo_shot():
    # demo-02: "14 GB" thuộc câu thứ 3 nhưng hiện ở shot phủ câu 2 → giờ phải
    # bắt đầu đúng lúc câu chứa nó bắt đầu.
    lines = [Line("a"), Line("b", overlay="16-bit"), Line("c", overlay="14 GB")]
    spans = _spans((0, 2), (2.3, 5.0), (5.3, 7.0))
    ov = _timed_overlays(lines, spans, total=7.5)
    assert [(o["text"], o["start_sec"]) for o in ov] == [("16-bit", 2.3), ("14 GB", 5.3)]


def test_hai_overlay_lien_nhau_khong_de_nhau():
    lines = [Line("a", overlay="A"), Line("b", overlay="B")]
    spans = _spans((0, 0.8), (1.0, 3.0))  # câu đầu ngắn → min 1,8s sẽ lấn câu sau
    a, b = _timed_overlays(lines, spans, total=3.0)
    assert a["end_sec"] <= b["start_sec"]


def test_overlay_khong_vuot_do_dai_video():
    ov = _timed_overlays([Line("a", overlay="X")], _spans((9.5, 9.9)), total=10.0)
    assert ov[0]["end_sec"] <= 10.0


def test_moi_kieu_chuyen_dong_du_scale_phu_kin_khung():
    # Pan p% cần scale ≥ 1 + 2p/100, thiếu là lộ dải nền đen ở mép.
    for k in range(8):
        m = _motion_preset(k, 1.0, 1.15)
        for st in (m["from"], m["to"]):
            pan = max(abs(st["x_pct"]), abs(st["y_pct"]))
            assert st["scale"] >= 1 + 2 * pan / 100, (k, st)


def _script(**kw):
    base = dict(
        topic="t", hook="Ai cũng bảo phải có card khủng.",
        sections=["Card sáu GB vẫn chạy được LLM nhé."],
        cta="Card bạn mấy GB thì comment đi.",
        shots=[Shot(prompt="p", duration_sec=5)],
        caption="LLM trên card cũ", hashtags=["a", "b", "c"], keywords=["LLM"],
    )
    base.update(kw)
    return Script(**base)


def test_check_bat_overlay_tro_ra_ngoai_cau():
    probs = _check(_script(overlays=[{"line": 9, "text": "6GB"}]))
    assert any("ngoài khoảng" in p for p in probs)


def test_check_bat_hai_overlay_mot_cau():
    probs = _check(_script(overlays=[{"line": 1, "text": "6GB"}, {"line": 1, "text": "LLM"}]))
    assert any("hơn một overlay" in p for p in probs)


def test_from_dict_doc_duoc_script_cu():
    d = {"hook": "h", "sections": [], "cta": "", "shots": [
        {"prompt": "p", "duration_sec": 3, "overlay": "6GB"}]}
    s = Script.from_dict(d, topic="t")
    assert s.shots[0].overlay == "6GB" and s.overlays == []


def test_cat_cau_khi_aligner_tach_token_khac():
    from create_video.spec.captions import split_spoken_by_lines
    from create_video.voice.base import Word

    lines = ["mô hình gpt năm chạy nhanh.", "rất tốt."]
    # aligner tách "gpt" thành "g p t" → thừa 2 token so với tách khoảng trắng
    toks = "mô hình g p t năm chạy nhanh rất tốt".split()
    words = [Word(w=t, start=i * 0.2, end=i * 0.2 + 0.15) for i, t in enumerate(toks)]
    a, b = split_spoken_by_lines(words, lines)
    assert [w.w for w in b] == ["rất", "tốt"]
    assert len(a) == 8


def test_tu_dien_phat_am_chi_thay_nguyen_tu():
    from create_video.voice.echo import apply_pronounce

    t = {"dataset": "đa ta sét"}
    assert apply_pronounce("Dataset mới, datasets cũ", t) == "đa ta sét mới, datasets cũ"
    assert apply_pronounce("open-dataset", t) == "open-dataset"
