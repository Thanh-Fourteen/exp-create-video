"""Nhân vật có mặt suốt video, đổi cỡ theo loại shot (2026-10-05, research/19)."""
import wave

import numpy as np

from create_video.spec.build import _mascot
from create_video.voice.echo import LineSpan


def _wav(p, sec=10.0, sr=16000):
    with wave.open(str(p), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes((np.sin(np.arange(int(sec * sr)) / 7) * 6000).astype(np.int16).tobytes())


def test_che_do_theo_shot(tmp_path):
    w = tmp_path / "v.wav"
    _wav(w)
    spans = [LineSpan(text="Hook.", start=0.0, end=2.0), LineSpan(text="Giữa.", start=2.0, end=6.0),
             LineSpan(text="Chốt.", start=6.0, end=10.0)]
    shots = [{"start_sec": 0.0, "end_sec": 4.0, "asset": {"kind": "video"}},
             {"start_sec": 4.0, "end_sec": 7.0, "asset": {"kind": "stat"}},
             {"start_sec": 7.0, "end_sec": 10.0, "asset": {"kind": "image"}}]
    m = _mascot(w, spans, {"kind": "kheo", "policy": "always"}, shots=shots, total=10.0)   # chính sách cũ, vẫn bật được
    modes = [(x["mode"], x["start_sec"], x["end_sec"]) for x in m["windows"]]
    assert modes == [("peek", 0.0, 2.2), ("dock", 2.2, 4.0), ("peek", 4.0, 7.0), ("dock", 7.0, 10.0)]
    assert sum(x["end_sec"] - x["start_sec"] for x in m["windows"]) == 10.0      # có mặt suốt video
    assert all(len(x["mouth"]) == round((x["end_sec"] - x["start_sec"]) * 30) for x in m["windows"][1:])


# ── AUDIT #8 (2026-11-16): chính sách mặc định "roles" — nhân vật có vai, không đè nội dung ─────────────────────────────

def test_vai_mac_dinh_khong_de_the_va_demo(tmp_path):
    w = tmp_path / "v.wav"
    _wav(w)
    spans = [LineSpan(text="Hook mở đầu.", start=0.0, end=2.0),
             LineSpan(text="Thông tin thường một hai ba.", start=2.0, end=5.0),
             LineSpan(text="Đừng bấm nút này kẻo mất tiền.", start=5.0, end=8.0),
             LineSpan(text="Nhưng còn một chuyện nữa.", start=8.0, end=10.0),
             LineSpan(text="Bạn chọn cách nào?", start=10.0, end=12.0)]
    shots = [{"start_sec": 0.0, "end_sec": 4.0, "asset": {"kind": "image"}},
             {"start_sec": 4.0, "end_sec": 7.0, "asset": {"kind": "stat"}},
             {"start_sec": 7.0, "end_sec": 9.0, "asset": {"kind": "video", "path": "demo/02.mp4"}},
             {"start_sec": 9.0, "end_sec": 12.0, "asset": {"kind": "image"}}]
    m = _mascot(w, spans, {"kind": "kheo"}, shots=shots, total=12.0)
    content = [(4.0, 7.0), (7.0, 9.0)]
    for x in m["windows"]:
        assert all(x["end_sec"] <= a or x["start_sec"] >= b for a, b in content), x   # không giao thẻ/demo
    on = sum(x["end_sec"] - x["start_sec"] for x in m["windows"])
    assert 0 < on < 12.0                                                               # không còn có mặt suốt video
    assert m["windows"][0]["mode"] == "peek" and m["windows"][0]["start_sec"] == 0.0     # hook: nhỏ ở góc


def test_vai_theo_cau():
    from create_video.spec.build import mascot_role

    assert mascot_role(0, 5, "x") == "hook" and mascot_role(4, 5, "x") == "ket"
    assert mascot_role(2, 5, "Bạn có biết không?") == "hoi"
    assert mascot_role(2, 5, "Đừng trộn giấm với javel.") == "canh_bao"
    assert mascot_role(2, 5, "Nhưng còn một thứ nữa.") == "chuyen_y"
    assert mascot_role(2, 5, "Dòng hai là hạn mức mỗi lần.") is None
