"""W6 (UPGRADE-PLAN 2026-11-17): nghe lại cả bài khi đọc cả đoạn; pop/nảy thẻ số đúng lúc đọc con số."""
from pathlib import Path

from create_video.voice.vieneu_local import VieneuLocalBackend as V


def _b():
    return V.__new__(V)


def test_cham_ban_doc():
    b = _b()
    ref_h, ref = "AI trong app ngân hàng", "AI trong app ngân hàng giờ được tự chuyển tiền mỗi ngày"
    good = b.judge_take("ai trong app ngân hàng giờ được tự chuyển tiền mỗi ngày", ref_h, ref)
    assert good["ok"] and good["body"] == 1.0
    rep = b.judge_take("ai ai trong app ngân hàng giờ được tự chuyển tiền mỗi ngày", ref_h, ref)
    assert not rep["ok"] and rep["repeat"]
    bad = b.judge_take("ai trong app ngân hàng cái gì đó hoàn toàn khác hẳn", ref_h, ref)
    assert not bad["ok"] and bad["body"] < V.BODY_MIN


def test_chon_ban_tot_nhat_khi_ban_dau_hong(monkeypatch, tmp_path):
    b = _b()
    b.seed, b._hook_ref, b.HOOK_TRIES = 0, "AI trong app", 3
    heard_by_seed = {0: "ai ai trong app tự chuyển tiền", 7919: "ai trong app tự chuyển tiền",
                     15838: "ai trong app tự chuyển"}

    def fake_super(self, text, n_sent=1):
        w = tmp_path / f"{self.seed}.wav"
        w.write_bytes(b"")
        return (w, text, 24000, 1.0)

    monkeypatch.setattr(V.__mro__[1], "_synth_checked", fake_super)
    monkeypatch.setattr(V, "_asr_clip", lambda self, w: w)
    monkeypatch.setattr(V, "_asr_batch", lambda self, ws: {str(w): heard_by_seed[int(Path(w).stem)] for w in ws})
    out = b._synth_checked("AI trong app tự chuyển tiền", n_sent=3)
    assert Path(out[0]).stem == "7919"
    assert b.seed == 0 and len(b.asr_log) == 3


def test_ban_dau_dat_thi_khong_doc_them(monkeypatch, tmp_path):
    b = _b()
    b.seed, b._hook_ref = 0, "AI trong app"
    calls = []

    def fake_super(self, text, n_sent=1):
        calls.append(self.seed)
        w = tmp_path / f"{self.seed}.wav"
        w.write_bytes(b"")
        return (w, text, 24000, 1.0)

    monkeypatch.setattr(V.__mro__[1], "_synth_checked", fake_super)
    monkeypatch.setattr(V, "_asr_clip", lambda self, w: w)
    monkeypatch.setattr(V, "_asr_batch", lambda self, ws: {str(w): "ai trong app tự chuyển tiền" for w in ws})
    b._synth_checked("AI trong app tự chuyển tiền", n_sent=3)
    assert calls == [0]


def test_cue_the_so_dung_tu_nhan():
    from create_video.spec.build import add_cues

    shots = [{"start_sec": 0.0, "end_sec": 3.0, "asset": {"kind": "stat"}},
             {"start_sec": 3.0, "end_sec": 6.0, "asset": {"kind": "stat"}},
             {"start_sec": 6.0, "end_sec": 9.0, "asset": {"kind": "chart"}}]
    add_cues(shots, [1.0, 4.4, 5.0, 6.1])
    assert "cues" not in shots[0]                 # shot 0 = thumbnail
    assert shots[1]["cues"] == [{"at_sec": 4.4, "type": "counter"}]
    assert "cues" not in shots[2]                 # 6,1 sát đầu shot (< 0,3s) → nhịp cũ


def test_pop_theo_cue():
    from create_video.sound.design import sfx_events

    spec = {"shots": [{"start_sec": 0.0, "end_sec": 6.0, "asset": {"kind": "image"}},
                      {"start_sec": 6.0, "end_sec": 10.0, "asset": {"kind": "stat"},
                       "cues": [{"at_sec": 7.4, "type": "counter"}]}]}
    assert (7.4, "pop") in sfx_events(spec)


def test_so_doc_bang_chu():
    from create_video.spec.build import number_times

    caps = [{"words": [{"w": "tối", "start": 1.0, "end": 1.2}, {"w": "đa", "start": 1.2, "end": 1.4},
                       {"w": "trăm", "start": 1.4, "end": 1.6}, {"w": "triệu", "start": 1.6, "end": 1.9},
                       {"w": "một", "start": 2.0, "end": 2.1}, {"w": "ngày.", "start": 2.1, "end": 2.4},
                       {"w": "GPT-5", "start": 3.0, "end": 3.4}]}]
    assert number_times(caps) == [1.35, 2.95]          # "một ngày" (mạo từ) không phải số


def test_schema_14_nhan_truong_moi_dung_cap():
    import json

    import jsonschema

    from create_video.spec.build import SPEC_VERSION
    from create_video.spec.validate import SCHEMA_PATH

    sch = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    item = {"definitions": sch.get("definitions", {}), **sch["properties"]["shots"]["items"]}
    shot = {"id": "s2", "start_sec": 3.0, "end_sec": 6.0, "asset": {"kind": "video", "path": "demo/01.mp4"},
            "motion": {"type": "ken_burns", "segments": [
                {"from": {"scale": 1.0}, "to": {"scale": 1.1}, "start_frac": 0.0},
                {"from": {"scale": 1.3}, "to": {"scale": 1.35}, "start_frac": 0.4}]},
            "label": {"text": "Demo thật · github.com/a/b", "kind": "demo"},
            "cues": [{"at_sec": 4.2, "type": "counter"}]}
    jsonschema.validate(shot, item)
    assert SPEC_VERSION == "1.4"
    assert "cues" not in json.dumps(sch["properties"]["shots"]["items"]["properties"]["asset"])
