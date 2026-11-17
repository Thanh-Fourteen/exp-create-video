"""W3 (UPGRADE-PLAN 2026-11-17): đổi khung đúng đầu câu, trần 4,5s, spec 1.4 `start_frac`."""
from create_video.spec import build as B


def test_cat_dung_dau_cau(monkeypatch):
    monkeypatch.setattr(B, "_montage_sec", lambda: None)
    fr = B.seg_bounds(20.0, 26.0, cuts=[22.5])           # câu 2 bắt đầu 22,5s; hai nửa ≤ 4,5s
    assert fr == [0.0, round(2.5 / 6, 4)]


def test_cau_qua_sat_mep_thi_bo(monkeypatch):
    monkeypatch.setattr(B, "_montage_sec", lambda: None)
    assert B.seg_bounds(20.0, 24.0, cuts=[20.5, 23.6]) == [0.0]   # < 1,2s từ mép → không cắt; 4s ≤ trần


def test_doan_dai_chia_theo_tran(monkeypatch):
    monkeypatch.setattr(B, "_montage_sec", lambda: None)
    fr = B.seg_bounds(30.0, 39.0)                          # 9s sau 15s → trần 4,5 → 2 đoạn
    assert fr == [0.0, 0.5]
    assert len(B.seg_bounds(30.0, 80.0)) == B.SEG_MAX


def test_reframe_ghi_start_frac_tang_dan(monkeypatch):
    monkeypatch.setattr(B, "_montage_sec", lambda: None)
    m = B._motion_preset(0, 1.0, 1.12)
    out = B._reframe(m, 16.0, 26.0, 0, cuts=[19.0, 23.0])
    fr = [s["start_frac"] for s in out["segments"]]
    assert fr[0] == 0.0 and fr == sorted(fr) and len(fr) == 3


def test_montage_kenh_meo_van_dung(monkeypatch):
    monkeypatch.setattr(B, "_montage_sec", lambda: 1.5)
    fr = B.seg_bounds(5.0, 10.0, cuts=[7.0])
    assert len(fr) >= 3 and round(2.0 / 5, 4) in fr


def test_screenshot_khong_theo_montage(monkeypatch):
    monkeypatch.setattr(B, "_montage_sec", lambda: 1.5)
    out = B._zoom_screenshot({"type": "none"}, 20.0, 24.0, close=1.35)
    assert "segments" not in out                          # 4s ≤ trần 4,5 → chữ đứng yên cho kịp đọc


def test_moc_tu_nhan_bo_hook_va_lui_truoc_tu():
    caps = [{"style": "hook", "words": [{"w": "5", "start": 0.2, "end": 0.4}]},
            {"style": "caption", "words": [{"w": "giảm", "start": 3.0, "end": 3.2}, {"w": "ba", "start": 3.2, "end": 3.4},
                                           {"w": "mươi", "start": 3.4, "end": 3.6}, {"w": "phần", "start": 3.6, "end": 3.8},
                                           {"w": "trăm", "start": 3.8, "end": 4.0}, {"w": "với", "start": 4.0, "end": 4.2}, {"w": "GPT-5", "start": 5.0, "end": 5.4}]}]
    t = B.accent_times(caps, ["ba mươi phần trăm"])
    assert t == [3.15, 4.95]
    assert "emph" not in caps[1]["words"][1]          # không làm bẩn captions
