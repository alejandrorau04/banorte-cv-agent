"""Conformidad con el contrato Open Responses. Sin red."""
from app.api.openresponses import build_response, error_body, extract_question


def test_response_incluye_los_31_campos_obligatorios(schema):
    required = schema["components"]["schemas"]["ResponseResource"]["required"]
    r = build_response({"model": "cv-agent"}, None)
    assert not [k for k in required if k not in r], "faltan campos obligatorios"
    assert len(required) == 31


def test_no_se_emiten_campos_fuera_del_esquema(schema):
    props = schema["components"]["schemas"]["ResponseResource"]["properties"]
    r = build_response({}, None)
    assert not [k for k in r if k not in props]


def test_object_es_constante_response():
    assert build_response({}, None)["object"] == "response"


def test_anulables_se_emiten_explicitamente_como_null():
    r = build_response({}, None)
    for k in ("incomplete_details", "previous_response_id", "instructions",
              "error", "reasoning", "safety_identifier", "prompt_cache_key"):
        assert k in r and r[k] is None


def test_request_sin_ningun_campo_no_se_rechaza(schema):
    """`CreateResponseBody.required` esta vacio: el servidor aplica defaults."""
    assert schema["components"]["schemas"]["CreateResponseBody"]["required"] == []
    r = build_response({}, None)
    assert r["status"] == "completed" and r["model"] == "cv-agent"


def test_input_admite_las_cuatro_formas():
    assert extract_question({"input": "hola"}) == "hola"
    assert extract_question({"input": [{"role": "user", "content": "hola"}]}) == "hola"
    assert extract_question({"input": [{"type": "message", "role": "user",
        "content": [{"type": "input_text", "text": "hola"}]}]}) == "hola"
    assert extract_question({}) == ""
    assert extract_question({"input": None}) == ""


def test_multiturno_toma_el_ultimo_mensaje_de_usuario():
    body = {"input": [
        {"role": "user", "content": "primera"},
        {"role": "assistant", "content": "respuesta"},
        {"role": "user", "content": "segunda"},
    ]}
    assert extract_question(body) == "segunda"


def test_error_tiene_la_forma_del_contrato():
    e = error_body("x", "invalid_request", "invalid_api_key")["error"]
    assert set(e) == {"message", "type", "code"}
    assert e["type"] in {"server_error", "invalid_request", "not_found",
                         "model_error", "too_many_requests"}


def test_la_tarjeta_a2a_trae_los_campos_obligatorios():
    """A2A v0.3.0 exige diez campos; v1.0.0 anade otros. Se emiten ambos
    conjuntos porque un cliente ignora los que no conoce."""
    from app.api.agentcard import agent_card
    c = agent_card("https://ejemplo.test")
    for campo in ("protocolVersion", "name", "description", "url",
                  "preferredTransport", "version", "capabilities",
                  "defaultInputModes", "defaultOutputModes", "skills"):
        assert campo in c, f"falta {campo}"
    assert c["url"].startswith("https://")
    assert c["capabilities"]["streaming"] is True
    assert c["skills"], "sin habilidades declaradas"
    for s in c["skills"]:
        assert {"id", "name", "description", "tags"} <= set(s)
        assert s["tags"] and s["examples"]


def test_la_tarjeta_no_expone_datos_de_contacto():
    """Mismo criterio que el corpus: la tarjeta es publica y sin autenticacion."""
    import json
    import re
    from app.api.agentcard import agent_card
    texto = json.dumps(agent_card("https://ejemplo.test"), ensure_ascii=False)
    assert not re.search(r"[\w.+-]+@[\w-]+\.\w+|\b\d{2}\s?\d{4}\s?\d{4}\b", texto)
