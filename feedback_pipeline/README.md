# Module 8 — Feedback Pipeline (`feedback_pipeline/`)

The **Feedback Pipeline** is the operational observability, telemetry persistence, and historical feedback layer of the AI Model Router framework. Positioned directly after Module 7 (Gateway Router), it ingests executed dispatch results (`GatewayResponse`), stores structured telemetry traces into a persistent repository (PostgreSQL in production, SQLite in testing), enables asynchronous user and evaluator quality rating submissions, and computes aggregated historical metrics to inform future routing optimizations.

---

## Architectural Responsibility

```
Incoming Request
      │
      ▼
Module 1 — Complexity Predictor
      │
      ▼
Module 2 — Model Registry
      │
      ▼
Module 3 — Capability Matcher
      │
      ▼
Module 4 — Rule Engine
      │
      ▼
Module 5 — Ranking Engine
      │
      ▼
Module 6 — Policy Engine
      │
      ▼
Module 7 — Gateway Router
      │
      ▼
Module 8 — Feedback Pipeline  <── [ THIS MODULE ]
      │
      ├── Telemetry Ingestion (Execution facts & metrics)
      ├── Qualitative Quality Feedback (User/evaluator ratings 1–5)
      ├── SQLAlchemy Repository (PostgreSQL / SQLite)
      └── Historical Analytics Dashboard (Aggregated metrics)
```

---

## Core Design Principles & Invariants

1. **Strict Observability Scope:** Module 8 strictly observes and records. It does **not** alter live routing decisions, re-rank candidate models, perform model inference, or execute commercial API calls.
2. **Telemetry vs. Feedback Domain Separation:**
   - **Telemetry ("What happened?"):** Model, provider, latency, retries, execution status, token counts, complexity scores, fallback usage. Emitted automatically upon execution completion.
   - **Feedback ("How good was the result?"):** Qualitative user ratings (1–5 scale), comments, quality categories (`accurate`, `slow`, `hallucination`). Attached asynchronously post-execution.
3. **Dual Persistence Architecture:**
   - **Production Target:** PostgreSQL with SQLAlchemy ORM.
   - **Testing & Local Prototype:** In-memory or local file-based SQLite database via SQLAlchemy, ensuring 100% deterministic offline testability with zero external daemon dependencies.
4. **Data Privacy & Prompt Sanitization:** Enterprise-grade prompt protection truncating or redacting full input prompts (`store_full_prompt: false`, default max 200 character summary).
5. **Lightweight Architecture:** Zero message brokers (Kafka/RabbitMQ), zero task queues (Celery), and zero external caching daemons (Redis).

---

## File Structure

```
feedback_pipeline/
├── README.md                           # Module overview, architecture, and usage
├── requirements.txt                    # Minimal dependencies (SQLAlchemy, FastAPI)
├── config/
│   └── default_feedback_config.json   # Default database URL and retention settings
├── docs/
│   └── design_overview.md             # In-depth architectural design specification
├── walkthrough.md                     # Implementation walkthrough and validation report
├── scripts/
│   └── demo.py                        # Interactive 5-scenario demonstration script
├── src/
│   ├── __init__.py                    # Public package exports
│   ├── models.py                      # RoutingEvent and FeedbackRecord dataclasses
│   ├── config.py                      # FeedbackConfig loader and validator
│   ├── schema.py                      # SQLAlchemy ORM declarative table schemas
│   ├── repository.py                  # Abstract & SQLAlchemy repository implementation
│   ├── service.py                     # FeedbackService coordinating ingestion and feedback
│   ├── analytics.py                   # FeedbackAnalytics computing aggregated metrics
│   └── api.py                         # Thin FastAPI transport endpoints
└── tests/
    ├── __init__.py
    ├── test_models.py                 # Domain models and conversion tests
    ├── test_repository.py             # SQLAlchemy CRUD & query tests on SQLite
    ├── test_service.py                # FeedbackService orchestration tests
    ├── test_analytics.py              # Aggregated metrics and calculation tests
    ├── test_integration.py            # End-to-end M1–M7 -> M8 integration tests
    ├── test_api.py                    # FastAPI transport endpoint tests
    └── test_demo_script.py            # Smoke execution of demo.py
```

---

## Quick Start & Usage

### 1. Ingest Gateway Telemetry Programmatically

```python
from gateway_router.src.orchestrator import PipelineRouter
from feedback_pipeline.src import FeedbackService, FeedbackAnalytics

# 1. Execute routing pipeline (Modules 1–7)
pipeline = PipelineRouter()
raw_request = {
    "request_id": "REQ-001",
    "prompt": "Write a Python function to compute primes.",
    "metadata": {"task_category": "Programming"}
}
response = pipeline.route_and_execute(raw_request)

# 2. Ingest telemetry into Feedback Pipeline (Module 8)
service = FeedbackService()
event = service.record_gateway_response(
    response=response,
    request_prompt=raw_request["prompt"],
    task_category="Programming"
)
print(f"Recorded Event ID: {event.event_id}, Model: {event.model_id}, Latency: {event.latency_ms}ms")

# 3. Attach User Feedback
service.submit_feedback(
    event_id=event.event_id,
    rating=5,
    quality_category="accurate",
    comment="Clean, optimal code."
)

# 4. Query Historical Analytics
analytics = FeedbackAnalytics(repository=service.repository)
print("System Summary:", analytics.get_summary_metrics())
print("Quality Metrics:", analytics.get_quality_metrics())
```

---

## Running Automated Tests

```bash
# Run Module 8 test suite
python -m unittest discover -s feedback_pipeline/tests -v

# Run demonstration script
python feedback_pipeline/scripts/demo.py
```
