import asyncio
from webless import search

async def main():
    print("⏳ Ngetes webless (DuckDuckGo + Mojeek + Bing)...\n")
    try:
        results = await search("berita AI terbaru", limit=5)
        if not results:
            print("⚠️ Gak ada hasil.")
            return
        
        print(f"✅ Dapet {len(results)} hasil:\n")
        for i, hit in enumerate(results, 1):
            print(f"{i}. {hit.title}")
            print(f"   🔗 {hit.url}")
            if hasattr(hit, 'snippet') and hit.snippet:
                print(f"   📝 {hit.snippet[:150]}...")
            print()
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
