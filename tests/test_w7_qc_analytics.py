"""W7 (UPGRADE-PLAN 2026-11-17): schema lỗi QC chung, một hướng sửa / mục tiêu, bảng đặc trưng + view 24h."""
from create_video import analytics as A
from create_video.qc import issues as I
from create_video.qc import loop as L

SPEC = {"shots": [{"id": "s1", "start_sec": 0.0, "end_sec": 3.0}, {"id": "s2", "start_sec": 3.0, "end_sec": 7.0}],
        "captions": [{"start_sec": 0.0, "end_sec": 2.9}, {"start_sec": 3.0, "end_sec": 6.9}]}
REC = {"blocking": [{"key": "t1:viền đen", "check": "viền đen", "detail": "dải tối 32px ở mép trên lúc 4.20s", "tier": "t1"},
                    {"key": "t4:1:x", "line": 1, "where": "câu 1", "why": "thiếu nguồn tier1", "tier": "t4"}],
       "suggestions": [{"key": "t2:s2", "shot_id": "s2", "issues": ["garbled_text_in_image"], "fix": "a cup", "tier": "t2"},
                       {"key": "t3:H:0", "line": 0, "why": "hook chậm", "tier": "t3"}]}


def test_chuan_hoa_co_moc_thoi_gian_va_thu_tu():
    out = I.normalize(REC, SPEC)
    assert [x["tier"] for x in out] == ["t4", "t1", "t2", "t3"]
    t1 = next(x for x in out if x["tier"] == "t1")
    assert t1["t_start"] == 4.2 and t1["shot_id"] == "s2" and t1["severity"] == "block" and t1["module"] == "render"
    t4 = next(x for x in out if x["tier"] == "t4")
    assert (t4["t_start"], t4["t_end"]) == (3.0, 6.9) and t4["module"] == "script"
    t2 = next(x for x in out if x["tier"] == "t2")
    assert t2["severity"] == "major" and t2["suggested_fix"] == "a cup" and t2["acceptance"]
    assert all(set(x) >= {"id", "tier", "t_start", "t_end", "shot_id", "line", "severity", "evidence", "module",
                          "suggested_fix", "acceptance"} for x in out)


def test_mot_huong_sua_t4_thang_t2():
    assert I.superseded_shots(I.normalize(REC, SPEC), SPEC) == {"s2"}


def test_plan_patches_bo_ve_lai_anh_cua_cau_dang_sua():
    from create_video.qc.loop import plan_patches

    tiers = {"t1": {"blocking": []}, "t2": {"suggestions": REC["suggestions"][:1]},
             "t3": {"summary": {}}, "t4": {"summary": {"notes": ["câu 1: thiếu nguồn"]}}}
    rec = {"tiers": tiers, "blocking": [], "suggestions": REC["suggestions"][:1],
           "issues": I.normalize({"blocking": REC["blocking"][1:], "suggestions": REC["suggestions"][:1]}, SPEC)}
    assert plan_patches(rec, SPEC)["visual"] is None
    assert plan_patches(rec)["visual"] is not None          # không có spec → hành vi cũ


def test_view_cung_tuoi():
    stats = [{"ts": 1000 + 3600 * h, "views": v} for h, v in ((3, 50), (23, 300), (27, 320), (60, 900))]
    assert A.views_at(stats, 1000) == 300
    assert A.views_at(stats[:1], 1000) is None             # mốc gần nhất cách 21 giờ → không đoán


def test_spearman_va_nguong_n():
    assert A.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert A.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    rows = [{"channel": "ai", "v24": i, **{f: i for f in A.NUMERIC}} for i in range(5)]
    assert "note" in A.summarize(rows)["ai"]
    rows = [{"channel": "ai", "v24": i, **{f: i for f in A.NUMERIC}} for i in range(12)]
    assert A.summarize(rows)["ai"]["rho_v24"]["duration_sec"] == 1.0


def test_dac_trung_tu_spec(tmp_path):
    import json

    spec = {"version": "1.4", "format": {"duration_sec": 10.0},
            "shots": [{"start_sec": 0, "end_sec": 4, "asset": {"kind": "stat"}, "motion": {}},
                      {"start_sec": 4, "end_sec": 10, "asset": {"kind": "video", "path": "demo/01.mp4"},
                       "motion": {"segments": [{}, {}]}}],
            "style": {"mascot": {"windows": [{"start_sec": 0, "end_sec": 1}]}}}
    (tmp_path / "video-spec.json").write_text(json.dumps(spec))
    (tmp_path / "script.json").write_text(json.dumps({"hook": "một hai ba", "sections": ["bốn năm"], "cta": "sáu"}))
    f = A.features(tmp_path, {"id": "x", "mp4": "video.mp4", "qc": {"rounds": 1, "remaining": []}})
    assert f["frame_changes_per_sec"] == 0.2 and f["demo_share"] == 0.6 and f["evidence_share"] == 0.4
    assert f["words_per_sec"] == 0.6 and f["mascot_share"] == 0.1


def _t1_rec(blocking):
    empty = {"blocking": [], "suggestions": [], "summary": {}, "ran": True}
    return {"tiers": {"t1": {**empty, "blocking": blocking}, "t2": dict(empty), "t3": dict(empty), "t4": dict(empty)},
            "blocking": blocking, "suggestions": []}


_T1_SPEC = {"shots": [
    {"id": "s1", "start_sec": 0.0, "end_sec": 4.0, "asset": {"kind": "image", "path": "stock/01.jpg", "alt": "laptop"}},
    {"id": "s2", "start_sec": 4.0, "end_sec": 8.0, "asset": {"kind": "list", "path": ""}},
    {"id": "s3", "start_sec": 8.0, "end_sec": 12.0, "asset": {"kind": "image", "path": "img/03.png"}}]}


def test_t1_pixel_trong_shot_anh_thi_thay_dung_shot():
    """2026-11-17 (1117-bench-ai-demo): phím laptop trong ảnh Pexels làm T1 "vùng an toàn (pixel)" chặn → thay ĐÚNG shot đó;
    ngưỡng không đổi — bản thay vẫn qua lại bộ kiểm cũ."""
    b = [{"key": "t1:vùng an toàn (pixel)", "check": "vùng an toàn (pixel)", "detail": "dải phải=0.58%", "at": [1.9, 9.0]}]
    plan = L.plan_patches(_t1_rec(b), _T1_SPEC)
    assert plan["stop"] is None and plan["visual"]["shot_ids"] == ["s1", "s3"]
    assert plan["visual"]["photo_ids"] == []


def test_t1_pixel_trong_the_chu_hoac_loi_khac_van_dung():
    b = [{"key": "t1:vùng an toàn (pixel)", "check": "vùng an toàn (pixel)", "detail": "x", "at": [5.0]}]   # thẻ list
    assert L.plan_patches(_t1_rec(b), _T1_SPEC)["stop"].startswith("T1 chặn")
    b2 = [{"key": "t1:loudness", "check": "loudness", "detail": "x"}]
    assert L.plan_patches(_t1_rec(b2), _T1_SPEC)["stop"].startswith("T1 chặn")
    b3 = [{"key": "t1:vùng an toàn (pixel)", "check": "vùng an toàn (pixel)", "detail": "x"}]                # không có mốc
    assert L.plan_patches(_t1_rec(b3), _T1_SPEC)["stop"].startswith("T1 chặn")
    assert L.plan_patches(_t1_rec([dict(b[0], at=[1.0])] + b2), _T1_SPEC)["stop"].startswith("T1 chặn")


def test_regen_stock_khi_chua_co_thu_muc_gen(tmp_path):
    """Video toàn stock không có gen/ → thay shot stock bằng ảnh AI từng crash FileNotFoundError (2026-11-17)."""
    import json

    from create_video.visual import regen

    (tmp_path / "stock").mkdir()
    (tmp_path / "stock" / "00.jpg").write_bytes(b"x")
    (tmp_path / "video-spec.json").write_text(json.dumps({"shots": [
        {"id": "s1", "start_sec": 0, "end_sec": 4, "asset": {"kind": "image", "path": "stock/00.jpg", "alt": "laptop"}}]}))
    jobs = regen.rerender(tmp_path, ["s1"], visual="color")
    assert (tmp_path / "stock" / "00.ai.png").exists() and (tmp_path / "gen" / "00.ai.png").exists()
    assert json.loads((tmp_path / "video-spec.json").read_text())["shots"][0]["asset"]["path"] == "stock/00.ai.png"
    assert jobs[0]["stock"]
