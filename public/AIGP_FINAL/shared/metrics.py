"""
shared/metrics.py
Prometheus metrics for all services.
"""
from prometheus_client import Counter, Histogram, Gauge

search_latency = Histogram(
    "search_latency_seconds",
    "Search request latency",
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0],
)

rerank_latency = Histogram(
    "rerank_latency_seconds",
    "Re-ranking latency",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1],
)

rec_requests_total = Counter(
    "rec_requests_total",
    "Total recommendation requests",
    ["user_tier"],
)

rec_cache_hits_total = Counter(
    "rec_cache_hits_total",
    "Total recommendation cache hits",
)

rec_latency = Histogram(
    "rec_latency_seconds",
    "Recommendation request latency",
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2],
)

summarise_requests_total = Counter(
    "summarise_requests_total",
    "Total summarisation requests",
)

summarise_active_jobs = Gauge(
    "summarise_active_jobs",
    "Number of active summarisation jobs",
)

summarise_latency = Histogram(
    "summarise_latency_seconds",
    "Summarisation request latency",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

rag_requests_total = Counter(
    "rag_requests_total",
    "Total RAG requests",
)

rag_hallucination_rate = Gauge(
    "rag_hallucination_rate",
    "RAG hallucination rate (shadow eval)",
)

rag_latency = Histogram(
    "rag_latency_seconds",
    "RAG request latency",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

embedding_chunks_total = Counter(
    "embedding_chunks_total",
    "Total chunks embedded",
)

embedding_failures_total = Counter(
    "embedding_failures_total",
    "Total embedding failures",
)

ingest_chunks_total = Counter(
    "ingest_chunks_total",
    "Total chunks ingested",
)

error_counter = Counter(
    "errors_total",
    "Total errors",
    ["service", "error_code"],
)