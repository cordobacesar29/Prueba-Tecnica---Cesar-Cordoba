# MineCatalog RAG - Sistema Automatizado de Soporte Técnico

## 📋 Descripción General

Sistema de **Retrieval-Augmented Generation (RAG)** automatizado que actúa como asistente de soporte técnico para **MineCatalog**. Integra procesamiento de documentos con Python, búsqueda semántica y generación de respuestas mediante OpenAI, orquestado a través de n8n.

**Características principales:**
- ✅ Ingesta automática de múltiples formatos (PDF, TXT, MD, JSON)
- ✅ Búsqueda semántica con embeddings (OpenAI o fallback local)
- ✅ Restricción absoluta de alucinación en respuestas
- ✅ API REST para integración con n8n
- ✅ Workflow n8n exportable y reutilizable
- ✅ Manejo robusto de errores y timeouts
- ✅ Respuestas contextualizadas basadas en documentación oficial

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      n8n Workflow                           │
│  [Webhook] → [Search API] → [OpenAI] → [Response]         │
└──────────────────┬──────────────────────────────────────────┘
                   │
         HTTP POST /search
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              FastAPI Python Server (main.py)               │
│  ├─ /health         → Estado del sistema                   │
│  ├─ /search         → Búsqueda semántica                   │
│  └─ /context        → Obtener contexto para LLM           │
└──────────────────┬──────────────────────────────────────────┘
                   │
         RAG Pipeline (rag_pipeline.py)
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼─────────┐  ┌────────▼────────┐
│ Document        │  │ Embedding       │
│ Processor       │  │ Manager         │
│ ├─ PDF loader   │  │ ├─ OpenAI API   │
│ ├─ TXT loader   │  │ ├─ Fallback TF   │
│ ├─ MD loader    │  │ └─ Search       │
│ ├─ JSON loader  │  │    (Cosine Sim) │
│ ├─ Cleaning     │  └─────────────────┘
│ └─ Chunking     │
└─────────────────┘

         ▲
         │
    /docs folder
    (4 documentation files)
```

---

## 🚀 Instalación y Configuración

### Requisitos Previos

- **Python 3.9+**
- **pip** (gestor de paquetes de Python)
- **n8n** (v1.0+) - [Descargar](https://n8n.io/)
- **OpenAI API Key** - [Obtener en OpenAI](https://platform.openai.com/api-keys)
- **Git** (opcional, para clonar el repositorio)

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/minecatalog-rag.git
cd minecatalog-rag
```

### Paso 2: Crear Archivo `.env`

Copia el archivo `.env.example` y configura tus variables:

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Docs Configuration
DOCS_DIR_PATH=./docs
VECTOR_DB_PATH=./vector_store/embeddings.json

# n8n Configuration
N8N_WEBHOOK_URL=http://localhost:5678/webhook-test/minecatalog-rag
N8N_API_URL=http://localhost:5678

# RAG Parameters
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=3
SIMILARITY_THRESHOLD=0.5

# Support Contact
SUPPORT_EMAIL=soporte.minecatalog@empresa.com
```

### Paso 3: Instalar Dependencias Python

```bash
pip install -r requirements.txt
```

### Paso 4: Preparar Documentación

Coloca los 4 archivos de documentación en la carpeta `docs/`:

```
docs/
├── Documentación 1.pdf
├── Documentación 2.txt
├── Documentación 3.md
└── Documentación 4.json
```

---

## 🎯 Ejecución Local

### Opción A: Ejecución Manual (Desarrollo)

#### Terminal 1: Iniciar API Python

```bash
python main.py
```

Salida esperada:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Starting MineCatalog RAG API...
INFO:     Initializing RAG pipeline...
INFO:     Loaded 156 document chunks
INFO:     RAG pipeline initialized successfully
```

**Endpoints disponibles:**
- `GET http://localhost:8000/health` - Verificar estado
- `POST http://localhost:8000/search` - Búsqueda semántica
- `POST http://localhost:8000/context` - Obtener contexto

#### Verificar que funciona:

```bash
curl -X GET http://localhost:8000/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "rag_initialized": true
}
```

---

## 📚 Uso de la API

### 1. Búsqueda Semántica

**Request:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿No se guardan los cambios de un material?",
    "top_k": 3,
    "threshold": 0.5
  }'
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "content": "Causa posible: Errores de validación de datos...",
      "similarity_score": 0.87
    },
    {
      "rank": 2,
      "content": "Solución: Revisar los campos obligatorios...",
      "similarity_score": 0.82
    }
  ],
  "total_results": 2,
  "query": "¿No se guardan los cambios de un material?"
}
```

### 2. Obtener Contexto para LLM

**Request:**
```bash
curl -X POST http://localhost:8000/context \
  -H "Content-Type: application/json" \
  -d '{"query": "Error de conexión a base de datos"}'
```

**Response:**
```json
{
  "success": true,
  "query": "Error de conexión a base de datos",
  "context": "- Servidor de base de datos apagado\n- Validar host, puerto, nombre de base de datos...",
  "num_results": 3,
  "threshold_used": 0.5
}
```

---

## 🔄 Integración con n8n

### Paso 1: Importar Workflow

1. Abre n8n en `http://localhost:5678`
2. Ve a **Workflows** → **Import from JSON**
3. Copia el contenido de `n8n_workflow.json`
4. Pega en el dialog de importación
5. Haz clic en **Import**

### Paso 2: Configurar Credenciales OpenAI

1. En el workflow importado, busca el nodo **"Generate Answer"**
2. Configura la credencial de OpenAI con tu API Key
3. Asegúrate que el modelo sea `gpt-4-turbo-preview`

### Paso 3: Probar el Workflow

**Enviar request a n8n:**
```bash
curl -X POST http://localhost:5678/webhook-test/minecatalog-support \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuáles son las causas posibles de un error de autenticación?"
  }'
```

**Response esperada:**
```json
{
  "success": true,
  "question": "¿Cuáles son las causas posibles de un error de autenticación?",
  "answer": "Según la documentación de MineCatalog, las causas posibles de error de autenticación ERR-AUTH-001 son...",
  "context_used": 3,
  "timestamp": "2024-05-29T20:34:27Z"
}
```

---

## 🛡️ Reglas de Alucinación y Restricciones

El sistema está configurado con las siguientes reglas estrictas:

### ✅ Respuesta Correcta (Documentada)

**Pregunta:** "¿No se guardan los cambios de un material?"

**Respuesta:** 
> "Basándome en la sección 4.3 de la documentación, si los cambios de un material no se guardan, verifique: 
> 1. Que todos los campos obligatorios estén completados
> 2. Permisos del usuario
> 3. Espacio en base de datos"

### ❌ Respuesta Bloqueada (No Documentada)

**Pregunta:** "¿Qué significa error 502?"

**Respuesta (Forzada):**
> "Lo siento, la información solicitada no se encuentra en la documentación interna de MineCatalog. Por favor, contacte a soporte técnico en soporte.minecatalog@empresa.com"

---

## 📊 Ejemplos de Validación

### Test Case 1: Consulta Documentada

```python
# Query: "Credenciales incorrectas"
# Esperado: Respuesta con detalles del error ERR-AUTH-001
# Resultado: ✅ PASS
```

### Test Case 2: Consulta No Documentada

```python
# Query: "Error 502 Bad Gateway"
# Esperado: Derivación a soporte
# Resultado: ✅ PASS
```

### Test Case 3: Input Vacío

```python
# Query: ""
# Esperado: HTTP 400 Bad Request
# Resultado: ✅ PASS
```

### Test Case 4: Timeout de OpenAI

```python
# Escenario: API de OpenAI cae
# Esperado: Error controlado, retry automático
# Resultado: ✅ PASS
```

---

## 🔧 Solución de Problemas

### Problema: "RAG pipeline not initialized"

**Solución:**
1. Verifica que la carpeta `docs/` contiene los archivos de documentación
2. Revisa los logs de Python en busca de errores de parseo
3. Reinicia el servidor API

### Problema: "OpenAI API Error: Invalid API Key"

**Solución:**
1. Verifica que `OPENAI_API_KEY` en `.env` es correcto
2. Asegúrate que la API Key tiene permisos suficientes
3. Confirma que no está en lista negra

### Problema: "Connection refused to localhost:8000"

**Solución:**
1. Verifica que el servidor Python está corriendo: `lsof -i :8000`
2. Comprueba que el puerto 8000 no está en uso por otro proceso
3. Reinicia la API

### Problema: "n8n Webhook not found"

**Solución:**
1. Asegúrate que n8n está corriendo en `http://localhost:5678`
2. Verifica que el workflow está activo (toggle encendido)
3. Comprueba la URL del webhook en la configuración

---

## 📈 Métricas y Monitoring

### Monitoreo de Búsquedas

Verifica el archivo de logs para analizar:
- Tiempo de latencia en búsquedas
- Score de similitud promedio
- Queries que derivaron a soporte

```bash
tail -f minecatalog_rag.log
```

### Health Check

```bash
watch -n 5 'curl -s http://localhost:8000/health | jq .'
```

---

## 🚀 Deployment en Producción

### Docker (Recomendado)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

**Build:**
```bash
docker build -t minecatalog-rag:latest .
```

**Run:**
```bash
docker run -d \
  -e OPENAI_API_KEY=sk-xxx \
  -e DOCS_DIR_PATH=/app/docs \
  -p 8000:8000 \
  minecatalog-rag:latest
```

---

## 📝 Estructura de Archivos

```
minecatalog-rag/
├── main.py                    # FastAPI application
├── rag_pipeline.py           # RAG processing logic
├── prompt_engineering.py     # System prompts & LLM config
├── n8n_workflow.json        # n8n workflow definition
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── README.md                # This file
└── docs/                    # Documentation files
    ├── Documentación 1.pdf
    ├── Documentación 2.txt
    ├── Documentación 3.md
    └── Documentación 4.json
```

---

## 🎓 Conceptos Clave

### RAG (Retrieval-Augmented Generation)

Combina recuperación de documentos relevantes con generación de texto:
1. **Retrieval:** Busca contexto relevante de la base de conocimiento
2. **Augmented:** Inyecta contexto en el prompt del LLM
3. **Generation:** LLM genera respuesta basada en contexto

### Chunking Inteligente

Divide documentos en fragmentos manejables mientras preserva contexto:
- `CHUNK_SIZE=500` palabras por fragmento
- `CHUNK_OVERLAP=50` palabras de solapamiento
- Preserva coherencia semántica

### Embeddings y Búsqueda Semántica

- **Embeddings:** Representación vectorial de texto
- **Cosine Similarity:** Mide proximidad entre vectores
- **Top-K Retrieval:** Retorna los K fragmentos más similares

---

## 📞 Soporte y Contacto

Para problemas con la implementación:
- Abre un issue en GitHub
- Contacta al equipo de soporte técnico
- Revisa la documentación de MineCatalog

**Email de Soporte:** soporte.minecatalog@empresa.com

---

## 📄 Licencia

Este proyecto es parte de la prueba técnica de Unilink. Todos los derechos reservados.

---

**Última actualización:** Mayo 2026
**Versión:** 1.0.0
**Desarrollador:** Ingeniero de ML Senior
