# Opción 5: Kubernetes CronJob con Script en Python y Aplicación Flask

Este proyecto incluye una aplicación Flask desplegada con ArgoCD y un CronJob que analiza todas las aplicaciones gestionadas por ArgoCD.

---

## **Descripción**

El CronJob verifica periódicamente el estado de las aplicaciones gestionadas por ArgoCD. Si alguna aplicación está en estado `degraded` o `error`, el script intenta sincronizarla hasta 5 veces. Si después de los intentos sigue fallando, la aplicación se pausa y se envía una notificación a Slack.

---

## **Diagrama de Flujo**

El siguiente diagrama describe el flujo de trabajo del CronJob:

```plaintext
graph TD;
    A[Inicio del CronJob] --> B[Obtener lista de aplicaciones de ArgoCD]
    B -->|Aplicación en estado Healthy| C[Fin]
    B -->|Aplicación en estado Degraded/Error| D[Intentar sincronización]
    D -->|Sincronización exitosa| C
    D -->|Sincronización fallida tras 5 intentos| E[Pausar aplicación]
    E --> F[Enviar notificación a Slack]
    F --> C
```

## Archivos

- `deploy_script.py`: Script en Python que maneja los reintentos y notificaciones.
- `Dockerfile`: Imagen base para ejecutar el script.
- `cronjob.yaml`: Configuración del CronJob en Kubernetes.
- `.env`: Archivo para almacenar configuraciones sensibles relacionadas con ArgoCD (no se sube al repositorio).

## Requisitos Previos

1. **Minikube**: Asegúrate de que Minikube está instalado y corriendo en tu DevContainer.
2. **ArgoCD**: Debe estar instalado en el clúster de Minikube.
3. **Slack Webhook**: Necesitas un webhook de Slack para enviar notificaciones.

## Notas para el Entorno DevContainer

- Este DevContainer incluye `kubectl`, Helm, y Minikube preinstalados y disponibles en el `PATH`.
- Cuando configures Ingress o accedas a servicios en tu clúster, utiliza la IP del nodo de Kubernetes en lugar de `localhost`. Esto se debe a que Kubernetes, por defecto, se vincula a la IP de una interfaz específica en lugar de `localhost` o todas las interfaces.
- Para obtener la IP del nodo de Minikube, ejecuta:
  ```bash
  minikube ip
  ```

## Pasos
1. Inicia Minikube y configura el contexto:
   ```bash
   minikube start
   kubectl config use-context minikube
   ```

2. Crea el namespace para ArgoCD:
   ```bash
   kubectl create namespace argocd
   ```

3. Instala ArgoCD en el namespace argocd:
   ```bash
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

4. Cambia el tipo de servicio de ArgoCD a NodePort:
   ```bash
   kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'
   ```

5. Obtén la contraseña inicial del administrador de ArgoCD:
   ```bash
   kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 --decode; echo
   ```

6. Construye la imagen Docker:
   ```bash
   docker build -t deploy-checker:latest .
   docker build -t <your-dockerhub-username>/microservice:latest .
   docker push <your-dockerhub-username>/microservice:latest
   docker build -t <your-dockerhub-username>/deploy-script:latest cronjob/
   docker push <your-dockerhub-username>/deploy-script:latest
   ```

7. Aplica la configuración del CronJob:
   ```bash
   kubectl apply -f cronjob/cronjob.yaml
   ```

8. Verifica el estado del CronJob:
   ```bash
   kubectl get cronjob -n argocd
   ```

9. Verifica los pods y logs del job:
   ```bash
   kubectl get pods
   kubectl logs <job-pod-name> -n argocd
   ```

10. Configura la aplicación en ArgoCD:
   ```yaml
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: microservice
     namespace: argocd
   spec:
     project: default
     source:
       repoURL: https://github.com/<your-repo>/microservice.git
       targetRevision: HEAD
       path: .
     destination:
       server: https://kubernetes.default.svc
       namespace: default
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
   ```

11. Aplica la configuración de la aplicación:
   ```bash
   kubectl apply -f application.yaml
   ```

12. Aplica la configuración de la aplicación Flask:
   ```bash
   kubectl apply -f app_flask/deployment.yaml
   kubectl apply -f app_flask/service.yaml
   kubectl apply -f app_flask/application.yaml
   ```

13. Verifica el servicio de la aplicación Flask:
   ```bash
   kubectl get svc flask-service -n poc
   ```

## Configuración

### 1. Crear el Archivo `.env`

Crea un archivo `.env` en el directorio del proyecto con el siguiente contenido:

```plaintext
ARGOCD_SERVER=localhost:8080
ARGOCD_USERNAME=admin
ARGOCD_PASSWORD=Thomas#1109
ARTIFACT_NAME=microservice
```

#### **`cronjob.yaml`**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: deploy-checker
  namespace: default
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: deploy-checker
              image: <your-dockerhub-username>/deploy-script:latest
          restartPolicy: OnFailure
```

#### **`app.py`**
```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### **`deploy_script.py`**
```python
import subprocess
import time
import requests

ARGOCD_SERVER = "http://<minikube-ip>:<node-port>"
ARTIFACT_NAME = "microservice"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."

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
```

#### **`Dockerfile`**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install requests
CMD ["python", "deploy_script.py"]
```

1. Construir y subir la imagen Docker de la aplicación Flask:
   ```bash
   docker build -t <your-dockerhub-username>/flask-app:latest .
   docker push <your-dockerhub-username>/flask-app:latest
```

Con estos pasos, tendrás una aplicación Flask gestionada por ArgoCD y un CronJob que analiza todas las aplicaciones del clúster.

## Estructura del Proyecto

```plaintext
opcion5-cronjob-python/
├── app_flask/
│   ├── main.py                # Código de la aplicación Flask
│   ├── Dockerfile             # Dockerfile para la aplicación Flask
│   ├── deployment.yaml        # Despliegue de la aplicación Flask en Kubernetes
│   ├── service.yaml           # Servicio para exponer la aplicación Flask
│   └── application.yaml       # Configuración de ArgoCD para la aplicación Flask
├── cronjob/
│   ├── deploy_script.py       # Script en Python para el CronJob
│   ├── Dockerfile             # Dockerfile para el CronJob
│   └── cronjob.yaml           # Configuración del CronJob en Kubernetes
├── .env                       # Variables de entorno (no se sube al repositorio)
├── .gitignore                 # Archivos ignorados por Git
└── README.md                  # Documentación del proyecto
```

---

### **Notas**

- El diagrama de flujo está en formato Markdown para facilitar su visualización en herramientas compatibles como GitHub.
- La estructura del proyecto está documentada para que sea fácil de entender y navegar.
- Asegúrate de reemplazar `<your-dockerhub-username>` y `<your-repo>` con los valores correspondientes a tu entorno.
