import os, asyncio, aiohttp, json
from dotenv import load_dotenv

load_dotenv()
E = os.environ
OUTPUT = "hasil_fixed.txt"

# Kata kunci model yang BUKAN buat chat (skip aja)
SKIP_KEYWORDS = ["embed", "whisper", "tts", "transcribe", "ocr", "audio", "image", "guard"]

async def test_model(session, provider, model, url, key, headers_extra=None, payload_type="openai"):
    headers = {"Content-Type": "application/json"}
    if key: headers["Authorization"] = f"Bearer {key}"
    if headers_extra: headers.update(headers_extra)
    
    payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    
    if payload_type == "gemini":
        url = f"{url}?key={key}" # Format URL Gemini
        payload = {"contents": [{"parts": [{"text": "Halo"}]}]}
    elif payload_type == "cohere":
        # Cohere v2 pakai format OpenAI (messages), tapi URL beda
        url = "https://api.cohere.com/v2/chat"
    
    try:
        async with session.post(url, headers=headers, json=payload, timeout=20) as r:
            if r.status == 200:
                return f"✅ [TERBANG] {provider} -> {model}"
            else:
                return f"❌ [GAGAL] {provider} -> {model} (HTTP {r.status})"
    except Exception as e:
        return f"❌ [ERROR] {provider} -> {model}"

async def main():
    with open(OUTPUT, "w") as f: f.write("=== HASIL RETEST FIXED ===\n\n")
    
    async with aiohttp.ClientSession() as session:
        
        # === 1. COHERE (FIX: URL v2) ===
        print("\n📦 Ngetes Cohere (v2)...")
        cohere_models = ["command-a-plus-05-2026", "command-a-03-2025", "command-r-plus-08-2024"]
        for m in cohere_models:
            res = await test_model(session, "Cohere", m, "https://api.cohere.com/v2/chat", E.get("COHERE_API_KEY"), payload_type="cohere")
            print(res)
            with open(OUTPUT, "a") as f: f.write(res + "\n")
            await asyncio.sleep(10) # Jeda

        # === 2. ZAI (FIX: Jeda Lama) ===
        print("\n📦 Ngetes ZAI...")
        zai_models = ["glm-5.3-flash", "glm-4.7", "glm-5.3"]
        for m in zai_models:
            res = await test_model(session, "ZAI", m, "https://open.bigmodel.cn/api/paas/v4/chat/completions", E.get("ZAI_API_KEY"))
            print(res)
            with open(OUTPUT, "a") as f: f.write(res + "\n")
            await asyncio.sleep(15) # Jeda 15 detik

        # === 3. GEMINI (FIX: Jeda Lama) ===
        print("\n📦 Ngetes Gemini...")
        gemini_models = ["gemini-3.1-pro-preview", "gemini-pro-latest", "gemini-2.5-flash"]
        for m in gemini_models:
            res = await test_model(session, "Gemini", m, f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent", E.get("GEMINI_API_KEY"), payload_type="gemini")
            print(res)
            with open(OUTPUT, "a") as f: f.write(res + "\n")
            await asyncio.sleep(15) # Jeda 15 detik

        # === 4. MISTRAL (FIX: Jeda Lama) ===
        print("\n📦 Ngetes Mistral...")
        mistral_models = ["mistral-medium-latest", "mistral-small-latest"]
        for m in mistral_models:
            res = await test_model(session, "Mistral", m, "https://api.mistral.ai/v1/chat/completions", E.get("MISTRAL_API_KEY"))
            print(res)
            with open(OUTPUT, "a") as f: f.write(res + "\n")
            await asyncio.sleep(15) # Jeda 15 detik

        # === 5. CHATANYWHERE (FIX: Jeda Lama) ===
        print("\n📦 Ngetes ChatAnywhere...")
        ca_models = ["gpt-5.4", "gpt-5.5"]
        for m in ca_models:
            res = await test_model(session, "ChatAnywhere", m, "https://api.chatanywhere.tech/v1/chat/completions", E.get("CHATANYWHERE_API_KEY"))
            print(res)
            with open(OUTPUT, "a") as f: f.write(res + "\n")
            await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
