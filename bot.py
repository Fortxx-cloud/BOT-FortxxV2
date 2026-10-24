import urllib.parse
import base64
import os

async def expand_url(url):
    """Buka link pendek buat dapet URL aslinya."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True, timeout=5) as r:
                return str(r.url)
    except:
        return url

import discord
import aiohttp
from discord.ext import commands
import os
import json
import io
from dotenv import load_dotenv
from ai_engine import (
    execute_task, execute_tool, agent_action, run_agent, check_rate_limit,
    delete_chat_history, get_bot_stats, search_internet, get_weather,
    get_dictionary, get_news, get_currency, get_ip_info, summarize_url,
    research_web, decide_action, NATURAL_SYSTEM, extract_facts_async,
    normalize_text, scan_guild_structure, transcribe_audio,
    extract_text_from_file, get_image_url
)
from keep_alive import keep_alive
import asyncio
import datetime
import time
USER_SPAM_TRACKER = {}
TEXT_SPAM_TRACKER = {}

import re as _re

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Database Link Scam (Local Cache)
PHISHING_DOMAINS = set()

bot = commands.Bot(command_prefix="\x00", intents=intents)


# ==========================================
# FITUR UI: TICKET SYSTEM
# ==========================================
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Tutup Tiket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket_btn")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Tiket akan ditutup dan transkrip dikirim ke mod-logs dalam 3 detik...", ephemeral=True)
        channel = interaction.channel
        
        # Simpan Transkrip
        transcript = ""
        async for msg in channel.history(limit=200, oldest_first=True):
            transcript += f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author.name}: {msg.content}\n"
            
        logs_ch = discord.utils.get(interaction.guild.text_channels, name="🎫・ticket-transcripts")
        if logs_ch:
            embed = discord.Embed(title=f"Transcript Tiket: {channel.name}", description=f"Ditutup oleh {interaction.user.mention}", color=discord.Color.red())
            file = discord.File(io.BytesIO(transcript.encode()), filename=f"{channel.name}-transcript.txt")
            await logs_ch.send(embed=embed, file=file)
            
        await asyncio.sleep(3)
        await channel.delete()

class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Buat Tiket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="create_ticket_btn")
    async def create_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        ch_name = f"tiket-{user.name}".lower()
        
        existing = discord.utils.get(guild.text_channels, name=ch_name)
        if existing:
            return await interaction.response.send_message(f"❌ Lu udah punya tiket yang kebuka: {existing.mention}", ephemeral=True)
            
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        admin_role = discord.utils.get(guild.roles, name="Admin")
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
        ticket_ch = await guild.create_text_channel(ch_name, overwrites=overwrites)
        embed = discord.Embed(title="🎫 Tiket Support", description=f"Halo {user.mention}, tulis keluhan/pertanyaan lu di sini. Admin bakal segera merespon.\n\nKlik tombol **Tutup Tiket** jika masalah sudah selesai.", color=discord.Color.blue())
        await ticket_ch.send(embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"✅ Tiket berhasil dibuat: {ticket_ch.mention}", ephemeral=True)

# ==========================================
# KELAS UI (TOMBOL & MODAL)
# ==========================================

class RolePermissionView(discord.ui.View):
    def __init__(self, role):
        super().__init__(timeout=300)
        self.role = role
        self.page = 0
        self.pending_perms = role.permissions
        self.pages = [
            {"title": "1: Umum & Admin", "perms": {
                "Administrator": "administrator", "Kelola Channel": "manage_channels",
                "Kelola Role": "manage_roles", "Kelola Server": "manage_guild", "Lihat Audit Log": "view_audit_log"
            }},
            {"title": "2: Text & Chat", "perms": {
                "Kirim Pesan": "send_messages", "Baca Riwayat Chat": "read_message_history",
                "Sematkan Link (Embed)": "embed_links", "Lampirkan File": "attach_files", "Hapus Pesan Orang": "manage_messages"
            }},
            {"title": "3: Voice", "perms": {
                "Masuk VC": "connect", "Bicara": "speak", "Share Screen/Video": "stream",
                "Bisukan Member": "mute_members", "Tulikan Member": "deafen_members"
            }},
            {"title": "4: Moderasi", "perms": {
                "Tendang (Kick)": "kick_members", "Blokir (Ban)": "ban_members",
                "Timeout (Mute)": "moderate_members", "Ubah Nickname": "manage_nicknames", "Tag @everyone": "mention_everyone"
            }}
        ]
        self.update_view()

    def get_embed(self):
        embed = discord.Embed(
            title=f"⚙️ Role: {self.role.name}", 
            description="Klik tombol untuk ubah izin.\n🟩 Hijau = Izinkan | ⬜ Abu = Tolak", 
            color=discord.Color.blue()
        )
        embed.set_footer(text=self.pages[self.page]["title"])
        return embed

    def update_view(self):
        self.clear_items()
        current_perms = self.pages[self.page]["perms"]
        
        # Bikin tombol per izin (baris 1 dan 2)
        for i, (label, p_name) in enumerate(current_perms.items()):
            is_on = getattr(self.pending_perms, p_name)
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.success if is_on else discord.ButtonStyle.secondary, row=i//5)
            
            async def cb(inter, p=p_name, b=btn):
                await inter.response.defer() # Anti Timeout
                curr = getattr(self.pending_perms, p)
                self.pending_perms.update(**{p: not curr})
                b.style = discord.ButtonStyle.success if not curr else discord.ButtonStyle.secondary
                await inter.edit_original_response(view=self)
            
            btn.callback = cb
            self.add_item(btn)
        
        # Tombol Navigasi (Baris 3)
        nav_row = 3
        if self.page > 0:
            p_btn = discord.ui.Button(label="⬅️ Sebelumnya", style=discord.ButtonStyle.primary, row=nav_row)
            p_btn.callback = self.prev
            self.add_item(p_btn)
            
        if self.page < len(self.pages) - 1:
            n_btn = discord.ui.Button(label="Selanjutnya ➡️", style=discord.ButtonStyle.primary, row=nav_row)
            n_btn.callback = self.next
            self.add_item(n_btn)
        
        # Tombol Simpan (Baris 4)
        s_btn = discord.ui.Button(label="💾 Simpan Perubahan", style=discord.ButtonStyle.success, row=4)
        s_btn.callback = self.save
        self.add_item(s_btn)

    async def prev(self, i):
        await i.response.defer()
        self.page -= 1
        self.update_view()
        await i.edit_original_response(embed=self.get_embed(), view=self)

    async def next(self, i):
        await i.response.defer()
        self.page += 1
        self.update_view()
        await i.edit_original_response(embed=self.get_embed(), view=self)

    async def save(self, i):
        await i.response.defer()
        try:
            await self.role.edit(permissions=self.pending_perms)
            active_perms = []
            for page in self.pages:
                for label, p_name in page["perms"].items():
                    if getattr(self.pending_perms, p_name):
                        active_perms.append(f"• {label}")
            
            if active_perms:
                msg = f"✅ **Role {self.role.mention} berhasil disimpan!**\n\n**Sekarang role ini bisa:**\n" + "\n".join(active_perms)
            else:
                msg = f"✅ **Role {self.role.mention} berhasil disimpan!**\n\n**Role ini sekarang tidak punya izin khusus.**"
            
            await i.followup.send(msg, ephemeral=True)
        except Exception as e:
            await i.followup.send(f"❌ Gagal menyimpan: {e}", ephemeral=True)

class RoleSelectView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=180)
        valid_roles = [r for r in guild.roles if not r.is_default() and not r.managed and r.position < guild.me.top_role.position][:25]
        opts = [discord.SelectOption(label=r.name, value=str(r.id)) for r in valid_roles] if valid_roles else [discord.SelectOption(label="Tidak ada role", value="none")]
        s = discord.ui.Select(placeholder="Pilih Role...", options=opts)
        s.callback = self.cb
        self.add_item(s)
        
        help_btn = discord.ui.Button(label="❓ Penjelasan Izin", style=discord.ButtonStyle.secondary, row=1)
        help_btn.callback = self.help_cb
        self.add_item(help_btn)

    async def cb(self, i):
        await i.response.defer()
        r = discord.utils.get(i.guild.roles, id=int(i.data["values"][0]))
        v = RolePermissionView(r)
        await i.edit_original_response(embed=v.get_embed(), view=v)

    async def help_cb(self, interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="📖 Panduan Izin Role", description="Ini penjelasan singkat buat tombol-tombol yang bakal lu temuin:", color=discord.Color.gold())
        embed.add_field(name="Halaman 1: Umum & Admin", value="🛡️ **Administrator**: Bypass semua batasan (Role Dewa).\n📁 **Manage Channels**: Bikin, ubah, hapus channel.\n🏷️ **Manage Roles**: Bikin role & atur role orang.\n⚙️ **Manage Server**: Ubah setting server.\n📜 **View Audit Log**: Lihat catatan admin.", inline=False)
        embed.add_field(name="Halaman 2: Text & Chat", value="💬 **Send Messages**: Ngetik chat.\n📖 **Read History**: Baca chat lama.\n🔗 **Embed Links**: Link jadi kotak cantik.\n📎 **Attach Files**: Upload file.\n🗑️ **Manage Messages**: Hapus chat orang.", inline=False)
        embed.add_field(name="Halaman 3: Voice", value="🔊 **Connect**: Masuk VC.\n🎙️ **Speak**: Ngomong.\n🖥️ **Video/Stream**: Share screen.\n🔇 **Mute Members**: Bungkam orang.\n🔕 **Deafen**: Tulikan orang.", inline=False)
        embed.add_field(name="Halaman 4: Moderasi", value="👢 **Kick**: Tendang keluar.\n🔨 **Ban**: Blacklist permanen.\n⏳ **Moderate**: Timeout.\n📝 **Manage Nicknames**: Ubah nama.\n📢 **Mention Everyone**: Tag @everyone.", inline=False)
        embed.set_footer(text="Pesan ini cuma bisa dilihat sama lu.")
        await interaction.followup.send(embed=embed, ephemeral=True)


# === UI CHANNEL BUILDER ===
class ChannelModal(discord.ui.Modal, title="Detail Channel"):
    def __init__(self, category, channel_type, privacy, role_perms):
        super().__init__()
        self.category = category
        self.channel_type = channel_type
        self.privacy = privacy
        self.role_perms = role_perms 
        
        self.name_input = discord.ui.TextInput(label="Nama Channel", placeholder="contoh: info-terbaru", max_length=100)
        self.add_item(self.name_input)
        
        if channel_type in ["text", "forum"]:
            self.topic_input = discord.ui.TextInput(label="Topik (Opsional)", required=False, max_length=1024)
            self.add_item(self.topic_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            name = self.name_input.value.lower().replace(" ", "-").replace("#", "")
            topic = getattr(self, 'topic_input', None)
            topic_val = topic.value if topic else None
            overwrites = {}
            
            if self.privacy == "private":
                overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(view_channel=False)
                
                for role, perms in self.role_perms.items():
                    perm = discord.PermissionOverwrite()
                    
                    # Logika Izin (Bisa lebih dari satu)
                    if "view" in perms or "connect" in perms or "chat" in perms or "speak" in perms or "full" in perms:
                        perm.view_channel = True
                        
                    if self.channel_type == "voice":
                        if "connect" in perms or "full" in perms:
                            perm.connect = True
                        if "speak" in perms or "full" in perms:
                            perm.speak = True
                        if "full" in perms:
                            perm.stream = True
                            perm.mute_members = True
                            perm.deafen_members = True
                    else: # Text / Forum
                        if "chat" in perms or "full" in perms:
                            perm.send_messages = True
                            perm.read_message_history = True
                        if "full" in perms:
                            perm.attach_files = True
                            perm.embed_links = True
                            perm.manage_messages = True
                            perm.mention_everyone = True
                    
                    overwrites[role] = perm
                    
                overwrites[interaction.guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)
            
            if self.channel_type == "voice":
                new_ch = await interaction.guild.create_voice_channel(name=name, category=self.category, overwrites=overwrites)
            elif self.channel_type == "forum":
                new_ch = await interaction.guild.create_forum(name=name, category=self.category, topic=topic_val, overwrites=overwrites)
            else:
                new_ch = await interaction.guild.create_text_channel(name=name, category=self.category, topic=topic_val, overwrites=overwrites)
                
            await interaction.followup.send(f"✅ **{self.channel_type.capitalize()}** {new_ch.mention} berhasil dibuat!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Gagal: {e}", ephemeral=True)

class RoleAccessConfigView(discord.ui.View):
    def __init__(self, selected_roles, category, channel_type, parent_view):
        super().__init__(timeout=300)
        self.selected_roles = selected_roles
        self.category = category
        self.channel_type = channel_type
        self.parent_view = parent_view
        self.current_role = selected_roles[0] if selected_roles else None
        
        # Default permissions (bisa nampung banyak akses)
        default_perms = {"view", "connect"} if channel_type == "voice" else {"view", "chat"}
        self.role_perms = {r: set(default_perms) for r in selected_roles}
        
        self.build_ui()

    def build_ui(self):
        self.clear_items()
        
        # 1. Dropdown Pilih Role
        if self.selected_roles:
            opts = [discord.SelectOption(label=r.name, value=str(r.id), default=(r == self.current_role)) for r in self.selected_roles]
            s = discord.ui.Select(placeholder="Pilih Role yang mau diatur...", options=opts, row=0)
            s.callback = self.select_role
            self.add_item(s)

        # 2. Tombol Hak Akses (Bisa ditekan semua)
        if self.current_role:
            curr_perms = self.role_perms[self.current_role]
            
            if self.channel_type == "voice":
                btn_connect = discord.ui.Button(label="🔊 Bisa Masuk", style=discord.ButtonStyle.success if "connect" in curr_perms else discord.ButtonStyle.secondary, row=1)
                btn_speak = discord.ui.Button(label="🎙️ Bisa Ngomong", style=discord.ButtonStyle.success if "speak" in curr_perms else discord.ButtonStyle.secondary, row=1)
                btn_full = discord.ui.Button(label="🛠️ Full Akses", style=discord.ButtonStyle.success if "full" in curr_perms else discord.ButtonStyle.secondary, row=2)
                
                btn_connect.callback = lambda i: self.toggle_perm(i, "connect")
                btn_speak.callback = lambda i: self.toggle_perm(i, "speak")
                btn_full.callback = lambda i: self.toggle_perm(i, "full")
                
                self.add_item(btn_connect)
                self.add_item(btn_speak)
                self.add_item(btn_full)
            else:
                btn_chat = discord.ui.Button(label="💬 Bisa Chat", style=discord.ButtonStyle.success if "chat" in curr_perms else discord.ButtonStyle.secondary, row=1)
                btn_full = discord.ui.Button(label="🛠️ Full Akses", style=discord.ButtonStyle.success if "full" in curr_perms else discord.ButtonStyle.secondary, row=1)
                
                btn_chat.callback = lambda i: self.toggle_perm(i, "chat")
                btn_full.callback = lambda i: self.toggle_perm(i, "full")
                
                self.add_item(btn_chat)
                self.add_item(btn_full)

        # 3. Tombol Selesai
        btn_done = discord.ui.Button(label="✅ Lanjut & Buat Channel", style=discord.ButtonStyle.primary, row=3)
        btn_done.callback = self.finish_config
        self.add_item(btn_done)

    def get_embed(self):
        embed = discord.Embed(
            title=f"⚙️ Pengaturan Hak Akses ({self.channel_type.upper()})", 
            description="Klik tombol untuk **Menyalakan (Hijau)** atau **Mematikan (Abu-abu)** hak akses role.\nBisa pilih lebih dari satu (Misal: Masuk & Ngomong).", 
            color=discord.Color.orange()
        )
        for r in self.selected_roles:
            perms = self.role_perms[r]
            perms_list = []
            if "full" in perms:
                perms_list.append("🛠️ Full Akses")
            else:
                if "connect" in perms or "chat" in perms or "speak" in perms or "view" in perms:
                    perms_list.append("👁️ Liat")
                if "connect" in perms: perms_list.append("🔊 Masuk")
                if "speak" in perms: perms_list.append("🎙️ Ngomong")
                if "chat" in perms: perms_list.append("💬 Chat")
            
            val_str = ", ".join(perms_list) if perms_list else "❌ Tidak ada akses"
            embed.add_field(name=f"🛡️ {r.name}", value=val_str, inline=False)
        return embed

    async def select_role(self, i):
        try:
            await i.response.defer()
            self.current_role = discord.utils.get(self.selected_roles, id=int(i.data["values"][0]))
            self.build_ui()
            await i.edit_original_response(embed=self.get_embed(), view=self)
        except discord.errors.NotFound: pass

    async def toggle_perm(self, i, perm_name):
        try:
            await i.response.defer()
            if self.current_role:
                curr = self.role_perms[self.current_role]
                
                if perm_name == "full":
                    if "full" in curr:
                        curr.remove("full")
                    else:
                        curr.add("full")
                else:
                    if perm_name in curr:
                        curr.remove(perm_name)
                    else:
                        curr.add(perm_name)
                        
                # Logika pintar: Ngomong wajib Masuk, Chat wajib Liat
                if "speak" in curr:
                    curr.add("connect")
                if "chat" in curr:
                    curr.add("view")
                    
            self.build_ui()
            await i.edit_original_response(embed=self.get_embed(), view=self)
        except discord.errors.NotFound: pass

    async def finish_config(self, i):
        # HAPUS defer(), langsung panggil modal
        try:
            await i.response.send_modal(ChannelModal(self.category, self.channel_type, "private", self.role_perms))
        except discord.errors.NotFound: pass

class ChannelBuilderView(discord.ui.View):
    def __init__(self, categories, roles):
        super().__init__(timeout=300)
        self.categories = categories
        self.roles = roles
        self.category = None
        self.channel_type = "text"
        self.privacy = "public"
        self.selected_roles = []
        self.update_view()

    def update_view(self):
        self.clear_items()
        
        cat_opts = [discord.SelectOption(label="Tanpa Kategori", value="none", emoji="📁", default=(self.category is None))]
        for c in self.categories:
            cat_opts.append(discord.SelectOption(label=c.name, value=str(c.id), default=(self.category is not None and str(self.category.id)==str(c.id))))
        s1 = discord.ui.Select(placeholder="1️⃣ Kategori", options=cat_opts[:25], row=0)
        s1.callback = self.cat_cb
        self.add_item(s1)

        type_opts = [
            discord.SelectOption(label="Text Channel", value="text", emoji="💬", default=(self.channel_type=="text")),
            discord.SelectOption(label="Voice Channel", value="voice", emoji="🔊", default=(self.channel_type=="voice")),
            discord.SelectOption(label="Forum Channel", value="forum", emoji="📝", default=(self.channel_type=="forum"))
        ]
        s2 = discord.ui.Select(placeholder="2️⃣ Tipe Channel", options=type_opts, row=1)
        s2.callback = self.type_cb
        self.add_item(s2)

        priv_opts = [
            discord.SelectOption(label="Public (Semua bisa lihat)", value="public", emoji="🌐", default=(self.privacy=="public")),
            discord.SelectOption(label="Private (Role Tertentu)", value="private", emoji="🔒", default=(self.privacy=="private"))
        ]
        s3 = discord.ui.Select(placeholder="3️⃣ Privasi", options=priv_opts, row=2)
        s3.callback = self.priv_cb
        self.add_item(s3)

        if self.privacy == "private":
            role_opts = [discord.SelectOption(label=r.name, value=str(r.id), default=(r in self.selected_roles)) for r in self.roles[:25] if not r.is_default()]
            if role_opts:
                s4 = discord.ui.Select(placeholder="4️⃣ Pilih Role yang diizinkan", options=role_opts, min_values=1, max_values=len(role_opts), row=3)
                s4.callback = self.role_cb
                self.add_item(s4)

        btn = discord.ui.Button(label="Buat Channel", style=discord.ButtonStyle.success, emoji="✅", row=4)
        btn.callback = self.submit_cb
        self.add_item(btn)

    # ANTI TIMEOUT JUGA
    async def cat_cb(self, i):
        try:
            await i.response.defer()
            val = i.data["values"][0]
            self.category = None if val == "none" else discord.utils.get(i.guild.categories, id=int(val))
            self.update_view()
            await i.edit_original_response(view=self)
        except discord.errors.NotFound: pass

    async def type_cb(self, i):
        try:
            await i.response.defer()
            self.channel_type = i.data["values"][0]
            self.update_view()
            await i.edit_original_response(view=self)
        except discord.errors.NotFound: pass

    async def priv_cb(self, i):
        try:
            await i.response.defer()
            self.privacy = i.data["values"][0]
            self.update_view()
            await i.edit_original_response(view=self)
        except discord.errors.NotFound: pass

    async def role_cb(self, i):
        try:
            await i.response.defer()
            self.selected_roles = [discord.utils.get(i.guild.roles, id=int(v)) for v in i.data["values"]]
            self.update_view()
            await i.edit_original_response(view=self)
        except discord.errors.NotFound: pass

    async def submit_cb(self, i):
        try:
            if self.privacy == "private" and self.selected_roles:
                await i.response.defer() # Defer aman karena pake edit_original_response
                config_view = RoleAccessConfigView(self.selected_roles, self.category, self.channel_type, self)
                await i.edit_original_response(embed=config_view.get_embed(), view=config_view)
            else:
                # Jangan pakai defer(), langsung send_modal
                await i.response.send_modal(ChannelModal(self.category, self.channel_type, "public", {}))
        except discord.errors.NotFound: pass


# === UI KATEGORI MANAGER ===
class CategoryNameModal(discord.ui.Modal, title="Ubah Nama Kategori"):
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.name_input = discord.ui.TextInput(label="Nama Kategori Baru", default=category.name, max_length=100)
        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            await self.category.edit(name=self.name_input.value)
            await interaction.followup.send(f"✅ Kategori berhasil diubah menjadi **{self.name_input.value}**.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Gagal: {e}", ephemeral=True)

class CategoryConfirmDeleteView(discord.ui.View):
    def __init__(self, category):
        super().__init__(timeout=60)
        self.category = category

    @discord.ui.button(label="Ya, Hapus Semua", style=discord.ButtonStyle.danger)
    async def confirm(self, i, button):
        await i.response.defer()
        try:
            await self.category.delete()
            await i.edit_original_response(content="✅ Kategori dan semua channel di dalamnya berhasil dihapus.", view=None, embed=None)
        except Exception as e:
            await i.edit_original_response(content=f"❌ Gagal: {e}", view=None, embed=None)

    @discord.ui.button(label="Batal", style=discord.ButtonStyle.secondary)
    async def cancel(self, i, button):
        await i.response.defer()
        await i.edit_original_response(content="❌ Penghapusan dibatalkan.", view=None, embed=None)

class CategoryManagerView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=180)
        self.guild = guild
        self.categories = sorted([c for c in guild.categories], key=lambda x: x.position)
        self.current_cat = self.categories[0] if self.categories else None
        self.build_ui()

    def build_ui(self):
        self.clear_items()
        
        if not self.categories:
            btn_create = discord.ui.Button(label="Buat Kategori Baru", style=discord.ButtonStyle.success)
            btn_create.callback = self.create_cat
            self.add_item(btn_create)
            return

        # 1. Dropdown Pilih Kategori
        opts = [discord.SelectOption(label=c.name, value=str(c.id), default=(c == self.current_cat)) for c in self.categories[:25]]
        s_cat = discord.ui.Select(placeholder="Pilih Kategori...", options=opts, row=0)
        s_cat.callback = self.select_cat
        self.add_item(s_cat)

        # 2. Dropdown Pilih Posisi Tujuan (BARU: Pengganti Tombol Geser)
        pos_opts = []
        for i, cat in enumerate(self.categories[:25]):
            pos_opts.append(discord.SelectOption(
                label=f"Posisi {i+1}: {cat.name}", 
                value=str(i), 
                default=(i == self.current_cat.position)
            ))
        s_pos = discord.ui.Select(placeholder="⬇️ Pindahkan ke Posisi...", options=pos_opts, row=1)
        s_pos.callback = self.move_to_pos
        self.add_item(s_pos)

        # 3. Tombol Aksi (Tanpa Naik/Turun lagi)
        btn_rename = discord.ui.Button(label="Ubah Nama", style=discord.ButtonStyle.primary, emoji="✏️", row=2)
        btn_rename.callback = self.rename_cat
        
        btn_delete = discord.ui.Button(label="Hapus Kategori", style=discord.ButtonStyle.danger, emoji="🗑️", row=2)
        btn_delete.callback = self.delete_cat
        
        btn_create = discord.ui.Button(label="Buat Baru", style=discord.ButtonStyle.success, emoji="➕", row=2)
        btn_create.callback = self.create_cat

        self.add_item(btn_rename)
        self.add_item(btn_delete)
        self.add_item(btn_create)

    def get_embed(self):
        if not self.categories: return discord.Embed(title="Belum ada kategori.", color=discord.Color.red())
        embed = discord.Embed(title="📂 Kategori Manager", description="Pilih kategori di menu pertama, lalu pilih posisi barunya di menu kedua.", color=discord.Color.blue())
        embed.add_field(name="Kategori Terpilih", value=f"**{self.current_cat.name}**", inline=True)
        embed.add_field(name="Posisi Saat Ini", value=f"Ke-{self.current_cat.position + 1} dari {len(self.categories)}", inline=True)
        return embed

    async def select_cat(self, i):
        await i.response.defer()
        self.current_cat = discord.utils.get(self.categories, id=int(i.data["values"][0]))
        self.build_ui()
        await i.edit_original_response(embed=self.get_embed(), view=self)

    async def move_to_pos(self, i):
        await i.response.defer()
        target_pos = int(i.data["values"][0])
        try:
            # Discord edit position bergantung pada index (0-based)
            await self.current_cat.edit(position=target_pos)
            self.categories = sorted([c for c in self.guild.categories], key=lambda x: x.position)
            self.build_ui()
            await i.edit_original_response(embed=self.get_embed(), view=self)
        except Exception as e:
            print(f"Error move pos: {e}")

    async def rename_cat(self, i):
        await i.response.send_modal(CategoryNameModal(self.current_cat))

    async def delete_cat(self, i):
        await i.response.defer()
        await i.edit_original_response(
            content=f"⚠️ **PERINGATAN!** Lu yakin mau hapus kategori **{self.current_cat.name}**? Semua channel di dalamnya bakal **IKUT TERHAPUS!**", 
            embed=None, 
            view=CategoryConfirmDeleteView(self.current_cat)
        )

    async def create_cat(self, i):
        await i.response.defer(ephemeral=True)
        await i.followup.send("Buat kategori baru lewat chat ya Bang: `@bot buat kategori NamaKategori`", ephemeral=True)

class ChannelMoverView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=180)
        self.guild = guild
        self.categories = guild.categories
        self.current_category = None
        self.channels_to_move = []
        self.target_category = None
        self.build_ui()

    def build_ui(self):
        self.clear_items()
        
        if not self.categories:
            return

        # 1. Pilih Kategori Asal
        cat_opts = [discord.SelectOption(label=c.name, value=str(c.id), default=(self.current_category and c.id == self.current_category.id)) for c in self.categories[:25]]
        s_cat = discord.ui.Select(placeholder="1️⃣ Pilih Kategori Asal", options=cat_opts, row=0)
        s_cat.callback = self.select_source_cat
        self.add_item(s_cat)

        # 2. Pilih Channel (Kalau udah milih kategori)
        if self.current_category:
            ch_opts = [discord.SelectOption(label=f"#{c.name}", value=str(c.id), default=(c in self.channels_to_move)) for c in self.current_category.channels if not c.is_category()]
            if ch_opts:
                s_ch = discord.ui.Select(placeholder="2️⃣ Pilih Channel yang mau digeser", options=ch_opts, min_values=1, max_values=len(ch_opts), row=1)
                s_ch.callback = self.select_channels
                self.add_item(s_ch)

        # 3. Pilih Kategori Tujuan
        if self.channels_to_move:
            target_opts = [discord.SelectOption(label=c.name, value=str(c.id), default=(self.target_category and c.id == self.target_category.id)) for c in self.categories[:25]]
            s_target = discord.ui.Select(placeholder="3️⃣ Pilih Kategori Tujuan", options=target_opts, row=2)
            s_target.callback = self.select_target_cat
            self.add_item(s_target)

        # 4. Tombol Eksekusi
        if self.channels_to_move and self.target_category:
            btn = discord.ui.Button(label="Pindahkan Channel", style=discord.ButtonStyle.success, emoji="🚚", row=3)
            btn.callback = self.execute_move
            self.add_item(btn)

    def get_embed(self):
        embed = discord.Embed(title="🚚 Pindah Channel (Mover)", description="Pilih Kategori Asal -> Pilih Channel -> Pilih Kategori Tujuan -> Pindahkan.", color=discord.Color.green())
        embed.add_field(name="Kategori Asal", value=self.current_category.name if self.current_category else "-", inline=True)
        embed.add_field(name="Channel Dipilih", value=f"{len(self.channels_to_move)} channel", inline=True)
        embed.add_field(name="Kategori Tujuan", value=self.target_category.name if self.target_category else "-", inline=True)
        return embed

    async def select_source_cat(self, i):
        await i.response.defer()
        self.current_category = discord.utils.get(self.categories, id=int(i.data["values"][0]))
        self.channels_to_move = []
        self.build_ui()
        await i.edit_original_response(embed=self.get_embed(), view=self)

    async def select_channels(self, i):
        await i.response.defer()
        self.channels_to_move = [discord.utils.get(self.guild.channels, id=int(v)) for v in i.data["values"]]
        self.build_ui()
        await i.edit_original_response(embed=self.get_embed(), view=self)

    async def select_target_cat(self, i):
        await i.response.defer()
        self.target_category = discord.utils.get(self.categories, id=int(i.data["values"][0]))
        self.build_ui()
        await i.edit_original_response(embed=self.get_embed(), view=self)

    async def execute_move(self, i):
        await i.response.defer()
        try:
            for ch in self.channels_to_move:
                await ch.edit(category=self.target_category)
            await i.edit_original_response(content=f"✅ **BERHASIL!** {len(self.channels_to_move)} channel telah dipindahkan ke **{self.target_category.name}**.", embed=None, view=None)
        except Exception as e:
            await i.edit_original_response(content=f"❌ Gagal memindahkan: {e}", embed=None, view=None)


# === UI: CHANNEL PERMISSION EDITOR ===
class ChannelPermEditorView(discord.ui.View):
    def __init__(self, channel, role):
        super().__init__(timeout=300)
        self.channel = channel
        self.role = role
        # Ambil overwrite saat ini, atau bikin baru kalau belum ada
        self.overwrite = channel.overwrites_for(role)
        self.page = 0
        
        self.pages = [
            {"title": "1: Umum", "perms": {
                "Lihat Channel": "view_channel", 
                "Kelola Channel": "manage_channels", 
                "Kelola Izin": "manage_permissions"
            }},
            {"title": "2: Teks & Chat", "perms": {
                "Kirim Pesan": "send_messages", 
                "Baca Riwayat": "read_message_history", 
                "Sematkan Link": "embed_links", 
                "Upload File": "attach_files", 
                "Tambah Reaksi": "add_reactions",
                "Hapus Pesan": "manage_messages",
                "Tag Everyone": "mention_everyone"
            }},
            {"title": "3: Voice", "perms": {
                "Masuk VC": "connect", 
                "Bicara": "speak", 
                "Share Screen": "stream", 
                "Voice Activity": "use_voice_activation", 
                "Bisukan": "mute_members",
                "Tulikan": "deafen_members",
                "Pindah Member": "move_members"
            }}
        ]
        self.update_view()

    def get_embed(self):
        embed = discord.Embed(
            title=f"⚙️ Izin: #{self.channel.name}",
            description=f"Mengatur role: **{self.role.mention}**\n\nKlik tombol untuk mengubah status:\n🟩 **Hijau** = Izinkan | 🟥 **Merah** = Larang | ⬜ **Abu** = Netral (Ikut Default)", 
            color=discord.Color.dark_theme()
        )
        embed.set_footer(text=self.pages[self.page]["title"])
        return embed

    def update_view(self):
        self.clear_items()
        current_perms = self.pages[self.page]["perms"]
        
        # Bikin tombol dengan sistem 3-State (Allow, Deny, Neutral)
        for i, (label, p_name) in enumerate(current_perms.items()):
            val = getattr(self.overwrite, p_name)
            
            if val is True:
                style = discord.ButtonStyle.success
                icon = "🟩"
            elif val is False:
                style = discord.ButtonStyle.danger
                icon = "🟥"
            else:
                style = discord.ButtonStyle.secondary
                icon = "⬜"

            btn = discord.ui.Button(label=label, style=style, emoji=icon, row=i//3)
            
            async def cb(inter, p=p_name, b=btn):
                await inter.response.defer() # Anti Timeout
                curr = getattr(self.overwrite, p)
                
                # Logika Siklus 3-State
                if curr is None:
                    setattr(self.overwrite, p, True)
                    b.style = discord.ButtonStyle.success
                    b.emoji = "🟩"
                elif curr is True:
                    setattr(self.overwrite, p, False)
                    b.style = discord.ButtonStyle.danger
                    b.emoji = "🟥"
                else:
                    setattr(self.overwrite, p, None)
                    b.style = discord.ButtonStyle.secondary
                    b.emoji = "⬜"
                    
                await inter.edit_original_response(view=self)
            
            btn.callback = cb
            self.add_item(btn)
            
        # Tombol Navigasi (Halaman)
        nav_row = 4
        if self.page > 0:
            p_btn = discord.ui.Button(label="⬅️", style=discord.ButtonStyle.primary, row=nav_row)
            p_btn.callback = self.prev
            self.add_item(p_btn)
        if self.page < len(self.pages) - 1:
            n_btn = discord.ui.Button(label="➡️", style=discord.ButtonStyle.primary, row=nav_row)
            n_btn.callback = self.next
            self.add_item(n_btn)
            
        # Tombol Simpan
        s_btn = discord.ui.Button(label="💾 Simpan Izin", style=discord.ButtonStyle.success, row=4)
        s_btn.callback = self.save
        self.add_item(s_btn)

    async def prev(self, i):
        await i.response.defer()
        self.page -= 1
        self.update_view()
        await i.edit_original_response(embed=self.get_embed(), view=self)

    async def next(self, i):
        await i.response.defer()
        self.page += 1
        self.update_view()
        await i.edit_original_response(embed=self.get_embed(), view=self)

    async def save(self, i):
        await i.response.defer()
        try:
            await self.channel.set_permissions(self.role, overwrite=self.overwrite)
            await i.followup.send(f"✅ Izin **{self.role.name}** di channel {self.channel.mention} berhasil disimpan!", ephemeral=True)
        except Exception as e:
            await i.followup.send(f"❌ Gagal menyimpan: {e}", ephemeral=True)

class ChannelSelectForPermView(discord.ui.View):
    def __init__(self, guild, channels):
        super().__init__(timeout=180)
        self.guild = guild
        # Filter: jangan tampilin kategori, maksimal 25 channel
        valid_channels = [c for c in channels if not isinstance(c, discord.CategoryChannel)][:25]
        
        opts = [discord.SelectOption(label=f"#{c.name}", value=str(c.id), emoji="💬" if isinstance(c, discord.TextChannel) else "🔊") for c in valid_channels]
        
        s = discord.ui.Select(placeholder="1️⃣ Pilih Channel yang mau diatur...", options=opts)
        s.callback = self.cb
        self.add_item(s)

    async def cb(self, i):
        await i.response.defer()
        channel = discord.utils.get(self.guild.channels, id=int(i.data["values"][0]))
        
        # Setelah milih channel, langsung munculin dropdown role
        roles = [r for r in self.guild.roles if not r.is_default() and not r.managed and r.position < self.guild.me.top_role.position][:25]
        role_opts = [discord.SelectOption(label=r.name, value=str(r.id), emoji="🛡️") for r in roles]
        
        v = discord.ui.View(timeout=180)
        s_role = discord.ui.Select(placeholder="2️⃣ Pilih Role yang mau diatur izinnya...", options=role_opts)
        
        async def role_cb(inter):
            await inter.response.defer()
            role = discord.utils.get(inter.guild.roles, id=int(inter.data["values"][0]))
            editor = ChannelPermEditorView(channel, role)
            await inter.edit_original_response(content=None, embed=editor.get_embed(), view=editor)
            
        s_role.callback = role_cb
        v.add_item(s_role)
        
        embed = discord.Embed(title="🛡️ Pilih Role", description=f"Channel terpilih: {channel.mention}\nSekarang pilih role yang mau diatur izinnya.", color=discord.Color.blue())
        await i.edit_original_response(embed=embed, view=v)


# === UI: INTERACTIVE HELP MENU ===
class HelpMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.current_page = "home"
        self.build_ui()

    def build_ui(self):
        self.clear_items()
        opts = [
            discord.SelectOption(label="🏠 Menu Utama", value="home", default=(self.current_page=="home")),
            discord.SelectOption(label="🧠 AI & Chat Multimodal", value="ai", default=(self.current_page=="ai")),
            discord.SelectOption(label="⚙️ UI Kelola Server", value="server", default=(self.current_page=="server")),
            discord.SelectOption(label="📂 UI Kategori & Channel", value="category", default=(self.current_page=="category")),
            discord.SelectOption(label="🛡️ Admin & Fitur Lain", value="admin", default=(self.current_page=="admin"))
        ]
        s = discord.ui.Select(placeholder="Pilih kategori menu bantuan...", options=opts)
        s.callback = self.select_page
        self.add_item(s)

    def get_embed(self):
        if self.current_page == "home":
            embed = discord.Embed(
                title="🤖 BOT-FortxxV2 — Pusat Komando", 
                description="Bot Agentic Multimodal dengan UI Interaktif.\nSilakan pilih kategori menu di dropdown bawah buat liat daftar perintahnya!", 
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=bot.user.display_avatar.url)
            embed.set_footer(text="Dibuat dengan ❤️ oleh Fortxx | 21 Model AI Fallback")
        elif self.current_page == "ai":
            embed = discord.Embed(title="🧠 AI & Chat Multimodal", color=discord.Color.blue())
            embed.add_field(name="Chat & Memori", value="`@bot halo` / `@bot <pertanyaan>`", inline=False)
            embed.add_field(name="Image Generator", value="`@bot bikin gambar kucing oren`", inline=False)
            embed.add_field(name="Dengerin VN (STT)", value="Kirim Voice Note sambil reply/tag bot", inline=False)
            embed.add_field(name="Baca Dokumen (RAG)", value="Upload PDF/TXT sambil tag bot", inline=False)
            embed.add_field(name="Web Search", value="`@bot cari berita AI terbaru`", inline=False)
        elif self.current_page == "server":
            embed = discord.Embed(title="⚙️ UI Kelola Server (Interaktif)", color=discord.Color.green())
            embed.add_field(name="Buat Channel (UI)", value="`@bot buat channel` — Dropdown Kategori, Tipe, Privasi", inline=False)
            embed.add_field(name="Atur Izin Role (UI)", value="`@bot atur role` — Tombol Warna Izin Global", inline=False)
            embed.add_field(name="Setting Channel Spesifik", value="`@bot setting channel` — Atur izin Role KHUSUS di 1 channel", inline=False)
            embed.add_field(name="Bikin Tombol Take Role", value="`@bot take role VIP` — Bikin tombol ambil role otomatis", inline=False)
        elif self.current_page == "category":
            embed = discord.Embed(title="📂 UI Kategori & Channel Mover", color=discord.Color.orange())
            embed.add_field(name="Kategori Manager (UI)", value="`@bot atur kategori` — Ubah nama, geser posisi, hapus", inline=False)
            embed.add_field(name="Pindah Channel (UI)", value="`@bot geser channel` — Mindahin channel antar kategori", inline=False)
            embed.add_field(name="Buat Kategori Cepat", value="`@bot buat kategori NamaBaru`", inline=False)
        elif self.current_page == "admin":
            embed = discord.Embed(title="🛡️ Admin & Fitur Intelijen", color=discord.Color.red())
            embed.add_field(name="Auto Setup Server", value="`@bot setup server` — Bikin 60+ Channel + Sistem Verifikasi", inline=False)
            embed.add_field(name="Scan Server", value="`@bot scan server [Nama]` — Intip struktur server dari DM", inline=False)
            embed.add_field(name="List Server", value="`@bot list server` — Liat server mutual", inline=False)
            embed.add_field(name="Reset Memori", value="`@bot reset` — Hapus ingatan bot di channel ini", inline=False)
            embed.add_field(name="Statistik Bot", value="`@bot stats` — Liat penggunaan bot", inline=False)
        return embed

    async def select_page(self, i):
        await i.response.defer()
        self.current_page = i.data["values"][0]
        self.build_ui()
        await i.edit_original_response(embed=self.get_embed(), view=self)

class VerifyView(discord.ui.View):
    def __init__(self, member_role):
        super().__init__(timeout=None)
        self.member_role = member_role

    @discord.ui.button(label="Verifikasi & Ambil Role", style=discord.ButtonStyle.success, emoji="✅", custom_id="verify_btn_v1")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Lapor duluan ke Discord biar gak timeout
        await interaction.response.defer(ephemeral=True)
        
        if self.member_role in interaction.user.roles:
            return await interaction.followup.send("✅ Lu udah terverifikasi kok Bang!", ephemeral=True)
            
        try:
            await interaction.user.add_roles(self.member_role)
            await interaction.followup.send("✅ **Berhasil!** Sekarang lu punya akses penuh ke semua channel server.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Gagal ngasih role: {e}", ephemeral=True)

class TakeRoleButton(discord.ui.Button):
    def __init__(self, role):
        super().__init__(label=f"Ambil {role.name}", style=discord.ButtonStyle.success, emoji="🎭")
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        # Lapor duluan ke Discord biar gak timeout
        await interaction.response.defer(ephemeral=True)
        
        try:
            if self.role in interaction.user.roles:
                await interaction.user.remove_roles(self.role)
                await interaction.followup.send(f"✅ Role **{self.role.name}** berhasil dicopot.", ephemeral=True)
            else:
                await interaction.user.add_roles(self.role)
                await interaction.followup.send(f"✅ Role **{self.role.name}** berhasil dikasih!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Gagal ubah role: {e}", ephemeral=True)

class SetupConfirmView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=300)
        self.guild = guild
        
    @discord.ui.button(label="Bangun Sekarang", style=discord.ButtonStyle.success, emoji="✅")
    async def btn_build(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.edit_original_response(content="⏳ **Sedang membangun MEGA SERVER...**\n*(Membuat Role, 11 Kategori, dan 60+ Channel. Mohon tunggu 20-30 detik!)*", embed=None, view=None)
        
        guild = self.guild
        
        # 1. BIKIN ROLE DASAR
        member_role = discord.utils.get(guild.roles, name="Member")
        if not member_role: member_role = await guild.create_role(name="Member", color=discord.Color.green())
        admin_role = discord.utils.get(guild.roles, name="Admin")
        if not admin_role: admin_role = await guild.create_role(name="Admin", permissions=discord.Permissions(administrator=True), color=discord.Color.red())
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role: muted_role = await guild.create_role(name="Muted", color=discord.Color.dark_gray())
        
        # 2. SETTING IZIN (GATEKEEPING & ROLE SETTINGS)
        overwrites_public = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            member_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        overwrites_private = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        overwrites_staff = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member_role: discord.PermissionOverwrite(read_messages=False),
            admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # 3. BLUEPRINT MEGA SERVER (60+ Channel)
        BLUEPRINT = {
            "📌 | INFORMATION": [
                ("👋・welcome", "text", "public"), ("📜・rules", "text", "public"),
                ("📢・announcements", "text", "public"), ("🗺️・server-map", "text", "public"),
                ("❓・faq", "text", "public")
            ],
            "💬 | COMMUNITY": [
                ("💬・general-chat", "text", "private"), ("👋・introductions", "text", "private"),
                ("🗣️・off-topic", "text", "private"), ("😂・memes", "text", "private"),
                ("❓・daily-questions", "text", "private"), ("📊・polls", "text", "private"),
                ("📸・selfies", "text", "private"), ("💡・suggestions", "text", "private")
            ],
            "💻 | TECH & CODING": [
                ("🆘・programming-help", "forum", "private"), ("🐍・python", "text", "private"),
                ("🟨・javascript", "text", "private"), ("🌐・web-dev", "text", "private"),
                ("🤖・ai-and-ml", "text", "private"), ("🛠️・showcase", "text", "private"),
                ("🐛・bug-reports", "text", "private")
            ],
            "🎮 | GAMING & ESPORTS": [
                ("📰・game-news", "text", "private"), ("🎯・lfg", "text", "private"),
                ("🎬・clips", "text", "private"), ("🏆・tournaments", "text", "private"),
                ("🔫・valorant", "text", "private"), ("⛏️・minecraft", "text", "private"),
                ("📱・mobile-legends", "text", "private"), ("🎲・other-games", "text", "private")
            ],
            "🎨 | CREATIVE CORNER": [
                ("🖼️・art-gallery", "text", "private"), ("🎵・music-sharing", "text", "private"),
                ("📷・photography", "text", "private"), ("✍️・writing", "text", "private"),
                ("💸・commissions", "text", "private")
            ],
            "📚 | EDUCATION": [
                ("📝・study-tips", "text", "private"), ("📚・resources", "text", "private"),
                ("🧮・math", "text", "private"), ("🔬・science", "text", "private"),
                ("🌍・languages", "text", "private")
            ],
            "💼 | MARKETPLACE": [
                ("🛒・buy-sell", "text", "private"), ("💼・services", "text", "private"),
                ("💰・crypto", "text", "private"), ("🤝・vouches", "text", "private")
            ],
            "🌐 | SOCIALS": [
                ("📺・youtube", "text", "private"), ("🎵・tiktok", "text", "private"),
                ("📸・instagram", "text", "private")
            ],
            "⭐ | BOOSTERS": [
                ("💎・booster-chat", "text", "private"), ("🎁・perks", "text", "private")
            ],
            "🛡️ | STAFF ONLY": [
                ("💬・staff-chat", "text", "staff"), ("📋・mod-logs", "text", "staff"),
                ("🤖・bot-commands", "text", "staff"), ("🎫・ticket-transcripts", "text", "staff"),
                ("📝・staff-notes", "text", "staff")
            ],
            "🔊 | VOICE CHANNELS": [
                ("🔊 General Lounge 1", "voice", "private"), ("🔊 General Lounge 2", "voice", "private"),
                ("🎮 Gaming Squad 1", "voice", "private"), ("🎮 Gaming Squad 2", "voice", "private"),
                ("🎤 Karaoke Room", "voice", "private"), ("📚 Study Room", "voice", "private"),
                ("🎵 Music Room", "voice", "private"), ("💤 AFK Room", "voice", "private"),
                ("🔊 VIP Lounge", "voice", "private"), ("🔊 Staff Meeting", "voice", "staff")
            ]
        }
        
        ch_created = 0
        for cat_name, channels in BLUEPRINT.items():
            cat_overwrites = overwrites_public if "INFORMATION" in cat_name else (overwrites_staff if "STAFF" in cat_name else overwrites_private)
            
            category = discord.utils.get(guild.categories, name=cat_name)
            if not category:
                category = await guild.create_category(cat_name, overwrites=cat_overwrites)
            
            for ch_name, ch_type, overwrite_type in channels:
                existing = discord.utils.get(category.channels, name=ch_name)
                if not existing:
                    try:
                        if overwrite_type == "public": ow = overwrites_public
                        elif overwrite_type == "staff": ow = overwrites_staff
                        else: ow = overwrites_private
                        
                        if ch_type == "voice":
                            await guild.create_voice_channel(ch_name, category=category, overwrites=ow)
                        elif ch_type == "forum":
                            await guild.create_forum(ch_name, category=category, overwrites=ow)
                        else:
                            new_ch = await guild.create_text_channel(ch_name, category=category, overwrites=ow)
                            if "welcome" in ch_name:
                                embed_welcome = discord.Embed(title="👋 Selamat Datang!", description="Halo! Selamat datang.\n\nKlik tombol **Verifikasi** di bawah ini untuk membuka akses ke seluruh channel!", color=discord.Color.green())
                                await new_ch.send(embed=embed_welcome, view=VerifyView(member_role))
                            elif "rules" in ch_name:
                                embed_rules = discord.Embed(title="📜 Peraturan Server", description="1. Jangan toxic & spam.\n2. Hormati sesama member.\n3. Dilarang promosi tanpa izin.\n4. Gunakan channel sesuai fungsinya.", color=discord.Color.blue())
                                await new_ch.send(embed=embed_rules)
                            elif "general-chat" in ch_name:
                                await new_ch.send(embed=discord.Embed(title="💬 Chat Umum", description="Mari berdiskusi di sini!", color=discord.Color.blurple()))
                            elif "announcements" in ch_name:
                                await new_ch.send(embed=discord.Embed(title="📢 Pengumuman", description="Info terbaru bakal ada di sini.", color=discord.Color.gold()))
                        ch_created += 1
                        await asyncio.sleep(0.3) # Jeda biar gak kena Rate Limit
                    except Exception as e:
                        pass
                    
        await interaction.edit_original_response(content=f"✅ **SETUP MEGA SERVER BERHASIL!**\n\n🔒 **Gatekeeping Aktif:** Member baru HANYA bisa melihat `#welcome` dan `#rules`.\n✅ **Auto-Verifikasi:** Klik tombol di `#welcome` untuk membuka akses.\n\n📁 **11 Kategori** & **{ch_created}** Channel baru berhasil dibangun!")

    @discord.ui.button(label="Batal", style=discord.ButtonStyle.danger, emoji="❌")
    async def btn_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ **Pembangunan server dibatalkan.**", embed=None, view=None)

# ==========================================
# FUNGSI BANTUAN & EVENT BOT
# ==========================================
async def send_long(target, text, placeholder=None):
    text = (text or "").strip()
    if not text: return
    if len(text) <= 1800:
        if placeholder: await placeholder.edit(content=text)
        else: await target.reply(text)
        return
    chunks = [text[i:i+1800] for i in range(0, len(text), 1800)]
    if placeholder: await placeholder.delete()
    for chunk in chunks:
        await target.channel.send(chunk)
        await asyncio.sleep(0.4)

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} udah online!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="🛡️ Jaga Server Lu"))
    
    # Update database scam saat bot nyala
    await update_phishing_database()
    
    # Looping update tiap 6 jam (21600 detik)
    async def loop_update():
        while True:
            await asyncio.sleep(21600)
            await update_phishing_database()
    bot.loop.create_task(loop_update())


import base64
import urllib.parse

async def scan_url_virustotal(url):
    """Scan URL menggunakan VirusTotal API v3."""
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key:
        return None # Skip kalo API key gak ada
        
    # Encode URL ke base64 (wajib untuk endpoint /urls/{id})
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    
    headers = {"x-apikey": api_key, "accept": "application/json"}
    
    async with aiohttp.ClientSession() as session:
        # Cek laporan URL di database VirusTotal
        async with session.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers) as r:
            if r.status == 200:
                data = await r.json()
                stats = data['data']['attributes']['last_analysis_stats']
                malicious = stats.get('malicious', 0)
                suspicious = stats.get('suspicious', 0)
                
                if malicious > 0 or suspicious > 0:
                    return f"⚠️ **BAHAYA!** Link ini terdeteksi berbahaya oleh {malicious} antivirus (Malicious) dan {suspicious} (Suspicious)."
                return "✅ Link aman (sudah pernah discan)."
                
            elif r.status == 404:
                # Kalo 404 (belum pernah discan), kita submit URL-nya buat di-scan
                async with session.post("https://www.virustotal.com/api/v3/urls", headers={"x-apikey": api_key, "accept": "application/json"}, data={"url": url}) as post_r:
                    if post_r.status == 200:
                        return "⏳ Link baru dikirim ke VirusTotal. (Bot butuh waktu buat analisis, link sementara diizinkan)."
    return None


async def update_phishing_database():
    """Download database link scam dari GitHub setiap 6 jam."""
    global PHISHING_DOMAINS
    url = "https://raw.githubusercontent.com/Discord-AntiScam/scam-links/main/list.json"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as r:
                if r.status == 200:
                    # Ambil teks mentah, lalu parse manual pakai json.loads (anti strict MIME)
                    import json
                    text_data = await r.text()
                    data = json.loads(text_data)
                    
                    global PHISHING_DOMAINS
                    PHISHING_DOMAINS = set(data)
                    print(f"🛡️ [SECURITY] Berhasil memuat {len(PHISHING_DOMAINS)} domain scam ke dalam database lokal!")
                else:
                    print(f"⚠️ Gagal download database scam. HTTP {r.status}")
    except Exception as e:
        print(f"⚠️ Error download database scam: {e}")

class SetupPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(label="Setup Rules", style=discord.ButtonStyle.primary, emoji="📜", row=0)
    async def btn_rules(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("❌ Command ini cuma buat Admin/Owner server.", ephemeral=True)
        ch = discord.utils.find(lambda c: isinstance(c, discord.TextChannel) and "rules" in c.name.lower(), interaction.guild.channels)
        if not ch:
            return await interaction.followup.send("❌ Channel `#rules` nggak ada. Bikin dulu channel bernama `#rules` atau `🔥┃rules`.", ephemeral=True)
        
        e = discord.Embed(
            title="📜 PERATURAN MUTLAK CÁRTEL DE JALISCO",
            description="Selamat datang di markas. Sebelum lu mulai beraktivitas, baca dan patuhi aturan besi di bawah ini. **Pelanggaran = Konsekuensi.**",
            color=discord.Color.dark_red()
        )
        e.add_field(name="🤝 1. KODE ETIK & RESPECT", value="• Hormati semua member (Jefes, Sicarios, maupun Rakyat).\n• Dilarang toxic, SARA, rasis, atau nge-flame member lain.\n• Jangan pernah sebar data pribadi (Doxxing) siapapun.\n• Dilarang spam mention (terutama @everyone) tanpa izin Admin.", inline=False)
        e.add_field(name="🛡️ 2. KEAMANAN SIBER (ZERO TOLERANCE)", value="• Dilarang keras nyebar link **Phishing, Malware, Scam**, atau IP Logger.\n• Dilarang promosi **Judi Online** (Slot, Gacor, Maxwin, Togel, Casino).\n• Dilarang nyebar link **Crypto/Investasi Bodong** atau ngajak transaksi di luar server.\n• Sistem AI 24 jam memantau. **Pesan otomatis dihapus & akun dibungkam.**", inline=False)
        e.add_field(name="💬 3. OBROLAN & SPAM", value="• Dilarang spam teks (ngetik pesan sama berulang kali).\n• Gunakan channel sesuai fungsinya (jangan mabar di channel info).\n• Dilarang NSFW (konten dewasa) di luar channel yang disediakan.", inline=False)
        e.add_field(name="🔊 4. VOICE CHANNEL", value="• Dilarang putar musik keras-keras (Earrape) di VC umum.\n• Jangan keluar-masuk VC berkali-kali cuma buat cari perhatian.\n• Patuhi instruksi Admin/Moderator saat di VC.", inline=False)
        e.add_field(name="💼 5. JUAL BELI & MARKETPLACE", value="• Transaksi di dalam server adalah tanggung jawab masing-masing.\n• Dilarang menipu (Scam) saat jual-beli.\n• Wajib pakai sistem Rekber (Rekening Bersama) jika transaksi di atas 50k.", inline=False)
        e.add_field(name="⚖️ 6. SANKSI PELANGGARAN", value="🟨 **Peringatan (Warn)**: Pelanggaran ringan / spam 1-2x.\n🟧 **Timeout (Mute)**: 1 Jam s/d 28 Hari (Spam, Scam, Toxic).\n🟥 **Kick / Ban**: Pelanggaran fatal (Phishing, Doxxing, Judi).", inline=False)
        e.set_footer(text="Dengan berada di server ini, lu otomatis setuju dengan peraturan di atas.")
        e.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await ch.send(embed=e)
        await interaction.followup.send(f"✅ **BERHASIL!** Peraturan Cártel telah dikirim ke {ch.mention}", ephemeral=True)

    @discord.ui.button(label="Setup Security Logs", style=discord.ButtonStyle.success, emoji="🛡️", row=0)
    async def btn_logs(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("❌ Command ini cuma buat Admin/Owner server.", ephemeral=True)
        existing = discord.utils.get(interaction.guild.text_channels, name="🛡️・security-logs")
        if existing:
            return await interaction.followup.send(f"✅ Channel log udah ada: {existing.mention}", ephemeral=True)
        
        ow = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        for r in ["Admin", "Moderator", "Owner"]:
            role = discord.utils.get(interaction.guild.roles, name=r)
            if role: ow[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
        await interaction.guild.create_text_channel("🛡️・security-logs", overwrites=ow)
        await interaction.followup.send("✅ **BERHASIL!** Channel `#🛡️・security-logs` dibuat! Logs link/gambar berbahaya bakal masuk ke sini.", ephemeral=True)
    
    @discord.ui.button(label="Setup Welcome", style=discord.ButtonStyle.primary, emoji="👋", row=1)
    async def btn_welcome(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("❌ Admin only.", ephemeral=True)
            
        ch = discord.utils.find(lambda c: isinstance(c, discord.TextChannel) and "welcome" in c.name.lower(), interaction.guild.channels)
        if not ch:
            cat = discord.utils.get(interaction.guild.categories, name="📌 | INFORMATION")
            ch = await interaction.guild.create_text_channel("👋・welcome", category=cat)
        
        e = discord.Embed(title="👋 Selamat Datang!", description="Halo! Selamat datang di server kami. Silakan baca peraturan di channel rules dan ambil role lu!", color=discord.Color.green())
        await ch.send(embed=e)
        await interaction.followup.send(f"✅ **BERHASIL!** Pesan sambutan dibuat di {ch.mention}", ephemeral=True)

    @discord.ui.button(label="Setup Server Full", style=discord.ButtonStyle.danger, emoji="🏗️", row=1)
    async def btn_server(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send("❌ Admin only.", ephemeral=True)
            
        member_role = discord.utils.get(interaction.guild.roles, name="Member")
        if not member_role: member_role = await interaction.guild.create_role(name="Member", color=discord.Color.green())
        
        ow_pub = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        ow_priv = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), member_role: discord.PermissionOverwrite(read_messages=True, send_messages=True), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        
        cat = discord.utils.get(interaction.guild.categories, name="📌 | INFORMATION")
        if not cat: cat = await interaction.guild.create_category("📌 | INFORMATION")
        
        ch_w = discord.utils.get(cat.channels, name="👋・welcome")
        if not ch_w:
            ch_w = await interaction.guild.create_text_channel("👋・welcome", category=cat, overwrites=ow_pub)
            await ch_w.send(embed=discord.Embed(title="👋 Selamat Datang!", description="Klik tombol **Verifikasi** buat buka akses.", color=discord.Color.green()), view=VerifyView(member_role))
            
        if not discord.utils.get(cat.channels, name="📜・rules"):
            await interaction.guild.create_text_channel("📜・rules", category=cat, overwrites=ow_pub)
            
        cat_c = discord.utils.get(interaction.guild.categories, name="💬 | COMMUNITY")
        if not cat_c: cat_c = await interaction.guild.create_category("💬 | COMMUNITY", overwrites=ow_priv)
        if not discord.utils.get(cat_c.channels, name="💬・general-chat"):
            await interaction.guild.create_text_channel("💬・general-chat", category=cat_c, overwrites=ow_priv)
            
        await interaction.followup.send("✅ **BERHASIL!** Server dengan verifikasi dibuat! Cek `#👋・welcome`.", ephemeral=True)
    
    @discord.ui.button(label="Menu Bantuan", style=discord.ButtonStyle.secondary, emoji="❓", row=2)
    async def btn_help(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        e = discord.Embed(title="🤖 Menu Bantuan", color=discord.Color.blurple())
        e.add_field(name="🧠 AI & Multimodal", value="`@bot halo` / `@bot bikin gambar` / `@bot cari berita`", inline=False)
        e.add_field(name="⚙️ UI Channel & Role", value="`@bot buat channel` / `@bot atur role` / `@bot setting channel`", inline=False)
        e.add_field(name="📂 UI Kategori", value="`@bot atur kategori` / `@bot geser channel`", inline=False)
        e.add_field(name="🛡️ Admin", value="`@bot setup rules` / `@bot scan server` / `@bot stats`", inline=False)
        await interaction.followup.send(embed=e, ephemeral=True)


# === EVENT VERIFIKASI REACTION ROLE ===
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    if str(payload.emoji) != "✅": return
    
    # Cek apakah pesannya ada di database/channel yang bener
    guild = bot.get_guild(payload.guild_id)
    if not guild: return
    
    channel = guild.get_channel(payload.channel_id)
    if not channel: return
    
    try:
        message = await channel.fetch_message(payload.message_id)
        # Cek apakah ini beneran pesan verifikasi (dari bot & ada judulnya)
        if message.author.id == bot.user.id and message.embeds:
            if "VERIFIKASI CÁRTEL" in message.embeds[0].title:
                role = discord.utils.get(guild.roles, name="WARGA CJNG")
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.add_roles(role, reason="Verifikasi Cártel (Reaction)")
                    print(f"✅ [VERIFIKASI] {member.name} telah bergabung dengan Cártel.")
    except: pass

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id: return
    if str(payload.emoji) != "✅": return
    
    guild = bot.get_guild(payload.guild_id)
    if not guild: return
    
    channel = guild.get_channel(payload.channel_id)
    if not channel: return
    
    try:
        message = await channel.fetch_message(payload.message_id)
        if message.author.id == bot.user.id and message.embeds:
            if "VERIFIKASI CÁRTEL" in message.embeds[0].title:
                role = discord.utils.get(guild.roles, name="WARGA CJNG")
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.remove_roles(role, reason="Mencabut Verifikasi Cártel")
                    print(f"❌ [VERIFIKASI] {member.name} keluar dari Cártel.")
    except: pass

@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name="👋・welcome") or discord.utils.get(member.guild.text_channels, name="welcome") or member.guild.system_channel
    if welcome_channel:
        embed = discord.Embed(title="👋 Member Baru!", description=f"Selamat datang {member.mention} di **{member.guild.name}**!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member ke-{len(member.guild.members)}")
        await welcome_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    goodbye_channel = discord.utils.get(member.guild.text_channels, name="✈️・goodbye") or discord.utils.get(member.guild.text_channels, name="goodbye")
    if goodbye_channel:
        embed = discord.Embed(title="😢 Member Keluar", description=f"**{member.name}** telah meninggalkan server.", color=discord.Color.dark_red())
        embed.set_thumbnail(url=member.display_avatar.url)
        await goodbye_channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild: return
    logs_channel = discord.utils.get(message.guild.text_channels, name="📋・mod-logs") or discord.utils.get(message.guild.text_channels, name="logs")
    if logs_channel:
        embed = discord.Embed(title="🗑️ Pesan Dihapus", color=discord.Color.red())
        embed.add_field(name="User", value=message.author.mention, inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Isi Pesan", value=message.content[:1024] or "*(Gambar/Embed)*", inline=False)
        await logs_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or not before.guild or before.content == after.content: return
    logs_channel = discord.utils.get(before.guild.text_channels, name="📋・mod-logs") or discord.utils.get(before.guild.text_channels, name="logs")
    if logs_channel:
        embed = discord.Embed(title="✏️ Pesan Diedit", color=discord.Color.orange())
        embed.add_field(name="User", value=before.author.mention, inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Sebelum", value=before.content[:500] or "-", inline=False)
        embed.add_field(name="Sesudah", value=after.content[:500] or "-", inline=False)
        await logs_channel.send(embed=embed)


# === SISTEM KEAMANAN AI (JANGAN DIHAPUS) ===
import base64
import urllib.parse

async def evaluate_discord_link_ai(message_content):
    prompt = f"""Kamu adalah moderator server Discord yang ketat. Analisis pesan berikut:
"{message_content}"

Apakah pesan ini mengandung SPAM link Discord (discord.gg)?
Ciri-ciri SPAM: Mengiming-imingi Nitro gratis, crypto, giveaway, link hack, atau judi online.
Ciri-ciri AMAN: HANYA berisi link discord.gg biasa, atau promosi server teman/komunitas dengan kalimat wajar. JANGAN anggap spam jika hanya share link Discord tanpa embel-embel mencurigakan.

Jawab HANYA dengan 'SPAM' atau 'AMAN'."""
    key = os.getenv("GROQ_API_KEY")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": "qwen/qwen3.8-27b", "messages": [{"role": "user", "content": prompt}], "max_tokens": 10, "temperature": 0}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    return "SPAM" in data['choices'][0]['message']['content'].strip().upper()
    except: pass
    return False

async def check_discord_invite(url, guild, message_content=""):
    match = _re.search(r'discord\.gg/([a-zA-Z0-9\-]+)', url)
    if not match: return False
    invite_code = match.group(1)
    try:
        invite = await bot.fetch_invite(invite_code)
        if invite.guild and invite.guild.id == guild.id: return False
        scam_keywords = ["nitro", "free", "gift", "crypto", "bitcoin", "investment", "profit", "steam", "airdrop", "giveaway"]
        if any(k in message_content.lower() for k in scam_keywords): return True
        if invite.guild and any(k in invite.guild.name.lower() for k in scam_keywords): return True
        return False
    except Exception:
        # KALO LINK EXPIRED / BOT GAK ADA DI SERVER TUJUAN:
        # Jangan langsung anggap scam. Cek dulu apakah ada kata kunci bahaya.
        scam_keywords = ["nitro", "free", "gift", "crypto", "bitcoin", "investment", "profit", "steam", "airdrop", "giveaway", "hack", "cheat", "judi", "slot", "gacor", "maxwin"]
        if any(k in message_content.lower() for k in scam_keywords):
            return True  # Baru hapus kalo ada keyword jahat
        return False  # Kalo link biasa, biarin aja

async def scan_url_virustotal(url):
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key: return None
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    headers = {"x-apikey": api_key, "accept": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers, timeout=10) as r:
                if r.status == 200:
                    stats = (await r.json())['data']['attributes']['last_analysis_stats']
                    if stats.get('malicious', 0) > 0 or stats.get('suspicious', 0) > 0: return "BAHAYA"
    except: pass
    return None

async def evaluate_image_risk(attachment):
    if attachment.size > 2 * 1024 * 1024: return 0, []
    try:
        img_bytes = await attachment.read()
        b64_img = base64.b64encode(img_bytes).decode('utf-8')
        prompt = "Analisis gambar ini. Apakah ini penipuan crypto/investasi, giveaway palsu (Free Nitro), atau screenshot hack? Jawab HANYA 'SCAM' atau 'AMAN'."
        key = os.getenv("GROQ_API_KEY")
        payload = {"model": "qwen/qwen3.8-27b", "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}]}], "max_tokens": 10}
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload, timeout=15) as r:
                if r.status == 200:
                    if "SCAM" in (await r.json())['choices'][0]['message']['content'].strip().upper(): return 70, ["AI mendeteksi gambar Scam/Crypto"]
    except: pass
    return 0, []


async def ai_intent_spam_detector(message_content, author_name):
    """Pakai AI buat ngebaca niat/maksud pesan, apakah spam atau bukan."""
    if not message_content or len(message_content) > 1000:
        return 0, ""
    
    prompt = f"""Kamu adalah AI penjaga server Discord yang SANGAT KETAT.
Tugasmu: Deteksi NIAT jahat dari pesan berikut.

Nama user: {author_name}
Isi pesan: "{message_content}"

FILTER UTAMA (Anggap SPAM jika memenuhi ini):
1. Promosi Judi Online (Slot, Gacor, Maxwin, Togel, Casino, Deposit, WD).
2. Crypto/Investasi Bodong (Profit, Cuan, Airdrop, Bitcoin palsu).
3. Phishing/Scam (Cek bio, Link di bio, Free Nitro, Giveaway palsu, Hack/Cheat).
4. Ajak transaksi luar server (Ajak DM, WA, Telegram).

PENTING: 
- Pesan singkat seperti "Tes", "Ok", "Halo" adalah AMAN (bukan spam).
- Bercanda atau ngobrol biasa adalah AMAN.

Balas HANYA dengan format JSON valid (tanpa markdown):
{{"verdict": "SPAM" atau "AMAN", "confidence": 0-100, "reason": "alasan singkat"}}"""

    key = os.getenv("GROQ_API_KEY")
    if not key: return 0, ""
    
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
        "temperature": 0
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    txt = data['choices'][0]['message']['content'].strip()
                    import json as _json
                    import re as _re_ai
                    m = _re_ai.search(r'\{.*\}', txt, _re_ai.DOTALL)
                    if m:
                        result = _json.loads(m.group(0))
                        verdict = result.get("verdict", "AMAN").upper()
                        confidence = int(result.get("confidence", 0))
                        reason = result.get("reason", "")
                        if verdict == "SPAM" and confidence >= 70:
                            return 60, f"AI mendeteksi Spam: {reason} (Confidence: {confidence}%)"
    except Exception as e:
        print(f"⚠️ AI Intent Error: {e}")
    return 0, ""

def should_ai_scan(message):
    """Filter cepat: Cuma kirim ke AI kalau ada kata kunci bahaya."""
    if not message.content: return False
    txt = message.content.lower()
    
    # Daftar kata kunci yang WAJIB dicek AI (Judi, Crypto, Bio, dll)
    trigger_words = [
        "bio", "judi", "slot", "gacor", "maxwin", "cuan", "crypto", 
        "bitcoin", "investasi", "profit", "nitro", "free", "gift", 
        "airdrop", "giveaway", "dm", "wa", "telegram", "hack", "cheat"
    ]
    
    # 1. Ada kata kunci bahaya
    if any(word in txt for word in trigger_words): return True
    
    # 2. Ada URL
    if "http://" in txt or "https://" in txt or "discord.gg" in txt: return True
    
    # 3. Karakter diulang-ulang (misal: aaaaa)
    import re as _re_f
    if _re_f.search(r'(.)\1{6,}', txt): return True
    
    return False


async def send_security_log(guild, author, channel, content, reasons, action_taken):
    """Fungsi mandiri buat ngirim log. Bikin channel otomatis kalau belum ada."""
    # 1. Cari channel (Toleran nama)
    log_ch = discord.utils.find(lambda c: isinstance(c, discord.TextChannel) and ("security" in c.name.lower() or "logs" in c.name.lower()), guild.channels)
    
    # 2. Kalau nggak ada, bikin baru
    if not log_ch:
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            # Kasih akses ke Staff
            for r_name in ["Admin", "Moderator", "Owner", "Staff"]:
                r = discord.utils.get(guild.roles, name=r_name)
                if r: overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
            log_ch = await guild.create_text_channel("🛡️・security-logs", overwrites=overwrites)
            print(f"✅ [LOG SYSTEM] Channel log baru otomatis dibuat: #{log_ch.name}")
        except Exception as e:
            print(f"❌ [LOG SYSTEM] Gagal bikin channel log: {e}")
            return

    # 3. Bikin Embed Laporan
    embed = discord.Embed(title="🚨 SECURITY LOG: TINDAKAN DARURAT", color=discord.Color.dark_red())
    embed.add_field(name="👤 Pelaku", value=f"{author.mention} (`{author.name}`)", inline=False)
    embed.add_field(name="📍 Lokasi", value=channel.mention, inline=True)
    embed.add_field(name="⚖️ Hukuman", value=action_taken, inline=True)
    
    pesan = content[:500] if content else "(Gambar/Attachment)"
    embed.add_field(name="💬 Pesan Asli", value=f"```{pesan}```", inline=False)
    
    reason_text = chr(10).join(["- " + r for r in reasons])
    embed.add_field(name="🔍 Alasan Teknis", value=reason_text[:1024] or "Skor tinggi", inline=False)
    embed.set_thumbnail(url=author.display_avatar.url)
    
    # 4. Kirim
    try:
        await log_ch.send(embed=embed)
        print(f"✅ [LOG SUCCESS] Laporan masuk ke #{log_ch.name}")
    except Exception as e:
        print(f"❌ [LOG FAILED] Gagal kirim ke #{log_ch.name}: {e}")


async def check_urlhaus(url):
    """Cek URL ke database malware URLhaus (abuse.ch). 100% gratis, tanpa API key."""
    endpoint = "https://urlhaus-api.abuse.ch/v1/url/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, data={"url": url}, timeout=8) as r:
                if r.status == 200:
                    data = await r.json()
                    status = data.get("query_status", "")
                    if status == "is_listed":
                        return True
    except Exception as e:
        print(f"⚠️ URLhaus error: {e}")
    return False

async def evaluate_message_risk(message):
    score = 0
    reasons = []
    
    account_age_days = (discord.utils.utcnow() - message.author.created_at).days
    if account_age_days < 7:
        score += 30
        reasons.append("Akun baru (< 7 hari)")

    content_lower = message.content.lower() if message.content else ""
    
    # 1. KATA KUNCI SCAM/JUDI
    scam_keywords = ["check my bio", "cek bio", "cek profil", "link di bio", "bio gw", "nitro", "free", "gift", "crypto", "bitcoin", "investment", "profit", "steam", "airdrop", "giveaway", "hack", "cheat", "judi", "slot", "gacor", "maxwin", "togel", "casino"]
    has_scam_keyword = any(k in content_lower for k in scam_keywords)
    if has_scam_keyword:
        score += 50
        reasons.append("Kata kunci Scam/Judi/Crypto")
        
    # 2. LINK DISCORD MENTAH (TANPA https://)
    raw_dc_links = _re.findall(r'(?<!http://)(?<!https://)(discord\.gg/[a-zA-Z0-9\-]+|discord\.com/invite/[a-zA-Z0-9\-]+)', content_lower)
    if raw_dc_links:
        # Kalo mentah TAPI gak ada kata kunci scam, cuma warning ringan (biar gak kehapus)
        if has_scam_keyword:
            score += 80
            reasons.append("Link Discord MENTAH + Kata kunci Scam")
        else:
            score += 20
            reasons.append("Link Discord MENTAH (Tapi tidak ada indikasi scam)")
        return score, reasons

    # 3. LINK BIASA (PAKAI https://)
    urls = _re.findall(r'(https?://[^\s]+)', content_lower)
    for url in urls:
        # Whitelist
        if any(wl in url for wl in ["youtube.com", "youtu.be", "tenor.com", "giphy.com", "imgur.com", "cdn.discordapp.com", "media.discordapp.net"]):
            continue
            
        # Kalo ini link Discord
        if "discord.gg" in url or "discord.com/invite" in url:
            # Cek validitas & AI
            bad_invite = await check_discord_invite(url, message.guild, content_lower)
            if bad_invite or has_scam_keyword:
                score += 80
                reasons.append("Invite Discord Berbahaya/Scam")
            else:
                # Kalo aman, jangan tambah skor sama sekali
                reasons.append("Link Discord (Terdeteksi Aman)")
            continue # Lanjut ke link berikutnya
            
        # Kalo ini link tes malware
        if "testsafebrowsing.appspot.com" in url:
            score = 100
            reasons.append("Link Test Malware (Bahaya Tinggi)")
            continue
            
        # Buka Link Pendek
        try:
            expanded_url = await expand_url(url)
        except:
            expanded_url = url
            
        # Cek URLhaus
        try:
            if await check_urlhaus(expanded_url):
                score = 100
                reasons.append("URLhaus mendeteksi Malware/Phishing")
                continue
        except: pass
            
        # Cek Link Shortener (Kalo gak ada keyword scam, cuma warning)
        if any(short in url for short in ["bit.ly", "tinyurl.com", "cutt.ly", "t.co", "in.run"]):
            if has_scam_keyword:
                score += 60
                reasons.append("Link Shortener + Kata kunci Scam")
            else:
                score += 20
                reasons.append("Link Shortener (Tidak ada indikasi scam)")
            
        # Cek VirusTotal
        if score < 70:
            try:
                if await scan_url_virustotal(expanded_url) == "BAHAYA":
                    score = 100
                    reasons.append("VirusTotal mendeteksi Malware/Phishing")
                    continue
            except:
                pass
                
    return score, reasons  # Langsung balikin skor tinggi

    # 4. LINK BIASA (PAKAI https://)
    urls = _re.findall(r'(https?://[^\s]+)', content_lower)
    for url in urls:
        # Whitelist link aman
        if any(wl in url for wl in ["youtube.com", "youtu.be", "tenor.com", "giphy.com", "imgur.com", "cdn.discordapp.com", "media.discordapp.net", "github.com"]):
            continue
            
        # Link tes malware (khusus ngetes)
        if "testsafebrowsing.appspot.com" in url:
            score = 100
            reasons.append("Link Test Malware (Bahaya Tinggi)")
            continue
            
        # A. BUKA LINK PENDEK (SHORTLINK EXPANDER)
        try:
            expanded_url = await expand_url(url)
        except:
            expanded_url = url
            
        if expanded_url != url:
            reasons.append(f"Link Pendek dibuka jadi: {expanded_url[:60]}")
            
        # B. CEK URL ASLI KE URLHAUS (GRATIS, NO KEY)
        try:
            if await check_urlhaus(expanded_url):
                score = 100
                reasons.append("URLhaus mendeteksi Malware/Phishing")
                continue
        except:
            pass
            
        # C. LINK SHORTENER (Curiga)
        if any(short in url for short in ["bit.ly", "tinyurl.com", "cutt.ly", "t.co", "in.run"]):
            score += 60
            reasons.append("Link Shortener (Mencurigakan)")
            
        # D. CEK VIRUSTOTAL
        if score < 70:
            try:
                if await scan_url_virustotal(expanded_url) == "BAHAYA":
                    score = 100
                    reasons.append("VirusTotal mendeteksi Malware/Phishing")
                    continue
            except:
                pass
                
        # E. CEK INVITE DISCORD (AI + VALIDITAS)
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
                reasons.append("Link Shortener + Kata kunci bahaya")
                
    # 5. AI INTENT DETECTOR (Buat "Check Bio", Judi, dll)
    # FITUR INI WAJIB ADA BIAR AI BISA BACA NIAT
    try:
        if should_ai_scan(message):
            ai_score, ai_reason = await ai_intent_spam_detector(message.content, message.author.name)
            score += ai_score
            if ai_reason:
                reasons.append(ai_reason)
    except Exception as e:
        print(f"⚠️ AI Intent error: {e}")
                
    return score, reasons

    # 3. LINK BIASA (PAKAI https://)
    urls = _re.findall(r'(https?://[^\s]+)', content_lower)
    for url in urls:
        # Whitelist
        if any(wl in url for wl in ["youtube.com", "youtu.be", "tenor.com", "giphy.com", "imgur.com", "cdn.discordapp.com", "media.discordapp.net"]):
            continue
            
        # Link tes malware khusus
        if "testsafebrowsing.appspot.com" in url:
            score = 100
            reasons.append("Link Test Malware (Bahaya Tinggi)")
            continue
            
        # A. Buka Link Pendek (Shortlink Expander)
        try:
            expanded_url = await expand_url(url)
        except:
            expanded_url = url
            
        if expanded_url != url:
            reasons.append(f"Link Pendek dibuka jadi: {expanded_url[:60]}")
            
        # B. Cek ke URLhaus (Gratis, No Key)
        try:
            if await check_urlhaus(expanded_url):
                score = 100
                reasons.append("URLhaus mendeteksi Malware/Phishing")
                continue
        except:
            pass
            
        # C. Link Shortener (Curiga)
        if any(short in url for short in ["bit.ly", "tinyurl.com", "cutt.ly", "t.co", "in.run"]):
            score += 60
            reasons.append("Link Shortener (Mencurigakan)")
            
        # D. Cek VirusTotal
        if score < 70:
            try:
                if await scan_url_virustotal(expanded_url) == "BAHAYA":
                    score = 100
                    reasons.append("VirusTotal mendeteksi Malware/Phishing")
                    continue
            except:
                pass
                
        # E. Cek Invite Discord
        if "discord.gg" in url:
            try:
                if await evaluate_discord_link_ai(message.content):
                    score += 80
                    reasons.append("AI mendeteksi SPAM Link Discord")
                    continue
                if await check_discord_invite(url, message.guild, content_lower):
                    score += 60
                    reasons.append("Invite Discord mencurigakan")
            except:
                pass
                
    return score, reasons

    if raw_dc_links:
        score += 80
        reasons.append("Link Discord MENTAH")
        return score, reasons

    # 3. LINK BIASA
    for url in urls:
        if any(wl in url for wl in ["youtube.com", "youtu.be", "tenor.com", "giphy.com", "imgur.com"]): continue
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if any(scam_domain in domain for scam_domain in PHISHING_DOMAINS):
            score += 80
            reasons.append(f"Link Blacklist ({domain})")
            continue
            
        if "discord.gg" in url:
            if await evaluate_discord_link_ai(message.content):
                score += 80
                reasons.append("AI mendeteksi SPAM Link Discord")
                continue
            if await check_discord_invite(url, message.guild, content_lower):
                score += 60
                reasons.append("Invite Discord mencurigakan")
                
        # Kalau VirusTotal bilang bahaya, skor langsung 100 (Auto Hapus)
        if await scan_url_virustotal(url) == "BAHAYA":
            score = 100 
            reasons.append("VirusTotal deteksi Malware/Phishing (Auto Hapus)")
                
    return score, reasons
        
    urls = _re.findall(r'(https?://[^\s]+)', content_lower)
    for url in urls:
        if any(wl in url for wl in ["youtube.com", "youtu.be", "tenor.com", "giphy.com", "imgur.com"]): continue
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.lower()
        if any(scam_domain in domain for scam_domain in PHISHING_DOMAINS):
            score += 80
            reasons.append(f"Link Blacklist ({domain})")
            continue
        if "discord.gg" in url:
            if await evaluate_discord_link_ai(message.content):
                score += 80
                reasons.append("AI mendeteksi SPAM Link Discord")
                continue
            if await check_discord_invite(url, message.guild, content_lower):
                score += 60
                reasons.append("Invite Discord mencurigakan")
        if score < 70:
            if await scan_url_virustotal(url) == "BAHAYA":
                score += 50
                reasons.append("VirusTotal deteksi malware")
                
    user_id = message.author.id
    now = time.time()
    if user_id not in USER_SPAM_TRACKER:
        USER_SPAM_TRACKER[user_id] = []
    USER_SPAM_TRACKER[user_id] = [t for t in USER_SPAM_TRACKER[user_id] if now - t < 10]
    USER_SPAM_TRACKER[user_id].append(now)
    if len(USER_SPAM_TRACKER[user_id]) >= 5:
        score += 100
        reasons.append("Spamming (Kirim pesan terlalu cepat)")
        
    return score, reasons

@bot.event
async def on_message(message):
    if message.author.bot: return

    # === BENTENG RULES (PALING DEPAN, ANTI NYAMBAR) ===
    if message.guild and message.content:
        _raw = message.content.lower()
        if "rules" in _raw and any(x in _raw for x in ["setup", "buat", "bikin", "atur", "config"]):
            if message.author.guild_permissions.administrator or message.author.id == message.guild.owner_id:
                _rc = discord.utils.find(lambda c: isinstance(c, discord.TextChannel) and "rules" in c.name.lower(), message.guild.channels)
                if _rc:
                    _embed = discord.Embed(
                        title="📜 PERATURAN CÁRTEL DE JALISCO",
                        description="Selamat datang di markas. Baca dan patuhi aturan besi di bawah ini. **Pelanggaran = Konsekuensi.**",
                        color=discord.Color.dark_red()
                    )
                    _embed.add_field(name="🤝 1. Kode Etik", value="• Hormati semua member.\n• Dilarang toxic, rasis, SARA.\n• Jangan sebar data pribadi (Doxxing).", inline=False)
                    _embed.add_field(name="🛡️ 2. Keamanan (ZERO TOLERANCE)", value="• Dilarang nyebar link **Phishing, Malware, Scam**.\n• Dilarang promosi Judi Online (Slot, Gacor).\n• Dilarang link Crypto/Investasi Bodong.\n• Sistem AI memantau 24 jam. **Pesan dihapus & akun dibungkam.**", inline=False)
                    _embed.add_field(name="💬 3. Chat & Spam", value="• Dilarang spam teks.\n• Dilarang mention `@everyone` tanpa izin.\n• Gunakan channel sesuai fungsi.", inline=False)
                    _embed.add_field(name="🔊 4. Voice Channel", value="• Dilarang putar musik keras (Earrape).\n• Jangan keluar-masuk VC cari perhatian.\n• Patuhi instruksi Admin.", inline=False)
                    _embed.add_field(name="⚖️ 5. Sanksi", value="🟨 **Peringatan**: Pelanggaran ringan.\n🟧 **Mute**: 1 Jam - 28 Hari.\n🟥 **Kick/Ban**: Pelanggaran fatal.", inline=False)
                    _embed.set_footer(text="Dengan berada di server ini, lu setuju dengan peraturan di atas.")
                    
                    await _rc.send(embed=_embed)
                    try: await message.delete()
                    except: pass
                    return
    # === END BENTENG RULES ===

    # --- INTERCEPTOR MUTLAK: RULES (PASTI JALAN) ---
    if message.guild and ("rules" in message.content.lower() and any(x in message.content.lower() for x in ["setup", "buat", "bikin", "atur"])):
        if not message.author.guild_permissions.administrator and message.author.id != message.guild.owner_id:
            await message.reply("❌ Command ini cuma buat Admin/Owner server.")
            return
            
        rules_ch = discord.utils.find(lambda c: isinstance(c, discord.TextChannel) and "rules" in c.name.lower(), message.guild.channels)
        if not rules_ch:
            await message.reply("❌ Channel `#rules` nggak ketemu. Bikin dulu ya.")
            return
            
        embed = discord.Embed(
            title="📜 PERATURAN CÁRTEL DE JALISCO",
            description="Selamat datang di markas. Baca dan patuhi aturan besi di bawah ini. **Pelanggaran = Konsekuensi.**",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="🤝 1. Kode Etik", value="• Hormati semua member.\n• Dilarang toxic, rasis, SARA.\n• Jangan sebar data pribadi (Doxxing).", inline=False)
        embed.add_field(name="🛡️ 2. Keamanan (ZERO TOLERANCE)", value="• Dilarang nyebar link **Phishing, Malware, Scam**.\n• Dilarang promosi Judi Online (Slot, Gacor).\n• Dilarang link Crypto/Investasi Bodong.\n• Sistem AI memantau 24 jam. **Pesan dihapus & akun dibungkam.**", inline=False)
        embed.add_field(name="💬 3. Chat & Spam", value="• Dilarang spam teks.\n• Dilarang mention `@everyone` tanpa izin.\n• Gunakan channel sesuai fungsi.", inline=False)
        embed.add_field(name="🔊 4. Voice Channel", value="• Dilarang putar musik keras (Earrape).\n• Jangan keluar-masuk VC cari perhatian.\n• Patuhi instruksi Admin.", inline=False)
        embed.add_field(name="⚖️ 5. Sanksi", value="🟨 **Peringatan**: Pelanggaran ringan.\n🟧 **Mute**: 1 Jam - 28 Hari.\n🟥 **Kick/Ban**: Pelanggaran fatal.", inline=False)
        embed.set_footer(text="Dengan berada di server ini, lu setuju dengan peraturan di atas.")
        
        await rules_ch.send(embed=embed)
        try: await message.delete()
        except: pass
        return
    # --- END INTERCEPTOR MUTLAK ---


    # --- SISTEM ANTI-SPAM TEKS (MUTE 80 TAHUN) ---
    if message.guild and message.content and not bot.user.mentioned_in(message):
        user_id = message.author.id
        msg_content = message.content.strip().lower()
        
        # Abaikan kalau cuma 1-3 huruf (misal "p", "ok", "wkwk")
        if len(msg_content) > 3:
            now = time.time()
            
            if user_id not in TEXT_SPAM_TRACKER:
                TEXT_SPAM_TRACKER[user_id] = {"msg": msg_content, "warns": 1, "time": now}
            else:
                data = TEXT_SPAM_TRACKER[user_id]
                
                # Kalau pesannya SAMA dan dalam waktu < 10 detik
                if msg_content == data["msg"] and (now - data["time"]) < 10:
                    data["warns"] += 1
                    data["time"] = now
                    
                    if data["warns"] == 3:
                        try: await message.channel.send(f"⚠️ {message.author.mention}, berhenti spam! Ini peringatan terakhir.")
                        except: pass
                        
                    elif data["warns"] >= 5:
                        try:
                            await message.delete()
                            await message.author.timeout(discord.utils.utcnow() + datetime.timedelta(days=28), reason="Auto-Mod: Spam Teks")
                            embed = discord.Embed(title="🚨 SPAMMER DIBUNGKAM! 🚨", description=f"{message.author.mention} di-Mute 80 Tahun karena spam teks berulang.", color=discord.Color.dark_red())
                            await message.channel.send(embed=embed)
                            print(f"✅ [ANTI-SPAM] Berhasil mute {message.author.name} karena spam.")
                            
                            # Kirim log
                            log_ch = discord.utils.find(lambda c: isinstance(c, discord.TextChannel) and ("security" in c.name.lower() or "logs" in c.name.lower()), message.guild.channels)
                            if log_ch:
                                await log_ch.send(embed=discord.Embed(title="🚨 SECURITY LOG: SPAM TEKS", description=f"**Pelaku:** {message.author.mention}\n**Hukuman:** Mute 80 Tahun\n**Pesan:** {msg_content}", color=discord.Color.dark_red()))
                                
                        except Exception as e:
                            print(f"❌ [ANTI-SPAM] GAGAL MUTE! Alasan: {e}")
                            
                            # Deteksi alasan spesifik
                            err_str = str(e).lower()
                            if "forbidden" in err_str or "permissions" in err_str:
                                if message.guild.owner_id == message.author.id:
                                    reason = "Orang ini adalah **Pemilik Server (Owner)**. Discord melarang mutlak untuk mute Owner."
                                elif message.guild.me.top_role <= message.author.top_role:
                                    reason = "**Role Bot** posisinya di bawah role orang ini. Geser Role Bot ke atas di Server Settings > Roles."
                                else:
                                    reason = "**Bot nggak punya izin Manage Members/Moderate Members**. Cek Role Bot."
                            else:
                                reason = f"Error API Discord: {e}"
                            
                            try: await message.channel.send(f"⚠️ Sistem mendeteksi spam, TAPI bot gagal nge-mute.\n\n**Alasan:** {reason}")
                            except: pass
                        data["warns"] = 0
                        data["msg"] = ""
                else:
                    # Reset kalau pesan beda
                    TEXT_SPAM_TRACKER[user_id] = {"msg": msg_content, "warns": 1, "time": now}


    # ==========================================
    # SYSTEM SECURITY FINAL (ANTI SPAM & PHISHING)
    # ==========================================
    if message.guild:
        is_admin = False
        is_command = bot.user.mentioned_in(message) or message.content.startswith("!")

        # Hanya scan kalau BUKAN Admin dan BUKAN Command
        if not is_command:
            async def process_risk():
                total_score = 0
                all_reasons = []
                
                # 1. Skor dari AI & Link (evaluate_message_risk)
                t_score, t_reasons = await evaluate_message_risk(message)
                total_score += t_score
                all_reasons.extend(t_reasons)
                
                # 2. Skor dari Gambar (evaluate_image_risk)
                if message.attachments:
                    for att in message.attachments:
                        if att.content_type and att.content_type.startswith("image/"):
                            i_score, i_reasons = await evaluate_image_risk(att)
                            total_score += i_score
                            all_reasons.extend(i_reasons)

                # JIKA SKOR TINGGI (HAPUS & LOG)
                if total_score >= 70:
                    try:
                        # Cek izin bot dulu sebelum hapus
                        if not message.guild.me.guild_permissions.manage_messages:
                            print(f"❌ [ERROR] Bot nggak punya izin Manage Messages untuk hapus pesan!")
                            return
                            
                        try: await message.delete()
                        except: pass
                        embed = discord.Embed(title="🚨 PELANGGARAN KEAMANAN TERDETEKSI 🚨", description=f"{message.author.mention}, pesan Anda telah dihapus paksa.\n\nSistem mendeteksi indikasi **Link Berbahaya, Phishing, atau Penipuan**.", color=discord.Color.red())
                        embed.set_footer(text="Automated Defense System")
                        await message.channel.send(embed=embed, delete_after=15)
                        
                        # PANGGIL FUNGSI LOG MANDIRI
                        await send_security_log(message.guild, message.author, message.channel, message.content, all_reasons, "🗑️ **Pesan Dihapus** (Bahaya Tinggi)")
                    except Exception as e: print(f"Gagal hapus: {e}")
                    
                # JIKA SKOR SEDANG (WARNING & LOG)
                elif total_score >= 40:
                    try:
                        embed = discord.Embed(title="⚠️ PERINGATAN SISTEM ⚠️", description=f"{message.author.mention}, pesan Anda terdeteksi mengandung konten mencurigakan.", color=discord.Color.orange())
                        embed.set_footer(text="Automated Defense System")
                        await message.reply(embed=embed)
                        
                        # PANGGIL FUNGSI LOG MANDIRI
                        await send_security_log(message.guild, message.author, message.channel, message.content, all_reasons, "⚠️ **Peringatan Diberikan**")
                    except: pass

            asyncio.create_task(process_risk())

    # RATE LIMIT & MENTION HANDLER# RATE LIMIT & MENTION HANDLER
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        is_owner = message.guild and message.author.id == message.guild.owner_id
        if not is_owner:
            allowed, reason, wait = check_rate_limit(message.author.id)
            if not allowed:
                reply = "⏱️ Quota abis." if reason == "per_hour" else f"⏱️ Tunggu {wait} detik."
                try: await message.reply(reply)
                except: pass
                return

        prompt = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()

        

        
        # FILE UPLOAD (VOICE/DOCS)
        target_attachments = message.attachments
        
        # --- VISION TO SERVER (BACA GAMBAR & BIKIN STRUKTUR) ---
        if target_attachments and any(f.filename.lower().endswith((".png", ".jpg", ".jpeg")) for f in target_attachments):
            attachment = target_attachments[0]
            msg = await message.reply("🧠 **AI Groq sedang membaca gambar & mengekstrak struktur...**")
            image_bytes = await attachment.read()
            b64_img = base64.b64encode(image_bytes).decode('utf-8')
            
            vision_prompt = '''Kamu adalah mesin OCR presisi tinggi. Baca gambar Discord ini dan SALIN PERSIS teks nama kategori dan channel beserta emojinya.
TENTUKAN TIPE CHANNEL DENGAN TEPAT:
- Jika ada icon speaker (🔊), type = "voice".
- Jika ada icon gelembung obrolan/dua orang (Forum), type = "forum".
- Jika ada icon pagar (#), type = "text".

Salin apa adanya termasuk emoji dan simbol. Ganti spasi dengan tanda hubung '-' atau titik '・'.

Output HANYA JSON:
{"categories": [{"name": "『 Registrasi Family 』", "channels": [{"name": "📋・family・registration", "type": "forum"}]}]}'''
            
            key = os.getenv("GROQ_API_KEY")
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": "qwen/qwen3.8-27b",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                }],
                "max_tokens": 2000
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30) as r:
                        if r.status != 200:
                            raise Exception(f"Groq API Error: HTTP{r.status}")
                        res_data = await r.json()
                        res_text = res_data['choices'][0]['message']['content']
                
                match = _re.search(r'\{.*\}', res_text, _re.DOTALL)
                if not match:
                    raise Exception(f"Format JSON tidak ditemukan. Response: {res_text[:100]}")
                data = json.loads(match.group(0))
                
                await msg.edit(content="⚙️ **Struktur ditemukan! Mulai membangun kategori & channel...**")
                
                created_count = 0
                for cat in data.get("categories", []):
                    cat_name = cat.get("name", "New Category")
                    category = discord.utils.get(message.guild.categories, name=cat_name)
                    if not category:
                        category = await message.guild.create_category(cat_name)
                        created_count += 1
                        await asyncio.sleep(1)
                        
                    for ch in cat.get("channels", []):
                        ch_name = ch.get("name", "new-channel").strip()
                        # Hapus karakter ilegal Discord, tapi biarin emoji & strip
                        ch_name = _re.sub(r'[^a-zA-Z0-9\s\-\_\|\・\•\📋\🔒\📁\🔊\📜\🚫\📩\⬆\🚀\💬\🎮\🎤\📚\🎵\💤\⭐\🛡\💎\🎁\📢\🗺\❓\😂\🗣\👋\🖼\📷\✍\💸\🧮\🔬\🌍\🛒\💼\💰\🤝\📺\🎵\📸]', '', ch_name).lower()
                        ch_name = ch_name.replace(" ", "-")
                        if not discord.utils.get(category.channels, name=ch_name):
                            ch_type = ch.get("type", "text").lower()
                            
                            # SMART FALLBACK: Kalau ada kata 'registration' atau 'forum', paksa jadi Forum!
                            if "registration" in ch_name.lower() or "forum" in ch_name.lower():
                                ch_type = "forum"
                                
                            if ch_type == "voice":
                                await message.guild.create_voice_channel(ch_name, category=category)
                            elif ch_type == "forum":
                                await message.guild.create_forum(ch_name, category=category)
                            else:
                                await message.guild.create_text_channel(ch_name, category=category)
                                
                            created_count += 1
                            await asyncio.sleep(1)
                            
                await msg.edit(content=f"✅ **BERHASIL!** Bot udah baca gambar lu dan berhasil bikin **{created_count}** kategori/channel baru!")
                return
            except Exception as e:
                await msg.edit(content=f"❌ Gagal baca struktur gambar: {e}")
                return

        # --- BALASAN REPLY VN/DOKUMEN ---
        if not target_attachments and message.reference:
            try:
                replied_msg = await message.channel.fetch_message(message.reference.message_id)
                target_attachments = replied_msg.attachments
            except: pass

        if target_attachments:
            attachment = target_attachments[0]
            filename = attachment.filename.lower()
            
            if filename.endswith((".ogg", ".mp3", ".wav", ".m4a")):
                msg = await message.reply("🎙️ **Mendengarkan voice note...**")
                file_bytes = await attachment.read()
                transcribed = await transcribe_audio(file_bytes, attachment.filename)
                if transcribed.startswith("❌"): return await msg.edit(content=transcribed)
                await msg.edit(content=f"🎙️ **Transkrip:** *'{transcribed}'*\n\nMemproses jawaban...")
                t_lower = normalize_text(transcribed)
                
                if _re.search(r'(chan|kanal)', t_lower) and _re.search(r'(bik|buat|tambah|create|new)', t_lower):
                    return await msg.edit(content="⚙️ **Gunakan perintah teks** `@bot buatkan channel` untuk UI Builder.")
                elif _re.search(r'(role|peran|roll|rol)', t_lower) and _re.search(r'(atur|set|edit|kelola|ubah|izin|perm)', t_lower):
                    return await msg.edit(content="🛡️ **Gunakan perintah teks** `@bot atur role` untuk UI Role Manager.")
                
                action_data = await decide_action(transcribed) or {}
                if action_data.get("action") in ["multi_step", "discord_action"]:
                    res = await run_agent(transcribed, message.guild, channel_id=message.channel.id, user_id=message.author.id, user_name=message.author.display_name)
                    if res: return await send_long(message, res)
                resp = await execute_task("fast_chat", transcribed, NATURAL_SYSTEM, channel_id=message.channel.id, user_id=message.author.id, user_name=message.author.display_name)
                return await send_long(message, resp)
                
            elif filename.endswith((".pdf", ".txt", ".md", ".csv")):
                msg = await message.reply("📄 **Membaca dokumen...**")
                file_bytes = await attachment.read()
                text_content = extract_text_from_file(filename, file_bytes)
                if not text_content or text_content.startswith("❌"): return await msg.edit(content=text_content or "❌ Gagal baca dokumen.")
                await msg.edit(content="📄 **Dokumen dibaca!** Sedang menganalisis...")
                user_q = prompt if prompt else "Tolong rangkum dokumen ini."
                final_prompt = f"Berikut adalah isi dokumennya:\n---\n{text_content}\n---\n\nPertanyaan User: {user_q}"
                resp = await execute_task("fast_chat", final_prompt, NATURAL_SYSTEM, channel_id=message.channel.id, user_id=message.author.id, user_name=message.author.display_name)
                return await msg.edit(content=resp)

        if not prompt:
            return await message.reply("Iya Bang? Ada yang bisa gue bantu? Ketik pertanyaan lu, atau kirim VN/File sambil nge-tag gue ya.")
            
        p_lower = normalize_text(prompt)

        # --- SETUP VERIFIKASI CARTEL (VERSI DEWA) ---
        if p_lower.startswith(("setupverifycartel", "setupverify", "setup cartel")):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.author.guild_permissions.administrator and message.author.id != message.guild.owner_id:
                return await message.reply("❌ Cuma buat Admin/Owner server.")
            
            target_channel = message.channel
            if message.channel_mentions:
                target_channel = message.channel_mentions[0]
                
            msg = await message.reply(f"⏳ **Mengunci server & menyiapkan panel di {target_channel.mention}...**")
            
            # Bikin Role
            role_name = "WARGA CJNG"
            cartel_role = discord.utils.get(message.guild.roles, name=role_name)
            if not cartel_role:
                cartel_role = await message.guild.create_role(name=role_name, color=discord.Color.dark_red())
            
            # Lockdown (Kunci semua channel kecuali target, rules, welcome)
            locked_count = 0
            for channel in message.guild.channels:
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
                    if channel.id == target_channel.id or "rules" in channel.name.lower() or "welcome" in channel.name.lower():
                        continue
                    try:
                        await channel.set_permissions(message.guild.default_role, read_messages=False)
                        await channel.set_permissions(cartel_role, read_messages=True, send_messages=True)
                        locked_count += 1
                    except: pass
                    
            # Embed Panel DEWA
            embed = discord.Embed(
                title="🩸 VERIFIKASI CÁRTEL DE JALISCO 🩸",
                description="**Selamat datang di markas rahasia.**\n\nSebelum lu bisa masuk ke dalam lingkaran kami, lu **wajib** melakukan verifikasi. Ini bukan sekadar formalitas, ini adalah **sumpah setia** lu kepada Cártel.\n\nSilakan klik reaksi **✅** di bawah ini untuk membuka akses penuh.\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                color=discord.Color.dark_red()
            )
            if message.guild.icon: embed.set_thumbnail(url=message.guild.icon.url)
            # embed.set_image dihapus, ganti pakai file GIF lokal
            
            embed.add_field(name="🛡️ KEUNTUNGAN JADI WARGA", value="> 🚪 Akses ke **seluruh channel** rahasia.\n> 💬 Bisa ngobrol & mabar bareng member lain.\n> 📢 Dapet info event & giveaway eksklusif.\n> 🎭 Dapet role khusus **WARGA CJNG**.", inline=False)
            embed.add_field(name="📜 ATURAN MARKAS", value="> ❌ Dilarang **Toxic, SARA, Doxxing**.\n> ❌ Dilarang **Spam / Scam / Phishing**.\n> ❌ Dilarang promosi **Judi & Crypto Bodong**.\n> ⚠️ Sistem AI 24 jam memantau. **Pelanggaran = Mute/Ban.**", inline=False)
            embed.add_field(name="⚠️ PERINGATAN KERAS", value="> Jika lu mencabut reaksi ✅ ini, sistem akan **otomatis mencabut akses** lu ke semua channel.\n> Jangan coba-coba membuat onar di markas kami.", inline=False)
            embed.set_footer(text=f"Cártel de Jalisco | Blood In, Blood Out | {message.guild.name}", icon_url=message.guild.icon.url if message.guild.icon else None)
            
            # Path ke folder Download HP lu
            gif_path = "/data/data/com.termux/files/home/storage/shared/Download/giphy.gif"
            
            if os.path.exists(gif_path):
                file = discord.File(gif_path, filename="cartel.gif")
                panel_msg = await target_channel.send(embed=embed, file=file)
            else:
                await msg.edit(content="⚠️ File `giphy.gif` nggak ketemu di folder Download. Pastiin namanya bener.")
                panel_msg = await target_channel.send(embed=embed)
                
            await panel_msg.add_reaction("✅")
            await msg.edit(content=f"✅ **Verifikasi Cártel Aktif!**\n\n📍 Panel ditaruh di {target_channel.mention}.\n🔒 **{locked_count}** channel berhasil dikunci.")
            return
        # --- END VERIFIKASI CARTEL ---
        
        # --- PANEL_SETUP_MARKER ---
        if p_lower in ["panel", "setup", "dashboard", "menu setup"]:
            view = SetupPanelView()
            embed = discord.Embed(
                title="⚙️ PANEL SETUP SERVER",
                description="Klik tombol di bawah buat setup otomatis.\n\n**Pilih:**",
                color=discord.Color.gold()
            )
            await message.reply(embed=embed, view=view)
            return
        # --- END PANEL_SETUP_MARKER ---
        print(f"\n🔍 [DEBUG] Prompt Asli: '{prompt}' | Setelah Typo: '{p_lower}'")

        


        


        

        # --- INTERCEPTOR: CHANNEL PERMISSION (UI) ---
        if _re.search(r'setting(s)? channel|atur izin channel|izin channel|permission channel', p_lower):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.guild.me.guild_permissions.manage_channels: return await message.reply("❌ Bot butuh izin **Manage Channels**.")
            if not message.author.guild_permissions.administrator and message.author.id != message.guild.owner_id:
                return await message.reply("❌ Command ini cuma buat Admin/Owner server.")
                
            view = ChannelSelectForPermView(message.guild, message.guild.channels)
            embed = discord.Embed(
                title="⚙️ Channel Permission Editor",
                description="Pilih channel yang mau diatur izin role-nya dari menu di bawah ini.",
                color=discord.Color.blue()
            )
            await message.reply(embed=embed, view=view)
            return

        # --- COMMAND: SETUP SECURITY LOGS ---
        if any(x in p_lower for x in ["setup log security", "buat log keamanan", "atur log keamanan"]):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.author.guild_permissions.administrator and message.author.id != message.guild.owner_id:
                return await message.reply("❌ Command ini cuma buat Admin/Owner server.")
                
            msg = await message.reply("⏳ Membuat channel Security Logs...")
            
            log_ch_name = "🛡️・security-logs"
            category = discord.utils.get(message.guild.categories, name="📌 | INFORMATION") 
            if not category: category = discord.utils.get(message.guild.categories, name="LOGS & INFO")
            
            # Setelan Izin: Semua bisa LIAT, tapi cuma Staff yang bisa CHAT
            overwrites = {
                message.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                message.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Kasih akses CHAT ke role-role Staff (bisa lu tambahin sendiri di list ini)
            staff_roles = ["Admin", "Moderator", "Owner", "Co-Owner", "Staff"]
            for role_name in staff_roles:
                role = discord.utils.get(message.guild.roles, name=role_name)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            # Cek apakah channel udah ada
            log_ch = discord.utils.get(message.guild.text_channels, name=log_ch_name)
            if log_ch:
                # Kalau udah ada, UPDATE izinnya biar sesuai settingan baru
                await log_ch.edit(overwrites=overwrites)
            else:
                # Kalau belum ada, bikin baru
                log_ch = await message.guild.create_text_channel(log_ch_name, category=category, overwrites=overwrites)
                
            await msg.edit(content=f"✅ **BERHASIL!** Channel intelijen udah dibuat: {log_ch.mention}\nSemua link/gambar berbahaya yang dihapus bakal dicatat di sini.")
            return

        # --- INTERCEPTOR: UNMUTE / LEPAS TIMEOUT ---
        if p_lower.startswith(("unmute ", "lepas mute ", "lepas timeout ")):
            if not message.author.guild_permissions.administrator and message.author.id != message.guild.owner_id:
                return await message.reply("❌ Command ini cuma buat Admin/Owner server.")
            
            target = message.mentions[0] if message.mentions else None
            if not target:
                return await message.reply("❌ Tag orangnya dong Bang. Contoh: `@bot unmute @Budi`")
                
            try:
                await target.timeout(None, reason=f"Di-unmute manual oleh {message.author.name}")
                await message.reply(f"✅ Berhasil melepas Mute/Timeout dari {target.mention}!")
            except Exception as e:
                await message.reply(f"❌ Gagal: {e}")
            return

        # --- INTERCEPTOR: KATEGORI & MOVER (UI) ---
        if "kategori" in p_lower and any(x in p_lower for x in ["atur", "setting", "kelola", "edit"]):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.guild.me.guild_permissions.manage_channels: return await message.reply("❌ Bot butuh izin **Manage Channels**.")
            v = CategoryManagerView(message.guild)
            await message.reply(embed=v.get_embed(), view=v)
            return

        elif any(x in p_lower for x in ["geser channel", "pindah channel", "atur posisi"]):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.guild.me.guild_permissions.manage_channels: return await message.reply("❌ Bot butuh izin **Manage Channels**.")
            v = ChannelMoverView(message.guild)
            await message.reply(embed=v.get_embed(), view=v)
            return
            
        elif p_lower.startswith("buat kategori "):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            cat_name = prompt[14:].strip()
            try:
                await message.guild.create_category(cat_name)
                return await message.reply(f"✅ Kategori **{cat_name}** berhasil dibuat!")
            except Exception as e:
                return await message.reply(f"❌ Gagal: {e}")

        # --- INTERCEPTOR: CHANNEL BUILDER (UI) ---
        if any(x in p_lower for x in ["buat channel", "bikin channel", "tambah channel", "create channel"]):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.guild.me.guild_permissions.manage_channels: return await message.reply("❌ Bot butuh izin **Manage Channels**.")
            
            embed = discord.Embed(
                title="⚙️ Channel Builder", 
                description="Silakan atur channel baru lu lewat menu di bawah ini.\nPilih Kategori, Tipe, dan Privasi, lalu klik **Buat Channel**.", 
                color=discord.Color.blue()
            )
            view = ChannelBuilderView(message.guild.categories, message.guild.roles)
            await message.reply(embed=embed, view=view)
            return

        p_lower = normalize_text(prompt)

        # --- INTERCEPTOR: ROLE MANAGEMENT (UI & SET ROLE) ---
                
        if ("role" in p_lower or "peran" in p_lower) and "rules" not in p_lower and "setup" not in p_lower:
            # 1. UI Role Manager (Atur Izin)
            if any(x in p_lower for x in ["atur", "setting", "edit", "kelola", "permission", "izin"]):
                if not message.guild: return await message.reply("❌ Cuma bisa di server.")
                if not message.guild.me.guild_permissions.manage_roles: return await message.reply("❌ Bot butuh izin **Manage Roles**.")
                if not message.author.guild_permissions.administrator and message.author.id != message.guild.owner_id: return await message.reply("❌ Khusus Admin.")
                
                embed = discord.Embed(title="🛡️ Role Manager", description="Silakan pilih role yang ingin diatur izinnya dari menu di bawah.", color=discord.Color.blue())
                await message.reply(embed=embed, view=RoleSelectView(message.guild))
                return
                
            # 2. Set Role (Kasih Role ke Orang)
            elif any(p_lower.startswith(x + " ") or p_lower == x for x in ["kasih", "set", "beri", "ubah", "tambah", "jadiin", "assign"]):
                if not message.guild: return await message.reply("❌ Cuma bisa di server.")
                if not message.guild.me.guild_permissions.manage_roles: return await message.reply("❌ Bot butuh izin **Manage Roles**.")
                
                match1 = _re.search(r'(?:ubah|jadiin|ganti) (?:role )?(.+?) (?:jadi|ke) (.+)', p_lower)
                match2 = _re.search(r'(?:kasih|set|beri|tambah|assign) (?:role )?(.+?) (?:ke|untuk) (.+)', p_lower)
                match3 = _re.search(r'(?:kasih|set|beri|tambah|assign) (?:role )?(.+)', p_lower)

                if match1:
                    member_name = match1.group(1).strip()
                    role_name = match1.group(2).strip()
                elif match2:
                    role_name = match2.group(1).strip()
                    member_name = match2.group(2).strip()
                elif match3:
                    role_name = match3.group(1).strip()
                    member_name = "gw"
                else:
                    return await message.reply("❌ Format kurang jelas. Contoh: `@bot set role VIP ke Budi` atau `@bot ubah role gw jadi VIP`")
                    
                if not role_name or role_name in ["gw", "gue", "aku", "saya"]:
                    return await message.reply("❌ Nama role-nya mana Bang? Contoh: `@bot set role VIP ke Budi`")
                        
                role = discord.utils.find(lambda r: r.name.lower() == role_name, message.guild.roles)
                if not role:
                    try: role = await message.guild.create_role(name=role_name, color=discord.Color.random())
                    except: return await message.reply(f"❌ Role **{role_name}** nggak ketemu.")
                        
                member = discord.utils.find(lambda m: m.name.lower() == member_name or m.display_name.lower() == member_name or m.mention == member_name, message.guild.members)
                if not member:
                    if member_name in ["gw", "gue", "aku", "saya", "w"]:
                        member = message.author
                    else:
                        return await message.reply(f"❌ Member **{member_name}** nggak ketemu.")
                        
                if role >= message.guild.me.top_role:
                    return await message.reply(f"❌ Role **{role.name}** posisinya lebih tinggi dari role bot. Geser role bot ke atas.")
                    
                try:
                    await member.add_roles(role)
                    return await message.reply(f"✅ Berhasil ngasih role **{role.name}** ke **{member.display_name}**!")
                except Exception as e:
                    return await message.reply(f"❌ Gagal: {e}")
        # --- END ROLE INTERCEPTOR ---



        



        # COMMANDS
        if p_lower in ["help", "bantuan", "menu", "fitur", "bisa apa aja"]:
            view = HelpMenuView()
            await message.reply(embed=view.get_embed(), view=view)
            return

        elif p_lower in ["reset", "hapus memori", "clear"]:
            if not message.author.guild_permissions.manage_messages and message.author.id != message.guild.owner_id:
                return await message.reply("❌ Khusus Admin.")
            delete_chat_history(message.channel.id)
            await message.reply("🧹 Memori dihapus.")
            return

        elif p_lower in ["stats", "statistik"]:
            if not message.author.guild_permissions.administrator and message.author.id != message.guild.owner_id:
                return await message.reply("❌ Khusus Admin.")
            data = get_bot_stats()
            if not data: return await message.reply("❌ Gagal ambil data.")
            embed = discord.Embed(title="📊 Statistik Bot", color=discord.Color.green())
            embed.add_field(name="Interaksi", value=f"{data['total_chat']} pesan")
            embed.add_field(name="Channel", value=f"{data['total_channels']} channel")
            embed.add_field(name="Request API", value=f"{data['total_requests']} req")
            await message.reply(embed=embed)
            return

        elif p_lower in ["buat panel tiket", "panel tiket", "bikin tiket", "buat tiket"]:
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            embed = discord.Embed(title="🎫 Pusat Bantuan (Ticket)", description="Klik tombol di bawah ini untuk menghubungi Admin/Staff.\nTiket akan dibuat secara privat.", color=discord.Color.green())
            await message.reply(embed=embed, view=TicketCreateView())
            return

        elif p_lower.startswith("buat poll ") or p_lower.startswith("bikin poll "):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            # Format: @bot buat poll Pertanyaan? | Opsi 1 | Opsi 2
            args = prompt.split("poll ", 1)[-1].split("|")
            if len(args) < 3:
                return await message.reply("❌ Format salah. Contoh: `@bot buat poll Makan apa? | Nasi Goreng | Mie Ayam | Bakso`")
                
            question = args[0].strip()
            options = [opt.strip() for opt in args[1:]]
            if len(options) > 10:
                return await message.reply("❌ Maksimal 10 opsi poll.")
                
            embed = discord.Embed(title=f"📊 Poll: {question}", color=discord.Color.blue())
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            desc = ""
            for i, opt in enumerate(options):
                desc += f"{emojis[i]} {opt}\n"
            embed.description = desc
            embed.set_footer(text=f"Polling dibuat oleh {message.author.display_name}")
            
            poll_msg = await message.channel.send(embed=embed)
            for i in range(len(options)):
                await poll_msg.add_reaction(emojis[i])
            try: await message.delete()
            except: pass
            return

        elif any(x in p_lower for x in ["setup server", "buatkan server lengkap", "buatkan logs"]):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.guild.me.guild_permissions.manage_roles or not message.guild.me.guild_permissions.manage_channels:
                return await message.reply("❌ Bot butuh izin **Manage Roles** & **Manage Channels**.")
            
            embed = discord.Embed(
                title="🏗️ Rencana Pembangunan Server",
                description="Bot bakal bikin sistem server dengan **Kuncian Keamanan (Gatekeeping)**.\n\n🔒 **Public:** Member baru cuma bisa liat `#welcome`, `#rules`, `#announcements`.\n✅ **Verifikasi:** Mereka harus klik tombol di `#welcome` buat dapet Role `Member`.\n🚪 **Private:** Setelah verifikasi, semua channel (Chat, Voice, dll) baru kebuka.",
                color=discord.Color.gold()
            )
            embed.add_field(name="👤 Role Baru", value="`Admin`, `Member`, `Muted`", inline=True)
            embed.add_field(name="📂 Kategori", value="`11 Kategori` (60+ Channel)", inline=True)
            embed.add_field(name="📝 Pesan Otomatis", value="Pesan Rules & Welcome udah otomatis diisi.", inline=False)
            
            view = SetupConfirmView(message.guild)
            await message.reply(embed=embed, view=view)
            return

        elif p_lower.startswith("take role "):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.guild.me.guild_permissions.manage_roles: return await message.reply("❌ Bot butuh izin **Manage Roles**.")
            keyword = "take role "
            idx = p_lower.find(keyword)
            role_name = prompt[idx + len(keyword):].strip() if idx != -1 else "Member"
            if not role_name: return await message.reply("❌ Format salah. Contoh: `@bot take role Gamer`")
            
            role = discord.utils.get(message.guild.roles, name=role_name)
            if not role:
                try:
                    role = await message.guild.create_role(name=role_name, color=discord.Color.random())
                    await message.reply(f"⚙️ Role **{role.name}** belum ada, gue bikinin dulu ya!")
                except Exception as e:
                    return await message.reply(f"❌ Gagal bikin role: {e}")

            embed = discord.Embed(title=f"🎭 Ambil Role {role.name}", description=f"Klik tombol di bawah buat **mengambil** atau **mencopot** role ini.", color=discord.Color.blue())
            view = discord.ui.View()
            view.add_item(TakeRoleButton(role))
            await message.reply(embed=embed, view=view)
            return

        # --- INTERCEPTOR: MANAJEMEN ROLE EKSPLISIT (ANTI NGELES) ---
        elif p_lower.startswith(("kasih role ", "set role ", "beri role ", "tambah role ")):
            if not message.guild: return await message.reply("❌ Cuma bisa di server.")
            if not message.guild.me.guild_permissions.manage_roles: return await message.reply("❌ Bot butuh izin **Manage Roles**.")
            
            # Format: kasih role [nama role] ke [nama member]
            match = _re.search(r'(?:kasih|set|beri|tambah) role (.+) ke (.+)', p_lower)
            if not match:
                return await message.reply("❌ Format salah. Contoh: `@bot kasih role VIP ke Budi`")
            
            role_name = match.group(1).strip()
            member_name = match.group(2).strip()
            
            # Cari role
            role = discord.utils.find(lambda r: r.name.lower() == role_name, message.guild.roles)
            if not role:
                try: role = await message.guild.create_role(name=role_name, color=discord.Color.random())
                except: return await message.reply(f"❌ Role **{role_name}** nggak ketemu.")
                    
            # Cari member
            member = discord.utils.find(lambda m: m.name.lower() == member_name or m.display_name.lower() == member_name or m.mention == member_name, message.guild.members)
            if not member:
                if member_name in ["gw", "gue", "aku", "saya", "w"]:
                    member = message.author
                else:
                    return await message.reply(f"❌ Member **{member_name}** nggak ketemu.")
                    
            if role >= message.guild.me.top_role:
                return await message.reply(f"❌ Role **{role.name}** posisinya lebih tinggi dari role bot. Geser role bot ke atas.")
                
            try:
                await member.add_roles(role)
                return await message.reply(f"✅ Berhasil ngasih role **{role.name}** ke **{member.display_name}**!")
            except Exception as e:
                return await message.reply(f"❌ Gagal: {e}")

        # AI ROUTER FALLBACK
        try:
            asyncio.create_task(extract_facts_async(message.author.id, message.author.display_name, prompt))
            action_data = await decide_action(prompt) or {}
            action_type = action_data.get("action", "chat")
            
            if action_type == "search":
                query = action_data.get("query", prompt)
                msg = await message.reply(f"🔍 **Mencari: {query}...**")
                res = await research_web(query, channel_id=message.channel.id)
                return await msg.edit(content=res)
            elif action_type == "scrape":
                url = action_data.get("url")
                msg = await message.reply(f"📄 **Membuka: {url}**")
                res = await summarize_url(url, channel_id=message.channel.id)
                return await msg.edit(content=res)
            elif action_type in ["weather", "dictionary", "news", "ip_info"]:
                pm = {"weather": "city", "dictionary": "word", "news": "query", "ip_info": "ip"}
                val = action_data.get(pm[action_type], prompt)
                fm = {"weather": get_weather, "dictionary": get_dictionary, "news": get_news, "ip_info": get_ip_info}
                async with message.channel.typing():
                    res = await fm[action_type](val)
                return await send_long(message, res)
            elif action_type == "discord_action":
                if not message.guild: return await message.reply("❌ Cuma bisa di server.")
                async with message.channel.typing():
                    res = await agent_action(message.guild, prompt, message.channel.id)
                if res: return await send_long(message, res)
                return await message.reply("❌ Gagal eksekusi. Contoh: `bikin channel #test`")
            elif action_type == "multi_step":
                async with message.channel.typing():
                    res = await run_agent(prompt, message.guild, channel_id=message.channel.id, user_id=message.author.id, user_name=message.author.display_name)
                if res: return await send_long(message, res)
                return await send_long(message, await execute_task("fast_chat", prompt, NATURAL_SYSTEM, channel_id=message.channel.id, user_id=message.author.id, user_name=message.author.display_name))
            else:
                async with message.channel.typing():
                    realtime = ["cuaca", "berita", "harga", "jadwal", "bmkg", "saham", "kripto", "bitcoin"]
                    if any(k in prompt.lower() for k in realtime):
                        msg = await message.reply("🔍 **Mencari info terbaru...**")
                        ok, sr = await execute_tool("search_web", message.guild, query=prompt)
                        if ok and sr:
                            sys_p = "Rangkum hasil pencarian dengan bahasa Indonesia santai. Jangan ngarang."
                            res = await execute_task("fast_chat", f"Hasil:\n{sr}\n\nPertanyaan: {prompt}", sys_p, channel_id=message.channel.id, user_id=message.author.id, user_name=message.author.display_name)
                            return await msg.edit(content=res)
                        return await msg.edit(content="❌ Gagal mencari.")
                    
                    resp = await execute_task("fast_chat", prompt, NATURAL_SYSTEM, channel_id=message.channel.id, user_id=message.author.id, user_name=message.author.display_name)
                    return await send_long(message, resp)
        except Exception as e:
            print(f"❌ Error: {e}")
            return await message.reply("⏱️ Waduh error, coba lagi bentar.")

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN: bot.run(TOKEN)
