import asyncio
import os
from dotenv import load_dotenv
from ai_engine import scrape_url

load_dotenv()

async def test_single(url, label):
    print(f"\n{'='*60}")
    print(f"🧪 Tes: {label}")
    print(f"📄 URL: {url}")
    print('='*60)
    data = await scrape_url(url)
    if data:
        print(f"✅ BERHASIL!")
        print(f"   📡 Scraper: {data['source']}")
        print(f"   🌐 Judul: {data['title'][:80]}")
        print(f"   📏 Panjang: {len(data['content'])} karakter")
        print(f"   📝 Preview: {data['content'][:150].replace(chr(10), ' ')}...")
    else:
        print(f"❌ GAGAL buka web.")

async def test_sequential():
    print("\n" + "="*60)
    print("🧪 TES SEQUENTIAL: 3 URL berturut-turut (jeda 2s)")
    print("="*60)
    urls = [
        ("https://id.wikipedia.org/wiki/PlayStation_5", "Wikipedia PS5"),
        ("https://www.kompas.com/tekno", "Kompas Tekno"),
        ("https://www.detik.com/", "Detik.com"),
    ]
    for url, label in urls:
        data = await scrape_url(url)
        if data:
            print(f"✅ {label} -> {data['source']} ({len(data['content'])} char)")
        else:
            print(f"❌ {label} GAGAL")
        await asyncio.sleep(2)  # Jeda 2 detik

async def main():
    print("🔍 CEK API KEY JINA:")
    jina_key = os.getenv("JINA_API_KEY")
    if jina_key:
        print(f"   ✅ Ada (length: {len(jina_key)} char)")
    else:
        print(f"   ⚠️ TIDAK ADA di .env! Mode keyless bakal kena limit.")
    
    await test_single("https://id.wikipedia.org/wiki/PlayStation_5", "Single - Wikipedia PS5")
    await test_sequential()

if __name__ == "__main__":
    asyncio.run(main())
