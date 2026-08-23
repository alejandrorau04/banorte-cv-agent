"""Tarjeta de agente A2A — `/.well-known/agent-card.json`.

A2A (Agent2Agent) es un estandar de DESCUBRIMIENTO, distinto y complementario a
Open Responses, que es el de CONVERSACION. La tarjeta declara quien es el agente,
que sabe hacer, donde vive su endpoint y como autenticarse; un cliente la lee
antes de enviar nada.

El formulario de alta de la plataforma del reto ofrece importar desde esta
tarjeta y rellenar los campos automaticamente, asi que servirla convierte el
registro manual en un clic.

Se emite un SUPERCONJUNTO de los campos de la v0.3.0 y la v1.0.0: los requisitos
difieren entre versiones y un cliente ignora los campos que no conoce, de modo
que satisfacer ambas cuesta unas lineas y evita apostar por una.

Referencia: https://a2a-protocol.org/v0.3.0/specification/
"""
from __future__ import annotations
from typing import Any

from app import config

PROTOCOLO = "0.3.0"

_HABILIDADES = [
    {
        "id": "trayectoria",
        "name": "Trayectoria profesional",
        "description": ("Responde sobre los puestos, empresas, fechas y responsabilidades "
                        "de Alejandro Rau Lázaro, citando el hecho del CV que respalda "
                        "cada afirmación."),
        "tags": ["cv", "experiencia", "empleo", "trayectoria", "resume", "career"],
        "examples": [
            "¿Dónde trabaja actualmente y desde cuándo?",
            "Lista todas las empresas en orden cronológico",
            "What was his previous job before GlobalConnect?",
        ],
    },
    {
        "id": "competencias",
        "name": "Competencias técnicas y formación",
        "description": ("Responde sobre lenguajes, frameworks, nube, certificaciones e "
                        "idiomas. Ante una tecnología ausente del CV lo reconoce en lugar "
                        "de suponerla."),
        "tags": ["habilidades", "tecnologias", "certificaciones", "skills", "education"],
        "examples": [
            "¿Qué experiencia tiene con inteligencia artificial?",
            "¿Tiene experiencia con Kubernetes?",
            "What are his cloud and DevOps skills?",
        ],
    },
    {
        "id": "disponibilidad",
        "name": "Situación profesional",
        "description": ("Responde sobre disponibilidad, objetivos y motivación. No comparte "
                        "datos de contacto ni expectativa salarial."),
        "tags": ["disponibilidad", "objetivos", "availability", "goals"],
        "examples": [
            "¿Está disponible para trabajar en CDMX?",
            "¿Qué busca en su próximo rol?",
        ],
    },
]


def agent_card(base_url: str) -> dict[str, Any]:
    base = base_url.rstrip("/")
    return {
        "protocolVersion": PROTOCOLO,
        "name": "Agente de CV — Alejandro Rau Lázaro",
        "description": (
            "Agente conversacional bilingüe (español e inglés) sobre la trayectoria "
            "profesional de Alejandro Rau Lázaro. Recuperación aumentada sobre un corpus "
            "verificado y versionado: cada afirmación cita el hecho que la respalda, y "
            "cuando la evidencia recuperada no supera un umbral calibrado el agente lo "
            "reconoce en lugar de improvisar."
        ),
        # Endpoint de conversacion. Es el dato que la plataforma necesita.
        "url": f"{base}/v1",
        "preferredTransport": "HTTP+JSON",
        "version": config.VERSION,
        "capabilities": {
            "streaming": True,             # SSE conforme a Open Responses
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": _HABILIDADES,
        "provider": {
            "organization": "Alejandro Rau Lázaro",
            "url": "https://github.com/alejandrorau04/banorte-cv-agent",
        },
        "documentationUrl": "https://alejandrorau04.github.io/banorte-cv-agent/",
        "securitySchemes": {
            "bearer": {"type": "http", "scheme": "bearer",
                       "description": "Token acordado en el alta del agente."}
        },
        "security": [{"bearer": []}],
        "supportsAuthenticatedExtendedCard": False,
        # Declarado explicitamente: el contrato de conversacion no es A2A.
        "additionalInterfaces": [
            {"url": f"{base}/v1/responses", "transport": "HTTP+JSON",
             "protocolBinding": "HTTP+JSON", "protocolVersion": "2026-04-24"}
        ],
    }
