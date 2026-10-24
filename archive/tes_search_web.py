import asyncio
from ai_engine import search_multi, scrape_url

async def test_search():
    print("=" * 65)
    print("🧪 TES 1: search_multi (LangSearch prioritas)")
    print("=" * 65)
    query = "harga PS5 terbaru di Indonesia"
    print(f"🔍 Query: {query}\n")
    
    results = await search_multi(query, limit=5)
    if results:
        print(f"\n✅ Total {len(results)} hasil:")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. [{r['source']}] {r['title']}")
            print(f"   🔗 {r['url']}")
            print(f"   📝 {r['snippet'][:100]}...")
    else:
        print("❌ Gak ada hasil.")

async def test_scrape():
    print("\n" + "=" * 65)
    print("🧪 TES 2: scrape_url (Buka isi web)")
    print("=" * 65)
    url = "https://id.wikipedia.org/wiki/PlayStation_5"
    print(f"📄 URL: {url}\n")
    
    data = await scrape_url(url)
    if data:
        print(f"✅ Berhasil buka web!")
        print(f"   📡 Sumber: {data['source']}")
        print(f"   🌐 Judul: {data['title']}")
        print(f"   📏 Panjang: {len(data['content'])} karakter")
        print(f"\n📝 Preview 300 karakter pertama:")
        print(f"   {data['content'][:300]}...")
    else:
        print("❌ Gagal buka web.")

async def main():
    await test_search()
    await test_scrape()

if __name__ == "__main__":
    asyncio.run(main())
