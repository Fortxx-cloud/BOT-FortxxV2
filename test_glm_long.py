import os, asyncio, aiohttp, time
from dotenv import load_dotenv
load_dotenv(".env")

async def test():
    key = os.getenv("ZAI_API_KEY")
    url = "https://api.z.ai/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "glm-4.5-flash",
        "messages": [{"role": "user", "content": "Jawab singkat: apa ibukota Indonesia?"}],
        "max_tokens": 2000,  # naikin drastis
    }
    t = time.time()
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=headers, json=payload, timeout=60) as r:
            data = await r.json()
            elapsed = time.time() - t
            msg = data["choices"][0]["message"]
            print(f"⏱️  Total: {elapsed:.2f}s")
            print(f"Content: {msg.get('content', '')!r}")
            print(f"Reasoning: {len(msg.get('reasoning_content', ''))} chars")
            print(f"Finish: {data['choices'][0].get('finish_reason')}")
            print(f"Tokens: {data['usage']}")

asyncio.run(test())
