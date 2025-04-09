FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install requests python-dotenv kubernetes
CMD ["python", "deploy_script.py"]