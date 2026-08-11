# Rule Engine Architectural Design Overview

## Overview

The **Rule Engine** is the fourth independent prototype within the **Enterprise AI Model Router Framework**. It acts as the organizational governance filtering stage following technical feasibility matching (**Module 3 — Capability Matcher**), evaluating candidate models against organizational policies, business rules, compliance requirements, tenant tier limits, and cost caps.

Its primary responsibility is **deterministic hard policy filtering**: determining which technically feasible foundation models are **allowed** vs. **rejected** based on organizational policy rules. It does not perform model ranking, score weighting, or preference ordering.

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
                     ┌────────────────────────┐
                     │ Allowed Candidates Set │ ──► (Passed to Ranking Engine)
                     └────────────────────────┘
```

---

## Built-in Organizational Policy Rules

1. **`AllowedProvidersRule` / `DisallowedProvidersRule`**:
   - Enforces organizational provider whitelists and blacklists per tenant context.
2. **`DataResidencyRule`**:
   - Enforces regional data residency compliance (e.g., `"EU"`, `"US"`) based on candidate model tags (`"eu-hosted"`, `"us-only"`, `"global"`).
3. **`SecurityComplianceRule`**:
   - Enforces required security compliance tags (e.g., `{"hipaa", "soc2", "enterprise"}`).
4. **`TenantAccessTierRule`**:
   - Enforces access tier policies (e.g., models with status `"preview"` or `"premium"` cost tier require `tenant_tier == "enterprise"`).
5. **`MaxCostTierRule`**:
   - Enforces cost caps using deterministic cost tier ordering (`low` < `medium` < `high` < `premium`).

---

## Data Models Specification

- **`PolicyContext`**: Dataclass capturing tenant metadata, allowed/disallowed providers, data residency region, required compliance tags, max cost tier, and allowed model statuses.
- **`PolicyExcludedModel`**: Captures candidate models rejected by organizational rules with explicit rule violation details and failed rule names.
- **`RuleEvaluationResult`**: Container object returning `request_id`, `is_rule_satisfiable`, `policy_context`, `allowed_candidates`, `policy_excluded_candidates`, `capability_excluded_models` (preserved from Module 3), and summary metrics.
