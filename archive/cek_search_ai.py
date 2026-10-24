import os, aiohttp, asyncio, json
from dotenv import load_dotenv

load_dotenv()
E = os.environ

async def probe(session, name, url, headers=None, method="GET", payload=None):
    """Fungsi probe generic"""
    try:
        if method == "GET":
            async with session.get(url, headers=headers, timeout=10) as r:
                text = (await r.text())[:200].replace("\n", " ")
                return f"{name} | HTTP {r.status} | {text}"
        else:
            async with session.post(url, headers=headers, json=payload, timeout=10) as r:
                text = (await r.text())[:200].replace("\n", " ")
                return f"{name} | HTTP {r.status} | {text}"
    except Exception as e:
        return f"{name} | ERROR | {e}"

async def main():
    async with aiohttp.ClientSession() as s:
        tasks = []

        # ==== SERPER (Google Search) ====
        tasks.append(probe(s, "Serper /models", "https://google.serper.dev/models", 
                          {"X-API-KEY": E.get("SERPER_API_KEY")}))
        tasks.append(probe(s, "Serper /ai", "https://google.serper.dev/ai", 
                          {"X-API-KEY": E.get("SERPER_API_KEY"), "Content-Type": "application/json"}, 
                          "POST", {"q": "Halo"}))

        # ==== LANGSARCH ====
        tasks.append(probe(s, "LangSearch /models", "https://api.langsearch.com/v1/models", 
                          {"Authorization": f"Bearer {E.get('LANGSEARCH_API_KEY')}"}))
        tasks.append(probe(s, "LangSearch /chat", "https://api.langsearch.com/v1/chat/completions", 
                          {"Authorization": f"Bearer {E.get('LANGSEARCH_API_KEY')}", "Content-Type": "application/json"}, 
                          "POST", {"model": "gpt-4o-mini", "messages": [{"role":"user","content":"Hi"}]}))

        # ==== EXA ====
        tasks.append(probe(s, "Exa /models", "https://api.exa.ai/models", 
                          {"x-api-key": E.get("EXA_API_KEY")}))
        tasks.append(probe(s, "Exa /answer", "https://api.exa.ai/answer", 
                          {"x-api-key": E.get("EXA_API_KEY"), "Content-Type": "application/json"}, 
                          "POST", {"query": "What is Discord?"}))

        # ==== JINA ====
        tasks.append(probe(s, "Jina /models", "https://api.jina.ai/v1/models", 
                          {"Authorization": f"Bearer {E.get('JINA_API_KEY')}"}))
        tasks.append(probe(s, "Jina /chat", "https://api.jina.ai/v1/chat/completions", 
                          {"Authorization": f"Bearer {E.get('JINA_API_KEY')}", "Content-Type": "application/json"}, 
                          "POST", {"model": "jina-chat", "messages": [{"role":"user","content":"Hi"}]}))

        # ==== SERPAPI ====
        tasks.append(probe(s, "SerpAPI /account", f"https://serpapi.com/account?api_key={E.get('SERPAPI_KEY')}"))

        # ==== GOOGLE CUSTOM SEARCH ====
        tasks.append(probe(s, "Google CSE", f"https://www.googleapis.com/customsearch/v1?key={E.get('GOOGLE_API_KEY')}&cx={E.get('GOOGLE_CX')}&q=test"))

        # ==== GIPHY ====
        tasks.append(probe(s, "Giphy API", f"https://api.giphy.com/v1/gifs/trending?api_key={E.get('GIPHY_API_KEY')}&limit=1"))

        # ==== PEXELS ====
        tasks.append(probe(s, "Pexels API", "https://api.pexels.com/v1/search?query=test&per_page=1", 
                          {"Authorization": E.get("PEXELS_API_KEY")}))

        # ==== CF WORKERS AI ====
        tasks.append(probe(s, "CF Workers AI", f"https://api.cloudflare.com/client/v4/accounts/{E.get('CF_ACCOUNT_ID')}/ai/models/search",
                          {"Authorization": f"Bearer {E.get('CF_API_TOKEN')}"}))

        # ==== MISTRAL EMBED (mungkin ada chat juga) ====
        # (Skip, udah tau Mistral punya chat)

        results = await asyncio.gather(*tasks)
        for r in results:
            print(r)
            print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())
