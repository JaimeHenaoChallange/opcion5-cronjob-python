# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el script Python al contenedor
COPY deploy_script.py /app/deploy_script.py

# Instala dependencias si es necesario (descomenta si tienes un requirements.txt)
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Instala el CLI de ArgoCD
RUN apt-get update && apt-get install -y curl && \
    curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64 && \
    chmod +x /usr/local/bin/argocd && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Define el comando predeterminado para ejecutar el script
CMD ["python", "/app/deploy_script.py"]