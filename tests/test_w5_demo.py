"""W5 (UPGRADE-PLAN 2026-11-17): demoability, nhãn Demo thật, demo lặp URL chạy tiếp, license vào nguồn."""
import json

from create_video.visual import demo as D


def test_demoability(monkeypatch):
    monkeypatch.setattr(D, "repo_media", lambda r: ("https://raw.githubusercontent.com/a/b/main/x.gif", "MIT")
                        if r == "a/b" else None)
    assert D.demoability("xem https://github.com/a/b nhé") == "repo_media"
    assert D.demoability("https://github.com/c/d") == "page"
    assert D.demoability("https://example.com/tool") == "page"
    assert D.demoability("không có link") == ""

    def boom(r):
        raise OSError("mạng")
    monkeypatch.setattr(D, "repo_media", boom)
    assert D.demoability("https://github.com/a/b") == "page"


def test_nhan_demo_ngan_gon():
    assert D.label_text("https://github.com/localsend/localsend/tree/main") == "Demo thật · github.com/localsend/localsend"
    assert D.label_text("https://github.com/a/b", "scroll") == "Trang thật · github.com/a/b"
    assert len(D.label_text("https://www.example.com/" + "x" * 80 + "/y")) <= 48


def test_nhan_vao_shot_khong_vao_asset(monkeypatch):
    from create_video.spec import build as B
    from create_video.voice.echo import LineSpan

    monkeypatch.setattr(B, "_layout_on", lambda: True)
    spans = [LineSpan(text="a", start=0.0, end=3.0), LineSpan(text="b", start=3.0, end=6.0)]
    style = {"motion": {"shot_duration_sec": [3, 7], "ken_burns": {"zoom_range": [1.0, 1.1]},
                        "transition": {"accent": "fade", "duration_frames": 6, "accent_every": 3}}}
    ev = {1: {"kind": "video", "path": "demo/01.mp4", "label": {"text": "Demo thật · github.com/a/b", "kind": "demo"}}}
    shots = B._plan_shots(spans, 6.0, [], style, "#000", evidence=ev, breaks={1})
    assert shots[-1]["label"]["kind"] == "demo" and "label" not in shots[-1]["asset"]
    assert "label" not in shots[0]


def test_demo_lan_hai_chay_tiep(monkeypatch, tmp_path):
    calls = []
    src = tmp_path / "c.mp4"
    src.write_bytes(b"x")
    monkeypatch.setattr(D, "CACHE", tmp_path)
    monkeypatch.setattr(D, "_key", lambda u: "k")
    (tmp_path / "k.mp4").write_bytes(b"x")
    (tmp_path / "k.json").write_text(json.dumps({"url": "u", "ok": True, "path": str(tmp_path / "k.mp4"),
                                                 "source": "scroll"}))
    monkeypatch.setattr(D, "_rotate", lambda s, d, off: calls.append(off) or d.write_bytes(b"y"))
    assert D.make("u", tmp_path / "o1.mp4").ok and calls == []
    assert D.make("u", tmp_path / "o2.mp4", offset_sec=4.2).ok and calls == [4.2]


def test_goi_y_uu_tien_y_tuong_co_demo():
    from create_video.channel import get
    from create_video.team.idea_gen import DEMO_MARK
    from create_video.team.idea_scout import suggest

    ch = get("ai")
    p = next(iter(ch.pillars))
    rows = {"i1": {"idea_id": "i1", "title": "Ý tưởng không demo về máy in", "pillar": p, "source": "may", "note": "x",
                   "updated_at": 2},
            "i2": {"idea_id": "i2", "title": "Ý tưởng có demo về ghép ảnh", "pillar": p, "source": "may",
                   "note": DEMO_MARK + "y", "updated_at": 1}}
    out = [s["title"] for s in suggest(ch, 40, rows=rows, videos=[], taken=[]) if s["pillar"] == p]
    assert out.index("Ý tưởng có demo về ghép ảnh") < out.index("Ý tưởng không demo về máy in")


def test_kich_ban_repo_can_hai_demo(monkeypatch):
    from create_video.agents import scriptwriter as SW
    from create_video.agents.scriptwriter import Script, Shot

    monkeypatch.setenv("CV_CHANNEL", "ai")
    if True:
        s = Script(topic="t", hook="h", sections=["a"], cta="c", pillar="repo_hay",
                   shots=[Shot(prompt="p", kind="demo", line=1, url="https://github.com/a/b")])
        assert SW._check_demo(s, "ĐỀ BÀI: https://github.com/a/b")
        s.shots.append(Shot(prompt="p", kind="demo", line=2, url="https://github.com/a/b"))
        assert SW._check_demo(s, "ĐỀ BÀI: https://github.com/a/b") == []
        s.pillar = "tin_nong"
        s.shots.pop()
        assert SW._check_demo(s, "ĐỀ BÀI: https://github.com/a/b") == []
