# AI Rule Engine Prototype (Module 4)

The Rule Engine is a lightweight organizational governance filtering engine designed as the fourth independent prototype within the Enterprise AI Model Router Framework. In multi-model AI routing architectures, technical feasibility matching (Module 3 — Capability Matcher) identifies models capable of performing a task. However, enterprise organizations must also enforce business rules, data residency laws, vendor blacklists, security compliance standards, tenant tier permissions, and budget cost caps. The Rule Engine evaluates technically feasible candidate models against a `PolicyContext` across a suite of modular rules, outputting an auditable `RuleEvaluationResult` containing allowed candidates and policy rejection telemetry.

---

## Motivation

Deploying foundation models in enterprise production requires strict compliance governance:

- **Vendor Governance**: Certain enterprise departments or tenants may prohibit specific model providers.
- **Sovereignty & Data Residency**: EU regulatory standards (GDPR, EU AI Act) mandate that customer data remain within designated geographical boundaries.
- **Security & Regulatory Compliance**: Healthcare or financial workloads require models with explicit compliance tags (`HIPAA`, `SOC 2`).
- **Cost & Tier Controls**: Standard tenant tiers must be capped at low/medium cost models, reserving high/premium models for enterprise tier tenants.

The Rule Engine decouples organizational governance from model inference and scoring, ensuring policy enforcement remains objective, transparent, and fully auditable.

---

## Features

- **Deterministic Hard Policy Filtering**: Evaluates candidate models against explicit organizational rules without subjective scoring or preference weights.
- **Modular Rule Architecture**: Built on a clean `BaseRule` interface allowing effortless addition of custom business policy rules.
- **Multi-Violation Telemetry Collection**: Evaluates all rules per candidate and collects full violation telemetry rather than stopping after the first failure.
- **Deterministic Cost Tier Ordering**: Enforces cost caps using strict ordinal ordering (`low` < `medium` < `high` < `premium`).
- **Data Residency Verification**: Enforces regional sovereignty rules against model catalog tags and metadata attributes.
- **Preserved Lineage Audit**: Separates Module 3 capability exclusions from Module 4 policy exclusions in `RuleEvaluationResult`.
- **Zero Third-Party Dependencies**: Built entirely using Python Standard Library (`dataclasses`, `json`, `pathlib`, `typing`, `abc`).

---

## Architecture

$$\text{CapabilityMatchResult (Module 3)} + \text{PolicyContext} \longrightarrow \text{Rule Engine Pipeline} \longrightarrow \text{RuleEvaluationResult}$$

### Evaluation Pipeline

1. **Input Check**: Receives `CapabilityMatchResult` from Module 3. If empty (`is_satisfiable = False`), short-circuits gracefully.
2. **Provider Whitelist/Blacklist**: Evaluates `AllowedProvidersRule` and `DisallowedProvidersRule`.
3. **Data Residency Compliance**: Evaluates `DataResidencyRule` against regional tags (e.g. `eu-hosted`, `us-only`).
4. **Security & Regulatory Compliance**: Evaluates `SecurityComplianceRule` against required tags (`hipaa`, `soc2`).
5. **Tenant Access Tier & Status**: Evaluates `TenantAccessTierRule` for preview models or premium tiers.
6. **Max Cost Tier Governance**: Evaluates `MaxCostTierRule` using deterministic cost ordering.
7. **Result Assembly**: Places passing models in `allowed_candidates` and rejected models in `policy_excluded_candidates` with complete violation details.

---

## Project Structure

```text
rule_engine/
├── src/                        # Core Python source modules
│   ├── __init__.py             # Package exports (RuleEngine, PolicyContext, RuleEvaluationResult)
│   ├── context.py              # PolicyContext & COST_TIER_ORDER definitions
│   ├── result.py               # PolicyExcludedModel & RuleEvaluationResult dataclasses
│   ├── rules/                  # Modular policy rule implementations
│   │   ├── __init__.py         # Exports base classes and DEFAULT_RULES
│   │   ├── base.py             # Abstract BaseRule & RuleOutcome definitions
│   │   ├── provider_rules.py   # AllowedProvidersRule & DisallowedProvidersRule
│   │   ├── residency_rules.py  # DataResidencyRule
│   │   ├── compliance_rules.py # SecurityComplianceRule & TenantAccessTierRule
│   │   └── cost_rules.py       # MaxCostTierRule
│   └── engine.py               # RuleEngine orchestrator class
│
├── config/                     # Declarative policy configuration templates
│   └── default_policy.json     # Default organizational policy configuration
│
├── scripts/                    # Command-line entry points
│   └── demo.py                 # Interactive demonstration script (6 scenarios)
│
├── docs/                       # Architectural design documentation
│   └── design_overview.md      # System specification document
│
├── requirements.txt            # Python dependencies (Standard Library only)
└── README.md                   # Complete module documentation
```

---

## Tech Stack

- **Python**: 3.10+
- **Standard Library Modules**: `dataclasses`, `json`, `pathlib`, `typing`, `abc`, `unittest`, `subprocess`

---

## Setup & Execution

### Prerequisites
- Python 3.10 or higher

### Running the Demonstration Script
To execute the interactive demonstration script across 6 distinct governance scenarios:

```bash
cd rule_engine
python scripts/demo.py
```

### Running the Automated Test Suite
To execute the comprehensive unit and integration test suite:

```bash
cd rule_engine
python -m unittest discover -s tests
```

---

## Programmatic Usage Example

```python
from capability_matcher.src.matcher import CapabilityMatcher
from rule_engine.src import RuleEngine, PolicyContext

# 1. Run Capability Matcher to get technically feasible candidates
matcher = CapabilityMatcher()
cap_result = matcher.match({
    "prompt": "Write Python code.",
    "metadata": {"task_category": "Programming"}
})

# 2. Define Tenant Policy Context
policy_context = PolicyContext(
    tenant_id="tenant_finance",
    tenant_tier="enterprise",
    allowed_providers={"Anthropic", "OpenAI"},
    max_cost_tier="high"
)

# 3. Evaluate Organizational Rules
rule_engine = RuleEngine()
result = rule_engine.evaluate(cap_result, context=policy_context)

print(f"Satisfiable: {result.is_rule_satisfiable}")
print(f"Allowed Models: {result.allowed_count} / Feasible Input: {result.total_feasible_input}")

for candidate in result.allowed_candidates:
    print(f" - Allowed Model: {candidate.model_id} ({candidate.provider})")
```
