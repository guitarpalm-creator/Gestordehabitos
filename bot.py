import os
import sys
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio
from asgiref.sync import sync_to_async

# Habilita el log para ver errores de Telegram en Render
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 1. Variables de Entorno y Configuración ---
# Render proporciona estas variables
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
# La URL externa ya no se usa, ya que configuramos el webhook manualmente
# RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 
PORT = int(os.environ.get("PORT", "5000")) 

# --- 2. Lógica del Bot (Funciones Asíncronas) ---
async def start(update: Update, context):
    """Responde al comando /start."""
    # Envía la respuesta al usuario
    await update.message.reply_text('¡Hola! Soy tu bot de hábitos. ¡Estoy activo y listo!')

async def echo(update: Update, context):
    """Responde a mensajes de texto normales."""
    # Envía una respuesta simple
    await update.message.reply_text(f"Recibí: {update.message.text}. Procesando tu solicitud...")

# --- 3. Inicialización y Handlers ---
if not BOT_TOKEN:
    logger.error("BOT_TOKEN no está configurado. Saliendo.")
    sys.exit(1)
    
# Crea la aplicación (sin inicializar aún)
application = Application.builder().token(BOT_TOKEN).build()

# Registrar los handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- 4. Inicialización Asíncrona Final (Necesaria para Application.process_update) ---
# Esta es la solución final para el RuntimeError y el AttributeError.
# Inicializamos el objeto Application de forma asíncrona ANTES de que Flask lo use.
@sync_to_async
def initialize_app():
    """Inicializa la aplicación de forma asíncrona dentro de un contexto síncrono."""
    try:
        application.loop = asyncio.get_event_loop()
    except RuntimeError:
        application.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(application.loop)
        
    application.loop.run_until_complete(application.initialize())

# Ejecutar la inicialización
try:
    initialize_app()
except Exception as e:
    logger.error(f"Error durante la inicialización de la aplicación: {e}")
    # En caso de fallar, el bot no podrá procesar mensajes.

# --- 5. Configuración del Servidor Flask (Punto de entrada de Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    """Ruta para verificar que Render está funcionando."""
    return "Bot Service is Running!", 200

@app.route('/webhook', methods=['POST'])
async def webhook_handler():
    """Ruta que recibe las actualizaciones de Telegram."""
    if request.method == "POST":
        # 1. Obtiene el JSON de la solicitud de Telegram
        data = request.get_json(force=True)
        # 2. Convierte el JSON en un objeto Update de Telegram
        update = Update.de_json(data, application.bot)
        
        # 3. Procesa la actualización de forma asíncrona
        await application.process_update(update)
        
        # 4. Devuelve una respuesta 200/ok a Telegram
        return "ok"
    return "Bad Request", 400

# Punto de Entrada para Gunicorn: Gunicorn buscará la variable 'app' para iniciar el servicio web.