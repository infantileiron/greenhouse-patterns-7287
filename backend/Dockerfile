FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home appuser && mkdir -p /artifacts && chown -R appuser:appuser /app /artifacts
USER appuser
CMD ["uvicorn","src.main:app","--host","0.0.0.0","--port","8000"]
