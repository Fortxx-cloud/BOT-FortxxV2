import os, aiohttp, asyncio, time
from dotenv import load_dotenv

load_dotenv()
E = os.environ
OUTPUT_FILE = "hasil_speed_test.txt"

# Mapping Provider
PROVIDERS = {
    "chatanywhere": {"url": "https://api.chatanywhere.tech/v1/chat/completions", "key": E.get("CHATANYWHERE_API_KEY"), "type": "openai"},
    "cloudflare": {"url": "https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/", "key": E.get("CF_API_TOKEN"), "acc": E.get("CF_ACCOUNT_ID"), "type": "cloudflare"},
    "gemini": {"url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}", "key": E.get("GEMINI_API_KEY"), "type": "gemini"},
    "mistral": {"url": "https://api.mistral.ai/v1/chat/completions", "key": E.get("MISTRAL_API_KEY"), "type": "openai"},
    "onomeo": {"url": "https://onomeo.com/v1/chat/completions", "key": E.get("ONOMEO_API_KEY"), "type": "openai"},
    "openrouter": {"url": "https://openrouter.ai/api/v1/chat/completions", "key": E.get("OPENROUTER_API_KEY"), "type": "openai"},
    "groq": {"url": "https://api.groq.com/openai/v1/chat/completions", "key": E.get("GROQ_API_KEY"), "type": "openai"},
    "cohere": {"url": "https://api.cohere.com/v2/chat", "key": E.get("COHERE_API_KEY"), "type": "cohere"},
    "ovh": {"url": "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions", "key": "no-auth", "type": "openai"},
    "llm7": {"url": "https://api.llm7.io/v1/chat/completions", "key": E.get("LLM7_TOKENS"), "type": "openai"},
    "pollinations": {"url": "https://text.pollinations.ai/openai", "key": None, "type": "openai"},
    "dahl": {"url": "https://inference.dahl.global/v1/chat/completions", "key": E.get("DAHL_TOKEN_1"), "type": "openai"}
}

# Daftar 127 Model (lu bisa copy dari file ai_engine.py lu atau list di atas)
MODELS_TO_TEST = [
    # ChatAnywhere (27)
    ("chatanywhere", "gpt-6.1-sol"), ("chatanywhere", "gpt-6-astra"), ("chatanywhere", "gpt-6-sol"), ("chatanywhere", "gpt-6-luna"),
    ("chatanywhere", "gpt-5.6-sol"), ("chatanywhere", "gpt-5.6-luna"), ("chatanywhere", "gpt-5.6-terra"), ("chatanywhere", "gpt-5.5"),
    ("chatanywhere", "gpt-5.4"), ("chatanywhere", "gpt-5.4-mini"), ("chatanywhere", "gpt-5.4-nano"), ("chatanywhere", "gpt-5.2"),
    ("chatanywhere", "gpt-5.1"), ("chatanywhere", "gpt-5"), ("chatanywhere", "gpt-5-mini"), ("chatanywhere", "gpt-5-nano"),
    ("chatanywhere", "gpt-4o"), ("chatanywhere", "gpt-4o-mini"), ("chatanywhere", "gpt-4.1"), ("chatanywhere", "gpt-4.1-mini"),
    ("chatanywhere", "gpt-4.1-nano"), ("chatanywhere", "gpt-3.5-turbo"), ("chatanywhere", "deepseek-v4-pro"), ("chatanywhere", "deepseek-v4-flash"),
    ("chatanywhere", "deepseek-v4.1-flash"), ("chatanywhere", "deepseek-chat"), ("chatanywhere", "deepseek-v3.2"),
    # Groq (4)
    ("groq", "openai/gpt-oss-120b"), ("groq", "openai/gpt-oss-20b"), ("groq", "qwen/qwen3.8-27b"), ("groq", "allam-2-7b"),
    # Gemini (5)
    ("gemini", "gemini-3.6-flash"), ("gemini", "gemini-3.5-flash"), ("gemini", "gemini-3.5-flash-lite"), ("gemini", "gemini-3-flash-preview"), ("gemini", "gemma-4-31b-it"),
    # Onomeo (15)
    ("onomeo", "auto"), ("onomeo", "deepseek-v4-flash"), ("onomeo", "glm-5.2"), ("onomeo", "gemini-3.1-flash-lite"), ("onomeo", "gemini-3.5-flash-lite"),
    ("onomeo", "gpt-oss-20b"), ("onomeo", "muse-glimmer-30b"), ("onomeo", "minimax-m2.7"), ("onomeo", "codestral-latest"), ("onomeo", "ministral-14b-latest"),
    ("onomeo", "hy4-preview"), ("onomeo", "stealth/glyph-cluster"), ("onomeo", "glm-4.5-flash"), ("onomeo", "glm-4.6v-flash"), ("onomeo", "glm-4.7-flash"),
    # Cloudflare (23)
    ("cloudflare", "@cf/openai/gpt-oss-120b"), ("cloudflare", "@cf/openai/gpt-oss-20b"), ("cloudflare", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
    ("cloudflare", "@cf/meta/llama-4-scout-17b-16e-instruct"), ("cloudflare", "@cf/meta/llama-3.1-8b-instruct-fp8"), ("cloudflare", "@cf/meta/llama-3.2-3b-instruct"),
    ("cloudflare", "@cf/meta/llama-3.2-1b-instruct"), ("cloudflare", "@cf/meta-llama/llama-2-7b-chat-hf-lora"), ("cloudflare", "@cf/qwen/qwen3.8-27b"),
    ("cloudflare", "@cf/qwen/qwq-32b"), ("cloudflare", "@cf/qwen/qwen2.5-coder-32b-instruct"), ("cloudflare", "@cf/qwen/qwen3-30b-a3b-fp8"),
    ("cloudflare", "@cf/google/gemma-4-26b-a4b-it"), ("cloudflare", "@cf/google/gemma-7b-it-lora"), ("cloudflare", "@cf/google/gemma-2b-it-lora"),
    ("cloudflare", "@cf/mistralai/mistral-small-3.1-24b-instruct"), ("cloudflare", "@cf/mistral/mistral-7b-instruct-v0.2-lora"), ("cloudflare", "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"),
    ("cloudflare", "@cf/zai-org/glm-4.7-flash"), ("cloudflare", "@cf/nvidia/nemotron-3-120b-a12b"), ("cloudflare", "@cf/ibm-granite/granite-4.0-h-micro"),
    ("cloudflare", "@cf/aisingapore/gemma-sea-lion-v4-27b-it"), ("cloudflare", "@cf/daily-co/phonellm-mini-alpha-2"),
    # Mistral (12)
    ("mistral", "codestral-2508"), ("mistral", "codestral-latest"), ("mistral", "mistral-code-latest"), ("mistral", "mistral-code-fim-latest"),
    ("mistral", "ministral-14b-2512"), ("mistral", "ministral-14b-latest"), ("mistral", "ministral-3b-2512"), ("mistral", "ministral-3b-latest"),
    ("mistral", "ministral-8b-2512"), ("mistral", "ministral-8b-latest"), ("mistral", "voxtral-small-2507"), ("mistral", "voxtral-small-latest"),
    # OpenRouter (11)
    ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"), ("openrouter", "nvidia/nemotron-3.5-super-vl:free"), ("openrouter", "nvidia/nemotron-3.5-lightning:free"),
    ("openrouter", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"), ("openrouter", "nvidia/nemotron-3.5-content-safety:free"), ("openrouter", "recursive/flint-v1.0:free"),
    ("openrouter", "dots-studio/dots-3-note-preview:free"), ("openrouter", "liquid/lfm-2.5-2.6b:free"), ("openrouter", "poolside/laguna-s-2.1:free"),
    ("openrouter", "cohere/north-mini-code:free"), ("openrouter", "openrouter/free"),
    # Cohere (10)
    ("cohere", "command-a-plus-05-2026"), ("cohere", "command-a-03-2025"), ("cohere", "command-a-reasoning-08-2025"), ("cohere", "command-a-translate-08-2025"),
    ("cohere", "command-a-vision-07-2025"), ("cohere", "command-r-plus-08-2024"), ("cohere", "command-r-08-2024"), ("cohere", "command-r7b-12-2024"),
    ("cohere", "c4ai-aya-expanse-32b"), ("cohere", "c4ai-aya-vision-32b"),
    # OVH/KiloCode (12)
    ("ovh", "Meta-Llama-3_3-70B-Instruct"), ("ovh", "Mistral-Small-3.2-24B-Instruct-2506"), ("ovh", "Qwen2.5-VL-72B-Instruct"), ("ovh", "Mistral-Nemo-Instruct-2407"),
    ("llm7", "codestral-latest"), ("llm7", "gpt-oss:20b"), ("llm7", "minimax-m2.7"), ("llm7", "mistral-Nemo-Instruct-2407"), ("llm7", "nemotron-3-nano:30b"),
    # Pollinations (2) & Dahl (1)
    ("pollinations", "openai"), ("pollinations", "openai-fast"), ("dahl", "MiniMaxAI/MiniMax-M2.7")
]

async def test_speed(session, provider_name, model):
    cfg = PROVIDERS.get(provider_name)
    if not cfg: return None
    
    headers = {"Content-Type": "application/json"}
    if cfg["key"]: headers["Authorization"] = f"Bearer {cfg['key']}"

    payload = {"model": model, "messages": [{"role": "user", "content": "Halo"}], "max_tokens": 10}
    
    # Handle specific provider formats
    if cfg["type"] == "gemini":
        url = cfg["url"].format(model=model, key=cfg["key"])
        payload = {"contents": [{"parts": [{"text": "Halo"}]}]}
    elif cfg["type"] == "cloudflare":
        url = f"{cfg['url'].format(acc=cfg['acc'])}{model}"
    elif cfg["type"] == "cohere":
        url = cfg["url"]
    else:
        url = cfg["url"]

    start_time = time.time()
    try:
        async with session.post(url, headers=headers, json=payload, timeout=15) as r:
            if r.status == 200:
                await r.json() # Make sure we get the full body
                elapsed = round(time.time() - start_time, 2)
                return elapsed
    except Exception:
        pass
    return None

async def main():
    print(f"⏳ Memulai Speed Test {len(MODELS_TO_TEST)} Model...")
    print("Ngetes satu per satu (maks 15 detik per model).\n")
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for provider, model in MODELS_TO_TEST:
            print(f"Menguji {provider} -> {model}...", end=" ", flush=True)
            speed = await test_speed(session, provider, model)
            if speed is not None:
                print(f"✅ {speed}s")
                results.append((provider, model, speed))
            else:
                print(f"❌ Gagal/Timeout")
    
    # Urutin berdasarkan kecepatan (paling kecil = paling cepat)
    results.sort(key=lambda x: x[2])
    
    with open(OUTPUT_FILE, "w") as f:
        f.write("=== HASIL SPEED TEST ===\n\n")
        for i, (p, m, s) in enumerate(results, 1):
            f.write(f"{i}. {s}s - {p} -> {m}\n")
            
    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")
    print("Liat 10 Model Tercepat:")
    for i, (p, m, s) in enumerate(results[:10], 1):
        print(f"{i}. {s}s - {p} -> {m}")

if __name__ == "__main__":
    asyncio.run(main())
