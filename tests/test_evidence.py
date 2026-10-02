"""P3b.S4: shot bằng chứng — router, cổng kiểm của scriptwriter, tokenizer, điểm cắt."""

from __future__ import annotations

from create_video.agents.scriptwriter import Script, Shot, _check_shots
from create_video.spec.build import _group_spans
from create_video.visual import router
from create_video.visual.code import tokenize
from create_video.visual.screenshot import target_for
from create_video.voice.echo import LineSpan


def _spans(durs):
    out, t = [], 0.0
    for d in durs:
        out.append(LineSpan("x", t, t + d))
        t += d
    return out


def _script(shots, n_lines=8):
    return Script(topic="t", hook="câu hook", sections=[f"câu {i}" for i in range(n_lines - 2)],
                  cta="cta", shots=shots)


# ── điểm cắt ───────────────────────────────────────────────────────────────
def test_breaks_ep_mo_shot_moi_dung_cau_bang_chung():
    spans = _spans([2.0] * 6)                          # mỗi câu 2s, lo=3 → nhóm 2 câu
    assert _group_spans(spans, 3, 8) == [[0, 1], [2, 3], [4, 5]]
    # đuôi [5] 2s nhập vào nhóm trước (6s ≤ hi+2) — luật đuôi ngắn có từ trước
    assert _group_spans(spans, 3, 8, breaks={3}) == [[0, 1], [2], [3, 4, 5]]


def test_duoi_ngan_khong_nhap_vao_shot_truoc_neu_la_diem_cat():
    spans = _spans([2.0, 2.0, 1.0])
    assert _group_spans(spans, 3, 8)[-1] == [0, 1, 2]
    assert _group_spans(spans, 3, 8, breaks={2}) == [[0, 1], [2]]


# ── router ─────────────────────────────────────────────────────────────────
def test_script_cu_giu_xoay_vong_prompt():
    shots = [Shot(prompt="a"), Shot(prompt="b")]
    v = router.plan(shots, [[0], [1], [2]], [0, 1, 2])
    assert [x.prompt for x in v] == ["a", "b", "a"] and all(x.kind == "image" for x in v)


def test_shot_bang_chung_vao_dung_nhom_bat_dau_bang_cau_do():
    shots = [Shot(prompt="hook img", line=0),
             Shot(prompt="fb", kind="stat", line=3, stat={"value": 6, "label": "VRAM"}),
             Shot(prompt="broll", line=5)]
    kept = list(range(8))
    assert router.breaks(shots, kept) == {3}
    groups = [[0, 1, 2], [3, 4], [5, 6, 7]]
    v = router.plan(shots, groups, kept)
    assert [x.kind for x in v] == ["image", "stat", "image"]
    assert v[1].data == {"value": 6, "label": "VRAM"}
    assert v[2].prompt == "broll"


def test_fallback_prompt_lay_prompt_cua_chinh_shot():
    v = [router.Visual("image", prompt="a"), router.Visual("screenshot", prompt="own")]
    assert router.fallback_prompt(v, 1, []) == "own"


# ── cổng kiểm scriptwriter ─────────────────────────────────────────────────
def _ok_shots():
    return [
        Shot(prompt="p", line=0),
        Shot(prompt="p", kind="stat", line=2, stat={"value": 624, "unit": "MiB", "label": "VRAM đỉnh"}),
        Shot(prompt="p", kind="screenshot", line=4, url="https://huggingface.co/ByteDance/SDXL-Lightning"),
        Shot(prompt="p", line=6),
    ]


def test_shots_hop_le():
    assert _check_shots(_script(_ok_shots())) == []


def test_script_cu_khong_bi_ap_luat_moi():
    assert _check_shots(_script([Shot(prompt="a"), Shot(prompt="b")])) == []


def test_thieu_shot_bang_chung():
    shots = [Shot(prompt="p", line=i) for i in range(4)]
    assert any("shot bằng chứng" in p for p in _check_shots(_script(shots)))


def test_bang_chung_o_cau_0_duoc_phep():
    # Phase V3 (2026-10-02): frame 0 NÊN là bằng chứng mang chủ đề (research/11 §4.1) — luật cũ
    # "cấm bằng chứng ở câu 0" bị thay có chủ ý.
    shots = _ok_shots()
    shots[0] = Shot(prompt="p", kind="stat", line=0, stat={"value": 1, "label": "x"})
    assert not any("câu 0" in p for p in _check_shots(_script(shots)))


def test_url_ngoai_danh_sach_bi_chan():
    shots = _ok_shots()
    shots[2].url = "https://arxiv.org/pdf/2402.13929"     # PDF/figure: license không cho
    assert any("ngoài danh sách" in p for p in _check_shots(_script(shots)))


def test_chart_can_dung_mot_cot_highlight():
    shots = _ok_shots()
    shots[1] = Shot(prompt="p", kind="chart", line=2,
                    chart={"title": "t", "bars": [{"label": "a", "value": 1}, {"label": "b", "value": 2}]})
    assert any("MỘT cột highlight" in p for p in _check_shots(_script(shots)))


def test_code_qua_dai_bi_chan():
    shots = _ok_shots()
    shots[1] = Shot(prompt="p", kind="code", line=2, code={"lang": "python", "lines": ["x" * 41]})
    assert any("40 ký tự" in p for p in _check_shots(_script(shots)))


# ── chụp trang: danh sách cho phép ─────────────────────────────────────────
def test_target_for():
    assert target_for("https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct").selector == "main"
    assert target_for("https://github.com/remotion-dev/remotion").selector == "article.markdown-body"
    assert target_for("https://arxiv.org/abs/2402.13929v2").selector == "#abs"
    assert target_for("https://huggingface.co/papers/2402.13929") is None
    assert target_for("https://arxiv.org/pdf/2402.13929") is None
    assert target_for("https://example.com/a/b") is None


# ── code ───────────────────────────────────────────────────────────────────
def test_tokenize_giu_dung_so_dong_va_noi_dung():
    lines = ["import torch", "", "x = 8  # step"]
    toks = tokenize("python", lines)
    assert len(toks) == 3
    assert ["".join(t["v"] for t in row) for row in toks] == lines
    assert toks[0][0] == {"t": "kw", "v": "import"}
    assert toks[2][-1]["t"] == "com"


def test_chu_tren_hinh_khong_dau_bi_bat():
    from create_video.agents.scriptwriter import _looks_unaccented

    assert _looks_unaccented("VRAM dinh so voi dung luong card")
    assert _looks_unaccented("Khi chay offload")
    assert not _looks_unaccented("VRAM đỉnh so với dung lượng card")
    assert not _looks_unaccented("RTX 2060")
    assert not _looks_unaccented("SDXL base")
    shots = _ok_shots()
    shots[1].stat = {"value": 1, "label": "Trung binh moi anh"}
    assert any("KHÔNG DẤU" in p for p in _check_shots(_script(shots)))
