"""research/36 (2026-11-16): T1 viền đen — chỉ dải tối có BIÊN rõ mới là viền; ảnh tối tràn mép không phải."""

import numpy as np

from create_video.qc.t1_technical import border_sides


def _img(seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(60, 200, size=(1920, 1080), dtype=np.uint8)   # ảnh có kết cấu


def test_dai_den_co_bien_la_vien():
    g = _img()
    g[:, :22] = 0
    assert border_sides(g)["trái"] == 22


def test_anh_toi_tran_mep_khong_phai_vien():
    g = _img()
    g[:300, :] = 1            # vùng trên đen tuyền sâu 300px (vignette/scrim) — tối tới hết cửa sổ soi
    assert border_sides(g)["trên"] == 0


def test_dai_toi_nhat_dan_khong_co_bien_khong_phai_vien():
    g = _img()
    for y in range(40):       # tối rồi sáng dần — gradient, không có đường biên
        g[-1 - y, :] = min(2 + y // 4, 19)
    g[-41:-40, :] = 20
    assert border_sides(g)["dưới"] == 0


def test_khung_sach():
    assert set(border_sides(_img(1)).values()) == {0}
