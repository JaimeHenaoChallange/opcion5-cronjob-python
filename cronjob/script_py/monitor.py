import sys
import os
import time
import subprocess
from datetime import datetime
from script_py.argocd_client import ArgoCDClient
from script_py.slack_notifier import SlackNotifier

REQUEST_TIMEOUT = 10  # Tiempo de espera en segundos
GIT_REPO_PATH = "/tmp/argocd-repo"  # Ruta temporal para clonar el repositorio
GIT_REPO_URL = "https://github.com/JaimeHenaoChallange/monitor-argocd-cronjob-1.git"  # URL del repositorio
GIT_BRANCH = "main"  # Rama principal

# Diccionario para rastrear el estado y la versión de las aplicaciones
app_versions = {}

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

def print_separator():
    """Imprime un separador visual para las aplicaciones."""
    print("\n" + "=" * 50 + "\n")

def print_result(app_name, status, message):
    """Imprime el resultado del análisis de una aplicación en un cuadro."""
    print(f"{get_current_time()} 📦 Aplicación: {app_name}")
    print(f"┌{'─' * 48}┐")
    print(f"│ Estado: {status:<40} │")
    print(f"│ {message:<46} │")
    print(f"└{'─' * 48}┘\n")

def rollback_application(app_name):
    """Realiza un rollback de la aplicación actualizando el repositorio de Git."""
    try:
        if not os.path.exists(GIT_REPO_PATH):
            subprocess.run(["git", "clone", GIT_REPO_URL, GIT_REPO_PATH], check=True)
        os.chdir(GIT_REPO_PATH)
        subprocess.run(["git", "checkout", GIT_BRANCH], check=True)
        subprocess.run(["git", "revert", "--no-commit", "HEAD"], check=True)
        subprocess.run(["git", "commit", "-m", f"Rollback for application {app_name}"], check=True)
        subprocess.run(["git", "push", "origin", GIT_BRANCH], check=True)
        ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
        print(f"{get_current_time()} ✅ Rollback completado para la aplicación '{app_name}'.")
    except subprocess.CalledProcessError as e:
        print(f"{get_current_time()} ❌ Error al realizar el rollback para '{app_name}': {e}")
    except Exception as e:
        print(f"{get_current_time()} ❌ Error inesperado durante el rollback: {e}")

def main():
    global app_versions
    try:
        print(f"{get_current_time()} 🔧 Iniciando el monitor de ArgoCD...\n")
        print(f"{get_current_time()} 🌐 ARGOCD_API: {os.getenv('ARGOCD_API', '***')}")
        print(f"{get_current_time()} 🔗 SLACK_WEBHOOK_URL: {'***' if os.getenv('SLACK_WEBHOOK_URL') else 'No configurado'}")
        print(f"{get_current_time()} 🔑 ARGOCD_TOKEN: {'***' if os.getenv('ARGOCD_TOKEN') else 'No configurado'}\n")

        attempts = {}
        notified = set()
        paused_apps = set()
        problematic_apps = set()

        while True:
            try:
                print(f"{get_current_time()} 🔍 Obteniendo aplicaciones de ArgoCD...\n")
                apps = ArgoCDClient.get_applications(timeout=REQUEST_TIMEOUT)

                if not apps:
                    print(f"{get_current_time()} ⚠️ No se encontraron aplicaciones o hubo un error al obtenerlas.\n")
                    time.sleep(30)
                    continue

                for app in apps:
                    try:
                        print_separator()
                        app_name = app.get("metadata", {}).get("name", "Desconocido")
                        health_status = app["status"]["health"]["status"]
                        sync_status = app["status"]["sync"]["status"]
                        current_version = get_app_version(app)

                        if app_name == "argocd-monitor":
                            print(f"{get_current_time()} ⏩ Excluyendo la aplicación '{app_name}' del análisis.\n")
                            continue

                        print(f"{get_current_time()} 🔄 Procesando la aplicación: {app_name}\n")
                        ArgoCDClient.refresh_app(app_name, timeout=REQUEST_TIMEOUT)

                        if app_name not in attempts:
                            attempts[app_name] = 0

                        if app_name not in app_versions:
                            app_versions[app_name] = {"health_status": health_status, "version": current_version}

                        previous_health_status = app_versions[app_name]["health_status"]
                        previous_version = app_versions[app_name]["version"]

                        if health_status == "Healthy" and sync_status == "Synced":
                            print_result(app_name, "✅ Healthy & Synced", "Todo está en orden.")
                            if app_name in notified or app_name in paused_apps or app_name in problematic_apps:
                                SlackNotifier.send_notification(app_name, "Healthy", attempts[app_name], "La aplicación volvió a estar Healthy.")
                                notified.discard(app_name)
                                paused_apps.discard(app_name)
                                problematic_apps.discard(app_name)
                            attempts[app_name] = 0
                        elif app_name in paused_apps:
                            print_result(app_name, "⏸️ Pausada", "Monitoreando su estado...")
                        elif sync_status == "OutOfSync":
                            print_result(app_name, "⚠️ OutOfSync", "Intentando sincronizar...")
                            ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                            attempts[app_name] += 1
                        elif health_status in ["Degraded", "Error"]:
                            problematic_apps.add(app_name)
                            if attempts[app_name] < 3:
                                print_result(app_name, "🔄 Recuperando", f"Intento {attempts[app_name] + 1}/3...")
                                ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                                attempts[app_name] += 1
                                time.sleep(10)
                            else:
                                if app_name not in notified:
                                    print_result(app_name, "❌ Fallido", "Notificando y pausando...")
                                    SlackNotifier.send_notification(app_name, health_status, attempts[app_name], "La aplicación fue pausada después de 3 intentos fallidos.")
                                    paused_apps.add(app_name)
                                    notified.add(app_name)
                        elif health_status in ["Degraded", "Error", "OutOfSync"] and current_version != previous_version:
                            print_result(app_name, "⚠️ Rollback", "Iniciando rollback...")
                            rollback_application(app_name)
                            SlackNotifier.send_notification(app_name, health_status, 0, f"Rollback realizado para la versión {current_version}.")
                        else:
                            print_result(app_name, "ℹ️ Desconocido", f"Estado: {health_status}.")

                        app_versions[app_name]["health_status"] = health_status
                        app_versions[app_name]["version"] = current_version
                    except Exception as e:
                        print(f"{get_current_time()} ❌ Error al procesar la aplicación '{app_name}': {e}")

                time.sleep(60)

            except Exception as e:
                print(f"{get_current_time()} ❌ Error en el ciclo principal: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(30)
    except Exception as e:
        print(f"{get_current_time()} ❌ Error al iniciar el monitor: {e}")

if __name__ == "__main__":
    main()