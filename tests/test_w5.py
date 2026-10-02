"""W5 (2026-10-02): thống kê approve rate + giờ chạy đêm."""
from create_video.web import stats


def _v(i, dec, pillar="cong_cu", voice="tony"):
    return {"id": f"v{i}", "created_at": f"2026-10-0{i}", "pillar": pillar, "voice": voice, "hook_type": "con_so_soc",
            "review": {"decision": dec}, "qc": {}}


def test_approve_rate_va_nhom_yeu():
    s = stats.summary([_v(1, "post"), _v(2, "drop"), _v(3, "post"), _v(4, None)], {"tony": "Giọng Tony"})
    assert s["overall"] == {"n": 3, "post": 2, "rate": 2 / 3, "weak": True}
    assert s["rolling"] == [1.0, 0.5, 2 / 3]
    assert s["by_voice"][0]["name"] == "Giọng Tony" and s["by_hook"][0]["name"] == "Con số sốc"
    assert s["corr_t3"] is None          # < 20 video → không báo tương quan


def test_spearman_ci():
    rho, lo, hi = stats._spearman([1, 2, 3, 4, 5, 6], [2, 1, 4, 3, 6, 5])
    assert 0.7 < rho < 0.9 and lo < rho < hi


def test_khung_dem(monkeypatch):
    from create_video.web import worker
    monkeypatch.setattr(worker, "_night", lambda: {"enabled": True, "start": 23, "end": 6})
    import time
    t = time.mktime((2026, 10, 2, 23, 30, 0, 0, 0, -1))
    assert worker.in_night(t) and worker.in_night(t + 4 * 3600) and not worker.in_night(t - 6 * 3600)
