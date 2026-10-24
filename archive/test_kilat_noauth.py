import aiohttp
import asyncio
import time

# Endpoint No-Auth
PROVIDERS = {
    "UncloseAI": "https://hermes.ai.unturf.com/v1",
    "KiloCode": "https://api.kilo.ai/api/gateway",
    "OVH_AI": "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
    "ApiAirforce": "https://api.airforce/v1"
}

OUTPUT_FILE = "hasil_kilat_noauth.txt"

# Filter hanya buang yang jelas-jelas bukan teks (biar gak buang waktu)
BAD_WORDS = ["suno", "whisper", "tts", "dall-e", "stable-diffusion", "flux", "midjourney", "image-1", "embedding"]

# Batas maksimal request barengan biar gak dianggap DDoS
SEMAPHORE = asyncio.Semaphore(15) 
SUCCESS_COUNT = 0
TOTAL_TESTED = 0

async def get_models(session, base_url):
    try:
        async with session.get(f"{base_url}/models", timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                if isinstance(data, dict) and "data" in data:
                    return [m["id"] for m in data["data"]]
                elif isinstance(data, list):
                    return [m.get("id") or m.get("name") for m in data if isinstance(m, dict)]
    except:
        pass
    return []

async def test_model(session, provider, base_url, model):
    global SUCCESS_COUNT, TOTAL_TESTED
    async with SEMAPHORE:
        url = f"{base_url}/chat/completions"
        payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 5}
        try:
            async with session.post(url, json=payload, timeout=15) as r:
                if r.status == 200:
                    SUCCESS_COUNT += 1
                    res = f"✅ [TERBANG] {provider} -> {model}"
                elif r.status == 402:
                    res = f"💸 [BAYAR] {provider} -> {model}"
                elif r.status == 429:
                    res = f"⚠️ [LIMIT] {provider} -> {model}"
                else:
                    res = f"❌ [GAGAL] {provider} -> {model} (HTTP {r.status})"
        except Exception:
            res = f"❌ [ERROR] {provider} -> {model}"
            
        TOTAL_TESTED += 1
        # Tampilkan progress tiap 50 model
        if TOTAL_TESTED % 50 == 0:
            print(f"⏳ Progress: {TOTAL_TESTED} model dites. ({SUCCESS_COUNT} hidup)")
            
        with open(OUTPUT_FILE, "a") as f: 
            f.write(res + "\n")
        await asyncio.sleep(0.1) # Jeda super singkat

async def main():
    global TOTAL_TESTED
    print("🚀 MEMULAI TES KILAT (Concurrent 15 Requests)...")
    start_time = time.time()
    
    with open(OUTPUT_FILE, "w") as f: f.write("=== HASIL TES KILAT NO-AUTH ===\n\n")
    
    async with aiohttp.ClientSession() as session:
        all_tasks = []
        total_models = 0
        
        for provider, base_url in PROVIDERS.items():
            print(f"📦 Menarik model dari {provider}...")
            models = await get_models(session, base_url)
            
            # Filter model sampah
            models = [m for m in models if not any(bw in m.lower() for bw in BAD_WORDS)]
            total_models += len(models)
            print(f"   Dapet {len(models)} model buat dites.")
            
            for model in models:
                all_tasks.append(test_model(session, provider, base_url, model))
                
        print(f"\n🔥 NEMBAK {total_models} MODEL SECARA BERSAMAAN! (Sabar ~5 menit)\n")
        await asyncio.gather(*all_tasks)
        
    elapsed = round(time.time() - start_time, 1)
    print(f"\n✅ SELESAI dalam {elapsed} detik!")
    print(f"🏆 Total Model Hidup (✅): {SUCCESS_COUNT} dari {TOTAL_TESTED} model.")
    print(f"📄 Cek file {OUTPUT_FILE} buat liat semuanya.")

if __name__ == "__main__":
    asyncio.run(main())
