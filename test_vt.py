import os
import asyncio
import aiohttp
import base64
from dotenv import load_dotenv

load_dotenv(".env")

async def scan_url_virustotal(url):
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key:
        print("❌ ERROR: VIRUSTOTAL_API_KEY tidak ditemukan di .env")
        return
        
    print(f"🔍 Mengirim URL ke VirusTotal: {url}")
    
    # Encode URL ke base64 (wajib untuk endpoint /urls/{id})
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    headers = {"x-apikey": api_key, "accept": "application/json"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers) as r:
            if r.status == 200:
                data = await r.json()
                stats = data['data']['attributes']['last_analysis_stats']
                malicious = stats.get('malicious', 0)
                suspicious = stats.get('suspicious', 0)
                
                print("\n=== HASIL SCAN ===")
                print(f"🦠 Malicious (Virus/Phising): {malicious} engine")
                print(f"⚠️ Suspicious (Mencurigakan): {suspicious} engine")
                
                if malicious > 0 or suspicious > 0:
                    print("🚨 STATUS: BAHAYA! Link ini terdeteksi berbahaya.")
                else:
                    print("✅ STATUS: AMAN.")
                    
            elif r.status == 404:
                print("\n⏳ Link belum ada di database VirusTotal. Sedang mengirim untuk dianalisis...")
                async with session.post("https://www.virustotal.com/api/v3/urls", headers={"x-apikey": api_key, "accept": "application/json"}, data={"url": url}) as post_r:
                    if post_r.status == 200:
                        print("✅ Berhasil dikirim! Tunggu 1-2 menit, lalu jalankan script ini lagi buat liat hasilnya.")
                    else:
                        print(f"❌ Gagal mengirim URL. HTTP Status: {post_r.status}")
            else:
                print(f"❌ Gagal mengambil data. HTTP Status: {r.status}")

async def main():
    # URL Test Malware Resmi dari Google (Aman, cuma buat ngetes API)
    test_url = "http://testsafebrowsing.appspot.com/apiv4/ANY_PLATFORM/MALWARE/URL/"
    await scan_url_virustotal(test_url)

if __name__ == "__main__":
    asyncio.run(main())
