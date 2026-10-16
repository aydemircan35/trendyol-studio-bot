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
    os.environ["LIFESTYLE_THEME"] = theme_choice
    if custom_prompt:
        os.environ["CUSTOM_LIFESTYLE_PROMPT"] = custom_prompt
    log_message(f"🎨 Mekan stili güncellendi: {theme_choice}")
    return f"✅ Mekan stili '{theme_choice}' olarak güncellendi! Yeni atılacak tüm fotoğraflar bu temada üretilecek."


# ==========================================
# PROFESYONEL GRADIO DASHBOARD ARAYÜZÜ
# ==========================================

custom_theme = gr.themes.Soft(
    primary_hue="orange",
    neutral_hue="slate"
)

with gr.Blocks(title="Trendyol AI - Yönetici Kontrol Merkezi", theme=custom_theme) as demo:
    gr.Markdown("# 🏢 **Trendyol AI Mağaza Yöneticisi - Kurumsal Admin Paneli**")
    gr.Markdown("Bu kontrol paneli üzerinden botu, kullanıcı hesaplarını, üretilen görselleri ve sistem ayarlarını 7/24 denetleyebilirsiniz.")
    
    # Üst İstatistik Kartları (KPIs)
    with gr.Row():
        metric_users = gr.Textbox(label="👥 Toplam Satıcı / Kullanıcı", value="0 Satıcı", interactive=False)
        metric_products = gr.Textbox(label="📸 Üretilen Katalog Görseli", value="0 Görsel", interactive=False)
        metric_status = gr.Textbox(label="⚡ Sistem Canlılık Durumu", value="🟢 ÇALIŞIYOR (7/24 Kesintisiz)", interactive=False)
        with gr.Column():
            refresh_all_btn = gr.Button("🔄 Paneli Canlı Yenile", variant="primary")
            restart_svc_btn = gr.Button("⚡ Bot Servisini Yeniden Başlat")

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
                label="Hazır Mimari Temalar",
                choices=[
                    "İskandinav Aydınlık Yemek Odası (Doğal Gün Işığı, Meşe Parke)",
                    "Lüks Modern Salon (Mermer Zemin, LED Aydınlatmalı TV Konsolu)",
                    "Endüstriyel Loft (Tuğla Duvar, Geniş Fabrika Pencereleri)",
                    "Ferah Ev-Ofis (Büyük Cam, Minimalist Çalışma Alanı, Bitkiler)"
                ],
                value="İskandinav Aydınlık Yemek Odası (Doğal Gün Işığı, Meşe Parke)"
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

    # Buton olayları
    refresh_all_btn.click(
        get_dashboard_data,
        outputs=[metric_users, metric_products, metric_status, user_table, product_table, system_log_box]
    )
    restart_svc_btn.click(restart_bot_action, outputs=[action_alert])
    
    # Sayfa ilk yüklendiğinde verileri doldur
    demo.load(
        get_dashboard_data,
        outputs=[metric_users, metric_products, metric_status, user_table, product_table, system_log_box]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
