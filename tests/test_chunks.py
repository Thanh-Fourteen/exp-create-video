"""P3b.S5: phụ đề theo cụm + nhấn từ khoá."""

from __future__ import annotations

import copy

from create_video.agents.scriptwriter import Script, _check_emphasis
from create_video.spec.chunks import add_chunks, mark_emphasis, split_chunks


def _words(spec: list[tuple[str, float]], gap: float = 0.0):
    """[(từ, độ dài)] → words liền nhau (cách nhau `gap`)."""
    out, t = [], 0.0
    for w, d in spec:
        out.append({"w": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d + gap
    return out


def _texts(words, chunks):
    return [" ".join(w["w"] for w in words[c["from"]:c["to"]]) for c in chunks]


def test_cum_toi_da_3_am_tiet_va_phu_kin():
    ws = _words([(x, 0.25) for x in "một hai ba bốn năm sáu bảy".split()])
    ch = split_chunks(ws, 0.0, ws[-1]["end"])
    assert all(c["to"] - c["from"] <= 3 for c in ch)
    assert ch[0]["from"] == 0 and ch[-1]["to"] == len(ws)
    assert all(a["to"] == b["from"] and a["end_sec"] == b["start_sec"] for a, b in zip(ch, ch[1:]))
    assert ch[0]["start_sec"] == 0.0 and ch[-1]["end_sec"] == ws[-1]["end"]


def test_luon_cat_sau_dau_cau():
    ws = _words([("Log", .3), ("ghi", .3), ("rõ:", .3), ("gần", .3), ("năm", .3), ("GB", .3)])
    assert _texts(ws, split_chunks(ws, 0, ws[-1]["end"])) == ["Log ghi rõ:", "gần năm GB"]


def test_cat_tai_khoang_lang():
    ws = _words([("a", .3), ("b", .3)]) + [{"w": "c", "start": 1.5, "end": 1.8}]
    assert _texts(ws, split_chunks(ws, 0, 1.8)) == ["a b", "c"]


def test_cum_ngan_hon_min_sec_bi_nhap():
    # đọc rất nhanh: 0,08s/âm tiết → cụm 3 âm tiết chỉ 0,24s < 0,3s
    ws = _words([(x, 0.08) for x in "một hai ba bốn năm sáu bảy tám".split()])
    ch = split_chunks(ws, 0.0, ws[-1]["end"])
    assert all(c["end_sec"] - c["start_sec"] >= 0.3 - 1e-9 for c in ch[:-1])


def test_tu_dai_dung_mot_minh():
    ws = _words([("đã", .3), ("distill", .3), ("SDXL-Lightning", .6), ("từ", .3), ("SDXL", .3), ("gốc.", .3)])
    assert "SDXL-Lightning" in _texts(ws, split_chunks(ws, 0, ws[-1]["end"]))


def test_khong_mo_coi_cuoi_cau():
    ws = _words([("bộ", .3), ("nhớ", .3), ("của", .3), ("card.", .3)])
    assert _texts(ws, split_chunks(ws, 0, ws[-1]["end"]))[-1] != "card."


def test_nhan_so_va_cum_khai():
    ws = _words([("mỗi", .3), ("ảnh", .3), ("tám", .3), ("phẩy", .3), ("hai", .3), ("giây.", .3), ("GPT-5", .3)])
    n = mark_emphasis(ws, ["tám phẩy hai giây"])
    assert [bool(w.get("emph")) for w in ws] == [False, False, True, True, True, True, True]
    assert n == 5


def test_hook_giu_ca_cau_va_khong_sua_ban_goc():
    spec = {"captions": [
        {"start_sec": 0, "end_sec": 1, "text": "hook", "style": "hook", "words": _words([("hook", 1)])},
        {"start_sec": 1, "end_sec": 2, "text": "a b", "style": "caption", "words": _words([("a", .5), ("b", .5)])},
    ], "style": {"caption": {"size_px": 84}}}
    orig = copy.deepcopy(spec)
    out = add_chunks(copy.deepcopy(spec))
    assert "chunks" not in out["captions"][0] and out["captions"][1]["chunks"]
    assert out["style"]["caption"]["chunk_size_px"] == 113
    assert spec == orig


def test_emphasis_phai_co_trong_loi_doc():
    s = Script(topic="t", hook="SDXL-Lightning chạy nhanh", sections=["mỗi ảnh tám phẩy hai giây."], cta="x",
               emphasis=["SDXL-Lightning", "tám phẩy hai giây", "chín giây"])
    probs = _check_emphasis(s)
    assert len(probs) == 1 and "chín giây" in probs[0]


def test_min_sec_nhap_ve_phia_con_vua_mot_dong():
    # "kiến trúc MoE." (fixture 01): không được ra cụm quá rộng khi có phía khác vừa
    ws = _words([("dùng", .3), ("kiến", .29), ("trúc", .29), ("MoE.", .22)])
    fits = lambda t: len(t) <= 10
    for c in split_chunks(ws, 0, ws[-1]["end"], fits=fits):
        assert fits(" ".join(w["w"] for w in ws[c["from"]:c["to"]])) or c["to"] - c["from"] == 1


def test_tu_qua_rong_duoc_thu_nho():
    ws = _words([("Qwen3-30B-A3B", 1.6)])
    ch = split_chunks(ws, 0, 1.6, fits=lambda t: len(t) <= 8, width=lambda t: 8 / len(t))
    assert ch[0]["fit"] == round(8 / 13, 3)


def test_khong_xe_cum_nhan():
    ws = _words([(x, 0.3) for x in "xuống sáu trăm hai mươi bốn MiB.".split()])
    mark_emphasis(ws, ["sáu trăm hai mươi bốn MiB"])
    texts = _texts(ws, split_chunks(ws, 0, ws[-1]["end"]))
    assert "sáu trăm hai mươi bốn MiB." in " | ".join(texts).replace("xuống ", "")
    assert any(t.endswith("sáu trăm hai mươi bốn MiB.") for t in texts)
