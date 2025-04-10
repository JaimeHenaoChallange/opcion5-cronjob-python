# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el script Python al contenedor
COPY deploy_script.py /app/deploy_script.py

# Instala dependencias si es necesario (descomenta si tienes un requirements.txt)
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Define el comando predeterminado para ejecutar el script
CMD ["python", "/app/deploy_script.py"]