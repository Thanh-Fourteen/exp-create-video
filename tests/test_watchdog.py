"""Canh web (2026-10-09): treo 2 lần liền → in ngăn xếp + restart; ổ nghẽn thì KHÔNG restart."""
import json

from create_video.web import watchdog as w


def _run(monkeypatch, tmp_path, alive, busy=0.0):
    calls = []
    monkeypatch.setattr(w, "STATE", tmp_path / "s.json")
    monkeypatch.setattr(w, "ok", lambda: alive)
    monkeypatch.setattr(w, "io_busy", lambda: busy)
    monkeypatch.setattr(w, "web_pid", lambda: None)
    monkeypatch.setattr(w.subprocess, "run", lambda *a, **k: calls.append(a[0]))
    w.main()
    return calls, json.loads((tmp_path / "s.json").read_text())


def test_treo_hai_lan_lien_thi_restart(monkeypatch, tmp_path):
    calls, st = _run(monkeypatch, tmp_path, alive=False)
    assert calls == [] and st["fails"] == 1
    calls, st = _run(monkeypatch, tmp_path, alive=False)
    assert calls and "restart" in calls[0] and st["fails"] == 0


def test_o_nghen_thi_khong_restart(monkeypatch, tmp_path):
    _run(monkeypatch, tmp_path, alive=False, busy=65)
    calls, st = _run(monkeypatch, tmp_path, alive=False, busy=65)
    assert calls == [] and st["fails"] == 2


def test_tra_loi_lai_thi_dat_lai_dem(monkeypatch, tmp_path):
    _run(monkeypatch, tmp_path, alive=False)
    calls, st = _run(monkeypatch, tmp_path, alive=True)
    assert calls == [] and st["fails"] == 0
