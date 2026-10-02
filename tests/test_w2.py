"""W2 (2026-10-02): hàng đợi SQLite — nhận job nguyên tử, cổng duyệt, huỷ, nối tiếp sau crash."""
import time

from create_video.web import db


def test_vong_doi_job(tmp_path):
    p = tmp_path / "x.db"
    db.init(p)
    j = db.add_job("Gemini miễn phí", voice="tony", gate=True, path=p)
    assert j["state"] == "queued" and j["phase"] == "script"
    c = db.claim_next(p)
    assert c["id"] == j["id"] and c["state"] == "running" and db.claim_next(p) is None
    db.update_job(j["id"], state="awaiting_approval", path=p)
    assert db.approve(j["id"], p) and not db.approve(j["id"], p)
    j2 = db.get_job(j["id"], p)
    assert j2["state"] == "queued" and j2["phase"] == "full" and j2["approved"] == 1


def test_khong_cong_duyet_chay_thang_full(tmp_path):
    p = tmp_path / "x.db"
    db.init(p)
    assert db.add_job("x", gate=False, path=p)["phase"] == "full"


def test_huy(tmp_path):
    p = tmp_path / "x.db"
    db.init(p)
    a = db.add_job("a", path=p)
    assert db.request_cancel(a["id"], p) == "cancelled"
    b = db.add_job("b", path=p)
    db.claim_next(p)
    assert db.request_cancel(b["id"], p) == "cancelling" and db.get_job(b["id"], p)["cancel_requested"] == 1


def test_noi_tiep_sau_crash(tmp_path):
    p = tmp_path / "x.db"
    db.init(p)
    a = db.add_job("a", path=p)
    db.claim_next(p)
    db.update_job(a["id"], heartbeat_at=time.time() - 999, path=p)
    assert db.recover_stale(120, p) == [a["id"]] and db.get_job(a["id"], p)["state"] == "queued"


def test_bao_mot_lan(tmp_path):
    p = tmp_path / "x.db"
    db.init(p)
    a = db.add_job("a", path=p)
    assert db.mark_notified(a["id"], "done", p) and not db.mark_notified(a["id"], "done", p)
