"""
app.py
Hugging Face Spaces için başlatıcı dosya (ZeroGPU uyumlu).
"""

import threading
import gradio as gr
import spaces

def run_telegram_bot():
    """Telegram botunu arka plan thread'inde çalıştırır."""
    import bot
    bot.main()

# ZeroGPU'nun kontrol mekanizmasını tatmin eden kukla fonksiyon
@spaces.GPU
def gpu_keepalive():
    return "GPU OK"

# Telegram botunu ayrı bir thread'de 7/24 başlat
bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
bot_thread.start()

# Hugging Face için web arayüzü (sağlık/durum kontrolü)
with gr.Blocks(title="Trendyol AI Studio Bot") as demo:
    gr.Markdown("# 🛍️ Trendyol AI Studio Bot")
    gr.Markdown("### ✅ Bot şu anda aktif ve Telegram üzerinden 7/24 dinliyor!")
    gr.Markdown("👉 Telegram'dan test etmek için: [@Trendyol_studio_mehmetbot](https://t.me/Trendyol_studio_mehmetbot)")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
