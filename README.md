# Option 5: Kubernetes CronJob with Python Script and Flask Application

This project includes a Flask application deployed with ArgoCD and a CronJob that monitors all applications managed by ArgoCD. The CronJob attempts to synchronize applications in a degraded or error state and sends Slack notifications if issues persist.

---

## **Description**

- **Flask Application**: A simple Flask application deployed in Kubernetes and managed by ArgoCD.
- **CronJob**: Periodically checks the health of applications managed by ArgoCD. If an application is in a `Degraded` or `Error` state, it attempts to synchronize it up to 5 times. If the issue persists, the application is paused, and a Slack notification is sent.

---

## **Prerequisites**

1. **Minikube**: Ensure Minikube is installed and running.
2. **ArgoCD**: Installed in the Kubernetes cluster.
3. **Slack Webhook**: A valid Slack webhook URL for notifications.
4. **Docker Hub Account**: For pushing Docker images.
5. **kubectl**: Installed and configured to interact with your Kubernetes cluster.
6. **Python 3.9+**: Required for local testing of Python scripts.
7. **GitHub Actions**: Optional, for automating Docker image builds and pushes.

---

## **Project Structure**

```plaintext
opcion5-cronjob-python/
├── app_flask/
│   ├── main.py                # Flask application code
│   ├── template/              # HTML templates for Flask
│   ├── static/                # Static files (CSS, JS)
│   ├── Dockerfile             # Dockerfile for Flask application
│   ├── deployment.yaml        # Kubernetes Deployment for Flask application
│   ├── service.yaml           # Kubernetes Service for Flask application
│   └── application.yaml       # ArgoCD Application configuration for Flask
├── cronjob/
│   ├── script-py/             # Python scripts for the CronJob
│   │   ├── deploy_script.py   # Main script for managing ArgoCD applications
│   │   ├── monitor.py         # Main loop for monitoring applications
│   │   ├── slack_notifier.py  # Handles Slack notifications
│   │   ├── config.py          # Configuration loader and validator
│   │   ├── argocd_client.py   # Interacts with the ArgoCD API
│   ├── Dockerfile             # Dockerfile for the CronJob
│   ├── cronjob.yaml           # Kubernetes CronJob configuration
│   ├── role.yaml              # Role for accessing secrets
│   ├── rolebinding.yaml       # RoleBinding for accessing secrets
│   └── application.yaml       # ArgoCD Application configuration for CronJob
├── cronjob-test/
│   ├── cronjob-test.yaml      # Test CronJob configuration
│   └── application.yaml       # ArgoCD Application configuration for the test CronJob
├── .github/
│   └── workflows/
│       ├── flask-app-deploy.yml  # GitHub Actions workflow for Flask app
│       └── cronjob-deploy.yml    # GitHub Actions workflow for CronJob
├── .env                       # Environment variables (not committed to Git)
├── .gitignore                 # Files ignored by Git
└── README.md                  # Project documentation
```

---

## **Explanation of Files**

### **1. Files in `script-py/`**

- **`deploy_script.py`**:  
  The main script for managing ArgoCD applications. It handles tasks such as synchronizing applications, checking their health, pausing applications, and sending notifications to Slack. It also includes rollback functionality for applications by interacting with a Git repository.

- **`monitor.py`**:  
  Contains the main loop for monitoring applications. It periodically checks the health and synchronization status of applications and takes appropriate actions (e.g., syncing, pausing, or notifying).

- **`slack_notifier.py`**:  
  Handles sending notifications to Slack using the webhook URL. It formats and sends messages about application statuses and actions taken.

- **`config.py`**:  
  Loads and validates environment variables required for the CronJob. It ensures that all necessary variables (e.g., `ARGOCD_API`, `ARGOCD_TOKEN`, `SLACK_WEBHOOK_URL`) are set.

- **`argocd_client.py`**:  
  Provides functions to interact with the ArgoCD API. It includes methods for listing applications, syncing them, and checking their health. It also handles errors gracefully and logs detailed information about failures.

---

### **2. Files Outside `script-py/`**

- **`Dockerfile`**:  
  Defines the Docker image for the CronJob. It installs Python dependencies, the ArgoCD CLI, and sets up the environment to run the monitoring scripts.

- **`cronjob.yaml`**:  
  Configures the Kubernetes CronJob that runs the monitoring script periodically. It includes environment variables, resource limits, and the service account used for accessing Kubernetes secrets.

- **`role.yaml` and `rolebinding.yaml`**:  
  Define the Role and RoleBinding required for the CronJob to access Kubernetes resources such as secrets and ArgoCD applications.

- **`application.yaml`**:  
  Configures the ArgoCD Application resource for managing the CronJob itself. It ensures that the CronJob is synchronized with the Git repository.

---

## **ConfigMap Explanation**

The `ConfigMap` is used to store configuration data for the CronJob. It includes the URL of the ArgoCD API:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-monitor-config
  namespace: poc
data:
  ARGOCD_API: "https://argocd-server.argocd.svc.cluster.local/api/v1"
```

This `ConfigMap` is mounted into the CronJob as an environment variable (`ARGOCD_API`) to allow the script to communicate with the ArgoCD server.

---

## **Setup Instructions**

### **1. Start Minikube**

1. Start Minikube:
   ```bash
   minikube start
   kubectl config use-context minikube
   ```

2. Verify Minikube is running:
   ```bash
   minikube status
   ```

3. Retrieve the Minikube IP:
   ```bash
   minikube ip
   ```

---

### **2. Install ArgoCD**

1. Create the `argocd` namespace:
   ```bash
   kubectl create namespace argocd
   ```

2. Install ArgoCD:
   ```bash
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

3. Expose the ArgoCD server:
   ```bash
   kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'
   ```

4. Retrieve the initial admin password:
   ```bash
   kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 --decode; echo
   ```

5. Access the ArgoCD UI:
   ```bash
   minikube service argocd-server -n argocd --url
   ```

---

### **3. Obtain the ArgoCD Token**

1. **Enable API Key Capability**:
   Edit the ArgoCD ConfigMap to enable API key generation:
   ```bash
   kubectl edit configmap argocd-cm -n argocd
   ```

   Add the following under `data`:
   ```yaml
   data:
     accounts.admin: apiKey
   ```

2. **Restart the ArgoCD Server**:
   ```bash
   kubectl rollout restart deployment argocd-server -n argocd
   ```

3. **Generate the Token**:
   Use the ArgoCD CLI to generate a token:
   ```bash
   argocd account generate-token --account admin
   ```

   Save the token for use in the `ARGOCD_TOKEN` environment variable.

---

### **4. Create Required Secrets**

1. **Slack Webhook Secret**:
   ```bash
   kubectl create secret generic slack-webhook-secret \
     --namespace poc \
     --from-literal=SLACK_WEBHOOK_URL="https://hooks.slack.com/services/your/webhook/url"
   ```

   Replace `https://hooks.slack.com/services/your/webhook/url` with your actual Slack webhook URL.

2. **ArgoCD Token Secret**:
   ```bash
   kubectl create secret generic argocd-monitor-secret \
     --namespace poc \
     --from-literal=ARGOCD_TOKEN=<your-argocd-token>
   ```

   Replace `<your-argocd-token>` with the token generated in the previous step.

---

### **5. Deploy Resources to Kubernetes**

1. **Flask Application**:
   ```bash
   kubectl apply -f app_flask/deployment.yaml
   kubectl apply -f app_flask/service.yaml
   kubectl apply -f app_flask/application.yaml
   ```

2. **CronJob**:
   ```bash
   kubectl apply -f cronjob/role.yaml
   kubectl apply -f cronjob/rolebinding.yaml
   kubectl apply -f cronjob/cronjob.yaml
   kubectl apply -f cronjob/application.yaml
   ```

3. **Test CronJob**:
   ```bash
   kubectl apply -f cronjob-test/cronjob-test.yaml
   kubectl apply -f cronjob-test/application.yaml
   ```

---

### **6. Verify Deployments**

1. **Check the Flask Service**:
   ```bash
   kubectl get svc flask-service -n poc
   ```

2. **Check the CronJob**:
   ```bash
   kubectl get cronjob argocd-monitor -n poc
   ```

3. **View Logs of CronJob Pods**:
   ```bash
   kubectl logs <pod-name> -n poc
   ```

---

## **Conclusion**

With this setup, the Flask application and CronJob are managed by ArgoCD, ensuring that the repository is the single source of truth. GitHub Actions automates the build and push of Docker images, while ArgoCD handles synchronization and deployment.