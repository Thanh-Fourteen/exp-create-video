"""Probe stock video (2026-10-05) — research/18. Tiêu chí viết trước: ≥ 60% mô tả cảnh có ≥ 1 clip DỌC cao ≥ 1280px,
dài 4–30s. Đọc key từ .env (không in ra)."""
import json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path
env = dict(l.strip().split("=", 1) for l in Path(".env").read_text().splitlines() if "=" in l)
Q = [  # mô tả cảnh lấy từ kịch bản demo 2 kênh + chủ đề kho ý tưởng
 "hands holding smartphone reading text message", "person scrolling phone in dark room", "online shopping app on phone",
 "delivery package at door", "credit card payment on phone", "bank ATM withdrawing cash", "frozen meat thawing in water bowl",
 "refrigerator open food inside", "washing vegetables in sink", "rain on window", "flooded street motorbikes",
 "electric fan in hot room", "air conditioner remote control", "office meeting discussion", "friends talking cafe",
 "laptop typing code", "chatgpt on laptop screen", "phone notification close up", "money vietnamese dong", "street food vietnam"]
def pexels(q):
    r = urllib.request.Request("https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
        {"query": q, "orientation": "portrait", "per_page": 15}), headers={"Authorization": env["PEXELS_API_KEY"], "User-Agent": "xuong-video/1.0 (+personal pipeline)"})
    return json.load(urllib.request.urlopen(r, timeout=20))
rows = []
for q in Q:
    d = pexels(q)
    ok = [v for v in d.get("videos", []) if 4 <= v["duration"] <= 30 and v["height"] > v["width"] and v["height"] >= 1280]
    rows.append({"q": q, "total": d.get("total_results"), "usable": len(ok),
                 "sample": [f"https://www.pexels.com/video/{v['id']}" for v in ok[:2]]})
    print(f"{len(ok):>2}/15 · {q}")
    time.sleep(0.4)
hit = sum(r["usable"] > 0 for r in rows) / len(rows)
print(f"TỈ LỆ CÓ CLIP DÙNG ĐƯỢC: {hit:.0%}  (ngưỡng ≥ 60%)")
Path("research/probes/r-stock-probe.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
