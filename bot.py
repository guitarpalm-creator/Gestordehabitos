import os
import sys
import logging
from flask import Flask, request
from telegram import Update
# Usamos las clases antiguas para la versión 13.15
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Habilita el log
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 1. Variables de Entorno y Configuración ---
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
PORT = int(os.environ.get("PORT", "5000")) 

# --- 2. Lógica del Bot (Funciones Síncronas en v13) ---

def get_plans_info():
    """Devuelve la información de los planes para el mensaje de inicio."""
    return (
        "\n\n*📋 Planes de Suscripción:*\n"
        "---------------------------------------\n"
        "*1. Plan Gratuito (¡Empieza Ya!)*\n"
        "   - Hábito Máximo: *3 hábitos activos*.\n"
        "   - Historial: Acceso al progreso de la última semana.\n"
        "   - *Ideal para:* Probar la funcionalidad básica del bot.\n\n"
        "*2. Plan Pro (Suscripción Paga)*\n"
        "   - Hábito Máximo: *15 hábitos activos*.\n"
        "   - Historial: Acceso completo e ilimitado al historial.\n"
        "   - *Beneficio Extra:* Gráficos de racha y progreso mensual.\n\n"
        "*3. Plan VIP (Suscripción Paga Premium)*\n"
        "   - Hábito Máximo: *Ilimitados hábitos activos*.\n"
        "   - Historial: Acceso ilimitado y exportación de datos.\n"
        "   - *Beneficio Extra:* Notificaciones personalizadas y soporte prioritario.\n"
        "\n*¡Usa /premium para ver cómo adquirir los planes pagos!*"
    )


def start(update, context):
    """Responde al comando /start con una miniguía y planes."""
    user = update.effective_user
    welcome_message = (
        f"¡Hola, *{user.first_name}*! 👋 Soy tu Bot Gestor de Hábitos. "
        "Estoy activo y listo para ayudarte a construir consistencia.\n\n"
        "*🚀 Guía Rápida:*\n"
        "1. Usa `/add <nombre_del_hábito>` para empezar (Ej: `/add Beber 2L agua`).\n"
        "2. Usa `/check <hábito>` para marcarlo como completado hoy.\n"
        "3. Usa `/list` para ver tus hábitos activos y tu progreso.\n"
        "4. Si te pierdes, usa `/help` para ver todos los comandos.\n"
        f"{get_plans_info()}"
    )
    # Usamos reply_markdown para aplicar formato de Markdown
    update.message.reply_markdown(welcome_message)


def help_command(update, context):
    """Muestra la lista de comandos disponibles."""
    help_message = (
        "*Comandos Disponibles:*\n"
        "---------------------------------------\n"
        "*/start* - Mensaje de bienvenida y guía rápida.\n"
        "*/help* - Muestra esta lista de comandos.\n"
        "*/add <nombre>* - Añade un nuevo hábito. *(\u26A0\ufe0f Aún no funciona, estamos en desarrollo)*\n"
        "*/list* - Muestra tus hábitos y el estado de hoy. *(\u26A0\ufe0f Aún no funciona)*\n"
        "*/check <hábito>* - Marca un hábito como completado hoy. *(\u26A0\ufe0f Aún no funciona)*\n"
        "*/remove <hábito>* - Elimina un hábito de tu lista. *(\u26A0\ufe0f Aún no funciona)*\n"
        "*/premium* - Información sobre los planes Pro y VIP.\n"
    )
    update.message.reply_markdown(help_message)


def echo(update, context):
    """Responde a mensajes de texto normales."""
    update.message.reply_text(
        "Lo siento, no entendí ese comando. Usa `/help` para ver qué puedo hacer."
    )

def premium_info(update, context):
    """Muestra la información detallada sobre cómo adquirir los planes pagos."""
    info_message = (
        "*✨ ¡Pásate a Premium! ✨*\n\n"
        "Gracias por usar la versión gratuita. Para llevar tu progreso al siguiente nivel, considera nuestros planes pagos:\n"
        f"{get_plans_info()}\n\n"
        "*💳 ¿Cómo adquirirlo?*\n"
        "Por favor, visita nuestro portal de pago seguro en línea o contáctanos directamente para configurar tu plan:\n"
        "🔗 *Enlace de Pago:* `https://gestordehabitos.com/premium` (URL simulada)\n"
        "📧 *Soporte:* `soporte@gestordehabitos.com` (Correo simulado)\n\n"
        "_¡Desbloquea historial ilimitado, gráficos avanzados y hábitos ilimitados!_"
    )
    update.message.reply_markdown(info_message)


# --- 3. Inicialización y Handlers (v13.15) ---
if not BOT_TOKEN:
    logger.error("BOT_TOKEN no está configurado. Saliendo.")
    sys.exit(1)
    
# Creamos el Updater y el Dispatcher (el método antiguo)
updater = Updater(BOT_TOKEN)
dispatcher = updater.dispatcher

# Registrar los handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command)) 
dispatcher.add_handler(CommandHandler("premium", premium_info)) 
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))


# Inicializamos Flask
app = Flask(__name__)

@app.route('/')
def home():
    """Ruta para verificar que Render está funcionando."""
    return "Bot Service is Running!", 200

# --- WEBHOOK HANDLER: FUNCIÓN SÍNCRONA DE FLASK (v13.15) ---
@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Ruta síncrona que recibe las actualizaciones de Telegram y delega."""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), dispatcher.bot)
        
        # En v13, usamos el dispatcher de forma síncrona para procesar la actualización
        dispatcher.process_update(update)
        
        # Flask retorna una respuesta síncrona VÁLIDA inmediatamente.
        return "ok"
    
    return "Bad Request", 400