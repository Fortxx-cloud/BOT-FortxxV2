import os, asyncio, aiohttp, json
from dotenv import load_dotenv

load_dotenv()
E = os.environ

OUTPUT_FILE = "hasil_tes_akhir.txt"
OMNI_URL = E.get("OMNIROUTE_URL", "").rstrip("/")

# 1. PROVIDER STANDAR (Format OpenAI-compatible)
OPENAI_COMPATIBLE = {
    "ChatAnywhere": {"url": "https://api.chatanywhere.tech/v1/models", "chat": "https://api.chatanywhere.tech/v1/chat/completions", "key": E.get("CHATANYWHERE_API_KEY")},
    "Groq": {"url": "https://api.groq.com/openai/v1/models", "chat": "https://api.groq.com/openai/v1/chat/completions", "key": E.get("GROQ_API_KEY")},
    "Mistral": {"url": "https://api.mistral.ai/v1/models", "chat": "https://api.mistral.ai/v1/chat/completions", "key": E.get("MISTRAL_API_KEY")},
    "ZAI": {"url": "https://open.bigmodel.cn/api/paas/v4/models", "chat": "https://open.bigmodel.cn/api/paas/v4/chat/completions", "key": E.get("ZAI_API_KEY")},
    "Dahl": {"url": "https://inference.dahl.global/v1/models", "chat": "https://inference.dahl.global/v1/chat/completions", "key": E.get("DAHL_TOKEN_1")},
    "LLM7": {"url": "https://api.llm7.io/v1/models", "chat": "https://api.llm7.io/v1/chat/completions", "key": E.get("LLM7_TOKENS")},
    "SambaNova": {"url": "https://api.sambanova.ai/v1/models", "chat": "https://api.sambanova.ai/v1/chat/completions", "key": E.get("SAMBANOVA_API_KEY")},
    "Pollinations": {"url": "https://text.pollinations.ai/models", "chat": "https://text.pollinations.ai/openai", "key": E.get("POLLINATIONS_API_KEY")}
}

# Masukin OmniRoute kalau URL-nya ada
if OMNI_URL:
    OPENAI_COMPATIBLE["OmniRoute"] = {
        "url": f"{OMNI_URL}/v1/models", 
        "chat": f"{OMNI_URL}/v1/chat/completions", 
        "key": E.get("OMNIROUTE_TOKEN")
    }

async def get_models_openai(session, name, cfg):
    try:
        headers = {"Authorization": f"Bearer {cfg['key']}"} if cfg['key'] else {}
        async with session.get(cfg['url'], headers=headers, timeout=15) as r:
            if r.status != 200: return []
            data = await r.json()
            if name == "Pollinations":
                return [m['name'] for m in data] if isinstance(data, list) else []
            return [m['id'] for m in data.get('data', [])]
    except Exception as e: 
        print(f"⚠️ Gagal narik model {name}: {e}")
        return []

async def test_openai_model(session, provider, cfg, model):
    headers = {"Content-Type": "application/json"}
    if cfg['key']: headers["Authorization"] = f"Bearer {cfg['key']}"
    payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    try:
        async with session.post(cfg['chat'], headers=headers, json=payload, timeout=15) as r:
            return f"✅ [TERBANG] {provider} -> {model}" if r.status == 200 else f"❌ [MATI] {provider} -> {model} (HTTP {r.status})"
    except Exception: return f"❌ [ERROR] {provider} -> {model}"

# 2. PROVIDER KHUSUS (Gemini & Cohere & Cloudflare)
async def test_gemini(session):
    key = E.get("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    try:
        async with session.get(url, timeout=15) as r:
            if r.status != 200: return
            data = await r.json()
            models = [m['name'].replace('models/', '') for m in data.get('models', [])]
            for m in models:
                chat_url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
                payload = {"contents": [{"parts": [{"text": "Halo"}]}]}
                async with session.post(chat_url, json=payload, timeout=15) as cr:
                    res = f"✅ [TERBANG] Gemini -> {m}" if cr.status == 200 else f"❌ [MATI] Gemini -> {m} (HTTP {cr.status})"
                    print(res)
                    with open(OUTPUT_FILE, "a") as f: f.write(res + "\n")
                    await asyncio.sleep(2)
    except: pass

async def test_cohere(session):
    key = E.get("COHERE_API_KEY")
    url = "https://api.cohere.com/v1/models"
    chat_url = "https://api.cohere.com/v1/chat/completions"
    try:
        async with session.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=15) as r:
            if r.status != 200: return
            data = await r.json()
            models = [m['name'] for m in data.get('models', [])]
            for m in models:
                payload = {"model": m, "message": "Halo"}
                async with session.post(chat_url, headers={"Authorization": f"Bearer {key}"}, json=payload, timeout=15) as cr:
                    res = f"✅ [TERBANG] Cohere -> {m}" if cr.status == 200 else f"❌ [MATI] Cohere -> {m} (HTTP {cr.status})"
                    print(res)
                    with open(OUTPUT_FILE, "a") as f: f.write(res + "\n")
                    await asyncio.sleep(2)
    except: pass

async def test_cloudflare(session):
    acc = E.get("CF_ACCOUNT_ID")
    token = E.get("CF_API_TOKEN")
    url = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/models/search"
    try:
        async with session.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15) as r:
            if r.status != 200: return
            data = await r.json()
            models = [m['name'] for m in data.get('result', []) if "Text Generation" in m.get('task', {}).get('name', '')]
            for m in models:
                chat_url = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{m}"
                payload = {"messages": [{"role": "user", "content": "Halo"}]}
                async with session.post(chat_url, headers={"Authorization": f"Bearer {token}"}, json=payload, timeout=15) as cr:
                    res = f"✅ [TERBANG] Cloudflare -> {m}" if cr.status == 200 else f"❌ [MATI] Cloudflare -> {m} (HTTP {cr.status})"
                    print(res)
                    with open(OUTPUT_FILE, "a") as f: f.write(res + "\n")
                    await asyncio.sleep(2)
    except: pass

async def main():
    with open(OUTPUT_FILE, "w") as f: f.write("=== HASIL TES SEMUA AI (KECUALI OPENROUTER) ===\n\n")
    async with aiohttp.ClientSession() as session:
        
        # --- Tes Provider OpenAI-compatible ---
        for name, cfg in OPENAI_COMPATIBLE.items():
            if not cfg['key'] and name != "Pollinations": continue
            print(f"\n📦 Menarik model {name}...")
            models = await get_models_openai(session, name, cfg)
            print(f"Total: {len(models)} model. Mulai tes...\n")
            for m in models:
                res = await test_openai_model(session, name, cfg, m)
                print(res)
                with open(OUTPUT_FILE, "a") as f: f.write(res + "\n")
                await asyncio.sleep(2)
                
        # --- Tes Gemini ---
        print(f"\n📦 Menarik model Gemini...")
        await test_gemini(session)
        
        # --- Tes Cohere ---
        print(f"\n📦 Menarik model Cohere...")
        await test_cohere(session)
        
        # --- Tes Cloudflare ---
        print(f"\n📦 Menarik model Cloudflare...")
        await test_cloudflare(session)
        
    print(f"\n✅ Selesai! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
