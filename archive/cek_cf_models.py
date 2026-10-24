import os, aiohttp, asyncio, json
from dotenv import load_dotenv

load_dotenv()
E = os.environ

async def main():
    url = f"https://api.cloudflare.com/client/v4/accounts/{E.get('CF_ACCOUNT_ID')}/ai/models/search"
    headers = {"Authorization": f"Bearer {E.get('CF_API_TOKEN')}"}
    
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers, timeout=15) as r:
            if r.status != 200:
                print(f"❌ Gagal: {r.status}")
                return
            data = await r.json()
            
            text_models = []
            image_models = []
            
            for m in data.get("result", []):
                task = m.get("task", {}).get("name", "")
                if "Text Generation" in task:
                    text_models.append(m.get("name"))
                elif "Text-to-Image" in task:
                    image_models.append(m.get("name"))
            
            print("🧠 MODEL TEXT GENERATION (LLM):")
            for m in text_models: print(f"  - {m}")
            
            print("\n🎨 MODEL TEXT-TO-IMAGE:")
            for m in image_models: print(f"  - {m}")

if __name__ == "__main__":
    asyncio.run(main())
