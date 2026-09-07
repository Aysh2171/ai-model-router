# AI Model Router Framework

The **AI Model Router** is a modular framework for evaluating, filtering, ranking, governing, and routing AI requests across a catalogue of foundation models and providers. It implements a decoupled 7-stage decision and execution pipeline, falling back dynamically to available providers if live executions fail or if API quotas are exhausted.

## Table of Contents
- [Setup & Startup (Windows)](#setup--startup-windows)
- [Architecture & Runtime Fallback](#architecture--runtime-fallback)
- [Provider & Model Documentation](#provider--model-documentation)
- [API Endpoints](#api-endpoints)
- [Router Authentication](#router-authentication)
- [Testing](#testing)
- [Manual Verification](#manual-verification)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Project Structure](#project-structure)

---

## Setup & Startup (Windows)

This guide assumes you are starting from a fresh Windows machine with Git and Python installed.

### 1. Clone Repository
```powershell
git clone <repository-url>
cd ai-model-router
```

### 2. Verify Python
The current development environment is targeting **Python 3.14.3**. Verify your Python version:
```powershell
python --version
```

### 3. Create Virtual Environment
Create an isolated Python environment:
```powershell
python -m venv .venv
```
Activate the virtual environment. If PowerShell blocks script execution, temporarily bypass the policy for the current session:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```
After activation, your command prompt should be prefixed with `(.venv)`.

### 4. Upgrade Pip
```powershell
python -m pip install --upgrade pip
```

### 5. Install Dependencies
Install all required packages from the pinned requirements file:
```powershell
pip install -r requirements.txt
```

### 6. Environment Configuration (.env)
The application requires environment variables for provider API keys and internal authentication. The system automatically loads a `.env` file from the root directory during startup (explicit environment variables take precedence).

Create a `.env` file in the repository root and configure the providers you wish to enable:
```env
# Client-facing API key for the Router
ROUTER_API_KEY=your_secure_router_secret

# Provider API Keys
GEMINI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
NVIDIA_API_KEY=
DEEPSEEK_API_KEY=
MISTRAL_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```
**Important Notes:**
- Do not commit your `.env` file to version control.
- You only need to provide keys for the providers you intend to use.
- The chatbot client requires `ROUTER_API_KEY` to authenticate with the router.

### 7. Free-Tier Provider Usage
This project supports multiple AI providers based on your configured credentials. 
- Provider availability depends on the keys you have configured in `.env`.
- **Free-tier API keys** are heavily subject to daily request limits, requests-per-minute limits, and token limits.
- If a provider rejects a request due to exhausted quotas or rate limits, the router will automatically fall back to the next available ranked provider.

### 8. Start the API
Start the application using the verified Uvicorn command:
```powershell
python -m uvicorn gateway_router.src.api:create_app --factory --host 127.0.0.1 --port 8000
```
- `gateway_router.src.api:create_app` specifies the module and application factory function.
- `--factory` tells Uvicorn to execute the function to build the FastAPI app instance.
- `--host 127.0.0.1 --port 8000` binds the server locally.

You will see "Application startup complete" when the server is ready.

### 9. Open the Chatbot
Open your web browser and navigate to:
**http://127.0.0.1:8000/chat**

This interactive UI allows you to submit prompts, inspect how the router selects models, and view execution latency/telemetry.

---

## Architecture & Runtime Fallback

The router employs a **7-Stage Pipeline** to process incoming requests:

1. **Complexity Predictor**: Uses ML to extract features and predict task complexity.
2. **Model Registry**: Queries the catalog of supported foundation models and their metadata.
3. **Capability Matcher**: Filters models by hard technical constraints (e.g., context window, required modalities).
4. **Rule Engine**: Evaluates organizational compliance and governance rules.
5. **Multi-Criteria Ranking**: Scores and orders candidates based on cost, latency, complexity suitability, and token headroom.
6. **Availability-Aware Policy**: Enforces budgets and operational quotas.
7. **Gateway Router / Provider Adapter**: Translates the request for the specific provider adapter and executes the live API call.

### Cross-Provider Runtime Fallback
If a selected provider experiences a runtime failure (e.g., connection timeout, rate limit, or transient 503 error), the pipeline dynamically falls back to alternative providers while preserving ranking order. 

**Example Flow:**
```text
Ranked candidates:
    Model A → Model B → Model C

Model A is selected
    ↓
Model A fails at runtime (e.g., Timeout)
    ↓
Model A is excluded for this specific request
    ↓
Model B is selected by the Policy Engine
    ↓
Model B succeeds
```
*Note: The failed candidate is excluded ephemerally for the current request. The underlying model registry is not permanently modified, and the GatewayRouter remains responsible for provider-level transient retries before giving up and triggering a cross-provider fallback.*

---

## Provider & Model Documentation

The Model Registry tracks numerous foundation models across major providers (OpenAI, Anthropic, Google, Meta, DeepSeek, Cohere, Mistral, xAI, NVIDIA, MiniMax, Groq). 

- **Registered Models**: The catalog contains metadata for many models.
- **Configured Providers**: Only providers with corresponding API keys in `.env` are considered "available" at runtime.
- Models belonging to unconfigured providers are safely skipped during the routing process. 
- The model catalogue intentionally retains unconfigured models to support future credentials without requiring codebase updates.

---

## API Endpoints

The system provides the following endpoints:

### GET `/health`
- **Purpose**: General service health check.
- **Authentication**: None.
- **Response**: JSON indicating health status and available providers.

### GET `/api/status`
- **Purpose**: Inspect provider configuration and availability status without exposing keys.
- **Authentication**: None.
- **Response**: JSON map of providers and their `configured` state.

### GET `/api/models`
- **Purpose**: List all models from the catalog and their availability status.
- **Authentication**: None.
- **Response**: JSON array of model metadata.

### POST `/api/chat`
- **Purpose**: Primary secure chatbot endpoint. Routes prompt through the full 7-stage pipeline.
- **Authentication**: Required (`X-Router-API-Key` header).
- **Request Format**: JSON (`message`, `task_category`, `expected_format`).
- **Response Format**: JSON containing the `response`, `selected_model`, `latency_ms`, and routing telemetry.

### POST `/v1/chat/completions`
- **Purpose**: Standard OpenAI-compatible chat completions endpoint.
- **Authentication**: None enforced strictly on this endpoint wrapper.
- **Request Format**: Standard OpenAI JSON (`messages`, `model`, `temperature`).

### POST `/v1/chat/completions/stream`
- **Purpose**: Server-Sent Events (SSE) streaming version of chat completions.

---

## Router Authentication

The router acts as a secure proxy to prevent external clients from accessing raw provider API keys.

```text
Client / Chatbot
      │
      │ (X-Router-API-Key)
      ▼
AI Model Router
      │
      │ (Provider-specific secrets e.g., GEMINI_API_KEY)
      ▼
Provider API
```

Clients calling `/api/chat` must supply the router's internal key using the `X-Router-API-Key` HTTP header. The router verifies this against its internal `.env` configuration before proceeding.

---

## Testing

To run the offline runtime fallback tests:
```powershell
pytest tests\test_runtime_fallback.py -v
```
This suite includes 7 localized mock-based tests that verify fallback mechanisms across transient errors, permanent errors, timeouts, and `400 Bad Request` scenarios. **These tests execute entirely offline and consume zero API quota.**

*(Note: The repository contains a suite of older legacy tests that currently fail to collect due to pre-existing import/PYTHONPATH structural issues. These legacy failures do not affect the new runtime fallback logic or the live operation of the API.)*

---

## Manual Verification

Because live provider testing consumes free-tier quota, manual verification should be kept minimal:

1. Ensure `.env` contains at least one valid provider key (e.g., `GEMINI_API_KEY`).
2. Start the API.
3. Open `http://127.0.0.1:8000/chat` in your browser.
4. Enter the prompt: `Say hello in one short sentence.`
5. Verify that a provider/model is selected and a valid response is returned to the UI.

---

## Troubleshooting

- **`python` not found**: Ensure Python 3.14+ is installed and added to your Windows PATH.
- **PowerShell blocking activation**: If `.\.venv\Scripts\Activate.ps1` fails with an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.
- **Dependencies failing to install**: Ensure you have activated the virtual environment and upgraded pip (`python -m pip install -U pip`).
- **Missing environment variables**: Check that your `.env` file is in the root directory (same folder as `main.py` and `requirements.txt`) and correctly named `.env` (not `.env.txt`).
- **Invalid / expired API keys**: If the router constantly falls back or fails, verify your keys are active on the provider's dashboard and that you have available quota.
- **Provider timeouts**: Free-tier APIs often experience high latency. The router will automatically retry or fallback if a request times out.
- **Port 8000 already in use**: If Uvicorn fails to bind, change the port using `--port 8080`.
- **Chatbot loads but requests fail (401 Unauthorized)**: Ensure the `ROUTER_API_KEY` defined in `.env` matches the expected client configuration, or set it to `development-session` for local testing.

---

## Security

- **Never expose provider API keys** to the frontend or commit them to version control.
- Provider keys belong exclusively in the `.env` file (which is ignored by Git).
- Use `ROUTER_API_KEY` as the sole client-facing credential to authenticate trusted clients with the router.

---

## Project Structure

```text
ai-model-router/
├── .env                       # (Ignored) Local configuration & secrets
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies (pip install -r)
├── tests/                     # Unit and integration tests
│   └── test_runtime_fallback.py # Offline fallback verification tests
│
├── gateway_router/            # Stage 7: Execution layer & adapters
│   └── src/
│       ├── api.py             # FastAPI entry point & endpoints
│       ├── orchestrator.py    # PipelineRouter & cross-provider fallback
│       └── adapters/          # Specific API integrations (Google, OpenAI, etc.)
│
├── complexity_predictor/      # Stage 1: Request analysis
├── model_registry/            # Stage 2: Catalog of available models
├── capability_matcher/        # Stage 3: Technical constraint filtering
├── rule_engine/               # Stage 4: Governance compliance rules
├── ranking_engine/            # Stage 5: Multi-criteria scoring
└── policy_engine/             # Stage 6: Availability and budget governance
```
