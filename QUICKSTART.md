# QUICK START GUIDE - MineCatalog RAG

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (1 min)

```bash
cd "c:\Users\César\César\Prueba Técnica - César Córdoba"
pip install -r requirements.txt
```

Expected output:
```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 ...
```

### Step 2: Configure Environment (1 min)

```bash
# Copy the template
cp .env.example .env

# Edit .env with your OpenAI API Key
# Find this line and replace with your actual key:
# OPENAI_API_KEY=sk-your-actual-key-here
```

On Windows, edit with:
```bash
notepad .env
```

### Step 3: Start the API Server (1 min)

```bash
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Starting MineCatalog RAG API...
INFO:     Initializing RAG pipeline...
INFO:     Loaded 156 document chunks
INFO:     RAG pipeline initialized successfully
```

### Step 4: Test the API (1 min)

In another terminal:
```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","rag_initialized":true}
```

### Step 5: Try a Search Query (1 min)

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Credenciales incorrectas","top_k":3,"threshold":0.5}'
```

Expected: JSON with search results

---

## 🧪 Validation Checklist

### ✅ File Structure
- [ ] `main.py` exists
- [ ] `rag_pipeline.py` exists
- [ ] `prompt_engineering.py` exists
- [ ] `n8n_workflow.json` exists
- [ ] `.env.example` exists
- [ ] `README.md` exists
- [ ] `docs/` folder contains 4 files

### ✅ Python Environment
- [ ] Python 3.9+ installed: `python --version`
- [ ] pip installed: `pip --version`
- [ ] Dependencies installed: `pip list | grep fastapi`

### ✅ Configuration
- [ ] `.env` created from `.env.example`
- [ ] `OPENAI_API_KEY` is valid and active
- [ ] `DOCS_DIR_PATH=./docs` points to correct location

### ✅ API Functionality
- [ ] Health endpoint responds: `/health`
- [ ] Search endpoint works: `/search`
- [ ] Context endpoint works: `/context`
- [ ] No errors in Python console

### ✅ n8n Integration (Optional)
- [ ] n8n installed and running on port 5678
- [ ] Workflow JSON can be imported
- [ ] Webhook URL is accessible
- [ ] OpenAI credentials configured in n8n

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
pip install -r requirements.txt --upgrade
```

### "OPENAI_API_KEY is invalid"
1. Get a new key: https://platform.openai.com/api-keys
2. Check key format starts with `sk-`
3. Verify .env has correct key
4. Restart Python server

### "Connection refused on port 8000"
```bash
# Check if port is in use
lsof -i :8000

# If needed, use different port:
# Edit .env: API_PORT=8001
# Then: python main.py
```

### "No document chunks loaded"
1. Verify `docs/` folder exists
2. Check files: `Documentación 1.pdf`, `Documentación 2.txt`, etc.
3. Check permissions on `docs/` folder
4. Look at Python error logs for parse errors

### "Hallucination detected in response"
- This is intentional (safety feature)
- System will use fallback message
- Check SYSTEM_PROMPT_TEMPLATE in `prompt_engineering.py`

---

## 📝 Example Queries to Test

### Queries Que Deben Funcionar (Documentadas)

```bash
# 1. Authentication Error
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Credenciales incorrectas"}'

# 2. Database Connection
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Error de conexión a la base de datos"}'

# 3. Duplicate Code
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Código de material duplicado"}'
```

### Queries Que Deben Mostrar Fallback (No Documentadas)

```bash
# Error 502 (not in docs)
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"¿Qué significa error 502?"}'

# Custom question (unlikely to be documented)
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"¿Cuál es el sentido de la vida?"}'
```

---

## 📊 Performance Verification

### Check Latency

```bash
# Install 'time' utility
# Then measure response time
time curl http://localhost:8000/health

# Should be < 100ms
```

### Check Concurrent Requests

```bash
# Use Apache Bench (if installed)
ab -n 100 -c 10 http://localhost:8000/health

# Or parallel requests with curl
for i in {1..10}; do
  curl http://localhost:8000/health &
done
wait
```

---

## 🚀 Next Steps

### 1. Integration with n8n
- See section "Integración con n8n" en README.md
- Import `n8n_workflow.json`
- Configure OpenAI credentials

### 2. Deployment
- Option A: Docker (see Dockerfile in docs)
- Option B: Cloud (AWS, GCP, Azure)
- Option C: VPS (DigitalOcean, Linode)

### 3. Monitoring
- Set up log aggregation (ELK, Splunk)
- Add metrics dashboard (Prometheus, Grafana)
- Set up alerting for errors

### 4. Feedback Loop
- Collect user feedback
- Track hallucination incidents
- Improve prompts iteratively

---

## 📞 Need Help?

### Resources
- 📖 See `README.md` for full documentation
- 🏗️ See `ARCHITECTURE.md` for technical details
- 🧪 See `tests.py` for validation scenarios
- 💬 Review `prompt_engineering.py` for prompt tuning

### Common Questions

**Q: Can I change the chunk size?**
A: Yes, edit `.env`: `CHUNK_SIZE=500` (default)

**Q: How do I add more documentation?**
A: Drop new files in `docs/` folder and restart API

**Q: Can I use different embeddings?**
A: Yes, modify `EmbeddingManager` in `rag_pipeline.py`

**Q: How do I prevent hallucinations?**
A: Already implemented! See `SYSTEM_PROMPT_TEMPLATE` validation

---

## ✨ Success Indicators

You'll know it's working when:

1. ✅ `python main.py` starts without errors
2. ✅ `curl http://localhost:8000/health` returns `{"status":"healthy"}`
3. ✅ Queries return results with similarity scores
4. ✅ Undocumented queries show fallback message
5. ✅ n8n webhook can call the API successfully
6. ✅ Full end-to-end flow works (webhook → search → LLM → response)

---

## 🎓 Learning Resources

- FastAPI: https://fastapi.tiangolo.com/
- RAG Concept: https://arxiv.org/abs/2005.11401
- OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings
- n8n: https://docs.n8n.io/

---

**Last Updated:** May 2024
**Status:** ✅ Ready to Use
**Support Email:** soporte.minecatalog@empresa.com
