# MineCatalog RAG Support Assistant

Sistema RAG (**Retrieval-Augmented Generation**) automatizado para soporte técnico de MineCatalog. Integra búsqueda semántica, procesamiento de documentos multiformato, y generación de respuestas con OpenAI a través de n8n.

---

## 📋 TABLA DE CONTENIDOS

1. [Inicio Rápido (5 minutos)](#-inicio-rápido-5-minutos)
2. [Arquitectura General](#-arquitectura-general)
3. [main.py - API Backend](#-mainpy---api-backend)
4. [rag_pipeline.py - Motor de Búsqueda](#-rag_pipelinepy---motor-de-búsqueda)
5. [Integración con n8n](#-integración-con-n8n)
6. [Configuración](#-configuración)
7. [Uso de Endpoints](#-uso-de-endpoints)
8. [Troubleshooting](#-troubleshooting)

---

## ⚡ INICIO RÁPIDO (5 MINUTOS)

### 1. Instalar Dependencias (1 min)

```bash
cd "c:\Users\César\César\Prueba Técnica - César Córdoba"
pip install -r requirements.txt
```

### 2. Configurar Entorno (1 min)

```bash
# Copiar template
cp .env.example .env

# Editar en Windows:
notepad .env
# Reemplazar: OPENAI_API_KEY=sk-tu-clave-real
```

### 3. Iniciar API (1 min)

```bash
python main.py
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Starting MineCatalog RAG API...
INFO:     Loaded 156 document chunks
INFO:     RAG pipeline initialized successfully
```

### 4. Verificar Salud (1 min)

```bash
curl http://localhost:8000/health

# Respuesta esperada:
# {"status":"healthy","rag_initialized":true}
```

### 5. Probar Búsqueda (1 min)

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"¿No se guardan los cambios?","top_k":3,"threshold":0.5}'
```

---

## 🏗️ ARQUITECTURA GENERAL

### Flujo de Datos

```
┌─────────────────────────────────────────────────────┐
│  USUARIO / INTERFAZ WEB                            │
│  http://localhost:8000/ui                          │
└──────────────────┬──────────────────────────────────┘
                   │ POST /ask
┌──────────────────▼──────────────────────────────────┐
│  CAPA DE APLICACIÓN (main.py - FastAPI)            │
│  - Validación Pydantic                             │
│  - Manejo de errores                               │
│  - CORS middleware                                 │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
   /health    /search    /context
        │          │          │
┌──────────────────▼──────────────────────────────────┐
│  CAPA DE LÓGICA (rag_pipeline.py)                  │
│  - DocumentProcessor (carga & chunking)            │
│  - EmbeddingManager (búsqueda semántica)           │
│  - RAGPipeline (orquestador)                       │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
    /docs (archivos)   OpenAI API (embeddings)
         │                    │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  VECTOR STORE      │
         │  (Numpy arrays)    │
         └────────────────────┘
```

### Componentes Principales

```
┌─────────────────────────────────────────────────────┐
│              MINECATALOG RAG SYSTEM                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. FastAPI Server (main.py)                        │
│     ✓ 3 Endpoints: /health, /search, /context      │
│     ✓ Validación automática (Pydantic)             │
│     ✓ CORS habilitado                              │
│     ✓ Manejo de errores exhaustivo                 │
│                                                     │
│  2. RAG Pipeline (rag_pipeline.py)                 │
│     ✓ DocumentProcessor: carga múltiples formatos  │
│     ✓ EmbeddingManager: búsqueda semántica         │
│     ✓ RAGPipeline: orquestador principal           │
│                                                     │
│  3. n8n Integration                                │
│     ✓ Webhook para recibir preguntas               │
│     ✓ HTTP Request al backend                      │
│     ✓ OpenAI Chat Model                            │
│     ✓ Response formatting                          │
│                                                     │
│  4. Frontend Web                                    │
│     ✓ UI estática (frontend/index.html)            │
│     ✓ Proxy /ask para evitar CORS                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📋 main.py - API BACKEND

### ¿QUÉ ES main.py?

`main.py` es un **servidor FastAPI** que actúa como el **puente central** del sistema MineCatalog RAG. Conecta:
- 📚 **Búsqueda semántica** (rag_pipeline)
- 🤖 **LLM** (OpenAI vía n8n)
- 🌐 **Clientes** (navegador, n8n, aplicaciones externas)

### FUNCIONES PRINCIPALES

#### 1. `lifespan()` - Ciclo de vida de la app

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Carga los documentos en memoria
    rag_pipeline = RAGPipeline(docs_dir, chunk_size, chunk_overlap)
    rag_pipeline.initialize()
    
    yield
    
    # Shutdown: Limpia recursos
```

**Parámetros desde `.env`:**
- `DOCS_DIR_PATH`: Carpeta de documentos
- `CHUNK_SIZE`: Tamaño de fragmentos (500 por defecto)
- `CHUNK_OVERLAP`: Solapamiento (50 por defecto)

#### 2. `/search` - Búsqueda Semántica

**Endpoints:**
- `POST /search` - JSON body (Swagger)
- `GET /search` - Query parameters (n8n)

**Parámetros:**
```json
{
  "query": "¿No se guardan los cambios?",
  "top_k": 3,           // Resultados a retornar
  "threshold": 0.5      // Score mínimo (0-1)
}
```

**Respuesta:**
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "content": "...",
      "similarity_score": 0.87
    }
  ],
  "total_results": 1,
  "query": "¿No se guardan los cambios?"
}
```

#### 3. `/context` - Contexto para LLMs

Similar a `/search` pero retorna texto formateado para inyectar en prompts de OpenAI.

**Respuesta:**
```json
{
  "success": true,
  "context": "- Doc1 content\n- Doc2 content",
  "num_results": 2,
  "threshold_used": 0.5
}
```

#### 4. `/health` - Health Check

```json
{
  "status": "healthy",
  "rag_initialized": true
}
```

#### 5. `/ask` - Proxy a n8n

Evita problemas CORS llamando a n8n desde el backend.

### CARACTERÍSTICAS DE SEGURIDAD

- ✅ **CORS habilitado** - Permite llamadas desde cualquier origen
- ✅ **Validación Pydantic** - Valida todos los inputs
- ✅ **Manejo robusto de errores** - Respuestas claras
- ✅ **Timeouts en webhooks** - 30 segundos máximo
- ✅ **Logging completo** - Registra todas las operaciones

### MODELOS DE DATOS

| Modelo | Propósito |
|--------|-----------|
| `SearchRequest` | Valida queries (soporta "question" de n8n) |
| `SearchResult` | Un resultado individual |
| `SearchResponse` | Respuesta con lista de resultados |
| `AskRequest` | Pregunta para el asistente |
| `ErrorResponse` | Error estandarizado |

---

## 🔍 rag_pipeline.py - MOTOR DE BÚSQUEDA

### ¿QUÉ ES rag_pipeline.py?

`rag_pipeline.py` es el **corazón del sistema de búsqueda semántica**. RAG = **"Retrieval-Augmented Generation"** (Generación Aumentada por Recuperación).

Coordina todo el proceso de:
1. Cargar documentos
2. Procesarlos (limpiar, chunquear)
3. Convertirlos a vectores (embeddings)
4. Buscar información relevante

### ESTRUCTURA - 3 CLASES PRINCIPALES

#### 1. `DocumentProcessor` - Carga y Procesa

**Soporta 4 formatos:** PDF, TXT, Markdown, JSON

| Método | Qué hace |
|--------|----------|
| `load_documents()` | Carga recursivamente de `/docs` |
| `_load_pdf()` | Extrae texto de PDFs |
| `_load_txt/md/json()` | Lee archivos de texto/markdown/JSON |
| `_clean_text()` | Normaliza (espacios, URLs, caracteres) |
| `_chunk_text()` | Divide en fragmentos con solapamiento |

**¿Por qué chunks con overlap?**

Evita perder contexto en bordes:
```
Texto: "La autenticación es importante. Es crítico para seguridad."
Chunk 1: "La autenticación es importante. Es crítico"
Chunk 2: "crítico para seguridad."
         ↑ palabra en ambos chunks = continuidad
```

#### 2. `EmbeddingManager` - Convierte Texto en Vectores

Transforma documentos en **vectores numéricos** para comparación semántica.

**Dos modos:**

**Modo 1: OpenAI (Recomendado)**
```
Texto → API OpenAI → Vector 1536-dimensional
Ventajas: Preciso semánticamente
Desventajas: Requiere API key y costo
```

**Modo 2: Fallback (Sin costo)**
```
Texto → Frecuencia de Palabras → Vector simple
Ventajas: Sin costo, funciona offline
Desventajas: Menos preciso
```

| Método | Propósito |
|--------|-----------|
| `generate_embeddings()` | Crea vectores para todos los docs |
| `_generate_openai_embeddings()` | Usa OpenAI API |
| `_generate_fallback_embeddings()` | Usa frecuencia de palabras (TF) |
| `cosine_similarity()` | Calcula similitud entre vectores |
| `search()` | Busca docs similares a query |

**¿Qué es Cosine Similarity?**

Mide el ángulo entre dos vectores:
```
Similitud 1.0 = Máxima (misma dirección)
Similitud 0.5 = Media
Similitud 0.0 = Mínima (perpendiculares)

Ejemplo:
Query: "¿Cómo login?"
Doc1: "Autenticación con contraseña"  → 0.87 ✓ RELEVANTE
Doc2: "Precios del producto"          → 0.15 ✗ NO RELEVANTE
```

#### 3. `RAGPipeline` - Orquestador

Coordina `DocumentProcessor` + `EmbeddingManager`.

| Método | Propósito |
|--------|-----------|
| `initialize()` | Carga docs y genera embeddings (startup) |
| `search()` | Recibe query y retorna documentos relevantes |

### FLUJO DE DATOS COMPLETO

```
┌─────────────────────────────────────────────────────────┐
│           RAG PIPELINE - FLUJO COMPLETO                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  INICIALIZACIÓN (una sola vez)                         │
│  ──────────────────────────────                         │
│  1. DocumentProcessor carga archivos (/docs)           │
│     - PDF → extrae texto                               │
│     - TXT/MD/JSON → lee contenido                       │
│                                                         │
│  2. _clean_text(): elimina ruido                        │
│     - URLs, espacios extras, caracteres especiales     │
│                                                         │
│  3. _chunk_text(): divide en fragmentos ~500 chars     │
│     - Con overlap del 10% para continuidad             │
│                                                         │
│  4. EmbeddingManager genera vectores                    │
│     - OpenAI: 1536 dimensiones (recomendado)           │
│     - Fallback: frecuencia de palabras                 │
│                                                         │
│  BÚSQUEDA (cada query del usuario)                     │
│  ────────────────────────────────────                  │
│  5. Usuario pregunta: "¿Cómo login?"                   │
│                                                         │
│  6. Se genera vector de la query                        │
│                                                         │
│  7. Cosine similarity: query vs todos los documentos   │
│     - Doc1: 0.87 ← RELEVANTE                           │
│     - Doc2: 0.45 ← BAJO                                │
│     - Doc3: 0.92 ← MUY RELEVANTE                       │
│                                                         │
│  8. Filtro por threshold (default: 0.5)                │
│     - Solo retorna docs con score ≥ 0.5               │
│                                                         │
│  9. Retorna top-k resultados (default: 3)              │
│     - Ordenados por similaridad (descendente)          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### PARÁMETROS CONFIGURABLES

```python
RAGPipeline(docs_dir, chunk_size, chunk_overlap)
```

| Parámetro | Default | Rango | Impacto |
|-----------|---------|-------|---------|
| `chunk_size` | 500 | 100-2000 | Tamaño de cada fragmento |
| `chunk_overlap` | 50 | 0-200 | Repetición entre chunks |
| `top_k` | 3 | 1-10 | Resultados a retornar |
| `threshold` | 0.5 | 0-1 | Similaridad mínima |

---

## 🔌 INTEGRACIÓN CON n8n

### Instalación de n8n

#### Opción 1: Docker (Recomendado)

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  n8nio/n8n:latest
```

Acceder: http://localhost:5678

#### Opción 2: Node.js Local

```bash
npm install -g n8n
n8n
```

#### Opción 3: n8n Cloud

```
https://n8n.cloud
```

### Estructura del Workflow

```
Webhook (Recibe pregunta)
    ↓
HTTP Request (Busca en backend)
    ↓
OpenAI Chat (Genera respuesta)
    ↓
Response (Devuelve resultado)
```

### CONFIGURACIÓN DE NODOS

#### Nodo 1: Webhook

```
Method: POST
Path: minecatalog-support
Response Mode: Response Node
Authentication: None
```

#### Nodo 2: HTTP Request

```
Method: GET
URL: http://127.0.0.1:8000/search
Body (JSON):
{
  "query": "{{ $json.body.question }}",
  "top_k": 3,
  "threshold": 0.5
}
```

#### Nodo 3: OpenAI Chat

```
Model: gpt-4-turbo o gpt-4.1-mini
System Prompt:
Eres un asistente técnico para MineCatalog.
Si la información NO está en el contexto, responde EXACTAMENTE:
"Lo siento, la información solicitada no se encuentra en la documentación 
interna de MineCatalog. Por favor, contacte a soporte técnico."

Contexto:
{{ $items[1].$json.results.map(r => r.content).join("\n\n") }}

User Message:
{{ $json.body.question }}
```

#### Nodo 4: Response

```
Response Body:
{
  "success": true,
  "question": "{{ $json.body.question }}",
  "answer": "{{ $items[2].$json.response }}",
  "context_used": {{ $items[1].$json.total_results }},
  "timestamp": "{{ new Date().toISOString() }}"
}
```

### URLs CRÍTICAS

| Componente | URL | Uso |
|---|---|---|
| Backend Health | http://localhost:8000/health | Estado RAG |
| Backend Search | http://localhost:8000/search | Búsqueda |
| Backend Swagger | http://localhost:8000/docs | Probar endpoints |
| UI Web | http://localhost:8000/ui | Demo |
| n8n Editor | http://localhost:5678 | Editar workflow |
| n8n Test Webhook | http://localhost:5678/webhook-test/minecatalog-support | Pruebas |
| n8n Prod Webhook | http://localhost:5678/webhook/minecatalog-support | Producción |

---

## ⚙️ CONFIGURACIÓN

### Variables de Entorno (.env)

```env
# OpenAI
OPENAI_API_KEY=sk-tu-clave-aqui
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Documentación
DOCS_DIR_PATH=./docs

# RAG Pipeline
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# n8n (opcional)
N8N_WEBHOOK_URL=http://localhost:5678/webhook-test/minecatalog-support
```

### Estructura de Carpetas

```
minecatalog-rag/
├── main.py                    # FastAPI server
├── rag_pipeline.py           # RAG processing
├── prompt_engineering.py     # LLM prompts
├── n8n_workflow.json         # Workflow n8n
├── tests.py                  # Test suite
├── requirements.txt          # Dependencies
├── .env.example              # Config template
├── .gitignore                # Git exclusions
├── Dockerfile                # Containerización
├── README.md                 # Este archivo
└── docs/                     # Archivos de documentación
    ├── Documentación 1.pdf
    ├── Documentación 2.txt
    ├── Documentación 3.md
    └── Documentación 4.json
```

---

## 📡 USO DE ENDPOINTS

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "rag_initialized": true
}
```

### 2. Búsqueda Semántica

#### POST /search (JSON)

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿No se guardan los cambios?",
    "top_k": 3,
    "threshold": 0.5
  }'
```

#### GET /search (Query Parameters)

```bash
curl "http://localhost:8000/search?query=error+credenciales&top_k=3&threshold=0.5"
```

**Respuesta:**
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "content": "Las credenciales deben cumplir...",
      "similarity_score": 0.87
    }
  ],
  "total_results": 1,
  "query": "error credenciales"
}
```

### 3. Contexto para LLM

```bash
curl -X POST http://localhost:8000/context \
  -H "Content-Type: application/json" \
  -d '{"query":"autenticación","top_k":3,"threshold":0.5}'
```

**Respuesta:**
```json
{
  "success": true,
  "context": "- Punto 1\n- Punto 2\n- Punto 3",
  "num_results": 3,
  "threshold_used": 0.5
}
```

### 4. Asistente (via n8n)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cómo resetear contraseña?"}'
```

---

## 🐛 TROUBLESHOOTING

### "ModuleNotFoundError: No module named 'fastapi'"

```bash
pip install -r requirements.txt --upgrade
```

### "OPENAI_API_KEY is invalid"

1. Obtener nueva key: https://platform.openai.com/api-keys
2. Verificar que comience con `sk-`
3. Verificar .env tiene la key correcta
4. Reiniciar servidor Python

### "Connection refused on port 8000"

```bash
# Verificar si puerto está en uso
netstat -ano | findstr :8000

# Si está ocupado, usar puerto diferente:
# Editar .env: API_PORT=8001
# Luego: python main.py
```

### "No document chunks loaded"

1. Verificar que carpeta `docs/` existe
2. Verificar archivos: `Documentación 1.pdf`, etc.
3. Verificar permisos en la carpeta
4. Revisar errores en Python console

### "shapes (...) not aligned"

```bash
# Reiniciar backend después de cambios
python main.py
```

### "Webhook not registered" (n8n)

1. Asegurarse que n8n está corriendo en puerto 5678
2. En workflow, hacer click en **Execute Workflow** button
3. Luego probar `/webhook-test/...`
4. Cuando workflow esté activo, cambiar a `/webhook/...`

### "RAG pipeline not initialized"

```bash
# Verificar startup logs
# En Python console, buscar: "RAG pipeline initialized successfully"

# Si no aparece, verificar:
1. Carpeta docs/ existe
2. Tiene archivos válidos
3. No hay errores de parsing
```

### Respuestas sin contexto

```bash
# Bajar temporalmente el threshold
"threshold": 0.3  # en lugar de 0.5

# O revisar calidad de documentos en docs/
```

---

## 📚 STACK TECNOLÓGICO

| Componente | Tecnología | Rol |
|---|---|---|
| **Frontend** | HTML + Fetch API | UI web estática |
| **Backend** | FastAPI (Python 3.9+) | API REST |
| **Orquestación** | n8n | Automatización |
| **LLM** | OpenAI (GPT-4) | Generación de respuestas |
| **Embeddings** | OpenAI (text-embedding-3-small) | Búsqueda semántica |
| **Vectores** | NumPy | Almacenamiento local |
| **Contenedor** | Docker | Despliegue |
| **Formato Docs** | PDF, TXT, MD, JSON | Ingesta multiformato |

---

## ✅ CHECKLIST DE VERIFICACIÓN

### Instalación
- [ ] Python 3.9+ instalado
- [ ] pip instalado
- [ ] requirements.txt instalados
- [ ] .env creado con OPENAI_API_KEY válida

### Funcionalidad
- [ ] `python main.py` inicia sin errores
- [ ] `/health` responde correctamente
- [ ] `/search` retorna resultados
- [ ] `/context` retorna contexto formateado

### n8n (Opcional)
- [ ] n8n instalado y corriendo en puerto 5678
- [ ] n8n_workflow.json importado
- [ ] Credencial OpenAI configurada y testeada
- [ ] 4 nodos conectados correctamente
- [ ] Webhook URL accesible

### Producción
- [ ] Dockerfile testado
- [ ] Variables de entorno en producción
- [ ] Logs habilitados
- [ ] CORS configurado correctamente
- [ ] Timeouts establecidos

---

## 📝 EJEMPLOS PRÁCTICOS

### Query Documentada

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"credenciales incorrectas"}'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "content": "Las causas posibles de credenciales incorrectas...",
      "similarity_score": 0.89
    }
  ]
}
```

### Query No Documentada

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"cual es la mejor estrategia de inversion"}'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "results": [],
  "total_results": 0
}
```

### Desde n8n

```bash
curl -X POST http://localhost:5678/webhook/minecatalog-support \
  -H "Content-Type: application/json" \
  -d '{"question":"¿No se guardan los cambios?"}'
```

---

## 🚀 PRÓXIMOS PASOS

### Mejoras Inmediatas
- [ ] Agregar caché Redis para embeddings
- [ ] Implementar logging a base de datos
- [ ] Agregar notificaciones por email
- [ ] Analytics de queries

### Escalabilidad
- [ ] Desplegar en AWS/GCP/Azure
- [ ] Load balancing con múltiples instancias
- [ ] Vector store distribuido (Pinecone, Weaviate)
- [ ] Replication de n8n

### Funcionalidades
- [ ] Soporte para múltiples idiomas
- [ ] Fine-tuning de embeddings
- [ ] Feedback loop para mejorar resultados
- [ ] Dashboard de monitoreo

---

## 📞 REFERENCIA RÁPIDA

### Comandos Útiles

```bash
# Ver si servicios están corriendo
curl http://localhost:8000/health
curl http://localhost:5678/

# Reiniciar servicios
python main.py
docker restart n8n

# Ver logs
# En terminal donde corre Python: output directo
docker logs -f n8n

# Instalar/actualizar dependencias
pip install -r requirements.txt --upgrade

# Ejecutar tests
python tests.py
```

### Variables Clave en n8n

```
$json.body.question      → Pregunta del usuario
$items[1].$json.results  → Resultados búsqueda
$items[2].$json.response → Respuesta del LLM
new Date().toISOString() → Timestamp actual
```

---

## 📄 ARCHIVOS IMPORTANTES

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `main.py` | ~250 | FastAPI server con endpoints |
| `rag_pipeline.py` | ~450 | DocumentProcessor, EmbeddingManager, RAGPipeline |
| `prompt_engineering.py` | ~200 | System prompts y validación |
| `n8n_workflow.json` | ~150 | Definición del workflow |
| `requirements.txt` | ~20 | Dependencias Python |
| `.env.example` | ~15 | Template de variables |

