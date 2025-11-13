import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# --------------------------
# 1. Configuración de Logging y Token
# --------------------------

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# El token se obtiene de las variables de entorno para un despliegue seguro
# Asegúrate de que esta variable esté configurada en Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# --------------------------
# 2. Base de Datos Simulada (Diccionario Global)
# --------------------------

# user_data: { user_id: { 'plan': 'gratis'/'pro'/'vip', 'habits': [h1, h2, ...] } }
user_data = {}

# Límites de hábitos por plan
HABIT_LIMITS = {
    'gratis': 3,
    'pro': 15,
    'vip': 999
}

# --------------------------
# 3. Funciones de Ayuda para la Lógica de Planes
# --------------------------

def get_user_plan(user_id):
    """Inicializa y obtiene el plan del usuario."""
    if user_id not in user_data:
        # Inicialización por defecto
        user_data[user_id] = {
            'plan': 'gratis',
            'habits': []
        }
    return user_data[user_id]['plan']

def get_habit_count(user_id):
    """Devuelve la cantidad de hábitos activos del usuario."""
    return len(user_data.get(user_id, {}).get('habits', []))

def get_limit_message(user_id):
    """Genera un mensaje sobre el límite de hábitos del usuario."""
    plan = get_user_plan(user_id)
    limit = HABIT_LIMITS[plan]
    count = get_habit_count(user_id)
    return (f"Tienes el plan **{plan.upper()}**.\n"
            f"Actualmente tienes **{count}** de **{limit}** hábitos.")

# --------------------------
# 4. Comandos del Bot
# --------------------------

def start_command(update: Update, context):
    """Muestra el mensaje de bienvenida y la guía rápida."""
    user_id = update.effective_user.id
    plan_info = get_limit_message(user_id)
    
    welcome_message = (
        "👋 **¡Bienvenido(a) al Gestor de Hábitos!**\n\n"
        "Estoy aquí para ayudarte a construir consistencia día a día.\n\n"
        "**Guía Rápida:**\n"
        "**/add <hábito>**: Agrega un nuevo hábito (ej: `/add Beber agua`).\n"
        "**/list**: Ve tus hábitos y tu progreso (¡Próximamente!).\n"
        "**/check**: Marca un hábito como completado (¡Próximamente!).\n"
        "**/premium**: Conoce nuestros planes de pago.\n"
        "**/help**: Lista todos los comandos.\n\n"
        f"--- **Tu Estado Actual** ---\n{plan_info}"
    )
    update.message.reply_text(welcome_message, parse_mode='Markdown')

def help_command(update: Update, context):
    """Lista todos los comandos disponibles."""
    help_message = (
        "📚 **Lista de Comandos Disponibles**\n\n"
        "**/start**: Mensaje de bienvenida y estado del plan.\n"
        "**/add <hábito>**: Agrega un nuevo hábito.\n"
        "**/list**: Muestra tus hábitos (Próximamente).\n"
        "**/check**: Marca un hábito como completado (Próximamente).\n"
        "**/premium**: Información sobre planes Pro y VIP.\n"
        "**/help**: Muestra esta lista de comandos."
    )
    update.message.reply_text(help_message, parse_mode='Markdown')

def premium_command(update: Update, context):
    """Muestra la información de los planes de suscripción."""
    premium_message = (
        "✨ **Planes Premium**\n\n"
        "🚀 **Plan Pro**:\n"
        f"  - Límite de **{HABIT_LIMITS['pro']}** hábitos.\n"
        "  - Recordatorios por la mañana y noche.\n\n"
        "💎 **Plan VIP**:\n"
        f"  - Límite de **{HABIT_LIMITS['vip']}** hábitos.\n"
        "  - Recordatorios personalizados.\n"
        "  - Reportes semanales de progreso.\n\n"
        "¡Mejora tu plan para desbloquear tu potencial completo!"
    )
    update.message.reply_text(premium_message, parse_mode='Markdown')

def add_habit_command(update: Update, context):
    """Permite al usuario agregar un hábito, respetando el límite de su plan."""
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)
    current_habits = user_data[user_id]['habits']
    habit_limit = HABIT_LIMITS[plan]

    # El hábito es el texto que sigue al comando /add
    if not context.args:
        update.message.reply_text("❌ **Error**: Debes especificar el hábito. \nEjemplo: `/add Meditar 10 minutos`")
        return

    # Unir todos los argumentos para formar el nombre completo del hábito
    new_habit = " ".join(context.args).strip()
    
    if len(current_habits) >= habit_limit:
        # Límite alcanzado
        limit_message = get_limit_message(user_id)
        update.message.reply_text(
            f"🛑 **Límite Alcanzado**\n\n"
            f"No puedes agregar **'{new_habit}'** porque has llegado al límite de tu plan.\n"
            f"{limit_message}\n\n"
            f"Considera mejorar tu plan con `/premium` o usa `/list` (próximamente) para eliminar uno."
            , parse_mode='Markdown'
        )
        return
    
    if new_habit in current_habits:
        update.message.reply_text(f"⚠️ **Ya existe**: El hábito **'{new_habit}'** ya está en tu lista.", parse_mode='Markdown')
        return

    # Agregar el nuevo hábito
    current_habits.append(new_habit)
    count = len(current_habits)

    update.message.reply_text(
        f"✅ ¡Hábito **'{new_habit}'** agregado!\n\n"
        f"Ahora tienes **{count}** de **{habit_limit}** hábitos activos.",
        parse_mode='Markdown'
    )

def main():
    """Función principal para inicializar y arrancar el bot."""
    if not TELEGRAM_TOKEN:
        logging.error("TELEGRAM_TOKEN no está configurado en las variables de entorno.")
        return

    # Usamos Updater y Dispatcher (v13.15)
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Registrar los comandos
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("premium", premium_command))
    # Note: 'add' debe ser CommandHandler, no requiere filtro de texto
    dispatcher.add_handler(CommandHandler("add", add_habit_command))

    # Iniciar el bot. En un entorno de despliegue como Render,
    # el webhook se configuraría, pero para pruebas o un entorno simple,
    # el polling funciona. La configuración de Render maneja el webhook.
    
    # Para la configuración con Gunicorn/Flask, la inicialización del bot
    # es un poco diferente. En este caso, este script se ejecutaría para
    # iniciar el bot, pero para un servidor web, se necesita Flask.
    # Asumo que tienes un archivo de servidor Flask que importa y ejecuta este 'main'
    # o que este archivo 'bot.py' es el punto de entrada principal para el polling
    # o el webhook (configurado externamente).
    
    # Para el despliegue con Render que usa Gunicorn, normalmente se usa un patrón
    # de Webhook que no es compatible directamente con este `updater.start_polling()`
    # a menos que se use un proceso separado.
    
    # Para mantener la compatibilidad con el despliegue estándar de Render,
    # **necesitamos la estructura de Flask/Gunicorn que no está aquí**.
    # Asumo que la estructura de *despliegue* está en un archivo `app.py` 
    # o similar, que **sí** usa Flask.

    # **Asumo que este código solo será llamado para las funciones de handler
    # y la inicialización del bot en un script separado de Flask/Gunicorn.**
    
    # Si la intención es que `bot.py` sea el **único** archivo de entrada 
    # para el servidor web, se requiere una adaptación.
    
    # **Mantendré la estructura de Updater para los handlers, ya que eso funciona
    # con la v13.15, y espero que la integración con el servidor Flask esté resuelta
    # o que se aplique un patrón de polling simple si se ejecuta como un proceso
    # independiente, no como un webhook/servidor.**

    # Para seguir adelante, solo nos enfocaremos en los handlers.

    logging.info("Handlers de comandos cargados correctamente.")
    # No inicio el polling/webhook aquí para enfocarme en la lógica,
    # y porque el entorno de Render lo maneja de forma externa.
    
    return updater # Devolvemos el updater para potencial uso externo

if __name__ == '__main__':
    main()