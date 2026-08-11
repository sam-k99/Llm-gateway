<img width="1920" height="995" alt="dashboard02" src="https://github.com/user-attachments/assets/18a6c41a-8308-4856-bef3-f3c3ed5de8aa" />


The **LLM Gateway** is a high-throughput, production-grade API middleware designed to sit between client applications and Large Language Model (LLM) providers. 

As enterprises scale AI adoption, they face three critical bottlenecks: exorbitant API costs, latency bottlenecks, and security vulnerabilities (PII leaks and prompt injections). This gateway solves these issues by providing a unified, OpenAI-compatible API interface that handles dynamic model routing, semantic caching, real-time safety guardrails, and full observability.

---

## 🚀 Key Features

*   **Dynamic Model Routing:** Classifies prompt complexity and routes simple queries to cheap/fast models (`open-mistral-7b`), reserving expensive models (`mistral-large-latest`) for complex reasoning tasks.
*   **Semantic Caching:** Utilizes Redis and vector embeddings to cache responses. If a similar prompt (cosine similarity > 85%) is received, the gateway returns the cached response instantly, bypassing the LLM entirely.
*   **Security & Guardrails:** Intercepts prompts to redact Personally Identifiable Information (PII) using Regex and blocks adversarial prompt injection attacks before they reach external servers.
*   **Observability:** Tracks token usage, cost, cache hits, and latency per request in real-time using Prometheus, visualized in a live Grafana dashboard.

---

## 📊 Real-World Benchmark Results

Tested against 50 varied and semantically duplicated requests (simulating real-world chatbot traffic where users ask the same questions differently):

```text
========================================
  ENTERPRISE BENCHMARK RESULTS
========================================
Total Requests      : 50
Cache Hits          : 47
Cache Misses        : 3
Cache Hit Rate      : 94.00%
Avg Latency/Request : 954.95ms
----------------------------------------
Cost WITHOUT Gateway (GPT-4o): $0.2463
Cost WITH Gateway (Mistral+Cache): $0.0002
Total Money Saved   : $0.2460 (99.90% reduction)
========================================
```
*Result:* By routing to cheaper models and utilizing semantic caching, the gateway effectively eliminates standard API costs for redundant traffic, achieving a **99.90% cost reduction** compared to standard GPT-4o routing.

---

## 📈 Live Monitoring Dashboard (Grafana)

The gateway exposes a `/metrics` endpoint that Prometheus scrapes every 5 seconds. Grafana visualizes this data in real-time, allowing engineering teams to monitor cache hit rates, token consumption, and API latency.

Grafana hits vs misses
![Grafana Dashboard](dashboard03.png)
![Grafana Dashboard](dashboard05.png)

Token usage and latency
![Grafana Dashboard](dashboard08.png)
![Grafana Dashboard](dashboard06.png)

terminal-view
![Grafana Dashboard](dashboard01.png)


---

## 🛠 Tech Stack

*   **API Framework:** FastAPI (Python 3.12)
*   **LLM Routing:** OpenAI-compatible client (Mistral AI)
*   **Caching Layer:** Redis, NumPy (Cosine Similarity Vector Math)
*   **Security:** Custom Regex PII Redaction, Prompt Injection Defense
*   **Observability:** Prometheus, Grafana
*   **Containerization:** Docker, Docker Compose

---

## 🏗 Architecture Diagram

```text
[Client App / User]
       |
       v
+---------------------------------------------------+
|           FastAPI Gateway Application             |
|                                                   |
| 1. Input Validation & Logging (Prometheus)        |
|       |                                           |
|       v                                           |
| 2. Security Guardrails                            |
|    - PII Redaction (e.g., SSN -> [REDACTED])      |
|    - Prompt Injection Detection (Block/Reject)    |
|       |                                           |
|       v                                           |
| 3. Semantic Cache Layer (Redis Vector DB)         |
|    - Generate Embedding for prompt                |
|    - Check for similar cached prompts (> 0.85 sim)|
|    - IF MATCH: Return cached response (Exit)      |
|    - IF NO MATCH: Proceed to Router               |
|       |                                           |
|       v                                           |
| 4. Dynamic Router                                 |
|    - LLM Classifier (Simple vs. Complex)          |
|    - IF Simple: Route to open-mistral-7b          |
|    - IF Complex: Route to mistral-large-latest    |
|       |                                           |
|       v                                           |
| 5. LLM Provider (External API)                    |
|       |                                           |
|       v                                           |
| 6. Response Processor                             |
|    - Calculate Cost (Tokens * Rate)               |
|    - Store Prompt+Response in Redis Cache         |
|    - Log Metrics to Prometheus                    |
+---------------------------------------------------+
       |
       v
[JSON Response Returned to Client]
```

---

## ⚙️ How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sam-k99/llm-gateway.git
   cd llm-gateway
   ```

2. **Set Environment Variables:**
   Create a `.env` file in the root directory and add your API key:
   ```env
   MISTRAL_API_KEY=your-mistral-api-key-here
   ```

3. **Spin up the infrastructure:**
   Ensure Docker and Docker Compose are installed, then run:
   ```bash
   docker-compose up -d --build
   ```
   This will start four containers:
   * `llm-gateway-app` (FastAPI Server on port 8000)
   * `llm-gateway-redis` (Redis Cache on port 6379)
   * `llm-gateway-prometheus` (Monitoring on port 9090)
   * `llm-gateway-grafana` (Dashboard on port 3000)

4. **Test the Endpoint:**
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
   -H "Content-Type: application/json" \
   -d '{
     "model": "auto-router",
     "messages": [{"role": "user", "content": "What is the capital of France?"}]
   }'
   ```

5. **View the Dashboard:**
   Open `http://localhost:3000` to access Grafana (Username: `admin` / Password: `admin`). 

---

## 🔬 Engineering Challenges & Solutions

*   **Challenge:** Python module pathing in Docker vs Local environments caused `ModuleNotFoundError` and circular imports.
    *   **Solution:** Restructured data models into a separate `models.py` file to break circular dependencies. Utilized `PYTHONPATH` locally and changed the Dockerfile `WORKDIR` to `/app/src` to standardize module resolution without changing application code.
*   **Challenge:** Substring matching in the routing classifier caused false positives (e.g., the word "c-API-tal" contained the keyword "api", routing simple prompts to the expensive model).
    *   **Solution:** Refactored the classifier to split the prompt into a set of words and use set-intersection matching instead of basic substring matching.
*   **Challenge:** Dependency conflicts between FastAPI/Starlette, the OpenAI Python SDK, and the Prometheus Instrumentator caused runtime crashes (`proxies` keyword error).
    *   **Solution:** Pinned the exact required versions (`httpx==0.27.0`, `starlette==0.37.2`, etc.) in `requirements.txt` to ensure reproducible, stable builds across all environments.



***
# Commmands:
***
### 🚀 Lifecycle Management (Docker Compose)

**Start the entire system (Gateway + Redis + Prometheus + Grafana):**
```bash
docker-compose up -d
```

**Stop the entire system (safely shuts down all containers):**
```bash
docker-compose down
```

**Rebuild the system (use this if you change `requirements.txt`, `Dockerfile`, or `docker-compose.yml`):**
```bash
docker-compose up -d --build
```

---

### 📋 Monitoring & Debugging

**Check if all 4 containers are running:**
```bash
docker ps
```

**View live logs for the FastAPI Gateway (great for seeing routing and cache hits):**
```bash
docker logs -f llm-gateway-app
```
*(Press `Ctrl+C` to exit the live log view).*

**View live logs for everything at once:**
```bash
docker-compose logs -f
```

---

### 🧪 Testing & Benchmarking

**Send a test prompt to the Gateway:**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "auto-router", "messages": [{"role": "user", "content": "What is the capital of France?"}]}'
```

**Run the 50-request benchmark script (generates traffic and calculates cost savings):**
```bash
python benchmark.py
```

---

### 🗄️ Redis Cache Maintenance

**Wipe the semantic cache clean (forces the gateway to make fresh LLM calls):**
```bash
docker exec -it llm-gateway-redis redis-cli FLUSHALL
```

---

### 💻 Local Development (Without Docker)

If you want to run the FastAPI server locally on your machine (without Docker) while keeping Redis in Docker:

**1. Start only Redis via Docker:**
```bash
docker run -d --name redis-local -p 6379:6379 redis
```

**2. Activate your local Python environment:**
```bash
source venv/bin/activate
```

**3. Run the FastAPI server locally:**
```bash
PYTHONPATH=src python -m uvicorn main:app --reload --port 8000
```

---

### 🧹 Complete Cleanup (Free up disk space)

**Stop containers AND delete their volumes (wipes all persistent data):**
```bash
docker-compose down -v
```

**Remove the built Docker image (forces a complete fresh build next time):**
```bash
docker rmi llm-gateway-gateway
```

***

### Accessing the UIs
*   **FastAPI Docs (Swagger UI):** `http://localhost:8000/docs`
*   **Raw Prometheus Metrics:** `http://localhost:8000/metrics`
*   **Prometheus Dashboard:** `http://localhost:9090`
*   **Grafana Dashboard:** `http://localhost:3000` (admin / admin)




***
# File Stucture:
***

llm-gateway/
├── .env                      # Environment variables (MISTRAL_API_KEY)
├── .dockerignore             # Files ignored by Docker (venv, .env, etc.)
├── .gitignore                # Files ignored by Git (venv, .env, __pycache__)
├── Dockerfile                # Blueprint for building the FastAPI Docker image
├── docker-compose.yml        # Orchestrates Gateway, Redis, Prometheus, and Grafana
├── prometheus.yml            # Configuration telling Prometheus to scrape port 8000
├── benchmark.py              # Script to generate traffic and calculate cost savings
├── requirements.txt          # Python dependencies with pinned versions
├── README.md                 # Project documentation
└── src/                      # Main application source code
    ├── __init__.py
    ├── main.py               # FastAPI entry point, Prometheus instrumentation
    ├── api/
    │   ├── __init__.py
    │   ├── models.py         # Pydantic models (OpenAI-compatible JSON schemas)
    │   └── routes.py         # API endpoints (/v1/chat/completions)
    └── core/
        ├── __init__.py
        ├── router.py         # Dynamic routing logic, metrics recording
        ├── security.py       # PII redaction & prompt injection defense
        ├── cache.py          # Semantic caching (Redis + Vector Embeddings)
        └── metrics.py        # Prometheus custom metrics definitions



***
# Server logs:
***


# To see the "stats"  you have **three places** to look:
***


### 1. The Terminal Logs (See the routing decisions live)
If you want to see your Gateway thinking and routing in real-time, run this command in your terminal:
```bash
docker logs -f llm-gateway-app
```
When you send that `curl` command, you will see lines pop up in this terminal like:
*   `[Router] Prompt Type: SIMPLE | Routing to: open-mistral-7b`
*   `[Cache] 💾 Saved to cache.`
*(Press `Ctrl+C` to exit the live logs).*

### 2. The Raw Metrics (Prometheus format)
Open your web browser and go to:
**http://localhost:8000/metrics**

Scroll down to the `gateway_` section. You will see your custom metrics updating. You'll see things like:
*   `gateway_llm_tokens_total{model="ministral-8b-latest",token_type="prompt"} 10.0`
*   `gateway_llm_latency_seconds_sum{model="ministral-8b-latest"} 1.23`

### 3. The Grafana Dashboard (The Visual UI)
Since you just spun up the containers fresh, you will need to do the Grafana setup one more time to see the visual graph:
1. Go to **http://localhost:3000** (Login: `admin` / `admin`).    --change pass according to you 
2. Click the **Plus (+) icon** -> **New Dashboard** -> **Add Visualization**.
3. Select **Prometheus** as the data source.
4. Under the Query box, click **"Select metric"** and search for `gateway_cache_hits_total`.
5. Change the visualization type on the right to **Stat**.
6. Click **Save**.
