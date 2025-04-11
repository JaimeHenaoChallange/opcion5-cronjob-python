import time
import logging
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

    attempts = {}
    notified = set()
    paused_apps = set()

    while True:
        try:
            apps = ArgoCDClient.get_applications(timeout=REQUEST_TIMEOUT)
            for app in apps:
                app_name = app.get("metadata", {}).get("name", "Desconocido")
                health_status = app["status"]["health"]["status"]
                sync_status = app["status"]["sync"]["status"]
                current_version = get_app_version(app)

                if app_name not in app_versions:
                    app_versions[app_name] = {"health_status": health_status, "version": current_version}

                if health_status == "Healthy" and sync_status == "Synced":
                    if app_name in notified or app_name in paused_apps:
                        SlackNotifier.send_notification(app_name, "Healthy", attempts.get(app_name, 0), "La aplicación volvió a estar Healthy.")
                        notified.discard(app_name)
                        paused_apps.discard(app_name)
                    attempts[app_name] = 0
                elif sync_status == "OutOfSync":
                    ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                    attempts[app_name] = attempts.get(app_name, 0) + 1
                elif health_status in ["Degraded", "Error"]:
                    if attempts.get(app_name, 0) < 3:
                        ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                        attempts[app_name] = attempts.get(app_name, 0) + 1
                    else:
                        if app_name not in notified:
                            SlackNotifier.send_notification(app_name, health_status, attempts[app_name], "La aplicación fue pausada después de 3 intentos fallidos.")
                            paused_apps.add(app_name)
                            notified.add(app_name)

                app_versions[app_name]["health_status"] = health_status
                app_versions[app_name]["version"] = current_version

            time.sleep(60)
        except Exception as e:
            logging.error(f"Error en el ciclo principal: {e}")
            time.sleep(30)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()