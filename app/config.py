"""Configuración centralizada. Todo valor operativo llega por entorno."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Version del SERVICIO y su contrato (SemVer). No versiona el contenido del CV:
# una correccion del corpus es PATCH; un cambio en la forma de la respuesta que
# un cliente pudiera notar es MINOR o MAJOR. Ver CHANGELOG.md.
VERSION = "1.1.0"

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
# Cadena de modelos de embedding. El corpus se indexa con TODOS: cada modelo
# produce vectores en un espacio distinto, asi que una consulta solo puede
# compararse contra el conjunto generado por su MISMO modelo. Indexar con varios
# convierte la cuota de embeddings -- punto unico de fallo mas grave del sistema,
# porque se invoca en cada peticion -- en algo realmente redundante.
#
# Medido el 2026-08-22: la cuota es `PerProjectPerModel`, de modo que cada modelo
# tiene su propio limite diario. Ver ADR-011.
EMBED_MODELS = ("gemini-embedding-001", "gemini-embedding-2")
EMBED_MODEL = EMBED_MODELS[0]
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
# Cache de embeddings de consulta. Las preguntas sugeridas de la interfaz se
# repiten mucho, y el embedding es la llamada MAS frecuente: se calcula en cada
# peticion, incluso en las que luego se abstienen. Cachearlas elimina esa
# llamada por completo en las repeticiones.
QUERY_CACHE_SIZE = 512

# --- Recuperación ------------------------------------------------------------
TOP_K = 6
# Umbral de abstencion sobre el coseno CRUDO. Calibrado empiricamente el
# 2026-08-22 sobre 8 preguntas en dominio (min 0.663) y 7 fuera (max 0.590).
# Se elige 0.62, por debajo del punto medio 0.627: abstenerse ante una pregunta
# legitima cuesta mas que responder una fuera de dominio, que el prompt ya
# maneja con elegancia. Ver ADR-003.
# Umbral por modelo: la escala del coseno NO es comparable entre modelos, asi
# que cada uno necesita su propia calibracion empirica.
# Calibrado empiricamente el 2026-08-22 con scripts/calibrar.py:
#
#   gemini-embedding-001  dentro min 0.6633 / fuera max 0.5899  -> separacion +0.073
#   gemini-embedding-2    dentro min 0.5593 / fuera max 0.5620  -> SOLAPAMIENTO -0.003
#
# El segundo modelo no separa limpiamente: no existe umbral perfecto. Se elige
# 0.55, que deja pasar todas las preguntas legitimas a costa de que alguna fuera
# de dominio llegue al modelo, donde el prompt la redirige con elegancia. Es el
# mismo criterio asimetrico del ADR-003 y es aceptable porque este modelo solo
# entra como RESPALDO, cuando el primario agota cuota: una compuerta algo menos
# precisa en modo degradado es preferible a un agente que no responde.
MIN_SCORE_BY_MODEL = {
    "gemini-embedding-001": 0.62,
    "gemini-embedding-2": 0.55,
}
MIN_SCORE = MIN_SCORE_BY_MODEL["gemini-embedding-001"]

# --- Seguridad ---------------------------------------------------------------
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Presentacion de fuentes -------------------------------------------------
# Base para enlazar cada cita a las lineas exactas del corpus en el repositorio
# publico. Un identificador tecnico no debe llegar al usuario: se muestra una
# etiqueta legible que enlaza al dato original y puede verificarse con un clic.
CORPUS_URL = os.getenv(
    "CORPUS_URL",
    "https://github.com/alejandrorau04/banorte-cv-agent/blob/main/data/corpus.yaml",
)
# Con `False`, las fuentes se listan sin hipervinculo (clientes que no renderizan
# Markdown). Las citas verificadas siguen en `metadata.citations` en ambos casos.
SOURCES_AS_LINKS = os.getenv("SOURCES_AS_LINKS", "true").lower() != "false"
