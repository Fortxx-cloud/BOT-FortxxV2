import os, asyncio, aiohttp
from dotenv import load_dotenv
load_dotenv(".env")

KEY = os.getenv("NVIDIA_API_KEY")
URL = "https://integrate.api.nvidia.com/v1/chat/completions"

MODELS = [
    "meta/llama-3.3-70b-instruct",
    "meta/llama-3.1-405b-instruct",
    "meta/llama-3.1-70b-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "nvidia/llama-3.3-nemotron-super-49b-v1",
    "deepseek-ai/deepseek-r1",
    "qwen/qwen2.5-72b-instruct",
    "mistralai/mistral-large-2-instruct",
    "google/gemma-2-27b-it",
    "microsoft/phi-3-medium-128k-instruct",
]

async def test(session, model):
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}
    try:
        async with session.post(URL, headers=headers, json=payload, timeout=15) as r:
            if r.status == 200:
                print(f"✅ {model}")
            elif r.status == 410:
                print(f"❌ {model}: 410 deprecated")
            else:
                body = (await r.text())[:80]
                print(f"❌ {model}: HTTP{r.status} — {body}")
    except Exception as e:
        print(f"❌ {model}: {type(e).__name__}")

async def main():
    async with aiohttp.ClientSession() as s:
        for m in MODELS:
            await test(s, m)

if __name__ == "__main__":
    asyncio.run(main())
