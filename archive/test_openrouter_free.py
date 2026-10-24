import os
import asyncio
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
URL_MODELS = "https://openrouter.ai/api/v1/models"
URL_CHAT = "https://openrouter.ai/api/v1/chat/completions"
OUTPUT_FILE = "hasil_openrouter_free.txt"

async def get_free_models(session):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with session.get(URL_MODELS, headers=headers, timeout=20) as r:
        if r.status != 200:
            print(f"❌ Gagal narik model: HTTP {r.status}")
            return []
        data = await r.json()
        all_models = data.get("data", [])
        
        free_models = []
        for m in all_models:
            model_id = m.get("id", "")
            pricing = m.get("pricing", {})
            prompt_price = pricing.get("prompt")
            completion_price = pricing.get("completion")
            
            # Filter: ID mengandung ':free' ATAU harga prompt & completion 0
            is_free_id = ":free" in model_id
            is_free_price = (prompt_price == "0" and completion_price == "0")
            
            if is_free_id or is_free_price:
                free_models.append(model_id)
                
        return free_models

async def test_model(session, model_id, index, total):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://bot-fortxx.wispbyte.app",
        "X-Title": "Fortxx Free Tester"
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Halo"}],
        "max_tokens": 10
    }
    try:
        async with session.post(URL_CHAT, headers=headers, json=payload, timeout=25) as r:
            if r.status == 200:
                try:
                    data = await r.json()
                    reply = data['choices'][0]['message']['content']
                    return f"✅ [TERBANG] {model_id} -> \"{reply.strip()[:40]}...\""
                except:
                    return f"✅ [TERBANG] {model_id} (Respons non-JSON)"
            elif r.status == 429:
                return f"⚠️ [LIMIT] {model_id} (HTTP 429)"
            elif r.status == 402:
                return f"💸 [PAYMENT] {model_id} (HTTP 402)"
            else:
                return f"❌ [GAGAL] {model_id} (HTTP {r.status})"
    except Exception as e:
        return f"❌ [ERROR] {model_id} ({type(e).__name__})"

async def main():
    if not API_KEY:
        print("❌ OPENROUTER_API_KEY gak ada di .env")
        return
        
    print("⏳ Menarik daftar model gratis dari OpenRouter...")
    async with aiohttp.ClientSession() as session:
        free_models = await get_free_models(session)
        
        if not free_models:
            print("❌ Gak ada model gratis yang terdeteksi.")
            return
            
        total = len(free_models)
        print(f"\n🎉 Ketemu {total} model GRATIS!")
        print(f"⏱️ Estimasi waktu: ~{round(total * 3 / 60)} menit (jeda 3 detik/model)\n")
        
        with open(OUTPUT_FILE, "w") as f:
            f.write(f"=== TES OPENROUTER FREE ({total} Model) ===\n\n")
            
        for i, model in enumerate(free_models, 1):
            res = await test_model(session, model, i, total)
            print(f"[{i:03d}/{total}] {res}")
            
            with open(OUTPUT_FILE, "a") as f:
                f.write(res + "\n")
                
            await asyncio.sleep(3) # Jeda 3 detik anti rate limit
            
    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
