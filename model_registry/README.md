# AI Model Registry Prototype

The Model Registry is a lightweight, provider-independent metadata catalog service designed as the second independent prototype within the Enterprise AI Model Routing Framework. In multi-model AI routing architectures, downstream routing components—such as the Capability Matcher, Rule Engine, and Ranking Engine—require clean, structured metadata describing the capabilities, context limits, modalities, and routing tiers of foundation models. To meet this requirement, the Model Registry maintains an offline catalog of representative foundation models from major AI providers and exposes an extensible programmatic Python query API.

---

## Motivation

Modern enterprise AI platforms integrate models across multiple commercial and open-weights providers (e.g., OpenAI, Anthropic, Google, Meta, DeepSeek, Cohere, Mistral, xAI, MiniMax, NVIDIA). Hardcoding model capabilities or scattering model definitions across routing logic creates tight coupling and maintenance overhead. The Model Registry decouples model metadata from routing algorithms, enabling downstream components to query capabilities dynamically through a unified interface.

---

## Features

- **Structured Metadata Representation**: Uses a clean `ModelInfo` dataclass defining stable model identifiers, product families, display names, context window limits, output limits, and lifecycle statuses.
- **Abstract Routing Hints**: Categorizes models into abstract routing tiers (`cost_tier`: `low`/`medium`/`high`/`premium`, `latency_tier`: `fast`/`medium`/`slow`) rather than brittle live pricing or latency measurements.
- **Comprehensive Use Case & Modality Support**: Maps models against a broad set of routing-oriented use cases (`Programming`, `System Design`, `Document Analysis`, `Reasoning`, `Translation`, etc.) and strict content modalities (`text`, `image`, `audio`, `video`).
- **Granular Capability Flags**: Tracks boolean flags for advanced features including vision, audio, code, function calling, tool use, streaming, JSON mode, reasoning, long context, and structured output.
- **Flexible Model Tagging**: Supports lightweight tagging (`["flagship", "coding", "vision", "open-weights", "rag", "long-context"]`) for fast categorization.
- **Extensible Query & Search API**: Provides methods for exact model lookups, default model resolution, provider/family queries, keyword searching (`search_models`), and multi-criteria filtering (`filter_models`).
- **Zero Third-Party Dependencies**: Built entirely using Python Standard Library (`dataclasses`, `json`, `pathlib`, `typing`), ensuring maximum portability and zero installation overhead.

---

## Architecture

The Model Registry serves as the metadata foundation for downstream routing components:

$$\text{Model Catalog JSON} \longrightarrow \text{ModelRegistry Engine} \longrightarrow \text{ModelInfo Data Objects} \longrightarrow \text{Downstream Routing Components}$$

### How It Works

1. **Catalog Loading**: The `ModelRegistry` reads `config/models.json` on initialization and deserializes model definitions into `ModelInfo` instances.
2. **Schema Validation**: Lightweight Python validation verifies required fields (`model_id`, `provider`, `family`, `context_window`) and status/tier enum constraints.
3. **In-Memory Catalog**: Stores models in an indexed dictionary for $O(1)$ lookup by `model_id`.
4. **Programmatic Query Execution**: Exposes specialized lookup methods and an extensible keyword filter interface (`filter_models(**criteria)`) consumed by routing engines.

---

## Project Structure

```text
model_registry/
│
├── config/
│   └── models.json             # Factual catalog for representative foundation models across major providers
│
├── src/                        # Core Python source modules
│   ├── __init__.py             # Package initializer exposing ModelInfo and ModelRegistry
│   ├── model.py                # ModelInfo dataclass and dictionary validation
│   └── model_registry.py       # ModelRegistry catalog management, search, and query API
│
├── scripts/                    # Command-line entry points
│   └── demo.py                 # Demonstration script querying registry metadata
│
├── docs/                       # Architectural design documentation
│   └── design_overview.md      # Detailed system specification
│
├── requirements.txt            # Python dependencies (Standard Library only)
└── README.md                   # Project documentation
```

---

## Tech Stack

- **Python**: 3.10+
- **Standard Library Modules**: `dataclasses`, `json`, `pathlib`, `typing`

---

## Setup

### Prerequisites
- Python 3.10 or higher

### Installation
Clone the repository and inspect dependencies:
```bash
# Standard library only — no pip packages required
pip install -r requirements.txt
```

---

## Usage and Query API

### Running the Demonstration Script
To execute the interactive demonstration script illustrating registry lookups, searches, and multi-criteria filtering:

```bash
python scripts/demo.py
```

### Programmatic Python Usage

```python
from src.model_registry import ModelRegistry

# Initialize registry (loads config/models.json automatically)
registry = ModelRegistry()

# 1. Lookup a specific model
claude = registry.get_model("claude-3.5-sonnet")
print(claude.display_name, claude.context_window, claude.cost_tier)

# 2. Get default model for a provider or family
default_gpt = registry.get_default_model(provider="OpenAI")
default_claude = registry.get_default_model(family="Claude")

# 3. Search models by keyword
reasoning_models = registry.search_models("reasoning")

# 4. Filter models using flexible criteria
fast_vision_models = registry.filter_models(
    min_context_window=128000,
    supports_vision=True,
    latency_tier="fast"
)
```

---

## Supported Foundation Models Overview

The registry includes representative foundation models from major AI providers:

- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `o1-preview`
- **Anthropic**: `claude-3.5-sonnet`, `claude-3.5-haiku`
- **Google**: `gemini-1.5-pro`, `gemini-1.5-flash`
- **Meta**: `llama-3.1-405b`, `llama-3.1-70b`
- **DeepSeek**: `deepseek-v3`, `deepseek-r1`
- **Cohere**: `command-r-plus`
- **Mistral**: `mistral-large-2407`, `codestral-2405`
- **xAI**: `grok-2`
- **MiniMax**: `minimax-text-01`
- **NVIDIA**: `nemotron-4-340b`

---

## Current Scope

- **Metadata Catalog Service**: Provides structured metadata loading, validation, and querying.
- **Offline Operation**: Operates entirely offline without external API keys, SDKs, or network dependencies.
- **Abstract Routing Hints**: Uses abstract qualitative routing tiers (`cost_tier`, `latency_tier`) rather than live pricing APIs or real-time latency measurements.
- **Decoupled Architecture**: Designed to serve downstream router prototypes (Capability Matcher, Rule Engine, Ranking Engine).

---

## Future Work

- **Evaluation on Real Enterprise Logs**: Refine model tag definitions and use-case mappings against production workloads.
- **Richer Handcrafted Metadata**: Expand metadata fields to capture specialized tokenization characteristics and fine-tuning capabilities.
- **Improved Workload Heuristics**: Connect registry query methods directly into downstream capability matching logic.
- **Routing Gateway Integration**: Integrate the registry as the catalog backend for a live model routing engine.
