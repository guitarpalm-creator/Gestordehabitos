import os
import sys
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio

# Habilita el log para ver errores de Telegram en Render
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 1. Variables de Entorno y Configuración ---
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
PORT = int(os.environ.get("PORT", "5000")) 

# --- 2. Lógica del Bot (Funciones Asíncronas) ---
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
    
# Crea la aplicación (sin inicializar)
application = Application.builder().token(BOT_TOKEN).build()

# Registrar los handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Variable de estado global para la inicialización
is_initialized = False

# --- 4. Configuración del Servidor Flask (Punto de entrada de Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    """Ruta para verificar que Render está funcionando."""
    return "Bot Service is Running!", 200

@app.route('/webhook', methods=['POST'])
async def webhook_handler():
    """Ruta que recibe las actualizaciones de Telegram."""
    global is_initialized
    
    # --- SOLUCIÓN CRÍTICA: Inicializar Application solo una vez ---
    if not is_initialized:
        # Se requiere initialize() para process_update()
        await application.initialize()
        is_initialized = True
        logger.info("Application initialized successfully inside webhook_handler.")
        
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