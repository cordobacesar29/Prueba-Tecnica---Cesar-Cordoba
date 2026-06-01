# ARQUITECTURA Y DECISIONES TÉCNICAS - MineCatalog RAG

## Documento de Diseño Técnico

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Ingeniero:** ML Senior & Solution Architect  

---

## 1. RESUMEN EJECUTIVO

Este documento detalla las decisiones arquitectónicas, patrones de diseño y justificaciones técnicas para el sistema RAG de MineCatalog. El sistema fue diseñado bajo principios de:

- **Modularidad:** Componentes independientes y reutilizables
- **Robustez:** Manejo exhaustivo de errores y timeouts
- **Escalabilidad:** Arquitectura preparada para crecimiento
- **Mantenibilidad:** Código limpio, documentado y testeable
- **Seguridad:** Prevención absoluta de alucinaciones de LLM

---

## 2. ARQUITECTURA DEL SISTEMA

### 2.1 Componentes Principales

```
┌─────────────────────────────────────────────────────┐
│  CAPA DE ORQUESTACIÓN (n8n)                        │
│  - Webhook HTTP                                    │
│  - Orquestación de flujo                          │
│  - Integración con OpenAI                         │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────────────────┐
│  CAPA DE APLICACIÓN (FastAPI - main.py)           │
│  - /health   - /search   - /context               │
│  - Validación de inputs                           │
│  - Manejo de errores                              │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  CAPA DE LÓGICA (rag_pipeline.py)                 │
│  - DocumentProcessor                              │
│  - EmbeddingManager                              │
│  - RAGPipeline (orquestador)                     │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────────┐  ┌───────▼──────────┐
│ Procesamiento    │  │ Búsqueda         │
│ de Documentos    │  │ Semántica        │
│ - Ingesta        │  │ - Embeddings     │
│ - Limpieza       │  │ - Similaridad    │
│ - Chunking       │  │ - Ranking        │
└──────────────────┘  └──────────────────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  VECTOR STORE      │
        │  (JSON + Numpy)    │
        └────────────────────┘
```

### 2.2 Flujo de Datos

```
User Query (n8n)
    │
    ├─→ Validation Layer (FastAPI)
    │
    ├─→ Search Layer (RAG Pipeline)
    │   ├─ Query Embedding
    │   ├─ Cosine Similarity
    │   └─ Top-K Retrieval
    │
    ├─→ Context Injection
    │
    ├─→ LLM Processing (OpenAI)
    │   └─ System Prompt + Context + Query
    │
    └─→ Response (Validated)
        └─ Fallback if Hallucination Detected
```

---

## 3. DECISIONES ARQUITECTÓNICAS

### 3.1 ¿Por qué FastAPI en lugar de Flask?

| Aspecto | FastAPI | Flask |
|--------|---------|-------|
| Validación | Automática (Pydantic) | Manual |
| Async | Nativo | Terceros |
| Documentación | Auto (Swagger/OpenAPI) | Manual |
| Performance | 2-3x más rápido | Más lento |
| Curva aprendizaje | Moderada | Muy fácil |

**Decisión:** FastAPI  
**Razón:** Validación automática de datos, mejor performance, y documentación interactiva. Crítico para una API pública y mantenible.

### 3.2 ¿Por qué OpenAI Embeddings?

**Opciones evaluadas:**

1. **OpenAI text-embedding-3-small** ✅ ELEGIDO
   - Dimensionalidad: 1536
   - Costo: $0.02 por 1M tokens
   - Calidad: 62% mejor que v2
   - Velocidad: Rápido
   
2. Sentence Transformers (Local)
   - Ventaja: No costo API
   - Desventaja: Baja calidad, complejidad
   
3. FAISS Vector Store
   - Ventaja: Búsqueda rápida
   - Desventaja: Overhead de mantenimiento

**Decisión:** OpenAI + Fallback Local  
**Razón:** Mejor relación calidad-costo. El fallback local (simple TF) garantiza funcionamiento sin API externa.

### 3.3 ¿Por qué Cosine Similarity y no Búsqueda Vectorial Avanzada?

**Análisis:**

- **Cosine Similarity:** Implementación elegante, O(n) search
- **FAISS/Annoy:** Más rápido para millones de vectores, pero overhead

**Caso de uso:** ~200-500 chunks de documentos  
**Decisión:** Cosine Similarity local  
**Razón:** Suficiente para escala actual. Fácil de entender y debuggear. Vector DB es prematura optimización.

### 3.4 Chunking: RecursiveCharacterTextSplitter vs Simple Split

**Implementado:** Chunking inteligente con overlap

```python
CHUNK_SIZE = 500      # Palabras por chunk
CHUNK_OVERLAP = 50    # Overlap entre chunks (preserva contexto)
```

**Justificación:**
- 500 palabras ≈ 2000 caracteres ≈ 3-4 párrafos
- Preserva coherencia semántica
- Overlap evita corte de ideas en mitad
- Equilibrio entre precisión y eficiencia

### 3.5 Prevención de Alucinaciones: Multi-Capa

```python
# Capa 1: Threshold de Similitud
similarity_threshold = 0.5

# Capa 2: Detección de Patrones
if "creo que" in response or "probablemente" in response:
    # Flag como potencial alucinación

# Capa 3: Inyección de Sistema Prompt
"""
Si no está en la documentación, responde exactamente:
"Lo siento, la información solicitada no se encuentra..."
"""

# Capa 4: Validación Post-LLM
validate_response_against_context()
```

---

## 4. COMPONENTES PRINCIPALES

### 4.1 DocumentProcessor (rag_pipeline.py)

**Responsabilidades:**
- Detectar tipo de archivo automáticamente
- Extraer texto de múltiples formatos
- Limpiar y normalizar texto
- Dividir en chunks inteligentes

**Métodos Clave:**
```python
load_documents(docs_dir)   # Orquestador principal
_load_pdf(file)            # Extracción de PDFs
_load_txt(file)            # Lectura de TXT
_load_md(file)             # Lectura de Markdown
_load_json(file)           # Parseo estructurado JSON
_clean_text(text)          # Normalización
_chunk_text(text)          # Chunking inteligente
```

**Decisión de Diseño:** Método de factory pattern para loaders

```python
# Permite agregar nuevos formatos sin modificar código existente
loaders = {
    '.pdf': self._load_pdf,
    '.txt': self._load_txt,
    '.md': self._load_md,
    '.json': self._load_json
}
```

### 4.2 EmbeddingManager (rag_pipeline.py)

**Responsabilidades:**
- Generar embeddings usando OpenAI
- Calcular similitud coseno
- Implementar fallback local

**Método de Búsqueda:**
```python
def search(query: str, k: int = 3, threshold: float = 0.5):
    """
    1. Generate query embedding
    2. Calculate cosine similarity with all docs
    3. Filter by threshold
    4. Return top-k sorted by similarity
    """
```

**Ventajas del Diseño:**
- Separación de concerns (generación vs búsqueda)
- Fácil de testear
- Permite cambiar estrategia de búsqueda sin afectar resto

### 4.3 RAGPipeline (rag_pipeline.py)

**Patrón:** Facade + Coordinator

```python
class RAGPipeline:
    """
    Coordina:
    - Carga de documentos
    - Generación de embeddings
    - Búsqueda semántica
    
    Interfaz simple:
    - initialize() - Setup
    - search(query) - Búsqueda
    """
```

**Inicialización Lazy:**
```python
@lifespan
async def lifespan(app: FastAPI):
    # Startup: Cargar docs e inicializar pipeline
    rag_pipeline.initialize()
    yield
    # Shutdown: Cleanup
```

### 4.4 FastAPI Application (main.py)

**Endpoints:**

| Endpoint | Método | Propósito | Status |
|----------|--------|----------|--------|
| `/health` | GET | Verificar estado | 200/503 |
| `/search` | POST | Búsqueda semántica | 200/400/500 |
| `/context` | POST | Contexto para LLM | 200/503 |

**Validación con Pydantic:**
```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(3, ge=1, le=10)
    threshold: float = Field(0.5, ge=0.0, le=1.0)
```

**Manejo de Errores:**
```python
@app.exception_handler(HTTPException)
@app.exception_handler(Exception)  # Catch-all general
```

---

## 5. MANEJO DE ERRORES

### 5.1 Matriz de Errores

| Error | Causa | Respuesta | Recovery |
|-------|-------|----------|----------|
| Empty Query | User input | HTTP 400 | Ask for clarification |
| API Timeout | OpenAI down | Fallback embedding | Retry con jitter |
| PDF Corrupted | Bad file | Log + skip | Continue processing |
| No Results | Query mismatch | Fallback message | Escalate to support |
| Invalid API Key | Auth | HTTP 401 | Check .env file |

### 5.2 Logging Strategy

```python
# Niveles
logging.DEBUG    # Detalle granular
logging.INFO     # Eventos importantes
logging.WARNING  # Situaciones anómalas
logging.ERROR    # Errores críticos

# Estructura
logger.info(f"Searching for: {request.query}")
logger.error(f"Search error: {str(e)}", exc_info=True)
```

### 5.3 Timeout Handling

```python
# OpenAI API
timeout = 30  # segundos

# n8n Webhook
HTTP_REQUEST_TIMEOUT = 60

# Retry Strategy
retry_count = 3
backoff_factor = 2  # Exponential backoff
```

---

## 6. INGENIERÍA DE PROMPTS

### 6.1 System Prompt Design

**Principios:**

1. **Ser Explícito sobre Limitaciones**
   ```
   "Responde ÚNICAMENTE basándote en la documentación.
    Si no está, responde: [FALLBACK MESSAGE]"
   ```

2. **Inyectar Contexto Dinámicamente**
   ```
   f"Documentación de referencia:\n{context}"
   ```

3. **Ejemplos de Validación**
   ```
   "Pregunta: X → Respuesta correcta: Y
    Pregunta: A → Respuesta correcta: [FALLBACK]"
   ```

### 6.2 Estrategias de Prevención de Alucinación

**Pre-LLM:**
- Filtrar resultados bajo threshold
- Validar relevancia mínima
- Logging de queries problemáticas

**System Prompt:**
- Instrucciones explícitas de fallback
- Repetir restricciones múltiples veces
- Ejemplos claros

**Post-LLM:**
- Validar respuesta tiene contenido de docs
- Detectar patrones de alucinación
- Fallback si se detecta inventiva

---

## 7. n8n WORKFLOW

### 7.1 Nodos del Workflow

**1. Webhook (Entrada)**
```
Recibe: { "question": "string" }
Emisor: Cliente externo o usuario
```

**2. Search Documentation (HTTP Request)**
```
URL: http://localhost:8000/search
Body: { "query": request.question, "top_k": 3 }
Propósito: Obtener contexto relevante
```

**3. Generate Answer (OpenAI Chat)**
```
System Prompt: Inyecta contexto de Paso 2
User Query: Pregunta original del usuario
Modelo: gpt-4-turbo-preview
```

**4. Response (Salida)**
```
Devuelve: { success, question, answer, context_used }
A: Cliente original
```

### 7.2 Error Handling en n8n

```javascript
// Si Search retorna 0 resultados
if (items[0].$json.results.length === 0) {
    // Devolver respuesta de fallback
    return {
        success: false,
        error: "No relevant documentation found"
    };
}
```

---

## 8. TESTING Y VALIDACIÓN

### 8.1 Test Cases Críticos

**TC-1: Hallucination Prevention**
```
Input: Pregunta no documentada
Expected: Fallback message exacto
Validate: No invención de información
```

**TC-2: Documented Query**
```
Input: "Credenciales incorrectas"
Expected: Detalles de ERR-AUTH-001
Validate: Información correcta de docs
```

**TC-3: API Failure**
```
Trigger: OpenAI timeout
Expected: Graceful error response
Validate: No crash de sistema
```

### 8.2 Métricas de Éxito

| Métrica | Target | Medición |
|---------|--------|----------|
| Hallucination Rate | 0% | Manual + automated checks |
| Documented Query Accuracy | >95% | Comparison vs docs |
| API Latency (p99) | <1s | Response time logs |
| Relevance Score | >0.8 | Similarity metrics |
| System Uptime | 99.9% | Monitoring |

---

## 9. CONSIDERACIONES DE PRODUCCIÓN

### 9.1 Escalabilidad

**Vertical:**
- Aumentar chunk_size para docs más largos
- Cache de embeddings para queries frecuentes
- Batch embeddings generation

**Horizontal:**
- Load balancer frente a múltiples APIs
- Caché distribuido (Redis)
- Vector DB (Pinecone, Weaviate)

### 9.2 Seguridad

```python
# API Key Management
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Nunca hardcodear en código

# Rate Limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

# CORS
CORSMiddleware(allow_origins=ALLOWED_ORIGINS)
```

### 9.3 Monitoreo

```python
# Logging centralizado
import logging
logging.basicConfig(
    handlers=[
        logging.FileHandler("minecatalog_rag.log"),
        logging.StreamHandler()
    ]
)

# Métricas
- Query latency
- Embedding generation time
- Error rates
- Hallucination detection triggers
```

---

## 10. LECCIONES APRENDIDAS Y FUTURAS MEJORAS

### 10.1 Decisiones Futuras

1. **Vector Database (FAISS/Pinecone)**
   - Cuando escala > 10K chunks
   - Búsqueda más rápida

2. **Fine-tuning de Modelo**
   - Entrenar embeddings específicos para MineCatalog
   - Mejorar relevancia

3. **Feedback Loop**
   - Recolectar respuestas correctas/incorrectas
   - Mejorar continuamente

4. **Multi-idioma**
   - Expandir más allá de español
   - Mantener contexto entre idiomas

### 10.2 Patrones Implementados

- **Factory Pattern:** DocumentProcessor loaders
- **Strategy Pattern:** Embedding strategies
- **Facade Pattern:** RAGPipeline
- **Decorator Pattern:** FastAPI middleware
- **Singleton Pattern:** RAG instance global

---

## 11. CONCLUSIÓN

El sistema MineCatalog RAG implementa una arquitectura robusta, modular y escalable que:

1. ✅ Previene alucinaciones de LLM mediante múltiples capas
2. ✅ Proporciona búsqueda semántica precisa
3. ✅ Maneja errores con gracia
4. ✅ Es fácil de entender y mantener
5. ✅ Preparado para escalar en producción

**Código:** Limpio, documentado, modular  
**Testing:** Comprehensive con validación de hallucination  
**Deployment:** Docker-ready, cloud-compatible  

---

**Documento compilado por:** Ingeniero de ML Senior  
**Última revisión:** Mayo 2024  
**Estado:** ✅ Listo para Producción
