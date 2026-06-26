# Smart AI Library (AIGP)

A microservices-based AI-augmented digital library platform. Ingests books (PDF/ePub), generates semantic embeddings, and exposes APIs for search, recommendations, summarization, and RAG-based Q&A.

## Architecture

```
                    ┌─── HTTP ───┐
  User ──▶ ingestion ──Kafka──▶ embedding ──▶ Pinecone
          │ 8000       │          │
          │            │          │
          ├── rec ─────┤          │
          │  8001      │          │
          ├── search ──┼──────────┤
          │  8002      │          │
          ├── summarise┤   GPU    │
          │  8003      │          │
          └── rag ─────┤          │
             8004      │          │
                       ▼          ▼
                    Redis     PostgreSQL
```

Services communicate over HTTP (client → service) and Kafka (ingestion → embedding). Redis is used for caching and state, PostgreSQL for relational data (books, users, events), and Pinecone for vector storage.

## Prerequisites

- Python >=3.12
- Docker & Docker Compose
- Make
- (Optional) NVIDIA GPU + CUDA 12.1 for summarisation
- API keys: [Pinecone](https://www.pinecone.io/) (required), [OpenAI](https://platform.openai.com/) (required for RAG)

## Quick Start

### 1. Clone and set up the environment

```bash
git clone <repo-url>
cd aigp

python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
make install
pip install -e ./shared
```

The root `requirements.txt` contains all runtime dependencies. `shared/` is installed as a local package.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENV=your-pinecone-environment
OPENAI_API_KEY=your-openai-key
```

### 4. Start infrastructure

```bash
make up
```

This starts PostgreSQL 16, Redis 7, ZooKeeper, and Kafka via Docker Compose. Run `make ps` to verify all containers are healthy.

### 5. Run database migrations

```bash
alembic upgrade head
```

Creates the `books`, `users`, `reading_events`, `ratings`, and `bookmarks` tables.

### 6. Run the application

**Option A — Production (all services in Docker):**

```bash
make deploy-build
make deploy-up
```

**Option B — Development (run services locally):**

Start each service in a separate terminal:

```bash
# Terminal 1: Ingestion (port 8000)
uvicorn services.ingestion.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Embedding (Kafka consumer, no port)
python -m services.embedding.batch_job

# Terminal 3: Recommendations (port 8001)
uvicorn services.rec_service.main:app --host 0.0.0.0 --port 8001

# Terminal 4: Search (port 8002)
uvicorn services.search_service.main:app --host 0.0.0.0 --port 8002

# Terminal 5: Summarisation (port 8003, GPU)
uvicorn services.summarise_service.main:app --host 0.0.0.0 --port 8003

# Terminal 6: RAG Q&A (port 8004)
uvicorn services.rag_service.main:app --host 0.0.0.0 --port 8004
```

## Services

| Service | Port | Type | Description |
|---------|------|------|-------------|
| **ingestion** | 8000 | FastAPI | Upload PDF/ePub books, extract text, split into token-sized chunks |
| **embedding** | — | Batch consumer | Reads chunks from Kafka, encodes with sentence-transformers, upserts to Pinecone |
| **rec_service** | 8001 | FastAPI | Hybrid recommendations (Neural CF + Content-Based Filtering) |
| **search_service** | 8002 | FastAPI | Semantic search with bi-encoder + cross-encoder reranking |
| **summarise_service** | 8003 | FastAPI (GPU) | Map-reduce summarization with FLAN-T5-large, optional mind maps |
| **rag_service** | 8004 | FastAPI | RAG Q&A over book content using LangChain + OpenAI |

## Configuration

All services load configuration from environment variables via `shared/config.py`.

### Required variables

| Variable | Description |
|----------|-------------|
| `PINECONE_API_KEY` | Pinecone API key |
| `PINECONE_ENV` | Pinecone environment (e.g. `us-west1-gcp`) |
| `OPENAI_API_KEY` | OpenAI API key (for RAG service) |

### Common variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/smartailibrary` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka brokers |
| `PINECONE_INDEX` | `smart-library-books` | Pinecone index name |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CHUNK_SIZE` | 512 | Tokens per chunk |
| `EMBEDDING_MODEL` | `sentence-transformers/all-mpnet-base-v2` | Embedding model |
| `RAG_LLM_MODEL` | `gpt-4o-mini` | LLM for RAG |

See `shared/config.py` for the full list of 40+ configuration options.

## API Endpoints

### Ingestion (`/api/v1/ingestion`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingest` | Upload a book (PDF/ePub) |
| GET | `/status/{job_id}` | Check ingestion status |

### Search (`/api/v1/search`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/search` | Semantic search with filters |
| GET | `/similar/{isbn}` | Find similar books |

### Recommendations (`/api/v1/rec`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/recommendations/{user_id}` | Get personalized recommendations |

### Summarisation (`/api/v1/summarise`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/summarise` | Generate book summary (optionally with mind map) |
| GET | `/summary/{isbn}` | Retrieve cached summary |

### RAG (`/api/v1/qa`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/qa/sync` | Ask a question (JSON response with citations) |
| POST | `/qa/stream` | Ask a question (SSE streaming response) |

## Development

### Linting and formatting

```bash
make lint
```

Runs `isort`, `black`, `mypy`, and `ruff` across `services/`, `shared/`, and `tests/`.

### Testing

```bash
make test           # Run all tests
make test-coverage  # Run with coverage report
```

Tests use `pytest`, `pytest-asyncio`, `httpx` (for API tests), and `fakeredis` (for Redis tests).

### Database migrations

Alembic migrations are in `shared/migrations/`.

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Deployment

The production Docker Compose file is self-contained and includes all infrastructure, app services, and monitoring.

```bash
make deploy-build     # Build all Docker images
make deploy-up        # Start everything (infra + 6 services + monitoring)
make deploy-logs      # Tail logs from all containers
make deploy-ps        # List running containers
make deploy-down      # Stop and remove containers
```

Behind the scenes these run:
```bash
docker compose -f infra/docker-compose.prod.yml build
docker compose -f infra/docker-compose.prod.yml up -d
# etc.
```

### Docker image tags

All services are built with both an `image:` tag and `build:` config:

| Service | Image name |
|---------|------------|
| ingestion | `smart-ai-library-ingestion:latest` |
| embedding | `smart-ai-library-embedding:latest` |
| rec_service | `smart-ai-library-rec:latest` |
| search_service | `smart-ai-library-search:latest` |
| summarise_service | `smart-ai-library-summarise:latest` |
| rag_service | `smart-ai-library-rag:latest` |

## Monitoring

Prometheus scrapes all services every 15 seconds. Grafana dashboards are provisioned automatically.

When deployed:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin / admin)

Custom metrics (defined in `shared/metrics.py`):
- Request latency histograms
- Request / cache-hit / error counters
- Active GPU job gauge
- Hallucination rate gauge
- Kafka consumer lag

Alert rules (in `infra/prometheus/alerts.yml`):
- ServiceDown, HighLatency (>5s), LowCacheHitRate (<30%)
- HighPineconeLatency (>100ms p99), KafkaLag (>5000), HighErrorRate (>5%)

## Makefile reference

| Target | Description |
|--------|-------------|
| `install` | Install package in editable mode |
| `lint` | Run all linters (isort, black, mypy, ruff) |
| `test` | Run test suite |
| `test-coverage` | Run tests with coverage |
| `build` | Build Docker images (dev) |
| `up` | Start dev services |
| `down` | Stop dev services |
| `logs` | Tail dev logs |
| `ps` | List dev containers |
| `deploy-build` | Build production Docker images |
| `deploy-up` | Start production services |
| `deploy-down` | Stop production services |
| `deploy-logs` | Tail production logs |
| `deploy-ps` | List production containers |
| `clean` | Remove build artifacts |
