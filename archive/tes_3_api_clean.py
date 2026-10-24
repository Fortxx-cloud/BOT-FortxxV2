import os
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()
OUTPUT_FILE = "hasil_3_api_clean.txt"

# Ambil key dan bersihin spasi/enter yang nyangkut
PROVIDERS = {
    "Onomeo": {"url": "https://onomeo.com/v1", "key": os.getenv("ONOMEO_API_KEY", "").strip()},
    "Itera": {"url": "https://api.iteracompute.com/v1", "key": os.getenv("ITERA_API_KEY", "").strip()},
    "FreeTheAI": {"url": "https://api.freetheai.org/v1", "key": os.getenv("FREETHEAI_API_KEY", "").strip()}
}

async def get_models(session, name, cfg):
    headers = {"Authorization": f"Bearer {cfg['key']}"}
    try:
        async with session.get(f"{cfg['url']}/models", headers=headers, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                return data.get("data", [])
            else:
                print(f"❌ {name}: Gagal tarik model (HTTP {r.status}). Key: '{cfg['key'][:5]}...'")
    except Exception as e:
        print(f"❌ {name}: Error koneksi ({type(e).__name__})")
    return []

async def test_model(session, provider, cfg, model_id):
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    
    try:
        async with session.post(f"{cfg['url']}/chat/completions", headers=headers, json=payload, timeout=20) as r:
            if r.status == 200:
                data = await r.json()
                reply = data['choices'][0]['message']['content']
                res = f"✅ [TERBANG] {provider} -> {model_id} -> \"{reply.strip()[:30]}...\""
            elif r.status == 402:
                res = f"💸 [PAYMENT] {provider} -> {model_id}"
            elif r.status in [401, 403]:
                res = f"🔒 [AKSES] {provider} -> {model_id}"
            else:
                res = f"❌ [GAGAL] {provider} -> {model_id} (HTTP {r.status})"
    except Exception:
        res = f"❌ [ERROR] {provider} -> {model_id}"
        
    print(res)
    with open(OUTPUT_FILE, "a") as f:
        f.write(res + "\n")
    await asyncio.sleep(2)

async def main():
    print("⏳ Memulai tes 3 API (Versi Bersih)...\n")
    with open(OUTPUT_FILE, "w") as f: f.write("=== HASIL TES API BERSIH ===\n\n")
    
    async with aiohttp.ClientSession() as session:
        for name, cfg in PROVIDERS.items():
            if not cfg["key"]:
                print(f"⚠️ {name}: API Key kosong di .env")
                continue
                
            print(f"\n📦 Menarik model dari {name}...")
            all_models = await get_models(session, name, cfg)
            
            if not all_models:
                continue
                
            models_to_test = []
            
            # Khusus Itera, kita filter cuma yang is_free == true
            if name == "Itera":
                for m in all_models:
                    if m.get("is_free") is True:
                        models_to_test.append(m["id"])
                print(f"Total model: {len(all_models)} | Yang gratis (is_free): {len(models_to_test)}")
            else:
                models_to_test = [m["id"] for m in all_models]
                print(f"Total model: {len(models_to_test)}")
                
            if not models_to_test:
                print(f"❌ Gak ada model gratis yang bisa dites di {name}.")
                continue
                
            for m_id in models_to_test:
                await test_model(session, name, cfg, m_id)

    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
