"""
app.py
Trendyol AI Manager - 7/24 Bulut Admin Paneli ve Bot Yönetim Merkezi.
Botu bağımsız subprocess olarak 7/24 çalıştırır.
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

load_dotenv()

# ZeroGPU kontrol dekoratörü
@spaces.GPU
def check_gpu():
    return "GPU OK"

bot_process = None
bot_logs = []


def log_message(msg: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    bot_logs.append(entry)
    if len(bot_logs) > 100:
        bot_logs.pop(0)


def monitor_bot_output(proc):
    """Botun terminal çıktılarını canlı olarak okuyup log listesine ekler."""
    for line in iter(proc.stdout.readline, ""):
        if line:
            clean_line = line.strip()
            log_message(clean_line)
    proc.stdout.close()


def start_bot_process():
    """Botu arka planda bağımsız bir Python süreci olarak başlatır."""
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        log_message("🚀 Telegram Bot süreci başlatılıyor...")
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
        log_message("✅ Telegram Bot süreci başarıyla başlatıldı ve dinliyor!")


# Sayfa açıldığında botu otomatik başlat
start_bot_process()


def get_system_status():
    global bot_process
    is_running = bot_process is not None and bot_process.poll() is None
    status = "🟢 ÇALIŞIYOR (7/24 Canlı)" if is_running else "🔴 DURDURULDU"
    logs_text = "\n".join(bot_logs[-30:]) if bot_logs else "Log kaydı bekleniyor..."
    return status, logs_text


def restart_bot():
    """Botu admin panelinden yeniden başlatır."""
    global bot_process
    if bot_process and bot_process.poll() is None:
        bot_process.terminate()
        time.sleep(1)
    start_bot_process()
    return "🔄 Bot yeniden başlatıldı!"


def save_settings(openrouter_key: str):
    """Admin panelinden API Key güncellemesi."""
    if openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_key.strip()
        log_message("⚙️ OpenRouter API Anahtarı güncellendi!")
        return "✅ Ayarlar kaydedildi!"
    return "⚠️ Değişiklik yapılmadı."


with gr.Blocks(title="Trendyol AI Manager - Admin Paneli", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🛍️ **Trendyol AI Mağaza Yöneticisi - Bulut Admin Paneli**")
    gr.Markdown("Bu panel 7/24 internette çalışır. Bilgisayarınızı kapatsanız dahi bot aktiftir.")
    
    with gr.Row():
        with gr.Column(scale=1):
            bot_status = gr.Textbox(label="Bot Canlı Durumu", value="🟢 ÇALIŞIYOR (7/24 Canlı)", interactive=False)
            with gr.Row():
                refresh_btn = gr.Button("🔄 Durumu Yenile")
                restart_btn = gr.Button("⚡ Botu Yeniden Başlat", variant="secondary")
        with gr.Column(scale=2):
            gr.Markdown("### 📱 **Telegram Bot Bilgisi**")
            gr.Markdown("Bot: **[@Trendyol_studio_mehmetbot](https://t.me/Trendyol_studio_mehmetbot)**")
            action_msg = gr.Markdown()

    gr.Markdown("---")
    with gr.Tabs():
        with gr.TabItem("📝 Canlı Konsol Logları"):
            log_display = gr.Textbox(label="Canlı Sistem & Telegram İşlem Kayıtları", lines=14, interactive=False)

        with gr.TabItem("⚙️ Canlı Ayarlar"):
            api_key_input = gr.Textbox(label="OpenRouter API Key", type="password", value=os.getenv("OPENROUTER_API_KEY", ""))
            save_btn = gr.Button("💾 Ayarları Kaydet", variant="primary")
            save_msg = gr.Markdown()
            save_btn.click(save_settings, inputs=[api_key_input], outputs=[save_msg])

    refresh_btn.click(get_system_status, outputs=[bot_status, log_display])
    restart_btn.click(restart_bot, outputs=[action_msg])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
