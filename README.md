# Kubernetes CronJob Monitoring with Prometheus, Grafana, and Flask Application

This project includes:
1. A **Flask application** deployed in Kubernetes and managed by ArgoCD.
2. A **CronJob** that monitors applications managed by ArgoCD, attempts to synchronize degraded applications, and sends Slack notifications for persistent issues.
3. Integration with **Prometheus** and **Grafana** for metrics collection and visualization.
4. A **configuration file (`config.yaml`)** for centralized management of settings.
5. **Unit tests** for validating the functionality of the ArgoCD client.
6. A **Makefile** to simplify setup, testing, and deployment tasks.

---

## **Features**

1. **Application Monitoring**:
   - Periodically checks the health of applications managed by ArgoCD.
   - Attempts to synchronize applications in a degraded or error state.
   - Sends Slack notifications for persistent issues.

2. **Metrics Integration**:
   - Exposes metrics via Prometheus for monitoring the CronJob's performance.
   - Visualizes metrics using Grafana.

3. **Flask Application**:
   - A simple web application for generating geometric shapes.

4. **Configuration Management**:
   - Centralized configuration using `config.yaml` for excluded applications, API endpoints, and sync attempts.

5. **Testing**:
   - Includes unit tests for the ArgoCD client.

6. **Makefile**:
   - Simplifies setup, testing, and deployment tasks.

---

## **Setup Instructions**

### **1. Configure Prometheus and Grafana**

1. Navigate to the `monitoreo` directory:
   ```bash
   cd /workspaces/monitor-3.1/opcion5-cronjob-python/monitoreo
   ```

2. Start Prometheus and Grafana using Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Access Prometheus at:
   ```
   http://localhost:9090
   ```

4. Access Grafana at:
   ```
   http://localhost:3000
   ```
   Default credentials:
   - Username: `admin`
   - Password: `admin`

---

### **2. Add New Applications to Monitoring**

1. Update the `config.yaml` file in the `cronjob` directory:
   ```yaml
   excluded_apps:
     - argocd-monitor
     - cronjob-deploy-checker
     - cronjob-hello-world
     - <new-app-name>
   ```

2. Apply the updated configuration:
   ```bash
   kubectl apply -f /workspaces/monitor-3.1/opcion5-cronjob-python/cronjob/config.yaml
   ```

---

### **3. Run Tests**

1. Navigate to the `tests` directory:
   ```bash
   cd /workspaces/monitor-3.1/opcion5-cronjob-python/tests
   ```

2. Run the tests using `pytest`:
   ```bash
   pytest
   ```

---

### **4. Use the Makefile**

The `Makefile` simplifies common tasks. Use the following commands:

1. **Set up Prometheus**:
   ```bash
   make setup-prometheus
   ```

2. **Set up Grafana**:
   ```bash
   make setup-grafana
   ```

3. **Run Tests**:
   ```bash
   make run-tests
   ```

4. **Deploy the CronJob**:
   ```bash
   make deploy-cronjob
   ```

5. **Deploy the Flask Application**:
   ```bash
   make deploy-flask
   ```

6. **Clean Up Resources**:
   ```bash
   make clean
   ```

---

### **5. Verify Deployments**

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

### **6. Metrics Integration**

1. **Prometheus Configuration**:
   - The Prometheus configuration is located in `monitoreo/prometheus-config.yaml`.
   - It scrapes metrics from the CronJob at `localhost:8000`.

2. **Grafana Configuration**:
   - The Grafana data source is configured in `monitoreo/grafana-datasource.yaml`.
   - It connects to Prometheus at `http://prometheus:9090`.

3. **Exposed Metrics**:
   - **Total Applications**: Number of applications managed by ArgoCD.
   - **Healthy Applications**: Number of applications in a `Healthy` state.
   - **Degraded Applications**: Number of applications in a `Degraded` state.
   - **Error Applications**: Number of applications in an `Error` state.
   - **Sync Attempts**: Number of synchronization attempts made by the CronJob.

4. **Access Metrics**:
   - Prometheus scrapes metrics from the CronJob at `http://localhost:8000`.

---

### **7. Configuration Management**

1. **Centralized Configuration**:
   - The `config.yaml` file in the `cronjob` directory centralizes settings for the CronJob.

2. **Example Configuration**:
   ```yaml
   argocd_api: "http://argocd-server.argocd.svc.cluster.local/api/v1"
   excluded_apps:
     - argocd-monitor
     - cronjob-deploy-checker
     - cronjob-hello-world
   max_sync_attempts: 3
   ```

3. **Apply Configuration**:
   ```bash
   kubectl apply -f /workspaces/monitor-3.1/opcion5-cronjob-python/cronjob/config.yaml
   ```

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
│   ├── config.yaml            # Centralized configuration for the CronJob
│   └── application.yaml       # ArgoCD Application configuration for CronJob
├── monitoreo/
│   ├── prometheus-config.yaml # Prometheus configuration
│   ├── grafana-datasource.yaml # Grafana data source configuration
│   ├── docker-compose.yaml    # Docker Compose for Prometheus and Grafana
├── tests/
│   ├── test_argocd_client.py  # Unit tests for the ArgoCD client
├── .github/
│   └── workflows/
│       ├── flask-app-deploy.yml  # GitHub Actions workflow for Flask app
│       └── cronjob-deploy.yml    # GitHub Actions workflow for CronJob
├── .env                       # Environment variables (not committed to Git)
├── .gitignore                 # Files ignored by Git
├── Makefile                   # Simplifies setup, testing, and deployment tasks
└── README.md                  # Project documentation
```

---

## **Conclusion**

This solution integrates a Flask application and a CronJob with Prometheus and Grafana for monitoring. The `Makefile` simplifies deployment and testing tasks, while the `config.yaml` centralizes configuration management. If you encounter any issues, refer to the documentation or reach out for support.