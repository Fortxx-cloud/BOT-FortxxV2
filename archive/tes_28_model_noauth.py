import aiohttp
import asyncio

# Daftar 28 model yang lolos dari tes kilat
MODELS_TO_TEST = {
    "KiloCode": {
        "base_url": "https://api.kilo.ai/api/gateway",
        "models": [
            "recursive/flint-v1.0:free", "nvidia/nemotron-3.5-super-vl:free",
            "reflection/beam-free", "stealth/glyph-cluster", "kilo-auto/free",
            "nvidia/nemotron-3.5-lightning:free", "dots-studio/dots-3-note-preview:free",
            "poolside/laguna-s-2.1:free", "poolside/laguna-xs-2.1:free",
            "cohere/north-mini-code:free", "nvidia/nemotron-3.5-content-safety:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "openrouter/free", "liquid/lfm-2.5-2.6b:free", "kilo-auto/small"
        ]
    },
    "OVH_AI": {
        "base_url": "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
        "models": [
            "Qwen3Guard-Gen-0.6B", "Qwen3.6-27B", "Qwen3Guard-Gen-8B",
            "Meta-Llama-3_3-70B-Instruct", "Qwen3.8-27B", "Mistral-Small-3.2-24B-Instruct-2506",
            "gpt-oss-20b", "Qwen3.5-9B", "Qwen2.5-VL-72B-Instruct", 
            "Mistral-Nemo-Instruct-2407", "Qwen3.5-397B-A17B", "gpt-oss-120b"
        ]
    }
}

OUTPUT_FILE = "hasil_konfirmasi_28.txt"

async def test_model(session, provider, base_url, model, index, total):
    url = f"{base_url}/chat/completions"
    payload = {"model": model, "messages": [{"role": "user", "content": "Halo, siapa kamu?"}], "max_tokens": 20}
    try:
        async with session.post(url, json=payload, timeout=25) as r:
            if r.status == 200:
                data = await r.json()
                reply = data['choices'][0]['message']['content']
                res = f"✅ [STABIL] {provider} -> {model} -> \"{reply.strip()[:40]}...\""
            elif r.status == 429:
                res = f"⚠️ [LIMIT] {provider} -> {model} (HTTP 429)"
            else:
                res = f"❌ [GAGAL] {provider} -> {model} (HTTP {r.status})"
    except Exception as e:
        res = f"❌ [ERROR] {provider} -> {model}"
        
    print(f"[{index}/{total}] {res}")
    with open(OUTPUT_FILE, "a") as f:
        f.write(res + "\n")
    
    await asyncio.sleep(3) # Jeda 3 detik biar server mereka gak ngamuk

async def main():
    total_models = sum(len(p["models"]) for p in MODELS_TO_TEST.values())
    print(f"⏳ Ngetes {total_models} model no-auth secara perlahan (jeda 3 detik)...\n")
    
    with open(OUTPUT_FILE, "w") as f: f.write("=== KONFIRMASI MODEL NO-AUTH ===\n\n")
    
    async with aiohttp.ClientSession() as session:
        current_index = 1
        for provider, cfg in MODELS_TO_TEST.items():
            for model in cfg["models"]:
                await test_model(session, provider, cfg["base_url"], model, current_index, total_models)
                current_index += 1
                
    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
