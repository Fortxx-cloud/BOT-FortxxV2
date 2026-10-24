import os, aiohttp, asyncio
from dotenv import load_dotenv
load_dotenv()

# Kita fokus ke 1 model gratis dari Itera dan 1 model market dari FreeAI
TESTS = [
    {
        "name": "Itera (Qwen 3.8)",
        "url": "https://api.iteracompute.com/v1/chat/completions",
        "key": os.getenv("ITERA_API_KEY", "").strip(),
        "model": "qwen/qwen3.8-27b"
    },
    {
        "name": "FreeAI (DeepSeek Market)",
        "url": "https://api.freetheai.org/v1/chat/completions",
        "key": os.getenv("FREETHEAI_API_KEY", "").strip(),
        "model": "fta/cat/deepseek-ai/deepseek-v4-flash-0731"
    }
]

async def main():
    async with aiohttp.ClientSession() as session:
        for t in TESTS:
            print(f"\n⏳ Ngetes {t['name']}...")
            headers = {"Authorization": f"Bearer {t['key']}", "Content-Type": "application/json"}
            payload = {"model": t['model'], "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
            
            try:
                async with session.post(t['url'], headers=headers, json=payload, timeout=15) as r:
                    print(f"Status HTTP: {r.status}")
                    text = await r.text()
                    print(f"Respons Server: {text[:300]}") # Tampilin 300 karakter pertama
            except Exception as e:
                print(f"❌ Error Koneksi: {e}")

if __name__ == "__main__":
    asyncio.run(main())
