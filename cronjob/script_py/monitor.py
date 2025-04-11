import sys
import os
import time
import subprocess
from datetime import datetime
from script_py.argocd_client import ArgoCDClient
from script_py.slack_notifier import SlackNotifier
from concurrent.futures import ThreadPoolExecutorfrom prometheus_client import start_http_server, Counter, Gauge

REQUEST_TIMEOUT = 10  # Tiempo de espera en segundos
GIT_REPO_PATH = "/tmp/argocd-repo"  # Ruta temporal para clonar el repositorio
GIT_REPO_URL = "https://github.com/JaimeHenaoChallange/monitor-argocd-cronjob-1.git"  # URL del repositorioimeHenaoChallange/monitor-argocd-cronjob-1.git"  # URL del repositorio
GIT_BRANCH = "main"  # Rama principalGIT_BRANCH = "main"  # Rama principal

# Diccionario para rastrear el estado y la versión de las aplicacionesa rastrear el estado y la versión de las aplicaciones
app_versions = {}app_versions = {}

# Lista de aplicaciones a excluir de la revisión
EXCLUDED_APPS = ["argocd-monitor", "cronjob-deploy-checker", "cronjob-hello-world"]EXCLUDED_APPS = ["argocd-monitor", "cronjob-deploy-checker", "cronjob-hello-world"]

def get_current_time():
    """Devuelve la fecha y hora actual formateada."""aciones gestionadas")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")HEALTHY_APPS = Gauge("healthy_apps", "Número de aplicaciones en estado Healthy")
graded_apps", "Número de aplicaciones en estado Degraded")
def get_app_version(app):
    """Obtiene la versión de la aplicación desde su etiqueta o anotación."""EMPTS = Counter("sync_attempts", "Número de intentos de sincronización realizados")
    try:
        return app.get("metadata", {}).get("annotations", {}).get("argocd.argoproj.io/revision", "unknown")
    except Exception as e:
        print(f"{get_current_time()} ❌ Error al obtener la versión de la aplicación: {e}")).strftime("%Y-%m-%d %H:%M:%S")
        return "unknown"
p):
def print_separator(): o anotación."""
    """Imprime un separador visual para las aplicaciones."""
    print("\n" + "=" * 50 + "\n")        return app.get("metadata", {}).get("annotations", {}).get("argocd.argoproj.io/revision", "unknown")

def print_result(app_name, status, message):licación: {e}")
    """Imprime el resultado del análisis de una aplicación en un cuadro."""
    print(f"{get_current_time()} 📦 Aplicación: {app_name}")
    print(f"┌{'─' * 48}┐")
    print(f"│ Estado: {status:<40} │")ual para las aplicaciones."""
    print(f"│ {message:<46} │")"\n")
    print(f"└{'─' * 48}┘\n")
message):
def rollback_application(app_name):
    """Realiza un rollback de la aplicación actualizando el repositorio de Git."""t(f"{get_current_time()} 📦 Aplicación: {app_name}")
    try:
        if not os.path.exists(GIT_REPO_PATH):
            subprocess.run(["git", "clone", GIT_REPO_URL, GIT_REPO_PATH], check=True)
        os.chdir(GIT_REPO_PATH)
        subprocess.run(["git", "checkout", GIT_BRANCH], check=True)
        subprocess.run(["git", "revert", "--no-commit", "HEAD"], check=True)
        subprocess.run(["git", "commit", "-m", f"Rollback for application {app_name}"], check=True)e Git."""
        subprocess.run(["git", "push", "origin", GIT_BRANCH], check=True)
        ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
        print(f"{get_current_time()} ✅ Rollback completado para la aplicación '{app_name}'.")T_REPO_URL, GIT_REPO_PATH], check=True)
    except subprocess.CalledProcessError as e:
        print(f"{get_current_time()} ❌ Error al realizar el rollback para '{app_name}': {e}")it", "checkout", GIT_BRANCH], check=True)
    except Exception as e:
        print(f"{get_current_time()} ❌ Error inesperado durante el rollback: {e}")        subprocess.run(["git", "commit", "-m", f"Rollback for application {app_name}"], check=True)
process.run(["git", "push", "origin", GIT_BRANCH], check=True)
def process_application(app):nc_app(app_name, timeout=REQUEST_TIMEOUT)
    """Procesa una aplicación individual."""print(f"{get_current_time()} ✅ Rollback completado para la aplicación '{app_name}'.")
    global app_versions
    try:: {e}")
        app_name = app.get("metadata", {}).get("name", "Desconocido")

        # Omitir aplicaciones excluidas
        if app_name in EXCLUDED_APPS:
            return
 métricas en el puerto 8000
        print_separator()
        health_status = app["status"]["health"]["status"]    try:
        sync_status = app["status"]["sync"]["status"]t_current_time()} 🔧 Iniciando el monitor de ArgoCD...\n")
        current_version = get_app_version(app){get_current_time()} 🌐 ARGOCD_API: {os.getenv('ARGOCD_API', '***')}")
BHOOK_URL') else 'No configurado'}")
        print(f"{get_current_time()} 🔄 Procesando la aplicación: {app_name}\n")GOCD_TOKEN') else 'No configurado'}\n")
        ArgoCDClient.refresh_app(app_name, timeout=REQUEST_TIMEOUT)

        if app_name not in attempts:
            attempts[app_name] = 0
et()
        if app_name not in app_versions:
            app_versions[app_name] = {"health_status": health_status, "version": current_version}

        previous_health_status = app_versions[app_name]["health_status"]n")
        previous_version = app_versions[app_name]["version"]                apps = ArgoCDClient.get_applications(timeout=REQUEST_TIMEOUT)

        if health_status == "Healthy" and sync_status == "Synced":
            print_result(app_name, "✅ Healthy & Synced", "Todo está en orden.")rent_time()} ⚠️ No se encontraron aplicaciones o hubo un error al obtenerlas.\n")
            if app_name in notified or app_name in paused_apps or app_name in problematic_apps:                    time.sleep(30)
                SlackNotifier.send_notification(app_name, "Healthy", attempts[app_name], "La aplicación volvió a estar Healthy.")
                notified.discard(app_name)
                paused_apps.discard(app_name)
                problematic_apps.discard(app_name)licaciones
            attempts[app_name] = 0                healthy_count = sum(1 for app in apps if app["status"]["health"]["status"] == "Healthy")
        elif app_name in paused_apps:Degraded")
            print_result(app_name, "⏸️ Pausada", "Monitoreando su estado...")tus"] == "Error")
        elif sync_status == "OutOfSync":                HEALTHY_APPS.set(healthy_count)
            print_result(app_name, "⚠️ OutOfSync", "Intentando sincronizar...")
            ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
            attempts[app_name] += 1
        elif health_status in ["Degraded", "Error"]:
            problematic_apps.add(app_name)
            if attempts[app_name] < 3:                        app_name = app.get("metadata", {}).get("name", "Desconocido")
                print_result(app_name, "🔄 Recuperando", f"Intento {attempts[app_name] + 1}/3...")
                ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                attempts[app_name] += 1                        if app_name in EXCLUDED_APPS:
                time.sleep(10)
            else:
                if app_name not in notified:
                    print_result(app_name, "❌ Fallido", "Notificando y pausando...")
                    SlackNotifier.send_notification(app_name, health_status, attempts[app_name], "La aplicación fue pausada después de 3 intentos fallidos.")]["status"]
                    paused_apps.add(app_name))
                    notified.add(app_name)
        elif health_status in ["Degraded", "Error", "OutOfSync"] and current_version != previous_version:)} 🔄 Procesando la aplicación: {app_name}\n")
            print_result(app_name, "⚠️ Rollback", "Iniciando rollback...")name, timeout=REQUEST_TIMEOUT)
            rollback_application(app_name)
            SlackNotifier.send_notification(app_name, health_status, 0, f"Rollback realizado para la versión {current_version}.")
        else:
            print_result(app_name, "ℹ️ Desconocido", f"Estado: {health_status}.")
ions:
        app_versions[app_name]["health_status"] = health_status": health_status, "version": current_version}
        app_versions[app_name]["version"] = current_version
    except Exception as e:ersions[app_name]["health_status"]
        print(f"{get_current_time()} ❌ Error al procesar la aplicación '{app_name}': {e}")

def main():nd sync_status == "Synced":
    global app_versionsame, "✅ Healthy & Synced", "Todo está en orden.")
    global attempts, notified, paused_apps, problematic_appsp_name in notified or app_name in paused_apps or app_name in problematic_apps:
    try:ion(app_name, "Healthy", attempts[app_name], "La aplicación volvió a estar Healthy.")
        print(f"{get_current_time()} 🔧 Iniciando el monitor de ArgoCD...\n")
        print(f"{get_current_time()} 🌐 ARGOCD_API: {os.getenv('ARGOCD_API', '***')}")
        print(f"{get_current_time()} 🔗 SLACK_WEBHOOK_URL: {'***' if os.getenv('SLACK_WEBHOOK_URL') else 'No configurado'}")name)
        print(f"{get_current_time()} 🔑 ARGOCD_TOKEN: {'***' if os.getenv('ARGOCD_TOKEN') else 'No configurado'}\n")

        attempts = {}.")
        notified = set()
        paused_apps = set()
        problematic_apps = set()rgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)

        while True:                            SYNC_ATTEMPTS.inc()
            try:
                print(f"{get_current_time()} 🔍 Obteniendo aplicaciones de ArgoCD...\n")
                apps = ArgoCDClient.get_applications(timeout=REQUEST_TIMEOUT)p_name] < 3:
}/3...")
                if not apps:                                ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                    print(f"{get_current_time()} ⚠️ No se encontraron aplicaciones o hubo un error al obtenerlas.\n")  attempts[app_name] += 1
                    time.sleep(30)                                SYNC_ATTEMPTS.inc()
                    continueme.sleep(10)

                with ThreadPoolExecutor(max_workers=5) as executor:if app_name not in notified:
                    executor.map(process_application, apps)rint_result(app_name, "❌ Fallido", "Notificando y pausando...")
      SlackNotifier.send_notification(app_name, health_status, attempts[app_name], "La aplicación fue pausada después de 3 intentos fallidos.")
                time.sleep(60)          paused_apps.add(app_name)

            except Exception as e:                        elif health_status in ["Degraded", "Error", "OutOfSync"] and current_version != previous_version:
                print(f"{get_current_time()} ❌ Error en el ciclo principal: {e}")  print_result(app_name, "⚠️ Rollback", "Iniciando rollback...")
                import traceback                  rollback_application(app_name)







    main()if __name__ == "__main__":        print(f"{get_current_time()} ❌ Error al iniciar el monitor: {e}")    except Exception as e:                time.sleep(30)                traceback.print_exc()                            SlackNotifier.send_notification(app_name, health_status, 0, f"Rollback realizado para la versión {current_version}.")
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