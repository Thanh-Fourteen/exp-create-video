"""Số ảnh sinh ra phải khớp số shot sẽ dựng.

Đây là hồi quy cho một lỗi **im lặng** đã xảy ra thật ngày 2026-08-14: pipeline
đếm số shot bằng tham số mặc định (3-8 giây) trong khi `_plan_shots` đọc
`configs/style.yaml` (2-4 giây). Kết quả: sinh 7 ảnh cho 11 shot, 4 shot cuối
rơi về nền phẳng — video vẫn render, vẫn qua QC tầng 1, chỉ là 12 giây cuối
không có hình. Không có exception nào được ném ra.
"""

from __future__ import annotations

import yaml

from create_video.pipeline import REPO_ROOT, _estimate_shot_count
from create_video.spec.build import _plan_shots
from create_video.voice.echo import LineSpan


def _spans(durations: list[float], gap: float = 0.28) -> list[LineSpan]:
    out, t = [], 0.0
    for i, d in enumerate(durations):
        out.append(LineSpan(text=f"câu {i}", start=t, end=t + d))
        t += d + gap
    return out


def _style() -> dict:
    return yaml.safe_load((REPO_ROOT / "configs" / "style.yaml").read_text(encoding="utf-8"))


def test_uoc_luong_khop_ke_hoach_that():
    spans = _spans([2.4, 1.8, 3.1, 2.2, 2.9, 1.5, 2.6, 3.4, 2.0, 2.8, 1.9, 2.3, 3.0, 2.1, 2.7])
    style = _style()
    total = spans[-1].end
    planned = _plan_shots(spans, total, [], style, "#000000")
    assert _estimate_shot_count(spans) == len(planned)


def test_shot_phu_kin_va_khong_chong():
    spans = _spans([2.4, 1.8, 3.1, 2.2, 2.9, 1.5])
    style = _style()
    total = spans[-1].end
    shots = _plan_shots(spans, total, [], style, "#000000")
    assert shots[0]["start_sec"] == 0.0
    assert abs(shots[-1]["end_sec"] - total) < 1e-6
    for a, b in zip(shots, shots[1:]):
        assert a["end_sec"] == b["start_sec"], "shot phải nối liền, không hở không chồng"


def test_t1_bat_shot_nen_phang_lan_trong_video_that():
    """Trộn ảnh với nền phẳng = sinh thiếu ảnh. Đây là ca đã lọt qua T1 thật."""
    from create_video.qc.t1_technical import check_shots_have_image

    def spec(kinds):
        return {"shots": [{"id": f"s{i+1}", "asset": {"kind": k, "path": "x"}}
                          for i, k in enumerate(kinds)]}

    assert check_shots_have_image(spec(["image"] * 5)).ok
    assert check_shots_have_image(spec(["color"] * 5)).ok, "toàn nền phẳng = chế độ test"
    bad = check_shots_have_image(spec(["image", "image", "color", "color"]))
    assert not bad.ok and "s3" in bad.detail
