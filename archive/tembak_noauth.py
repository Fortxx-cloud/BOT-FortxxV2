import aiohttp
import asyncio
import re

# Endpoint No-Auth
PROVIDERS = {
    "UncloseAI": "https://hermes.ai.unturf.com/v1",
    "KiloCode": "https://api.kilo.ai/api/gateway",
    "OVH_AI": "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
    "ApiAirforce": "https://api.airforce/v1"
}

OUTPUT_FILE = "hasil_tembak_noauth.txt"

# Filter nama model aneh (bukan buat chat)
BAD_WORDS = ["image", "suno", "audio", "tts", "whisper", "embed", "vision-ocr", "moderation", "guard"]

async def get_models(session, base_url):
    try:
        async with session.get(f"{base_url}/models", timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                if isinstance(data, dict) and "data" in data:
                    return [m["id"] for m in data["data"]]
                elif isinstance(data, list):
                    return [m.get("id") for m in data if isinstance(m, dict)]
    except:
        return []
    return []

async def test_model(session, provider, base_url, model):
    url = f"{base_url}/chat/completions"
    payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    try:
        async with session.post(url, json=payload, timeout=15) as r:
            if r.status == 200:
                return f"✅ [TERBANG] {provider} -> {model}"
            else:
                return f"❌ [GAGAL] {provider} -> {model} (HTTP {r.status})"
    except Exception:
        return f"❌ [ERROR] {provider} -> {model}"

async def main():
    print("⏳ Memulai Pengeboman Model No-Auth...\n")
    
    with open(OUTPUT_FILE, "w") as f: f.write("=== HASIL TEMBAK NO-AUTH ===\n\n")
    
    async with aiohttp.ClientSession() as session:
        for provider, base_url in PROVIDERS.items():
            print(f"\n📦 Menarik model dari {provider}...")
            all_models = await get_models(session, base_url)
            
            # Filter model yang bukan buat chat
            chat_models = [m for m in all_models if not any(bw in m.lower() for bw in BAD_WORDS)]
            
            print(f"Total model: {len(all_models)} | Setelah difilter (Chat): {len(chat_models)}")
            
            # Batasi 50 model pertama per provider biar gak kelamaan (lu bisa ubah jadi 100 kalau mau)
            limit = 50
            if len(chat_models) > limit:
                print(f"Mengambil {limit} model pertama untuk dites...")
                chat_models = chat_models[:limit]
                
            for i, model in enumerate(chat_models, 1):
                res = await test_model(session, provider, base_url, model)
                print(f"[{i}/{len(chat_models)}] {res}")
                with open(OUTPUT_FILE, "a") as f: f.write(res + "\n")
                await asyncio.sleep(2) # Jeda 2 detik biar gak dianggap spam

    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
