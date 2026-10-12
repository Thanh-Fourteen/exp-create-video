"""Rà soát chuỗi đăng 2026-10-10 — mỗi test dựng lại đúng một tình huống reviewer nêu."""
import datetime as dt
import sqlite3

import pytest

from create_video import lich
from create_video import tiktok_post as tp
from create_video.web import db

TZ = lich.TZ


def at(d, h, m=0):
    return dt.datetime(2026, 10, d, h, m, tzinfo=TZ).timestamp()


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "x.db")
    db.init()
    conf = {"slots": ["08:30", "12:00", "17:30", "20:00"], "per_day": 4, "min_gap_hours": 2, "mode": "automatic",
            "order": "oldest", "auto": True}
    monkeypatch.setattr(lich, "cfg", lambda cid: dict(conf))
    vids = []
    monkeypatch.setattr("create_video.web.library.list_videos", lambda: vids)
    monkeypatch.setattr("create_video.paths.find_web_video", lambda vid: tmp_path / vid)
    monkeypatch.setattr(tp, "PUB_DIR", tmp_path / "pub")
    monkeypatch.setattr(tp, "sync_review", lambda vid, r=None: None)
    return {"vids": vids, "tmp": tmp_path}


def ok_post(calls):
    def f(vid, scheduling="automatic"):
        calls.append(vid)
        return {"post_id": f"p-{vid}-{len(calls)}", "status": "sending", "pub_file": "f.mp4"}
    return f


def test_bam_dang_hai_lan_chi_mot_lan_gui(env):
    assert db.claim_post("v1") is True
    assert db.claim_post("v1") is False                     # lần bấm thứ 2 / timer cùng lúc: thua


def test_dang_tay_huy_lich_thi_timer_khong_gui(env, monkeypatch):
    calls = []
    monkeypatch.setattr(tp, "post_video", ok_post(calls))
    db.set_schedule("v1", "meo", at(10, 17, 30))
    assert db.claim_post("v1")                               # nút Đăng tay giành trước…
    db.cancel_schedule_if("v1", "đã bấm Đăng tay")           # …rồi huỷ lịch
    lich.tick(at(10, 17, 30))
    assert calls == []                                       # timer không gửi lần 2


def test_timer_gianh_lich_truoc_thi_nut_khong_gui(env, monkeypatch):
    db.set_schedule("v1", "meo", at(10, 17, 30))
    assert db.claim_schedule("v1", "automatic")
    assert db.claim_post("v1") and not db.claim_post("v1")


def test_loi_mo_ho_khong_tu_thu_lai_va_khoa_video(env, monkeypatch):
    calls = []

    def timeout(vid, scheduling="automatic"):
        calls.append(vid)
        raise tp.PostError("Buffer không trả lời kịp (TimeoutError) — có thể bài ĐÃ tạo, kiểm Buffer trước")
    monkeypatch.setattr(tp, "post_video", timeout)
    db.set_schedule("v1", "meo", at(10, 17, 30))
    lich.tick(at(10, 17, 30))
    lich.tick(at(10, 17, 31))
    assert calls == ["v1"]                                   # KHÔNG thử lại (có thể đã đăng)
    assert db.get_schedule("v1")["status"] == "failed" and db.get_review("v1")["buffer_status"] == "error"
    env["vids"].append({"id": "v1", "channel": "meo", "review": db.get_review("v1"), "created_at": "x"})
    assert lich.backlog("meo") == []                         # không tự xếp lịch lại


def test_loi_chac_chan_thu_lai_toi_het_20_phut(env, monkeypatch):
    n = {"i": 0}

    def flaky(vid, scheduling="automatic"):
        n["i"] += 1
        if n["i"] <= 8:                                      # Funnel mất 8 phút mới thông — vượt 5 lần cũ
            raise tp.PostError("Buffer từ chối (InvalidInputError): Video could not be read from its URL.")
        return {"post_id": "p", "status": "sending", "pub_file": "f"}
    monkeypatch.setattr(tp, "post_video", flaky)
    monkeypatch.setattr(lich, "_heal_once", lambda log: None)
    db.set_schedule("v1", "meo", at(10, 17, 30))
    for m in range(9):
        lich.tick(at(10, 17, 30 + m))
    assert db.get_review("v1")["buffer_post_id"] == "p"
    db.set_schedule("v2", "meo", at(10, 8, 30))
    monkeypatch.setattr(tp, "post_video", lambda *a, **k: (_ for _ in ()).throw(
        tp.PostError("InvalidInputError: Video could not be read from its URL.")))
    lich.tick(at(10, 8, 51))                                 # quá 20 phút
    assert db.get_schedule("v2")["status"] in ("missed", "failed")


def test_dang_xong_db_ban_van_ghi_duoc(env, monkeypatch):
    real = db.set_review
    n = {"i": 0}

    def flaky_set(vid, path=None, **f):
        if f.get("buffer_post_id") and n["i"] == 0:
            n["i"] += 1
            raise sqlite3.OperationalError("database is locked")
        return real(vid, path, **f)
    monkeypatch.setattr(db, "set_review", flaky_set)
    monkeypatch.setattr(db.time, "sleep", lambda s: None)
    monkeypatch.setattr(tp, "post_video", ok_post([]))
    db.set_schedule("v1", "meo", at(10, 17, 30))
    lich.tick(at(10, 17, 30))
    assert db.get_review("v1")["buffer_post_id"]               # đã đăng thì phải ghi được post id


def test_luot_gui_bi_ngat_thi_khoa_khong_tu_dang_lai(env):
    assert db.claim_post("v1")                                 # tiến trình chết ngay sau khi giành quyền
    with db.db() as con:
        con.execute("UPDATE reviews SET updated_at=? WHERE video_id='v1'", (at(10, 8, 0),))
    log = {}
    lich._sweep(at(10, 9, 0), log)
    r = db.get_review("v1")
    assert log["stale"] == ["v1"] and r["buffer_status"] == "error" and "KIỂM" in r["buffer_error"]


def test_don_file_cong_khai_bi_sot(env):
    import os
    pub = env["tmp"] / "pub"
    pub.mkdir()
    (pub / "cu.mp4").write_bytes(b"x")
    (pub / "dang-dung.mp4").write_bytes(b"x")
    old = at(10, 6, 0)
    os.utime(pub / "cu.mp4", (old, old))
    os.utime(pub / "dang-dung.mp4", (old, old))
    db.set_review("v1", buffer_post_id="p", buffer_status="sending", pub_file="dang-dung.mp4")
    lich._sweep(at(10, 9, 0), {})
    assert not (pub / "cu.mp4").exists() and (pub / "dang-dung.mp4").exists()


def test_ban_doi_giong_khong_tu_len_lich(env):
    db.add_job("t", kind="revoice", source="v1") if hasattr(db, "add_job") else None
    jid = db.list_jobs(limit=5)[0]["id"]
    db.update_job(jid, video_id="v1-tony2")
    env["vids"].append({"id": "v1-tony2", "channel": "meo", "review": {}, "created_at": "x"})
    assert lich.backlog("meo") == []


def test_bai_bi_xoa_tren_buffer_khong_lam_sap(env, monkeypatch):
    monkeypatch.undo()
    monkeypatch.setattr(db, "DB_PATH", env["tmp"] / "y.db")
    db.init()
    db.set_review("v1", buffer_post_id="p1", buffer_status="sending")
    monkeypatch.setattr(tp, "status", lambda pid: None)
    assert "Buffer" in tp.sync_review("v1") and db.get_review("v1")["buffer_status"] == "error"
    monkeypatch.setattr(tp, "status", lambda pid: (_ for _ in ()).throw(TimeoutError("read timed out")))
    db.set_review("v2", buffer_post_id="p2", buffer_status="sending")
    assert "timed out" in tp.sync_review("v2")


def test_loi_het_gio_ma_bai_da_len_thi_tu_doi_chieu(env, monkeypatch):
    """2026-10-10 20:00: Buffer hết giờ trả lời nhưng bài ĐÃ đăng → khoá đúng, rồi tự hỏi Buffer và ghi 'đã đăng'."""
    db.set_schedule("v1", "meo", at(10, 20, 0))
    db.update_schedule("v1", status="failed", error="Buffer không trả lời kịp — có thể đã đăng")
    db.set_review("v1", buffer_status="error", buffer_error="Buffer không trả lời kịp — KIỂM Buffer/TikTok trước khi đăng lại")
    monkeypatch.setattr(tp, "caption_for", lambda vid: ("ch", "Mùa lũ Trung Bộ: gói giấy tờ trước"))
    monkeypatch.setattr(tp, "find_post", lambda cid, text, since: {"id": "B1", "status": "sent",
                                                                   "externalLink": "https://tiktok.com/@x/video/1"})
    log = {}
    lich._reconcile(at(10, 20, 15), log)
    r = db.get_review("v1")
    assert log["reconciled"] == ["v1"] and r["decision"] == "post" and r["tiktok_url"].endswith("/1")
    assert r["buffer_post_id"] == "B1"


def test_loi_het_gio_ma_chua_co_bai_thi_giu_khoa(env, monkeypatch):
    db.set_schedule("v1", "meo", at(10, 20, 0))
    db.update_schedule("v1", status="failed")
    db.set_review("v1", buffer_status="error", buffer_error="… KIỂM Buffer/TikTok trước khi đăng lại")
    monkeypatch.setattr(tp, "caption_for", lambda vid: ("ch", "x"))
    monkeypatch.setattr(tp, "find_post", lambda *a: None)
    lich._reconcile(at(10, 20, 15), {})
    assert db.get_review("v1")["buffer_status"] == "error" and db.get_schedule("v1")["status"] == "failed"


def test_tim_bai_theo_caption_va_thoi_gian(monkeypatch):
    monkeypatch.setattr(tp, "recent_posts", lambda cid, n=10: [
        {"id": "cu", "text": "Mùa lũ Trung Bộ: gói giấy tờ", "createdAt": "2026-10-09T13:00:00Z"},
        {"id": "moi", "text": "Mùa lũ  Trung Bộ:\ngói giấy tờ", "createdAt": "2026-10-10T13:00:20Z"}])
    assert tp.find_post("c", "Mùa lũ Trung Bộ: gói giấy tờ", at(10, 20, 0))["id"] == "moi"   # bài hôm qua không tính
    assert tp.find_post("c", "caption khác", at(10, 20, 0)) is None
