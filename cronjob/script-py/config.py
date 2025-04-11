import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # ARGOCD_API debe ser solo la dirección del servidor y el puerto (por ejemplo, "192.168.49.2:32376")
    ARGOCD_API = os.getenv("ARGOCD_API", "192.168.49.2:32376")
    ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN")
    ARGOCD_USERNAME = os.getenv("ARGOCD_USERNAME")
    ARGOCD_PASSWORD = os.getenv("ARGOCD_PASSWORD")  # Leer la contraseña desde la variable de entorno
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

    @staticmethod
    def validate():
        required_vars = ["ARGOCD_API", "SLACK_WEBHOOK_URL"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if not Config.ARGOCD_TOKEN and (not Config.ARGOCD_USERNAME or not Config.ARGOCD_PASSWORD):
            missing_vars.append("ARGOCD_TOKEN or ARGOCD_USERNAME and ARGOCD_PASSWORD")
        if missing_vars:
            raise ValueError(f"Faltan variables de entorno requeridas: {', '.join(missing_vars)}")