# ─────────────────────────────────────────────
# Base: CPU
# ─────────────────────────────────────────────
FROM python:3.11-slim AS python-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared


# ─────────────────────────────────────────────
# Runtime: CPU
# ─────────────────────────────────────────────
FROM python:3.11-slim AS python-runtime

WORKDIR /app

COPY --from=python-base /usr/local /usr/local
COPY . /app

ENV PYTHONPATH=/app


# ─────────────────────────────────────────────
# Base: GPU (CUDA)
# ─────────────────────────────────────────────
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS cuda-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-dev python3-pip build-essential \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY shared/ /tmp/shared
RUN pip3 install --no-cache-dir /tmp/shared && rm -rf /tmp/shared


# ─────────────────────────────────────────────
# Runtime: GPU (FIXED - NO /usr/local COPY)
# ─────────────────────────────────────────────
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS cuda-runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3-pip \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ❌ مهم: لا تنسخي /usr/local نهائيًا (كان سبب bug uvicorn)
COPY --from=cuda-base /app /app

ENV PYTHONPATH=/app


# ─────────────────────────────────────────────
# Services (CPU)
# ─────────────────────────────────────────────

FROM python-runtime AS ingestion
CMD ["uvicorn", "services.ingestion.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python-runtime AS embedding
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