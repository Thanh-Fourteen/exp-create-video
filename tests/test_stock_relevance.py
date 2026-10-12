"""Chọn clip stock theo độ liên quan (2026-10-05): "sạc điện thoại" từng ra đầu sạc ô tô điện."""
from create_video.visual.stock import relevance


def test_lac_de_xe_bi_tru_diem():
    q = "charging cable plugged into smartphone"
    assert relevance(q, "an-electric-car-charging-9790183") < 0
    assert relevance(q, "a-person-charging-a-smartphone-1") > relevance(q, "a-charging-port-9790184")


def test_dong_nghia_phone():
    assert relevance("hands holding phone", "woman-typing-on-cellphone-1") > 0


def test_dong_nghia_chi_tinh_mot_lan():
    # 2026-10-06: "smartphone" từng được đếm 5 lần (nở đồng nghĩa) → clip Apple Watch thắng clip "sạc"
    q = "charging cable plugged into smartphone"
    lac = relevance(q, "a-person-putting-a-smartphone-on-the-tiles-6374187")
    assert lac <= 1          # 2026-10-06: thiếu vật chính "charging" (từ đầu query) → dưới ngưỡng MIN_SCORE
    assert relevance(q, "a-smartphone-charging-with-cable-1") > lac


def test_thieu_vat_chinh_bi_loai():
    from create_video.visual.stock import MIN_SCORE

    q = "refrigerator door opened by hand"
    assert relevance(q, "person-opening-the-door-7646797") < MIN_SCORE
    assert relevance(q, "woman-opening-refrigerator-door-1") >= MIN_SCORE


def test_canh_mo_dau_can_hai_khai_niem():
    from create_video.visual.stock import MIN_SCORE_HOOK

    q = "charging cable plugged into smartphone"
    assert relevance(q, "a-person-putting-a-smartphone-on-the-tiles-6374187") < MIN_SCORE_HOOK
    assert relevance(q, "phone-charging-on-table-1") >= MIN_SCORE_HOOK
