"""Đăng 1 nút qua Buffer (2026-10-08, research/22) — không gọi mạng."""
import json

import pytest

from create_video import tiktok_post as tp


def _video(tmp_path, channel="meo"):
    d = tmp_path / "vid1"
    d.mkdir()
    (d / "video.mp4").write_bytes(b"\0" * 1000)
    (d / "result.json").write_text(json.dumps({"mp4": "video.mp4", "channel": channel, "title": "T",
                                               "post": {"caption": "Mẹo hay\n\n#songkheo #meovat"}}), encoding="utf-8")
    return d


@pytest.fixture
def env(tmp_path, monkeypatch):
    import create_video.paths as paths
    monkeypatch.setattr(tp, "PUB_DIR", tmp_path / "pub")
    monkeypatch.setattr(tp, "_env", lambda n: {"XUONG_PUB_URL": "https://x.ts.net:10000/bimat",
                                               "BUFFER_API_KEY": "k"}.get(n))
    d = _video(tmp_path)
    monkeypatch.setattr(paths, "find_web_video", lambda vid: d if vid == "vid1" else None)
    return tmp_path


def test_dang_dung_kenh_caption_va_nhan_ai(env, monkeypatch):
    sent = {}

    def gql(q, v=None):
        sent.update(v["i"])
        return {"createPost": {"__typename": "PostActionSuccess", "post": {"id": "p1", "status": "sending"}}}

    monkeypatch.setattr(tp, "gql", gql)
    monkeypatch.setattr(tp, "check_public", lambda url: None)
    r = tp.post_video("vid1")
    assert sent["channelId"] == "6ac766a56a5c39ccb64eda36"            # kênh meo
    assert sent["text"].endswith("#songkheo #meovat")
    assert sent["mode"] == "shareNow" and sent["schedulingType"] == "automatic"
    # 2026-10-11: nhãn AI theo `posting.ai_label` của kênh (thử nghiệm bỏ nhãn) — gửi đúng giá trị cấu hình
    assert sent["metadata"] == {"tiktok": {"isAiGenerated": tp.ai_label_for("meo")}} and r["ai_label"] == tp.ai_label_for("meo")
    url = sent["assets"][0]["video"]["url"]
    assert url.startswith("https://x.ts.net:10000/bimat/") and url.endswith(r["pub_file"])
    assert (env / "pub" / r["pub_file"]).exists() and r["post_id"] == "p1"


def test_co_bia_thi_noi_cuoi_va_tro_thumbnail_offset(env, monkeypatch):
    """Buffer cấm thumbnailUrl → bìa nối vào cuối video, thumbnailOffset trỏ vào đó; thiếu bìa thì không gửi offset."""
    d = env / "vid1"
    (d / "post").mkdir()
    (d / "post" / "cover.jpg").write_bytes(b"jpg")
    sent, called = {}, {}

    def fake_with_cover(mp4, cover, dst):
        called["cover"] = cover
        dst.write_bytes(b"noi")
        return 53966

    monkeypatch.setattr(tp, "with_cover", fake_with_cover)
    monkeypatch.setattr(tp, "check_public", lambda url: None)
    monkeypatch.setattr(tp, "gql", lambda q, v=None: sent.update(v["i"]) or
                        {"createPost": {"__typename": "PostActionSuccess", "post": {"id": "p1", "status": "sending"}}})
    r = tp.post_video("vid1")
    assert called["cover"] == d / "post" / "cover.jpg"
    assert sent["assets"][0]["video"]["metadata"] == {"thumbnailOffset": 53966}
    assert "thumbnailUrl" not in sent["assets"][0]["video"]
    assert (env / "pub" / r["pub_file"]).read_bytes() == b"noi"


def test_noi_bia_hong_van_dang_ban_goc(env, monkeypatch):
    import subprocess
    d = env / "vid1"
    (d / "post").mkdir()
    (d / "post" / "cover.jpg").write_bytes(b"jpg")
    sent = {}

    def boom(mp4, cover, dst):
        raise subprocess.CalledProcessError(1, "ffmpeg", stderr=b"hong")

    monkeypatch.setattr(tp, "with_cover", boom)
    monkeypatch.setattr(tp, "check_public", lambda url: None)
    monkeypatch.setattr(tp, "gql", lambda q, v=None: sent.update(v["i"]) or
                        {"createPost": {"__typename": "PostActionSuccess", "post": {"id": "p1", "status": "sending"}}})
    r = tp.post_video("vid1")
    assert "metadata" not in sent["assets"][0]["video"]
    assert (env / "pub" / r["pub_file"]).read_bytes() == (d / "video.mp4").read_bytes()


def test_loi_thi_don_file_cong_khai(env, monkeypatch):
    monkeypatch.setattr(tp, "check_public", lambda url: None)
    monkeypatch.setattr(tp, "gql", lambda q, v=None: {"createPost": {"__typename": "LimitReachedError",
                                                                       "message": "hết lượt"}})
    with pytest.raises(tp.PostError, match="hết lượt"):
        tp.post_video("vid1")
    assert not list((env / "pub").iterdir())


def test_thieu_url_cong_khai(env, monkeypatch):
    monkeypatch.setattr(tp, "_env", lambda n: None)
    with pytest.raises(tp.PostError, match="XUONG_PUB_URL"):
        tp.post_video("vid1")


def test_unstage_khong_thoat_thu_muc(env):
    (env / "pub").mkdir()
    (env / "ngoai.mp4").write_bytes(b"x")
    tp.unstage("../ngoai.mp4")
    assert (env / "ngoai.mp4").exists()


def test_web_dang_xong_thi_tu_tick_va_tai_lai(tmp_path, monkeypatch):
    """W6: POST đăng → thăm dò thấy 'sent' → HX-Refresh, review tự 'post' + link, file công khai bị xoá."""
    import os

    from fastapi.testclient import TestClient

    from create_video.web import app as web, db

    vids = [v for v in os.listdir("videos/meo") if (tp.REPO_ROOT / "videos/meo" / v / "result.json").exists()]
    if not vids:
        pytest.skip("không có video web để thử")
    vid = vids[0]
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "x.db")
    db.init()
    monkeypatch.setenv("XUONG_DEV", "1")
    monkeypatch.setattr(web, "DEV", True)
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "f.mp4").write_bytes(b"x")
    monkeypatch.setattr(tp, "PUB_DIR", pub)
    monkeypatch.setattr(tp, "post_video", lambda v: {"post_id": "p9", "status": "sending", "pub_file": "f.mp4"})
    state = {"s": "sending"}
    monkeypatch.setattr(tp, "status", lambda pid: {"status": state["s"], "externalLink": "https://tiktok.com/@a/video/1"})
    c = TestClient(web.app)

    r = c.post(f"/videos/{vid}/tiktok")
    assert "Đang đăng" in r.text and 'hx-trigger="every 10s' in r.text
    assert c.post(f"/videos/{vid}/tiktok").status_code == 200          # bấm lần 2 không gửi lại (post_id đã có)
    assert "Đang đăng" in c.get(f"/videos/{vid}/tiktok").text
    state["s"] = "sent"
    r = c.get(f"/videos/{vid}/tiktok")
    assert r.status_code == 204 and r.headers["HX-Refresh"] == "true"
    rv = db.get_review(vid)
    assert rv["decision"] == "post" and rv["tiktok_url"].endswith("/video/1") and not (pub / "f.mp4").exists()
    page = c.get(f"/library/{vid}").text
    assert "Đã đăng lên" in page and "Đánh dấu đã đăng tay" not in page and "Dựng lại với giọng khác" not in page
    db.add_stat(vid, 100.0, views=10, likes=1, comments=0)
    db.add_stat(vid, 200.0, views=1500, likes=9, comments=3)
    page = c.get(f"/library/{vid}").text
    assert "<polyline" in page and "1.500" in page and "Đọc 3 bình luận" in page



def test_tat_bat_nhan_ai_theo_kenh(env, monkeypatch):
    sent = {}
    monkeypatch.setattr(tp, "gql", lambda q, v=None: sent.update(v["i"]) or
                        {"createPost": {"__typename": "PostActionSuccess", "post": {"id": "p1", "status": "sending"}}})
    monkeypatch.setattr(tp, "check_public", lambda url: None)
    for val in (True, False):
        monkeypatch.setattr(tp, "ai_label_for", lambda cid, v=val: v)
        r = tp.post_video("vid1")
        assert sent["metadata"]["tiktok"]["isAiGenerated"] is val and r["ai_label"] is val
