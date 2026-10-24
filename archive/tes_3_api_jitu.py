import os
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()
OUTPUT_FILE = "hasil_3_api_jitu.txt"

PROVIDERS = {
    "Onomeo": {"url": "https://onomeo.com/v1", "key": os.getenv("ONOMEO_API_KEY")},
    "Itera": {"url": "https://api.iteracompute.com/v1", "key": os.getenv("ITERA_API_KEY")},
    "FreeTheAI": {"url": "https://api.freetheai.org/v1", "key": os.getenv("FREETHEAI_API_KEY")}
}

async def get_models(session, name, cfg):
    headers = {"Authorization": f"Bearer {cfg['key']}"}
    try:
        async with session.get(f"{cfg['url']}/models", headers=headers, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                return [m["id"] for m in data.get("data", [])]
    except Exception as e:
        print(f"❌ {name}: Error koneksi ({e})")
    return []

async def test_model(session, provider, cfg, model):
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    
    try:
        async with session.post(f"{cfg['url']}/chat/completions", headers=headers, json=payload, timeout=20) as r:
            if r.status == 200:
                data = await r.json()
                reply = data['choices'][0]['message']['content']
                res = f"✅ [TERBANG] {provider} -> {model} -> \"{reply.strip()[:30]}...\""
            elif r.status == 402:
                res = f"💸 [PAYMENT] {provider} -> {model} (Butuh Duit)"
            elif r.status == 401 or r.status == 403:
                res = f"🔒 [AKSES] {provider} -> {model} (Gak Punya Akses)"
            else:
                res = f"❌ [GAGAL] {provider} -> {model} (HTTP {r.status})"
    except Exception:
        res = f"❌ [ERROR] {provider} -> {model}"
        
    print(res)
    with open(OUTPUT_FILE, "a") as f:
        f.write(res + "\n")
    await asyncio.sleep(2) # Jeda 2 detik

async def main():
    print("⏳ Memulai tes 3 API Jitu...\n")
    with open(OUTPUT_FILE, "w") as f: f.write("=== HASIL TES 3 API JITU ===\n\n")
    
    async with aiohttp.ClientSession() as session:
        for name, cfg in PROVIDERS.items():
            if not cfg["key"]:
                print(f"⚠️ {name}: API Key kosong di .env")
                continue
                
            print(f"\n📦 Menarik model dari {name}...")
            models = await get_models(session, name, cfg)
            
            if not models:
                print(f"❌ {name}: Gak dapet model.")
                continue
                
            print(f"Total: {len(models)} model. Mulai ngetes...\n")
            for m in models:
                await test_model(session, name, cfg, m)

    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
