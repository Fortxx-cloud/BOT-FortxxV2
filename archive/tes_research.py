import asyncio
from ai_engine import research_web

async def main():
    print("🔍 Ngetes Deep Research: 'cuaca hari ini di Jakarta'\n")
    print("=" * 60)
    try:
        result = await research_web("cuaca hari ini di Jakarta")
        print(result)
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
