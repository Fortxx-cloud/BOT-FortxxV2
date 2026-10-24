import asyncio, aiohttp

async def main():
    async with aiohttp.ClientSession() as s:
        async with s.get("https://freenewsapi.ai/v1/search", params={"q": "teknologi", "size": 3}, timeout=15) as r:
            print("Status:", r.status)
            if r.status == 200:
                data = await r.json()
                arts = data.get("articles", [])
                for i, a in enumerate(arts, 1):
                    print(f"{i}. {a.get('title')}")
                    print(f"   {a.get('url')}")
            else:
                print(await r.text())

asyncio.run(main())
