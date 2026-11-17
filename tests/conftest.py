"""Chốt chung cho mọi test (2026-10-10).

`test_loi_tam_thi_thu_lai_phut_sau` từng gọi THẬT `kiem_dang.heal_funnel` → `tailscale funnel off` rồi bật lại mỗi lần chạy
pytest — Funnel thật mất ~90s mới thông, lịch đăng/nháp Buffer rơi vào khoảng đó thì hỏng. Test không bao giờ được đụng
hệ thống thật: mặc định thay heal_funnel bằng bản giả; test nào cần kiểm thì tự monkeypatch đè lên.
"""
import pytest


@pytest.fixture(autouse=True)
def _khong_dung_funnel_that(monkeypatch):
    from create_video import kiem_dang

    monkeypatch.setattr(kiem_dang, "heal_funnel", lambda: "giả (test)")


@pytest.fixture(autouse=True)
def _so_dem_buffer_rieng(monkeypatch, tmp_path):
    """2026-11-06: sổ đếm lượt gọi Buffer thật (exp/web/buffer-calls.json) có cờ `blocked_30d` → post_video bị chặn và
    test đỏ theo trạng thái máy. Mỗi test dùng sổ riêng."""
    from create_video import tiktok_post

    monkeypatch.setattr(tiktok_post, "LEDGER", tmp_path / "buffer-calls.json")
