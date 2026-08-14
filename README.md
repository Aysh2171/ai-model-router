# AI Model Router Framework

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Architecture: 8 Modules](https://img.shields.io/badge/modules-8%20completed-brightgreen.svg)
![Tests: 186/186 Passing](https://img.shields.io/badge/tests-186%2F186%20passing-success.svg)
![Adversarial: 50/50](https://img.shields.io/badge/adversarial-50%2F50%20passed-success.svg)
![Execution: Local Simulation](https://img.shields.io/badge/execution-local%20mock%20simulation-orange.svg)

The **AI Model Router** is a modular, research-oriented framework for evaluating, filtering, ranking, governing, and routing AI requests across a catalogue of foundation models and providers. Rather than relying on a monolithic routing heuristic, the system implements a decoupled, 8-module decision and execution pipeline where each stage has a distinct, auditable responsibility.

```text
                                Incoming AI Request
                                        │
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ Module 1 — Complexity Predictor                     │
             │ (Supervised ML Classifier & Feature Extraction)     │
             └─────────────────────────────────────────────────────┘
                                        │ Complexity Profile
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ Module 2 — Model Registry                           │
             │ (17-Model Metadata Catalog across 10 AI Providers)  │
             └─────────────────────────────────────────────────────┘
                                        │ Model Catalog
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ Module 3 — Capability Matcher                       │
             │ (5-Stage Deterministic Technical Feasibility Filter)│
             └─────────────────────────────────────────────────────┘
                                        │ Feasible Candidates
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ Module 4 — Rule Engine                              │
             │ (Organizational Governance, Compliance & Residency) │
             └─────────────────────────────────────────────────────┘
                                        │ Allowed Candidates
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ Module 5 — Ranking Engine                           │
             │ (Multi-Criteria Preference Scoring & Ordering)      │
             └─────────────────────────────────────────────────────┘
                                        │ Ranked Candidates
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ Module 6 — Policy Engine                            │
             │ (Runtime State, Quotas, Budgets & Ordered Fallback) │
             └─────────────────────────────────────────────────────┘
                                        │ Policy Decision
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ Module 7 — Gateway Router                           │
             │ (Execution Layer, Provider Adapters & Retries)      │
             └─────────────────────────────────────────────────────┘
                                        │ Gateway Response
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ Module 8 — Feedback Pipeline                        │
             │ (Telemetry Ingestion, User Ratings & Analytics)     │
             └─────────────────────────────────────────────────────┘
                                        │
                                        ▼
                         Auditable Routing Telemetry
```

---

## Table of Contents

- [Project Status](#project-status)
- [Important: Current Prototype Behaviour](#important-current-prototype-behaviour)
- [Repository Structure](#repository-structure)
- [Naming Convention & Terminology](#naming-convention--terminology)
- [Prerequisites & Environment](#prerequisites--environment)
- [Primary Execution — Interactive Console (`main.py`)](#primary-execution--interactive-console-mainpy)
- [Interactive Console Menu Breakdown](#interactive-console-menu-breakdown)
  - [Option 1: Route a New Request](#option-1-route-a-new-request)
  - [Option 2: Route Request with File Attachment](#option-2-route-request-with-file-attachment)
  - [Option 3: Routing Diagnostics (Deep Module Inspection)](#option-3-routing-diagnostics-deep-module-inspection)
  - [Option 4: Fault Injection & Retry Demonstration](#option-4-fault-injection--retry-demonstration)
  - [Option 5: View Model Catalogue](#option-5-view-model-catalogue)
  - [Option 6: Run Complete System Demonstration](#option-6-run-complete-system-demonstration)
  - [Option 7: Exit Console](#option-7-exit-console)
- [Module-Specific Demonstrations](#module-specific-demonstrations)
- [End-to-End Request Lifecycle](#end-to-end-request-lifecycle)
- [Real Execution Example (Diagnostic Trace)](#real-execution-example-diagnostic-trace)
- [Verified Interactive Execution](#verified-interactive-execution)
- [Automated Testing & Verification](#automated-testing--verification)
- [Supervisor Demonstration Quick Start](#supervisor-demonstration-quick-start)
- [Architectural Limitations](#architectural-limitations)

---

## Project Status

The implementation phase of the AI Model Router framework across all 8 modules and the root CLI console is **100% complete**. The repository has undergone comprehensive unit testing, integration testing, multi-stage adversarial auditing, state-isolation verification, and interactive CLI validation.

### Verification Summary

- **Total Unit Test Count**: **186 / 186 Passing (100%)**
- **Adversarial Benchmark**: **50 / 50 Scenarios Passing (100%)**
- **Request-Scoped State Isolation**: **0 state leakage across 100 repeated runs and 20-thread concurrency**
- **Malformed Input Resilience**: **100% controlled `ValueError` handling for corrupted inputs; 100% safe normalization for optional fields**
- **Task Category Taxonomy**: **Canonical use cases and aliases cleanly resolved; unsupported categories strictly yield `NO_CANDIDATE`**
- **Zero Commercial Spend**: **$0.00 (Pure local deterministic simulation mode)**

---

## Important: Current Prototype Behaviour

To maintain complete technical accuracy when operating or demonstrating this repository, note the exact distinction between routing logic and provider execution:

| Subsystem | Execution State | Description |
| :--- | :--- | :--- |
| **Routing and Decision Pipeline (M1–M6)** | **Live Local Implementation** | Complexity prediction, registry querying, capability matching, rule filtering, multi-criteria ranking, and policy governance run live local algorithms. |
| **Provider Execution (M7)** | **MOCKED (LOCAL)** | Foundation model provider API calls are handled locally by `MockProviderAdapter` with deterministic responses, realistic simulated latency, and token metrics. |
| **Telemetry & Feedback (M8)** | **REAL LOCAL** | Telemetry ingestion, event persistence in SQLAlchemy / SQLite, feedback correlation, and analytics calculation execute live. |
| **Commercial API Calls** | **NONE ($0.00)** | Zero calls are dispatched to external cloud APIs (OpenAI, Anthropic, Google, DeepSeek, etc.). Zero API keys are required. |

---

## Repository Structure

```text
ai-model-router/
├── main.py                    # Primary human-facing CLI console and demonstration entry point
├── README.md                  # Authoritative system documentation
│
├── complexity_predictor/      # Module 1: Supervised ML request complexity classifier (Random Forest)
│   ├── src/                   # Feature extraction, request analyzer, model wrapper
│   ├── models/                # Serialized model artifacts (random_forest_model.joblib)
│   ├── scripts/               # Training (train.py) and CLI prediction (predict.py)
│   └── tests/                 # 35 unit tests
│
├── model_registry/            # Module 2: Foundation model catalog service (17 models / 10 providers)
│   ├── src/                   # ModelInfo, ModelRegistry service, catalog loader
│   ├── config/                # Offline models.json catalog configuration
│   ├── scripts/               # Standalone demo (demo.py)
│   └── tests/                 # 18 unit tests
│
├── capability_matcher/        # Module 3: 5-stage deterministic technical feasibility filter
│   ├── src/                   # RequirementExtractor, CapabilityMatcher, candidate models
│   ├── scripts/               # Standalone demo (demo.py)
│   └── tests/                 # 18 unit tests
│
├── rule_engine/               # Module 4: Organizational governance, compliance & residency rules
│   ├── src/                   # RuleEngine, PolicyContext, modular compliance rules
│   ├── scripts/               # Standalone demo (demo.py)
│   └── tests/                 # 10 unit tests
│
├── ranking_engine/            # Module 5: Multi-criteria preference scoring and candidate ranking
│   ├── src/                   # RankingEngine, RankingConfig, ComponentScorer, tie-breaking
│   ├── scripts/               # Standalone demo (demo.py)
│   └── tests/                 # 14 unit tests
│
├── policy_engine/             # Module 6: Runtime operational governance, budgets & ordered fallback
│   ├── src/                   # PolicyEngine, UsageState, Budget/Quota/RateLimit policies
│   ├── scripts/               # Standalone demo (demo.py)
│   └── tests/                 # 20 unit tests
│
├── gateway_router/            # Module 7: Execution layer, provider adapters & pipeline orchestrator
│   ├── src/                   # GatewayRouter, PipelineRouter, MockProviderAdapter, retries
│   ├── scripts/               # Standalone demo (demo.py)
│   └── tests/                 # 30 unit tests
│
├── feedback_pipeline/         # Module 8: Telemetry ingestion, user ratings & historical analytics
│   ├── src/                   # FeedbackService, FeedbackAnalytics, SQLAlchemy repository
│   ├── scripts/               # End-to-end multi-scenario demonstration (demo.py)
│   └── tests/                 # 26 unit tests
│
├── tests/                     # Root test package & CLI test suite
│   ├── __init__.py
│   └── test_main.py           # 15 unit and functional tests for main.py
│
└── docs/                      # Architectural design specifications & technical papers
```

---

## Naming Convention & Terminology

The framework consistently adheres to the following nomenclature throughout code, dataclasses, and documentation:

### Module Designations
- **M1 = Complexity Predictor**: Analyzes request text, token bounds, and structural indicators to output a `ComplexityProfile` (`Low`, `Medium`, `High`).
- **M2 = Model Registry**: Central offline repository supplying standardized `ModelInfo` schemas for 17 foundation models.
- **M3 = Capability Matcher**: Validates hard technical constraints (modalities, context window, capabilities, use cases) producing `CapabilityMatchResult`.
- **M4 = Rule Engine**: Enforces organizational policy constraints (allowed providers, data residency, tenant tiers, cost caps) producing `RuleEvaluationResult`.
- **M5 = Ranking Engine**: Calculates multi-criteria weighted utility scores producing an ordered `RankingResult`.
- **M6 = Policy Engine**: Enforces runtime state (budgets, quotas, rate limits) and manages candidate fallback producing a `PolicyDecision`.
- **M7 = Gateway Router**: Dispatches requests through registered `BaseProviderAdapter` instances producing a `GatewayResponse`.
- **M8 = Feedback Pipeline**: Ingests telemetry, attaches user ratings, and queries historical performance analytics via `FeedbackService`.

### Core Class Contracts
- `PipelineRouter`: Top-level orchestrator in Module 7 chaining M1 through M7 and recording telemetry into M8.
- `MockProviderAdapter`: Thread-safe mock provider implementation supporting deterministic latency, token generation, and request-scoped fault injection.
- `GatewayRequest` / `GatewayResponse`: Standardized input and output payloads of the execution layer.
- `CandidateModel` / `RankedModel`: Intermediate model representations carrying technical headroom metrics and ranking scores.
- `PolicyDecision`: Runtime governance outcome carrying decision states (`APPROVED`, `APPROVED_WITH_FALLBACK`, `REJECTED`, `NO_CANDIDATE`).
- `ExecutionStatus`: Final dispatch status (`SUCCESS`, `FAILED`, `TIMEOUT`, `NO_CANDIDATE`, `REJECTED`).
- `ExecutionMode`: Operational transport mode (`mock` for local simulation).

---

## Prerequisites & Environment

The framework runs locally without external network dependencies:

- **Python Version**: Python 3.10+ (Verified in the current development environment on Python 3.14.3).
- **Core Dependencies**:
  ```text
  scikit-learn >= 1.2.0
  pandas >= 2.0.0
  numpy >= 1.24.0
  joblib >= 1.3.0
  sqlalchemy >= 2.0.0
  pydantic >= 2.0.0
  fastapi >= 0.100.0
  uvicorn >= 0.22.0
  httpx >= 0.24.0
  ```
- **Database Target**: SQLite in-memory (`sqlite:///:memory:`) for local prototyping / tests; PostgreSQL-ready ORM schema for production deployment.
- **API Keys & Cloud Spend**: **Zero API keys required. Zero cloud spending.** All foundation models execute through deterministic local adapters.

---

## Primary Execution — Interactive Console (`main.py`)

The primary human-facing entry point for running and demonstrating the complete system is `main.py` located at the root of the repository.

### Launch Command

```powershell
cd /d E:\Myridius\ai-model-router
python main.py
```

### Main Console Interface

```text
==============================================================================
                      AI MODEL ROUTER FRAMEWORK                       
                      Interactive System Console                      
==============================================================================
  Execution Environment : Local Prototype
  Provider Execution    : MockProviderAdapter (Deterministic Local Simulation)
  External Calls        : ZERO Commercial API Calls | ZERO Cloud Spending
==============================================================================

MAIN MENU:
  1. Route a New Request
  2. Route Request with File Attachment
  3. Routing Diagnostics (Deep Step-by-Step Module Trace)
  4. Fault Injection & Retry Demonstration (Gateway Resilience)
  5. View Model Catalogue (17 Registered Foundation Models)
  6. Run Complete System Demonstration (5 Predefined Scenarios)
  7. Exit Console
------------------------------------------------------------------------------
Select an option (1-7) [1]:
```

---

## Interactive Console Menu Breakdown

### Option 1: Route a New Request
Interactively creates and routes a request through the full 8-module pipeline.

1. **Request ID**: Defaults to an auto-generated identifier (e.g. `REQ-8F12A0C4`).
2. **Prompt Entry**: Enter any custom prompt, or press Enter without typing to use the pre-formatted example:
   ```text
   Enter your prompt.
   Press Enter without typing anything to use the example below.

   Example:
     Explain the difference between synchronous and asynchronous execution in Python.

   > Explain how binary search works and give a simple Python example.
   ```
3. **Task Category Selection**: Choose from canonical use cases or alias mappings:
   - `1. General Question Answering`
   - `2. Programming`
   - `3. Reasoning`
   - `4. Analysis & Review (Alias -> Reasoning)`
   - `5. Data Processing (Alias -> Data Extraction)`
   - `6. Document Processing (Alias -> Document Analysis)`
   - `7. System Architecture (Alias -> Software Architecture)`
   - `8. Multimodal (Alias -> Vision Analysis)`
   - `9. Mathematical Reasoning`
   - `10. Code Review`
   - `11. Vision Analysis`
   - `12. Enter custom category...` (e.g. unsupported categories like `QuantumTeleportation`)
4. **Expected Output Format**: `Text`, `Code`, `JSON`, or custom format.
5. **Conversation Context**: Number of historical turns.

**Sample Output Display**:
```text
==============================================================================
                              ROUTING RESULT                              
==============================================================================
  Status            : SUCCESS
  Decision State    : APPROVED
  Selected Model    : claude-3.5-haiku
  Provider          : Anthropic
  Execution Mode    : MOCK (Local Simulation)
  Retry Count       : 0
  Fallback Used     : False
  Latency           : 15.00 ms
  Token Usage       : Prompt=5, Completion=23, Total=28
------------------------------------------------------------------------------
 MODEL RESPONSE CONTENT
------------------------------------------------------------------------------
  [MOCK EXECUTION] Simulated response from provider 'Anthropic' for model 'claude-3.5-haiku'. Prompt summary: 'Explain how binary search works and give a simple Python exa...'. Execution completed in local simulation mode.
==============================================================================
```

---

### Option 2: Route Request with File Attachment
Demonstrates attachment-aware routing using locally extracted file metadata.

- Prompts user for a local file path (e.g. `docs/architecture_text.txt`).
- Validates file existence locally and rejects directory paths.
- Extracts file size (MB) and file extension/type.
- Passes attachment metadata to the router (`type`, `file_type`, `size_mb`, `filename`).
- **Transparency Note**: Clearly declares that only locally extracted attachment metadata is supplied to the router in local simulation mode; file contents are not uploaded or transmitted to external servers.

---

### Option 3: Routing Diagnostics (Deep Module Inspection)
Exposes the internal decision state across all 8 modules sequentially for any prompt.

- **Module 1 (Complexity Predictor)**: Predicted Complexity (`Low`, `Medium`, `High`), Score (0–100), and Confidence.
- **Module 2 (Model Registry)**: Total catalog count (17 models) and registered provider list.
- **Module 3 (Capability Matcher)**: Extracted requirements (modalities, use cases, min context window), satisfiability flag, eligible candidates list, and exclusion telemetry.
- **Module 4 (Rule Engine)**: Allowed candidates count vs. policy-excluded candidates.
- **Module 5 (Ranking Engine)**: Ordered ranking table with scores and rank positions (`#1`, `#2`, `#3`...).
- **Module 6 (Policy Engine)**: Policy decision state (`APPROVED`), selected model, and fallback attempts.
- **Module 7 (Gateway Router)**: Simulated latency, retry count, token consumption, and status.
- **Module 8 (Feedback Pipeline)**: Event persistence confirmation and correlation Event ID.

---

### Option 4: Fault Injection & Retry Demonstration
Demonstrates the resilience and state-isolation guarantees of `GatewayRouter` and `MockProviderAdapter`:

1. **Transient Failure $\rightarrow$ Retry $\rightarrow$ Success (`fail_mode="transient_then_success"`)**:
   - Attempt 1: Injects simulated transient glitch.
   - Gateway automatically catches failure, increments retry counter, and re-executes.
   - Attempt 2: Succeeds cleanly. Result shows `Status: SUCCESS, Retry Count: 1`.
2. **Permanent Failure $\rightarrow$ Immediate Abort (`fail_mode="permanent"`)**:
   - Attempt 1: Injects simulated non-retryable 400 Bad Request.
   - Gateway aborts immediately without wasting retries. Result shows `Status: FAILED, Retry Count: 0`.
3. **Timeout Glitch Simulation (`fail_mode="timeout"`)**:
   - Gateway retries up to configured limit before returning `Status: TIMEOUT`.
4. **Clean Execution**: Standard failure-free execution.
5. **Request-Scoped State Isolation Verification**:
   - Executes Request A (`REQ-ISOLATION-A`) with transient fault (Attempt 1 fail, Attempt 2 success).
   - Executes Request B (`REQ-ISOLATION-B`) on the **same adapter instance** with the same configuration.
   - Proves Request B independently experiences Attempt 1 failure and Attempt 2 retry, confirming zero state leakage between requests.

---

### Option 5: View Model Catalogue
Interactively inspects the 17 foundation models stored in Module 2's offline catalog:

- **Tabular Catalog View**:
  ```text
  Model ID               Provider     Cost Tier  Latency Tier Context    Status  
  ------------------------------------------------------------------------------
  gpt-4o                 OpenAI       high       medium       128k       available
  gpt-4o-mini            OpenAI       low        fast         128k       available
  o1-preview             OpenAI       premium    slow         128k       preview 
  claude-3.5-sonnet      Anthropic    high       fast         200k       available
  claude-3.5-haiku       Anthropic    low        fast         200k       available
  gemini-1.5-pro         Google       high       medium       2000k      available
  gemini-1.5-flash       Google       low        fast         1000k      available
  llama-3.1-405b         Meta         premium    slow         128k       available
  llama-3.1-70b          Meta         medium     medium       128k       available
  deepseek-v3            DeepSeek     low        fast         128k       available
  deepseek-r1            DeepSeek     medium     medium       128k       available
  command-r-plus         Cohere       high       medium       128k       available
  mistral-large-2407     Mistral      high       fast         128k       available
  codestral-2405         Mistral      medium     fast         32k        available
  grok-2                 xAI          high       medium       128k       available
  minimax-text-01        MiniMax      medium     medium       4000k      available
  nemotron-4-340b        NVIDIA       high       medium       128k       available
  ```
- **Catalogue Sub-Actions**: Filter by Provider, Cost Tier, Latency Tier, Keyword Search, or view complete metadata for any individual model ID.

---

### Option 6: Run Complete System Demonstration
Invokes `feedback_pipeline/scripts/demo.py`, executing 5 predefined operational scenarios:

1. **Normal Pipeline Dispatch**: Routes a predefined programming request through M1–M7, records the resulting model selection and execution telemetry, and ingests the event into the Module 8 repository.
2. **Policy-Governed Budget Fallback**: A simulated budget cap causes the top-ranked high-cost candidate to be rejected, after which the Policy Engine selects the next eligible candidate and records an `APPROVED_WITH_FALLBACK` decision.
3. **Policy Rejection**: A request with an exhausted tenant request quota is rejected by the Policy Engine with an auditable `REQUEST_QUOTA_EXCEEDED` reason.
4. **User Feedback Attachment**: Demonstrates attaching 1–5 star quality ratings and textual feedback to previously recorded routing events.
5. **Historical Feedback Analytics**: Generates aggregate system-health, routing/policy distribution, qualitative satisfaction, and per-model historical performance metrics.

---

### Option 7: Exit Console
Terminates the interactive session cleanly.

---

## Module-Specific Demonstrations

Each module can also be inspected and demonstrated independently:

| Module | Direct Execution Command | Focus Area |
| :--- | :--- | :--- |
| **Complete System (M1–M8)** | `python main.py` | Interactive terminal console |
| **Feedback Pipeline (M8)** | `python feedback_pipeline/scripts/demo.py` | 5-scenario end-to-end pipeline & analytics |
| **Gateway Router (M7)** | `python gateway_router/scripts/demo.py` | Multi-scenario adapter dispatch & retries |
| **Policy Engine (M6)** | `python policy_engine/scripts/demo.py` | Budget/quota enforcement & candidate fallback |
| **Ranking Engine (M5)** | `python ranking_engine/scripts/demo.py` | Weighted utility scoring & tie-breaking |
| **Rule Engine (M4)** | `python rule_engine/scripts/demo.py` | Organizational policy & compliance rules |
| **Capability Matcher (M3)** | `python capability_matcher/scripts/demo.py` | 5-stage deterministic feasibility filter |
| **Model Registry (M2)** | `python model_registry/scripts/demo.py` | Offline catalog querying & filtering |
| **Complexity Predictor (M1)** | `python complexity_predictor/scripts/predict.py --demo` | Random Forest ML complexity inference |

---

## End-to-End Request Lifecycle

When a request enters the router, it transitions through 9 distinct operational steps:

```text
1. Request Ingestion
   └── Raw request received by PipelineRouter (request_id, prompt, metadata, attachments).

2. Module 1: Complexity Prediction
   └── RequestAnalyzer normalizes payload; 38 handcrafted features extracted; Random Forest predicts complexity.

3. Module 2: Model Registry Query
   └── ModelRegistry supplies 17 normalized ModelInfo specifications.

4. Module 3: Capability Matching
   └── Hard technical constraints extracted; 5-stage filter yields eligible CandidateModel list.

5. Module 4: Organizational Rule Evaluation
   └── PolicyContext applied (data residency, allowed providers, cost caps); non-compliant models excluded.

6. Module 5: Multi-Criteria Ranking
   └── ComponentScorer computes weighted utility across cost, latency, complexity suitability, and token headroom.

7. Module 6: Runtime Policy Governance
   └── UsageState evaluated; if top candidate violates budget/quota, router executes ordered fallback (A -> B -> C).

8. Module 7: Gateway Execution
   └── MockProviderAdapter resolves model adapter, executes simulated call, and manages retries if transient errors occur.

9. Module 8: Telemetry Ingestion & Analytics
   └── GatewayResponse ingested into SQLAlchemy repository; telemetry correlated for historical feedback analytics.
```

---

## Real Execution Example (Diagnostic Trace)

Below is an authentic diagnostic trace generated by the system for a complex distributed systems reasoning prompt:

```text
==============================================================================
                    INTERMEDIATE PIPELINE TRACE TRACE                     
==============================================================================

[ MODULE 1 — COMPLEXITY PREDICTOR ]
  Predicted Complexity  : High
  Complexity Score      : 74.00 / 100
  Prediction Confidence : 0.71

[ MODULE 2 — MODEL REGISTRY ]
  Total Catalog Models  : 17
  Registered Providers  : Anthropic, Cohere, DeepSeek, Google, Meta, MiniMax, Mistral, NVIDIA, OpenAI, xAI

[ MODULE 3 — CAPABILITY MATCHER ]
  Required Modalities   : ['text']
  Required Use Cases    : ['Programming', 'Reasoning']
  Min Context Window    : 16,384 tokens
  Satisfiable           : True
  Eligible Candidates   : 5 / 17
  Eligible Model IDs    : gpt-4o, claude-3.5-sonnet, llama-3.1-405b, deepseek-v3, mistral-large-2407

[ MODULE 4 — RULE ENGINE ]
  Allowed Candidates    : 4 / 5
  Policy Excluded Count : 1

[ MODULE 5 — RANKING ENGINE ]
  Ranked Candidates     : 4
    Rank #1: deepseek-v3        (Score: 0.9216 | Provider: DeepSeek)
    Rank #2: claude-3.5-sonnet  (Score: 0.8050 | Provider: Anthropic)
    Rank #3: mistral-large-2407 (Score: 0.7266 | Provider: Mistral)
    Rank #4: gpt-4o             (Score: 0.6266 | Provider: OpenAI)

[ MODULE 6 — POLICY ENGINE ]
  Policy Decision State : APPROVED
  Selected Model        : deepseek-v3
  Fallback Attempts     : 0

[ MODULE 7 — GATEWAY ROUTER ]
  Execution Status      : SUCCESS
  Execution Mode        : MOCK (Local Simulation)
  Simulated Latency     : 15.00 ms
  Retry Count           : 0

[ MODULE 8 — FEEDBACK PIPELINE ]
  Telemetry Recorded    : SUCCESS
  Event Record ID       : e64604ba-1a18-417e-b851-3dec8c6bfbb7
  Database Storage      : SQLite In-Memory Repository
==============================================================================
```

*(Note: Execution performed under local mock simulation mode; no external API calls were made to DeepSeek).*

---

## Verified Interactive Execution

Beyond automated unit and integration testing, the root interactive console (`main.py`) was manually exercised across the primary routing, file-attachment, diagnostics, fault-injection, model-catalogue, and complete-demonstration paths. The following records summarise the verified user-facing execution behaviour. All provider execution remained in deterministic local mock mode, with zero commercial API calls.

| Console Option | Verified Scenario | Result |
| :--- | :--- | :---: |
| **1 — Route a New Request** | Complex system-architecture request and machine-learning reasoning request routed through the pipeline | **PASS** |
| **2 — Route Request with File Attachment** | Local `pbl_report.docx` attachment detected and its metadata passed into the routing pipeline | **PASS** |
| **3 — Routing Diagnostics** | Full M1–M8 intermediate pipeline trace displayed for a complex distributed-systems prompt | **PASS** |
| **4 — Fault Injection & Retry Demonstration** | Transient retry, permanent failure, timeout exhaustion, and request-scoped isolation scenarios | **PASS** |
| **5 — View Model Catalogue** | Provider, cost-tier, latency-tier filtering and individual model metadata inspection | **PASS** |
| **6 — Run Complete System Demonstration** | Normal routing, budget fallback, policy rejection, feedback attachment, and historical analytics | **PASS** |
| **7 — Exit Console** | Interactive console exit path | **PASS** |

### Verified Option 1 — Representative Routing

Two representative requests were manually executed through Option 1:

1. **Distributed Database Architecture Request**: A comprehensive system design prompt covering sharding, replication, consistency models, distributed transactions, caching strategies, failure recovery, load balancing, SQL vs NoSQL tradeoffs, network partitions, duplicate requests, stale reads, and concurrent updates.
   - **Task Category**: `System Architecture` (Alias $\rightarrow$ `Software Architecture`)
   - **Expected Output**: `Text`
   - **Observed Selected Model**: `claude-3.5-sonnet`
   - **Provider**: `Anthropic`
   - **Status**: `SUCCESS`
   - **Decision State**: `APPROVED`
   - **Execution Mode**: `MOCK (Local Simulation)`

2. **Imbalanced Machine Learning Pipeline Request**: A technical machine-learning prompt covering preprocessing, feature selection, stratified cross-validation, class imbalance mitigation, hyperparameter optimisation, decision threshold tuning, evaluation metrics (Precision, Recall, F1, ROC-AUC, PR-AUC), overfitting prevention, and data leakage controls.
   - **Task Category**: `Reasoning`
   - **Expected Output**: `Code`
   - **Observed Selected Model**: `deepseek-v3`
   - **Provider**: `DeepSeek`
   - **Status**: `SUCCESS`
   - **Decision State**: `APPROVED`
   - **Execution Mode**: `MOCK (Local Simulation)`

*(Note: Model selections reflect the observed dynamic outputs of the current multi-criteria ranking and policy configuration for these specific request parameters; they are not hard-coded static outcomes).*

### Verified Option 2 — File Attachment Routing

A request containing a local file attachment was submitted to test metadata-aware routing:

- **Prompt**: Requested comprehensive architectural analysis of the attached document.
- **Task Category**: `Document Processing` (Alias $\rightarrow$ `Document Analysis`)
- **Local File**: `pbl_report.docx`
- **File Type Detected**: `docx`
- **File Size Reported**: `1.48 MB`
- **Attachment Count**: `1`
- **Observed Selected Model**: `minimax-text-01`
- **Provider**: `MiniMax`
- **Status**: `SUCCESS`
- **Decision State**: `APPROVED`
- **Execution Mode**: `MOCK (Local Simulation)`

*(Note: The router extracted and supplied local attachment metadata during execution; document contents were not uploaded to external servers).*

### Verified Option 4 — Fault Injection and Retry Behaviour

All four fault simulation scenarios were executed and verified:

#### Transient Failure → Retry → Success
- **Fault Mode**: `transient_then_success` (`fail_count_before_success=1`)
- **Expected Behaviour**: Attempt 1 fails with simulated transient error $\rightarrow$ Gateway router catches failure and retries $\rightarrow$ Attempt 2 succeeds.
- **Observed Status**: `SUCCESS`
- **Observed Retry Count**: `1`

#### Permanent Failure → Immediate Abort
- **Fault Mode**: `permanent`
- **Expected Behaviour**: Simulated non-retryable 400 Bad Request error immediately terminates execution without wasting retries.
- **Observed Status**: `FAILED`
- **Observed Retry Count**: `0`
- **Error Classification**: Non-retryable permanent execution failure.

#### Timeout → Retry Exhaustion
- **Fault Mode**: `timeout`
- **Expected Behaviour**: Gateway router retries until the configured retry limit is exhausted before aborting.
- **Observed Status**: `TIMEOUT`
- **Observed Retry Count**: `2`
- **Error State**: Execution retries exhausted.

#### Request-Scoped State Isolation
- **Request A**: `REQ-ISOLATION-A` executed with `transient_then_success` on the shared adapter instance $\rightarrow$ `SUCCESS` with `1` retry.
- **Request B**: `REQ-ISOLATION-B` executed with `transient_then_success` on the **same adapter instance** $\rightarrow$ `SUCCESS` with `1` retry.
- **Final Verdict**: `PASS (Zero State Leakage)`. Request B independently experienced its own Attempt 1 failure and Attempt 2 retry, proving it did not inherit completed attempt state from Request A.

### Verified Option 5 — Model Catalogue

The 17-model catalog was inspected and filtered across multiple dimensions:

- **Total Registered Models**: `17` foundation models across 10 providers.
- **Provider Filtering**:
  - `OpenAI` $\rightarrow$ 3 models (`gpt-4o`, `gpt-4o-mini`, `o1-preview`)
  - `Anthropic` $\rightarrow$ 2 models (`claude-3.5-sonnet`, `claude-3.5-haiku`)
- **Cost-Tier Filtering**:
  - `low` $\rightarrow$ 4 models (`gpt-4o-mini`, `claude-3.5-haiku`, `gemini-1.5-flash`, `deepseek-v3`)
  - `medium` $\rightarrow$ Available as a catalogue filter
  - `high` $\rightarrow$ 7 models (`gpt-4o`, `claude-3.5-sonnet`, `gemini-1.5-pro`, `command-r-plus`, `mistral-large-2407`, `grok-2`, `nemotron-4-340b`)
  - `premium` $\rightarrow$ 2 models (`o1-preview`, `llama-3.1-405b`)
- **Latency-Tier Filtering**:
  - `fast` $\rightarrow$ 7 models (`gpt-4o-mini`, `claude-3.5-sonnet`, `claude-3.5-haiku`, `gemini-1.5-flash`, `deepseek-v3`, `mistral-large-2407`, `codestral-2405`)
  - `slow` $\rightarrow$ 2 models (`o1-preview`, `llama-3.1-405b`)
- **Individual Model Inspection (`deepseek-v3`)**:
  - **Provider**: `DeepSeek`
  - **Family**: `DeepSeek`
  - **Status**: `available`
  - **Cost Tier**: `low`
  - **Latency Tier**: `fast`
  - **Context Window**: `128,000 tokens`
  - **Max Output Tokens**: `8,192 tokens`
  - **Supported Modalities**: `text`
  - **Supported Use Cases**: `Programming, Code Review, Debugging, Reasoning, Mathematical Reasoning, Data Extraction`
  - **Capabilities**: `Vision=False, Code=True, FunctionCalling=True`

### Verified Option 6 — Complete System Demonstration

The automated 5-scenario system demonstration was executed through Option 6 with the following observed outputs:

#### Scenario 1 — Normal Pipeline Dispatch
- **Telemetry Ingestion**: Event successfully ingested into Module 8 repository.
- **Request ID**: `REQ-DEMO-M8-001`
- **Selected Model**: `minimax-text-01`
- **Provider**: `MiniMax`
- **Complexity Tier**: `Medium` (Score: `40`)
- **Execution Status**: `SUCCESS`
- **Execution Mode**: `mock`
- **Latency**: `15.00 ms`
- **Total Tokens**: `39`

#### Scenario 2 — Policy-Governed Fallback
- **Context**: Simulated budget cap of `2.0` units rejects the top-ranked high-cost candidate.
- **Action**: Policy Engine selects Rank #2 model.
- **Selected Model**: `claude-3.5-haiku`
- **Provider**: `Anthropic`
- **Decision State**: `APPROVED_WITH_FALLBACK`
- **Fallback Used**: `True`

#### Scenario 3 — Policy Rejection
- **Context**: Tenant daily request quota exhausted.
- **Execution Status**: `REJECTED`
- **Audit Reason**: `REQUEST_QUOTA_EXCEEDED`

#### Scenario 4 — Feedback Attachment
- Attached `5/5` star rating with category `accurate` and comment to normal-routing event (`8557f102...`).
- Attached `4/5` star rating with category `accurate` to fallback event (`4ef24cd4...`).
- Persisted event trace query confirmed feedback correlation.

#### Scenario 5 — Historical Analytics Scorecard
- **Total Requests Handled**: `3`
- **Successful Requests**: `2`
- **Failed / Blocked Requests**: `1`
- **Overall Success Rate**: `66.7%`
- **Average Routing Latency**: `10.00 ms`
- **Total Tokens Processed**: `77`
- **Fallback Trigger Rate**: `33.3%` (1 event)
- **Total Feedback Captured**: `2`
- **Average User Rating**: `4.50 / 5.0`
- **Satisfaction Rate (`>= 4`)**: `100.0%`
- **Per-Model Historical Breakdown**:
  - `claude-3.5-haiku` (Anthropic): 1 request, 100% success, 15.0ms avg latency, 4.00/5.0 avg rating
  - `minimax-text-01` (MiniMax): 1 request, 100% success, 15.0ms avg latency, 5.00/5.0 avg rating

---

## Automated Testing & Verification

The root CLI test suite is verified via `python -m unittest discover -s tests -t .` (**15 / 15 tests passing**). The repository-wide test suite was separately verified across all 9 test suites with **186 / 186 tests passing (100%)**:

### Complete Test Matrix

| Subsystem / Test Suite | Discovery Command | Tests | Status |
| :--- | :--- | :---: | :---: |
| **Module 1 (Complexity Predictor)** | `python -m unittest discover -s complexity_predictor/tests -t complexity_predictor` | 35 | **PASS** |
| **Module 2 (Model Registry)** | `python -m unittest discover -s model_registry/tests -t model_registry` | 18 | **PASS** |
| **Module 3 (Capability Matcher)** | `python -m unittest discover -s capability_matcher/tests -t capability_matcher` | 18 | **PASS** |
| **Module 4 (Rule Engine)** | `python -m unittest discover -s rule_engine/tests -t rule_engine` | 10 | **PASS** |
| **Module 5 (Ranking Engine)** | `python -m unittest discover -s ranking_engine/tests -t ranking_engine` | 14 | **PASS** |
| **Module 6 (Policy Engine)** | `python -m unittest discover -s policy_engine/tests -t policy_engine` | 20 | **PASS** |
| **Module 7 (Gateway Router)** | `python -m unittest discover -s gateway_router/tests -t gateway_router` | 30 | **PASS** |
| **Module 8 (Feedback Pipeline)** | `python -m unittest discover -s feedback_pipeline/tests -t feedback_pipeline` | 26 | **PASS** |
| **Root CLI (Interactive Console)** | `python -m unittest discover -s tests -t .` | 15 | **PASS** |
| **Total Test Count** | **All 9 test suites** | **186** | **186 / 186 PASS (100%)** |

---

## Supervisor Demonstration Quick Start

When presenting this project to a supervisor or evaluator, follow this concise walkthrough:

1. **Launch Console**:
   ```powershell
   python main.py
   ```
2. **Demonstrate Standard Routing (Option 1)**:
   - Select `1. Route a New Request`.
   - Submit a complex system-architecture or machine-learning prompt.
   - Show how the router dynamically evaluates complexity, calculates multi-criteria utility, governs runtime policies, and dispatches to the selected model (e.g. `claude-3.5-sonnet` or `deepseek-v3`) with full token and latency telemetry.
3. **Demonstrate File-Attachment-Aware Routing (Option 2)**:
   - Select `2. Route Request with File Attachment`.
   - Provide a local document path (e.g. `pbl_report.docx`).
   - Highlight that the system automatically inspects local file metadata (filename, size, format, and extension) and incorporates that attachment metadata into the routing decision without uploading file contents to third-party cloud servers.
4. **Demonstrate Step-by-Step Diagnostics (Option 3)**:
   - Select `3. Routing Diagnostics`.
   - Enter a complex distributed-systems prompt.
   - Walk the evaluator through all 8 intermediate decision stages: M1 complexity score, M2 catalog inspection, M3 technical constraint matching, M4 policy exclusions, M5 weighted multi-criteria ranking, M6 runtime budget governance, M7 gateway execution, and M8 SQLite telemetry persistence.
5. **Demonstrate Fault Resilience & State Isolation (Option 4)**:
   - Select `4. Fault Injection & Retry Demonstration`.
   - Run scenario `1. Transient Failure -> Retry -> Success` (demonstrates automatic Attempt 1 failure recovery).
   - Run scenario `5. Request-Scoped State Isolation Test` (proves that independent sequential requests on the same adapter instance maintain isolated attempt counters with zero state leakage).
6. **Demonstrate 5-Scenario System Suite & Analytics (Option 6)**:
   - Select `6. Run Complete System Demonstration`.
   - Show automated policy budget fallback (`APPROVED_WITH_FALLBACK`), quota rejection (`REQUEST_QUOTA_EXCEEDED`), user feedback attachment (1–5 star ratings and comments), and the aggregated historical feedback analytics dashboard.

---

## Architectural Limitations

1. **Mock Provider Execution**: The execution layer operates in deterministic local simulation mode using `MockProviderAdapter`. Live production calls to commercial APIs (OpenAI, Anthropic, Google, DeepSeek) are not dispatched in this prototype.
2. **Static ML Model**: Module 8 calculates historical telemetry analytics but does not automatically trigger continuous online retraining of Module 1's Random Forest classifier.
3. **In-Process Communication**: Module-to-module communication occurs via in-process Python method calls rather than an asynchronous distributed message broker (e.g. Apache Kafka or RabbitMQ).
4. **Default Persistence**: The default demonstration environment uses an in-memory SQLite database (`sqlite:///:memory:`). Persistent storage can be enabled by configuring a persistent database URL.
