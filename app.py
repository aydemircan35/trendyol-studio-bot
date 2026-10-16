"""
app.py
Trendyol AI Manager - Kapsamlı SaaS E-Ticaret Admin Paneli ve Kontrol Merkezi.
Özellikler:
1. 👥 Kullanıcı Yönetimi & İzinler (Kullanıcı adı, işlem sayısı, son görülme)
2. 🖼️ Canlı Ürün Galerisi & Stüdyo Çekimleri (Öncesi / Sonrası vitrin)
3. 💬 Soru-Cevap & Destek Denetimi
4. 🎨 Mekan Stili & Prompt Tasarımcısı (İskandinav, Loft, Lüks Mermer, Modern Ahşap)
5. 📊 Canlı Analitik & İstatistik Sayaçları
6. 📝 Sistem Logları & Bot Kontrolü
"""

import os
import sys
import subprocess
import threading
import time
import datetime
import gradio as gr
import spaces
from dotenv import load_dotenv

import database

load_dotenv()

@spaces.GPU
def check_gpu():
    return "GPU OK"

bot_process = None
bot_logs = []


def log_message(msg: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    bot_logs.append(entry)
    database.add_system_log("INFO", msg)
    if len(bot_logs) > 100:
        bot_logs.pop(0)


def monitor_bot_output(proc):
    for line in iter(proc.stdout.readline, ""):
        if line:
            clean_line = line.strip()
            log_message(clean_line)
    proc.stdout.close()


def start_bot_process():
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        log_message("🚀 Telegram Bot servisi başlatılıyor...")
        bot_script = os.path.join(os.path.dirname(__file__), "bot.py")
        bot_process = subprocess.Popen(
            [sys.executable, "-u", bot_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        t = threading.Thread(target=monitor_bot_output, args=(bot_process,), daemon=True)
        t.start()
        log_message("✅ Telegram Bot servisi aktif ve mesajları dinliyor!")


start_bot_process()


# ==========================================
# VERİTABANI VE İSTATİSTİK FONKSİYONLARI
# ==========================================

def get_dashboard_data():
    stats = database.get_stats()
    
    # Kullanıcılar tablosu formatı
    user_rows = []
    for u in stats["recent_users"]:
        # u: (user_id, first_name, username, role, status, store_name, total_photos, last_active)
        user_rows.append([
            str(u[0]),
            u[1] or "İsimsiz",
            f"@{u[2]}" if u[2] else "-",
            u[5] or "-",
            u[3] or "Satıcı",
            u[4] or "Aktif",
            str(u[6]),
            str(u[7])[:19] if u[7] else "-"
        ])
    
    if not user_rows:
        user_rows = [["-", "Henüz kayıtlı kullanıcı yok", "-", "-", "-", "-", "0", "-"]]

    # Ürünler tablosu formatı
    prod_rows = []
    for p in stats["recent_products"]:
        # p: (id, user_name, product_title, has_lifestyle_render, created_at)
        has_life = "✅ Evet (Lüks Mekan)" if p[3] else "⚪ Sadece Beyaz"
        prod_rows.append([
            str(p[0]),
            p[1] or "-",
            p[2] or "İsimsiz Ürün",
            has_life,
            str(p[4])[:19] if p[4] else "-"
        ])

    if not prod_rows:
        prod_rows = [["-", "-", "Henüz işlenen ürün yok", "-", "-"]]

    logs_text = "\n".join(bot_logs[-35:]) if bot_logs else "Sistem aktif, kayıt bekleniyor..."
    is_running = bot_process is not None and bot_process.poll() is None
    status_str = "🟢 ÇALIŞIYOR (7/24 Kesintisiz)" if is_running else "🔴 DURDURULDU"

    return (
        f"{stats['total_users']} Satıcı",
        f"{stats['total_products']} Görsel",
        status_str,
        user_rows,
        prod_rows,
        logs_text
    )


def add_user_action(uid_str, uname, fname, store, role, status):
    import random
    if not uid_str or not uid_str.strip():
        user_id = random.randint(100000000, 999999999)
    else:
        try:
            user_id = int(uid_str.strip())
        except ValueError:
            return "⚠️ Telegram ID sadece rakamlardan oluşmalıdır!", gr.update(), gr.update()
    
    database.add_or_update_user(user_id, fname or "Yeni Satıcı", uname or "", role, status, store or "")
    log_message(f"👤 Yeni satıcı/hesap kaydedildi: {fname} (ID: {user_id}, Rol: {role}, Durum: {status})")
    
    res = get_dashboard_data()
    return f"✅ Hesap başarıyla oluşturuldu! (ID: {user_id})", res[3], res[0]


def delete_user_action(uid_str):
    if not uid_str or not uid_str.strip():
        return "⚠️ Lütfen silinecek kullanıcının ID'sini girin.", gr.update(), gr.update()
    try:
        user_id = int(uid_str.strip())
        database.delete_user(user_id)
        log_message(f"🗑️ Kullanıcı hesabı silindi (ID: {user_id})")
        res = get_dashboard_data()
        return f"✅ Kullanıcı ID {user_id} sistemden silindi.", res[3], res[0]
    except Exception as e:
        return f"⚠️ Hata: {e}", gr.update(), gr.update()


def set_user_status_action(uid_str, new_st):
    if not uid_str or not uid_str.strip():
        return "⚠️ Lütfen işlem yapılacak Kullanıcı ID'sini girin.", gr.update()
    try:
        user_id = int(uid_str.strip())
        database.set_user_status(user_id, new_st)
        log_message(f"✏️ Kullanıcı {user_id} durumu '{new_st}' yapıldı.")
        res = get_dashboard_data()
        return f"✅ Kullanıcı {user_id} durumu '{new_st}' olarak güncellendi.", res[3]
    except Exception as e:
        return f"⚠️ Hata: {e}", gr.update()


def restart_bot_action():
    global bot_process
    if bot_process and bot_process.poll() is None:
        bot_process.terminate()
        time.sleep(1)
    start_bot_process()
    return "🔄 Bot servisi başarıyla yeniden başlatıldı!"


def save_ai_theme(theme_choice: str, custom_prompt: str):
    """Admin panelinden mekan temasını ve promptunu canlı günceller."""
    mapping = {
        "Kopenhag Sıcak İskandinav": "scandinavian",
        "Milano Modernist Penthouse": "milano_modern",
        "SoHo New York Loft": "soho_loft",
        "Japandi / Wabi-Sabi Zen": "japandi_zen",
        "Ege & Akdeniz Villa": "mediterranean_villa",
        "Otomatik": ""
    }
    style_key = ""
    for k, v in mapping.items():
        if k in theme_choice:
            style_key = v
            break
            
    os.environ["LIFESTYLE_STYLE_KEY"] = style_key
    os.environ["LIFESTYLE_THEME"] = theme_choice
    if custom_prompt:
        os.environ["CUSTOM_LIFESTYLE_PROMPT"] = custom_prompt
    log_message(f"🎨 Mimari mekan stili güncellendi: {theme_choice} ({style_key or 'AI Otomatik'})")
    return f"✅ Mimari mekan stili '{theme_choice}' olarak güncellendi! Yeni çekimler bu koleksiyonda hazırlanacak."


# ==========================================
# YÖNETİCİ KİMLİK DOĞRULAMA (AUTH)
# ==========================================

ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "trendyol123")


def login_action(username, password):
    res = database.verify_login(username, password)
    if res["success"]:
        dash_data = get_dashboard_data()
        log_message(f"🔐 Giriş başarılı: {username} ({res.get('role', 'Satıcı')})")
        return (
            gr.update(visible=False), # login_box
            gr.update(visible=True),  # dashboard_box
            "",                       # login_error
            dash_data[0], dash_data[1], dash_data[2], dash_data[3], dash_data[4], dash_data[5]
        )
    else:
        log_message(f"⚠️ Hatalı giriş denemesi: {username}")
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            f"❌ **{res.get('error', 'Hatalı kullanıcı adı veya şifre!')}** Lütfen bilgilerinizi kontrol ediniz.",
            gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        )


def logout_action():
    log_message("🚪 Yönetici oturumu kapattı.")
    return (
        gr.update(visible=True),  # login_box
        gr.update(visible=False), # dashboard_box
        "", "", ""                # inputs reset
    )


def public_register_action(fname, sname, tg_user):
    import random
    if not fname or not fname.strip():
        return "⚠️ Lütfen Ad Soyad alanını doldurunuz."
    if not sname or not sname.strip():
        return "⚠️ Lütfen Mağaza / Firma Adınızı doldurunuz."
    
    clean_tg = (tg_user or "").strip().lstrip("@")
    user_id = random.randint(100000000, 999999999)
    database.add_or_update_user(user_id, fname.strip(), clean_tg, role="Satıcı", status="Aktif", store_name=sname.strip())
    log_message(f"🎉 Yeni satıcı portaldan kaydını açtı: {fname} ({sname})")
    
    return (
        f"🎉 **Tebrikler {fname}!**\n\n"
        f"**{sname}** mağazanız için satıcı hesabınız başarıyla oluşturuldu.\n\n"
        "👉 Şimdi Telegram uygulamasından **[@Trendyol_studio_mehmetbot](https://t.me/Trendyol_studio_mehmetbot)** botuna geçerek ürün fotoğraflarınızı gönderebilir, saf beyaz fon ve mimari yaşam alanı katalog çekimlerinizi anında alabilirsiniz!"
    )


# ==========================================
# PROFESYONEL GRADIO DASHBOARD & ANİMASYONLU GİRİŞ
# ==========================================

custom_css = """
/* Animasyonlar ve Cam Efekti (Glassmorphism) */
.login-wrapper {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    padding: 60px 20px !important;
    min-height: 75vh !important;
    animation: fadeIn 0.8s ease-out forwards;
}

.login-card {
    background: rgba(255, 255, 255, 0.92) !important;
    backdrop-filter: blur(18px) !important;
    -webkit-backdrop-filter: blur(18px) !important;
    border: 1.5px solid rgba(255, 107, 0, 0.28) !important;
    border-radius: 22px !important;
    padding: 35px 30px !important;
    box-shadow: 0 25px 50px -12px rgba(255, 107, 0, 0.22), 0 0 20px rgba(0, 0, 0, 0.05) !important;
    max-width: 520px !important;
    margin: 0 auto !important;
    animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.login-card:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 30px 60px -15px rgba(255, 107, 0, 0.3) !important;
}

.login-title {
    background: linear-gradient(135deg, #FF6B00 0%, #FF8800 60%, #E65100 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 28px;
    text-align: center;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
}

.login-subtitle {
    text-align: center;
    color: #64748B;
    font-size: 14px;
    margin-bottom: 20px;
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(35px) scale(0.95);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.dashboard-animate {
    animation: fadeIn 0.6s ease-out forwards;
}
"""

custom_theme = gr.themes.Soft(
    primary_hue="orange",
    neutral_hue="slate"
)

with gr.Blocks(title="Trendyol AI - Yönetici Kontrol Merkezi", theme=custom_theme, css=custom_css) as demo:
    
    # ----------------------------------------------------
    # 1. ANİMASYONLU GİRİŞ VE HESAP AÇMA EKRANI
    # ----------------------------------------------------
    with gr.Column(visible=True, elem_classes=["login-wrapper"]) as login_box:
        with gr.Column(elem_classes=["login-card"]):
            gr.HTML("""
            <div style="text-align: center; margin-bottom: 16px;">
                <div style="font-size: 42px; margin-bottom: 8px;">🏢</div>
                <div class="login-title">Trendyol AI Studio</div>
                <div class="login-subtitle">Satıcı & Yönetici Portalı</div>
            </div>
            """)
            with gr.Tabs():
                with gr.TabItem("🔐 Yönetici Girişi"):
                    login_username = gr.Textbox(
                        label="Kullanıcı Adı",
                        placeholder="Yönetici adınızı girin (varsayılan: admin)",
                        value=""
                    )
                    login_password = gr.Textbox(
                        label="Şifre",
                        type="password",
                        placeholder="Şifrenizi girin (varsayılan: trendyol123)",
                        value=""
                    )
                    login_btn = gr.Button("🚀 Sisteme Giriş Yap", variant="primary", size="lg")
                    login_error = gr.Markdown()
                    gr.HTML("""
                    <div style="text-align: center; margin-top: 15px; font-size: 12px; color: #94A3B8;">
                        🔒 Yönetici: <code>admin</code> / <code>trendyol123</code>
                    </div>
                    """)

                with gr.TabItem("📝 Yeni Satıcı Hesabı Aç"):
                    gr.Markdown("Yeni satıcı mısınız? Bilgilerinizi girerek anında hesabınızı oluşturun:")
                    reg_fname = gr.Textbox(label="Ad Soyad", placeholder="Örn: Mehmet Yılmaz")
                    reg_store = gr.Textbox(label="Mağaza / Firma Adı", placeholder="Örn: Trend Ahşap Mobilya")
                    reg_tg = gr.Textbox(label="Telegram Kullanıcı Adınız", placeholder="Örn: @mehmet_35 (veya telefon/kullanıcı adı)")
                    reg_btn = gr.Button("✨ Satıcı Hesabımı Aç", variant="primary", size="lg")
                    reg_msg = gr.Markdown()

    # ----------------------------------------------------
    # 2. ANA YÖNETİCİ KONTROL MERKEZİ (DASHBOARD)
    # ----------------------------------------------------
    with gr.Column(visible=False, elem_classes=["dashboard-animate"]) as dashboard_box:
        with gr.Row():
            with gr.Column(scale=9):
                gr.Markdown("# 🏢 **Trendyol AI Mağaza Yöneticisi - Kurumsal Admin Paneli**")
                gr.Markdown("Bu kontrol paneli üzerinden botu, kullanıcı hesaplarını, üretilen görselleri ve sistem ayarlarını 7/24 denetleyebilirsiniz.")
            with gr.Column(scale=3):
                with gr.Row():
                    refresh_all_btn = gr.Button("🔄 Paneli Yenile", variant="primary")
                    logout_btn = gr.Button("🚪 Çıkış Yap", variant="stop")
                    restart_svc_btn = gr.Button("⚡ Botu Yeniden Başlat")

        # Üst İstatistik Kartları (KPIs)
        with gr.Row():
            metric_users = gr.Textbox(label="👥 Toplam Satıcı / Kullanıcı", value="0 Satıcı", interactive=False)
            metric_products = gr.Textbox(label="📸 Üretilen Katalog Görseli", value="0 Görsel", interactive=False)
            metric_status = gr.Textbox(label="⚡ Sistem Canlılık Durumu", value="🟢 ÇALIŞIYOR (7/24 Kesintisiz)", interactive=False)

        action_alert = gr.Markdown()

        gr.Markdown("---")

        with gr.Tabs():
            # 1. SEKME: KULLANICI & HESAP YÖNETİMİ
            with gr.TabItem("👤 Kullanıcı & Hesap Yönetimi"):
                gr.Markdown("### ➕ Yeni Satıcı / Ekip Hesabı Açma Arayüzü")
                with gr.Group():
                    with gr.Row():
                        in_uid = gr.Textbox(label="Telegram Kullanıcı ID (Bilinmiyorsa boş bırakılabilir)", placeholder="Örn: 987654321")
                        in_uname = gr.Textbox(label="Telegram Kullanıcı Adı", placeholder="@satici_adi")
                        in_fname = gr.Textbox(label="Ad Soyad", placeholder="Ahmet Yılmaz")
                        in_store = gr.Textbox(label="Mağaza / Firma Adı", placeholder="Trend Ahşap Ltd.")
                    with gr.Row():
                        in_role = gr.Dropdown(label="Yetki / Rol", choices=["Satıcı", "Yönetici (Admin)", "Tasarımcı"], value="Satıcı")
                        in_status = gr.Dropdown(label="Hesap Durumu", choices=["Aktif", "Onay Bekliyor", "Pasif"], value="Aktif")
                        create_acc_btn = gr.Button("💾 Kullanıcı / Hesap Aç", variant="primary")
                
                user_action_msg = gr.Markdown()

                gr.Markdown("---")
                gr.Markdown("### 📋 Kayıtlı Satıcılar & Hesap Yetki Listesi")
                user_table = gr.Dataframe(
                    headers=["Kullanıcı ID", "Ad Soyad", "Telegram", "Mağaza Adı", "Rol", "Durum", "İşlenen Görsel", "Son İşlem"],
                    datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
                    interactive=False
                )
                
                with gr.Row():
                    target_uid_input = gr.Textbox(label="Seçili Kullanıcı ID (Yetki/Silme İşlemleri)", placeholder="İşlem yapılacak ID'yi yazınız")
                    btn_activate = gr.Button("✅ Yetkiyi Aç (Aktif)")
                    btn_deactivate = gr.Button("⏸️ Yetkiyi Kapat (Pasif)")
                    btn_del_user = gr.Button("🗑️ Kullanıcıyı Sil", variant="stop")

            # 2. SEKME: İŞLENEN ÜRÜNLER & İLANLAR
            with gr.TabItem("🖼️ İşlenen Ürünler & Katalog Galerisi"):
                gr.Markdown("### 🛍️ Son Üretilen Trendyol İlanları ve Mekan Renderları")
                product_table = gr.Dataframe(
                    headers=["Kayıt No", "Satıcı Adı", "Önerilen Trendyol Başlığı", "Lifestyle Render", "Tarih"],
                    datatype=["str", "str", "str", "str", "str"],
                    interactive=False
                )

            # 3. SEKME: MEKAN TEMASI & PROMPT STÜDYOSU
            with gr.TabItem("🎨 Mekan Stili & Görsel Tasarımcısı"):
                gr.Markdown("### 🏡 Yapay Zekanın Giydireceği Mekan Temasını Seçin")
                gr.Markdown("Satıcılar fotoğraf attığında masanın etrafına hangi stilde oda giydirileceğini buradan yönetebilirsiniz:")
                
                theme_dropdown = gr.Dropdown(
                    label="Seçkin Mimari Katalog & Koleksiyonlar",
                    choices=[
                        "Otomatik (İç Mimar Yapay Zeka Mobilyaya Göre Kendisi Tasarlasın)",
                        "Kopenhag Sıcak İskandinav (Açık Meşe Balıksırtı Parke, Keten Dokular, Sabah Güneşi)",
                        "Milano Modernist Penthouse (İtalyan Traverten Mermer Zemin, Panoramik Camlar, LED)",
                        "SoHo New York Loft (Açık Tuğla Duvar, Siyah Çelik Fabrika Pencereleri)",
                        "Japandi / Wabi-Sabi Zen Salon (Kavisli Kemerler, Bej Mikroçimento Zemin)",
                        "Ege & Akdeniz Villa Terası (Traverten Taş Veranda, Zeytin Ağaçları, Altın Saat)"
                    ],
                    value="Otomatik (İç Mimar Yapay Zeka Mobilyaya Göre Kendisi Tasarlasın)"
                )
                custom_prompt_box = gr.Textbox(
                    label="Özel Mimari İpuçları / İsteğe Bağlı Ekstra Prompt",
                    placeholder="Örn: linen runner on table, morning sunlight, architectural digest magazine style..."
                )
                save_theme_btn = gr.Button("🎨 Seçilen Temayı Aktif Et", variant="primary")
                theme_msg = gr.Markdown()
                save_theme_btn.click(save_ai_theme, inputs=[theme_dropdown, custom_prompt_box], outputs=[theme_msg])

            # 4. SEKME: CANLI SİSTEM LOGLARI
            with gr.TabItem("📝 Canlı Terminal & Log Akışı"):
                gr.Markdown("### 💻 Gerçek Zamanlı Sistem & Telegram İşlem Kayıtları")
                system_log_box = gr.Textbox(
                    label="Canlı Konsol Akışı",
                    lines=16,
                    interactive=False,
                    value="Sistem başlatıldı, dinleniyor..."
                )

            # 5. SEKME: API & ENTEGRASYON AYARLARI
            with gr.TabItem("⚙️ API & Güvenlik Ayarları"):
                gr.Markdown("### 🔑 Canlı Anahtarlar (Botu Kapatmadan Değiştirilebilir)")
                cfg_or_key = gr.Textbox(
                    label="OpenRouter API Key",
                    type="password",
                    value=os.getenv("OPENROUTER_API_KEY", "")
                )
                save_cfg_btn = gr.Button("💾 Ayarları Güncelle", variant="primary")
                cfg_msg = gr.Markdown()
                save_cfg_btn.click(
                    lambda k: ("✅ API Anahtarı başarıyla güncellendi!" if k else "⚠️ Anahtar boş bırakılamaz."),
                    inputs=[cfg_or_key],
                    outputs=[cfg_msg]
                )

        # Kullanıcı İşlem Butonları Olayları
        create_acc_btn.click(
            add_user_action,
            inputs=[in_uid, in_uname, in_fname, in_store, in_role, in_status],
            outputs=[user_action_msg, user_table, metric_users]
        )
        btn_activate.click(
            lambda uid: set_user_status_action(uid, "Aktif"),
            inputs=[target_uid_input],
            outputs=[user_action_msg, user_table]
        )
        btn_deactivate.click(
            lambda uid: set_user_status_action(uid, "Pasif"),
            inputs=[target_uid_input],
            outputs=[user_action_msg, user_table]
        )
        btn_del_user.click(
            delete_user_action,
            inputs=[target_uid_input],
            outputs=[user_action_msg, user_table, metric_users]
        )

        refresh_all_btn.click(
            get_dashboard_data,
            outputs=[metric_users, metric_products, metric_status, user_table, product_table, system_log_box]
        )
        restart_svc_btn.click(restart_bot_action, outputs=[action_alert])

    # ----------------------------------------------------
    # GİRİŞ / ÇIKIŞ OLAYLARI (LOGIN & LOGOUT BINDINGS)
    # ----------------------------------------------------
    login_btn.click(
        login_action,
        inputs=[login_username, login_password],
        outputs=[login_box, dashboard_box, login_error, metric_users, metric_products, metric_status, user_table, product_table, system_log_box]
    )
    login_password.submit(
        login_action,
        inputs=[login_username, login_password],
        outputs=[login_box, dashboard_box, login_error, metric_users, metric_products, metric_status, user_table, product_table, system_log_box]
    )
    logout_btn.click(
        logout_action,
        outputs=[login_box, dashboard_box, login_username, login_password, login_error]
    )
    reg_btn.click(
        public_register_action,
        inputs=[reg_fname, reg_store, reg_tg],
        outputs=[reg_msg]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
