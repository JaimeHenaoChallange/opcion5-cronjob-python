import subprocess
import time
import requests
import os
import logging
from dotenv import load_dotenv
import kubernetes.client
import kubernetes.config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Cargar variables desde el archivo .env
load_dotenv()

ARGOCD_SERVER = os.getenv("ARGOCD_SERVER")
ARGOCD_USERNAME = os.getenv("ARGOCD_USERNAME")
ARGOCD_PASSWORD = os.getenv("ARGOCD_PASSWORD")

# Cargar el secreto de Kubernetes para el Slack Webhook
def get_slack_webhook():
    try:
        kubernetes.config.load_incluster_config()
        v1 = kubernetes.client.CoreV1Api()
        secret = v1.read_namespaced_secret("slack-webhook-secret", "argocd")
        return secret.data["SLACK_WEBHOOK_URL"]
    except Exception as e:
        logging.error(f"Error al obtener el Slack Webhook: {e}")
        raise

SLACK_WEBHOOK_URL = get_slack_webhook()

def argocd_login():
    try:
        subprocess.run(
            ["argocd", "login", ARGOCD_SERVER, "--username", ARGOCD_USERNAME, "--password", ARGOCD_PASSWORD, "--insecure"],
            check=True
        )
        logging.info("Autenticación en ArgoCD exitosa.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al autenticar en ArgoCD: {e}")
        raise

def get_applications():
    try:
        result = subprocess.run(
            ["argocd", "app", "list", "--output", "json"],
            capture_output=True,
            text=True
        )
        result.check_returncode()
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al obtener aplicaciones: {e}")
        raise

def check_health(app_name):
    try:
        result = subprocess.run(
            ["argocd", "app", "get", app_name, "--output", "json"],
            capture_output=True,
            text=True
        )
        result.check_returncode()
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al verificar la salud de {app_name}: {e}")
        raise

def deploy(app_name):
    for attempt in range(5):
        logging.info(f"Intentando desplegar {app_name}, intento {attempt + 1}")
        try:
            subprocess.run(["argocd", "app", "sync", app_name], check=True)
            time.sleep(10)
            health = check_health(app_name)
            if "Healthy" in health:
                logging.info(f"{app_name} está healthy.")
                return True
        except subprocess.CalledProcessError as e:
            logging.warning(f"Error al sincronizar {app_name}: {e}")
    logging.error(f"No se pudo desplegar {app_name} después de 5 intentos.")
    return False

def notify_slack(message):
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        response.raise_for_status()
        logging.info(f"Notificación enviada a Slack: {message}")
    except requests.RequestException as e:
        logging.error(f"Error al enviar notificación a Slack: {e}")

def pause_application(app_name):
    try:
        subprocess.run(["argocd", "app", "pause", app_name], check=True)
        logging.info(f"Aplicación {app_name} pausada.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al pausar la aplicación {app_name}: {e}")

def resume_application(app_name):
    try:
        subprocess.run(["argocd", "app", "resume", app_name], check=True)
        logging.info(f"Aplicación {app_name} reanudada.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al reanudar la aplicación {app_name}: {e}")

if __name__ == "__main__":
    try:
        argocd_login()  # Ensure ArgoCD CLI is authenticated
        apps = get_applications()
        for app in apps:
            app_name = app["name"]
            app_status = app["status"]
            if app_status in ["OutOfSync", "Degraded", "Error"]:
                logging.info(f"Analizando aplicación: {app_name}")
                if not deploy(app_name):
                    logging.warning(f"{app_name} sigue en estado {app_status}. Pausando...")
                    pause_application(app_name)
                    notify_slack(f"{app_name} está en estado {app_status} y ha sido pausado.")
            elif app_status == "Paused":
                logging.info(f"Reanudando aplicación pausada: {app_name}")
                resume_application(app_name)
    except Exception as e:
        logging.error(f"Error en el script: {e}")