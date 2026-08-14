# Design Overview — Module 8: Feedback Pipeline

## 1. Executive Architecture Summary

Module 8 (**Feedback Pipeline**) completes the eight-module AI Model Router framework. Positioned downstream of Module 7 (Gateway Router), its mission is to observe, record, correlate, and analyze execution traces alongside user evaluations.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AI MODEL ROUTER PIPELINE                         │
└─────────────────────────────────────────────────────────────────────────────┘
  Incoming Request
        │
        ▼
  [Module 1] Complexity Predictor  ───> Complexity Profile (Tier, Score, Confidence)
        │
        ▼
  [Module 2] Model Registry        ───> 12 Static Foundation Models Catalog
        │
        ▼
  [Module 3] Capability Matcher    ───> Hard Feasibility Filtering
        │
        ▼
  [Module 4] Rule Engine           ───> Organizational Compliance Policies
        │
        ▼
  [Module 5] Ranking Engine        ───> Multi-Criteria Scoring (Tier-Aware Norm)
        │
        ▼
  [Module 6] Policy Engine         ───> Runtime Budgets, Quotas & Bounded Fallback
        │
        ▼
  [Module 7] Gateway Router        ───> Local Mock Execution & Transient Retries
        │
        ▼
  [Module 8] Feedback Pipeline     ───> Telemetry Persistence & Historical Analytics
```

---

## 2. Core Entities and Schemas

### 2.1 `RoutingEvent` (`routing_events` table)
Captures execution facts emitted by the router and gateway:
- **Identification:** `event_id` (UUID PK), `request_id` (Indexed), `timestamp` (UTC).
- **Classification:** `task_category`, `complexity_tier`, `complexity_score`, `complexity_confidence`.
- **Selection & Governance:** `model_id`, `provider`, `decision_state`, `selected_rank`, `cost_tier`, `latency_tier`, `fallback_used`.
- **Execution:** `execution_status`, `execution_mode`, `latency_ms`, `retry_count`, `error_message`.
- **Consumption:** `prompt_tokens`, `completion_tokens`, `total_tokens`.
- **Privacy:** `prompt_summary` (truncated snippet), `metadata_json`.

### 2.2 `FeedbackRecord` (`feedback_records` table)
Captures qualitative human or agent evaluations:
- `feedback_id` (UUID PK)
- `event_id` (ForeignKey linking to `routing_events.event_id`, Indexed)
- `rating` (Integer $1 \le \text{rating} \le 5$, Indexed)
- `quality_category` (Optional categorical tag e.g. `"accurate"`, `"slow"`, `"hallucination"`)
- `comment` (Optional qualitative text)
- `evaluator_id` (Optional user or automated evaluator ID)
- `created_at` (UTC timestamp)

---

## 3. Analytical Capabilities (`FeedbackAnalytics`)

The analytical engine computes real-time operational aggregates from historical database records:
1. **Health & Volume:** Total requests, success count, failure count, success rate (%), average latency (ms), average retry count, total token volume.
2. **Routing Distributions:** Fallback trigger frequency (%), model selection breakdown, provider usage breakdown, complexity tier distribution.
3. **Quality & Satisfaction:** Average rating (1.0–5.0), satisfaction percentage (% with rating $\ge 4$), quality category breakdown.
4. **Per-Model Performance Breakdown:** Volume, success rate, average latency, average token count, and average user rating grouped by model ID.

---

## 4. Scope and Safety Guarantees

1. **Zero Real-Time Routing Mutation:** Module 8 never alters live requests or policy limits.
2. **Zero ML Retraining Loops:** It aggregates telemetry and quality indicators for future offline analysis without spawning automated model retraining jobs in this prototype.
3. **Deterministic Persistence:** Fully testable with in-memory SQLite and production-ready for PostgreSQL.
