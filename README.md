# Enterprise AI Model Router

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License: TBD](https://img.shields.io/badge/license-TBD-lightgrey.svg)
![Status: Active Development](https://img.shields.io/badge/status-active--development-green.svg)
![Core Modules: Complete](https://img.shields.io/badge/core%20modules-complete-brightgreen.svg)
![Tests: Passing](https://img.shields.io/badge/tests-passing-success.svg)

The Enterprise AI Model Router is a research-oriented architectural framework designed to evaluate, filter, and route complex enterprise AI requests across multiple foundation models and provider APIs. Rather than relying on a monolithic routing system, this repository explores a modular, component-driven architecture in which distinct routing responsibilities are implemented as independent, composable prototypes.

---

## Table of Contents

- [Key Features](#key-features)
- [Motivation](#motivation)
- [Project Goals](#project-goals)
- [Overall Architecture](#overall-architecture)
- [Repository Structure](#repository-structure)
- [Implemented Prototypes](#implemented-prototypes)
- [Current Status](#current-status)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Running the Prototypes](#running-the-prototypes)
- [Design Principles](#design-principles)
- [Roadmap](#roadmap)
- [License](#license)

---

## Key Features

- **Modular Prototype Architecture**: Cleanly decouples routing concerns into independent, self-contained submodules.
- **Independent, Composable Components**: Each prototype evolves autonomously without system-wide coupling.
- **Offline Model Metadata Registry**: Stores rich catalog definitions for 17 foundation models across 10 major AI providers without external API calls.
- **Machine Learning Complexity Estimation**: Employs a Random Forest classifier to predict request complexity (`Low`, `Medium`, `High`) based on 35+ handcrafted features.
- **Deterministic Capability Filtering**: Evaluates technical hard constraints objectively across a 5-stage early-exit pipeline.
- **Organizational Rule Engine**: Enforces business policy rules, data residency limits, vendor blacklists, security compliance, and cost caps.
- **Provider-Independent Design**: Abstracts away provider-specific SDKs in favor of normalized data representations.
- **Comprehensive Documentation**: Includes architectural design specifications, feature engineering guides, and benchmark metrics.
- **Automated Test Suite**: Features deterministic unit, integration, end-to-end, and edge-case tests built using Python's standard library `unittest`.

---

## Motivation

As enterprise AI adoption matures, organizations increasingly rely on multi-model strategies using diverse models from OpenAI, Anthropic, Google, Meta, Mistral, DeepSeek, Cohere, and open-weight ecosystems. Monolithic single-model strategies lead to significant inefficiency:

- **Cost Overruns**: Routing trivial text queries to high-tier frontier models (e.g., GPT-4o or Claude 3.5 Sonnet) incurs unnecessary financial costs.
- **Latency Bottlenecks**: Routing time-sensitive tasks to deep reasoning models introduces latency overhead.
- **Capability Violations**: Dispatching multimodal requests or long-context payloads to models lacking vision support or sufficient context windows causes runtime failures.
- **Vendor Lock-in**: Hardcoding provider-specific SDKs impairs adaptability as model capabilities rapidly evolve.

Separating the routing process into independent, modular prototypes enables enterprise teams to evolve complexity classifiers, metadata catalogs, feasibility filters, policy engines, and cost rankers autonomously without system-wide coupling.

---

## Project Goals

- **Exploring Enterprise AI Routing Architectures**: Study modular, component-driven design patterns for multi-LLM routing.
- **Building Independent Routing Components**: Develop self-contained prototypes for request analysis, catalog querying, constraint filtering, and organizational policy enforcement.
- **Pre-Selection Feasibility & Governance Evaluation**: Determine technical feasibility and business policy compliance objectively before applying candidate ranking.
- **Maintaining Provider Independence**: Abstract away vendor-specific SDKs using normalized request and capability data structures.
- **Extensible Router Foundation**: Provide a clean, documented baseline for future policy, rule, and ranking engines.

---

## Overall Architecture

The AI Model Router pipeline processes incoming requests through sequential, decoupled stages:

```text
               Incoming AI Request Payload
                            │
                            ▼
         ┌─────────────────────────────────────┐
         │ Complexity Predictor (Prototype 1) │
         └─────────────────────────────────────┘
                            │
                    Complexity Profile
                            │
                            ▼
         ┌─────────────────────────────────────┐
         │    Model Registry   (Prototype 2) │
         └─────────────────────────────────────┘
                            │
                      Model Catalog
                            │
                            ▼
         ┌─────────────────────────────────────┐
         │  Capability Matcher (Prototype 3) │
         └─────────────────────────────────────┘
                            │
                   CapabilityMatchResult
                            │
                            ▼
         ┌─────────────────────────────────────┐
         │     Rule Engine     (Prototype 4)   │
         └─────────────────────────────────────┘
                            │
                  RuleEvaluationResult
                            │
                            ▼
         ┌─────────────────────────────────────┐
         │    Ranking Engine   (Planned)       │
         └─────────────────────────────────────┘
                            │
                            ▼
                 Selected Target Model
```

Each stage operates strictly within its single responsibility boundary and can be replaced, updated, or extended independently.

---

## Repository Structure

```text
ai-model-router/
├── complexity_predictor/      # Prototype 1: Supervised ML request complexity classifier
├── model_registry/            # Prototype 2: Offline foundation model catalog service
├── capability_matcher/        # Prototype 3: Deterministic technical feasibility filter
├── rule_engine/               # Prototype 4: Organizational policy and governance engine
├── docs/                      # Architectural design & system specification documents
└── README.md                  # Root repository overview documentation
```

Each prototype can be executed independently and maintains its own documentation, scripts, and implementation details. This modular organization enables isolated experimentation without impacting other components.

### Directory Overview

- **`complexity_predictor/`**: Contains the Random Forest classification pipeline, 35+ handcrafted feature extractors, dataset generators, model evaluation scripts, interactive CLI, and comprehensive test suite.
- **`model_registry/`**: Contains the offline catalog metadata schema (`models.json`), data validation models (`ModelInfo`), and multi-criteria querying service (`ModelRegistry`).
- **`capability_matcher/`**: Contains the 5-stage early-exit deterministic feasibility engine (`CapabilityMatcher`), constraint extractor (`RequirementExtractor`), and candidate result containers (`CapabilityMatchResult`).
- **`rule_engine/`**: Contains the organizational governance engine (`RuleEngine`), policy context models (`PolicyContext`), and modular rules (`AllowedProvidersRule`, `DataResidencyRule`, `SecurityComplianceRule`, `MaxCostTierRule`).
- **`docs/`**: Contains detailed architectural specifications, technology stack rationale, and system design documents.

---

## Implemented Prototypes

### Prototype 1 — Complexity Predictor

The Complexity Predictor estimates the operational and computational complexity of incoming AI requests before downstream model allocation.

- **Request Analysis**: Converts raw request payloads into standardized structured request domain objects.
- **Feature Extraction**: Computes 35+ handcrafted features across text length, token bounds, scale indicators (e.g., page/paper counts), domain terminology, and technology keywords.
- **Supervised ML Classification**: Trains a Random Forest classifier mapping feature vectors to `Low`, `Medium`, or `High` complexity tiers.
- **Output Artifacts**: Returns a structured JSON Complexity Profile (`complexity`, `complexity_score`, `confidence`).
- **Included Assets**: Dedicated architecture docs (`docs/design_overview.md`, `docs/feature_engineering.md`, `docs/benchmarks.md`), interactive CLI script (`scripts/predict.py --demo`), and automated unit/integration test suite (`tests/`).

### Prototype 2 — Model Registry

The Model Registry serves as the centralized metadata repository for available foundation models across commercial and open-weight providers.

- **Offline Metadata Catalog**: Stores structured catalog definitions for representative models across major providers (OpenAI, Anthropic, Google, Meta, Mistral, DeepSeek, Cohere, xAI, MiniMax, NVIDIA).
- **Rich Model Attributes**: Captures context windows, max output limits, cost tiers, latency tiers, supported modalities, boolean capabilities, and tags.
- **Programmatic Query APIs**: Exposes flexible filtering by provider, family, modalities, use cases, capabilities, and keyword search.
- **Provider Independence**: Operates locally without external API calls, SDK dependencies, or network requirements.

### Prototype 3 — Capability Matcher

The Capability Matcher bridges the Complexity Predictor and Model Registry by determining which models are technically capable of fulfilling a request.

- **Constraint Extraction**: Derives technical requirements (`min_context_window`, `required_modalities`, `required_use_cases`, boolean capability flags) from normalized requests and complexity profiles.
- **5-Stage Deterministic Pipeline**: Filters models sequentially by Status $\rightarrow$ Modality $\rightarrow$ Capability Flags $\rightarrow$ Context Capacity $\rightarrow$ Use Case Alignment.
- **Auditable Candidate Sets**: Returns clean `CandidateModel` objects (with surplus token headroom metrics) and `ExcludedModel` objects (with explicit rejection telemetry).
- **Strict Feasibility Scope**: Evaluates hard technical feasibility objectively without subjective cost scoring or model ranking.

### Prototype 4 — Rule Engine

The Rule Engine evaluates technically feasible candidate models against organizational, compliance, security, and governance policies.

- **Policy Context Construction**: Accepts tenant tier metadata, allowed/disallowed providers, data residency regions, security compliance tags, and max cost tier caps.
- **Modular Policy Rules**: Evaluates `AllowedProvidersRule`, `DisallowedProvidersRule`, `DataResidencyRule`, `SecurityComplianceRule`, `TenantAccessTierRule`, and `MaxCostTierRule`.
- **Full Violation Telemetry**: Collects all rule violations per candidate model without stopping at the first failure.
- **Auditable Candidate Filtering**: Outputs allowed candidate sets (`allowed_candidates`) and detailed policy exclusion traces (`policy_excluded_candidates`).

---

## Current Status

| Component | Status | Description |
| :--- | :--- | :--- |
| **Complexity Predictor** | **Complete** | Request complexity estimation |
| **Model Registry** | **Complete** | Offline metadata catalog |
| **Capability Matcher** | **Complete** | Technical feasibility filtering |
| **Rule Engine** | **Complete** | Enterprise policy enforcement |
| **Ranking Engine** | *Planned* | Candidate scoring and optimization |

---

## Technology Stack

The repository uses Python and standard data science libraries:

- **Core Language**: Python 3.10+
- **Standard Library**: `dataclasses`, `pathlib`, `json`, `typing`, `unittest`, `subprocess`, `uuid`
- **Machine Learning**: `scikit-learn`
- **Data Processing**: `pandas`, `numpy`
- **Serialization**: `joblib`
- **Version Control**: Git

---

## Getting Started

Clone the repository:

```bash
git clone https://github.com/Aysh2171/ai-model-router.git
cd ai-model-router
```

Each prototype is self-contained and can be explored independently. Refer to the respective subdirectory for implementation details and documentation.

---

## Running the Prototypes

Each prototype is self-contained. Navigate into the corresponding directory before executing its demonstration script.

### Prototype 1 — Complexity Predictor
```bash
# Navigate to prototype folder
cd complexity_predictor

# Run interactive demonstration script
python scripts/predict.py --demo

# Run comprehensive automated test suite
python -m unittest discover -s tests
```

### Prototype 2 — Model Registry
```bash
# Navigate to prototype folder
cd model_registry

# Run interactive demonstration script (catalog queries & filters)
python scripts/demo.py
```

### Prototype 3 — Capability Matcher
```bash
# Navigate to prototype folder
cd capability_matcher

# Run interactive demonstration script (6 feasibility scenarios)
python scripts/demo.py
```

---

## Design Principles

- **Single Responsibility Principle (SRP)**: Each component focuses strictly on a single routing concern.
- **Modular Component Isolation**: Prototypes maintain independent source trees, documentation, and requirements.
- **Provider Independence**: Abstracts away provider-specific SDKs in favor of normalized data representations.
- **Deterministic Hard Constraint Filtering**: Separates objective technical feasibility from subjective preference ranking.
- **Offline & Lightweight Execution**: Runs locally without network dependencies or cloud credentials.
- **Extensible API Contracts**: Designed for effortless downstream integration into active gateway services.

---

## Roadmap

```text
Current Implementation

Complexity Predictor
        │
        ▼
  Model Registry
        │
        ▼
Capability Matcher

Next Phases

   Rule Engine
        │
        ▼
  Policy Engine
        │
        ▼
 Ranking Engine
        │
        ▼
 Gateway Router
```

Future components planned for development include:

1. **Rule Engine**: Hard organizational constraint filtering (data residency, security compliance, tenant tier limits).
2. **Policy Engine**: Dynamic enterprise budget controls, token usage quotas, and fallback governance.
3. **Ranking Engine**: Utility scoring balancing cost optimization, latency target SLAs, and model quality metrics.
4. **Gateway Router**: Production-grade async HTTP entry point tying all prototypes into a unified routing engine.
5. **Evaluation Framework**: Automated benchmark suite evaluating routing efficiency against live enterprise workloads.

---

## License

This project is currently unlicensed. An open-source license will be added prior to the first public release.
