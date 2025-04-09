FROM python:3.9-slim
WORKDIR /app
COPY . .
ENV PIP_INDEX_URL=https://pypi.org/simple
RUN pip install Flask
CMD ["python", "main.py"]