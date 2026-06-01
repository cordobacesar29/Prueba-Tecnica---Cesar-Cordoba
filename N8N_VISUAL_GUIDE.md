# DIAGRAMA VISUAL: Integración n8n + Python + OpenAI

## 🔄 FLUJO COMPLETO

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
║                      CLIENTE / USUARIO                          ║
║  (Aplicación web, móvil, Postman, cURL, etc)                  ║
└────────────────────────┬─────────────────────────────────────────┘
                         │ POST /webhook/minecatalog-support
                         │ {"question": "..."}
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
║                         n8n WORKFLOW                            ║
║                    (Puerto: 5678)                              ║
║ ┌────────────────────────────────────────────────────────────┐ ║
║ │ [1] WEBHOOK NODE                                           │ ║
║ │  ├─ Método: POST                                          │ ║
║ │  ├─ Path: minecatalog-support                             │ ║
║ │  └─ Recibe: { "question": "..." }                        │ ║
║ │      ↓ OUTPUT:                                            │ ║
║ │      { body: { question: "..." } }                        │ ║
║ └────────────────────────────────────────────────────────────┘ ║
║                         │                                       ║
║                         ▼                                       ║
║ ┌────────────────────────────────────────────────────────────┐ ║
║ │ [2] HTTP REQUEST NODE (Search API)                        │ ║
║ │  ├─ URL: http://localhost:8000/search                    │ ║
║ │  ├─ Método: POST                                          │ ║
║ │  ├─ Body: {                                              │ ║
║ │  │         "query": "$json.body.question",               │ ║
║ │  │         "top_k": 3,                                   │ ║
║ │  │         "threshold": 0.5                              │ ║
║ │  │       }                                               │ ║
║ │  └─ OUTPUT: { success, results: [...] }                 │ ║
║ └────────────────────────────────────────────────────────────┘ ║
║                         │                                       ║
║                         ▼                                       ║
║ ┌────────────────────────────────────────────────────────────┐ ║
║ │ [3] OPENAI CHAT MODEL NODE                                │ ║
║ │  ├─ Credencial: OpenAI API Key                           │ ║
║ │  ├─ Modelo: gpt-4-turbo-preview                          │ ║
║ │  ├─ System Prompt:                                       │ ║
║ │  │   "Eres asistente MineCatalog..."                     │ ║
║ │  │   "Contexto: $items[1].results"                       │ ║
║ │  ├─ User Message:                                        │ ║
║ │  │   "$json.body.question"                               │ ║
║ │  └─ OUTPUT: { response: "Respuesta..." }                │ ║
║ └────────────────────────────────────────────────────────────┘ ║
║                         │                                       ║
║                         ▼                                       ║
║ ┌────────────────────────────────────────────────────────────┐ ║
║ │ [4] RESPONSE NODE (Webhook Out)                           │ ║
║ │  ├─ Status: 200                                           │ ║
║ │  ├─ Body: {                                              │ ║
║ │  │        "success": true,                               │ ║
║ │  │        "question": "$json.body.question",             │ ║
║ │  │        "answer": "$items[2].response",                │ ║
║ │  │        "context_used": 3,                             │ ║
║ │  │        "timestamp": "2024-05-29..."                   │ ║
║ │  │      }                                                │ ║
║ │  └─ Devuelve al cliente                                 │ ║
║ └────────────────────────────────────────────────────────────┘ ║
└────────────────────────┬──────────────────────────────────────────┘
                         │ HTTP 200 + JSON Response
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
║                   CLIENTE RECIBE RESPUESTA                      ║
║  {                                                             ║
║    "success": true,                                            ║
║    "question": "¿Cuáles son las causas...",                   ║
║    "answer": "Según la documentación...",                     ║
║    "context_used": 3,                                         ║
║    "timestamp": "2024-05-29T22:34:51Z"                       ║
║  }                                                             ║
└━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘
```

---

## 🐍 DETALLE: Python API Backend

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
║          PYTHON API (FastAPI)                         ║
║         (Puerto: 8000)                                ║
║ ┌──────────────────────────────────────────────────┐ ║
║ │ Solicitud n8n:                                   │ ║
║ │ POST /search                                     │ ║
║ │ {                                                │ ║
║ │   "query": "Credenciales incorrectas",          │ ║
║ │   "top_k": 3,                                   │ ║
║ │   "threshold": 0.5                              │ ║
║ │ }                                                │ ║
║ └──────────────────────────────────────────────────┘ ║
║                       │                              ║
║                       ▼                              ║
║ ┌──────────────────────────────────────────────────┐ ║
║ │ MAIN.PY: Validación                             │ ║
║ │ - Verificar query no está vacío                │ ║
║ │ - Validar tipos con Pydantic                   │ ║
║ │ - Log de entrada                               │ ║
║ └──────────────────────────────────────────────────┘ ║
║                       │                              ║
║                       ▼                              ║
║ ┌──────────────────────────────────────────────────┐ ║
║ │ RAG_PIPELINE.PY: Búsqueda Semántica            │ ║
║ │                                                  │ ║
║ │ 1. Generate Query Embedding                    │ ║
║ │    query → OpenAI API → vector (1536 dims)     │ ║
║ │                                                  │ ║
║ │ 2. Calculate Similarity                        │ ║
║ │    Para cada doc:                              │ ║
║ │    similarity = cosine(query_vec, doc_vec)    │ ║
║ │                                                  │ ║
║ │ 3. Filter & Sort                               │ ║
║ │    - Filtrar por threshold (0.5)              │ ║
║ │    - Ordenar descendente por score            │ ║
║ │    - Retornar top 3                           │ ║
║ │                                                  │ ║
║ │ 4. Return Results                              │ ║
║ │    [                                            │ ║
║ │      {                                          │ ║
║ │        "rank": 1,                              │ ║
║ │        "content": "ERR-AUTH-001 causas...",   │ ║
║ │        "similarity_score": 0.92                │ ║
║ │      },                                         │ ║
║ │      ...                                        │ ║
║ │    ]                                            │ ║
║ └──────────────────────────────────────────────────┘ ║
║                       │                              ║
║                       ▼                              ║
║ ┌──────────────────────────────────────────────────┐ ║
║ │ Respuesta HTTP 200:                             │ ║
║ │ {                                                │ ║
║ │   "success": true,                              │ ║
║ │   "results": [                                  │ ║
║ │     {                                            │ ║
║ │       "rank": 1,                                │ ║
║ │       "content": "...",                         │ ║
║ │       "similarity_score": 0.92                  │ ║
║ │     },                                           │ ║
║ │     { "rank": 2, ... },                         │ ║
║ │     { "rank": 3, ... }                          │ ║
║ │   ],                                             │ ║
║ │   "total_results": 3,                           │ ║
║ │   "query": "Credenciales incorrectas"          │ ║
║ │ }                                                │ ║
║ └──────────────────────────────────────────────────┘ ║
└━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 🧠 DETALLE: OpenAI Integration

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
║          n8n → OpenAI Chat Model Node                      ║
┌────────────────────────────────────────────────────────────┐
│ [INPUTS]                                                   │
│                                                            │
│ 1. Credencial: sk-...xxx (tu API key)                    │
│    └─ Verificado mediante test en n8n                   │
│                                                            │
│ 2. System Prompt:                                         │
│    ├─ Define rol: "Eres asistente técnico"              │
│    ├─ Define restricción: "Si no está, responde..."     │
│    ├─ Inyecta contexto:                                 │
│    │  "Documentación: [results[0], results[1], ...]"    │
│    └─ Define formato de respuesta                       │
│                                                            │
│ 3. User Message:                                          │
│    └─ "$json.body.question"                             │
│       ej: "Credenciales incorrectas"                    │
│                                                            │
│ 4. Model: gpt-4-turbo-preview                            │
│ 5. Temperature: 0.7 (creativo pero controlado)           │
│ 6. Max Tokens: 1000                                       │
└────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ [API CALL TO OPENAI]                                       │
│                                                            │
│ POST https://api.openai.com/v1/chat/completions           │
│ {                                                          │
│   "model": "gpt-4-turbo-preview",                        │
│   "messages": [                                           │
│     {                                                     │
│       "role": "system",                                   │
│       "content": "Eres asistente técnico..."             │
│                   "Contexto: [docs]"                     │
│     },                                                    │
│     {                                                     │
│       "role": "user",                                     │
│       "content": "Credenciales incorrectas"              │
│     }                                                     │
│   ],                                                      │
│   "temperature": 0.7,                                     │
│   "max_tokens": 1000                                      │
│ }                                                          │
└────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ [OPENAI PROCESSING]                                        │
│                                                            │
│ 1. Read system prompt (constraints)                       │
│ 2. Analyze user query                                     │
│ 3. Check if info exists in context                       │
│ 4. Generate response respecting constraints              │
│ 5. Return response                                        │
└────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ [RESPONSE FROM OPENAI]                                     │
│                                                            │
│ {                                                          │
│   "choices": [                                            │
│     {                                                     │
│       "message": {                                        │
│         "role": "assistant",                              │
│         "content": "Según la documentación,              │
│                    las causas posibles de..."            │
│       }                                                   │
│     }                                                     │
│   ]                                                       │
│ }                                                          │
│                                                            │
│ n8n extrae: $items[2].$json.response                     │
│ └─ "Según la documentación, las causas..."              │
└────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│ [DEVUELTO A CLIENTE]                                       │
│                                                            │
│ En el nodo Response (Webhook Out), n8n                   │
│ devuelve la respuesta al cliente original                 │
└────────────────────────────────────────────────────────────┘
```

---

## 📊 MAPEO DE VARIABLES EN n8n

```
Referencia rápida de cómo acceder a datos en n8n:

┌─────────────────────────────────────────────────────────────┐
│ NODO 1: Webhook                                             │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Output:                                               │  │
│ │ {                                                     │  │
│ │   "body": {                                           │  │
│ │     "question": "Credenciales incorrectas"           │  │
│ │   }                                                   │  │
│ │ }                                                     │  │
│ │                                                       │  │
│ │ Acceso en n8n:                                       │  │
│ │ $json.body.question                                  │  │
│ │ → "Credenciales incorrectas"                        │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ NODO 2: HTTP Search Request                                 │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Output:                                               │  │
│ │ {                                                     │  │
│ │   "success": true,                                    │  │
│ │   "results": [                                        │  │
│ │     {                                                 │  │
│ │       "rank": 1,                                      │  │
│ │       "content": "ERR-AUTH-001 causas...",          │  │
│ │       "similarity_score": 0.92                        │  │
│ │     },                                                │  │
│ │     { "rank": 2, ... }                                │  │
│ │   ]                                                   │  │
│ │ }                                                     │  │
│ │                                                       │  │
│ │ Acceso en n8n:                                       │  │
│ │ $items[1].$json.body.results                        │  │
│ │ → [{ rank: 1, content: "...", score: 0.92 }, ...]   │  │
│ │                                                       │  │
│ │ Para mapear al System Prompt:                        │  │
│ │ $items[1].$json.body.results                        │  │
│ │   .map(r => r.content)                              │  │
│ │   .join("\n\n")                                       │  │
│ │ → "ERR-AUTH-001 causas...\n\n..."                  │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ NODO 3: OpenAI Chat Model                                   │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Output:                                               │  │
│ │ {                                                     │  │
│ │   "response": "Según la documentación de              │  │
│ │              MineCatalog, las causas posibles..."   │  │
│ │ }                                                     │  │
│ │                                                       │  │
│ │ Acceso en n8n:                                       │  │
│ │ $items[2].$json.response                            │  │
│ │ → "Según la documentación..."                       │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ NODO 4: Response (Webhook Out)                              │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Devuelve al cliente:                                  │  │
│ │ {                                                     │  │
│ │   "success": true,                                    │  │
│ │   "question": "Credenciales incorrectas",            │  │
│ │   "answer": "Según la documentación...",             │  │
│ │   "context_used": 3,                                  │  │
│ │   "timestamp": "2024-05-29T22:34:51Z"               │  │
│ │ }                                                     │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎛️ CONFIGURACIÓN DE CADA NODO (Referencia Rápida)

### Nodo 1: Webhook
```
HTTP Method:      POST
Path:             minecatalog-support
Response Mode:    Response Node
Authentication:   None
```

### Nodo 2: HTTP Request (Search)
```
Method:           POST
URL:              http://localhost:8000/search
Headers:
  Content-Type:   application/json

Body (JSON):
{
  "query": "{{ $json.body.question }}",
  "top_k": 3,
  "threshold": 0.5
}
```

### Nodo 3: OpenAI Chat
```
Authentication:   [Tu Credencial OpenAI]
Model:            gpt-4-turbo-preview
Temperature:      0.7
Max Tokens:       1000

System Prompt:
Eres un asistente técnico especializado en MineCatalog.

RESTRICCIÓN CRÍTICA:
Si la información NO está en el contexto, responde EXACTAMENTE:
"Lo siento, la información solicitada no se encuentra en la documentación 
interna de MineCatalog. Por favor, contacte a soporte técnico en 
soporte.minecatalog@empresa.com"

CONTEXTO DE DOCUMENTACIÓN:
{{ $items[1].$json.body.results.map(r => r.content).join("\n\n") }}

Responde siempre en español.

User Message:
{{ $json.body.question }}
```

### Nodo 4: Response
```
Status Code:      200

Response Body:
{
  "success": true,
  "question": "{{ $json.body.question }}",
  "answer": "{{ $items[2].$json.response }}",
  "context_used": {{ $items[1].$json.body.results.length }},
  "timestamp": "{{ new Date().toISOString() }}"
}
```

---

## 🧪 TABLA DE PRUEBAS

| Caso | Input Query | Expected Behavior | Expected Output |
|------|-------------|-------------------|-----------------|
| 1 | "Credenciales incorrectas" | Respuesta con contexto | ERR-AUTH-001 details |
| 2 | "Error 502" | Fallback (no documentado) | Mensaje de soporte |
| 3 | "" (vacío) | Error HTTP 400 | Validation error |
| 4 | "No se guardan cambios" | Respuesta con contexto | Pasos de solución |
| 5 | Timeout OpenAI | Graceful error | Error message |

---

## 📞 DEBUGGING: Ver Datos en Cada Paso

**En n8n:**

```
1. Click en botón "Execute Workflow" (▶)
2. Esperar a que termine
3. Click en cada nodo para ver OUTPUT
4. Ver exactamente qué datos se pasan
5. Si hay error, aparecerá en rojo

Ejemplo de Debug Output:

[Webhook Output]
{
  "body": {
    "question": "¿Credenciales?"
  }
}

[HTTP Request Output]
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "content": "ERR-AUTH-001...",
      "similarity_score": 0.89
    }
  ]
}

[OpenAI Output]
{
  "response": "Según la documentación..."
}

[Response Output]
Devuelto al cliente ✓
```

---

**Última actualización:** Mayo 2024  
**Versión:** 1.0  
**Estado:** ✅ Listo para usar
