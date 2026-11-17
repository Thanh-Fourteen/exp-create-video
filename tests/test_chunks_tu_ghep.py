"""AUDIT #8 (2026-11-16): cụm phụ đề không xé đôi từ ghép, ưu tiên cắt trước hư từ."""

from create_video.spec.chunks import split_chunks


def _texts(text, step=0.25):
    w = [{"w": x, "start": i * step, "end": i * step + step * 0.9} for i, x in enumerate(text.split())]
    return [" ".join(x["w"] for x in w[c["from"]:c["to"]]) for c in split_chunks(w, 0.0, w[-1]["end"])]


def test_khong_tach_ngan_hang():
    out = _texts("Nhiều người tưởng ngân hàng tự bật")
    assert not any(t.endswith("ngân") for t in out), out
    assert any("ngân hàng" in t for t in out), out


def test_khong_tach_thoa_thuan_va_dien_thoai():
    for t in ("Màn hình app hiện tờ thoả thuận lúc bạn đang vội", "Mở điện thoại vào cài đặt tìm mục tạm dừng"):
        out = _texts(t)
        assert not any(x.split()[-1] in ("thoả", "điện", "cài", "tạm") for x in out), out


def test_cat_truoc_hu_tu():
    out = _texts("Dòng một là phạm vi giao dịch")
    assert not any(t.endswith(" là") for t in out), out
