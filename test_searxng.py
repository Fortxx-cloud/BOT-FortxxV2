import asyncio, aiohttp

INSTANCES = [
    "https://searx.be",
    "https://search.bus-hit.me",
    "https://searx.tiekoetter.com",
    "https://priv.au",
    "https://baresearch.org",
]

async def test_instance(session, base):
    try:
        async with session.get(
            f"{base}/search",
            params={"q": "berita AI terbaru", "format": "json"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        ) as r:
            if r.status == 200:
                try:
                    data = await r.json()
                except:
                    print(f"⚠️  {base}: 200 tapi bukan JSON")
                    return
                results = data.get("results", [])
                print(f"✅ {base}: {len(results)} hasil")
                if results:
                    print(f"   #1: {results[0].get('title','?')[:70]}")
            elif r.status == 403:
                print(f"🚫 {base}: 403 (JSON disabled)")
            else:
                print(f"❌ {base}: HTTP{r.status}")
    except Exception as e:
        print(f"❌ {base}: {type(e).__name__}")

async def main():
    async with aiohttp.ClientSession() as s:
        for inst in INSTANCES:
            await test_instance(s, inst)

if __name__ == "__main__":
    asyncio.run(main())
