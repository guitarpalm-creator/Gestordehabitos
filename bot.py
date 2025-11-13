import os
import sys
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
# Importamos la utilidad para correr tareas asíncronas en el hilo de Gunicorn
from asgiref.sync import async_to_sync, sync_to_async 

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

# --- FUNCIÓN ASÍNCRONA PARA PROCESAR UPDATES (DEBE SER ESPERADA) ---
async def process_telegram_update(data):
    """Maneja la inicialización y el procesamiento de la actualización."""
    global is_initialized
    
    # Se inicializa solo la primera vez que se recibe un mensaje
    if not is_initialized:
        # La inicialización se hace aquí para garantizar que se use un bucle de eventos válido
        await application.initialize()
        is_initialized = True
        logger.info("Application initialized successfully on first webhook call.")

    # Procesa la actualización
    update = Update.de_json(data, application.bot)
    await application.process_update(update)

# --- WEBHOOK HANDLER: DELEGAMOS A UN HILO ESTABLE ---
# Usamos el decorador @sync_to_async en la función de envoltura de Flask
@app.route('/webhook', methods=['POST'])
@sync_to_async
def webhook_handler_wrapper():
    """Una función síncrona/de envoltura para la ruta /webhook de Flask."""
    if request.method == "POST":
        data = request.get_json(force=True)
        try:
            # Ejecutamos la función asíncrona dentro del contexto síncrono del wrapper
            # Esto maneja el conflicto del Event Loop Closed
            async_to_sync(process_telegram_update)(data)
            return "ok"
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            # El código de error 500 garantiza que Telegram reintente el mensaje
            return "Internal Server Error", 500
    
    return "Bad Request", 400

# El nombre de la ruta que Flask necesita es webhook_handler_wrapper
# Lo renombramos para que sea más intuitivo
webhook_handler = webhook_handler_wrapper

# Punto de Entrada para Gunicorn: Gunicorn buscará la variable 'app' para iniciar el servicio web.