import ast
import re

with open("bot.py", "r") as f:
    content = f.read()

# 1. AMBIL BLOK RULES YANG LAMA
start_marker = "        # --- INTERCEPTOR: AUTO GENERATE RULES ---"
end_marker = "        # --- INTERCEPTOR: KATEGORI & MOVER (UI) ---"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print("❌ Gagal nemu blok Rules lama. Mungkin belum ke-patch.")
    exit(1)

# Ekstrak blok Rules-nya
rules_block = content[start_idx:end_idx]
# Hapus dari posisi lama
content = content[:start_idx] + content[end_idx:]

# 2. SISIPKAN KE PALING ATAS (Setelah handler Help/Reset/Stats)
# Kita cari handler 'help' sebagai patokan awal yang aman
anchor_help = 'if p_lower in ["help", "bantuan", "menu", "fitur", "bisa apa aja"]:'

# Cari akhir dari handler help (kira-kira diakhiri dengan return)
# Biar gampang, kita cari posisi interceptor ROLE yang lama
anchor_role = "        # --- INTERCEPTOR: MANAJEMEN ROLE EKSPLISIT ---"
if anchor_role not in content:
    anchor_role = "        # --- INTERCEPTOR: ROLE MANAGEMENT ---"

if anchor_role in content:
    # Sisipkan rules block sebelum Role Interceptor
    content = content.replace(anchor_role, rules_block + anchor_role, 1)
    print("✅ Blok Rules dipindahkan ke paling atas (sebelum Role Interceptor).")
else:
    print("⚠️ Gagal nemu anchor Role. Coba cari manual.")

# 3. KARENA KATA "setup" MIRIP "set", KITA GANTI TRIGGER JADI LEBIH SPESIFIK
# Biar nggak nabrak kata "set" di role
content = content.replace(
    'if any(x in p_lower for x in ["setup rules", "buat rules", "bikin rules", "atur rules"]):',
    'if any(x in p_lower for x in ["setup rules", "buat rules", "bikin rules", "atur rules", "rules server", "peraturan server"]):'
)

with open("bot.py", "w") as f:
    f.write(content)

try:
    ast.parse(content)
    print("✅ Syntax bot.py 100% OK!")
except Exception as e:
    print(f"❌ Syntax Error: {e}")
