import ast
import re

with open("bot.py", "r") as f:
    content = f.read()

# Cari blok dari if p_lower in ["setupverifycartel"... sampai return
pattern = r'(?s)        # --- COMMAND: SETUP VERIFIKASI CÁRTEL \(REACTION ROLE\) ---.*?return\n'

match = re.search(pattern, content)
if not match:
    print("❌ Gagal nemu blok setupverifycartel lama.")
    exit(1)

# Kode baru dengan argumen channel + embed DEWA
new_block = '''        # --- COMMAND: SETUP VERIFIKASI CÁRTEL (REACTION ROLE v2) ---
        if p_lower.startswith(("setupverifycartel", "setupverify", "setup cartel")):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.author.guild_permissions.administrator and message.author.id != message.guild.owner_id:
                return await message.reply("❌ Command ini cuma buat Admin/Owner server.")
                
            # Deteksi channel target (dari mention atau fallback ke channel sekarang)
            target_channel = message.channel
            if message.channel_mentions:
                target_channel = message.channel_mentions[0]
                
            msg = await message.reply(f"⏳ **Mengunci server & menyiapkan panel di {target_channel.mention}...**")
            
            # 1. Cari atau Bikin Role WARGA CJNG
            role_name = "WARGA CJNG"
            cartel_role = discord.utils.get(message.guild.roles, name=role_name)
            if not cartel_role:
                cartel_role = await message.guild.create_role(name=role_name, color=discord.Color.dark_red())
            
            # 2. Lockdown Server
            locked_count = 0
            for channel in message.guild.channels:
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                    # Skip channel target & rules/welcome
                    if channel.id == target_channel.id or "rules" in channel.name.lower() or "welcome" in channel.name.lower():
                        continue
                    try:
                        await channel.set_permissions(message.guild.default_role, read_messages=False)
                        await channel.set_permissions(cartel_role, read_messages=True, send_messages=True)
                        locked_count += 1
                    except: pass
                    
            # 3. Kirim Panel Embed DEWA
            embed = discord.Embed(
                title="🩸 VERIFIKASI CÁRTEL DE JALISCO 🩸",
                description=(
                    "**Selamat datang di markas rahasia.**\\n\\n"
                    "Sebelum lu bisa masuk ke dalam lingkaran kami, lu **wajib** melakukan verifikasi. "
                    "Ini bukan sekadar formalitas, ini adalah **sumpah setia** lu kepada Cártel.\\n\\n"
                    "Silakan klik reaksi **✅** di bawah ini untuk membuka akses penuh ke seluruh markas.\\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                ),
                color=discord.Color.dark_red()
            )
            
            if message.guild.icon:
                embed.set_thumbnail(url=message.guild.icon.url)
                
            embed.set_image(url="https://i.imgur.com/8Q5y5eE.jpeg")
            
            embed.add_field(
                name="🛡️ KEUNTUNGAN JADI WARGA",
                value=(
                    "> 🚪 Akses ke **seluruh channel** rahasia.\\n"
                    "> 💬 Bisa ngobrol & mabar bareng member lain.\\n"
                    "> 📢 Dapet info event & giveaway eksklusif.\\n"
                    "> 🎭 Dapet role khusus **WARGA CJNG** (merah darah)."
                ),
                inline=False
            )
            
            embed.add_field(
                name="📜 ATURAN MARKAS (Baca Dulu!)",
                value=(
                    "> ❌ Dilarang **Toxic, SARA, Doxxing**.\\n"
                    "> ❌ Dilarang **Spam / Scam / Phishing**.\\n"
                    "> ❌ Dilarang promosi **Judi & Crypto Bodong**.\\n"
                    "> ⚠️ Sistem AI 24 jam memantau. **Pelanggaran = Mute/Ban.**"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⚠️ PERINGATAN KERAS",
                value=(
                    "> Jika lu mencabut reaksi ✅ ini, sistem akan **otomatis mencabut akses** lu ke semua channel.\\n"
                    "> Jangan coba-coba membuat onar di markas kami."
                ),
                inline=False
            )
            
            embed.set_footer(
                text=f"Cártel de Jalisco | Blood In, Blood Out | {message.guild.name}",
                icon_url=message.guild.icon.url if message.guild.icon else None
            )
            
            panel_msg = await target_channel.send(embed=embed)
            await panel_msg.add_reaction("✅")
            
            await msg.edit(content=f"✅ **Verifikasi Cártel Aktif!**\\n\\n📍 Panel ditaruh di {target_channel.mention}.\\n🔒 **{locked_count}** channel berhasil dikunci.")
            return

'''

new_content = content[:match.start()] + new_block + content[match.end():]

with open("bot.py", "w") as f:
    f.write(new_content)

try:
    ast.parse(new_content)
    print("✅ BERHASIL! Command setupverifycartel sekarang nerima argumen channel + embed DEWA!")
except Exception as e:
    print(f"❌ Syntax Error: {e}")
