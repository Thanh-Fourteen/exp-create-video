"""Đổi chỗ trên trang Lịch (2026-10-10): đổi giờ 2 video / chuyển sang ô trống — chỉ video Đã hẹn, cùng kênh, tương lai."""
import time

import pytest
from fastapi.testclient import TestClient

from create_video.web import db


@pytest.fixture
def c(tmp_path, monkeypatch):
    from create_video.web import app as web
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "x.db")
    db.init()
    monkeypatch.setattr(web, "DEV", True)
    return TestClient(web.app)


H = {"HX-Request": "true"}


def test_doi_gio_hai_video(c):
    t = time.time()
    db.set_schedule("a", "meo", t + 3600)
    db.set_schedule("b", "meo", t + 7200)
    r = c.post("/lich/move", data={"vid": "a", "target": "b"}, headers=H)
    assert r.status_code == 204
    assert db.get_schedule("a")["due_at"] == pytest.approx(t + 7200) and db.get_schedule("b")["due_at"] == pytest.approx(t + 3600)


def test_chuyen_sang_o_trong(c):
    t = time.time()
    db.set_schedule("a", "meo", t + 3600)
    assert c.post("/lich/move", data={"vid": "a", "due": str(t + 9000)}, headers=H).status_code == 204
    assert db.get_schedule("a")["due_at"] == pytest.approx(t + 9000)


def test_tu_choi_cac_truong_hop_sai(c):
    t = time.time()
    db.set_schedule("a", "meo", t + 3600)
    db.set_schedule("ai1", "ai", t + 7200)
    db.set_schedule("dang", "meo", t + 5400)
    db.update_schedule("dang", status="posting")
    db.set_schedule("o", "meo", t + 9000)
    assert "cùng kênh" in c.post("/lich/move", data={"vid": "a", "target": "ai1"}, headers=H).text
    assert c.post("/lich/move", data={"vid": "a", "target": "dang"}, headers=H).status_code == 409   # đang đăng
    assert c.post("/lich/move", data={"vid": "dang", "due": str(t + 20000)}, headers=H).status_code == 409
    assert c.post("/lich/move", data={"vid": "a", "due": str(t - 60)}, headers=H).status_code == 400   # giờ đã qua
    assert "đã có video" in c.post("/lich/move", data={"vid": "a", "due": str(t + 9000)}, headers=H).text   # trùng giờ
    assert db.get_schedule("a")["due_at"] == pytest.approx(t + 3600)                                   # không đổi gì


def test_doi_cho_nguyen_tu_khi_timer_vua_gianh(c):
    t = time.time()
    db.set_schedule("a", "meo", t + 3600)
    db.set_schedule("b", "meo", t + 7200)
    assert db.claim_schedule("b", "automatic")          # timer giành b đúng lúc
    assert db.swap_schedule("a", "b") is False
    assert db.get_schedule("a")["due_at"] == pytest.approx(t + 3600)

