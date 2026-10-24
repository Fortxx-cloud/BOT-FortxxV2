import aiohttp
import asyncio
import json

ENDPOINTS = {
    "BlockRun": "https://blockrun.ai/api/v1/models",
    "KeylessAI": "https://keylessai.thryx.workers.dev/v1/models",
    "UncloseAI": "https://hermes.ai.unturf.com/v1/models",
    "Api.Airforce": "https://api.airforce/v1/models"
}

async def cek(session, name, url):
    try:
        async with session.get(url, timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                models = []
                if isinstance(data, dict) and "data" in data:
                    models = [m.get("id") for m in data["data"] if m.get("id")]
                elif isinstance(data, list):
                    models = [m.get("id") or m.get("name") for m in data if isinstance(m, dict)]
                
                if models:
                    print(f"\n✅ {name}: {len(models)} model")
                    for m in models[:15]: # Tampilkan 15 pertama
                        print(f"   - {m}")
                    if len(models) > 15:
                        print(f"   ... dan {len(models)-15} model lainnya")
                else:
                    print(f"\n⚠️ {name}: Endpoint merespons, tapi format model tidak dikenali.")
            else:
                print(f"\n❌ {name}: HTTP {r.status} (Mungkin butuh key atau endpoint salah)")
    except Exception as e:
        print(f"\n❌ {name}: Error koneksi ({type(e).__name__})")

async def main():
    print("⏳ Menarik daftar model dari gateway no-auth...\n")
    async with aiohttp.ClientSession() as session:
        tasks = [cek(session, name, url) for name, url in ENDPOINTS.items()]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
