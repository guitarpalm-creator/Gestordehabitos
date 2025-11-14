import os
import logging
from flask import Flask, request, jsonify
from bot import initialize_updater, TELEGRAM_TOKEN

# --------------------------
# Configuración
# --------------------------
logging.basicConfig(level=logging.INFO)

# Obtener variables de entorno
PORT = int(os.environ.get('PORT', 5000))
# RENDER_EXTERNAL_HOSTNAME es la URL pública que Render asigna a tu servicio.
RENDER_URL = os.environ.get("RENDER_EXTERNAL_HOSTNAME") 

if not RENDER_URL:
    logging.warning("RENDER_EXTERNAL_HOSTNAME no encontrado. Usando polling (solo para pruebas locales).")

# Inicializa el Updater y el Dispatcher
updater = initialize_updater()
if updater:
    dispatcher = updater.dispatcher

app = Flask(__name__)

# --------------------------
# Rutas Webhook
# --------------------------

@app.route('/')
def index():
    """Ruta de salud para verificar que el servidor esté activo."""
    return 'Bot Webhook is ready', 200

# La ruta del Webhook debe ser un secreto (usamos el token para ello)
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Maneja las actualizaciones de Telegram."""
    if request.method == "POST" and updater:
        # Pasa el objeto JSON de Telegram directamente al Dispatcher
        update = request.get_json()
        updater.update_queue.put(Update.de_json(update, updater.bot))
        return "ok", 200
    return "Error en la configuración del Webhook", 400

# --------------------------
# Inicialización (Webhooks)
# --------------------------

# Ejecuta esta función al inicio para configurar el Webhook en Telegram
if updater and RENDER_URL:
    try:
        WEBHOOK_URL = f"https://{RENDER_URL}/{TELEGRAM_TOKEN}"
        
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TELEGRAM_TOKEN,
                              webhook_url=WEBHOOK_URL)
        
        logging.info(f"Webhook iniciado en: {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"Error al iniciar el Webhook: {e}")

if __name__ == '__main__':
    # Para pruebas locales, puedes usar app.run(). 
    # En Render, Gunicorn se encarga de esto.
    if not RENDER_URL:
        updater.start_polling()
        logging.info("Iniciando en modo Polling (Local).")
        updater.idle()
    else:
        # La aplicación ya está lista para ser servida por Gunicorn
        app.run(port=PORT)