"""Tự kiểm đường đăng (2026-10-09) — không gọi mạng: Buffer/Funnel/systemctl đều là bản giả."""
import pytest

from create_video import kiem_dang as kd
from create_video import tiktok_post as tp
from create_video.web import db


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "x.db")
    db.init()
    monkeypatch.setattr(kd, "HEAL_WAITS", (0, 0, 0, 0, 0))
    monkeypatch.setattr(kd.time, "sleep", lambda s: None)
    monkeypatch.setattr(kd, "timer_active", lambda name: True)
    monkeypatch.setattr(tp, "channels", lambda: [{"id": "6ac766106a5c39ccb64ed6db", "isDisconnected": False},
                                                 {"id": "6ac766a56a5c39ccb64eda36", "isDisconnected": False}])
    st = {"funnel_open": True, "heals": 0, "drafts": 0, "deleted": 0}
    monkeypatch.setattr(kd, "buffer_reads_url", lambda cid: (True, "ok") if st["funnel_open"] else
                        (False, "InvalidInputError: Invalid post: Video could not be read from its URL."))

    def heal():
        st["heals"] += 1
        st["funnel_open"] = True
        return "off=0 on=0"
    monkeypatch.setattr(kd, "heal_funnel", heal)
    return st


def test_moi_thu_on(env):
    r = kd.run()
    assert r["ok"] and env["heals"] == 0 and db.kv_get("kiem_dang")["ok"]


def test_funnel_dong_thi_tu_bat_lai(env):
    env["funnel_open"] = False
    r = kd.run()
    assert r["ok"] and env["heals"] == 1 and "ĐÃ SỬA" in r["checks"][2]["msg"]


def test_khong_tu_sua_thi_bao_hong(env):
    env["funnel_open"] = False
    r = kd.run(heal=False)
    assert not r["ok"] and env["heals"] == 0


def test_kenh_mat_ket_noi(env, monkeypatch):
    monkeypatch.setattr(tp, "channels", lambda: [{"id": "6ac766106a5c39ccb64ed6db", "isDisconnected": True}])
    r = kd.run()
    bad = [c["name"] for c in r["checks"] if not c["ok"]]
    assert not r["ok"] and set(bad) == {"kênh ai", "kênh meo"}


def test_nhap_that_luon_bi_xoa_va_don_file(tmp_path, monkeypatch):
    """buffer_reads_url: tạo nháp → xoá nháp → xoá file công khai, kể cả khi Buffer từ chối."""
    monkeypatch.setattr(tp, "PUB_DIR", tmp_path / "pub")
    monkeypatch.setattr(tp, "_env", lambda n: "https://x.ts.net:10000/bimat" if n == "XUONG_PUB_URL" else "k")
    monkeypatch.setattr(kd, "TEST_MP4", tmp_path / "t.mp4")
    (tmp_path / "t.mp4").write_bytes(b"\0" * 100)
    calls = []

    def gql(q, v=None):
        calls.append(q)
        if "createPost" in q:
            assert v["i"]["saveToDraft"] is True and v["i"]["dueAt"].startswith("2030")
            return {"createPost": {"__typename": "PostActionSuccess", "post": {"id": "d1"}}}
        return {"deletePost": {"__typename": "DeletePostSuccess"}}
    monkeypatch.setattr(tp, "gql", gql)
    ok, _ = kd.buffer_reads_url("c")
    assert ok and len(calls) == 2 and "createPost" in calls[0] and "deletePost" in calls[1]   # nháp luôn bị xoá
    assert not list((tmp_path / "pub").iterdir())
    monkeypatch.setattr(tp, "gql", lambda q, v=None: {"createPost": {"__typename": "InvalidInputError", "message": "could not be read"}})
    ok, msg = kd.buffer_reads_url("c")
    assert not ok and "could not be read" in msg and not list((tmp_path / "pub").iterdir())


def test_bat_lai_lau_moi_thong(env, monkeypatch):
    """16:11 10/10: bật lại + 90s vẫn hỏng, vài phút sau mới thông → phải chờ tiếp, bật lại lần 2 nếu cần."""
    env["funnel_open"] = False
    seq = iter([False, False, False, False, True])   # thông ở lần kiểm thứ 5 (sau khi bật lại lần 2)

    def reads(cid):
        return (True, "ok") if next(seq) else (False, "InvalidInputError: Video could not be read from its URL.")
    monkeypatch.setattr(kd, "buffer_reads_url", reads)
    heals = []
    monkeypatch.setattr(kd, "heal_funnel", lambda: heals.append(1) or "ok")
    clock = {"t": 1_000_000.0}                      # đồng hồ giả chạy theo thời gian chờ
    monkeypatch.setattr(kd.time, "time", lambda: clock["t"])
    monkeypatch.setattr(kd.time, "sleep", lambda s: clock.__setitem__("t", clock["t"] + s))
    monkeypatch.setattr(kd, "HEAL_WAITS", (90, 120, 180, 120, 180))
    r = kd.run()
    assert r["ok"] and len(heals) == 2               # lần 2 ở giây 390 > khoá 300s của bước tự kiểm



def test_auto_bo_qua_khi_vua_on(env, monkeypatch):
    calls = []
    monkeypatch.setattr(kd, "run", lambda heal=True: calls.append(1) or {"ok": True, "checks": []})
    db.kv_set("kiem_dang", {"ok": True, "ts": kd.time.time() - 600})
    kd.main(["--auto"])
    assert calls == []
    db.kv_set("kiem_dang", {"ok": False, "ts": kd.time.time() - 600})
    kd.main(["--auto"])
    assert calls == [1]
