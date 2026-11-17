"""AUDIT 2026-11-16 — đợt W2: đọc được, bớt che."""

from create_video.visual import screenshot as sc


def test_chu_than_sau_phong_dat_nguong_doc():
    # chữ thân sau CSS phóng (READ_CSS_PX) phải ≥ 40px trên khung (UPGRADE-PLAN §4) và ≥ MIN_READABLE_PX
    assert sc.display_font_px(sc.READ_CSS_PX) >= 40
    assert sc.display_font_px(12) < sc.MIN_READABLE_PX     # 12px không phóng → bị chặn, lùi b-roll


def test_css_an_quang_cao_khong_an_khung_noi_dung():
    css = sc._HIDE_GENERIC
    assert "[class*=advert i]" in css and "[class*=voucher i]" in css
    # [class*=banner] từng ẩn .ContentBanner = toàn bộ nội dung chinhphu.vn → timeout (2026-11-16)
    assert "[class*=banner i]," not in css.replace("[class*=banner i][class*=top i]", "")


def test_khoa_cache_doi_theo_phien_ban():
    assert sc._key("https://a.vn/x") != __import__("hashlib").sha256(b"https://a.vn/x").hexdigest()[:16]
