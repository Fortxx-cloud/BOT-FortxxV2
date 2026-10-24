import asyncio, aiohttp

async def main():
    async with aiohttp.ClientSession() as s:
        params = {"query": "artificial intelligence", "mode": "ArtList", "maxrecords": 3, "format": "json", "sort": "DateDesc"}
        async with s.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params, timeout=20) as r:
            print("Status:", r.status)
            if r.status == 200:
                data = await r.json()
                arts = data.get("articles", [])
                for i, a in enumerate(arts, 1):
                    print(f"{i}. {a.get('title')[:80]}")
                    print(f"   {a.get('url')}")
            else:
                print(await r.text())

asyncio.run(main())
