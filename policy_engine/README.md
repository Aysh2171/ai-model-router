# AI Policy Engine Prototype (Module 6)

The Policy Engine is a lightweight runtime governance and operational policy decision engine designed as the sixth independent prototype within the Enterprise AI Model Router Framework. In multi-model AI routing architectures:

- **Module 3 (Capability Matcher)** checks technical feasibility (*"Can it handle it?"*).
- **Module 4 (Rule Engine)** checks hard organizational policies (*"Are we allowed to use it under policy?"*).
- **Module 5 (Ranking Engine)** checks candidate preferences (*"Which allowed model do we prefer?"*).
- **Module 6 (Policy Engine)** checks runtime operational state (*"Can we actually dispatch it right now under current runtime limits, budget, quotas, and rate limits?"*).

The Policy Engine evaluates pre-ranked candidates from Module 5 in strict rank order against `PolicyContext` and `UsageState`, outputting an auditable `PolicyDecision` ready for gateway dispatch.

---

## Features

- **Runtime Operational Governance**: Enforces tenant budget limits, token/request quotas, and rate limits dynamically without modifying static candidate rankings.
- **Ordered Fallback Dispatch**: If a top-ranked candidate fails candidate-level runtime policy (e.g. budget limit exceeded), the Policy Engine evaluates fallback candidates in strict rank order without re-ranking.
- **Explicit Fallback Bounding**: `max_fallback_attempts = N` permits evaluating up to $N$ fallback candidates after Rank #1 (e.g., `max_fallback_attempts = 1` permits Rank #1 to fail and Rank #2 to be evaluated).
- **Failure Classification & Short-Circuiting**: Distinguishes candidate-specific failures (e.g. `BUDGET_EXCEEDED`, where fallback may succeed) from request/tenant-level failures (`RATE_LIMIT_EXCEEDED`, `REQUEST_QUOTA_EXCEEDED`, `TOKEN_QUOTA_EXCEEDED`), which short-circuit evaluation immediately.
- **Strict Ranking Invariant**: Preserves candidate scores and ordering ($A > B > C$) without altering pre-selection rank positions.
- **Structured Audit Telemetry**: Returns explicit machine-readable decision states (`APPROVED`, `APPROVED_WITH_FALLBACK`, `REJECTED`, `NO_CANDIDATE`) and failure reasons (`BUDGET_EXCEEDED`, `REQUEST_QUOTA_EXCEEDED`, `TOKEN_QUOTA_EXCEEDED`, `RATE_LIMIT_EXCEEDED`, `FALLBACK_DISABLED`, `MAX_FALLBACK_ATTEMPTS_EXCEEDED`). `fallback_used = True` is reported strictly on `APPROVED_WITH_FALLBACK`.
- **Zero Third-Party Dependencies**: Built entirely using Python Standard Library (`dataclasses`, `enum`, `json`, `pathlib`, `typing`, `unittest`).

---

## Architecture

$$\text{RankingResult (Module 5)} + \text{PolicyContext} + \text{UsageState} \longrightarrow \text{Policy Engine Pipeline} \longrightarrow \text{PolicyDecision}$$

### Evaluation Pipeline

1. **Input Check**: Consumes `RankingResult` from Module 5. If empty (`is_satisfiable = False`), returns `NO_CANDIDATE`.
2. **Ordered Candidate Evaluation**: Evaluates candidates sequentially ($Rank \#1 \rightarrow Rank \#2 \rightarrow Rank \#3...$).
3. **Runtime Policy Checks**: Evaluates budget, token/request quotas, and rate limits against tenant `UsageState`.
4. **Failure Classification**: If a candidate fails due to a request/tenant-level policy (`RATE_LIMIT_EXCEEDED`, `REQUEST_QUOTA_EXCEEDED`, `TOKEN_QUOTA_EXCEEDED`), evaluation halts immediately.
5. **Fallback Bounding**: If candidate-level policy (`BUDGET_EXCEEDED`) fails, fallback evaluates subsequent candidates up to `max_fallback_attempts`.
6. **Decision Telemetry Output**: Returns `PolicyDecision` with `selected_model`, `selected_rank`, `fallback_used` (`True` only on fallback approval), and complete audit trace.

---

## Project Structure

```text
policy_engine/
├── src/                        # Core Python source modules
│   ├── __init__.py             # Package exports (PolicyEngine, PolicyContext, UsageState, PolicyDecision)
│   ├── context.py              # PolicyContext & limits dataclass
│   ├── usage.py                # UsageState runtime consumption tracker
│   ├── decisions.py            # DecisionState & FailureReason enums
│   ├── result.py               # PolicyEvaluation & PolicyDecision dataclasses
│   ├── policies/               # Modular policy evaluators
│   │   ├── __init__.py         # Exports BasePolicy & DEFAULT_POLICIES
│   │   ├── base.py             # Abstract BasePolicy & PolicyEvaluationOutcome
│   │   ├── budget.py           # Runtime BudgetPolicy
│   │   ├── quota.py            # Request and Token QuotaPolicy
│   │   └── rate_limit.py       # RateLimitPolicy
│   └── engine.py               # PolicyEngine orchestrator class
│
├── config/                     # Declarative policy configuration templates
│   └── default_policy.json     # Default runtime governance policy configuration
│
├── scripts/                    # Command-line entry points
│   └── demo.py                 # Interactive demonstration script (6 scenarios)
│
├── tests/                      # Automated test suite
│   ├── __init__.py
│   ├── test_budget.py          # Unit tests for budget policy
│   ├── test_quota.py           # Unit tests for quota policy
│   ├── test_rate_limit.py      # Unit tests for rate limit policy
│   ├── test_fallback.py       # Unit tests for fallback governance & ranking order preservation
│   ├── test_engine.py          # Integration tests for PolicyEngine
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
To execute the interactive demonstration script across 6 distinct governance scenarios:

```bash
cd policy_engine
python scripts/demo.py
```

### Running the Automated Test Suite
To execute the comprehensive unit and integration test suite:

```bash
cd policy_engine
python -m unittest discover -s tests -v
```

---

## Programmatic Usage Example

```python
from capability_matcher.src import CapabilityMatcher
from rule_engine.src import RuleEngine
from ranking_engine.src import RankingEngine
from policy_engine.src import PolicyEngine, PolicyContext, UsageState

# 1. Run Pipeline Modules (Modules 3 -> 4 -> 5)
matcher = CapabilityMatcher()
cap_result = matcher.match({"prompt": "Analyze code."})

rule_engine = RuleEngine()
rule_result = rule_engine.evaluate(cap_result)

ranking_engine = RankingEngine()
ranking_result = ranking_engine.rank(rule_result)

# 2. Define Runtime Policy Context & Usage State
policy_context = PolicyContext(tenant_id="tenant_enterprise", budget_limit=50.0, max_requests_per_window=100)
usage_state = UsageState(tenant_id="tenant_enterprise", budget_consumed=10.0)

# 3. Evaluate Operational Governance & Dispatch
policy_engine = PolicyEngine()
decision = policy_engine.evaluate(ranking_result, context=policy_context, usage_state=usage_state)

print(f"Dispatch Decision: {decision.decision}")
print(f"Selected Model: {decision.selected_model.model_id} (Rank #{decision.selected_rank})")
print(f"Fallback Used: {decision.fallback_used}")
```
