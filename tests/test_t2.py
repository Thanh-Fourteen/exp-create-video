"""P4.S1: phần thuần của T2 — quyết định từ P(Yes), dHash. Không GPU."""

from __future__ import annotations

from PIL import Image

from create_video.qc.t2_vlm import FIX_TEXT, _thresholds, decide, dhash, hamming


def _p(topic=0.95, text=0.01, anatomy=0.01):
    return {"topic": topic, "text": text, "anatomy": anatomy}


def test_anh_tot_pass():
    ok, score, issues, fix = decide(_p(), False, _thresholds())
    assert ok and score == 10 and issues == [] and fix is None


def test_lac_de_chan():
    ok, score, issues, _ = decide(_p(topic=0.2), False, _thresholds())
    assert not ok and score == 2 and issues == ["topic_mismatch"]


def test_nguong_min_shot_score_tu_thresholds():
    thr = _thresholds()
    edge = thr["min_shot_score"] / 10
    assert decide(_p(topic=edge), False, thr)[0]
    assert not decide(_p(topic=edge - 0.06), False, thr)[0]


def test_chu_trong_anh_chan_va_co_fix():
    ok, _, issues, fix = decide(_p(text=0.9), False, _thresholds())
    assert not ok and "garbled_text_in_image" in issues and FIX_TEXT in fix


def test_harsh_cut_chi_canh_bao():
    ok, _, issues, _ = decide(_p(), True, _thresholds())
    assert ok and issues == ["harsh_cut"]


def test_dhash_anh_giong_gan_nhau(tmp_path):
    import random

    rnd = random.Random(0)
    a = Image.new("L", (90, 160))
    a.putdata([rnd.randrange(256) for _ in range(90 * 160)])
    a = a.resize((9, 8)).resize((90, 160))                            # mảng lớn, ổn định
    a.save(tmp_path / "a.png")
    a.point(lambda v: min(255, v + 3)).save(tmp_path / "b.png")      # sáng lên chút
    a.transpose(Image.FLIP_LEFT_RIGHT).save(tmp_path / "c.png")      # cảnh khác hẳn
    ha, hb, hc = (dhash(tmp_path / f"{x}.png") for x in "abc")
    assert hamming(ha, hb) <= 8 < hamming(ha, hc)
