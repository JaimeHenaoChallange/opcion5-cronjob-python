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
ARTIFACT_NAME = os.getenv("ARTIFACT_NAME")

# Cargar el secreto de Kubernetes para el Slack Webhook
def get_slack_webhook():
    kubernetes.config.load_incluster_config()
    v1 = kubernetes.client.CoreV1Api()
    secret = v1.read_namespaced_secret("slack-webhook-secret", "default")
    return secret.data["SLACK_WEBHOOK_URL"]

SLACK_WEBHOOK_URL = get_slack_webhook()

def check_health():
    result = subprocess.run(
        ["argocd", "app", "get", ARTIFACT_NAME, "--output", "json"],
        capture_output=True,
        text=True
    )
    return result.stdout

def deploy():
    for attempt in range(5):
        print(f"Intentando desplegar {ARTIFACT_NAME}, intento {attempt + 1}")
        subprocess.run(["argocd", "app", "sync", ARTIFACT_NAME])
        time.sleep(10)
        health = check_health()
        if "Healthy" in health:
            print(f"{ARTIFACT_NAME} está healthy.")
            return True
    return False

def notify_slack(message):
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})

if __name__ == "__main__":
    if not deploy():
        print(f"{ARTIFACT_NAME} sigue en estado degraded. Pausando...")
        subprocess.run(["argocd", "app", "pause", ARTIFACT_NAME])
        notify_slack(f"{ARTIFACT_NAME} está en estado degraded y ha sido pausado.")