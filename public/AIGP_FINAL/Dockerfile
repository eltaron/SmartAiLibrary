# ─────────────────────────────────────────────
# Base: CPU
# ─────────────────────────────────────────────
FROM python:3.12-slim AS python-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy English model via wheel (avoids spacy CLI import issues during build)
RUN pip install --no-cache-dir \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

COPY shared/ /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared


# ─────────────────────────────────────────────
# Runtime: CPU
# ─────────────────────────────────────────────
FROM python:3.12-slim AS python-runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=python-base /usr/local /usr/local
COPY . /app

ENV PYTHONPATH=/app


# ─────────────────────────────────────────────
# Base: GPU (CUDA) - uses official PyTorch image with a stable Python build
# ─────────────────────────────────────────────
FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime AS cuda-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy English model via wheel (needed by ingestion/cleaner pipeline)
RUN pip install --no-cache-dir \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

COPY shared/ /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

COPY . /app


# ─────────────────────────────────────────────
# Runtime: GPU
# ─────────────────────────────────────────────
FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime AS cuda-runtime

WORKDIR /app

COPY --from=cuda-base /app /app
COPY --from=cuda-base /opt/conda /opt/conda

ENV PYTHONPATH=/app


# ─────────────────────────────────────────────
# Services (CPU)
# ─────────────────────────────────────────────

FROM python-runtime AS ingestion
CMD ["uvicorn", "services.ingestion.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM cuda-runtime AS embedding
CMD ["python", "-m", "services.embedding.batch_job"]

FROM python-runtime AS rec_service
CMD ["uvicorn", "services.rec_service.main:app", "--host", "0.0.0.0", "--port", "8001"]

FROM python-runtime AS search_service
CMD ["uvicorn", "services.search_service.main:app", "--host", "0.0.0.0", "--port", "8002"]

FROM python-runtime AS rag_service
CMD ["uvicorn", "services.rag_service.main:app", "--host", "0.0.0.0", "--port", "8004"]


# ─────────────────────────────────────────────
# Services (GPU)
# ─────────────────────────────────────────────

FROM cuda-runtime AS summarise_service
CMD ["uvicorn", "services.summarise_service.main:app", "--host", "0.0.0.0", "--port", "8003"]
