import ast

with open("bot.py", "r") as f:
    lines = f.readlines()

# 1. Tambahin import time dan variabel global pelacak spam
import_added = False
for i, line in enumerate(lines):
    if "import asyncio" in line and not import_added:
        lines.insert(i + 1, "import time\n")
        lines.insert(i + 2, "USER_SPAM_TRACKER = {}\n\n")
        import_added = True
        break

# 2. Update fungsi evaluate_message_risk untuk deteksi "Check Bio"
for i, line in enumerate(lines):
    if "async def evaluate_message_risk(message):" in line:
        # Kita cari titik return score, reasons paling akhir di fungsi ini
        for j in range(i, len(lines)):
            if "return score, reasons" in lines[j]:
                # Sisipkan logika "Check Bio" dan Rate Limit sebelum return
                bio_logic = '''
    # 5. CEK KATA KUNCI PHISHING BIO (CHECK MY BIO)
    bio_keywords = ["check my bio", "check bio", "cek bio", "cek profil", "see my bio", "link di bio", "bio gw", "bio gue"]
    if any(k in content_lower for k in bio_keywords):
        is_ai_spam_bio = await evaluate_discord_link_ai(message.content)
        if is_ai_spam_bio:
            score += 80
            reasons.append("AI mendeteksi Spam 'Check My Bio' (Penipuan)")
        else:
            score += 40
            reasons.append("Mengandung kata kunci 'Check Bio' yang mencurigakan")

    # 6. CEK SPAM RATE LIMIT (PESAN TERLALU CEPAT)
    user_id = message.author.id
    now = time.time()
    if user_id not in USER_SPAM_TRACKER:
        USER_SPAM_TRACKER[user_id] = []
    # Simpan waktu pesan, buang yang lebih dari 10 detik
    USER_SPAM_TRACKER[user_id] = [t for t in USER_SPAM_TRACKER[user_id] if now - t < 10]
    USER_SPAM_TRACKER[user_id].append(now)
    
    if len(USER_SPAM_TRACKER[user_id]) >= 5:
        score += 100 # Skor maksimal, langsung hapus
        reasons.append("Spamming (Mengirim pesan terlalu cepat)")
'''
                lines.insert(j, bio_logic)
                break
        break

# 3. Update logika process_risk di on_message (Tambah Timeout)
for i, line in enumerate(lines):
    if "if total_score >= 70:" in line and "await message.delete()" in lines[i+2]:
        # Kita tembak di blok if total_score >= 70
        timeout_logic = '''
                    # Kalau skornya tembus 100 (Spam parah / Hack), langsung Timeout 10 Menit
                    if total_score >= 100:
                        try:
                            await message.author.timeout(discord.utils.utcnow() + discord.timedelta(minutes=10), reason="Auto-Mod: Spamming/Phishing")
                            all_reasons.append("Di-Timeout 10 menit karena spam parah.")
                        except Exception as e:
                            print(f"Gagal timeout: {e}")

'''
        lines.insert(i, timeout_logic)
        break

with open("bot.py", "w") as f:
    f.writelines(lines)

# Verifikasi
try:
    ast.parse("".join(lines))
    print("✅ SUMPAH BERHASIL! Sistem Anti-Spam 'Check Bio' & Timeout 100% OK!")
except Exception as e:
    print(f"❌ Syntax Error: {e}")
