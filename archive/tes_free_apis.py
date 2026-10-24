import asyncio
import aiohttp

async def test_weather(session):
    print("🌤️  Tes Cuaca (Open-Meteo)...")
    try:
        async with session.get("https://geocoding-api.open-meteo.com/v1/search", 
                               params={"name": "Jakarta", "count": 1, "language": "id"}, timeout=10) as r:
            geo = await r.json()
            if not geo.get("results"): return print("   ❌ Lokasi gak ketemu.")
            loc = geo["results"][0]
            async with session.get("https://api.open-meteo.com/v1/forecast",
                                   params={"latitude": loc["latitude"], "longitude": loc["longitude"],
                                           "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                                           "timezone": "Asia/Jakarta"}, timeout=10) as r:
                w = await r.json()
                cur = w["current"]
                print(f"   ✅ {loc['name']}: {cur['temperature_2m']}°C, Kelembapan {cur['relative_humidity_2m']}%, Angin {cur['wind_speed_10m']} km/h")
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def test_dictionary(session):
    print("\n📖 Tes Kamus (Free Dictionary)...")
    try:
        async with session.get("https://api.dictionaryapi.dev/api/v2/entries/en/serendipity", timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                d = data[0]["meanings"][0]["definitions"][0]["definition"]
                print(f"   ✅ serendipity: {d[:100]}...")
            else:
                print(f"   ❌ HTTP {r.status}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def test_news(session):
    print("\n📰 Tes Berita (NewsMCP)...")
    try:
        async with session.get("https://newsmcp.io/v1/news/", timeout=15) as r:
            print(f"   Status HTTP: {r.status}")
            if r.status == 200:
                data = await r.json()
                items = data if isinstance(data, list) else data.get("articles", [])
                if items:
                    print(f"   ✅ Dapet {len(items)} berita. Contoh: {items[0].get('title', items[0].get('name', 'No title'))[:80]}")
                else:
                    print(f"   ⚠️  Response: {str(data)[:200]}")
            else:
                print(f"   ❌ Gagal. Response: {(await r.text())[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")

async def test_currency(session):
    print("\n💱 Tes Kurs (Frankfurter)...")
    try:
        async with session.get("https://api.frankfurter.app/latest?from=USD&to=IDR", timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                rate = data["rates"].get("IDR")
                print(f"   ✅ 1 USD = {rate} IDR (update: {data['date']})")
            else:
                print(f"   ❌ HTTP {r.status}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def test_ip(session):
    print("\n🌍 Tes IP Info (ip-api)...")
    try:
        async with session.get("http://ip-api.com/json/8.8.8.8?fields=status,country,city,isp,query", timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                if data.get("status") == "success":
                    print(f"   ✅ {data['query']} -> {data['city']}, {data['country']} ({data['isp']})")
                else:
                    print(f"   ❌ Status: {data.get('status')}")
            else:
                print(f"   ❌ HTTP {r.status}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def main():
    print("🚀 Memulai tes 5 API Keyless...\n")
    print("=" * 60)
    async with aiohttp.ClientSession() as session:
        await test_weather(session)
        await test_dictionary(session)
        await test_news(session)
        await test_currency(session)
        await test_ip(session)
    print("\n" + "=" * 60)
    print("✅ Selesai!")

if __name__ == "__main__":
    asyncio.run(main())
