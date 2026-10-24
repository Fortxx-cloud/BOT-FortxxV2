import os, aiohttp, asyncio
from dotenv import load_dotenv
load_dotenv()

PROVIDERS = {
    "Onomeo": {"url": "https://onomeo.com/v1", "key": os.getenv("ONOMEO_API_KEY")},
    "Itera": {"url": "https://api.iteracompute.com/v1", "key": os.getenv("ITERA_API_KEY")},
    "FreeTheAI": {"url": "https://api.freetheai.org/v1", "key": os.getenv("FREETHEAI_API_KEY")}
}

async def test(session, name, cfg):
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    try:
        # 1. Coba tarik daftar model
        async with session.get(f"{cfg['url']}/models", headers=headers, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                models = [m["id"] for m in data.get("data", [])]
                print(f"✅ {name}: Berhasil tarik {len(models)} model.")
                # 2. Tes model pertama
                if models:
                    payload = {"model": models[0], "messages": [{"role": "user", "content": "Halo"}]}
                    async with session.post(f"{cfg['url']}/chat/completions", headers=headers, json=payload, timeout=20) as r2:
                        print(f"   {name} -> {models[0]}: {'✅ BERHASIL' if r2.status == 200 else f'❌ GAGAL (HTTP {r2.status})'}")
            else:
                print(f"❌ {name}: Gagal tarik model (HTTP {r.status})")
    except Exception as e:
        print(f"❌ {name}: Error koneksi ({type(e).__name__})")

async def main():
    print("⏳ Ngetes ulang 3 API (URL sudah diperbaiki)...\n")
    async with aiohttp.ClientSession() as session:
        for name, cfg in PROVIDERS.items():
            if not cfg["key"]:
                print(f"⚠️ {name}: API Key kosong di .env")
                continue
            await test(session, name, cfg)

if __name__ == "__main__":
    asyncio.run(main())
