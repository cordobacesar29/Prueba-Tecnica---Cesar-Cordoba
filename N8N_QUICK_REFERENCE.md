# TARJETA DE REFERENCIA RÁPIDA: n8n Integration

**Imprime esta página para tenerla a mano mientras integras**

---

## ✅ CHECKLIST: 10 PASOS EN 30 MINUTOS

```
□ PASO 1 (2 min): n8n instalado
   docker run -d -p 5678:5678 n8nio/n8n:latest
   
□ PASO 2 (3 min): Python API corriendo  
   cd "...Prueba Técnica..."
   python main.py
   
□ PASO 3 (2 min): Verificar API
   curl http://localhost:8000/health
   
□ PASO 4 (3 min): Crear .env
   cp .env.example .env
   [Editar con OPENAI_API_KEY]
   
□ PASO 5 (5 min): Abrir n8n
   http://localhost:5678
   Crear nueva workflow
   
□ PASO 6 (2 min): Agregar 4 nodos
   1. Webhook (POST)
   2. HTTP Request (Search)
   3. OpenAI Chat
   4. Response
   
□ PASO 7 (5 min): Configurar credenciales
   Credentials → OpenAI
   Test → ✓
   
□ PASO 8 (3 min): Conectar nodos
   Webhook → HTTP → OpenAI → Response
   
□ PASO 9 (2 min): Guardar y activar
   Save → Toggle Active → ✓
   
□ PASO 10 (2 min): Probar con cURL
   curl -X POST http://localhost:5678/webhook/...
```

---

## 🔌 URLS CRÍTICAS

| Servicio | URL | Status |
|----------|-----|--------|
| n8n | http://localhost:5678 | 🟢 |
| Python API | http://localhost:8000 | 🟢 |
| Health Check | http://localhost:8000/health | 🟢 |

---

## 📝 CONFIGURACIÓN NODAL (Copy-Paste Ready)

### NODO 2: HTTP Request Body
```json
{
  "query": "{{ $json.body.question }}",
  "top_k": 3,
  "threshold": 0.5
}
```

### NODO 3: System Prompt
```
Eres un asistente técnico especializado en MineCatalog.

Si la información NO está en el contexto, responde EXACTAMENTE:
"Lo siento, la información solicitada no se encuentra en la documentación 
interna de MineCatalog. Por favor, contacte a soporte técnico en 
soporte.minecatalog@empresa.com"

Contexto:
{{ $items[1].$json.body.results.map(r => r.content).join("\n\n") }}

Responde en español.
```

### NODO 3: User Message
```
{{ $json.body.question }}
```

### NODO 4: Response Body
```json
{
  "success": true,
  "question": "{{ $json.body.question }}",
  "answer": "{{ $items[2].$json.response }}",
  "context_used": {{ $items[1].$json.body.results.length }},
  "timestamp": "{{ new Date().toISOString() }}"
}
```

---

## 🧪 TEST QUERIES

**Copiar y pegar en cURL o Postman:**

```bash
# Query Documentada (debe dar respuesta)
curl -X POST http://localhost:5678/webhook/minecatalog-support \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cuáles son las causas de un error de credenciales?"}'

# Query No Documentada (debe dar fallback)
curl -X POST http://localhost:5678/webhook/minecatalog-support \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Qué significa error 502?"}'

# Query Corta (prueba simple)
curl -X POST http://localhost:5678/webhook/minecatalog-support \
  -H "Content-Type: application/json" \
  -d '{"question":"autenticación"}'
```

---

## 🐛 TROUBLESHOOTING RÁPIDO

| Problema | Solución |
|----------|----------|
| n8n no abre | `docker restart n8n` |
| API no responde | `python main.py` en terminal nueva |
| Webhook not found | Workflow debe estar **Active** (toggle verde) |
| OpenAI error | Verificar API key en Credentials → Test |
| Timeout | Aumentar timeout en HTTP node a 30s |
| Variables undefined | Usar btn "fx" en campo para insertar referencia |

---

## 📊 MAPEO DE DATOS

```
Cliente
  ↓ {"question": "..."}
Webhook ($json.body.question)
  ↓
HTTP Search ($items[1].$json.body.results)
  ↓
OpenAI (usa results como contexto)
  ↓
Response ($items[2].$json.response)
  ↓
Cliente recibe respuesta
```

---

## 🔐 CREDENCIALES OPENAI

```
1. Obtener: https://platform.openai.com/api-keys
2. Copiar: sk-xxxxxxxxxxxxx (comenzar con "sk-")
3. En n8n:
   Credentials → Create New → OpenAI
   Pegar API Key
   Click "Test"
   Debe mostrar ✓
```

---

## 📞 COMANDOS ÚTILES

```bash
# Ver servicios corriendo
docker ps | grep n8n
lsof -i :8000  # Python

# Logs
docker logs -f n8n
# En Python: ver output directo en terminal

# Reiniciar
docker restart n8n
pkill -f "python main.py"

# Test rápido
curl http://localhost:8000/health
curl http://localhost:5678/
```

---

## ⚡ WORKFLOW JSON

Para importar directamente:
1. n8n UI → Menu ☰ → Import from JSON
2. Pegar contenido de `n8n_workflow.json`
3. Click "Import"
4. Configurar credenciales

---

## 📈 FLUJO RESUMIDO

```
Usuario envía pregunta
          ↓
n8n Webhook recibe
          ↓
Llama Python /search
          ↓
Obtiene documentos relevantes
          ↓
Inyecta en System Prompt
          ↓
Llama OpenAI
          ↓
OpenAI genera respuesta
          ↓
n8n devuelve JSON
          ↓
Usuario recibe respuesta
```

---

## 💾 GUARDAR Y RECUPERAR

```
n8n guarda automáticamente en:
~/n8n_data/  (si usas Docker con volumen)

Para exportar workflow:
Menu → Export as JSON
Guardar en safe place

Para importar:
Menu → Import from JSON
Seleccionar archivo o pegar JSON
```

---

## 🎯 VALIDACIÓN FINAL

Antes de decir "listo":

- [ ] Health endpoint responde: `curl http://localhost:8000/health`
- [ ] n8n está activo: `http://localhost:5678`
- [ ] Workflow está **ACTIVE** (toggle verde)
- [ ] Webhook URL funciona: `curl http://localhost:5678/webhook/minecatalog-support`
- [ ] Query documentada devuelve respuesta
- [ ] Query no documentada devuelve fallback
- [ ] Logs no muestran errores
- [ ] Timestamps correctos en respuestas

---

## 📞 REFERENCIA DE VARIABLES n8n

```
$json              → Output del nodo actual
$items[0]          → Primer nodo (Webhook)
$items[1]          → Segundo nodo (HTTP Search)
$items[2]          → Tercer nodo (OpenAI)

$json.body         → Body de webhook
$json.body.question    → Campo "question"
$items[1].$json.body   → Body del segundo nodo
$items[1].$json.body.results  → Resultados búsqueda
```

---

## 🚀 PRÓXIMO: PRODUCTION

Una vez verificado, para producción:

```bash
# 1. Docker compose para ambos servicios
docker-compose up -d

# 2. SSL/HTTPS
nginx reverse proxy

# 3. Monitoreo
Prometheus + Grafana

# 4. Logs
ELK Stack o similar

# 5. Backups
Copias de n8n_data/ regularmente
```

---

## 📄 ARCHIVOS IMPORTANTES

```
En tu carpeta del proyecto:
├── n8n_workflow.json         ← Importar en n8n
├── N8N_INTEGRATION_GUIDE.md  ← Guía detallada
├── N8N_VISUAL_GUIDE.md       ← Diagramas
├── main.py                   ← API Server
├── .env.example              ← Copiar a .env
└── README.md                 ← Documentación general
```

---

## ✨ ¡LISTO!

Con estos pasos tienes integración completa:

```
Cliente → n8n → Python API → OpenAI → Respuesta
```

**¿Dudas?** Ver archivos de guía detallada.

---

**Impreso en:** Mayo 2024  
**Versión:** Quick Reference 1.0  
**Tiempo estimado:** 30 minutos
