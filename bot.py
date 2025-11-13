import os
import sys
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Habilita el log para ver errores de Telegram en Render
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 1. Variables de Entorno y Configuración ---
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 
PORT = int(os.environ.get("PORT", "5000")) 

# --- 2. Lógica del Bot ---
async def start(update: Update, context):
    """Responde al comando /start."""
    await update.message.reply_text('¡Hola! Soy tu bot de hábitos. ¡Estoy activo y listo!')

async def echo(update: Update, context):
    """Responde a mensajes de texto normales."""
    await update.message.reply_text(f"Recibí: {update.message.text}. Procesando tu solicitud...")

# --- 3. Inicialización y Handlers ---
if not BOT_TOKEN:
    logger.error("BOT_TOKEN no está configurado. Saliendo.")
    sys.exit(1)
    
# Crea la aplicación
application = Application.builder().token(BOT_TOKEN).build()

# Registrar los handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- 4. Configuración del Servidor Flask (Punto de entrada de Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    """Ruta para verificar que Render está funcionando."""
    return "Bot Service is Running!", 200

@app.route('/webhook', methods=['POST'])
async def webhook_handler():
    """Ruta que recibe las actualizaciones de Telegram."""
    if request.method == "POST":
        # Pasa el JSON de Telegram directamente a la aplicación
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return "ok"
    return "Bad Request", 400

# Esta función configura el webhook, se llama una sola vez al inicio
async def set_webhook():
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        logger.info(f"Setting webhook to: {webhook_url}")
        # Asegúrate de usar 'await' si estás fuera del bucle de eventos
        async with application:
             await application.bot.set_webhook(url=webhook_url)

# Llamamos a la función de configuración del webhook inmediatamente
import threading
def run_setup():
    application.loop.run_until_complete(set_webhook())

# Iniciamos la configuración del webhook en un hilo separado
threading.Thread(target=run_setup).start()

# Punto de Entrada para Gunicorn
# Gunicorn ejecutará app.run() en un entorno de producción, ignorando el if __name__ == '__main__':