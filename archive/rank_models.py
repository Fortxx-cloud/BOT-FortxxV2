import json, glob
from collections import defaultdict

SCORE = {"BENAR": 3, "REVIEW": 1, "SALAH": 0}
FAST = 5
SLOW = 15

def load_all():
    merged = []
    files = sorted(glob.glob("hasil_kubu_*.json"))
    if not files:
        print("❌ Nggak ada hasil_kubu_*.json. Run 3 kubu dulu!")
        return []
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        for r in data.get("ok", []):
            r["kubu"] = data["kubu"]
            merged.append(r)
        print(f"📂 {f}: {len(data.get('ok', []))} sukses, {len(data.get('fail', []))} gagal")
    return merged

def categorize(r):
    score = SCORE.get(r["grade"], 0)
    lat = r["elapsed"]
    if score == 3 and lat <= FAST:   return "S1_TOP"
    if score == 3 and lat <= SLOW:   return "S2_OK"
    if score == 3:                   return "S3_SLOW"
    if score == 1:                   return "S4_REVIEW"
    return "S5_SALAH"

def main():
    models = load_all()
    if not models: return

    for r in models:
        r["score"] = SCORE.get(r["grade"], 0)
        r["cat"] = categorize(r)

    models.sort(key=lambda r: (-r["score"], r["elapsed"]))

    cats = defaultdict(list)
    for r in models: cats[r["cat"]].append(r)

    def show(cat, title, icon):
        rows = cats.get(cat, [])
        if not rows: return
        print(f"\n{icon} {title} ({len(rows)} model)")
        print("─" * 72)
        for i, r in enumerate(rows, 1):
            print(f"  {i:>2}. {r['elapsed']:>6}s  {r['provider']:<12} → {r['model']}")

    print("\n" + "═" * 72)
    print("🏆 RANKING FINAL")
    print("═" * 72)
    print(f"Total sukses dinilai: {len(models)}")
    print(f"  ✅ BENAR : {sum(1 for r in models if r['grade']=='BENAR')}")
    print(f"  🟡 REVIEW: {sum(1 for r in models if r['grade']=='REVIEW')}")
    print(f"  🟠 SALAH : {sum(1 for r in models if r['grade']=='SALAH')}")

    show("S1_TOP",    "TIER 1 — BENAR & CEPAT (<5s, primary bot DC)", "🥇")
    show("S2_OK",     "TIER 2 — BENAR & SEDANG (5-15s)",               "🥈")
    show("S3_SLOW",   "TIER 3 — BENAR tapi LAMBAT (>15s, fallback)",    "🥉")
    show("S4_REVIEW", "TIER 4 — Perlu review manual",                   "🟡")

    print("\n" + "═" * 72)
    print("🔗 REKOMENDASI FALLBACK CHAIN (1 per provider, BENAR terbaik)")
    print("═" * 72)
    best_per_provider = {}
    for r in models:
        if r["grade"] != "BENAR": continue
        p = r["provider"]
        if p not in best_per_provider or r["elapsed"] < best_per_provider[p]["elapsed"]:
            best_per_provider[p] = r
    for p, r in sorted(best_per_provider.items(), key=lambda x: x[1]["elapsed"]):
        print(f"  {r['elapsed']:>6}s  {p:<12} → {r['model']}")

    out = {
        "total": len(models),
        "benar": sum(1 for r in models if r["grade"] == "BENAR"),
        "review": sum(1 for r in models if r["grade"] == "REVIEW"),
        "salah": sum(1 for r in models if r["grade"] == "SALAH"),
        "ranking": [{k: r[k] for k in ("provider","model","kubu","grade","elapsed","cat")} for r in models],
        "fallback_chain": [
            {"provider": p, "model": r["model"], "elapsed": r["elapsed"]}
            for p, r in sorted(best_per_provider.items(), key=lambda x: x[1]["elapsed"])
        ],
    }
    with open("hasil_final.json", "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"\n💾 hasil_final.json disimpan")

if __name__ == "__main__":
    main()
