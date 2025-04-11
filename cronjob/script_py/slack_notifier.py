import requests
from script_py.config import Config

class SlackNotifier:
    @staticmethod
    def send_notification(app_name, status, attempts, action=""):
        message = {
            "text": f"⚠️ *Estado de la aplicación:*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*Aplicación:* `{app_name}`\n"
                            f"*Estado:* `{status}`\n"
                            f"*Intentos:* `{attempts}`\n"
                            f"*Acción:* {action}\n"
                        )
                    }
                }
            ]
        }
        try:
            response = requests.post(Config.SLACK_WEBHOOK_URL, json=message)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al enviar notificación a Slack: {e}")