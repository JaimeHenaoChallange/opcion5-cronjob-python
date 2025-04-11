import subprocess
import logging

class ArgoCDClient:
    @staticmethod
    def get_applications(timeout=10):
        try:
            result = subprocess.run(
                ["argocd", "app", "list", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            result.check_returncode()
            return eval(result.stdout)  # Convierte el JSON a un diccionario
        except subprocess.CalledProcessError as e:
            logging.error(f"Error al obtener aplicaciones de ArgoCD: {e}")
            raise

    @staticmethod
    def sync_app(app_name, timeout=10):
        try:
            subprocess.run(
                ["argocd", "app", "sync", app_name],
                check=True,
                timeout=timeout
            )
            logging.info(f"Sincronización exitosa para la aplicación: {app_name}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error al sincronizar la aplicación {app_name}: {e}")
            raise