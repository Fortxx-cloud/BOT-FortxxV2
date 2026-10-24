import os, asyncio, aiohttp
from dotenv import load_dotenv
load_dotenv(".env")

TESTS = [
    ("NVIDIA",    "https://integrate.api.nvidia.com/v1/chat/completions",   os.getenv("NVIDIA_API_KEY"),     "meta/llama-3.3-70b-instruct"),
    ("SAMBANOVA", "https://api.sambanova.ai/v1/chat/completions",           os.getenv("SAMBANOVA_API_KEY"),  "Meta-Llama-3.3-70B-Instruct"),
    ("ZAI",       "https://api.z.ai/api/paas/v4/chat/completions",          os.getenv("ZAI_API_KEY"),        "glm-4-flash"),
    ("ITERA",     "https://api.itera.ai/v1/chat/completions",               os.getenv("ITERA_API_KEY"),      "gpt-3.5-turbo"),
    ("FREETHEAI", "https://api.freetheai.xyz/v1/chat/completions",          os.getenv("FREETHEAI_API_KEY"),  "gpt-3.5-turbo"),
    ("OMNIROUTE", (os.getenv("OMNIROUTE_URL") or "") + "/v1/chat/completions", os.getenv("OMNIROUTE_TOKEN"), "gpt-3.5-turbo"),
]

async def test(session, name, url, key, model):
    if not key:
        print(f"⚠️  {name}: key kosong")
        return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    payload = {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}
    try:
        async with session.post(url, headers=headers, json=payload, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                try:
                    txt = data["choices"][0]["message"]["content"][:30]
                except Exception:
                    txt = "(parse gagal)"
                print(f"✅ {name}: HIDUP — reply: {txt!r}")
            else:
                body = (await r.text())[:120].replace("\n", " ")
                print(f"❌ {name}: HTTP{r.status} — {body}")
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__} — {str(e)[:60]}")

async def main():
    print("🔍 Test 6 provider...\n")
    async with aiohttp.ClientSession() as s:
        for t in TESTS:
            await test(s, *t)
    print("\n✅ Selesai. Yang HIDUP siap di-wire ke PROVIDERS.")

if __name__ == "__main__":
    asyncio.run(main())
