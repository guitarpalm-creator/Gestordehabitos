import os
import logging
import json # NUEVO: Módulo para manejar JSON
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# --------------------------
# 1. Configuración de Logging y Token
# --------------------------

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# --------------------------
# 2. Base de Datos Simulada (Diccionario Global)
# --------------------------

# Nombre del archivo donde se guardará la persistencia
DATA_FILE = "user_data.json" 

# user_data: { user_id: { 'plan': 'gratis'/'pro'/'vip', 'habits': [{'name': h1, 'checked_today': bool}, ...] } }
user_data = {}

# Límites de hábitos por plan
HABIT_LIMITS = {
    'gratis': 3,
    'pro': 15,
    'vip': 999
}

# --------------------------
# 3. Funciones de Persistencia de Datos
# --------------------------

def load_data():
    """Carga los datos del archivo JSON en la variable global user_data al inicio."""
    global user_data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                # La clave del usuario debe ser un string para JSON, 
                # así que la convertimos a int al cargar.
                raw_data = json.load(f)
                user_data = {int(k): v for k, v in raw_data.items()}
            logging.info("Datos cargados exitosamente desde user_data.json.")
        except json.JSONDecodeError:
            logging.error("Error al decodificar el archivo JSON. Iniciando con datos vacíos.")
            user_data = {}
    else:
        logging.info("Archivo de datos no encontrado. Iniciando con datos vacíos.")
        user_data = {}

def save_data():
    """Guarda los datos de la variable global user_data en el archivo JSON."""
    # Nota: Convertimos las claves de ID de usuario a string para que JSON pueda serializarlas correctamente.
    serializable_data = {str(k): v for k, v in user_data.items()}
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(serializable_data, f, indent=4)
        # En entornos con Gunicorn/multi-worker, este enfoque de archivo JSON 
        # puede tener problemas de concurrencia. Una base de datos real sería la solución.
        logging.info("Datos guardados exitosamente en user_data.json.")
    except Exception as e:
        logging.error(f"Error al guardar los datos: {e}")

# --------------------------
# 4. Funciones de Ayuda para la Lógica de Planes
# --------------------------

def get_user_plan(user_id):
    """Inicializa y obtiene el plan del usuario."""
    if user_id not in user_data:
        # Inicialización por defecto
        user_data[user_id] = {
            'plan': 'gratis',
            'habits': [] 
        }
        # Guardar la inicialización en el archivo
        save_data() # NUEVO
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
# 5. Comandos del Bot
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
        "**/list**: Ve tus hábitos y su progreso.\n"
        "**/check <número/nombre>**: Marca un hábito como completado.\n"
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
        "**/list**: Muestra tus hábitos.\n"
        "**/check <número/nombre>**: Marca un hábito como completado.\n"
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

    if not context.args:
        update.message.reply_text("❌ **Error**: Debes especificar el hábito. \nEjemplo: `/add Meditar 10 minutos`")
        return

    new_habit = " ".join(context.args).strip()
    
    # Búsqueda de duplicados usando la clave 'name'
    if new_habit in [h['name'] for h in current_habits]:
        update.message.reply_text(f"⚠️ **Ya existe**: El hábito **'{new_habit}'** ya está en tu lista.", parse_mode='Markdown')
        return
        
    if len(current_habits) >= habit_limit:
        # Límite alcanzado
        limit_message = get_limit_message(user_id)
        update.message.reply_text(
            f"🛑 **Límite Alcanzado**\n\n"
            f"No puedes agregar **'{new_habit}'** porque has llegado al límite de tu plan.\n"
            f"{limit_message}\n\n"
            f"Considera mejorar tu plan con `/premium` o usa `/list` para eliminar uno."
            , parse_mode='Markdown'
        )
        return

    # Agregar el nuevo hábito con su estado inicial
    current_habits.append({'name': new_habit, 'checked_today': False})
    
    # GUARDAR DATOS después de la modificación
    save_data()

    count = len(current_habits)

    update.message.reply_text(
        f"✅ ¡Hábito **'{new_habit}'** agregado!\n\n"
        f"Ahora tienes **{count}** de **{habit_limit}** hábitos activos.",
        parse_mode='Markdown'
    )

def list_habits_command(update: Update, context):
    """Muestra la lista de hábitos activos del usuario con su estado de finalización."""
    user_id = update.effective_user.id
    habits = user_data.get(user_id, {}).get('habits', [])
    plan_info = get_limit_message(user_id)

    if not habits:
        message = (
            "📋 **Lista de Hábitos**\n\n"
            "Aún no tienes hábitos agregados. ¡Es hora de empezar!\n"
            "Usa **/add <hábito>** para crear tu primer hábito. \n\n"
            f"--- **Tu Estado Actual** ---\n{plan_info}"
        )
    else:
        habit_lines = []
        for i, habit_obj in enumerate(habits):
            status = '✅' if habit_obj.get('checked_today', False) else '⚪' 
            habit_name = habit_obj['name']
            habit_lines.append(f"**{i+1}.** {status} *{habit_name}*")
        
        habit_list_text = "\n".join(habit_lines)
        
        message = (
            "📋 **Tus Hábitos Activos (Hoy)**\n"
            "⚪ = Pendiente, ✅ = Completado\n\n"
            f"{habit_list_text}\n\n"
            f"--- **Tu Estado Actual** ---\n{plan_info}\n\n"
            "Usa **/check <número/nombre>** para marcar/desmarcar un hábito."
        )
    
    update.message.reply_text(message, parse_mode='Markdown')

def check_habit_command(update: Update, context):
    """Permite al usuario marcar o desmarcar un hábito como completado."""
    user_id = update.effective_user.id
    habits = user_data.get(user_id, {}).get('habits', [])
    
    if not context.args:
        update.message.reply_text("❌ **Error**: Debes especificar el **número** o **nombre** del hábito a marcar.\nEjemplo: `/check 1` o `/check Beber agua`")
        return
        
    query = " ".join(context.args).strip()
    target_habit_obj = None

    # 1. Intentar buscar por índice (número)
    try:
        habit_index = int(query) - 1
        if 0 <= habit_index < len(habits):
            target_habit_obj = habits[habit_index]
    except ValueError:
        # 2. Si no es un número, intentar buscar por nombre
        for habit_obj in habits:
            if habit_obj['name'].lower() == query.lower():
                target_habit_obj = habit_obj
                break

    if target_habit_obj:
        # Alternar el estado
        current_status = target_habit_obj.get('checked_today', False)
        new_status = not current_status
        target_habit_obj['checked_today'] = new_status
        
        # GUARDAR DATOS después de la modificación
        save_data()

        habit_name = target_habit_obj['name']
        
        if new_status:
            response = f"✅ ¡Hábito **'{habit_name}'** marcado como **COMPLETADO** para hoy!"
        else:
            response = f"🔄 Hábito **'{habit_name}'** marcado como **PENDIENTE** (desmarcado)."
            
        update.message.reply_text(response, parse_mode='Markdown')
    else:
        update.message.reply_text(f"❌ **Error**: Hábito **'{query}'** no encontrado en tu lista. Usa `/list` para ver tus hábitos.", parse_mode='Markdown')


def main():
    """Función principal para inicializar y arrancar el bot."""
    # CARGAR DATOS al inicio del bot
    load_data()

    if not TELEGRAM_TOKEN:
        logging.error("TELEGRAM_TOKEN no está configurado en las variables de entorno.")
        return

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Registrar los comandos
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("premium", premium_command))
    dispatcher.add_handler(CommandHandler("add", add_habit_command))
    dispatcher.add_handler(CommandHandler("list", list_habits_command)) 
    dispatcher.add_handler(CommandHandler("check", check_habit_command)) 

    logging.info("Handlers de comandos cargados correctamente.")
    
    return updater 

if __name__ == '__main__':
    main()