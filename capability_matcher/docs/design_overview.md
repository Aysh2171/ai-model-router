# Capability Matcher Architectural Design Overview

## Overview

The **Capability Matcher** is the third independent prototype within the **Enterprise AI Model Routing Framework**. It serves as the architectural bridge between the **Complexity Predictor** (Prototype 1) and the **Model Registry** (Prototype 2), outputting an eligible candidate model set for downstream components (Rule Engine, Policy Engine, Ranking Engine).

Its primary responsibility is **deterministic technical feasibility filtering**: determining which registered foundation models **CAN** satisfy an incoming request. It does not perform model ranking, cost optimization, latency scoring, or model execution.

---

## Architectural Boundaries & Workflow

```text
                               AI MODEL ROUTER PIPELINE
                               
  ┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
  │ Complexity Predictor │     │    Model Registry    │     │  Capability Matcher  │
  │    (Prototype 1)     │     │    (Prototype 2)     │     │    (Prototype 3)     │
  └──────────────────────┘     └──────────────────────┘     └──────────────────────┘
             │                            │                            │
     Complexity Profile             Model Catalog              Feasibility Filter
             │                            │                            │
             └───────────────────┬────────┘                            │
                                 ▼                                     │
                    ┌──────────────────────────┐                       │
                    │   Requirement Extractor  │                       │
                    └──────────────────────────┘                       │
                                 │                                     │
                         MatchRequirements                             │
                                 │                                     │
                                 ▼                                     │
                    ┌──────────────────────────┐                       │
                    │ Capability Matcher Engine│ ◄─────────────────────┘
                    └──────────────────────────┘
                                 │
                       CapabilityMatchResult
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │ Candidate Models List  │ ──► (Passed to Ranking Engine)
                     └────────────────────────┘
```

---

## 5-Stage Deterministic Filtering Pipeline

The `CapabilityMatcher` processes registered foundation models through a 5-stage early-exit evaluation sequence:

1. **Status & Lifecycle Check**: Verifies model status (`available`, `preview`, `deprecated`) against `allow_preview` and `allow_deprecated` configuration options.
2. **Modality Subset Check**: Verifies `required_modalities.issubset(model.supported_modalities)`.
3. **Boolean Capability Flags Check**: Verifies mandatory boolean capability flags (`supports_vision`, `supports_function_calling`, `supports_json`, `supports_code`, `supports_tools`, `supports_structured_output`).
4. **Context & Output Token Bounds**: Verifies `model.context_window >= min_context_window` and `model.max_output_tokens >= min_max_output_tokens`.
5. **Use Case Set Subset Check**: Verifies `required_use_cases.issubset(model.supported_use_cases)`.

---

## Data Models Specification

- **`MatchRequirements`**: Dataclass representing technical matching constraints derived from a normalized request (`required_modalities: Set[str]`, `min_context_window: int`, `min_max_output_tokens: int`, `required_use_cases: Set[str]`, `required_capabilities: Dict[str, bool]`).
- **`CandidateModel`**: Wraps `model_id`, `provider`, `family`, `model_info`, `context_headroom`, `matched_constraint_count`, and `matched_constraints`.
- **`ExcludedModel`**: Captures `model_id`, `provider`, and detailed `exclusion_reasons` for telemetry auditing.
- **`CapabilityMatchResult`**: Parent container storing `request_id`, `is_satisfiable`, `complexity_profile`, `requirements`, `eligible_candidates`, and `excluded_models`.
