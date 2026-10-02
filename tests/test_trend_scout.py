"""P5.S1: trend scout — phần code thuần (không mạng, không model, không LLM)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from create_video.team import trend_scout as ts
from create_video.team.snapshot import Snapshot

NOW = datetime(2026, 10, 2, 13, 0, tzinfo=timezone.utc)


def _it(url, src="hn", kind="forum", v=1.0, hours=1, title="x"):
    return ts.Item(url=url, title=title, source=src, kind=kind,
                   published_at=ts._iso(NOW - timedelta(hours=hours)), velocity_raw=v)


def test_canon_url():
    assert ts.canon_url("https://arxiv.org/pdf/2509.12345v2") == "https://arxiv.org/abs/2509.12345"
    assert ts.canon_url("https://www.Example.com/a/?utm_source=x&id=3#top") == "https://example.com/a?id=3"


def test_parse_feed_rss_va_atom():
    rss = "<rss><channel><item><title>A</title><link>https://a.vn/1</link><pubDate>Thu, 01 Oct 2026 10:00:00 +0700</pubDate><description>&lt;p&gt;x&lt;/p&gt;</description></item></channel></rss>"
    atom = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>B</title><link href="https://b.com/2"/><published>2026-10-01T00:00:00Z</published></entry></feed>'
    assert ts.parse_feed(rss)[0]["link"] == "https://a.vn/1"
    assert ts.parse_feed(atom)[0]["link"] == "https://b.com/2"


def test_normalize_percentile_trong_nguon_va_decay():
    items = [_it("u1", v=1), _it("u2", v=10), _it("u3", v=100, hours=48),
             _it("b1", src="openai", kind="blog", v=0)]
    ts.normalize(items, NOW, ts.load_config()["scoring"])
    assert items[0].velocity < items[1].velocity < items[2].velocity
    assert items[3].velocity == 0.5                    # blog không có số đo
    assert abs(items[2].decay - np.exp(-1)) < 1e-3     # 48h → e^-1


def test_cluster_noi_theo_cosine_va_tran_kich_thuoc():
    v = np.array([[1, 0], [0.99, 0.141], [0, 1], [0.995, 0.0998]], dtype="float32")
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    groups = sorted(sorted(g) for g in ts.cluster(v, 0.95, 12))
    assert groups == [[0, 1, 3], [2]]
    # không nối chuỗi: 0~1 và 1~2 nhưng 0≁2 → 2 không vào cụm của hạt nhân 0
    w = np.array([[1, 0], [0.97, 0.243], [0.88, 0.475]], dtype="float32")
    w /= np.linalg.norm(w, axis=1, keepdims=True)
    assert sorted(sorted(g) for g in ts.cluster(w, 0.95, 12)) == [[0, 1], [2]]
    assert max(len(g) for g in ts.cluster(v, 0.95, 2)) == 2


def test_diem_thuong_nhieu_loai_nguon_va_bo_cum_toan_arxiv():
    cfg = ts.load_config()
    items = [_it("a", src="hn"), _it("b", src="genk_ai", kind="news_vn"), _it("c", src="arxiv", kind="paper")]
    for i in items:
        i.velocity = 1.0
    v = np.eye(3, dtype="float32")
    cl = ts.score_clusters(items, [[0, 1], [2]], v, None, [], cfg)
    assert len(cl) == 1                                # cụm chỉ có arXiv không thành topic
    assert cl[0].kinds == ["forum", "news_vn"] and cl[0].parts["multi_kind"] == 0.5 and cl[0].parts["vn_fit"] == 0.5


def test_trung_video_da_lam_bi_tru_diem():
    cfg = ts.load_config()
    items = [_it("a")]
    items[0].velocity = 1.0
    v = np.array([[1.0, 0.0]], dtype="float32")
    base = ts.score_clusters(items, [[0]], v, None, [], cfg)[0].hot
    dup = ts.score_clusters(items, [[0]], v, np.array([[1.0, 0.0]], dtype="float32"), [], cfg)[0].hot
    assert abs(dup - base * cfg["scoring"]["done_penalty"]) < 1e-6


def test_claim_chi_giu_khi_trich_co_nguyen_van_trong_snapshot():
    snap = Snapshot(url="https://a.com/x", kind="article", sha256="abc", fetched_at="", chars=50, path="p",
                    text="Qwen3.5 was released on September 30 with a 256K context window.")
    c = ts.Cluster(id=0, items=[])
    j = ts.JudgeOut(clusters=[ts.JudgeItem(cluster_id=0, label_vi="Qwen3.5", vn_fit_reason="r", explainable_40s=True,
                                           explain_reason="e", claims=[
        ts.ClaimOut(text="đúng", quote="released on September 30", url="https://a.com/x"),
        ts.ClaimOut(text="bịa", quote="released on October 5", url="https://a.com/x"),
        ts.ClaimOut(text="url lạ", quote="256K context", url="https://b.com/y")])])
    dropped = ts.gate_claims([c], j, {"https://a.com/x": snap})
    assert dropped == 2 and [x["text"] for x in c.claims] == ["đúng"]
    assert c.claims[0]["snapshot_sha256"] == "abc"


def test_entity_keys_va_luat_noi():
    k = ts.entity_keys
    assert k("Qwen/Qwen-Image-2.1") == k("tamimKTH/image-studio: Local Qwen-Image 2.1 studio") == {"qwen-image"}
    assert "gpt-6.1" in k("Hủy ra mắt GPT-6.1 Astra, OpenAI giới thiệu GPT-6.1 Sol")
    assert k("Trợ lý Muse bị phàn nàn") & k("Không được cấp quyền, Muse AI của Meta")
    assert k("Identity Management for Agentic AI [pdf] (2025)") == set()     # Title Case
    assert not (k("OpenAI ra mắt dots") & k("OpenAI tung ra hơn 20 sản phẩm"))  # chung tên hãng ≠ cùng chủ đề
    sc = {"cluster_cos": 0.82, "cluster_cos_strong": 0.93}
    assert ts.linked(0.95, set(), set(), sc)
    assert ts.linked(0.85, {"muse"}, {"muse"}, sc) and not ts.linked(0.85, {"a"}, {"b"}, sc)
    assert not ts.linked(0.80, {"muse"}, {"muse"}, sc)
