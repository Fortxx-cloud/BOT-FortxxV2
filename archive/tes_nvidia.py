import os
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("NVIDIA_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/v1"

OUTPUT_FILE = "hasil_nvidia.txt"

# Filter model yang bukan buat chat
BAD_WORDS = ["embed", "vision-ocr", "audio", "tts", "whisper", "guard", "image", "safety"]

async def get_models(session):
    print("⏳ Menarik daftar model dari NVIDIA NIM...")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        async with session.get(f"{BASE_URL}/models", headers=headers, timeout=15) as r:
            if r.status != 200:
                print(f"❌ Gagal narik model: HTTP {r.status}")
                return []
            data = await r.json()
            return [m["id"] for m in data.get("data", [])]
    except Exception as e:
        print(f"❌ Error koneksi: {e}")
        return []

async def test_model(session, model, index, total):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Halo"}],
        "max_tokens": 10
    }
    
    try:
        async with session.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=30) as r:
            if r.status == 200:
                data = await r.json()
                reply = data['choices'][0]['message']['content']
                res = f"✅ [TERBANG] {model} -> \"{reply.strip()[:30]}...\""
            else:
                res = f"❌ [GAGAL] {model} (HTTP {r.status})"
    except Exception as e:
        res = f"❌ [ERROR] {model} ({type(e).__name__})"
        
    print(f"[{index}/{total}] {res}")
    with open(OUTPUT_FILE, "a") as f:
        f.write(res + "\n")
        
    await asyncio.sleep(2) # Jeda 2 detik (aman buat 40 RPM)

async def main():
    if not API_KEY:
        print("❌ NVIDIA_API_KEY gak ketemu di .env")
        return
        
    with open(OUTPUT_FILE, "w") as f: 
        f.write("=== HASIL TES NVIDIA NIM ===\n\n")
        
    async with aiohttp.ClientSession() as session:
        all_models = await get_models(session)
        
        if not all_models:
            return
            
        # Filter model sampah
        chat_models = [m for m in all_models if not any(bw in m.lower() for bw in BAD_WORDS)]
        
        print(f"Total model ditemukan: {len(all_models)}")
        print(f"Model chat yang bakal dites: {len(chat_models)}\n")
        
        for i, model in enumerate(chat_models, 1):
            await test_model(session, model, i, len(chat_models))

    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
