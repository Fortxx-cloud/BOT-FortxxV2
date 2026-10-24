import os, asyncio, aiohttp
from dotenv import load_dotenv
load_dotenv(".env")

KEY = os.getenv("ZAI_API_KEY")
URL = "https://api.z.ai/api/paas/v4/chat/completions"

MODELS = [
    "glm-4-flash",
    "glm-4.5-flash",
    "glm-4.6",
    "glm-4.6-flash",
    "glm-4-plus",
    "glm-4-air",
    "glm-4-long",
    "glm-z1-air",
    "glm-z1-flash",
]

async def test(session, model):
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}
    try:
        async with session.post(URL, headers=headers, json=payload, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                try: reply = data["choices"][0]["message"]["content"][:30]
                except: reply = "(parse fail)"
                print(f"✅ {model} — {reply!r}")
            else:
                body = (await r.text())[:100]
                print(f"❌ {model}: HTTP{r.status} — {body}")
    except Exception as e:
        print(f"❌ {model}: {type(e).__name__}")

async def main():
    async with aiohttp.ClientSession() as s:
        for m in MODELS:
            await test(s, m)

if __name__ == "__main__":
    asyncio.run(main())
