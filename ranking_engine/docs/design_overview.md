# Ranking Engine Architectural Design Overview

## Overview

The **Ranking Engine** is the fifth independent prototype within the **Enterprise AI Model Router Framework**. It acts as the preference-based scoring and ordering stage following hard policy governance (**Module 4 — Rule Engine**).

While Module 4 answers **"Is this candidate model allowed under organizational policy?"**, Module 5 answers **"Among the policy-approved candidate models, which is the most suitable target model based on configured preferences?"**

The Ranking Engine does not perform hard capability feasibility checks (Module 3) or organizational compliance blacklisting (Module 4). It evaluates transparent weighted preference criteria across candidate models to determine an ordered list of ranked models (`RankedModel`) and selects the top candidate (`selected_model`).

---

## Architectural Boundaries & Pipeline Workflow

```text
                               AI MODEL ROUTER PIPELINE
                               
  ┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
  │ Complexity Predictor │     │    Model Registry    │     │  Capability Matcher  │
  │     (Module 1)       │     │     (Module 2)       │     │     (Module 3)       │
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
                    ┌──────────────────────────┐     ┌──────────────────────────┐
                    │    Rule Engine Engine    │ ◄───│  PolicyContext (Tenant)  │
                    │        (Module 4)        │     └──────────────────────────┘
                    └──────────────────────────┘
                                 │
                       RuleEvaluationResult
                                 │
                                 ▼
                    ┌──────────────────────────┐     ┌──────────────────────────┐
                    │   Ranking Engine Engine  │ ◄───│ RankingConfig (Weights)  │
                    │        (Module 5)        │     └──────────────────────────┘
                    └──────────────────────────┘
                                 │
                         RankingResult
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Selected Target Model #1 │ ──► (Passed to Gateway Router)
                    └──────────────────────────┘
```

---

## Scoring Methodology & Mathematical Formulation

The Ranking Engine calculates a weighted overall score $S_{\text{overall}} \in [0.0, 1.0]$ for each candidate model:

$$S_{\text{overall}} = (S_{\text{cost}} \cdot w_{\text{cost}}) + (S_{\text{latency}} \cdot w_{\text{latency}}) + (S_{\text{suitability}} \cdot w_{\text{suitability}}) + (S_{\text{headroom}} \cdot w_{\text{headroom}})$$

where:
- $\sum w_i = 1.0$ (automatically normalized if positive weights are specified; residual rounding adjustments are applied to the largest non-zero weight, keeping explicit zero weights strictly zero).
- Each component score $S_i \in [0.0, 1.0]$ is derived strictly from candidate metadata and request context without machine-learning randomness or external API calls.

### 1. Cost Score ($S_{\text{cost}}$)
Mapped directly from `ModelInfo.cost_tier`:
- `"low"` $\rightarrow 1.00$
- `"medium"` $\rightarrow 0.70$
- `"high"` $\rightarrow 0.35$
- `"premium"` $\rightarrow 0.10$

If `prefer_lower_cost = False`, clean linear inversion is applied: $S_{\text{cost\_inverted}} = 1.0 - S_{\text{cost\_normal}}$.

### 2. Latency Score ($S_{\text{latency}}$)
Mapped directly from `ModelInfo.latency_tier`:
- `"fast"` $\rightarrow 1.00$
- `"medium"` $\rightarrow 0.60$
- `"slow"` $\rightarrow 0.20$

If `prefer_lower_latency = False`, clean linear inversion is applied: $S_{\text{latency\_inverted}} = 1.0 - S_{\text{latency\_normal}}$.

### 3. Suitability Score ($S_{\text{suitability}}$)
Evaluates alignment between `ModelInfo` capabilities and request complexity (`complexity_profile` string `"complexity"` or numeric score fallback):
- **`LOW` Complexity**: Lightweight fast models score $1.00$; premium cost models score $0.40$ (over-provisioned).
- **`MEDIUM` Complexity**: Balanced general-purpose models score $1.00$.
- **`HIGH` Complexity**: Deep reasoning models (`supports_reasoning=True`, high context, code support) score $1.00$; low-capacity models score $0.40$.

Note: Suitability scoring is strictly status-independent. Model availability and lifecycle access are managed by Modules 3 and 4.

### 4. Context Headroom Score ($S_{\text{headroom}}$)
Evaluates remaining context headroom (`CandidateModel.context_headroom`):
- Batch relative mode: $\text{ratio} = \text{headroom} / \text{batch\_max\_headroom}$ (clamped to $[0.0, 1.0]$).
- Standalone evaluation mode: $\text{ratio} = \text{headroom} / 200,000$ (reference scale, clamped to $[0.0, 1.0]$).
- Zero or negative headroom tokens evaluate strictly to $0.0$.

---

## Deterministic Tie-Breaking Protocol

When two candidates produce identical overall scores ($S_{\text{overall}}$), ties are broken deterministically using a strict 3-tier tuple comparison key:

$$\text{Sort Key} = \left( -S_{\text{overall}}, -\text{headroom}, \text{model\_id} \right)$$

1. **Primary**: Overall score (descending: higher score wins).
2. **Secondary**: Context headroom tokens (descending: larger headroom wins).
3. **Tertiary**: Model ID string (ascending: alphabetical string order).

This guarantees 100% reproducible rankings across all platforms and environments.
