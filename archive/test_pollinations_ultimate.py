import aiohttp
import asyncio
import time

# Daftar LENGKAP model teks Pollinations dari dokumentasi & komunitas
# (Termasuk alias dan model tersembunyi)
MODELS = [
    # --- OPENAI FAMILY ---
    "openai", "openai-fast", "openai-large", "openai-reasoning", "openai-audio",
    "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini",
    
    # --- GOOGLE FAMILY ---
    "gemini", "gemini-fast", "gemini-large", "gemini-legacy", 
    "gemini-search", "gemini-thinking", "gemini-2.0-flash", "gemini-2.5-flash",
    
    # --- ANTHROPIC FAMILY ---
    "claude", "claude-fast", "claude-large", "claude-legacy", 
    "claude-hybridspace", "claude-3-5-sonnet", "claude-3-7-sonnet",
    
    # --- DEEPSEEK & REASONING ---
    "deepseek", "deepseek-r1", "deepseek-reasoner", "deepseek-v3", 
    "deepseek-r1-distill", "perplexity-reasoning", "perplexity-fast",
    
    # --- CODING MODELS ---
    "qwen-coder", "codestral", "mistral-code",
    
    # --- LLAMA FAMILY ---
    "llama", "llamalight", "llamaguard", "llama-scaleway", 
    "llama-3.3-70b", "llama-4-scout", "llama-4-maverick",
    
    # --- MISTRAL FAMILY ---
    "mistral", "mistral-large", "mistral-medium", "mistral-small", 
    "sur-mistral", "unity",
    
    # --- COMMUNITY / OTHERS ---
    "midijourney", "rtist", "searchgpt", "evil", "hormoz", 
    "hypnosis-tracy", "sur", "grok", "kimi", "qwen-safety", 
    "glm", "minimax", "nova-fast", "phi", "command-r"
]

URL = "https://text.pollinations.ai/openai"
OUTPUT_FILE = "hasil_pollinations_ultimate.txt"

async def test_model(session, model, index, total):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Halo"}],
        "max_tokens": 10
    }
    try:
        async with session.post(URL, json=payload, timeout=25) as r:
            if r.status == 200:
                try:
                    data = await r.json()
                    reply = data['choices'][0]['message']['content']
                    return f"✅ [TERBANG] {model} -> \"{reply.strip()[:40]}...\""
                except:
                    return f"✅ [TERBANG] {model} (Respons non-JSON)"
            elif r.status == 429:
                return f"⚠️ [LIMIT] {model} (HTTP 429 - Rate Limit)"
            else:
                return f"❌ [GAGAL] {model} (HTTP {r.status})"
    except Exception as e:
        return f"❌ [TIMEOUT] {model}"

async def main():
    total = len(MODELS)
    print(f"⏳ MEMULAI TES POLLINATIONS ULTIMATE")
    print(f"📦 Total model: {total}")
    print(f"⏱️ Estimasi waktu: ~{round(total * 15 / 60)} menit (jeda 15 detik/model)")
    print(f"📄 Hasil disimpan di: {OUTPUT_FILE}\n")
    
    with open(OUTPUT_FILE, "w") as f:
        f.write(f"=== TES POLLINATIONS ULTIMATE ({total} Model) ===\n\n")

    async with aiohttp.ClientSession() as session:
        for i, model in enumerate(MODELS, 1):
            start = time.time()
            res = await test_model(session, model, i, total)
            elapsed = round(time.time() - start, 1)
            
            print(f"[{i:02d}/{total}] {res} ({elapsed}s)")
            
            with open(OUTPUT_FILE, "a") as f:
                f.write(res + "\n")
            
            # Jeda 15 detik anti rate limit (Pollinations anonim)
            if i < total:
                await asyncio.sleep(15)
                
    print(f"\n✅ SELESAI! Cek file {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
