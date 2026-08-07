# Model Registry Architectural Design Overview

## Overview

The **Model Registry** is the second independent prototype within the **Enterprise AI Model Routing Framework**. It functions as the central catalog service storing, validating, and serving structured metadata for foundation models across major AI providers (e.g., OpenAI, Anthropic, Google, Meta, DeepSeek, Cohere, Mistral, xAI, MiniMax, NVIDIA).

Downstream routing components—such as the Capability Matcher, Rule Engine, Policy Engine, and Ranking Engine—rely on the Model Registry to retrieve model capabilities, context window limits, supported modalities, supported use cases, and abstract routing hints (`cost_tier`, `latency_tier`) without needing provider-specific SDKs or external network calls.

---

## Architectural Scope & Boundaries

```text
                                 AI MODEL ROUTER FRAMEWORK
                                 
  ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
  │ Complexity Predictor │ ───► │    Model Registry    │ ───► │  Capability Matcher  │
  │    (Prototype 1)     │      │    (Prototype 2)     │      │     (Prototype 3)    │
  └──────────────────────┘      └──────────────────────┘      └──────────────────────┘
                                           │
                                  Metadata Query API
                                           │
                                 ┌───────────────────┐
                                 │   models.json     │
                                 └───────────────────┘
```

### In-Scope Responsibilities
- **Metadata Representation**: Dataclass-based representation (`ModelInfo`) encapsulating provider, family, model ID, display name, status, tags, context limits, use cases, modalities, and boolean capability flags.
- **Abstract Routing Tiers**: Abstract hints (`cost_tier`: `low`/`medium`/`high`/`premium`, `latency_tier`: `fast`/`medium`/`slow`) rather than live dollar figures or real-time latency measurements.
- **Metadata Validation**: Python standard library validation verifying required fields and tier values during JSON deserialization.
- **Extensible Query API**: Methods for provider lookup, family lookup, default model selection, keyword search (`search_models`), and flexible multi-criteria filtering (`filter_models(**criteria)`).

### Explicit Out-of-Scope Elements
- **No Provider SDKs / API Keys**: Zero integration with OpenAI, Anthropic, or Google Python SDKs.
- **No Network / HTTP Calls**: Operates strictly offline on local catalog metadata.
- **No Model Inference / Routing Scoring**: Model evaluation, scoring, capability matching, and execution belong to downstream prototypes.
- **No Live Pricing or Latency Metrics**: Relies entirely on static abstract routing hints.

---

## Data Model & Configuration Schema

### ModelInfo Schema Definition
Each model entry in `config/models.json` conforms to the `ModelInfo` dataclass:

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `provider` | `str` | Foundation model provider name | `"OpenAI"`, `"Anthropic"` |
| `family` | `str` | Model product family group | `"GPT"`, `"Claude"`, `"Gemini"` |
| `model_id` | `str` | Canonical unique identifier | `"gpt-4o"`, `"claude-3.5-sonnet"` |
| `display_name` | `str` | Human-readable title | `"GPT-4o"`, `"Claude 3.5 Sonnet"` |
| `description` | `str` | Concise overview of capabilities | `"Flagship multimodal model..."` |
| `status` | `str` | Lifecycle availability state | `"available"`, `"preview"`, `"deprecated"` |
| `is_default` | `bool` | Default choice for provider/family | `True` / `False` |
| `tags` | `List[str]` | Lightweight categorization tags | `["flagship", "coding", "vision"]` |
| `context_window` | `int` | Maximum context limit (tokens) | `128000`, `200000`, `2000000` |
| `max_output_tokens` | `int` | Maximum generation limit (tokens) | `4096`, `8192`, `16384` |
| `cost_tier` | `str` | Abstract routing cost estimate | `"low"`, `"medium"`, `"high"`, `"premium"` |
| `latency_tier` | `str` | Abstract routing latency estimate | `"fast"`, `"medium"`, `"slow"` |
| `supported_modalities` | `List[str]` | Supported content input/output types | `["text", "image", "audio", "video"]` |
| `supported_use_cases` | `List[str]` | Supported workload use cases | `["Programming", "System Design", ...]` |
| `supports_vision` | `bool` | Image/Vision input support flag | `True` / `False` |
| `supports_function_calling` | `bool` | Structured tool/function call flag | `True` / `False` |
| `supports_structured_output` | `bool` | JSON schema enforcement flag | `True` / `False` |

---

## Query API Architecture

The `ModelRegistry` class exposes a high-level Python API:

1. **`get_model(model_id)`**: $O(1)$ exact lookup by unique identifier.
2. **`get_default_model(provider, family)`**: Retrieves the designated default model for a given provider or model family.
3. **`get_models_by_provider(provider)` / `get_models_by_family(family)`**: Returns all models belonging to a specific provider or family.
4. **`get_models_supporting(modality)` / `get_models_for_use_case(use_case)`**: Returns models capable of handling specific content modalities or workload use cases.
5. **`search_models(query)`**: Performs case-insensitive substring search across model identifiers, display names, providers, families, and tags.
6. **`filter_models(**criteria)`**: Flexible multi-criteria query interface supporting keyword arguments (`min_context_window`, `required_modalities`, `required_use_cases`, `cost_tier`, `latency_tier`, boolean capability flags) designed to support future extension without signature changes.
