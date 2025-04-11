import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    ARGOCD_API = os.getenv("ARGOCD_API", "https://localhost:8080/api/v1")
    ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

    @staticmethod
    def validate():
        required_vars = ["ARGOCD_API", "ARGOCD_TOKEN", "SLACK_WEBHOOK_URL"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Faltan variables de entorno requeridas: {', '.join(missing_vars)}")