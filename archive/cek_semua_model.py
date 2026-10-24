import os, json, aiohttp, asyncio
from dotenv import load_dotenv

load_dotenv()
ENV = os.environ

PROVIDERS = {
    "OmniRoute": {
        "url": f"{ENV.get('OMNIROUTE_URL', 'https://api.omniroute.ai').rstrip('/')}/v1/models",
        "headers": {"Authorization": f"Bearer {ENV.get('OMNIROUTE_TOKEN')}"},
        "type": "openai",
        "filter_free": True
    },
    "LLM7": {
        "url": "https://api.llm7.io/v1/models",
        "headers": {},
        "type": "openai"
    },
    "Dahl": {
        "url": "https://inference.dahl.global/v1/models",
        "headers": {"Authorization": f"Bearer {ENV.get('DAHL_TOKEN_1')}"},
        "type": "openai"
    },
    "ZAI": {
        "url": "https://open.bigmodel.cn/api/paas/v4/models",
        "headers": {"Authorization": f"Bearer {ENV.get('ZAI_API_KEY')}"},
        "type": "openai"
    },
    "Groq": {
        "url": "https://api.groq.com/openai/v1/models",
        "headers": {"Authorization": f"Bearer {ENV.get('GROQ_API_KEY')}"},
        "type": "openai"
    },
    "Gemini": {
        "url": f"https://generativelanguage.googleapis.com/v1beta/models?key={ENV.get('GEMINI_API_KEY')}",
        "headers": {},
        "type": "gemini"
    },
    "Mistral": {
        "url": "https://api.mistral.ai/v1/models",
        "headers": {"Authorization": f"Bearer {ENV.get('MISTRAL_API_KEY')}"},
        "type": "openai"
    },
    "Cohere": {
        "url": "https://api.cohere.com/v1/models",
        "headers": {"Authorization": f"Bearer {ENV.get('COHERE_API_KEY')}"},
        "type": "cohere"
    },
    "OpenRouter": {
        "url": "https://openrouter.ai/api/v1/models",
        "headers": {"Authorization": f"Bearer {ENV.get('OPENROUTER_API_KEY')}"},
        "type": "openai"
    },
    "ChatAnywhere": {
        "url": "https://api.chatanywhere.tech/v1/models",
        "headers": {"Authorization": f"Bearer {ENV.get('CHATANYWHERE_API_KEY')}"},
        "type": "openai"
    }
}

async def fetch_models(session, name, cfg):
    try:
        async with session.get(cfg["url"], headers=cfg["headers"], timeout=15) as r:
            if r.status != 200:
                return name, f"❌ HTTP {r.status}"
            data = await r.json()
            
            models = []
            if cfg["type"] == "openai":
                models = [m.get("id") for m in data.get("data", [])]
            elif cfg["type"] == "gemini":
                models = [m.get("name").replace("models/", "") for m in data.get("models", [])]
            elif cfg["type"] == "cohere":
                models = [m.get("name") for m in data.get("models", [])]
            
            if cfg.get("filter_free"):
                # Filter OmniRoute: tampilkan yang punya awalan free tier atau mengandung 'free'
                free_prefixes = ('kr/', 'if/', 'oc/', 'felo/', 'free/')
                models = [m for m in models if any(m.startswith(p) for p in free_prefixes) or 'free' in m.lower()]
            
            return name, models
    except Exception as e:
        return name, f"❌ ERROR: {e}"

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_models(session, name, cfg) for name, cfg in PROVIDERS.items()]
        results = await asyncio.gather(*tasks)
        
        for name, data in results:
            print(f"\n{'='*50}\n📦 {name}\n{'='*50}")
            if isinstance(data, str):
                print(data)
                continue
            if not data:
                print("(Tidak ada model yang cocok / terdeteksi)")
                continue
            print(f"Total: {len(data)} model")
            for m in data[:30]: # Batasi 30 biar gak kepanjangan
                print(f"  - {m}")
            if len(data) > 30:
                print(f"  ... dan {len(data)-30} model lainnya")

if __name__ == "__main__":
    asyncio.run(main())
