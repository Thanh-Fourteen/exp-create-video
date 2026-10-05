"""Tổng hợp metadata kênh khảo sát (out/tham-khao/kenh/<niche>-<handle>.json) — research/15."""
import glob, json, statistics as st, sys
niche = sys.argv[1]
rows, per = [], []
for f in sorted(glob.glob(f"out/tham-khao/kenh/{niche}-*.json")):
    e = json.load(open(f)).get("entries") or []
    h = f.split(f"{niche}-", 1)[1][:-5]
    v = [x.get("view_count") or 0 for x in e]
    d = [x.get("duration") or 0 for x in e]
    if not v:
        continue
    per.append((h, len(e), int(st.median(v)), max(v), int(st.median(d))))
    for x in e:
        rows.append({"h": h, "v": x.get("view_count") or 0, "d": x.get("duration") or 0, "t": (x.get("title") or "")[:90],
                     "url": x.get("url") or x.get("webpage_url"), "id": x.get("id"),
                     "rel": (x.get("view_count") or 0) / max(st.median(v), 1)})
print("kênh | n | trung vị view | max | trung vị dài(s)")
for p in sorted(per, key=lambda p: -p[2]):
    print(" | ".join(map(str, p)))
print("\nTOP 20 theo view:")
for r in sorted(rows, key=lambda r: -r["v"])[:20]:
    print(f"{r['v']:>9} · {r['d']:>4}s · ×{r['rel']:.1f} · @{r['h']} · {r['t']}")
print("\nTOP 15 theo 'vượt trung vị kênh' (×):")
for r in sorted(rows, key=lambda r: -r["rel"])[:15]:
    print(f"×{r['rel']:>5.1f} · {r['v']:>8} · {r['d']:>4}s · @{r['h']} · {r['t']}")
# độ dài vs hiệu quả
b = {}
for r in rows:
    k = "<30" if r["d"] < 30 else "30-60" if r["d"] < 60 else "60-120" if r["d"] < 120 else "120-180" if r["d"] < 180 else "180+"
    b.setdefault(k, []).append(r["rel"])
print("\nĐộ dài → trung vị (view / trung vị kênh):", {k: (len(v), round(st.median(v), 2)) for k, v in b.items()})
json.dump(rows, open(f"out/tham-khao/{niche}-rows.json", "w"), ensure_ascii=False)
