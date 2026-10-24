
import os, asyncio, aiohttp, time, json
from collections import Counter
from dotenv import load_dotenv
load_dotenv()
E = os.environ

MAX_CONCURRENT = 5
MAX_RETRIES = 2
RETRY_DELAY = 5

PROVIDERS = {
    "chatanywhere": {"url": "https://api.chatanywhere.tech/v1/chat/completions", "key": E.get("CHATANYWHERE_API_KEY"), "type": "openai"},
    "cloudflare": {"url": "https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/", "key": E.get("CF_API_TOKEN"), "acc": E.get("CF_ACCOUNT_ID"), "type": "cloudflare"},
    "gemini": {"url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}", "key": E.get("GEMINI_API_KEY"), "type": "gemini"},
    "mistral": {"url": "https://api.mistral.ai/v1/chat/completions", "key": E.get("MISTRAL_API_KEY"), "type": "openai"},
    "onomeo": {"url": "https://onomeo.com/v1/chat/completions", "key": E.get("ONOMEO_API_KEY"), "type": "openai"},
    "openrouter": {"url": "https://openrouter.ai/api/v1/chat/completions", "key": E.get("OPENROUTER_API_KEY"), "type": "openai"},
    "groq": {"url": "https://api.groq.com/openai/v1/chat/completions", "key": E.get("GROQ_API_KEY"), "type": "openai"},
    "cohere": {"url": "https://api.cohere.com/v2/chat", "key": E.get("COHERE_API_KEY"), "type": "cohere"},
    "llm7": {"url": "https://api.llm7.io/v1/chat/completions", "key": E.get("LLM7_TOKENS"), "type": "openai"},
    "pollinations": {"url": "https://text.pollinations.ai/openai", "key": None, "type": "openai"},
    "dahl": {"url": "https://inference.dahl.global/v1/chat/completions", "key": E.get("DAHL_TOKEN_1"), "type": "openai"},
    "ovh": {"url": "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions", "key": "no-auth", "type": "openai"},
    "kilocode": {"url": "https://api.kilo.ai/api/gateway/chat/completions", "key": "no-auth", "type": "openai"},
    "blockrun": {"url": "https://blockrun.ai/api/v1/chat/completions", "key": "no-auth", "type": "openai"},
}

SYSTEM = "Jawab dengan reasoning step-by-step. Bahasa Indonesia, padat, dan akhiri dengan 'JAWABAN AKHIR:' yang eksplisit."

def quick_grade(answer):
    if not answer: return "GAGAL"
    a = answer.lower()
    if not any(x in a for x in ["kotak c", "box c", "dari c ", "dari c,", "dari c.", "c (", "c)"]):
        return "SALAH"
    has_apel = "apel" in a
    has_jeruk = "jeruk" in a
    has_campur = any(x in a for x in ["campur", "mixed", "apel+jeruk", "apel + jeruk", "apel dan jeruk", "keduanya"])
    if has_apel and has_jeruk and has_campur:
        return "BENAR"
    return "REVIEW"

async def call_model(session, provider, model, prompt):
    cfg = PROVIDERS.get(provider)
    if not cfg: return None, "SKIP"
    headers = {"Content-Type": "application/json"}
    if cfg.get("key") and cfg["key"] != "no-auth":
        headers["Authorization"] = f"Bearer {cfg['key']}"
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/local-test"
        headers["X-Title"] = "Kubu Test"
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    if cfg["type"] == "gemini":
        url = cfg["url"].format(model=model, key=cfg["key"])
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0, "maxOutputTokens": 1000}}
    elif cfg["type"] == "cloudflare":
        url = f"{cfg['url'].format(acc=cfg['acc'])}{model}"
        payload = {"messages": messages, "max_tokens": 1000, "temperature": 0}
    elif cfg["type"] == "cohere":
        url = cfg["url"]
        payload = {"model": model, "messages": messages, "max_tokens": 1000, "temperature": 0}
    else:
        url = cfg["url"]
        payload = {"model": model, "messages": messages, "max_tokens": 1000, "temperature": 0}
    start = time.time()
    try:
        async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=90)) as r:
            elapsed = round(time.time() - start, 2)
            if r.status == 200:
                data = await r.json()
                try:
                    if cfg["type"] == "gemini":
                        txt = data['candidates'][0]['content']['parts'][0]['text']
                    elif cfg["type"] == "cloudflare":
                        txt = data['result']['response'] if 'result' in data and 'response' in data['result'] else data['choices'][0]['message']['content']
                    elif cfg["type"] == "cohere":
                        txt = data.get('message', {}).get('content', [{}])[0].get('text') or data['choices'][0]['message']['content']
                    else:
                        txt = data['choices'][0]['message']['content']
                    return txt.strip(), elapsed
                except (KeyError, IndexError, TypeError):
                    return None, f"PARSE_ERR:{list(data.keys())[:3]}"
            body = await r.text()
            if r.status in (429, 402, 403):
                return None, f"LIMIT({r.status})"
            return None, f"HTTP{r.status}:{body[:120]}"
    except asyncio.TimeoutError:
        return None, "TIMEOUT"
    except Exception as e:
        return None, f"ERR:{type(e).__name__}:{str(e)[:60]}"

async def call_with_retry(session, provider, model, prompt, sem):
    last = None
    for attempt in range(MAX_RETRIES + 1):
        async with sem:
            answer, status = await call_model(session, provider, model, prompt)
        if answer:
            return answer, status
        last = status
        if isinstance(status, str) and ("LIMIT" in status or "TIMEOUT" in status) and attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            continue
        break
    return None, last

async def main():
    QUESTION = "Ada 3 kotak di meja: A berlabel 'Apel', B berlabel 'Jeruk', C berlabel 'Apel+Jeruk'. TAPI ketiga label PASTI SALAH. Kamu boleh ambil 1 buah dari 1 kotak saja (tanpa lihat isi kotak). Bagaimana cara menentukan isi ketiga kotak dengan pasti?"
    MODELS = [('chatanywhere', 'gpt-6.1-sol'), ('chatanywhere', 'gpt-6-astra'), ('chatanywhere', 'gpt-6-sol'), ('chatanywhere', 'gpt-6-luna'), ('chatanywhere', 'gpt-5.6-sol'), ('chatanywhere', 'gpt-5.6-luna'), ('chatanywhere', 'gpt-5.6-terra'), ('chatanywhere', 'gpt-5.5'), ('chatanywhere', 'gpt-5.4'), ('chatanywhere', 'gpt-5.4-mini'), ('chatanywhere', 'gpt-5.4-nano'), ('chatanywhere', 'gpt-5.2'), ('chatanywhere', 'gpt-5.1'), ('chatanywhere', 'gpt-5'), ('chatanywhere', 'gpt-5-mini'), ('chatanywhere', 'gpt-5-nano'), ('chatanywhere', 'gpt-4o'), ('chatanywhere', 'gpt-4o-mini'), ('chatanywhere', 'gpt-4.1'), ('chatanywhere', 'gpt-4.1-mini'), ('chatanywhere', 'gpt-4.1-nano'), ('chatanywhere', 'gpt-3.5-turbo'), ('chatanywhere', 'deepseek-v4-pro'), ('chatanywhere', 'deepseek-v4-flash'), ('chatanywhere', 'deepseek-v4.1-flash'), ('chatanywhere', 'deepseek-chat'), ('chatanywhere', 'deepseek-v3.2'), ('cohere', 'command-a-plus-05-2026'), ('cohere', 'command-a-03-2025'), ('cohere', 'command-a-reasoning-08-2025'), ('cohere', 'command-a-translate-08-2025'), ('cohere', 'command-a-vision-07-2025'), ('cohere', 'command-r-plus-08-2024'), ('cohere', 'command-r-08-2024'), ('cohere', 'command-r7b-12-2024'), ('cohere', 'c4ai-aya-expanse-32b'), ('cohere', 'c4ai-aya-vision-32b'), ('gemini', 'gemini-3.6-flash'), ('gemini', 'gemini-3.5-flash'), ('gemini', 'gemini-3.5-flash-lite'), ('gemini', 'gemini-3-flash-preview'), ('gemini', 'gemma-4-31b-it')]
    KUBU = 1
    print(f"\n🧪 KUBU {KUBU} — {len(MODELS)} model (concurrent={MAX_CONCURRENT})\n")
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    lock = asyncio.Lock()
    results = {"ok": [], "fail": []}
    counter = {"n": 0}

    async def one(provider, model):
        answer, elapsed = await call_with_retry(session, provider, model, QUESTION, sem)
        async with lock:
            counter["n"] += 1
            tag = f"[{counter['n']}/{len(MODELS)}]"
            if answer:
                grade = quick_grade(answer)
                icon = "✅" if grade == "BENAR" else ("🟡" if grade == "REVIEW" else "🟠")
                print(f"{tag} {icon} {provider}->{model} | {elapsed}s | {grade}")
                print(f"     {answer[:120].replace(chr(10),' ')}...")
                results["ok"].append({"provider": provider, "model": model, "elapsed": elapsed, "grade": grade, "answer": answer})
            else:
                print(f"{tag} ❌ {provider}->{model} | {elapsed}")
                results["fail"].append({"provider": provider, "model": model, "error": elapsed})

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*(one(p, m) for p, m in MODELS))

    print(f"\n{'='*64}")
    print(f"📊 KUBU {KUBU} SUMMARY")
    print(f"{'='*64}")
    print(f"✅ Sukses: {len(results['ok'])} / {len(MODELS)}")
    print(f"❌ Gagal : {len(results['fail'])}")
    grades = Counter(r["grade"] for r in results["ok"])
    for g in ["BENAR", "REVIEW", "SALAH"]:
        if grades.get(g): print(f"   {g}: {grades[g]}")
    if results["ok"]:
        print(f"\n🏆 TOP 5 (BENAR, latency terendah):")
        top = sorted([r for r in results["ok"] if r["grade"] == "BENAR"], key=lambda x: x["elapsed"])[:5]
        for r in top:
            print(f"   {r['elapsed']:>6}s  {r['provider']}->{r['model']}")
    out = {"kubu": KUBU, "total": len(MODELS), "ok": results["ok"], "fail": results["fail"], "grades": dict(grades)}
    with open(f"hasil_kubu_{KUBU}.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n💾 hasil_kubu_{KUBU}.json disimpan")
    print(f"✅ KUBU {KUBU} SELESAI!")

if __name__ == "__main__":
    asyncio.run(main())
