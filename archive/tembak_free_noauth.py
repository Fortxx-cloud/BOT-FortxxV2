import aiohttp
import asyncio

# Endpoint No-Auth
PROVIDERS = {
    "UncloseAI": "https://hermes.ai.unturf.com/v1",
    "KiloCode": "https://api.kilo.ai/api/gateway",
    "OVH_AI": "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
    "ApiAirforce": "https://api.airforce/v1"
}

OUTPUT_FILE = "hasil_free_noauth.txt"

# Filter model yang bukan buat chat (gambar, audio, dll)
BAD_WORDS = ["image", "suno", "audio", "tts", "whisper", "embed", "vision-ocr", "moderation", "guard", "dall-e", "stable-diffusion", "flux", "midjourney"]

async def get_models(session, base_url):
    try:
        async with session.get(f"{base_url}/models", timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                if isinstance(data, dict) and "data" in data:
                    return [m["id"] for m in data["data"]]
                elif isinstance(data, list):
                    return [m.get("id") or m.get("name") for m in data if isinstance(m, dict)]
    except Exception:
        pass
    return []

async def test_model(session, provider, base_url, model):
    url = f"{base_url}/chat/completions"
    payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    try:
        async with session.post(url, json=payload, timeout=15) as r:
            if r.status == 200:
                return f"✅ [TERBANG] {provider} -> {model}"
            elif r.status == 402:
                return f"💸 [BAYAR] {provider} -> {model} (HTTP 402)"
            elif r.status == 429:
                return f"⚠️ [LIMIT] {provider} -> {model} (HTTP 429)"
            else:
                return f"❌ [GAGAL] {provider} -> {model} (HTTP {r.status})"
    except Exception:
        return f"❌ [ERROR] {provider} -> {model}"

async def main():
    print("⏳ Memulai TES KHUSUS MODEL FREE (No-Auth)...\n")
    
    with open(OUTPUT_FILE, "w") as f: f.write("=== HASIL TES MODEL FREE NO-AUTH ===\n\n")
    
    async with aiohttp.ClientSession() as session:
        for provider, base_url in PROVIDERS.items():
            print(f"\n📦 Menarik model dari {provider}...")
            all_models = await get_models(session, base_url)
            
            # 1. Filter buang model gambar/audio
            chat_models = [m for m in all_models if not any(bw in m.lower() for bw in BAD_WORDS)]
            
            # 2. Filter KHUSUS yang ada tulisan 'free' (kalau providernya punya penanda free)
            # Kalau provider gak ada embel-embel free (kayak OVH), kita ambil semua model chat-nya
            free_models = [m for m in chat_models if "free" in m.lower()]
            
            if free_models:
                models_to_test = free_models
                print(f"Ditemukan {len(free_models)} model berlabel 'free'.")
            else:
                # Kalau gak ada embel-embel free, kita ambil 30 model chat pertama buat dites
                models_to_test = chat_models[:30] 
                print(f"Gak ada label 'free', ngambil {len(models_to_test)} model chat pertama.")
                
            if not models_to_test:
                print("❌ Gak ada model chat yang bisa dites.")
                continue
                
            print(f"Mulai ngetes {len(models_to_test)} model...")
            
            for i, model in enumerate(models_to_test, 1):
                res = await test_model(session, provider, base_url, model)
                print(f"[{i}/{len(models_to_test)}] {res}")
                with open(OUTPUT_FILE, "a") as f: f.write(res + "\n")
                await asyncio.sleep(2) # Jeda 2 detik

    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
