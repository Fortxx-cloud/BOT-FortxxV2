import os, asyncio, aiohttp
from dotenv import load_dotenv
load_dotenv(".env")

async def test():
    key = os.getenv("ZAI_API_KEY")
    url = "https://api.z.ai/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "glm-4.5-flash",
        "messages": [{"role": "user", "content": "Jawab: apa ibukota Indonesia?"}],
        "max_tokens": 200,
        "temperature": 0.3,
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=headers, json=payload, timeout=30) as r:
            print(f"Status: {r.status}")
            data = await r.json()
            try:
                msg = data["choices"][0]["message"]
                print(f"Content: {msg.get('content', '')!r}")
                print(f"Reasoning: {msg.get('reasoning_content', '')[:100]!r}")
                print(f"Finish: {data['choices'][0].get('finish_reason')}")
                print(f"Usage: {data.get('usage', {})}")
            except Exception as e:
                print(f"Parse error: {e}")
                print(data)

asyncio.run(test())
