import asyncio
import aiohttp
import base64
import os
import json
from dotenv import load_dotenv
load_dotenv(".env")

# === KONFIGURASI ===
IMAGE_PATH = "test.png"  # Ganti dengan path gambar lu
PROMPT = "Baca gambar ini. Ekstrak semua kategori dan channel Discord dalam format JSON: {\"categories\": [{\"name\": \"...\", \"channels\": [{\"name\": \"...\", \"type\": \"text\"}]}]}"

# === FUNGSI BACA GAMBAR ===
def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# === TES 1: GROQ (QWEN 3.8 27B) ===
async def test_groq(session, b64_img):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return "GROQ: Key kosong"
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
            ]
        }],
        "max_tokens": 1000
    }
    try:
        async with session.post(url, headers=headers, json=payload, timeout=30) as r:
            if r.status == 200:
                data = await r.json()
                return f"✅ GROQ BERHASIL:\n{data['choices'][0]['message']['content'][:500]}..."
            else:
                return f"❌ GROQ GAGAL: HTTP{r.status} - {(await r.text())[:100]}"
    except Exception as e:
        return f"❌ GROQ ERROR: {e}"

# === TES 2: OPENROUTER (QWEN 2.5 VL) ===
async def test_openrouter(session, b64_img):
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return "OPENROUTER: Key kosong"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/local-test",
        "X-Title": "Vision Test"
    }
    payload = {
        "model": "qwen/qwen2.5-vl-32b-instruct:free",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
            ]
        }],
        "max_tokens": 1000
    }
    try:
        async with session.post(url, headers=headers, json=payload, timeout=30) as r:
            if r.status == 200:
                data = await r.json()
                return f"✅ OPENROUTER BERHASIL:\n{data['choices'][0]['message']['content'][:500]}..."
            else:
                return f"❌ OPENROUTER GAGAL: HTTP{r.status} - {(await r.text())[:100]}"
    except Exception as e:
        return f"❌ OPENROUTER ERROR: {e}"

# === TES 3: POLLINATIONS (TANPA KEY) ===
async def test_pollinations(session, b64_img):
    url = "https://text.pollinations.ai/openai"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "openai",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
            ]
        }],
        "max_tokens": 1000
    }
    try:
        async with session.post(url, headers=headers, json=payload, timeout=30) as r:
            if r.status == 200:
                data = await r.json()
                return f"✅ POLLINATIONS BERHASIL:\n{data['choices'][0]['message']['content'][:500]}..."
            else:
                return f"❌ POLLINATIONS GAGAL: HTTP{r.status} - {(await r.text())[:100]}"
    except Exception as e:
        return f"❌ POLLINATIONS ERROR: {e}"

async def main():
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ File '{IMAGE_PATH}' nggak ketemu. Simpan gambar dulu ya Bang.")
        return
    print(f"🖼️ Membaca gambar: {IMAGE_PATH}")
    b64 = encode_image(IMAGE_PATH)
    print(f"📦 Base64 size: {len(b64)} chars\n")
    
    async with aiohttp.ClientSession() as session:
        print("--- Tes 1: Groq (Qwen 3.8) ---")
        print(await test_groq(session, b64))
        print("\n--- Tes 2: OpenRouter (Qwen 2.5 VL) ---")
        print(await test_openrouter(session, b64))
        print("\n--- Tes 3: Pollinations (Tanpa Key) ---")
        print(await test_pollinations(session, b64))

if __name__ == "__main__":
    asyncio.run(main())
