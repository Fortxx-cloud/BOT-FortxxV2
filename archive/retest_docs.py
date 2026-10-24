import os, asyncio, aiohttp
from dotenv import load_dotenv

load_dotenv()
E = os.environ
OUTPUT = "hasil_retest_docs.txt"

async def test_zai(session, model):
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {E.get('ZAI_API_KEY')}",
        "Content-Type": "application/json",
        "Accept-Language": "en-US,en"  # Sesuai dokumentasi resmi
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Halo"}],
        "stream": False,
        "temperature": 1
    }
    try:
        async with session.post(url, headers=headers, json=payload, timeout=20) as r:
            return f"✅ [TERBANG] ZAI -> {model}" if r.status == 200 else f"❌ [GAGAL] ZAI -> {model} (HTTP {r.status})"
    except Exception as e:
        return f"❌ [ERROR] ZAI -> {model}"

async def test_gemini(session, model):
    key = E.get("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": "Halo"}]}]}
    try:
        async with session.post(url, json=payload, timeout=20) as r:
            return f"✅ [TERBANG] Gemini -> {model}" if r.status == 200 else f"❌ [GAGAL] Gemini -> {model} (HTTP {r.status})"
    except Exception:
        return f"❌ [ERROR] Gemini -> {model}"

async def test_mistral(session, model):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {E.get('MISTRAL_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    try:
        async with session.post(url, headers=headers, json=payload, timeout=20) as r:
            return f"✅ [TERBANG] Mistral -> {model}" if r.status == 200 else f"❌ [GAGAL] Mistral -> {model} (HTTP {r.status})"
    except Exception:
        return f"❌ [ERROR] Mistral -> {model}"

async def test_chatanywhere(session, model):
    url = "https://api.chatanywhere.tech/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {E.get('CHATANYWHERE_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    try:
        async with session.post(url, headers=headers, json=payload, timeout=20) as r:
            return f"✅ [TERBANG] ChatAnywhere -> {model}" if r.status == 200 else f"❌ [GAGAL] ChatAnywhere -> {model} (HTTP {r.status})"
    except Exception:
        return f"❌ [ERROR] ChatAnywhere -> {model}"

async def main():
    with open(OUTPUT, "w") as f: f.write("=== RETEST SESUAI DOKUMENTASI RESMI ===\n\n")
    async with aiohttp.ClientSession() as session:
        
        # Daftar model yang mau dites (bisa lu tambahin sendiri)
        zai_models = ["glm-5.3", "glm-5.3-flash", "glm-4.7", "glm-5.2", "glm-4.6"]
        gemini_models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
        mistral_models = ["mistral-small-latest", "ministral-8b-latest", "codestral-latest"]
        ca_models = ["gpt-6.1-sol", "gpt-5.5", "gpt-4o", "deepseek-v4-pro"]

        print("\n📦 Ngetes ZAI (format resmi)...")
        for m in zai_models:
            res = await test_zai(session, m)
            print(res)
            with open(OUTPUT, "a") as f: f.write(res + "\n")
            await asyncio.sleep(10)

        print("\n📦 Ngetes Gemini (format resmi)...")
        for m in gemini_models:
            res = await test_gemini(session, m)
            print(res)
            with open(OUTPUT, "a") as f: f.write(res + "\n")
            await asyncio.sleep(10)

        print("\n📦 Ngetes Mistral (format resmi)...")
        for m in mistral_models:
            res = await test_mistral(session, m)
            print(res)
            with open(OUTPUT, "a") as f: f.write(res + "\n")
            await asyncio.sleep(10)

        print("\n📦 Ngetes ChatAnywhere (format resmi)...")
        for m in ca_models:
            res = await test_chatanywhere(session, m)
            print(res)
            with open(OUTPUT, "a") as f: f.write(res + "\n")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
