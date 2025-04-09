# Opción 5: Kubernetes CronJob con Script en Python

Este directorio contiene los archivos necesarios para implementar un CronJob en Kubernetes que ejecuta un script en Python para manejar reintentos de despliegue y notificaciones en Slack.

## Descripción

El CronJob verifica periódicamente el estado de una aplicación gestionada por ArgoCD. Si la aplicación está en estado `degraded` o `error`, el script intenta sincronizarla hasta 5 veces. Si después de los intentos sigue fallando, la aplicación se pausa y se envía una notificación a Slack.

## Archivos

- `deploy_script.py`: Script en Python que maneja los reintentos y notificaciones.
- `Dockerfile`: Imagen base para ejecutar el script.
- `cronjob.yaml`: Configuración del CronJob en Kubernetes.

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
   docker build -t <your-dockerhub-username>/deploy-script:latest .
   docker push <your-dockerhub-username>/deploy-script:latest
   ```

7. Aplica la configuración del CronJob:
   ```bash
   kubectl apply -f cronjob.yaml
   ```

8. Verifica el estado del CronJob:
   ```bash
   kubectl get cronjob
   ```

9. Verifica los pods y logs del job:
   ```bash
   kubectl get pods
   kubectl logs <job-pod-name>
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
