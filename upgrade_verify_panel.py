import ast

with open("bot.py", "r") as f:
    content = f.read()

# Cari blok lama pembuatan embed verifikasi
old_embed = '''            # 3. Kirim Panel Embed
            embed = discord.Embed(
                title="🩸 VERIFIKASI CÁRTEL DE JALISCO",
                description="Klik reaksi ✅ di bawah ini untuk membuka akses ke seluruh channel server.\\n\\n*Note: Jika reaksi dihapus, akses akan dicabut otomatis.*",
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Cártel de Jalisco | Blood In, Blood Out")
            
            panel_msg = await message.channel.send(embed=embed)
            await panel_msg.add_reaction("✅")'''

new_embed = '''            # 3. Kirim Panel Embed (Versi Dewa)
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
            
            # Thumbnail: Logo Server
            if message.guild.icon:
                embed.set_thumbnail(url=message.guild.icon.url)
                
            # Banner gambar (kalo ada asset dari internet)
            embed.set_image(url="https://i.imgur.com/8Q5y5eE.jpeg")
            
            embed.add_field(
                name="🛡️ **KEUNTUNGAN JADI WARGA**",
                value=(
                    "> 🚪 Akses ke **seluruh channel** rahasia.\\n"
                    "> 💬 Bisa ngobrol & mabar bareng member lain.\\n"
                    "> 📢 Dapet info event & giveaway eksklusif.\\n"
                    "> 🎭 Dapet role khusus **WARGA CJNG** (merah darah)."
                ),
                inline=False
            )
            
            embed.add_field(
                name="📜 **ATURAN MARKAS** (Baca Dulu!)",
                value=(
                    "> ❌ Dilarang **Toxic, SARA, Doxxing**.\\n"
                    "> ❌ Dilarang **Spam / Scam / Phishing**.\\n"
                    "> ❌ Dilarang promosi **Judi & Crypto Bodong**.\\n"
                    "> ⚠️ Sistem AI 24 jam memantau. **Pelanggaran = Mute/Ban.**"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⚠️ **PERINGATAN KERAS**",
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
            
            panel_msg = await message.channel.send(embed=embed)
            await panel_msg.add_reaction("✅")'''

if old_embed in content:
    content = content.replace(old_embed, new_embed, 1)
    print("✅ Panel verifikasi berhasil di-upgrade jadi versi DEWA (dengan banner & detail)!")
else:
    print("⚠️ Gagal nemu blok embed verifikasi lama. Coba cek manual.")

with open("bot.py", "w") as f:
    f.write(content)

try:
    ast.parse(content)
    print("✅ Syntax bot.py 100% OK!")
except Exception as e:
    print(f"❌ Syntax Error: {e}")
