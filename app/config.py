"""Configuración centralizada. Todo valor operativo llega por entorno."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "corpus.yaml"
INDEX_PATH = ROOT / "data" / "corpus.index.json"

# --- Proveedor LLM -----------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Cadena de respaldo. El nivel gratuito devuelve 503 con frecuencia (medido
# 2026-08-22), por lo que un modelo unico es un punto de fallo.
#
# Ambos modelos deben ser RAPIDOS: un respaldo mas lento que el timeout nunca
# llega a completarse. Medicion 2026-08-22 (mediana / maximo de 3 ejecuciones):
#   gemini-3.1-flash-lite   1.12s / 1.18s   <- primario
#   gemini-3.5-flash-lite   1.01s / 1.01s   <- respaldo
#   gemini-3.6-flash       15.46s / 35.67s  <- DESCARTADO, excede el presupuesto
# Ver ADR-005.
GEN_MODELS = ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite")
EMBED_MODEL = "gemini-embedding-001"
# 768 en lugar de 3072: indice 4x menor y coseno 4x mas rapido en Python puro,
# con perdida de calidad marginal (embeddings truncables). Ver ADR-004.
EMBED_DIM = 768

# `minimal` elimina los tokens de razonamiento: 77% menos consumo y 4x menos
# latencia en la medición del ADR-005.
THINKING_LEVEL = "minimal"
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 800
# Timeout corto deliberado. El nivel gratuito presenta picos de latencia (p95
# medido: 32 s). Esperar 30 s y solo entonces reintentar acumula retraso; es
# preferible cortar pronto y pasar al modelo de respaldo. Ver ADR-005.
LLM_TIMEOUT_S = 12.0
# Cota superior del tiempo total dedicado al proveedor, incluidos reintentos y
# respaldos. Protege frente al timeout (no documentado) de la plataforma.
LLM_BUDGET_S = 25.0
# Presupuesto del embedding de la consulta, que tambien esta en la ruta critica.
EMBED_BUDGET_S = 8.0

# Llamadas simultaneas al proveedor. Medido el 2026-08-22: con 10 peticiones
# concurrentes, el nivel gratuito rechazaba 5 de 30 con HTTP 429. Encolar
# brevemente convierte un error en una espera corta. No protege de un abuso
# sostenido -- para eso hace falta rate limiting en la puerta de entrada
# (ver MODELO-AMENAZAS.md) -- pero absorbe rafagas, que es el caso real.
MAX_CONCURRENT_LLM = 3
# Espera maxima en cola antes de rendirse con 429.
QUEUE_WAIT_S = 6.0

# --- Recuperación ------------------------------------------------------------
TOP_K = 6
# Umbral de abstencion sobre el coseno CRUDO. Calibrado empiricamente el
# 2026-08-22 sobre 8 preguntas en dominio (min 0.663) y 7 fuera (max 0.590).
# Se elige 0.62, por debajo del punto medio 0.627: abstenerse ante una pregunta
# legitima cuesta mas que responder una fuera de dominio, que el prompt ya
# maneja con elegancia. Ver ADR-003.
MIN_SCORE = 0.62

# --- Seguridad ---------------------------------------------------------------
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
