"""Lịch đăng (2026-10-08, research/probes/w7-lich-dang-research.md) — không gọi mạng, DB tạm."""
import datetime as dt

import pytest

from create_video import lich
from create_video.web import db

TZ = lich.TZ


def at(d: int, h: int, m: int = 0) -> float:
    """Thời điểm ngày 2026-10-<d> h:m giờ VN."""
    return dt.datetime(2026, 10, d, h, m, tzinfo=TZ).timestamp()


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "x.db")
    db.init()
    conf = {"slots": ["11:30", "20:00"], "per_day": 1, "min_gap_hours": 4, "mode": "automatic", "order": "oldest"}
    monkeypatch.setattr(lich, "cfg", lambda cid: dict(conf))
    vids = []
    monkeypatch.setattr("create_video.web.library.list_videos", lambda: vids)
    deleted = set()
    monkeypatch.setattr("create_video.paths.find_web_video", lambda vid: None if vid in deleted else tmp_path / vid)
    return {"conf": conf, "vids": vids, "deleted": deleted}


def _v(vid, pillar="a", created="2026-10-01", channel="meo"):
    return {"id": vid, "channel": channel, "pillar": pillar, "created_at": created, "review": db.get_review(vid)}


def test_o_gio_theo_ngay_vn(env):
    ts = lich.slot_times("meo", at(9, 0), 2)
    assert [lich.fmt(t) for t in ts] == ["11:30 09/10", "20:00 09/10", "11:30 10/10", "20:00 10/10"]


def test_uu_tien_o_dau_trong_ngay(env):
    env["conf"]["slots"] = ["20:00", "11:45"]
    free = lich.free_slots("meo", at(9, 0), 2)
    assert [lich.fmt(t) for t in free] == ["20:00 09/10", "20:00 10/10"]   # per_day=1 → giờ chính, không phải giờ sớm


def test_o_trong_bo_ngay_da_du_bai(env):
    db.set_schedule("x", "meo", at(9, 11, 30))
    free = lich.free_slots("meo", at(9, 0), 2)
    assert [lich.fmt(t) for t in free] == ["11:30 10/10"]       # per_day=1: ngày 9 đủ; ngày 10 lấy ô đầu


def test_tu_xep_xen_pillar_va_cu_truoc(env):
    env["vids"] += [_v("v1", "a", "2026-10-01"), _v("v2", "a", "2026-10-02"), _v("v3", "b", "2026-10-03")]
    out = lich.plan("meo", days=3, now=at(9, 0))
    assert [v for v, _ in out] == ["v1", "v3", "v2"]            # cũ trước, nhưng không để hai bài 'a' liền nhau
    assert db.get_schedule("v1")["status"] == "scheduled"


def test_tu_xep_bo_video_da_quyet(env):
    env["vids"] += [_v("v1"), _v("v2")]
    db.set_review("v1", decision="drop")
    env["vids"][0]["review"] = db.get_review("v1")
    assert [v for v, _ in lich.plan("meo", 3, now=at(9, 0))] == ["v2"]


def test_tick_toi_gio_thi_dang(env, monkeypatch):
    from create_video import tiktok_post as tp
    db.set_schedule("v1", "meo", at(9, 11, 30))
    got = {}
    monkeypatch.setattr(tp, "post_video", lambda vid, scheduling: got.update(vid=vid, mode=scheduling) or
                        {"post_id": "p1", "status": "sending", "pub_file": "f.mp4"})
    monkeypatch.setattr(tp, "sync_review", lambda vid, r=None: None)
    assert lich.tick(at(9, 11, 29)) == {}                            # chưa tới giờ
    r = lich.tick(at(9, 11, 31))
    assert r["posted"] == ["v1"] and got == {"vid": "v1", "mode": "automatic"}
    assert db.get_schedule("v1")["status"] == "posting" and db.get_review("v1")["buffer_post_id"] == "p1"
    db.set_review("v1", buffer_status="sent", decision="post")
    assert lich.tick(at(9, 11, 40))["done"] == ["v1"]
    assert db.get_schedule("v1")["status"] == "posted"


def test_tick_tre_qua_20_phut_thi_lo_gio(env, monkeypatch):
    from create_video import tiktok_post as tp
    db.set_schedule("v1", "meo", at(9, 11, 30))
    monkeypatch.setattr(tp, "post_video", lambda *a, **k: pytest.fail("không được đăng muộn"))
    assert lich.tick(at(9, 12, 0))["missed"] == ["v1"]
    assert db.get_schedule("v1")["status"] == "missed"


def test_tick_tam_giu_tu_dong(env, monkeypatch):
    from create_video import tiktok_post as tp
    db.kv_set("auto_hold_until", at(9, 21))
    db.set_schedule("v1", "meo", at(9, 11, 30))
    monkeypatch.setattr(tp, "post_video", lambda *a, **k: pytest.fail("đang tạm giữ"))
    assert lich.tick(at(9, 11, 31))["held"] == ["v1"]
    env["conf"]["mode"] = "notification"                              # notification không bị giữ
    db.set_schedule("v2", "meo", at(9, 20))
    monkeypatch.setattr(tp, "post_video", lambda vid, scheduling: {"post_id": "p", "status": "scheduled", "pub_file": "f"})
    monkeypatch.setattr(tp, "sync_review", lambda vid, r=None: None)
    assert lich.tick(at(9, 20, 1))["posted"] == ["v2"]


def test_tick_huy_neu_da_dang_tay(env, monkeypatch):
    from create_video import tiktok_post as tp
    db.set_schedule("v1", "meo", at(9, 11, 30))
    db.set_review("v1", decision="post")
    monkeypatch.setattr(tp, "post_video", lambda *a, **k: pytest.fail("đã đăng tay"))
    assert lich.tick(at(9, 11, 31))["cancelled"] == ["v1"]


def test_loi_dang_thi_ghi_failed(env, monkeypatch):
    from create_video import tiktok_post as tp
    db.set_schedule("v1", "meo", at(9, 11, 30))

    def boom(vid, scheduling):
        raise tp.PostError("Funnel tắt")
    monkeypatch.setattr(tp, "post_video", boom)
    monkeypatch.setattr(tp, "sync_review", lambda vid, r=None: None)
    assert lich.tick(at(9, 11, 31))["failed"] == ["v1"]
    assert "Funnel" in db.get_schedule("v1")["error"]


def test_canh_bao_hen_tay(env, monkeypatch):
    monkeypatch.setattr(lich.time, "time", lambda: at(9, 0))
    db.set_schedule("v1", "meo", at(9, 11, 30))
    w = lich.warnings("meo", at(9, 13))
    assert any("dưới 4 giờ" in x for x in w) and any("đủ 1 bài" in x for x in w)
    assert lich.warnings("meo", at(10, 11, 30)) == []


def test_chinh_khung_gio_tren_web(tmp_path, monkeypatch):
    """Trang lịch thêm/bớt giờ, đổi số bài/ngày → kv `posting:<kênh>` đè channel.yaml."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "y.db")
    db.init()
    base = lich.cfg("meo")["slots"]
    c = lich.set_slots("meo", slots=base + ["7:05"], per_day=2)
    assert c["slots"] == base + ["07:05"] and c["per_day"] == 2
    assert lich.set_slots("meo", per_day=9)["per_day"] == 4
    with pytest.raises(ValueError):
        lich.set_slots("meo", slots=[])
    with pytest.raises(ValueError):
        lich.set_slots("meo", slots=["25:00"])


def test_loi_tam_thi_thu_lai_phut_sau(env, monkeypatch):
    """2026-10-09 17:00: Buffer không đọc được video lúc ổ nghẽn → thử lại, không đánh 'lỗi' ngay."""
    from create_video import tiktok_post as tp
    db.set_schedule("v1", "meo", at(9, 17, 0))
    n = {"i": 0}

    def flaky(vid, scheduling):
        n["i"] += 1
        if n["i"] == 1:
            raise tp.PostError("Buffer từ chối (InvalidInputError): Invalid post: Video could not be read from its URL.")
        return {"post_id": "p", "status": "sending", "pub_file": "f"}
    monkeypatch.setattr(tp, "post_video", flaky)
    monkeypatch.setattr(tp, "sync_review", lambda vid, r=None: None)
    assert lich.tick(at(9, 17, 0, ))["retry"] == ["v1"] and db.get_schedule("v1")["status"] == "scheduled"
    assert lich.tick(at(9, 17, 1))["posted"] == ["v1"]


def test_video_xong_tu_gan_khung_gan_nhat(env, monkeypatch):
    """2026-10-09 Tony: dựng xong → khung trống gần nhất; đã có lịch / đã quyết thì không gắn lại."""
    env["conf"].update(slots=["12:00", "17:30", "08:30"], per_day=3, min_gap_hours=3, auto=True)
    monkeypatch.setattr(lich.channels, "get", lambda cid: type("C", (), {"raw": {"buffer_channel_id": "x"}})())
    t4 = {"remaining": [{"tier": "t4", "what": "sai số"}]}
    monkeypatch.setattr("create_video.web.library.load_video",
                        lambda vid: {"id": vid, "qc": t4 if vid == "sai" else {"status": "blocked", "remaining": [{"tier": "t1"}]}})
    assert lich.assign_next("sai", "meo", now=at(9, 10, 0)) is None                      # còn lỗi sự thật → không tự lịch
    t1 = lich.assign_next("v1", "meo", now=at(9, 10, 0))                                  # chỉ lỗi hình T1 → vẫn lịch
    assert lich.fmt(t1) == "12:00 09/10"
    assert lich.fmt(lich.assign_next("v2", "meo", now=at(9, 10, 0))) == "17:30 09/10"
    assert lich.fmt(lich.assign_next("v3", "meo", now=at(9, 10, 0))) == "08:30 10/10"   # 08:30 hôm nay đã qua
    assert lich.assign_next("v1", "meo", now=at(9, 10, 0)) is None                       # đã có lịch
    db.set_review("v4", decision="drop")
    assert lich.assign_next("v4", "meo", now=at(9, 10, 0)) is None
    env["conf"]["auto"] = False
    assert lich.assign_next("v5", "meo", now=at(9, 10, 0)) is None


def test_bai_da_dang_chi_tinh_mot_lan(env):
    """Bài đăng theo lịch có cả giờ hẹn lẫn giờ đăng thật — chỉ được chiếm MỘT khung trong ngày."""
    env["conf"].update(slots=["08:30", "12:00", "17:30"], per_day=3, min_gap_hours=3)
    db.set_schedule("v1", "meo", at(9, 8, 30))
    db.update_schedule("v1", status="posted")
    db.set_review("v1", decision="post", posted_at=at(9, 8, 32))
    env["vids"].append(_v("v1"))
    env["vids"][0]["review"] = db.get_review("v1")
    same_day = [lich.fmt(t) for t in lich.free_slots("meo", at(9, 9, 0), 1) if t < at(10, 0)]
    assert same_day == ["12:00 09/10", "17:30 09/10"]   # trước khi sửa: chỉ còn 1 khung


def test_dang_bi_ngat_giua_chung_khong_ket_mai(env, monkeypatch):
    from create_video import tiktok_post as tp
    db.set_schedule("v1", "meo", at(9, 8, 30))
    db.update_schedule("v1", status="posting")            # timer bị giết trước khi gửi Buffer
    monkeypatch.setattr(tp, "sync_review", lambda vid, r=None: pytest.fail("chưa có bài Buffer thì không hỏi"))
    monkeypatch.setattr(lich.time, "time", lambda: at(9, 8, 31))
    assert lich.tick(at(9, 8, 35)).get("failed") is None   # mới 4 phút — còn chờ
    row = db.get_schedule("v1")
    assert lich.tick(row["updated_at"] + lich.STUCK_SEC + 60)["failed"] == ["v1"]
    assert "ngắt" in db.get_schedule("v1")["error"]


def test_nut_dang_tay_khong_dang_trung_voi_lich(env, monkeypatch):
    import os

    from fastapi.testclient import TestClient

    from create_video import tiktok_post as tp
    from create_video.web import app as web
    monkeypatch.setitem(os.environ, "XUONG_DEV", "1")
    monkeypatch.setattr(web, "DEV", True)
    monkeypatch.setattr(web, "load_video", lambda vid: {"id": vid, "channel": "meo", "review": db.get_review(vid)})
    monkeypatch.setattr(web, "_tiktok_frag", lambda request, vid, err=None: web.HTMLResponse(err or "ok"))
    sent = []
    monkeypatch.setattr(tp, "post_video", lambda vid, scheduling="automatic": sent.append(vid) or
                        {"post_id": "p", "status": "sending", "pub_file": "f"})
    c = TestClient(web.app)
    db.set_schedule("v1", "meo", at(9, 8, 30))
    db.update_schedule("v1", status="posting")
    r = c.post("/videos/v1/tiktok")
    assert "đang đăng" in r.text and sent == []                       # timer đang đăng → nút không gửi lần 2
    db.set_schedule("v2", "meo", at(9, 20, 0))
    c.post("/videos/v2/tiktok")
    assert sent == ["v2"] and db.get_schedule("v2")["status"] == "cancelled"   # đăng tay → huỷ lịch


def test_dang_gap_funnel_dong_thi_tu_sua_mot_lan(env, monkeypatch):
    from create_video import kiem_dang
    from create_video import tiktok_post as tp
    db.set_schedule("v1", "meo", at(9, 8, 30))
    heals = []
    monkeypatch.setattr(kiem_dang, "heal_funnel", lambda: heals.append(1) or "ok")

    def boom(vid, scheduling):
        raise tp.PostError("Buffer từ chối (InvalidInputError): Invalid post: Video could not be read from its URL.")
    monkeypatch.setattr(tp, "post_video", boom)
    monkeypatch.setattr(tp, "sync_review", lambda vid, r=None: None)
    r = lich.tick(at(9, 8, 30))
    assert r["retry"] == ["v1"] and heals == [1]
    lich.tick(at(9, 8, 31))
    assert heals == [1]                       # trong 10 phút không bật/tắt lại lần nữa


def test_video_da_xoa_thi_huy_lich_khong_bao_loi(env, monkeypatch):
    """2026-10-10: Tony xoá video lúc 23:37, lịch 08:30 vẫn cố đăng → 'Không thấy video' → Lỗi."""
    from create_video import tiktok_post as tp
    db.set_schedule("v1", "meo", at(10, 8, 30))
    env["deleted"].add("v1")
    monkeypatch.setattr(tp, "post_video", lambda *a, **k: pytest.fail("video đã xoá"))
    assert lich.tick(at(10, 8, 30))["cancelled"] == ["v1"]
    assert db.get_schedule("v1")["status"] == "cancelled" and "xoá" in db.get_schedule("v1")["error"]


def test_y_tuong_buoi_sang_tung_kenh_va_thu_lai(tmp_path, monkeypatch):
    """Rà soát 2026-10-10: 06:30 hai kênh chạy cùng lúc, cùng hỏng, cả ngày không chạy lại."""
    import time as _t
    from create_video.web import worker
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "w.db")
    db.init()
    monkeypatch.setattr(worker, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(worker, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(worker.time, "localtime", lambda *a: _t.struct_time((2026, 10, 10, 9, 0, 0, 5, 283, 0)))
    launched = []

    class P:
        def __init__(self, cmd, **kw):
            launched.append(cmd[-1])
            self.rc = None

        @property
        def returncode(self):
            return self.rc

        def poll(self):
            return self.rc
    monkeypatch.setattr(worker.subprocess, "Popen", P)
    monkeypatch.setattr(worker, "_IDEAS", [])
    worker.daily_ideas()
    worker.daily_ideas()
    assert len(launched) == 1                              # đang chạy một kênh → không chạy chồng
    worker._IDEAS[0].rc = 1                                # hỏng
    worker.daily_ideas()
    assert len(launched) == 2 and launched[1] != launched[0]   # sang kênh kia
    worker._IDEAS[0].rc = 1
    worker.daily_ideas()
    assert len(launched) == 2                              # kênh đầu: chưa đủ 2 giờ → chưa thử lại
