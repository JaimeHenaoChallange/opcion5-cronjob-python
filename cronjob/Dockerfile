# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia todos los archivos Python desde la carpeta script_py al contenedor
COPY script_py/*.py /app/script_py/
COPY script_py/__init__.py /app/script_py/

# Copia el archivo monitor.py al directorio raíz del contenedor
COPY script_py/monitor.py /app/

# Copiar el archivo config.yaml al contenedor
COPY config.yaml /app/config.yaml

# Copia el archivo requirements.txt e instala las dependencias
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Agregar /app al PYTHONPATH
ENV PYTHONPATH=/app

# Instala el CLI de ArgoCD
RUN apt-get update && apt-get install -y curl && \
    curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64 && \
    chmod +x /usr/local/bin/argocd && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Define el comando predeterminado para ejecutar el script
CMD ["python", "/app/monitor.py"]