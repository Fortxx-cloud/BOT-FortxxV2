import os, aiohttp, asyncio
from dotenv import load_dotenv

load_dotenv()

async def cek_api():
    async with aiohttp.ClientSession() as session:
        # 1. Tes Serper (Google Search)
        print("⏳ Ngetes Serper API...")
        try:
            async with session.post("https://google.serper.dev/search", 
                                    headers={"X-API-KEY": os.getenv("SERPER_API_KEY"), "Content-Type": "application/json"},
                                    json={"q": "Discord server aesthetic ideas"}, timeout=10) as r:
                print("✅ Serper API: BERHASIL" if r.status == 200 else f"❌ Serper API: GAGAL (HTTP {r.status})")
        except Exception as e:
            print(f"❌ Serper API: ERROR ({e})")

        # 2. Tes LangSearch
        print("⏳ Ngetes LangSearch API...")
        try:
            async with session.post("https://api.langsearch.com/v1/web-search", 
                                    headers={"Authorization": f"Bearer {os.getenv('LANGSEARCH_API_KEY')}", "Content-Type": "application/json"},
                                    json={"query": "GTA SAMP server name ideas", "count": 1}, timeout=10) as r:
                print("✅ LangSearch API: BERHASIL" if r.status == 200 else f"❌ LangSearch API: GAGAL (HTTP {r.status})")
        except Exception as e:
            print(f"❌ LangSearch API: ERROR ({e})")

        # 3. Tes Exa AI
        print("⏳ Ngetes Exa API...")
        try:
            async with session.post("https://api.exa.ai/search", 
                                    headers={"x-api-key": os.getenv("EXA_API_KEY"), "Content-Type": "application/json"},
                                    json={"query": "best discord server layouts", "numResults": 1}, timeout=10) as r:
                print("✅ Exa API: BERHASIL" if r.status == 200 else f"❌ Exa API: GAGAL (HTTP {r.status})")
        except Exception as e:
            print(f"❌ Exa API: ERROR ({e})")

        # 4. Tes Pollinations (Multimodal / Image Gen)
        print("⏳ Ngetes Pollinations API...")
        try:
            url = "https://image.pollinations.ai/prompt/cool%20dragon%20logo"
            async with session.get(url, timeout=15) as r:
                print("✅ Pollinations API: BERHASIL" if r.status == 200 else f"❌ Pollinations API: GAGAL (HTTP {r.status})")
        except Exception as e:
            print(f"❌ Pollinations API: ERROR ({e})")

if __name__ == "__main__":
    asyncio.run(cek_api())
