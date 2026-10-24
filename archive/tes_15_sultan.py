import os, asyncio, aiohttp, json, time
from dotenv import load_dotenv

load_dotenv()
E = os.environ
OUTPUT = "hasil_15_sultan.txt"

# === 15 MODEL EMAS ===
GOLDEN_15 = [
    # (provider, model, tier)
    ("chatanywhere", "gpt-6.1-sol", "S"),
    ("chatanywhere", "gpt-6-astra", "S"),
    ("chatanywhere", "gpt-4o", "S"),
    ("chatanywhere", "deepseek-v4-pro", "S"),
    ("cohere", "command-a-reasoning-08-2025", "S"),
    ("chatanywhere", "gpt-5.6-sol", "A"),
    ("chatanywhere", "gpt-6-luna", "A"),
    ("cohere", "command-a-plus-05-2026", "A"),
    ("mistral", "codestral-latest", "A"),
    ("groq", "qwen/qwen3.8-27b", "A"),
    ("chatanywhere", "gpt-4.1", "B"),
    ("chatanywhere", "deepseek-v4.1-flash", "B"),
    ("cloudflare", "@cf/openai/gpt-oss-120b", "B"),
    ("gemini", "gemini-3.6-flash", "B"),
    ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free", "B"),
]

PROVIDERS = {
    "chatanywhere": {"url": "https://api.chatanywhere.tech/v1/chat/completions", "key": E.get("CHATANYWHERE_API_KEY"), "type": "openai"},
    "cloudflare": {"url": "https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/", "key": E.get("CF_API_TOKEN"), "acc": E.get("CF_ACCOUNT_ID"), "type": "cloudflare"},
    "gemini": {"url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}", "key": E.get("GEMINI_API_KEY"), "type": "gemini"},
    "mistral": {"url": "https://api.mistral.ai/v1/chat/completions", "key": E.get("MISTRAL_API_KEY"), "type": "openai"},
    "openrouter": {"url": "https://openrouter.ai/api/v1/chat/completions", "key": E.get("OPENROUTER_API_KEY"), "type": "openai"},
    "groq": {"url": "https://api.groq.com/openai/v1/chat/completions", "key": E.get("GROQ_API_KEY"), "type": "openai"},
    "cohere": {"url": "https://api.cohere.com/v2/chat", "key": E.get("COHERE_API_KEY"), "type": "cohere"},
}

# === 3 PERTANYAAN SULIT ===
QUESTIONS = [
    {
        "label": "LOGIKA",
        "prompt": "Seorang pria punya 53 stoking di laci gelap: 21 merah, 15 biru, 17 hitam. Berapa minimal stoking yang harus dia ambil supaya PASTI punya sepasang warna yang sama? Jelaskan reasoning-mu secara singkat."
    },
    {
        "label": "CODING",
        "prompt": "Jelaskan perbedaan mendasar antara mutex, semaphore, dan spinlock. Untuk tiap mekanisme, sebutkan satu skenario konkret di mana dia JAUH lebih baik dari dua lainnya. Jawab maksimal 200 kata."
    },
    {
        "label": "REASONING",
        "prompt": "Jika 3 kucing menangkap 3 tikus dalam 3 menit, berapa kucing yang dibutuhkan untuk menangkap 100 tikus dalam 100 menit? Tunjukkan caranya, jangan cuma jawaban akhir."
    }
]

async def call_model(session, provider, model, prompt):
    cfg = PROVIDERS.get(provider)
    if not cfg: return None, "SKIP"

    headers = {"Content-Type": "application/json"}
    if cfg["key"]: headers["Authorization"] = f"Bearer {cfg['key']}"

    messages = [
        {"role": "system", "content": "Kamu asisten AI pinter. Jawab dengan reasoning jelas, bahasa Indonesia, padat tapi lengkap."},
        {"role": "user", "content": prompt}
    ]

    if cfg["type"] == "gemini":
        url = cfg["url"].format(model=model, key=cfg["key"])
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
    elif cfg["type"] == "cloudflare":
        url = f"{cfg['url'].format(acc=cfg['acc'])}{model}"
        payload = {"messages": messages, "max_tokens": 800}
    elif cfg["type"] == "cohere":
        url = cfg["url"]
        payload = {"model": model, "messages": messages, "max_tokens": 800}
    else:
        url = cfg["url"]
        payload = {"model": model, "messages": messages, "max_tokens": 800}

    start = time.time()
    try:
        async with session.post(url, headers=headers, json=payload, timeout=60) as r:
            elapsed = round(time.time() - start, 2)
            if r.status == 200:
                data = await r.json()
                if cfg["type"] == "gemini":
                    text = data['candidates'][0]['content']['parts'][0]['text']
                elif cfg["type"] == "cloudflare":
                    text = data['result']['response']
                else:
                    text = data['choices'][0]['message']['content']
                return text.strip(), elapsed
            elif r.status in [429, 402, 403]:
                return None, f"LIMIT({r.status})"
            else:
                return None, f"HTTP{r.status}"
    except asyncio.TimeoutError:
        return None, "TIMEOUT"
    except Exception as e:
        return None, type(e).__name__

async def main():
    print(f"🚀 TES 15 MODEL EMAS × 3 PERTANYAAN SULIT")
    print(f"⏱️  Estimasi: ~3-4 menit\n")

    with open(OUTPUT, "w") as f:
        f.write("=== TES 15 MODEL EMAS ===\n\n")

    # Statistik buat ranking
    stats = {m: {"success": 0, "total_time": 0, "answers": {}} for _, m, _ in GOLDEN_15}

    async with aiohttp.ClientSession() as session:
        for qi, q in enumerate(QUESTIONS, 1):
            print("\n" + "="*70)
            print(f"📝 PERTANYAAN {qi}/3 — {q['label']}")
            print("="*70)
            print(f"Q: {q['prompt'][:100]}...\n")

            with open(OUTPUT, "a") as f:
                f.write("\n" + "="*70 + f"\nPERTANYAAN {qi}: {q['label']}\n" + "="*70 + "\n")
                f.write(f"Q: {q['prompt']}\n\n")

            for provider, model, tier in GOLDEN_15:
                print(f"⏳ [{tier}] {provider} -> {model}")
                answer, elapsed = await call_model(session, provider, model, q["prompt"])

                with open(OUTPUT, "a") as f:
                    f.write(f"\n--- [{tier}] {provider} -> {model} ---\n")
                    if answer:
                        f.write(f"[WAKTU: {elapsed}s]\n{answer}\n")
                        stats[model]["success"] += 1
                        stats[model]["total_time"] += elapsed if isinstance(elapsed, (int, float)) else 0
                        stats[model]["answers"][q["label"]] = answer[:500]
                    else:
                        f.write(f"[GAGAL: {elapsed}]\n")
                        stats[model]["answers"][q["label"]] = f"GAGAL: {elapsed}"

                if answer:
                    print(f"   ✅ {elapsed}s — {answer[:80]}...")
                else:
                    print(f"   ❌ {elapsed}")

                await asyncio.sleep(2)

    # === RANKING ===
    print("\n\n" + "="*70)
    print("🏆 RANKING BERDASARKAN JUMLAH SUKSES + KECEPATAN")
    print("="*70)

    with open(OUTPUT, "a") as f:
        f.write("\n\n" + "="*70 + "\nRANKING\n" + "="*70 + "\n")

    # Sort: yang sukses 3 duluan, lalu rata-rata waktu
    ranking = []
    for provider, model, tier in GOLDEN_15:
        s = stats[model]
        avg = round(s["total_time"] / s["success"], 2) if s["success"] > 0 else 999
        ranking.append((tier, provider, model, s["success"], avg))

    # Sort by: -success (paling banyak duluan), lalu avg (paling cepet duluan)
    ranking.sort(key=lambda x: (-x[3], x[4]))

    for i, (tier, provider, model, success, avg) in enumerate(ranking, 1):
        line = f"{i:>2}. [{tier}] {provider:<15} {model:<45} {success}/3 sukses, avg {avg}s"
        print(line)
        with open(OUTPUT, "a") as f:
            f.write(line + "\n")

    print(f"\n📄 Detail jawaban tersimpan di: {OUTPUT}")
    print(f"   Cek isi: cat {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
