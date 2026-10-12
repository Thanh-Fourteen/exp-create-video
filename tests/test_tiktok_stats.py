"""Theo dõi số TikTok (2026-10-08, research/23) — không gọi mạng."""
from create_video import tiktok_stats as ts


def _v(vid, cap, created="2026-10-05T10:00:00+0700", decision=None, url=None):
    return {"id": vid, "created_at": created, "post": {"caption": cap},
            "review": {"decision": decision, "tiktok_url": url}}


def _e(eid, desc, t=1791300000):
    return {"id": eid, "description": desc, "timestamp": t}


def test_khop_caption_bo_hashtag_va_dau_cau():
    vids = [_v("a", "Sạc qua đêm có hại pin? 3 điều Apple nói 🔋\n\n#songkheo #meovat"),
            _v("b", "Đồ ăn thừa để tủ lạnh được mấy ngày")]
    m = ts.match([_e("111", "Sạc qua đêm có hại pin 3 điều Apple nói #pin #meo")], vids)
    assert list(m) == ["a"] and m["a"]["id"] == "111"


def test_khong_khop_video_da_co_link_da_bo_hoac_sinh_sau():
    vids = [_v("a", "Mẹo A rất dài để khớp", url="https://www.tiktok.com/@x/video/111"),
            _v("b", "Mẹo B rất dài để khớp", decision="drop"),
            _v("c", "Mẹo C rất dài để khớp", created="2026-12-01T10:00:00+0700")]
    es = [_e("111", "Mẹo A rất dài để khớp"), _e("222", "Mẹo B rất dài để khớp"), _e("333", "Mẹo C rất dài để khớp")]
    assert ts.match(es, vids) == {}


def test_ban_dung_lai_giong_uu_tien_ban_da_danh_dau_dang():
    vids = [_v("goc", "Cùng một caption cho hai bản", decision="post", created="2026-10-05T09:00:00+0700"),
            _v("goc-v2", "Cùng một caption cho hai bản", created="2026-10-05T11:00:00+0700")]
    assert list(ts.match([_e("9", "Cùng một caption cho hai bản")], vids)) == ["goc"]


def test_luu_va_doc_so(tmp_path):
    from create_video.web import db
    p = tmp_path / "x.db"
    db.init(p)
    db.add_stat("v", 1.0, path=p, views=10, likes=1)
    db.add_stat("v", 2.0, path=p, views=25, comments=2)
    assert [r["views"] for r in db.stats_for("v", p)] == [10, 25]
    assert db.latest_stats(p)["v"]["comments"] == 2
