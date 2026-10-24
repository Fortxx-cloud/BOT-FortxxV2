import asyncio
from ai_engine import search_multi, research_web

async def main():
    print("=" * 65)
    print("🧪 TES 1: search_multi (5 hasil, multi-source)")
    print("=" * 65)
    
    query = "harga PS5 terbaru di Indonesia"
    print(f"🔍 Query: {query}\n")
    results = await search_multi(query, limit=5)
    
    if results:
        print(f"✅ Dapet {len(results)} hasil:")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. [{r.get('source')}] {r.get('title')}")
            print(f"   🔗 {r.get('url')}")
            print(f"   📝 {r.get('snippet', '')[:100]}...")
    else:
        print("❌ Gak ada hasil.")

    print("\n" + "=" * 65)
    print("🧪 TES 2: research_web (Multi-Source Rangkuman)")
    print("=" * 65)
    
    print(f"\n🔍 Query: {query}\n")
    result = await research_web(query, max_urls=5)
    
    print("\n" + "-" * 65)
    print("📄 HASIL RANGKUMAN:")
    print("-" * 65)
    print(result[:3000])

if __name__ == "__main__":
    asyncio.run(main())
