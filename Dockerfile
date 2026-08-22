# Imagen minima: sin dependencias con compilacion nativa y con el indice de
# embeddings ya versionado, el contenedor arranca sin llamar al proveedor.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY data/corpus.yaml data/corpus.index.json ./data/

# Usuario sin privilegios: requisito basico de hardening de contenedores.
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=4).status==200 else 1)"

# Un solo worker: el estado (indice de 92 vectores) es de solo lectura y cabe
# en memoria; escalar se hace con replicas, no con procesos.
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1"]
