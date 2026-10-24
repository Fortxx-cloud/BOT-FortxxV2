import re, shutil, py_compile, sys

shutil.copy("ai_engine.py", "ai_engine.py.multisearch.bak")
print("✅ Backup: ai_engine.py.multisearch.bak")

with open("ai_engine.py") as f:
    c = f.read()

# Cari fungsi search_internet lama dan ganti dengan versi Multi-Search
new_search_code = '''
# === MULTI-SEARCH FALLBACK (EXA -> SERPER -> LANGSEARCH -> SERPAPI) ===
async def search_internet(query):
    # 1. Coba Exa AI
    exa_key = os.getenv("EXA_API_KEY")
    if exa_key:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.exa.ai/search", 
                                        headers={"x-api-key": exa_key, "Content-Type": "application/json"},
                                        json={"query": query, "numResults": 3}, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        res = data.get("results", [])
                        if res:
                            txt = "🌐 **Hasil Pencarian (Exa):**\\n"
                            for i in res: txt += f"- **{i.get('title')}**\\n  {i.get('url')}\\n  {i.get('text')[:150]}...\\n\\n"
                            return txt
                    elif r.status in [429, 402, 403]:
                        print("⚠️ [SEARCH] Exa limit. Pindah ke Serper...")
        except: pass

    # 2. Coba Serper (Google)
    serper_key = os.getenv("SERPER_API_KEY")
    if serper_key:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://google.serper.dev/search", 
                                        headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                                        json={"q": query, "num": 3}, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        res = data.get("organic", [])
                        if res:
                            txt = "🌐 **Hasil Pencarian (Google/Serper):**\\n"
                            for i in res: txt += f"- **{i.get('title')}**\\n  {i.get('link')}\\n  {i.get('snippet')[:150]}...\\n\\n"
                            return txt
                    elif r.status in [429, 402, 403]:
                        print("⚠️ [SEARCH] Serper limit. Pindah ke LangSearch...")
        except: pass

    # 3. Coba LangSearch
    lang_key = os.getenv("LANGSEARCH_API_KEY")
    if lang_key:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.langsearch.com/v1/web-search", 
                                        headers={"Authorization": f"Bearer {lang_key}", "Content-Type": "application/json"},
                                        json={"query": query, "count": 3}, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        # Format LangSearch agak beda
                        pages = data.get("data", {}).get("webPages", {}).get("value", [])
                        if pages:
                            txt = "🌐 **Hasil Pencarian (LangSearch):**\\n"
                            for i in pages: txt += f"- **{i.get('name')}**\\n  {i.get('url')}\\n  {i.get('snippet')[:150]}...\\n\\n"
                            return txt
                    elif r.status in [429, 402, 403]:
                        print("⚠️ [SEARCH] LangSearch limit. Pindah ke SerpApi...")
        except: pass
        
    # 4. Coba SerpApi
    serpapi_key = os.getenv("SERPAPI_KEY")
    if serpapi_key:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://serpapi.com/search?api_key={serpapi_key}&q={query}&engine=google"
                async with session.get(url, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        res = data.get("organic_results", [])
                        if res:
                            txt = "🌐 **Hasil Pencarian (SerpApi):**\\n"
                            for i in res: txt += f"- **{i.get('title')}**\\n  {i.get('link')}\\n  {i.get('snippet')[:150]}...\\n\\n"
                            return txt
        except: pass

    return "❌ Semua API Search (Exa, Serper, LangSearch, SerpApi) sedang limit/error."
'''

# Replace fungsi search_internet lama
pattern = r'async def search_internet\(query\):.*?(?=# === 3\. MAP PROVIDER)'
if re.search(pattern, c, re.DOTALL):
    c = re.sub(pattern, new_search_code + "\n\n", c, flags=re.DOTALL)
    with open("ai_engine.py", "w") as f:
        f.write(c)
    print("✅ Multi-Search Fallback berhasil ditambahkan ke ai_engine.py!")
else:
    print("⚠️ Fungsi search_internet lama gak ketemu. Cek manual ya.")

try:
    py_compile.compile("ai_engine.py", doraise=True)
    print("✅ Syntax OK!")
except py_compile.PyCompileError as e:
    print(f"❌ Syntax ERROR:\\n{e}")
    shutil.copy("ai_engine.py.multisearch.bak", "ai_engine.py")
    sys.exit(1)
