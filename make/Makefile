.PHONY: setup-prometheus setup-grafana run-tests deploy-cronjob deploy-flask clean

# Configura Prometheus
setup-prometheus:
	@echo "Setting up Prometheus..."
	cd monitoreo && docker-compose up -d prometheus

# Configura Grafana
setup-grafana:
	@echo "Setting up Grafana..."
	cd monitoreo && docker-compose up -d grafana

# Ejecuta pruebas unitarias
run-tests:
	@echo "Running tests..."
	cd tests && pytest

# Despliega el CronJob en Kubernetes
deploy-cronjob:
	@echo "Deploying CronJob..."
	kubectl apply -f cronjob/role.yaml
	kubectl apply -f cronjob/rolebinding.yaml
	kubectl apply -f cronjob/cronjob.yaml
	kubectl apply -f cronjob/application.yaml

# Despliega la aplicación Flask en Kubernetes
deploy-flask:
	@echo "Deploying Flask application..."
	kubectl apply -f app_flask/deployment.yaml
	kubectl apply -f app_flask/service.yaml
	kubectl apply -f app_flask/application.yaml

# Limpia recursos de Kubernetes y detiene Prometheus y Grafana
clean:
	@echo "Cleaning up resources..."
	kubectl delete -f cronjob/role.yaml || true
	kubectl delete -f cronjob/rolebinding.yaml || true
	kubectl delete -f cronjob/cronjob.yaml || true
	kubectl delete -f cronjob/application.yaml || true
	kubectl delete -f app_flask/deployment.yaml || true
	kubectl delete -f app_flask/service.yaml || true
	kubectl delete -f app_flask/application.yaml || true
	cd monitoreo && docker-compose down
