# GUÍA COMPLETA: INTEGRACIÓN CON n8n - MineCatalog RAG

**Versión:** 1.0  
**Fecha:** Mayo 2024  
**Nivel:** Principiante a Intermedio  

---

## 📋 ÍNDICE

1. [Instalación de n8n](#instalación-de-n8n)
2. [Preparación del Sistema Python](#preparación-del-sistema-python)
3. [Importar el Workflow](#importar-el-workflow)
4. [Configurar Credenciales](#configurar-credenciales)
5. [Configurar Nodos](#configurar-nodos)
6. [Pruebas y Validación](#pruebas-y-validación)
7. [Troubleshooting](#troubleshooting)
8. [Ejemplos Prácticos](#ejemplos-prácticos)

---

## 🚀 INSTALACIÓN DE N8N

### Opción 1: Docker (Recomendado)

**Ventajas:** Fácil, aislado, sin dependencias

```bash
# Crear carpeta para n8n
mkdir -p ~/n8n_data

# Ejecutar con Docker
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=password123 \
  -v ~/n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

**Verificar que está corriendo:**
```bash
docker ps | grep n8n
```

**Acceder:** http://localhost:5678

---

### Opción 2: Node.js Local

**Requisitos:**
- Node.js 16+
- npm o yarn

```bash
# Instalar n8n globalmente
npm install -g n8n

# Iniciar n8n
n8n

# Salida esperada:
# ┌─────────────────────────────────────┐
# │ n8n ready on http://localhost:5678  │
# └─────────────────────────────────────┘
```

---

### Opción 3: Aplicación Web (Cloud)

**Usando n8n Cloud:**
1. Ir a https://n8n.cloud
2. Registrarse
3. Crear nuevo workspace
4. No requiere instalación local

---

## 🔧 PREPARACIÓN DEL SISTEMA PYTHON

### PASO 1: Verificar que API Python está corriendo

**En Terminal 1:**
```bash
cd "c:\Users\César\César\Prueba Técnica - César Córdoba"

# Verificar ambiente
python --version  # Debe ser 3.9+
pip list | grep fastapi

# Instalar si no está
pip install -r requirements.txt
```

### PASO 2: Crear archivo .env

```bash
# Copiar template
cp .env.example .env

# Editar con tu editor favorito
notepad .env  # Windows
# o
nano .env     # Linux/Mac
```

**Contenido mínimo requerido:**
```env
OPENAI_API_KEY=sk-tu-clave-real-aqui
API_HOST=0.0.0.0
API_PORT=8000
DOCS_DIR_PATH=./docs
```

### PASO 3: Iniciar API Python

**En Terminal 1:**
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

### PASO 4: Verificar API está accesible

**En Terminal 2:**
```bash
# Health check
curl http://localhost:8000/health

# Respuesta esperada:
# {"status":"healthy","rag_initialized":true}
```

✅ **Si ves esto, la API está lista para n8n**

---

## 📥 IMPORTAR EL WORKFLOW

### PASO 5: Acceder a n8n

1. Abrir navegador
2. Ir a **http://localhost:5678**
3. Si pide login, usar credenciales configuradas
4. Verás la pantalla principal de n8n

### PASO 6: Crear Nuevo Workflow

```
Opción 1: Click en "+ Add Workflow"
Opción 2: Menu → Workflows → New Workflow
```

### PASO 7: Importar JSON

**Método A: Desde UI**
```
1. Click en menu (☰) arriba a la derecha
2. Seleccionar "Import from JSON"
3. Pegar contenido de n8n_workflow.json
4. Click en "Import"
```

**Método B: Desde línea de comandos**
```bash
# Copiar el contenido del workflow
cat n8n_workflow.json

# Luego en n8n UI:
# Menu → Import from JSON
# Pegar contenido
```

**Método C: Crear Manualmente**

Si prefieres, crearemos los nodos uno a uno en los pasos siguientes.

---

## 🔐 CONFIGURAR CREDENCIALES

### PASO 8: Agregar Credencial OpenAI

**En n8n:**

```
1. Click en Credentials (llave 🔑 arriba a la derecha)
2. Click en "+ Create New"
3. Buscar "OpenAI" en la lista
4. Seleccionar "OpenAI API"
```

**Rellenar formulario:**
```
Name: OpenAI MineCatalog
API Key: sk-tu-clave-real
Organization ID: (opcional)
Base URL: (dejar en blanco - usa default)
```

**Guardar:** Click "Save"

### PASO 9: Verificar Conexión

```
Click en el botón "Test" al lado del credential
Debe mostrar: ✓ Authentication successful
```

---

## 🧩 CONFIGURAR NODOS

### Estructura del Workflow

```
┌──────────────┐
│   Webhook    │  Recibe pregunta
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Search Doc  │  Busca contexto
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Gen Answer  │  Llama OpenAI
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Response    │  Devuelve respuesta
└──────────────┘
```

---

### NODO 1: Webhook (HTTP In)

**Función:** Recibir preguntas del usuario

**Pasos:**

```
1. En n8n, Click en "Add node"
2. Buscar "Webhook"
3. Seleccionar "Webhook"
4. Click en el nodo
```

**Configuración:**

```
HTTP Method: POST
Path: minecatalog-support    (o el que prefieras)
Response Mode: Response Node
Authentication: None
```

**Salida del nodo:**
```json
{
  "body": {
    "question": "¿Cuáles son las causas del error 502?"
  }
}
```

---

### NODO 2: HTTP Request (Buscar Documentos)

**Función:** Llamar Python API para búsqueda semántica

**Pasos:**

```
1. Click en "Add node" (después del Webhook)
2. Buscar "HTTP Request"
3. Seleccionar "HTTP Request"
```

**Configuración:**

```
Method: POST
URL: http://localhost:8000/search

Headers:
  Content-Type: application/json

Body (JSON):
{
  "query": {{ $json.body.question }},
  "top_k": 3,
  "threshold": 0.5
}
```

**IMPORTANTE:** Reemplazar `{{ $json.body.question }}` con la variable de entrada

**En n8n, hacer así:**
1. Click en el campo "Body"
2. Cambiar a "JSON" mode
3. Pegar el JSON pero reemplazar el valor:
```json
{
  "query": "{{ $json.body.question }}",
  "top_k": 3,
  "threshold": 0.5
}
```

**Salida esperada:**
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "content": "...",
      "similarity_score": 0.87
    }
  ]
}
```

---

### NODO 3: OpenAI Chat Model

**Función:** Generar respuesta usando LLM

**Pasos:**

```
1. Click en "Add node" (después del HTTP)
2. Buscar "OpenAI"
3. Seleccionar "OpenAI Chat Model"
```

**Configuración:**

```
Authentication: (Seleccionar credencial creada en PASO 9)
Model: gpt-4-turbo-preview
Temperature: 0.7
Max Tokens: 1000

System Prompt:
```

**System Prompt (Copiar y Pegar):**
```
Eres un asistente técnico especializado en MineCatalog.

REGLA CRÍTICA: Si la información NO está en el contexto, responde EXACTAMENTE:
"Lo siento, la información solicitada no se encuentra en la documentación interna de MineCatalog. 
Por favor, contacte a soporte técnico en soporte.minecatalog@empresa.com"

Contexto de documentación:
{{ $items[1].$json.body.results.map(r => r.content).join("\n\n") }}

Responde siempre en español, de forma profesional y útil.
```

**User Message:**
```
{{ $json.body.question }}
```

**Chat Input:** (dejar en blanco si ya usas User Message)

---

### NODO 4: Response (HTTP Out)

**Función:** Devolver respuesta al cliente

**Pasos:**

```
1. Click en "Add node" (después del OpenAI)
2. Buscar "Respond to Webhook"
3. Seleccionar "Respond to Webhook"
```

**Configuración:**

```
Response Body:
{
  "success": true,
  "question": {{ $json.body.question }},
  "answer": {{ $items[2].$json.response }},
  "context_used": {{ $items[1].$json.body.total_results }},
  "timestamp": new Date().toISOString()
}

Status Code: 200
```

---

## 🧪 PRUEBAS Y VALIDACIÓN

### PASO 10: Activar Workflow

```
1. En n8n, click en botón "Save" (arriba a la derecha)
2. Nombre: "MineCatalog RAG Support"
3. Click en toggle "Active" para activar
4. Debe mostrar: Workflow active
```

### PASO 11: Obtener URL del Webhook

```
En el nodo Webhook, verás:
"Webhook URL: http://localhost:5678/webhook/minecatalog-support"

Copiar esta URL - la usaremos para probar
```

### PASO 12: Probar con cURL

**En Terminal 3 (nueva):**

```bash
# Prueba 1: Query Documentada (debe funcionar)
curl -X POST http://localhost:5678/webhook/minecatalog-support \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuáles son las causas posibles de un error de credenciales?"
  }'

# Respuesta esperada:
# {
#   "success": true,
#   "question": "¿Cuáles son las causas...",
#   "answer": "Según la documentación...",
#   "context_used": 3,
#   "timestamp": "2024-05-29T..."
# }
```

```bash
# Prueba 2: Query No Documentada (debe dar fallback)
curl -X POST http://localhost:5678/webhook/minecatalog-support \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué significa error 502?"
  }'

# Respuesta esperada:
# {
#   "success": true,
#   "question": "¿Qué significa error 502?",
#   "answer": "Lo siento, la información solicitada no se encuentra...",
#   "context_used": 0,
#   "timestamp": "2024-05-29T..."
# }
```

### PASO 13: Visualizar en n8n

```
1. En el workflow de n8n
2. Click en botón "Execute" (▶)
3. Verás el flujo completo ejecutándose
4. Cada nodo mostrará sus outputs
5. Al final, verás la respuesta en el Response node
```

---

## 📊 MONITOREO EN TIEMPO REAL

### Ver Logs de Ejecución

```
En n8n:
1. Click en "Executions" (historial 📋)
2. Verás todas las ejecuciones del workflow
3. Click en una ejecución para ver detalles
4. Ver datos que pasaron por cada nodo
```

### Ver Logs de Python API

**En Terminal 1 (donde corre python main.py):**
```
Verás líneas como:
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     127.0.0.1:54321 - "POST /search HTTP/1.1" 200 OK
```

---

## 🔧 TROUBLESHOOTING

### Problema 1: "Connection refused on port 5678"

**Solución:**
```bash
# Verificar si n8n está corriendo
docker ps | grep n8n

# Si no aparece, iniciar:
docker run -d -p 5678:5678 n8nio/n8n:latest
```

### Problema 2: "Error connecting to localhost:8000"

**Solución:**
```bash
# Verificar que API Python está corriendo
curl http://localhost:8000/health

# Si no responde:
cd "c:\Users\César\César\Prueba Técnica - César Córdoba"
python main.py
```

### Problema 3: "OpenAI API key invalid"

**Solución:**
```
1. En n8n, ir a Credentials
2. Editar credencial OpenAI
3. Verificar que API key comienza con "sk-"
4. Verificar en https://platform.openai.com/api-keys que la key es válida
5. Hacer Test nuevamente
```

### Problema 4: "Undefined reference $json.body.question"

**Solución:**
```
1. Hacer click en el nodo
2. En el campo, click en botón "fx" (functions)
3. Seleccionar $json → body → question
4. Esto autogenerará la referencia correcta
```

### Problema 5: Timeout (respuesta muy lenta)

**Solución:**
```
1. Aumentar timeout en HTTP Request node
   Timeout: 30 segundos

2. Verificar que OpenAI API está respondiendo
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer sk-tu-key"

3. Reducir TOP_K en búsqueda
   "top_k": 2 en lugar de 3
```

---

## 📝 EJEMPLOS PRÁCTICOS

### Ejemplo 1: Query Documentada

**Entrada:**
```json
{
  "question": "¿No se guardan los cambios de un material?"
}
```

**Flujo:**
```
1. Webhook recibe la pregunta
2. HTTP Request busca documentos similares
3. Encuentra: "Causas posibles", "Solución", "Validación"
4. OpenAI genera respuesta basada en contexto
5. Response devuelve respuesta completa
```

**Salida esperada:**
```json
{
  "success": true,
  "question": "¿No se guardan los cambios de un material?",
  "answer": "Basándome en la documentación, si los cambios de un material no se guardan, verifique: 1. Que todos los campos obligatorios estén completados...",
  "context_used": 3
}
```

---

### Ejemplo 2: Query No Documentada

**Entrada:**
```json
{
  "question": "¿Cuál es la mejor estrategia de inversión?"
}
```

**Flujo:**
```
1. Webhook recibe la pregunta
2. HTTP Request busca documentos similares
3. No encuentra resultados relevantes (score < 0.5)
4. OpenAI detecta falta de contexto
5. Response devuelve fallback message
```

**Salida esperada:**
```json
{
  "success": true,
  "question": "¿Cuál es la mejor estrategia de inversión?",
  "answer": "Lo siento, la información solicitada no se encuentra en la documentación interna de MineCatalog. Por favor, contacte a soporte técnico en soporte.minecatalog@empresa.com",
  "context_used": 0
}
```

---

### Ejemplo 3: Integración desde Aplicación Externa

**Desde tu aplicación (Node.js, Python, Java, etc.):**

```javascript
// JavaScript/Node.js
const question = "¿Qué significa error de conexión a base de datos?";

const response = await fetch('http://localhost:5678/webhook/minecatalog-support', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ question })
});

const data = await response.json();
console.log(data.answer);
```

```python
# Python
import requests

question = "¿Cuáles son los pasos para resolver error de código duplicado?"
webhook_url = "http://localhost:5678/webhook/minecatalog-support"

response = requests.post(webhook_url, json={"question": question})
data = response.json()
print(f"Respuesta: {data['answer']}")
```

```bash
# cURL
curl -X POST http://localhost:5678/webhook/minecatalog-support \
  -H "Content-Type: application/json" \
  -d '{"question":"Cuéntame sobre autenticación"}'
```

---

## 📈 PRÓXIMOS PASOS

### 1. Personalizar el Workflow

**Agregar notificaciones por email:**
```
1. Después del nodo Response
2. Agregar nodo "Send Email"
3. Configurar para enviar respuesta por email
4. Activar trigger en ciertos casos
```

**Agregar logging a base de datos:**
```
1. Agregar nodo "PostgreSQL" o "MongoDB"
2. Guardar pregunta, respuesta y score
3. Análisis posterior de queries
```

---

### 2. Escalar para Producción

**Usar n8n en la nube:**
```
1. Desplegar en AWS, GCP, Azure
2. n8n Cloud oficial
3. Self-hosted en VPS
```

**Load balancing:**
```
1. Múltiples instancias de Python API
2. Balanceador de carga (nginx)
3. Caché distribuido (Redis)
```

---

### 3. Monitoreo Avanzado

**Configurar alertas:**
```
- Error rate > 5%
- Latencia > 2 segundos
- 0 resultados encontrados
- API key expirada
```

**Dashboard:**
```
- Preguntas más frecuentes
- Tasa de alucinación
- Tiempo de respuesta promedio
- Errores diarios
```

---

## 📞 REFERENCIA RÁPIDA

### URLs Importantes

| Servicio | URL | Puerto |
|----------|-----|--------|
| n8n | http://localhost:5678 | 5678 |
| API Python | http://localhost:8000 | 8000 |
| Webhook | http://localhost:5678/webhook/minecatalog-support | - |
| Health Check | http://localhost:8000/health | - |

### Variables Clave en n8n

```
$json.body.question          → Pregunta del usuario
$items[1].$json.body.results → Resultados búsqueda
$items[2].$json.response     → Respuesta del LLM
new Date().toISOString()     → Timestamp actual
```

### Comandos Útiles

```bash
# Ver si servicios están corriendo
curl http://localhost:5678/
curl http://localhost:8000/health

# Reiniciar servicios
docker restart n8n
# Matar proceso Python y reiniciar
pkill -f "python main.py"
python main.py

# Ver logs
docker logs -f n8n
# En terminal Python, ver output directo
```

---

## ✅ CHECKLIST FINAL

- [ ] n8n instalado y corriendo en puerto 5678
- [ ] API Python corriendo en puerto 8000
- [ ] .env.example copiado a .env con OPENAI_API_KEY válida
- [ ] Workflow n8n_workflow.json importado o nodos creados
- [ ] Credencial OpenAI configurada en n8n y testeada
- [ ] 4 nodos creados: Webhook → Search → LLM → Response
- [ ] Webhook URL anotada y accesible
- [ ] Pruebas con cURL exitosas
- [ ] Query documentada retorna respuesta con contexto
- [ ] Query no documentada retorna fallback message
- [ ] Workflow está activo (toggle verde)
- [ ] Logs muestran datos correctamente en cada nodo

---

## 🎓 CONCLUSIÓN

¡Ya tienes integración completa n8n + Python + OpenAI! 

**El flujo es:**
```
Usuario → n8n Webhook → Python Search API → OpenAI LLM → Respuesta
```

**Próximo paso:** Personaliza según tus necesidades específicas.

---

**Última actualización:** Mayo 2024  
**Versión:** 1.0  
**Estado:** ✅ Listo para usar
