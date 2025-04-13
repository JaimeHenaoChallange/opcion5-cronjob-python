FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install Flask
# -- habilitar CMD ["false"] para poner artefacto en degraded y comentra el siguiente
#CMD ["false"] 
CMD ["python", "main.py"]
