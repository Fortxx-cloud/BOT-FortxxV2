import os
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()
OUTPUT_FILE = "hasil_3_api_baru.txt"

# Konfigurasi Provider (Mencoba endpoint standar OpenAI /v1)
PROVIDERS = {
    "Onomeo": {
        "url": "https://onomeo.com/v1",
        "key": os.getenv("ONOMEO_API_KEY")
    },
    "Itera": {
        "url": "https://api.iteracompute.com/v1", # Asumsi endpoint standar
        "key": os.getenv("ITERA_API_KEY")
    },
    "FreeAI": {
        "url": "https://api.freetheai.com/v1", # Asumsi endpoint standar
        "key": os.getenv("FREETHEAI_API_KEY")
    }
}

async def get_models(session, name, url, key):
    headers = {"Authorization": f"Bearer {key}"}
    try:
        async with session.get(f"{url}/models", headers=headers, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                if isinstance(data, dict) and "data" in data:
                    return [m["id"] for m in data["data"]]
                elif isinstance(data, list):
                    return [m.get("id") for m in data if isinstance(m, dict)]
            else:
                print(f"❌ {name}: Gagal narik model (HTTP {r.status}). Cek URL/Key.")
    except Exception as e:
        print(f"❌ {name}: Error koneksi ({type(e).__name__}).")
    return []

async def test_model(session, name, url, key, model):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    try:
        async with session.post(f"{url}/chat/completions", headers=headers, json=payload, timeout=25) as r:
            if r.status == 200:
                data = await r.json()
                reply = data['choices'][0]['message']['content']
                res = f"✅ [TERBANG] {name} -> {model} -> \"{reply.strip()[:30]}...\""
            else:
                res = f"❌ [GAGAL] {name} -> {model} (HTTP {r.status})"
    except Exception:
        res = f"❌ [ERROR] {name} -> {model}"
        
    print(res)
    with open(OUTPUT_FILE, "a") as f:
        f.write(res + "\n")
    await asyncio.sleep(1.5) # Jeda biar aman

async def main():
    print("⏳ Memulai tes 3 API Baru...\n")
    with open(OUTPUT_FILE, "w") as f: f.write("=== HASIL TES 3 API BARU ===\n\n")
    
    async with aiohttp.ClientSession() as session:
        for name, cfg in PROVIDERS.items():
            if not cfg["key"]:
                print(f"⚠️ {name}: API Key gak ketemu di .env")
                continue
                
            print(f"\n📦 Menarik model dari {name}...")
            models = await get_models(session, name, cfg["url"], cfg["key"])
            
            if not models:
                continue
                
            print(f"Total model: {len(models)}. Mulai ngetes...")
            for m in models:
                await test_model(session, name, cfg["url"], cfg["key"], m)
                
    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
