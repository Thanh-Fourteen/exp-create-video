"""Trang Thống kê kênh (2026-10-08, research/24) — luật số, không mạng."""
from create_video.web import analytics as an

H = 3600


def _s(h, v):
    return {"ts": 1000 + h * H, "views": v}


def test_views_at_noi_suy_giua_hai_moc_that():
    assert an.views_at([_s(20, 100), _s(26, 160)], 1000, 24) == 140


def test_views_at_khong_doan_tu_0_khi_moc_dau_qua_xa():
    assert an.views_at([_s(30, 500)], 1000, 24) is None          # chưa theo dõi lúc 24h
    assert an.views_at([_s(25, 500)], 1000, 24) == 500           # mốc đầu cách ≤ 3h → lấy luôn
    assert an.views_at([_s(10, 50)], 1000, 24) is None           # video chưa tới 24h


def test_er_gop_khong_bi_video_it_view_keo_lech():
    rows = [{"views": 1, "likes": 2}, {"views": 999, "likes": 18}]
    assert an._er({"views": 1, "likes": 2}) == 2.0                # từng video: 200% — nhiễu
    tot = sum(r["likes"] for r in rows) / sum(r["views"] for r in rows)
    assert abs(tot - 0.02) < 1e-9
