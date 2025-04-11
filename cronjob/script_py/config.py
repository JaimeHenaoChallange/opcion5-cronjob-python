import os
import yaml
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

class Config:
    CONFIG_FILE = "/app/config.yaml"  # Actualiza la ruta al archivo config.yaml

    try:
        ARGOCD_API = os.getenv("ARGOCD_API", "https://localhost:8080/api/v1")
        ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN")
        SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

        @staticmethod
        def validate():
            missing_vars = []
            if not Config.ARGOCD_API:
                missing_vars.append("ARGOCD_API")
            if not Config.ARGOCD_TOKEN:
                missing_vars.append("ARGOCD_TOKEN")
            if not Config.SLACK_WEBHOOK_URL:
                missing_vars.append("SLACK_WEBHOOK_URL")
            if missing_vars:
                raise ValueError(f"❌ Faltan variables de entorno requeridas: {', '.join(missing_vars)}")
    except Exception as e:
        print(f"❌ Error al cargar la configuración: {e}")
        raise

    @staticmethod
    def load():
        with open(Config.CONFIG_FILE, "r") as file:
            return yaml.safe_load(file)

CONFIG = Config.load()
