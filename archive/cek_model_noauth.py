import aiohttp
import asyncio
import json

# Endpoint No-Auth (Tanpa Login)
ENDPOINTS = {
    "Pollinations": "https://text.pollinations.ai/models",
    "UncloseAI": "https://hermes.ai.unturf.com/v1/models",
    "KeylessAI": "https://keylessai.thryx.workers.dev/v1/models",
    "BlockRun": "https://blockrun.ai/api/v1/models",
    "OVH AI": "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/models",
    "Kilo Code": "https://api.kilo.ai/api/gateway/models",
    "Api.Airforce": "https://api.airforce/v1/models"
}

async def cek_endpoint(session, name, url):
    print(f"\n📦 Nembak {name} ({url})...")
    try:
        async with session.get(url, timeout=10) as r:
            if r.status == 200:
                try:
                    data = await r.json()
                    # Kalau formatnya OpenAI (ada 'data')
                    if isinstance(data, dict) and "data" in data:
                        models = [m.get("id") for m in data["data"]]
                        print(f"✅ [BERHASIL] Dapet {len(models)} model:")
                        for m in models[:10]: # Batasi 10 biar gak kepanjangan
                            print(f"   - {m}")
                        if len(models) > 10:
                            print(f"   ... dan {len(models)-10} model lainnya")
                    # Kalau formatnya list of dict (kayak Pollinations)
                    elif isinstance(data, list):
                        models = [m.get("name") or m.get("id") for m in data if isinstance(m, dict)]
                        print(f"✅ [BERHASIL] Dapet {len(models)} model:")
                        for m in models[:10]:
                            print(f"   - {m}")
                        if len(models) > 10:
                            print(f"   ... dan {len(models)-10} model lainnya")
                    else:
                        print(f"⚠️ [FORMAT ANEH] Respons: {str(data)[:100]}...")
                except Exception as e:
                    print(f"❌ [GAGAL PARSE JSON] {e}")
            else:
                print(f"❌ [HTTP {r.status}] Endpoint ini gak ngasih daftar model. (Harus nembak manual)")
    except Exception as e:
        print(f"❌ [KONEKSI ERROR] {e}")

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [cek_endpoint(session, name, url) for name, url in ENDPOINTS.items()]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
