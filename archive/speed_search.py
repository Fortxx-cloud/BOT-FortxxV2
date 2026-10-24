import os, asyncio, aiohttp, time
from dotenv import load_dotenv
from webless import search as webless_search
from bs4 import BeautifulSoup
import urllib.parse

load_dotenv()

QUERY = "harga PS5 terbaru di Indonesia"

async def test_serper(session):
    key = os.getenv("SERPER_API_KEY")
    if not key: return ("Serper", None, "no key")
    start = time.time()
    try:
        headers = {"X-API-KEY": key, "Content-Type": "application/json"}
        payload = {"q": QUERY, "num": 5, "gl": "id", "hl": "id"}
        async with session.post("https://google.serper.dev/search", headers=headers, json=payload, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                n = len(data.get("organic", []))
                return ("Serper (Google)", round(time.time() - start, 2), f"{n} hasil")
            return ("Serper (Google)", None, f"HTTP {r.status}")
    except Exception as e:
        return ("Serper (Google)", None, type(e).__name__)

async def test_ddg(session):
    start = time.time()
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with session.get("https://html.duckduckgo.com/html/", params={"q": QUERY}, headers=headers, timeout=15) as r:
            if r.status == 200:
                html = await r.text()
                soup = BeautifulSoup(html, "html.parser")
                n = len(soup.select("a.result__a"))
                return ("DDG HTML", round(time.time() - start, 2), f"{n} hasil")
            return ("DDG HTML", None, f"HTTP {r.status}")
    except Exception as e:
        return ("DDG HTML", None, type(e).__name__)

async def test_webless():
    start = time.time()
    try:
        res = await webless_search(QUERY, limit=5)
        return ("Webless", round(time.time() - start, 2), f"{len(res)} hasil")
    except Exception as e:
        return ("Webless", None, type(e).__name__)

async def test_tavily(session):
    start = time.time()
    try:
        headers = {"Content-Type": "application/json", "X-Tavily-Access-Mode": "keyless"}
        payload = {"query": QUERY, "max_results": 5}
        async with session.post("https://api.tavily.com/search", headers=headers, json=payload, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                n = len(data.get("results", []))
                return ("Tavily", round(time.time() - start, 2), f"{n} hasil")
            return ("Tavily", None, f"HTTP {r.status}")
    except Exception as e:
        return ("Tavily", None, type(e).__name__)

async def test_exa(session):
    key = os.getenv("EXA_API_KEY")
    if not key: return ("Exa", None, "no key")
    start = time.time()
    try:
        headers = {"x-api-key": key, "Content-Type": "application/json"}
        payload = {"query": QUERY, "numResults": 5}
        async with session.post("https://api.exa.ai/search", headers=headers, json=payload, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                n = len(data.get("results", []))
                return ("Exa AI", round(time.time() - start, 2), f"{n} hasil")
            return ("Exa AI", None, f"HTTP {r.status}")
    except Exception as e:
        return ("Exa AI", None, type(e).__name__)

async def test_langsearch(session):
    key = os.getenv("LANGSEARCH_API_KEY")
    if not key: return ("LangSearch", None, "no key")
    start = time.time()
    try:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {"query": QUERY, "count": 5}
        async with session.post("https://api.langsearch.com/v1/web-search", headers=headers, json=payload, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                pages = data.get("data", {}).get("webPages", {}).get("value", [])
                return ("LangSearch", round(time.time() - start, 2), f"{len(pages)} hasil")
            return ("LangSearch", None, f"HTTP {r.status}")
    except Exception as e:
        return ("LangSearch", None, type(e).__name__)

async def test_serpapi(session):
    key = os.getenv("SERPAPI_KEY")
    if not key: return ("SerpApi", None, "no key")
    start = time.time()
    try:
        url = f"https://serpapi.com/search?api_key={key}&q={QUERY}&engine=google&num=5"
        async with session.get(url, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                n = len(data.get("organic_results", []))
                return ("SerpApi", round(time.time() - start, 2), f"{n} hasil")
            return ("SerpApi", None, f"HTTP {r.status}")
    except Exception as e:
        return ("SerpApi", None, type(e).__name__)

async def main():
    print(f"🚀 SPEED TEST SEARCH ENGINE")
    print(f"📝 Query: '{QUERY}'\n")
    print("=" * 65)
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            test_serper(session),
            test_ddg(session),
            test_webless(),
            test_tavily(session),
            test_exa(session),
            test_langsearch(session),
            test_serpapi(session),
        ]
        results = await asyncio.gather(*tasks)
    
    # Filter yang sukses (ada waktu)
    sukses = [r for r in results if r[1] is not None]
    gagal = [r for r in results if r[1] is None]
    
    # Urutkan dari tercepat
    sukses.sort(key=lambda x: x[1])
    
    print("\n🏆 RANKING (Tercepat → Terlambat):")
    print("=" * 65)
    for i, (name, t, info) in enumerate(sukses, 1):
        print(f"{i}. {name:<20} {t:>6.2f}s   {info}")
    
    if gagal:
        print("\n❌ GAGAL / GAK PUNYA KEY:")
        print("=" * 65)
        for name, _, info in gagal:
            print(f"   {name:<20} {info}")
    
    print("\n" + "=" * 65)
    if sukses:
        fastest = sukses[0]
        print(f"⚡ TERCEPAT: {fastest[0]} ({fastest[1]}s)")
        print(f"🎯 REKOMENDASI: Taruh {fastest[0]} di urutan pertama di search_multi()")

if __name__ == "__main__":
    asyncio.run(main())
