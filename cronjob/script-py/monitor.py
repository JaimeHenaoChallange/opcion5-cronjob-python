import sys
import os
import time
from datetime import datetime
from script_py.argocd_client import ArgoCDClient
from script_py.slack_notifier import SlackNotifier
from concurrent.futures import ThreadPoolExecutor
from prometheus_client import start_http_server, Counter

REQUEST_TIMEOUT = 10  # Tiempo de espera en segundos
EXCLUDED_APPS = ["argocd-monitor", "cronjob-deploy-checker", "cronjob-hello-world", "prometheus", "grafana"]  # Aplicaciones excluidas
ANALYSIS_INTERVAL = 15 * 60  # Intervalo de análisis en segundos (15 minutos)

# Diccionario para rastrear el estado y la versión de las aplicaciones
app_versions = {}

# Métricas de Prometheus
TOTAL_SYNC_ATTEMPTS = Counter("total_sync_attempts", "Número total de intentos de sincronización")

def get_current_time():
    """Devuelve la fecha y hora actual formateada."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_app_version(app):
    """Obtiene la versión de la aplicación desde su etiqueta o anotación."""
    try:
        return app.get("metadata", {}).get("annotations", {}).get("argocd.argoproj.io/revision", "unknown")
    except Exception as e:
        print(f"{get_current_time()} ❌ Error al obtener la versión de la aplicación: {e}")
        return "unknown"

def process_application(app):
    """Procesa una aplicación individual."""
    global app_versions
    try:
        app_name = app.get("metadata", {}).get("name", "Desconocido")

        # Omitir aplicaciones excluidas
        if app_name in EXCLUDED_APPS:
            return

        health_status = app["status"]["health"]["status"]
        sync_status = app["status"]["sync"]["status"]
        current_version = get_app_version(app)

        print(f"{get_current_time()} 🔄 Procesando la aplicación: {app_name}")

        # Realizar refresh solo si la aplicación no está en estado Healthy
        if health_status != "Healthy":
            print(f"{get_current_time()} 🔄 Realizando refresh para la aplicación: {app_name}")
            ArgoCDClient.refresh_app(app_name, timeout=REQUEST_TIMEOUT)

        # Inicializar el estado y la versión si no están registrados
        if app_name not in app_versions:
            app_versions[app_name] = {"health_status": health_status, "version": current_version}

        previous_health_status = app_versions[app_name]["health_status"]
        previous_version = app_versions[app_name]["version"]

        # Verificar el estado de la aplicación
        if health_status == "Healthy" and sync_status == "Synced":
            print(f"{get_current_time()} ✅ '{app_name}' está en estado Healthy y Synced.")
        elif sync_status == "OutOfSync":
            print(f"{get_current_time()} ⚠️ '{app_name}' está OutOfSync. Intentando sincronizar...")
            ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
            TOTAL_SYNC_ATTEMPTS.inc()
        elif health_status in ["Degraded", "Error"]:
            print(f"{get_current_time()} ❌ '{app_name}' está en estado {health_status}.")
            SlackNotifier.send_notification(app_name, health_status, 0, "La aplicación requiere atención.")
        elif health_status in ["Degraded", "Error", "OutOfSync"] and current_version != previous_version:
            print(f"{get_current_time()} ⚠️ '{app_name}' cambió de versión ({previous_version} -> {current_version}).")
        else:
            print(f"{get_current_time()} ℹ️ '{app_name}' está en estado desconocido: {health_status}.")

        # Actualizar el estado y la versión registrados
        app_versions[app_name]["health_status"] = health_status
        app_versions[app_name]["version"] = current_version

    except Exception as e:
        print(f"{get_current_time()} ❌ Error al procesar la aplicación '{app_name}': {e}")

def main():
    global app_versions
    print(f"{get_current_time()} 🔧 Iniciando el monitor de ArgoCD...")

    # Iniciar el servidor HTTP para métricas
    start_http_server(8000)

    while True:
        try:
            print(f"{get_current_time()} 🔍 Obteniendo aplicaciones de ArgoCD...")
            apps = ArgoCDClient.get_applications(timeout=REQUEST_TIMEOUT)

            if not apps:
                print(f"{get_current_time()} ⚠️ No se encontraron aplicaciones o hubo un error al obtenerlas.")
                time.sleep(ANALYSIS_INTERVAL)
                continue

            with ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(process_application, apps)

            print(f"{get_current_time()} ⏳ Esperando {ANALYSIS_INTERVAL // 60} minutos para el próximo análisis...")
            time.sleep(ANALYSIS_INTERVAL)

        except Exception as e:
            print(f"{get_current_time()} ❌ Error en el ciclo principal: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(30)

if __name__ == "__main__":
    main()