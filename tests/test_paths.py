"""Nơi lưu video (2026-10-05): web → videos/<kênh>/<id>, CLI thử nghiệm → out/<id>."""
from create_video import paths


def test_out_root_mac_dinh_la_out(monkeypatch):
    monkeypatch.delenv("CV_OUT_ROOT", raising=False)
    assert paths.out_root() == paths.OUT


def test_out_root_theo_env_tuong_doi(monkeypatch):
    monkeypatch.setenv("CV_OUT_ROOT", "videos/meo")
    assert paths.out_root() == paths.REPO_ROOT / "videos" / "meo"


def test_find_web_video(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "VIDEOS", tmp_path)
    (tmp_path / "meo" / "v1").mkdir(parents=True)
    assert paths.find_web_video("v1") == tmp_path / "meo" / "v1"
    assert paths.find_web_video("khong-co") is None
    assert paths.web_video_dirs() == [tmp_path / "meo" / "v1"]
