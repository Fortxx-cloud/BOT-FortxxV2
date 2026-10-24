import aiohttp
import asyncio

GATEWAYS = {
    "BlockRun": "https://blockrun.ai/api/v1",
    "ApiAirforce": "https://api.airforce/v1"
}

OUTPUT_FILE = "hasil_2_gateway.txt"
SEMAPHORE = asyncio.Semaphore(10)

BAD_WORDS = ["suno", "image", "nano-banana", "flux", "dall-e", "stable-diffusion", "tts", "whisper", "embed", "midjourney", "audio", "guard"]

# Prioritas model papan atas
TOP_KEYWORDS = ["gpt", "claude", "qwen", "llama", "deepseek", "kimi", "mistral", "glm", "sonnet", "opus", "nemotron"]

async def get_models(session, base_url):
    try:
        async with session.get(f"{base_url}/models", timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                if isinstance(data, dict) and "data" in data:
                    return [m["id"] for m in data["data"]]
                elif isinstance(data, list):
                    return [m.get("id") or m.get("name") for m in data if isinstance(m, dict)]
    except Exception as e:
        print(f"❌ Gagal narik model: {e}")
    return []

async def test_model(session, provider, base_url, model):
    async with SEMAPHORE:
        payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 15}
        try:
            async with session.post(f"{base_url}/chat/completions", json=payload, timeout=25) as r:
                if r.status == 200:
                    data = await r.json()
                    reply = data['choices'][0]['message']['content']
                    res = f"✅ [TERBANG] {provider} -> {model} -> \"{reply.strip()[:40]}...\""
                elif r.status == 429:
                    res = f"⚠️ [LIMIT] {provider} -> {model}"
                elif r.status == 402:
                    res = f"💸 [BAYAR] {provider} -> {model}"
                else:
                    res = f"❌ [GAGAL] {provider} -> {model} (HTTP {r.status})"
        except Exception:
            res = f"❌ [ERROR] {provider} -> {model}"
            
        print(res)
        with open(OUTPUT_FILE, "a") as f:
            f.write(res + "\n")
        await asyncio.sleep(0.3)

async def main():
    print("🚀 NEMBAK 2 GATEWAY YANG BENERAN HIDUP...\n")
    with open(OUTPUT_FILE, "w") as f: f.write("=== HASIL 2 GATEWAY ===\n\n")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for provider, base_url in GATEWAYS.items():
            print(f"\n📦 Menarik model dari {provider}...")
            models = await get_models(session, base_url)
            
            # Filter model sampah
            models = [m for m in models if not any(bw in m.lower() for bwc in [BAD_WORDS] for bw in bwc)]
            
            # Ambil model top aja biar gak kelamaan
            top_models = [m for m in models if any(k in m.lower() for k in TOP_KEYWORDS)]
            
            if not top_models:
                top_models = models[:50]
            else:
                top_models = top_models[:60] # Maks 60 per provider
                
            print(f"   Total: {len(models)} model chat | Ngambil {len(top_models)} model top.")
            
            for m in top_models:
                tasks.append(test_model(session, provider, base_url, m))
                
        print(f"\n🔥 Nembak {len(tasks)} model secara bersamaan...\n")
        await asyncio.gather(*tasks)
        
    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
