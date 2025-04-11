# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia todos los archivos Python desde la carpeta script-py al contenedor
COPY script-py/*.py /app/

# Copia el archivo requirements.txt e instala las dependencias
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Instala el CLI de ArgoCD
RUN apt-get update && apt-get install -y curl && \
    curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64 && \
    chmod +x /usr/local/bin/argocd && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Define el comando predeterminado para ejecutar el script
CMD ["python", "/app/monitor.py"]