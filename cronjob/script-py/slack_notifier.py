import requests
import logging
from config import Config

class SlackNotifier:
    @staticmethod
    def send_notification(app_name, status, attempts, message):
        try:
            payload = {
                "text": f"Aplicación: {app_name}\nEstado: {status}\nIntentos: {attempts}\nMensaje: {message}"
            }
            response = requests.post(Config.SLACK_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            logging.info(f"Notificación enviada a Slack: {message}")
        except requests.RequestException as e:
            logging.error(f"Error al enviar notificación a Slack: {e}")