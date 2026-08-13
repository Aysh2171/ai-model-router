# Policy Engine Architectural Design Overview

## Overview

The **Policy Engine** is the sixth independent prototype within the **Enterprise AI Model Router Framework**. It acts as the runtime governance and operational policy decision stage following preference-based candidate ranking (**Module 5 — Ranking Engine**).

### Architectural Responsibilities Boundary

- **Module 3 — Capability Matcher**: Technical Feasibility (*"Can it handle it?"*)
- **Module 4 — Rule Engine**: Organizational Eligibility (*"Are we allowed to use it under policy?"*)
- **Module 5 — Ranking Engine**: Preference Ordering (*"Which allowed model do we prefer?"*)
- **Module 6 — Policy Engine**: Runtime Operational Governance (*"Can we actually dispatch it right now under current runtime limits, budget, quotas, and rate limits?"*)

The Policy Engine operates as a runtime decision layer. It does **not** re-evaluate technical capabilities, hard organizational policies (such as data residency or provider allowlists), or re-rank candidate models.

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
                    ┌──────────────────────────┐     ┌──────────────────────────┐
                    │   Policy Engine Engine   │ ◄───│   UsageState & Context   │
                    │        (Module 6)        │     └──────────────────────────┘
                    └──────────────────────────┘
                                 │
                          PolicyDecision
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Final Target Dispatch    │ ──► (Passed to Gateway Router)
                    └──────────────────────────┘
```

---

## Runtime Policy Governance Modules

1. **Runtime Budget Governance (`BudgetPolicy`)**:
   - Compares current tenant spending (`UsageState.budget_consumed`) plus estimated request cost against `PolicyContext.budget_limit`.
   - Uses transparent prototype cost units derived from `cost_tier`: `low`=1.0, `medium`=3.0, `high`=7.0, `premium`=12.0.

2. **Request and Token Quotas (`QuotaPolicy`)**:
   - Enforces single request token bounds (`max_tokens_per_request`), daily request quotas (`daily_request_limit`), daily token limits (`daily_token_limit`), and monthly quotas.

3. **Rate Limiting (`RateLimitPolicy`)**:
   - Enforces window-based request caps (`max_requests_per_window`).

4. **Ordered Fallback Governance & Failure Classification**:
   - Distinguishes candidate-specific failures (`BUDGET_EXCEEDED`, where fallback to another candidate may succeed) from request/tenant-level failures (`RATE_LIMIT_EXCEEDED`, `REQUEST_QUOTA_EXCEEDED`, `TOKEN_QUOTA_EXCEEDED`), which short-circuit fallback evaluation immediately.
   - `max_fallback_attempts = N` permits evaluating up to $N$ fallback candidates after Rank #1 (e.g. `max_fallback_attempts = 1` permits Rank #1 to fail and Rank #2 to be evaluated).
   - **CRITICAL INVARIANT**: Ranking order ($A > B > C$) is strictly preserved. Scores and candidate rank positions are never modified.

---

## Decision States & Telemetry

- **`DecisionState`**:
  - `APPROVED`: Top-ranked candidate (Rank #1) satisfied all runtime policies (`fallback_used = False`).
  - `APPROVED_WITH_FALLBACK`: Top-ranked candidate failed runtime policy, but a lower-ranked candidate passed ordered fallback evaluation (`fallback_used = True`).
  - `REJECTED`: All ranked candidates failed runtime policies, or request/tenant limits were exhausted (`fallback_used = False`).
  - `NO_CANDIDATE`: Input `RankingResult` was empty or unsatisfiable (`fallback_used = False`).
- **`FailureReason`**: `BUDGET_EXCEEDED`, `REQUEST_QUOTA_EXCEEDED`, `TOKEN_QUOTA_EXCEEDED`, `RATE_LIMIT_EXCEEDED`, `FALLBACK_DISABLED`, `MAX_FALLBACK_ATTEMPTS_EXCEEDED`, `NO_RANKED_CANDIDATES`.
