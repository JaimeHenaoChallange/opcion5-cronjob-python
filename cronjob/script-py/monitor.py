import time
import logging
import subprocess  # Importar subprocess
from argocd_client import ArgoCDClient
from slack_notifier import SlackNotifier
from config import Config

REQUEST_TIMEOUT = 10
app_versions = {}

def get_app_version(app):
    return app.get("metadata", {}).get("annotations", {}).get("argocd.argoproj.io/revision", "unknown")

def main():
    try:
        Config.validate()
        logging.info("Todas las variables de entorno requeridas están configuradas.")
    except ValueError as e:
        logging.error(f"Error de configuración: {e}")
        raise

    while True:
        try:
            apps = ArgoCDClient.get_applications(timeout=REQUEST_TIMEOUT)
            for app in apps:
                app_name = app.get("metadata", {}).get("name", "Desconocido")
                health_status = app["status"]["health"]["status"]
                sync_status = app["status"]["sync"]["status"]

                # Lógica para manejar aplicaciones...
                logging.info(f"Aplicación: {app_name}, Estado: {health_status}, Sincronización: {sync_status}")

            time.sleep(60)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error al ejecutar un comando de ArgoCD: {e}")
            time.sleep(30)
        except Exception as e:
            logging.error(f"Error en el ciclo principal: {e}")
            time.sleep(30)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()