import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# --- 1. Variables de Entorno y Configuración ---
# Render nos proporciona estas variables automáticamente
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 
PORT = int(os.environ.get("PORT", "5000")) 

# --- 2. Lógica del Bot (Funciones Asíncronas) ---
async def start(update: Update, context):
    """Responde al comando /start."""
    await update.message.reply_text('¡Hola! Soy tu bot de Telegram. Estoy activo en Render.')

async def help_command(update: Update, context):
    """Responde al comando /help."""
    await update.message.reply_text('Puedo ayudarte con tu negocio.')

async def echo(update: Update, context):
    """Responde a mensajes de texto normales."""
    await update.message.reply_text(f"Recibí tu mensaje: {update.message.text}. Procesando...")

# --- 3. Inicialización de la Aplicación y Servidor Flask ---
application = Application.builder().token(BOT_TOKEN).build()

# Registrar los handlers (Comandos y Mensajes)
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Configuración del servidor Flask
app = Flask(__name__)

@app.route('/')
def home():
    """Ruta para verificar que Render está funcionando (no usada por Telegram)."""
    return "Bot Service is Running!", 200

@app.route('/webhook', methods=['POST'])
async def webhook_handler():
    """Ruta que recibe las actualizaciones de Telegram."""
    if request.method == "POST":
        # Ejecutamos la función que procesa la actualización del bot
        await application.update_queue.put(
            Update.de_json(request.get_json(force=True), application.bot)
        )
        return "ok"
    return "Bad Request", 400

# Función para configurar el webhook después del despliegue inicial
async def set_webhook():
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        # Usamos el puerto que Render asigna, NO el puerto local.
        await application.bot.set_webhook(url=webhook_url) 

# --- 4. Punto de Entrada para Render/Gunicorn ---
if __name__ == '__main__':
    # Esto es solo para pruebas locales, Render usará Gunicorn
    print(f"Flask App running on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)