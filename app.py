"""
app.py
Trendyol AI Manager - 7/24 Bulut Admin Paneli ve Bot Yönetim Merkezi.
Hugging Face Spaces üzerinde çalışır. Bilgisayar bağımlılığı yoktur.
"""

import os
import sys
import threading
import time
import datetime
import gradio as gr
from dotenv import load_dotenv

load_dotenv()

# Arka plan bot thread kontrolü
bot_thread = None
is_bot_running = False
bot_logs = []


def log_message(msg: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    bot_logs.append(entry)
    if len(bot_logs) > 60:
        bot_logs.pop(0)


def start_bot_background():
    global is_bot_running
    try:
        log_message("🤖 Telegram Bot başlatılıyor...")
        import bot
        is_bot_running = True
        bot.main()
    except Exception as e:
        log_message(f"❌ Bot hatası: {str(e)}")
        is_bot_running = False


# İlk açılışta botu otomatik 7/24 başlat
if not is_bot_running:
    bot_thread = threading.Thread(target=start_bot_background, daemon=True)
    bot_thread.start()


# ==========================================
# ADMİN PANELİ FONKSİYONLARI (WEB ARAYÜZÜ)
# ==========================================

def get_system_status():
    status = "🟢 ÇALIŞIYOR (7/24 Canlı)" if is_bot_running else "🔴 DURDURULDU"
    logs_text = "\n".join(bot_logs[-20:]) if bot_logs else "Henüz bir işlem kaydı yok..."
    return status, logs_text


def save_settings(openrouter_key: str):
    """Admin panelinden API Key veya ayarları botu kapatmadan anında günceller."""
    if openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_key.strip()
        log_message("⚙️ OpenRouter API Anahtarı canlı olarak güncellendi!")
        return "✅ Ayarlar başarıyla güncellendi! Bot kapatılmadan yeni ayarlar aktif oldu."
    return "⚠️ Değişiklik yapılmadı."


# ==========================================
# MODERN GRADIO ADMİN ARAYÜZÜ
# ==========================================

custom_css = """
.admin-card { background: #1e1e2d; border-radius: 12px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.metric-box { text-align: center; font-size: 24px; font-weight: bold; color: #f27a1a; }
"""

with gr.Blocks(title="Trendyol AI Manager - Admin Paneli", css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🛍️ **Trendyol AI Mağaza Yöneticisi - Bulut Admin Paneli**")
    gr.Markdown("Bu panel 7/24 internette çalışır. Bilgisayarınızı kapatsanız dahi bot aktiftir.")
    
    with gr.Row():
        with gr.Column(scale=1):
            bot_status = gr.Textbox(label="Bot Canlı Durumu", value="🟢 ÇALIŞIYOR (7/24 Canlı)", interactive=False)
            refresh_btn = gr.Button("🔄 Durumu ve Logları Yenile")
        with gr.Column(scale=2):
            gr.Markdown("### 📱 **Telegram Bot Bilgisi**")
            gr.Markdown("Bot Kullanıcı Adı: **[@Trendyol_studio_mehmetbot](https://t.me/Trendyol_studio_mehmetbot)**")
            gr.Markdown("Durum: **Simülasyon & Gerçek Mağaza Destekli**")

    gr.Markdown("---")
    
    with gr.Tabs():
        with gr.TabItem("📊 Canlı İstatistikler & Kullanıcılar"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### 📈 Kullanım Özeti")
                    gr.Markdown("- **Desteklenen Platform:** Trendyol (Partner API)")
                    gr.Markdown("- **Görsel Motoru:** FLUX AI Lifestyle + u2net Studio")
                    gr.Markdown("- **SEO & Destek Motoru:** Gemini 2.5 Flash (OpenRouter)")
                with gr.Column():
                    gr.Markdown("#### 👥 Son Aktif Kullanıcılar")
                    gr.Markdown("Telegram üzerinden bota erişen satıcılar otomatik kayıt altına alınır.")

        with gr.TabItem("📝 Canlı Konsol Logları"):
            log_display = gr.Textbox(label="Sistem & Telegram İşlem Kayıtları", lines=12, interactive=False, value="Sistem başlatıldı, dinleniyor...")

        with gr.TabItem("⚙️ Canlı Ayarlar (Botu Kapatmadan)"):
            gr.Markdown("Buradan yapacağınız değişiklikler **botu yeniden başlatmaya gerek kalmadan** anında geçerli olur.")
            api_key_input = gr.Textbox(label="OpenRouter API Key", type="password", value=os.getenv("OPENROUTER_API_KEY", ""))
            save_btn = gr.Button("💾 Ayarları Kaydet", variant="primary")
            save_msg = gr.Markdown()
            save_btn.click(save_settings, inputs=[api_key_input], outputs=[save_msg])

    refresh_btn.click(get_system_status, outputs=[bot_status, log_display])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
