import os, asyncio, aiohttp
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("GEMINI_API_KEY")

# Daftar model Gemini (dari tes sebelumnya yang ✅)
MODELS = [
    "gemini-3.6-flash", 
    "gemini-3.5-flash", 
    "gemini-3-flash-preview", 
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemma-4-31b-it"
]

async def test(session, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={KEY}"
    payload = {"contents": [{"parts": [{"text": "Halo"}]}]}
    try:
        async with session.post(url, json=payload, timeout=20) as r:
            if r.status == 200:
                data = await r.json()
                reply = data['candidates'][0]['content']['parts'][0]['text']
                return f"✅ [TERBANG] Gemini -> {model} -> \"{reply.strip()[:30]}...\""
            else:
                return f"❌ [GAGAL] Gemini -> {model} (HTTP {r.status})"
    except Exception as e:
        return f"❌ [ERROR] Gemini -> {model}"

async def main():
    print("⏳ Ngetes ulang model Gemini (Jeda 15 detik)...\n")
    async with aiohttp.ClientSession() as session:
        for i, m in enumerate(MODELS, 1):
            res = await test(session, m)
            print(f"[{i}/{len(MODELS)}] {res}")
            await asyncio.sleep(15) # Jeda 15 detik biar gak kena rate limit Google

if __name__ == "__main__":
    asyncio.run(main())
