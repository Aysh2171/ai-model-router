# AI Capability Matcher Prototype

The Capability Matcher is a lightweight feasibility filtering engine designed as the third independent prototype within the Enterprise AI Model Routing Framework. In multi-model AI routing architectures, downstream components—such as the Rule Engine, Policy Engine, and Ranking Engine—require a pre-filtered set of foundation models that are technically capable of fulfilling an incoming request. To solve this problem, the Capability Matcher accepts a normalized AI request representation, derives technical matching constraints, queries the Model Registry catalog, and executes a 5-stage deterministic filtering pipeline to determine which models **CAN** satisfy the request.

---

## Motivation

Modern enterprise AI routing systems process requests with diverse requirements, including multi-page document attachments, vision inputs, structured JSON schemas, function call tools, and long context turn histories. Evaluating complex economic policies or computing ranking utility scores against unsuitable models wastes CPU cycles. The Capability Matcher eliminates technically non-viable models early in the pipeline, ensuring downstream ranking engines process only valid, capable candidates.

---

## Features

- **Deterministic Hard Constraint Filtering**: Evaluates foundation models against mandatory technical constraints without subjective scoring or cost bias.
- **Requirement Extraction Engine**: Consumes normalized AI request representations and Complexity Profiles to derive structured `MatchRequirements` (`required_modalities`, `min_context_window`, `min_max_output_tokens`, `required_use_cases`, `required_capabilities`).
- **5-Stage Early-Exit Pipeline**: Filters models sequentially by Status $\rightarrow$ Modality $\rightarrow$ Capability Flags $\rightarrow$ Context Capacity $\rightarrow$ Use Case Alignment.
- **Request-Level Complexity Context**: Preserves the `Complexity Profile` from Prototype 1 at the request container level (`CapabilityMatchResult`), passing it downstream for ranking engines.
- **Model-Specific Candidate Objects**: Generates clean `CandidateModel` objects storing `context_headroom` surplus tokens, `matched_constraint_count`, and satisfied constraint notes.
- **Granular Disqualification Telemetry**: Captures `ExcludedModel` audit traces containing explicit rejection reasons for every disqualified catalog model.
- **Explicit Unsatisfied State**: Sets `is_satisfiable = False` when zero registered models meet technical matching constraints.
- **Zero Third-Party Dependencies**: Built entirely using Python Standard Library (`uuid`, `dataclasses`, `pathlib`, `typing`).

---

## Architecture

The Capability Matcher connects Prototype 1 and Prototype 2 to produce candidate sets for downstream routers:

$$\text{Normalized AI Request} + \text{Complexity Profile} \longrightarrow \text{Requirement Extractor} \longrightarrow \text{Capability Matcher Pipeline} \longrightarrow \text{CapabilityMatchResult}$$

### How It Works

1. **Requirement Extraction**: `RequirementExtractor` consumes normalized request representations, inspects input tokens, attachments (e.g. `image`, `pdf`), output format requirements, and derives `MatchRequirements`.
2. **Catalog Fetching**: Queries `ModelRegistry` (Prototype 2) to retrieve registered `ModelInfo` catalog definitions.
3. **Stage 1 (Status Check)**: Verifies model lifecycle status (`available`, `preview`, `deprecated`).
4. **Stage 2 (Modality Check)**: Verifies `required_modalities.issubset(model.supported_modalities)`.
5. **Stage 3 (Capability Flags)**: Verifies mandatory boolean capability flags (`supports_vision`, `supports_function_calling`, `supports_json`, `supports_code`, `supports_tools`).
6. **Stage 4 (Token Capacity)**: Verifies `model.context_window >= min_context_window` and `model.max_output_tokens >= min_max_output_tokens`.
7. **Stage 5 (Use Case Alignment)**: Verifies `required_use_cases.issubset(model.supported_use_cases)`.
8. **Result Assembly**: Wraps passing models into `CandidateModel` objects and rejected models into `ExcludedModel` objects.

---

## Project Structure

```text
capability_matcher/
│
├── src/                        # Core Python source modules
│   ├── __init__.py             # Package initializer exposing matcher and data objects
│   ├── matcher.py             # CapabilityMatcher core evaluation engine
│   ├── requirements.py        # RequirementExtractor and MatchRequirements dataclass
│   └── candidate.py           # CandidateModel, ExcludedModel, and CapabilityMatchResult
│
├── scripts/                    # Command-line entry points
│   └── demo.py                 # Interactive demonstration script
│
├── docs/                       # Architectural design documentation
│   └── design_overview.md      # System specification document
│
├── requirements.txt            # Python dependencies (Standard Library only)
└── README.md                   # Project documentation
```

---

## Tech Stack

- **Python**: 3.10+
- **Standard Library Modules**: `uuid`, `dataclasses`, `pathlib`, `typing`

---

## Setup

### Prerequisites
- Python 3.10 or higher

### Installation
Clone the repository and inspect dependencies:
```bash
# Standard library only — no external pip packages required
pip install -r requirements.txt
```

---

## Usage and Matcher Examples

### Running the Demonstration Script
To execute the interactive demonstration script across 6 distinct test scenarios:

```bash
python scripts/demo.py
```

### Programmatic Python Usage

```python
from src.matcher import CapabilityMatcher

# Initialize CapabilityMatcher (loads ModelRegistry automatically)
matcher = CapabilityMatcher()

# Sample Normalized AI Request Payload
request_payload = {
    "request_id": "REQ-001",
    "prompt": "Inspect screenshot and write React code.",
    "attachments": [{"file_name": "ui.png", "file_type": "image", "size_mb": 1.5}],
    "metadata": {"task_category": "Programming"},
    "expected_output": {"format": "code"}
}

# Optional Complexity Profile from Prototype 1
complexity_profile = {"complexity": "MEDIUM", "complexity_score": 45, "confidence": 0.90}

# Execute capability matching
result = matcher.match(request_payload, complexity_profile=complexity_profile)

print(f"Satisfiable: {result.is_satisfiable}")
print(f"Eligible Models: {result.eligible_count} / Total Registered: {result.total_registered}")

for cand in result.eligible_candidates:
    print(f" - Candidate: {cand.model_id} (Headroom: +{cand.context_headroom:,} tokens, Constraints Matched: {cand.matched_constraint_count})")
```

---

## Current Scope

- **Deterministic Hard Constraint Filtering**: Evaluates technical feasibility objectively.
- **No Model Ranking or Preference Scoring**: Models are not ordered by cost, speed, or quality.
- **No Cost/Budget Exclusion**: High-capacity models (e.g. `gpt-4o`) are retained if technically capable.
- **No Constraint Relaxation**: Unresolvable requests report `is_satisfiable = False`.
- **Decoupled Architecture**: Designed to output candidate sets for downstream engines (Rule Engine, Ranking Engine).

---

## Future Work

- **Evaluation on Real Request Logs**: Refine token margin heuristics against production request logs.
- **Richer Soft Constraint Annotations**: Annotate candidate models with context headroom indices for downstream scoring.
- **Routing Gateway Integration**: Connect the Capability Matcher into an active model routing engine pipeline.
