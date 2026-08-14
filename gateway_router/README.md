# Module 7 — Gateway Router (`gateway_router/`)

The **Gateway Router** is the execution layer of the AI Model Router framework. Positioned directly after Module 6 (Policy Engine), it accepts authorized model dispatch decisions (`PolicyDecision`), resolves the target provider adapter, executes the request through a local simulated execution path (requiring zero external API calls or credentials), manages bounded retries for transient execution failures, and exposes a streaming-compatible response abstraction alongside a lightweight FastAPI transport layer.

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
Module 7 — Gateway Router  <── [ THIS MODULE ]
      │
      ▼
Mock Provider Adapters (Local Simulation)
      │
      ▼
Future Module 8 — Feedback Pipeline
```

---

## Core Design Principles & Constraints

1. **Zero Commercial API Calls & Zero Cloud Spending:**
   The Gateway Router operates entirely offline using local `MockProviderAdapter` instances. It requires no API keys, no provider SDKs (`openai`, `anthropic`, `google-generativeai`), and incurs no financial costs.
2. **Explicit Mock Execution:**
   All responses are clearly identified with `execution_mode: "mock"` and descriptive content (`"[MOCK EXECUTION] Simulated response from provider 'OpenAI' for model 'gpt-4o'..."`). It never claims that external foundation models were contacted.
3. **Strict Separation of Governance vs. Execution Retries:**
   - **Module 6 (Policy Engine)** owns runtime budget, quota enforcement, and *bounded fallback model selection*.
   - **Module 7 (Gateway Router)** owns execution and *transient retries on the same selected model*. It does NOT re-rank or switch models independently.
4. **Explicit Adapter Resolution:**
   Missing provider adapters return `ExecutionStatus.ADAPTER_NOT_FOUND` rather than silently falling back to a generic default adapter.
5. **Decoupled Transport:**
   FastAPI is a thin transport wrapper (`api.py`). The core `GatewayRouter` and `PipelineRouter` classes are 100% usable programmatically in standard Python scripts without running an HTTP server.

---

## Module Structure

```
gateway_router/
├── README.md
├── requirements.txt
├── config/
│   └── default_gateway_config.json
├── docs/
│   └── design_overview.md
├── walkthrough.md
├── scripts/
│   └── demo.py
├── src/
│   ├── __init__.py
│   ├── models.py          # GatewayRequest, GatewayResponse, StreamChunk, Enums
│   ├── config.py          # GatewayConfig specification and loader
│   ├── exceptions.py      # Error classification (Transient vs Permanent)
│   ├── gateway.py         # GatewayRouter core execution engine
│   ├── orchestrator.py    # PipelineRouter (M1->M7 end-to-end composer)
│   ├── api.py             # FastAPI REST & SSE streaming transport
│   └── adapters/
│       ├── __init__.py
│       ├── base.py        # BaseProviderAdapter abstraction
│       ├── mock.py        # MockProviderAdapter with fault injection hooks
│       └── registry.py    # AdapterRegistry for provider resolution
└── tests/
    ├── __init__.py
    ├── test_adapters.py   # Adapter execution & simulation tests
    ├── test_gateway.py    # Decision state handling & policy blocking
    ├── test_retries.py    # Bounded retries & error classification
    ├── test_streaming.py  # Stream chunk generation & final chunk flags
    ├── test_integration.py# End-to-end M1->M7 pipeline tests
    ├── test_api.py        # FastAPI endpoints tests via TestClient
    └── test_demo_script.py# Demo smoke execution test
```

---

## Quick Start & Usage

### 1. Programmatic Gateway Execution
```python
from gateway_router.src import GatewayRouter, GatewayRequest
from policy_engine.src import PolicyDecision, DecisionState

gateway = GatewayRouter()

# Executing an authorized PolicyDecision
request = GatewayRequest(
    request_id="REQ-001",
    prompt="Explain recursion in Python.",
    provider="OpenAI",
    model_id="gpt-4o"
)
response = gateway.execute(request)
print(response.status)       # ExecutionStatus.SUCCESS
print(response.content)      # [MOCK EXECUTION] Simulated response...
print(response.retry_count)  # 0
```

### 2. End-to-End Pipeline Routing
```python
from gateway_router.src import PipelineRouter

pipeline = PipelineRouter()
raw_request = {
    "request_id": "REQ-PROD-001",
    "prompt": "Write a quicksort function in Python.",
    "metadata": {"task_category": "Programming"},
    "expected_output": {"format": "code"}
}

response = pipeline.route_and_execute(raw_request)
print(f"Executed Model: {response.model_id} via Provider: {response.provider}")
print(f"Content: {response.content}")
```

### 3. Running the Demonstration
```bash
python gateway_router/scripts/demo.py
```

### 4. Running the Test Suite
```bash
python -m unittest discover -s gateway_router/tests -v
```

---

## Future Provider Integration Path
When live commercial API integration is approved in the future, real provider adapters (e.g. `OpenAIAdapter`, `AnthropicAdapter`) can be created by subclassing `BaseProviderAdapter` and registered with `AdapterRegistry` without modifying `GatewayRouter` or Modules 1–6.
