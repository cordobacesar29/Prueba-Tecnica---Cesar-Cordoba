"""
System prompts and prompt engineering utilities for MineCatalog RAG.
Ensures hallucination prevention and consistent responses.
"""

SYSTEM_PROMPT_TEMPLATE = """Eres un asistente técnico especializado en soporte para MineCatalog, software de catálogo de materiales.

Tu rol es responder preguntas de forma precisa y útil basándote ÚNICAMENTE en la documentación oficial proporcionada. 

REGLA CRÍTICA - RESTRICCIÓN ABSOLUTA DE ALUCINACIÓN:
Si la información solicitada por el usuario NO está explícitamente mencionada en el contexto de documentación proporcionado a continuación, debes responder exactamente con:

"Lo siento, la información solicitada no se encuentra en la documentación interna de MineCatalog. Por favor, contacte a soporte técnico en soporte.minecatalog@empresa.com"

ESTÁ COMPLETAMENTE PROHIBIDO:
- Inventar soluciones o funcionalidades
- Asumir características no documentadas
- Proporcionar información sobre otros sistemas
- Dar consejos no basados en la documentación oficial

DOCUMENTACIÓN DE REFERENCIA:
{context}

DIRECTRICES DE RESPUESTA:
1. Responde siempre en español, usando un tono profesional y amable
2. Si la respuesta está en la documentación, proporciona la solución paso a paso
3. Incluye códigos de error (ej: ERR-AUTH-001) si son relevantes
4. Proporciona causas posibles y soluciones específicas
5. Si la pregunta es ambigua, pide clarificación

EJEMPLOS DE VALIDACIÓN:

Pregunta: "¿Qué significa error 502?"
Respuesta CORRECTA: "Lo siento, la información solicitada no se encuentra en la documentación interna de MineCatalog. Por favor, contacte a soporte técnico en soporte.minecatalog@empresa.com"
(Razón: El error 502 no está documentado en los archivos proporcionados)

Pregunta: "¿Cuáles son las causas posibles del error de credenciales?"
Respuesta CORRECTA: [Proporcionar la sección ERR-AUTH-001 de la documentación con causas y soluciones]

Pregunta: "¿Cómo resuelvo un error de conexión a la base de datos?"
Respuesta CORRECTA: [Proporcionar pasos de solución del error de base de datos con verificaciones específicas]

IMPORTANTE: Antes de responder, verifica que la información esté en el contexto proporcionado.
Cuando dudes, es mejor admitir limitaciones que proporcionar información incorrecta.
"""

FALLBACK_RESPONSE = """Lo siento, la información solicitada no se encuentra en la documentación interna de MineCatalog. Por favor, contacte a soporte técnico en soporte.minecatalog@empresa.com"""

SUPPORT_EMAIL = "soporte.minecatalog@empresa.com"


def build_system_prompt(context: str) -> str:
    """
    Build the final system prompt with injected context.
    
    Args:
        context: Retrieved documentation context
    
    Returns:
        Formatted system prompt
    """
    return SYSTEM_PROMPT_TEMPLATE.format(context=context)


def validate_response_for_hallucination(
    response: str,
    context: str,
    threshold: float = 0.3
) -> tuple[bool, str]:
    """
    Validate if response appears to be hallucinating.
    
    Args:
        response: Generated response from LLM
        context: Retrieved context from documents
        threshold: Confidence threshold
    
    Returns:
        Tuple of (is_valid, validation_message)
    """
    # Check for exact fallback response
    if FALLBACK_RESPONSE.strip() in response or "no se encuentra en la documentación" in response.lower():
        return True, "Response is a valid fallback"
    
    # Check if response references the support email (good sign)
    if SUPPORT_EMAIL in response:
        return True, "Response appropriately references support"
    
    # Simple heuristic: if context is empty and response suggests action, flag it
    if not context or context.strip() == "":
        if any(phrase in response.lower() for phrase in ["debe", "intente", "prueba", "realice"]):
            return False, "Potential hallucination detected: suggesting actions without documentation"
    
    return True, "Response validation passed"


def format_context_for_prompt(search_results: list) -> str:
    """
    Format search results into context string for system prompt.
    
    Args:
        search_results: List of search result dictionaries
    
    Returns:
        Formatted context string
    """
    if not search_results:
        return ""
    
    context_lines = [
        "# Documentación de referencia:\n"
    ]
    
    for i, result in enumerate(search_results, 1):
        content = result.get("content", "")
        similarity = result.get("similarity_score", 0)
        
        context_lines.append(f"\n## Resultado {i} (Relevancia: {similarity:.2%})")
        context_lines.append(content)
    
    return "\n".join(context_lines)


def should_trigger_escalation(query: str, context: str) -> bool:
    """
    Determine if query should be escalated to human support.
    
    Args:
        query: User query
        context: Retrieved context
    
    Returns:
        True if escalation recommended
    """
    # Escalate if no relevant context found
    if not context or len(context) < 50:
        return True
    
    # Escalate on critical keywords
    escalation_keywords = [
        "emergencia",
        "urgente",
        "critico",
        "crash",
        "pérdida de datos",
        "compromiso",
        "seguridad"
    ]
    
    query_lower = query.lower()
    for keyword in escalation_keywords:
        if keyword in query_lower:
            return True
    
    return False


# Configuration for different response modes
RESPONSE_MODES = {
    "strict": {
        "description": "Only answer if high confidence match",
        "similarity_threshold": 0.7,
        "max_tokens": 500
    },
    "balanced": {
        "description": "Standard QA mode",
        "similarity_threshold": 0.5,
        "max_tokens": 1000
    },
    "helpful": {
        "description": "Try to be helpful with lower confidence",
        "similarity_threshold": 0.3,
        "max_tokens": 1500
    }
}


def get_response_config(mode: str = "balanced") -> dict:
    """Get configuration for response mode."""
    return RESPONSE_MODES.get(mode, RESPONSE_MODES["balanced"])
