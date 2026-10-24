import asyncio
from ai_engine import decide_action, research_web, summarize_url

async def test_router(prompt):
    print("\n" + "="*60)
    print(f"📝 Prompt: {prompt}")
    print("-"*60)
    
    # 1. Tes AI Router (keputusan)
    print("🧠 Nanya ke AI Router...")
    action = await decide_action(prompt)
    print(f"✅ Keputusan: {action}")
    
    # 2. Eksekusi sesuai keputusan
    action_type = action.get("action", "chat")
    
    if action_type == "search":
        query = action.get("query", prompt)
        print(f"\n🔍 Eksekusi SEARCH: {query}")
        res = await research_web(query)
        print(f"📄 Hasil:\n{res[:800]}...")
        
    elif action_type == "scrape":
        url = action.get("url")
        print(f"\n📄 Eksekusi SCRAPE: {url}")
        res = await summarize_url(url)
        print(f"📄 Hasil:\n{res[:800]}...")
        
    else:
        print("\n💬 Action CHAT — bot gak akan search, langsung jawab via AI.")

async def main():
    # Daftar prompt buat dites
    prompts = [
        "cek harga PS5 terbaru di Indonesia",
        "rangkum https://id.wikipedia.org/wiki/Kecerdasan_buatan",
        "jelasin apa itu machine learning",
        "siapa pemenang Piala Dunia 2022?",
        "berita terbaru tentang AI hari ini",
    ]
    
    for p in prompts:
        await test_router(p)

if __name__ == "__main__":
    asyncio.run(main())
