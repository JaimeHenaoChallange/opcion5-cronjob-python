import requests
import logging
import urllib3
from config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ArgoCDClient:
    @staticmethod
    def get_applications(timeout=10):
        headers = {"Authorization": f"Bearer {Config.ARGOCD_TOKEN}"}
        try:
            response = requests.get(f"{Config.ARGOCD_API}/applications", headers=headers, verify=False, timeout=timeout)
            response.raise_for_status()
            return response.json().get("items", [])
        except requests.exceptions.RequestException as e:
            logging.error(f"Error al obtener aplicaciones de ArgoCD: {e}")
            return []

    @staticmethod
    def sync_app(app_name, timeout=10):
        headers = {"Authorization": f"Bearer {Config.ARGOCD_TOKEN}", "Content-Type": "application/json"}
        try:
            response = requests.post(f"{Config.ARGOCD_API}/applications/{app_name}/sync", headers=headers, verify=False, json={}, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error al sincronizar la aplicación '{app_name}': {e}")

    @staticmethod
    def refresh_app(app_name, timeout=10):
        headers = {"Authorization": f"Bearer {Config.ARGOCD_TOKEN}"}
        try:
            response = requests.get(f"{Config.ARGOCD_API}/applications/{app_name}?refresh=true", headers=headers, verify=False, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error al actualizar la aplicación '{app_name}': {e}")