# Module 7 — Gateway Router: Design & Architecture Overview

> **Module Name:** `gateway_router`  
> **Position in Architecture:** Module 7 (Execution Layer)  
> **Primary Predecessor:** Module 6 — Policy Engine (`policy_engine/`)  
> **Primary Successor:** Module 8 — Feedback Pipeline (`feedback_pipeline/` - Planned)  
> **Execution Mode:** 100% Local Prototype Simulation (`ExecutionMode.MOCK`)  

---

## 1. Executive Summary & Architectural Motivation

The **Gateway Router** bridges the gap between decision intelligence and execution. Prior to Module 7, the AI Model Router framework determined which foundation model should process an incoming prompt through five specialized stages:
1. **Module 1 (Complexity Predictor):** Analyzes cognitive difficulty (`Low`, `Medium`, `High`).
2. **Module 3 (Capability Matcher):** Validates technical feasibility against the 17-model catalog in Module 2.
3. **Module 4 (Rule Engine):** Enforces organizational compliance, data residency, and tenant access tiers.
4. **Module 5 (Ranking Engine):** Ranks eligible candidates via multi-factor weighted preference scoring.
5. **Module 6 (Policy Engine):** Evaluates runtime budgets, quotas, rate limits, and bounded fallback.

The output of Module 6 is a `PolicyDecision`. However, a policy decision is an authorization artifact, not an executed response. The Gateway Router consumes this decision, resolves the provider adapter, executes the prompt in a controlled local execution environment, handles transient retry loops, and delivers standardized execution results to client callers.

---

## 2. Core Architectural Principles

```
                                [ PolicyDecision ]
                          (From Module 6 Policy Engine)
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │        GatewayRouter          │
                       │ • Inspects Decision State     │
                       │ • Blocks REJECTED requests    │
                       │ • Extracts Selected Model     │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │        AdapterRegistry        │
                       │ • Resolves Provider Name      │
                       │ • Matches Registered Adapter  │
                       │ • Returns ADAPTER_NOT_FOUND   │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │     BaseProviderAdapter       │
                       │ (MockProviderAdapter in M7)   │
                       │ • Deterministic execution     │
                       │ • Fault injection hooks       │
                       │ • Token usage estimation      │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  Bounded Retry Controller     │
                       │ • Retries Transient Errors    │
                       │ • Aborts on Permanent Errors  │
                       │ • Keeps Selected Model Fixed  │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                               [ GatewayResponse ]
```

### 2.1 Principle of Explicit Local/Mock Execution
In accordance with zero-spending prototype requirements:
- No real commercial API calls are made to OpenAI, Anthropic, Google, Meta, or Mistral.
- No third-party provider SDKs are installed or required.
- All response payloads, token metrics, and execution times are explicitly marked with `execution_mode: "mock"`.
- Response text explicitly states: `"[MOCK EXECUTION] Simulated response from provider '<provider>' for model '<model_id>'..."`.

### 2.2 Strict Separation of Governance vs. Execution Retries
A key architectural boundary exists between **Policy Fallback** and **Execution Retry**:
- **Policy Fallback (Module 6 Ownership):** When a model fails organizational governance (e.g. `BUDGET_EXCEEDED`), Module 6 cascades to the next ranked candidate. Module 7 **never** switches models or re-ranks.
- **Execution Retry (Module 7 Ownership):** When the selected model encounters a transient network glitch or timeout during execution, Module 7 retries the **same model** up to `max_retries`.

### 2.3 Explicit Adapter Resolution
If a provider adapter is not registered, the Gateway returns `ExecutionStatus.ADAPTER_NOT_FOUND` rather than silently substituting a generic adapter.

---

## 3. Data Model Specification

### 3.1 GatewayRequest
Encapsulates the execution input:
- `request_id` (`str`): Unique correlation identifier.
- `prompt` (`str`): User input text.
- `policy_decision` (`Optional[PolicyDecision]`): Authorized routing artifact from Module 6.
- `model_id` (`Optional[str]`): Direct model identifier if bypassing upstream pipeline.
- `provider` (`Optional[str]`): Direct provider identifier.
- `stream` (`bool`): Toggle for streaming chunk generation.
- `temperature` (`float`): Generation sampling parameter (default: 0.7).
- `max_tokens` (`Optional[int]`): Generation token ceiling.
- `simulation_options` (`Optional[Dict[str, Any]]`): Controlled testing hooks (`fail_mode`, `fail_count_before_success`, `custom_response`, `simulated_latency_ms`).

### 3.2 GatewayResponse
Unified execution result:
- `request_id` (`str`): Correlation ID.
- `status` (`ExecutionStatus`): `SUCCESS`, `FAILED`, `TIMEOUT`, `RETRY_EXHAUSTED`, `REJECTED`, `NO_CANDIDATE`, `ADAPTER_NOT_FOUND`.
- `decision_state` (`Optional[str]`): Value from PolicyDecision (`APPROVED`, `APPROVED_WITH_FALLBACK`, `REJECTED`, `NO_CANDIDATE`).
- `model_id` (`Optional[str]`): Executed model ID.
- `provider` (`Optional[str]`): Executing provider.
- `content` (`Optional[str]`): Generated response text.
- `execution_mode` (`str`): Constant `"mock"`.
- `latency_ms` (`float`): Execution duration in milliseconds.
- `retry_count` (`int`): Number of transient retries performed.
- `fallback_used` (`bool`): Passthrough from `PolicyDecision.fallback_used`.
- `error_message` (`Optional[str]`): Error or policy rejection audit string.
- `usage` (`Dict[str, int]`): Estimated token counts (`prompt_tokens`, `completion_tokens`, `total_tokens`).

### 3.3 StreamChunk
Incremental token chunk:
- `request_id` (`str`), `chunk_index` (`int`), `content` (`str`), `model_id` (`str`), `provider` (`str`), `is_final` (`bool`), `execution_mode` (`str = "mock"`).

---

## 4. Error Handling and Failure Classification

Execution errors are strictly categorized:
1. **`TransientExecutionError` / `TimeoutExecutionError` (Retryable):**
   Simulates transient network dropped connections, HTTP 503 service unavailable, or provider timeouts. The Gateway retries the same model up to `max_retries` (default: 2). If retries fail, returns `RETRY_EXHAUSTED` or `TIMEOUT`.
2. **`PermanentExecutionError` (Non-Retryable):**
   Simulates client format errors, 400 Bad Request, or invalid token payloads. The Gateway aborts immediately (`retry_count = 0`, `status = FAILED`).
3. **`AdapterNotFoundError`:**
   Raised when no adapter is registered for the requested provider. Returns `ADAPTER_NOT_FOUND`.
4. **Policy Rejection:**
   When `policy_decision.decision == REJECTED`, adapter execution is completely bypassed and returns `REJECTED`.

---

## 5. End-to-End Orchestration (`PipelineRouter`)

To simplify client integration and multi-stage testing, `PipelineRouter` composes all seven modules:
```python
pipeline = PipelineRouter()
response = pipeline.route_and_execute(raw_request, runtime_policy_context=ctx)
```
The orchestrator executes in sequence:
$$\text{Raw Request} \xrightarrow{\text{M1}} \text{Complexity} \xrightarrow{\text{M3 (M2)}} \text{Feasibility} \xrightarrow{\text{M4}} \text{Rules} \xrightarrow{\text{M5}} \text{Ranking} \xrightarrow{\text{M6}} \text{Policy} \xrightarrow{\text{M7}} \text{GatewayResponse}$$

---

## 6. Future Real Provider Integration Strategy

When commercial API access is introduced in production:
1. Create concrete subclasses of `BaseProviderAdapter` (e.g. `OpenAIProviderAdapter`, `AnthropicProviderAdapter`) wrapping `httpx.AsyncClient` or official SDKs.
2. Store API keys securely in environment variables or cloud secret managers.
3. Register the real adapters in `AdapterRegistry`:
   ```python
   registry.register(OpenAIProviderAdapter(api_key=os.environ["OPENAI_API_KEY"]))
   ```
4. `GatewayRouter` will automatically dispatch live requests without changing any routing, policy, or ranking logic.
