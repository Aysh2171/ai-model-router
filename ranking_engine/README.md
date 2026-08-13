# AI Ranking Engine Prototype (Module 5)

The Ranking Engine is a lightweight preference scoring and model candidate ordering engine designed as the fifth independent prototype within the Enterprise AI Model Router Framework. In multi-model AI routing architectures, Module 3 (Capability Matcher) checks technical feasibility and Module 4 (Rule Engine) enforces hard organizational policies. The Ranking Engine answers the final pre-dispatch question: **"Among the policy-approved candidate models, which model is most suitable based on configured preferences?"**

---

## Motivation

Once a request has been vetted for feasibility and policy compliance, enterprise router systems must select a specific target model among multiple viable candidates:

- **Cost Optimization**: Defaulting to ultra-high-cost frontier models for routine queries increases inference bills unnecessarily.
- **Latency Sensitivity**: Interactive user applications require prioritizing low-latency fast models over slower deep-reasoning models.
- **Complexity Alignment**: High-complexity coding and reasoning tasks require high-capacity models, whereas low-complexity tasks perform best on lightweight models.
- **Explainability & Transparency**: Hardcoded or opaque black-box router rankings lead to unexpected behavior and vendor bias.

The Ranking Engine provides transparent, configurable, weighted scoring and deterministic tie-breaking without machine-learning randomness or external API dependencies.

---

## Features

- **Transparent Preference Scoring**: Combines Cost, Latency, Complexity Suitability, and Context Headroom scores using configurable weights.
- **Deterministic Tie-Breaking Protocol**: Resolves identical scores using strict secondary headroom and tertiary model ID alphabetical ordering.
- **Configurable Weight Policy**: Supports declarative JSON policy files and programmatic overrides with automatic weight validation and normalization.
- **Zero Third-Party Dependencies**: Built entirely using Python Standard Library (`dataclasses`, `json`, `pathlib`, `typing`, `unittest`).
- **Clean Decoupled Architecture**: Consumes `RuleEvaluationResult` (from Module 4) directly without modifying previous modules or querying external registries.

---

## Architecture

$$\text{RuleEvaluationResult (Module 4)} + \text{RankingConfig} \longrightarrow \text{Ranking Engine Pipeline} \longrightarrow \text{RankingResult}$$

### Evaluation Pipeline

1. **Input Verification**: Consumes `allowed_candidates` from Module 4. If empty, short-circuits gracefully (`is_satisfiable = False`).
2. **Criteria Scoring**: Calculates normalized scores $S_i \in [0.0, 1.0]$ for Cost, Latency, Suitability, and Headroom.
3. **Weighted Combination**: Computes overall score $S_{\text{overall}} = \sum (S_i \cdot w_i)$.
4. **Deterministic Sorting**: Orders models by `(-overall_score, -headroom, model_id)`.
5. **Selection Output**: Assigns 1-indexed rank positions, selects top candidate (`selected_model`), and generates explanation telemetry.

---

## Project Structure

```text
ranking_engine/
├── src/                        # Core Python source modules
│   ├── __init__.py             # Package exports (RankingEngine, RankingConfig, RankedModel, RankingResult)
│   ├── config.py               # RankingConfig dataclass & weight validation
│   ├── result.py               # RankedModel & RankingResult dataclasses
│   ├── scoring.py              # ComponentScorer criteria algorithms
│   └── engine.py               # RankingEngine orchestrator class
│
├── config/                     # Declarative policy configuration templates
│   └── default_ranking_policy.json # Default ranking policy weights
│
├── scripts/                    # Command-line entry points
│   └── demo.py                 # Interactive demonstration script (6 scenarios)
│
├── tests/                      # Automated test suite
│   ├── __init__.py
│   ├── test_scoring.py         # Unit tests for scoring logic & tie-breaking
│   ├── test_engine.py          # Integration tests for RankingEngine
│   └── test_demo_script.py     # Smoke test for CLI demo execution
│
├── docs/                       # Architectural design documentation
│   └── design_overview.md      # System specification document
│
├── requirements.txt            # Python dependencies (Standard Library only)
└── README.md                   # Complete module documentation
```

---

## Setup & Execution

### Prerequisites
- Python 3.10 or higher

### Running the Demonstration Script
To execute the interactive demonstration script across 6 distinct ranking scenarios:

```bash
cd ranking_engine
python scripts/demo.py
```

### Running the Automated Test Suite
To execute the comprehensive unit and integration test suite:

```bash
cd ranking_engine
python -m unittest discover -s tests -v
```

---

## Programmatic Usage Example

```python
from capability_matcher.src.matcher import CapabilityMatcher
from rule_engine.src import RuleEngine, PolicyContext
from ranking_engine.src import RankingEngine, RankingConfig

# 1. Run Capability Matcher & Rule Engine
matcher = CapabilityMatcher()
cap_result = matcher.match({"prompt": "Analyze code repository."})

rule_engine = RuleEngine()
rule_result = rule_engine.evaluate(cap_result, context=PolicyContext())

# 2. Define Cost-Focused Ranking Configuration
ranking_config = RankingConfig(
    cost_weight=0.60,
    latency_weight=0.20,
    suitability_weight=0.10,
    headroom_weight=0.10
)

# 3. Rank Candidates and Select Target Model
ranking_engine = RankingEngine()
result = ranking_engine.rank(rule_result, config=ranking_config)

print(f"Top Selected Model: {result.selected_model.model_id} (Score: {result.selected_model.overall_score:.4f})")
```
