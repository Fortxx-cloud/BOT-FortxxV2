import aiohttp
import asyncio
import json
import re

QUERY = "berita AI terbaru"

async def test_wikipedia(session):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": QUERY,
        "format": "json",
        "utf8": 1
    }
    try:
        async with session.get(url, params=params, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                results = data.get("query", {}).get("search", [])
                if results:
                    return f"✅ Wikipedia: {len(results)} hasil. Contoh: {results[0]['title']}"
                return "⚠️ Wikipedia: 0 hasil."
            return f"❌ Wikipedia: HTTP {r.status}"
    except Exception as e:
        return f"❌ Wikipedia: {type(e).__name__}"

async def test_ddg_instant(session):
    url = "https://api.duckduckgo.com/"
    params = {"q": QUERY, "format": "json", "no_html": 1}
    try:
        async with session.get(url, params=params, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                abstract = data.get("AbstractText", "")
                related = data.get("RelatedTopics", [])
                if abstract:
                    return f"✅ DDG Instant: {abstract[:100]}..."
                elif related:
                    return f"✅ DDG Instant: {len(related)} topik terkait."
                return "⚠️ DDG Instant: 0 hasil."
            return f"❌ DDG Instant: HTTP {r.status}"
    except Exception as e:
        return f"❌ DDG Instant: {type(e).__name__}"

async def test_searxng(session):
    # Coba beberapa instance publik
    instances = ["https://searx.be", "https://searx.tiekoetter.com", "https://search.bus-hit.me"]
    for base in instances:
        url = f"{base}/search"
        params = {"q": QUERY, "format": "json"}
        try:
            async with session.get(url, params=params, timeout=15) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get("results", [])
                    if results:
                        return f"✅ SearXNG ({base}): {len(results)} hasil."
                    return f"⚠️ SearXNG ({base}): 0 hasil."
                elif r.status == 403:
                    continue
        except:
            continue
    return "❌ SearXNG: Semua instance publik gagal."

async def test_ddg_lite(session):
    url = "https://html.duckduckgo.com/html/"
    params = {"q": QUERY}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(url, params=params, headers=headers, timeout=15) as r:
            if r.status == 200:
                html = await r.text()
                # Cari jumlah hasil pake regex sederhana
                results = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)">(.*?)</a>', html)
                if results:
                    return f"✅ DDG Lite: {len(results)} hasil (HTML)."
                return "⚠️ DDG Lite: 0 hasil."
            return f"❌ DDG Lite: HTTP {r.status}"
    except Exception as e:
        return f"❌ DDG Lite: {type(e).__name__}"

async def test_mojeek(session):
    url = "https://www.mojeek.com/search"
    params = {"q": QUERY}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(url, params=params, headers=headers, timeout=15) as r:
            if r.status == 200:
                html = await r.text()
                results = re.findall(r'<a class="ob" href="(.*?)"', html)
                if results:
                    return f"✅ Mojeek: {len(results)} hasil (HTML)."
                return "⚠️ Mojeek: 0 hasil."
            return f"❌ Mojeek: HTTP {r.status}"
    except Exception as e:
        return f"❌ Mojeek: {type(e).__name__}"

async def main():
    print(f"⏳ Ngetes API Keyless Search buat query: '{QUERY}'...\n")
    async with aiohttp.ClientSession() as session:
        tasks = [
            test_wikipedia(session),
            test_ddg_instant(session),
            test_searxng(session),
            test_ddg_lite(session),
            test_mojeek(session)
        ]
        results = await asyncio.gather(*tasks)
        for res in results:
            print(res)

if __name__ == "__main__":
    asyncio.run(main())
