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
# 2026-08-22), por lo que un modelo único es un punto de fallo. Ver ADR-004.
GEN_MODELS = ("gemini-3.1-flash-lite", "gemini-3.6-flash")
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
