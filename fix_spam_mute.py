import ast
import re

with open("bot.py", "r") as f:
    content = f.read()

# Cari blok SPAM TEKS dari awal sampai akhir
start_marker = "        # 1. SPAM TEKS (Pinter & Cuek sama pesan pendek)"
end_marker = '                    TEXT_SPAM_TRACKER[user_id] = {"msg": msg_content, "warns": 0}'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print("❌ Gagal nemu blok Spam Teks lama.")
    exit(1)

before = content[:start_idx]
after = content[end_idx + len(end_marker):]

# KODE BARU: GALAK & ANTI BYPASS ADMIN
new_spam = '''        # 1. SPAM TEKS (Sangat Galak)
        # Hapus syarat 'not is_admin' biar Admin juga kena mute
        if not is_command and message.content: 
            user_id = message.author.id
            msg_content = message.content.strip().lower()
            
            import time
            now = time.time()
            
            if user_id not in TEXT_SPAM_TRACKER:
                TEXT_SPAM_TRACKER[user_id] = {"msg": msg_content, "warns": 1, "time": now}
            else:
                data = TEXT_SPAM_TRACKER[user_id]
                # Kalau pesannya sama dan dalam waktu < 10 detik
                if msg_content == data["msg"] and (now - data["time"]) < 10:
                    data["warns"] += 1
                    data["time"] = now
                    
                    # Warning di pesan ke-3
                    if data["warns"] == 3:
                        try: await message.channel.send(f"⚠️ {message.author.mention}, berhenti spam! Ini peringatan terakhir sebelum lu di-Mute.")
                        except: pass
                        
                    # MUTE di pesan ke-5
                    elif data["warns"] >= 5:
                        try:
                            await message.delete()
                            # Timeout 28 Hari
                            await message.author.timeout(discord.utils.utcnow() + discord.timedelta(days=28), reason="Auto-Mod: Spam Teks")
                            embed = discord.Embed(title="🚨 SPAMMER DIBUNGKAM! 🚨", description=f"{message.author.mention} di-Mute 80 Tahun karena spam teks berulang.", color=discord.Color.dark_red())
                            await message.channel.send(embed=embed)
                            print(f"✅ [ANTI-SPAM] Berhasil mute {message.author.name} karena spam.")
                            data["warns"] = 0
                            data["msg"] = ""
                        except Exception as e:
                            # KALAU GAGAL MUTE, PRINT DI TERMINAL BIAR LU TAU
                            print(f"❌ [ANTI-SPAM] GAGAL MUTE {message.author.name}! Alasan: {e}")
                            try: await message.channel.send(f"⚠️ Sistem mendeteksi spam, TAPI bot gagal nge-mute (Role bot lu di bawah role dia).")
                            except: pass
                else:
                    # Reset tracker kalau pesan beda atau jeda > 10 detik
                    TEXT_SPAM_TRACKER[user_id] = {"msg": msg_content, "warns": 1, "time": now}'''

new_content = before + new_spam + after

with open("bot.py", "w") as f:
    f.write(new_content)

try:
    ast.parse(new_content)
    print("✅ BERHASIL! Sistem Anti-Spam diganti (5x Spam = Mute, Admin juga kena).")
except Exception as e:
    print(f"❌ Syntax Error: {e}")
