from curl_cffi import requests
import time
import json

print("=====================================")
print("    SILENT SPY V4 (CURL_CFFI BYPASS) ")
print("=====================================")
USER_TOKEN = input("1. Paste USER_TOKEN di sini: ").strip()
WEBHOOK_URL = input("2. Paste WEBHOOK_URL di sini: ").strip()

if not USER_TOKEN or not WEBHOOK_URL:
    print("❌ Token atau Webhook kosong.")
    exit()

headers = {
    "Authorization": USER_TOKEN,
    "Content-Type": "application/json",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
}

def send_webhook(embed):
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]}, impersonate="chrome")
        time.sleep(1.5)
    except:
        pass

def spy_all_servers():
    print("\n🕵️ Mengambil daftar server...")
    r = requests.get("https://discord.com/api/v10/users/@me/guilds", headers=headers, impersonate="chrome")
    
    if r.status_code != 200:
        print(f"❌ Gagal ambil server. (HTTP {r.status_code})")
        print(f"Pesan Error: {r.text[:100]}")
        print("💡 Jika tetap 401, token benar-benar sudah mati. Ambil token baru dan paste langsung ke sini.")
        return

    guilds = r.json()
    print(f"✅ Ditemukan {len(guilds)} server. Mulai scan...\n")

    for g in guilds:
        guild_name = g['name']
        guild_id = g['id']
        print(f"  -> Scanning: {guild_name}")
        
        ch_req = requests.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers, impersonate="chrome")
        channels = ch_req.json() if ch_req.status_code == 200 else []
        
        role_req = requests.get(f"https://discord.com/api/v10/guilds/{guild_id}/roles", headers=headers, impersonate="chrome")
        roles = role_req.json() if role_req.status_code == 200 else []

        ch_text = ""
        if isinstance(channels, list):
            for c in channels:
                icon = "💬" if c['type'] == 0 else "🔊" if c['type'] == 2 else "📁"
                ch_text += f"{icon} {c['name']}\n"
        else:
            ch_text = "❌ Nggak punya akses baca."

        role_text = ""
        if isinstance(roles, list):
            roles = sorted(roles, key=lambda x: x['position'], reverse=True)
            for rl in roles:
                if rl['name'] != "@everyone":
                    role_text += f"🛡️ {rl['name']}\n"
        else:
            role_text = "❌ Nggak punya akses role."

        embed = {
            "title": f"📡 {guild_name}",
            "description": f"ID: `{guild_id}`",
            "color": 3447003,
            "fields": [
                {"name": "📂 Channels", "value": ch_text[:1024] if ch_text else "Kosong", "inline": False},
                {"name": "🛡️ Roles", "value": role_text[:1024] if role_text else "Kosong", "inline": False}
            ]
        }
        
        send_webhook(embed)
        time.sleep(1.5)

    print("\n✅ Scan Selesai! Cek Webhook DC lu.")

if __name__ == "__main__":
    spy_all_servers()
