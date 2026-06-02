# MineCatalog RAG Support Assistant

Sistema RAG para soporte técnico de MineCatalog. El usuario pregunta desde una UI web o desde un webhook n8n; n8n consulta el backend FastAPI, recupera contexto de `docs/` y usa OpenAI para generar una respuesta controlada por documentación.

## Arquitectura rápida

```text
Usuario/UI
  -> n8n Webhook GET /webhook-test/minecatalog-support?question=...
  -> Backend FastAPI GET /search?question=...
  -> RAG local sobre docs/
  -> OpenAI node en n8n
  -> Respuesta al usuario
```

## Requisitos

- Python 3.9+.
- n8n local o Docker.
- OpenAI API key configurada en n8n para el nodo `Generate Answer`.
- Archivos de documentación en `docs/`.

## 1. Levantar el backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python main.py
```

Verificación:

```powershell
curl http://localhost:8000/health
```

Swagger:

```text
http://localhost:8000/docs
```

UI local servida por FastAPI:

```text
http://localhost:8000/ui
```

Proxy backend hacia n8n, usado por la UI para evitar CORS:

```text
POST http://localhost:8000/ask
```

## 2. Probar el backend sin n8n

```powershell
curl -X POST http://localhost:8000/search `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"¿No se guardan los cambios de un material?\",\"top_k\":3,\"threshold\":0.5}"
```

Respuesta esperada: `success: true`, lista `results` y `similarity_score` por fragmento.

## 3. Levantar n8n

Opción rápida con `npx`:

```powershell
npx n8n
```

Opción Docker:

```powershell
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

Abrir:

```text
http://localhost:5678
```

## 4. Conectar la automatización

1. En n8n, importar `n8n_workflow.json`.
2. Configurar credenciales OpenAI en el nodo `Generate Answer`.
3. Revisar la URL del nodo `Search Documentation`:
  - n8n local: `http://127.0.0.1:8000/search?question=...`.
  - n8n en Docker: usar `http://host.docker.internal:8000/search?question=...`.
4. Ejecutar el workflow en modo test.
5. Probar el webhook:

```powershell
curl "http://localhost:5678/webhook-test/minecatalog-support?question=No%20se%20guardan%20los%20cambios%20de%20un%20material"
```

Cuando el workflow esté activo en producción, cambiar `webhook-test` por `webhook`:

```text
http://localhost:5678/webhook/minecatalog-support?question=...
```

## URLs importantes

| Componente | URL local | Uso |
|---|---|---|
| Backend health | `http://localhost:8000/health` | Estado del RAG |
| Backend Swagger | `http://localhost:8000/docs` | Probar endpoints |
| UI web | `http://localhost:8000/ui` | Demo amigable |
| Backend ask proxy | `http://localhost:8000/ask` | UI -> FastAPI -> n8n |
| Backend search | `http://127.0.0.1:8000/search?question=...` | Llamado desde n8n |
| n8n editor | `http://localhost:5678` | Editar workflow |
| n8n test webhook | `http://localhost:5678/webhook-test/minecatalog-support?question=...` | Pruebas |
| n8n prod webhook | `http://localhost:5678/webhook/minecatalog-support?question=...` | Workflow activo |

## Interfaz web

Se implementó una UI estática en `frontend/index.html`, servida desde `http://localhost:8000/ui`.

Tres opciones de evolución:

1. **Consola web liviana:** la versión actual; ideal para demo y prueba técnica porque no requiere Node ni build.
2. **Widget embebible:** botón flotante dentro de MineCatalog para soporte contextual.
3. **Panel QA interno:** historial de preguntas, contexto recuperado, scores, trazas n8n y errores OpenAI para soporte/operaciones.

## Guía del flujo completo

1. El usuario abre `http://localhost:8000/ui`.
2. La UI envía `POST /ask` al backend FastAPI.
3. FastAPI llama server-side al webhook n8n configurado en `N8N_WEBHOOK_URL`.
4. n8n recibe la pregunta en el nodo `Webhook`.
5. El nodo `Search Documentation` llama al backend: `GET /search?question=...`.
6. FastAPI valida la query con Pydantic y ejecuta el pipeline RAG sobre `docs/`.
7. El backend devuelve fragmentos relevantes con score de similitud.
8. n8n inyecta esos fragmentos como contexto en el nodo OpenAI.
9. OpenAI responde únicamente con información del contexto; si no hay evidencia suficiente, responde con el fallback de soporte.
10. n8n devuelve un JSON final a FastAPI y FastAPI lo devuelve a la UI.

La conexión clave es: n8n orquesta la conversación y el backend solo recupera evidencia documental. Esa separación evita acoplar el LLM al backend y permite ajustar prompts/modelos desde n8n sin tocar Python.

## Manejo de errores OpenAI en n8n

Basado en la guía oficial de errores de OpenAI: https://developers.openai.com/api/docs/guides/error-codes

Recomendación práctica para este workflow:

- `401/403`: validar credencial OpenAI en n8n y permisos del proyecto.
- `429`: agregar retry con backoff en n8n y mostrar mensaje de saturación temporal.
- `500/503`: reintentar una vez y devolver error controlado si persiste.
- `timeout`: configurar timeout explícito en OpenAI y devolver fallback operativo.
- Errores de WebSocket/realtime: no aplican a este flujo HTTP, pero conviene documentarlos si se migra a streaming.

Mensaje seguro para errores externos:

```text
No se pudo generar la respuesta en este momento. Intente nuevamente en unos minutos o contacte a soporte técnico.
```

## Troubleshooting

- `RAG pipeline not initialized`: verificar que `docs/` exista y tenga archivos `.pdf`, `.txt`, `.md` o `.json`.
- `shapes (...) not aligned`: reiniciar el backend después del último cambio; el fallback local ahora usa el mismo vector TF para documentos y consulta.
- `Connection refused` desde n8n: confirmar que `python main.py` sigue corriendo y revisar `127.0.0.1` vs `host.docker.internal`.
- `422 Unprocessable Entity` en `Search Documentation`: el backend no recibió `question`; probar directo `curl "http://localhost:8000/search?question=No%20se%20guardan%20los%20cambios"`.
- `Webhook not found`: en modo edición abrir el workflow y presionar **Execute workflow** antes de llamar `/webhook-test/...`; con workflow activo usar `/webhook/...`.
- CORS en la UI: usar `/ask`; no llamar n8n directamente desde el navegador salvo que n8n tenga CORS configurado.
- Respuestas sin contexto: bajar temporalmente `threshold` o revisar la calidad de los documentos en `docs/`.

## Archivos principales

```text
main.py               FastAPI, Swagger, /search, /health y /ui
rag_pipeline.py       Carga documentos, chunking y búsqueda semántica
prompt_engineering.py Prompts y fallback anti-alucinación
n8n_workflow.json     Automatización n8n importable
frontend/index.html   UI web estática
docs/                 Base documental del RAG
```
