import subprocess
import time
import requests
import os
from dotenv import load_dotenv
import kubernetes.client
import kubernetes.config

# Cargar variables desde el archivo .env
load_dotenv()

ARGOCD_SERVER = os.getenv("ARGOCD_SERVER")
ARGOCD_USERNAME = os.getenv("ARGOCD_USERNAME")
ARGOCD_PASSWORD = os.getenv("ARGOCD_PASSWORD")

# Cargar el secreto de Kubernetes para el Slack Webhook
def get_slack_webhook():
    kubernetes.config.load_incluster_config()
    v1 = kubernetes.client.CoreV1Api()
    secret = v1.read_namespaced_secret("slack-webhook-secret", "default")
    return secret.data["SLACK_WEBHOOK_URL"]

SLACK_WEBHOOK_URL = get_slack_webhook()

def get_applications():
    result = subprocess.run(
        ["argocd", "app", "list", "--output", "json"],
        capture_output=True,
        text=True
    )
    return result.stdout

def check_health(app_name):
    result = subprocess.run(
        ["argocd", "app", "get", app_name, "--output", "json"],
        capture_output=True,
        text=True
    )
    return result.stdout

def deploy(app_name):
    for attempt in range(5):
        print(f"Intentando desplegar {app_name}, intento {attempt + 1}")
        subprocess.run(["argocd", "app", "sync", app_name])
        time.sleep(10)
        health = check_health(app_name)
        if "Healthy" in health:
            print(f"{app_name} está healthy.")
            return True
    return False

def notify_slack(message):
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})

if __name__ == "__main__":
    apps = get_applications()
    for app in apps:
        app_name = app["name"]
        app_status = app["status"]
        if app_status in ["OutOfSync", "Degraded", "Error"]:
            print(f"Analizando aplicación: {app_name}")
            if not deploy(app_name):
                print(f"{app_name} sigue en estado {app_status}. Pausando...")
                subprocess.run(["argocd", "app", "pause", app_name])
                notify_slack(f"{app_name} está en estado {app_status} y ha sido pausado.")