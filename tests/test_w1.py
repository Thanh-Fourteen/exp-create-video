"""W1 (2026-10-02): tiến độ 8 bước từ state.json + cổng duyệt."""
import json

from create_video.progress import snapshot, step_of

H = {"research": 100, "script": 100, "approve": 0, "voice": 100, "visual": 100, "music": 100, "render": 100, "qc": 100}


def _state(tmp_path, stage, stages):
    (tmp_path / "state.json").write_text(json.dumps({"stage": stage, "stages": stages}), encoding="utf-8")


def test_step_of():
    assert step_of("images") == "visual" and step_of("qc1_patch") == "qc" and step_of("qc0_t4") == "qc"
    assert step_of("awaiting_approval") is None


def test_cho_duyet(tmp_path):
    _state(tmp_path, "awaiting_approval", {"research": {"status": "done"}, "script": {"status": "done"}})
    s = snapshot(tmp_path, hist=H)
    assert s["awaiting_approval"] and s["eta_sec"] is None
    assert [x["status"] for x in s["steps"]][:3] == ["done", "done", "running"]
    assert s["percent"] == 29   # 200 / 700


def test_dang_dung_hinh(tmp_path):
    _state(tmp_path, "images", {"research": {"status": "done"}, "script": {"status": "done"},
                                "tts": {"status": "done"}, "images": {"status": "running", "started_at": ""}})
    s = snapshot(tmp_path, hist=H)
    assert s["current"] == "visual" and dict((x["key"], x["status"]) for x in s["steps"])["approve"] == "done"
    assert s["eta_sec"] == 400


def test_xong_khi_co_result(tmp_path):
    _state(tmp_path, "qc0_t4", {"qc0_t4": {"status": "running"}})
    (tmp_path / "result.json").write_text("{}", encoding="utf-8")
    assert snapshot(tmp_path, hist=H)["percent"] == 100
