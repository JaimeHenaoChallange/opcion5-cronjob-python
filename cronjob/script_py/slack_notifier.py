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
                            f"```\n"
                            f"{'Aplicación':<20} {'Estado':<15} {'Intentos':<10}\n"
                            f"{'-' * 50}\n"
                            f"{app_name:<20} {status:<15} {attempts:<10}\n"
                            f"{'-' * 50}\n"
                            f"{action}\n"
                            f"```"
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