import os, asyncio, aiohttp, json
from dotenv import load_dotenv

load_dotenv()
E = os.environ
OUTPUT = "hasil_retest_niat.txt"

# Daftar model yang mau diselamatkan
RETEST_DATA = {
    "Cohere": {
        "models": ["command-a-plus-05-2026", "command-a-03-2025", "command-r-plus-08-2024", "command-r-08-2024"],
        "url": "https://api.cohere.com/v1/chat/completions",
        "key": E.get("COHERE_API_KEY"),
        "type": "cohere" # Format khusus Cohere
    },
    "ZAI": {
        "models": ["glm-5.3-flash", "glm-4.7", "glm-5.2", "glm-5.3"],
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "key": E.get("ZAI_API_KEY"),
        "type": "openai"
    },
    "Gemini": {
        "models": ["gemini-3.1-pro-preview", "gemini-pro-latest", "gemini-2.5-flash-image", "gemini-3-pro-image"],
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        "key": E.get("GEMINI_API_KEY"),
        "type": "gemini"
    },
    "Mistral": {
        "models": ["mistral-medium-latest", "mistral-small-latest", "magistral-medium-latest"],
        "url": "https://api.mistral.ai/v1/chat/completions",
        "key": E.get("MISTRAL_API_KEY"),
        "type": "openai"
    },
    "ChatAnywhere": {
        "models": ["gpt-5.4", "gpt-5.5"],
        "url": "https://api.chatanywhere.tech/v1/chat/completions",
        "key": E.get("CHATANYWHERE_API_KEY"),
        "type": "openai"
    }
}

async def test_model(session, provider, cfg, model):
    headers = {"Content-Type": "application/json"}
    if cfg['type'] != 'gemini': headers["Authorization"] = f"Bearer {cfg['key']}"
    
    url = cfg['url']
    if cfg['type'] == 'gemini':
        url = url.format(model=model, key=cfg['key'])
        payload = {"contents": [{"parts": [{"text": "Halo"}]}]}
    elif cfg['type'] == 'cohere':
        payload = {"message": "Halo", "model": model} # Cohere pakai 'message' bukan 'messages'
    else:
        payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}

    try:
        async with session.post(url, headers=headers, json=payload, timeout=25) as r:
            if r.status == 200:
                return f"✅ [HIDUP LAGI] {provider} -> {model}"
            else:
                return f"❌ [TETAP GAGAL] {provider} -> {model} (HTTP {r.status})"
    except Exception:
        return f"❌ [ERROR] {provider} -> {model}"

async def main():
    with open(OUTPUT, "w") as f: f.write("=== HASIL RETEST NIAT ===\n\n")
    async with aiohttp.ClientSession() as session:
        for provider, cfg in RETEST_DATA.items():
            if not cfg['key']: continue
            print(f"\n📦 Ngetes ulang {provider}...")
            for model in cfg['models']:
                print(f"⏳ Mencoba {model}...")
                res = await test_model(session, provider, cfg, model)
                print(res)
                with open(OUTPUT, "a") as f: f.write(res + "\n")
                await asyncio.sleep(10) # JEDA 10 DETIK BIAR GAK KENA RATE LIMIT

if __name__ == "__main__":
    asyncio.run(main())
