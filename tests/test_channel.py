"""Kênh (2026-10-04, research/13 §5): cấu hình theo kênh, shot chat/list, luật tier1 của T4. Không LLM/mạng."""

from __future__ import annotations

import pytest

from create_video import channel
from create_video.agents.scriptwriter import Script, Shot, _check_shots, _system_prompt
from create_video.qc import t4_facts as t4
from create_video.team.snapshot import Snapshot, classify


@pytest.fixture(autouse=True)
def _reset():
    import os

    os.environ.pop("CV_CHANNEL", None)
    yield
    os.environ.pop("CV_CHANNEL", None)   # activate() ghi env — không để rò sang test khác


def test_hai_kenh_va_pillar_mot_nguon():
    ids = [c.id for c in channel.all_channels()]
    assert ids[:2] == ["ai", "meo"]
    assert channel.current().id == "ai"
    assert "tin_nong" in channel.get("ai").pillars
    meo = channel.get("meo")
    assert set(meo.pillars) == {"giao_tiep", "tien_bac", "phap_luat", "dien_thoai", "bep_an_toan", "theo_mua"}
    assert abs(sum(p["mix"] for p in meo.pillars.values()) - 1.0) < 1e-6
    assert meo.rubric_path.exists()


def test_tang_nguon():
    meo = channel.get("meo")
    assert meo.tier("https://vfa.gov.vn/canh-bao/x") == 1
    assert meo.tier("https://www.mayoclinic.org/a") == 2
    assert meo.tier("https://vnexpress.net/a") == 3
    assert meo.tier("https://random.blog/a") is None


def test_allowlist_theo_kenh():
    assert classify("https://vfa.gov.vn/x")[0] == "blocked"      # kênh AI: không đối chiếu nguồn y tế
    channel.activate("meo")
    assert classify("https://vfa.gov.vn/x")[0] == "html"
    assert classify("https://random.blog/x")[0] == "blocked"


def test_prompt_kenh_meo_co_chat_list_khong_co_code():
    channel.activate("meo")
    p = _system_prompt(40)
    assert "Sống Khéo" in p and "`chat`" in p and "`list`" in p
    assert "`code`: đoạn code" not in p and "huggingface.co/<org>" not in p
    channel.activate("ai")
    p = _system_prompt(40)
    assert "`code`: đoạn code" in p and "`chat`" not in p


def _chat(n=2, text="Thứ năm em gửi bản đầu ạ"):
    return {"messages": [{"from": "me" if i % 2 else "them", "text": text} for i in range(n)]}


def test_kiem_shot_chat_list():
    channel.activate("meo")
    base = dict(topic="t", hook="h", sections=["a", "b", "c"], cta="x")
    ok = Script(**base, shots=[
        Shot(prompt="p", line=0, kind="chat", chat=_chat()),
        Shot(prompt="p", line=1, kind="list", list={"items": [{"text": "Cà chua", "mark": "no"},
                                                             {"text": "Hành tây", "mark": "no"}]}),
        Shot(prompt="p", line=2, kind="stock", query="hands holding smartphone"),
        Shot(prompt="q", line=3, kind="stock", query="vietnamese street market")])
    assert _check_shots(ok) == []
    bad = Script(**base, shots=[
        Shot(prompt="p", line=0, kind="chat", chat=_chat(n=1)),
        Shot(prompt="p", line=1, kind="list", list={"items": [{"text": "x" * 40}, {"text": "y"}]}),
        Shot(prompt="p", line=2, kind="code", code={"lang": "text", "lines": ["a"]})])
    probs = " | ".join(_check_shots(bad))
    assert "2-5 tin nhắn" in probs and "1-34 ký tự" in probs and "không dùng kind 'code'" in probs


def test_list_tren_hinh_thanh_claim():
    s = Script(topic="t", hook="h", sections=["a"], cta="x",
               shots=[Shot(prompt="p", line=1, kind="list", list={"title": "Đừng cho vào tủ lạnh",
                                                                  "items": [{"text": "Cà chua"}, {"text": "Hành"}]})])
    cl = t4.screen_claims(s)
    assert [c.claim for c in cl] == ["[trên hình] Đừng cho vào tủ lạnh: Cà chua", "[trên hình] Đừng cho vào tủ lạnh: Hành"]


def _snap(url, text="Không nên rã đông thịt ở nhiệt độ phòng quá hai giờ."):
    return Snapshot(url=url, kind="html", sha256="x", fetched_at="", chars=len(text), path="", text=text)


def test_claim_suc_khoe_can_tier1():
    channel.activate("meo")
    s = Script(topic="t", hook="h", sections=["a", "b"], cta="x")
    claim_cls = t4._extract_model().model_fields["claims"].annotation.__args__[0]   # Literal có food_safety
    claims = [claim_cls(line=1, claim="rã đông quá hai giờ không an toàn", type="food_safety")]
    quote = "Không nên rã đông thịt ở nhiệt độ phòng quá hai giờ."
    v = [t4.Verdict(claim_id=0, verdict="supported", source_id="S1", quote=quote)]
    thr = {"max_contradictions": 0, "max_unverified_claims": 3}
    rep_bao = t4.build_report(s, claims, v, {"S1": _snap("https://vnexpress.net/a")}, [], thr)
    assert rep_bao.verdict == "block" and "tier1" in rep_bao.issues[0]["why"]
    rep_vfa = t4.build_report(s, claims, v, {"S1": _snap("https://vfa.gov.vn/a")}, [], thr)
    assert rep_vfa.verdict == "pass"
    channel.activate("ai")   # kênh AI không có luật này
    assert t4.build_report(s, claims, v, {"S1": _snap("https://vnexpress.net/a")}, [], thr).verdict == "pass"


def test_caption_kenh_meo():
    from create_video.publish import build_caption

    channel.activate("meo")
    cap = build_caption({"caption": "Rã đông thịt đúng cách", "pillar": "bep_an_toan",
                         "hashtags": ["meobep", "radong", "thit", "antoan", "bep"]})
    assert "không thay lời khuyên" in cap
    tags = cap.split("\n")[-1].split()
    assert len(tags) == 5 and "#songkheo" in tags and "#meovat" in tags
    channel.activate("ai")
    assert "#songkheo" not in build_caption({"caption": "x", "hashtags": ["a", "b", "c"]})


# ── web: đổi kênh, tạo job theo kênh, kho ý tưởng (DB tạm, không đụng hàng đợi thật) ─────────────────────────
@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("XUONG_DEV", "1")
    from create_video.web import app as appmod, db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "x.db")
    monkeypatch.setattr(appmod, "DEV", True)
    db.init()
    from fastapi.testclient import TestClient

    return TestClient(appmod.app), db


def test_web_doi_kenh_va_tao_job(client):
    c, db = client
    r = c.get("/k/meo?next=/ideas", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/ideas" and "kenh=meo" in r.headers["set-cookie"]
    c.cookies.set("kenh", "meo")
    page = c.get("/").text
    assert "Tạo video cho Sống Khéo" in page and "--color-primary: #F2B544" in page
    assert c.get("/k/khong-co").status_code == 404
    assert c.get("/k/meo?next=//evil.com", follow_redirects=False).headers["location"] == "/"
    r = c.post("/jobs", data={"topic": "Từ chối cho bạn vay tiền mà không mất lòng", "voice": "tony",
                              "duration": 45, "channel": "meo", "pillar": "giao_tiep", "idea": "g01"},
               follow_redirects=False)
    assert r.status_code == 303
    j = db.list_jobs()[0]
    assert (j["channel"], j["pillar"], j["idea_id"]) == ("meo", "giao_tiep", "g01")
    assert db.idea_rows("meo")["g01"]["status"] == "used"
    from create_video.web.worker import command

    cmd = command(j)
    assert cmd[cmd.index("--channel") + 1] == "meo" and cmd[cmd.index("--pillar") + 1] == "giao_tiep"


def test_web_kho_y_tuong(client):
    c, db = client
    c.cookies.set("kenh", "meo")
    assert "Kho" in c.get("/ideas").text
    c.post("/ideas", data={"title": "Cách nhắn tin đòi nợ bạn bè khéo léo", "pillar": "giao_tiep"})
    tony = [r for r in db.idea_rows("meo").values() if r["source"] == "tony"]
    assert len(tony) == 1
    assert c.post("/ideas", data={"title": "ngắn", "pillar": "giao_tiep"}).status_code == 400
    c.post("/ideas/b01/status", data={"status": "skip"})
    assert "Đông đá" in c.get("/ideas?s=skip").text
    for path in ("/library", "/stats", "/queue", "/settings"):
        assert c.get(path).status_code == 200
    c.cookies.set("kenh", "all")
    assert "Tất cả kênh" in c.get("/library").text


def test_goi_y_an_chu_de_da_lam_va_khong_quan_tam(client, monkeypatch):
    c, db = client
    c.cookies.set("kenh", "meo")
    from create_video.web.library import suggestions

    first = suggestions("meo", 6)
    t0 = next(t for t in first if t["kinds"] != ["mùa"])
    # tạo video từ gợi ý → biến khỏi gợi ý (Tony 2026-10-04)
    c.post("/jobs", data={"topic": t0["title"], "voice": "tony", "duration": 45, "channel": "meo",
                          "pillar": t0["pillar"], "idea": t0["idea_id"] or ""})
    assert t0["title"] not in [t["title"] for t in suggestions("meo", 50)]
    # ✕ không quan tâm
    t1 = suggestions("meo", 6)[0]
    html = c.post("/suggest/dismiss", data={"c": "meo", "title": t1["title"], "idea": t1["idea_id"] or ""}).text
    assert t1["title"] not in html and 'id="suggest"' in html
    # đổi lô: lô 1 khác lô 0
    p0 = {t["title"] for t in suggestions("meo", 6, 0)}
    p1 = {t["title"] for t in suggestions("meo", 6, 1)}
    assert p1 and p1 != p0
    assert "Đổi gợi ý" in c.get("/p/suggest?c=meo&page=1").text


def test_tim_chu_de_moi_chay_nen(client, monkeypatch):
    c, db = client
    import subprocess

    calls = []

    class FakeP:
        returncode = None

        def poll(self):
            return None

    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: calls.append(cmd) or FakeP())
    html = c.post("/suggest/refresh", data={"c": "meo"}).text
    assert calls and calls[0][2] == "create_video.team.idea_gen" and "Đang tìm tin mới" in html
    c.post("/suggest/refresh", data={"c": "meo"})          # đang chạy → không chạy chồng
    assert len(calls) == 1
    c.post("/suggest/refresh", data={"c": "ai"})
    assert calls[1][2:] == ["create_video.team.trend_scout", "--slot", "r"]


def test_idea_gen_loc_trung():
    from create_video.team.idea_gen import is_dup

    assert is_dup("Rã đông thịt đúng cách: ba cách an toàn", ["Rã đông thịt đúng cách: ba cách an toàn, một cách nên tránh"])
    assert not is_dup("Bật bảo mật hai lớp cho Zalo", ["Rã đông thịt đúng cách"])
