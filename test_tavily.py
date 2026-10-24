import asyncio, aiohttp, json

async def test_tavily():
    async with aiohttp.ClientSession() as s:
        async with s.post(
            "https://api.tavily.com/search",
            headers={
                "Content-Type": "application/json",
                "X-Tavily-Access-Mode": "keyless"
            },
            json={"query": "berita AI terbaru", "max_results": 3, "search_depth": "basic"},
            timeout=15
        ) as r:
            print(f"Status: {r.status}")
            data = await r.json()
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2500])

if __name__ == "__main__":
    asyncio.run(test_tavily())
