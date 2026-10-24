import ast
import re

with open("bot.py", "r") as f:
    content = f.read()

# ==========================================
# 1. BENERIN FUNGSI check_discord_invite (Lebih Toleran)
# ==========================================
old_func = '''async def check_discord_invite(url, guild, message_content=""):
    match = re.search(r'discord\\.gg/([a-zA-Z0-9\\-]+)', url)
    if not match: return False
    invite_code = match.group(1)
    try:
        invite = await bot.fetch_invite(invite_code)
        # ... logika lama ...
        return False
    except:
        return True  # <-- INI MASALAHNYA: Link invalid langsung dianggap SCAM'''

new_func = '''async def check_discord_invite(url, guild, message_content=""):
    match = re.search(r'discord\\.gg/([a-zA-Z0-9\\-]+)', url)
    if not match: return False
    invite_code = match.group(1)
    try:
        invite = await bot.fetch_invite(invite_code)
        # Kalo invite valid, cek nama server & konten
        if invite.guild and invite.guild.id == guild.id: return False
        scam_keywords = ["nitro", "free", "gift", "crypto", "bitcoin", "investment", "profit", "steam", "airdrop", "giveaway"]
        if any(k in message_content.lower() for k in scam_keywords): return True
        if invite.guild and any(k in invite.guild.name.lower() for k in scam_keywords): return True
        return False
    except Exception:
        # KALO LINK INVALID/EXPIRED ATAU BOT GAK ADA DI SERVER TUJUAN:
        # JANGAN LANGSUNG ANGGAP SCAM. Cek dulu apakah ada keyword scam di teks.
        scam_keywords = ["nitro", "free", "gift", "crypto", "bitcoin", "investment", "profit", "steam", "airdrop", "giveaway", "hack", "cheat", "judi", "slot", "gacor", "maxwin"]
        if any(k in message_content.lower() for k in scam_keywords):
            return True  # Kalo ada keyword scam, baru hapus
        return False  # Kalo link biasa aja, biarin (mungkin cuma expired)'''

if old_func in content:
    content = content.replace(old_func, new_func, 1)
    print("✅ Fungsi check_discord_invite di-upgrade (Lebih toleran ke link normal).")
else:
    print("⚠️ Pattern check_discord_invite tidak ketemu.")

# ==========================================
# 2. TURUNIN SKOR LINK DISCORD BIAR GAK OTOMATIS HAPUS
# ==========================================
old_risk = '''        # E. CEK INVITE DISCORD (AI + VALIDITAS)
        if "discord.gg" in url or "discord.com/invite" in url:
            try:
                if await evaluate_discord_link_ai(message.content):
                    score += 80
                    reasons.append("AI mendeteksi SPAM Link Discord")
                    continue
                if await check_discord_invite(url, message.guild, content_lower):
                    score += 60
                    reasons.append("Invite Discord mencurigakan")
            except:
                pass'''

new_risk = '''        # E. CEK INVITE DISCORD (AI + VALIDITAS)
        if "discord.gg" in url or "discord.com/invite" in url:
            try:
                # Cek AI dulu (Apakah ini spam berdasarkan konteks?)
                if await evaluate_discord_link_ai(message.content):
                    score += 80
                    reasons.append("AI mendeteksi SPAM Link Discord")
                    continue
                    
                # Cek validitas invite (Sekarang lebih toleran)
                is_bad_invite = await check_discord_invite(url, message.guild, content_lower)
                if is_bad_invite:
                    # Kalo beneran scam/berbahaya, skor tinggi
                    score += 70
                    reasons.append("Invite Discord terdeteksi SCAM (Ada keyword bahaya)")
                else:
                    # Kalo cuma link expired atau bot gak kenal, skor rendah aja
                    # Biar gak otomatis kehapus, minimal dapet warning
                    reasons.append("Link Discord terdeteksi (tapi belum tentu scam)")
            except Exception as e:
                print(f"⚠️ Error cek invite: {e}")

        # Kalo cuma link shortener TANPA indikasi scam lain, skornya jangan tinggi
        if any(short in url for short in ["bit.ly", "tinyurl.com", "cutt.ly", "t.co", "in.run"]):
            # Turunin skor shortener kalo gak ada keyword bahaya
            if not any(k in content_lower for k in ["judi", "slot", "gacor", "crypto", "phishing", "scam", "nitro"]):
                score += 20  # Cuma warning ringan
                reasons.append("Link Shortener (Belum terdeteksi bahaya)")
            else:
                score += 60  # Kalo ada keyword bahaya, baru tinggi
                reasons.append("Link Shortener + Kata kunci bahaya")'''

if old_risk in content:
    content = content.replace(old_risk, new_risk, 1)
    print("✅ Skor Risk Scoring di-upgrade (Link normal gak bakal kehapus).")
else:
    print("⚠️ Pattern risk scoring tidak ketemu.")

with open("bot.py", "w") as f:
    f.write(content)

try:
    ast.parse(content)
    print("✅ Syntax bot.py 100% OK!")
except Exception as e:
    print(f"❌ Syntax Error: {e}")
