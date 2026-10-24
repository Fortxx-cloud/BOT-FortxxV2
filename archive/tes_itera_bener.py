import os
import aiohttp
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ITERA_API_KEY", "").strip()

async def main():
    if not API_KEY:
        print("❌ API Key Itera gak ketemu di .env")
        return

    url = "https://api.iteracompute.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Payload persis kayak di dokumentasi mereka
    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [{"role": "user", "content": "Reply with exactly: Hello!"}],
        "max_tokens": 512,
        "chat_template_kwargs": {"enable_thinking": False}
    }

    print("⏳ Nembak Itera Qwen3.8-27B...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=180) as r:
                print(f"Status HTTP: {r.status}")
                if r.status == 200:
                    data = await r.json()
                    reply = data["choices"][0]["message"]["content"]
                    if reply and reply.strip():
                        print(f"✅ [SUKSES AKTIVASI] Jawaban: \"{reply.strip()}\"")
                    else:
                        print("⚠️ [GAGAL] Jawaban kosong. Aktivasi belum selesai / limit.")
                else:
                    error_text = await r.text()
                    print(f"❌ [GAGAL] Respons: {error_text[:200]}")

    except Exception as e:
        print(f"❌ Error Koneksi: {e}")

if __name__ == "__main__":
    asyncio.run(main())
