import os, asyncio, aiohttp
from dotenv import load_dotenv

load_dotenv()
E = os.environ
OUTPUT = "hasil_mega_final.txt"

# Filter model sampah (embedding, audio, dll)
SKIP = ["embed", "whisper", "tts", "transcribe", "ocr", "audio", "guard", "moderation", "image"]

async def get_models(session, url, key, p_type):
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    try:
        async with session.get(url, headers=headers, timeout=15) as r:
            if r.status != 200: return []
            data = await r.json()
            if p_type == "gemini": return [m['name'].replace('models/', '') for m in data.get('models', [])]
            elif p_type == "cohere": return [m['name'] for m in data.get('models', [])]
            elif p_type == "cloudflare": return [m['name'] for m in data.get('result', []) if "Text Generation" in m.get('task', {}).get('name', '')]
            else: return [m['id'] for m in data.get('data', [])]
    except: return []

async def test_model(session, provider, model, url, key, p_type="openai"):
    headers = {"Content-Type": "application/json"}
    if p_type not in ["gemini", "cloudflare"]: headers["Authorization"] = f"Bearer {key}"
    elif p_type == "cloudflare": headers["Authorization"] = f"Bearer {key}"
    
    if p_type == "gemini":
        url = f"{url}/{model}:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": "Halo"}]}]}
    elif p_type == "cohere":
        payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}]}
    elif p_type == "cloudflare":
        payload = {"messages": [{"role": "user", "content": "Halo"}]}
    else:
        payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
        
    try:
        async with session.post(url, headers=headers, json=payload, timeout=20) as r:
            return f"✅ [TERBANG] {provider} -> {model}" if r.status == 200 else f"❌ [GAGAL] {provider} -> {model} (HTTP {r.status})"
    except Exception:
        return f"❌ [ERROR] {provider} -> {model}"

async def main():
    with open(OUTPUT, "w") as f: f.write("=== MEGA TESTER FINAL ===\n\n")
    
    # Konfigurasi Provider (ZAI di-skip)
    PROVIDERS = [
        {"name": "ChatAnywhere", "m_url": "https://api.chatanywhere.tech/v1/models", "c_url": "https://api.chatanywhere.tech/v1/chat/completions", "key": E.get("CHATANYWHERE_API_KEY"), "type": "openai"},
        {"name": "Mistral", "m_url": "https://api.mistral.ai/v1/models", "c_url": "https://api.mistral.ai/v1/chat/completions", "key": E.get("MISTRAL_API_KEY"), "type": "openai"},
        {"name": "Cohere", "m_url": "https://api.cohere.com/v1/models", "c_url": "https://api.cohere.com/v2/chat", "key": E.get("COHERE_API_KEY"), "type": "cohere"},
        {"name": "Groq", "m_url": "https://api.groq.com/openai/v1/models", "c_url": "https://api.groq.com/openai/v1/chat/completions", "key": E.get("GROQ_API_KEY"), "type": "openai"},
        {"name": "Cloudflare", "m_url": f"https://api.cloudflare.com/client/v4/accounts/{E.get('CF_ACCOUNT_ID')}/ai/models/search", "c_url": "https://api.cloudflare.com/client/v4/accounts/" + E.get('CF_ACCOUNT_ID') + "/ai/run/", "key": E.get("CF_API_TOKEN"), "type": "cloudflare"},
        {"name": "LLM7", "m_url": "https://api.llm7.io/v1/models", "c_url": "https://api.llm7.io/v1/chat/completions", "key": E.get("LLM7_TOKENS"), "type": "openai"},
        {"name": "Dahl", "m_url": "https://inference.dahl.global/v1/models", "c_url": "https://inference.dahl.global/v1/chat/completions", "key": E.get("DAHL_TOKEN_1"), "type": "openai"},
        {"name": "Pollinations", "m_url": "https://text.pollinations.ai/models", "c_url": "https://text.pollinations.ai/openai", "key": None, "type": "openai"},
        {"name": "Gemini", "m_url": f"https://generativelanguage.googleapis.com/v1beta/models?key={E.get('GEMINI_API_KEY')}", "c_url": "https://generativelanguage.googleapis.com/v1beta/models", "key": E.get("GEMINI_API_KEY"), "type": "gemini"}
    ]

    async with aiohttp.ClientSession() as session:
        for p in PROVIDERS:
            print(f"\n{'='*50}\n📦 MENARIK SEMUA MODEL: {p['name']}\n{'='*50}")
            models = await get_models(session, p['m_url'], p['key'], p['type'])
            
            # Filter model sampah
            models = [m for m in models if not any(s in m.lower() for s in SKIP)]
            
            if not models:
                print(f"❌ Gagal nemu model {p['name']} / Kosong.")
                continue
                
            print(f"Total model chat: {len(models)}. Mulai ngetes...\n")
            
            for i, m in enumerate(models, 1):
                # Handle Cloudflare URL
                c_url = p['c_url'] + m if p['type'] == "cloudflare" else p['c_url']
                
                res = await test_model(session, p['name'], m, c_url, p['key'], p['type'])
                print(f"[{i}/{len(models)}] {res}")
                
                with open(OUTPUT, "a") as f: f.write(res + "\n")
                await asyncio.sleep(3) # Jeda 3 detik anti rate-limit

    print(f"\n✅ SELESAI TOTAL! Cek file: {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
