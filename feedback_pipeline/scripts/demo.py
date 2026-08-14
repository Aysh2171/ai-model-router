"""
Demonstration Script for Module 8: Feedback Pipeline.
Showcases telemetry ingestion from Gateway execution, user quality feedback attachment,
historical event correlation, and analytical metric aggregation.
"""

import sys
from pathlib import Path

# Ensure project modules are resolvable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "complexity_predictor") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "complexity_predictor"))

from gateway_router.src.orchestrator import PipelineRouter
from rule_engine.src import PolicyContext as RulePolicyContext
from ranking_engine.src import RankingConfig
from policy_engine.src import PolicyContext as RuntimePolicyContext, UsageState

from feedback_pipeline.src.config import FeedbackConfig
from feedback_pipeline.src.repository import SQLAlchemyFeedbackRepository
from feedback_pipeline.src.service import FeedbackService
from feedback_pipeline.src.analytics import FeedbackAnalytics


def print_section(title: str) -> None:
    """Print standard visual section banner."""
    print(f"\n{'=' * 80}\n {title.upper()} \n{'=' * 80}")


def main() -> None:
    print_section("AI Model Router - Module 8: Feedback Pipeline Demonstration")
    print("Execution Environment: Local Prototype (Zero Commercial API calls / Zero Cloud Spending)")

    # 1. Initialize End-to-End Pipeline and Feedback Pipeline
    pipeline = PipelineRouter()
    config = FeedbackConfig(database_url="sqlite:///:memory:")
    repository = SQLAlchemyFeedbackRepository(database_url=config.database_url)
    service = FeedbackService(repository=repository, config=config)
    analytics = FeedbackAnalytics(repository=repository)

    # =========================================================================
    # SCENARIO 1: Normal Pipeline Dispatch & Telemetry Ingestion
    # =========================================================================
    print_section("Scenario 1: Normal Pipeline Dispatch & Telemetry Ingestion")
    print("  Action: Route programming request through M1-M7 -> Ingest GatewayResponse into Module 8.")
    req_1 = {
        "request_id": "REQ-DEMO-M8-001",
        "prompt": "Write a Python function to compute the Fibonacci sequence using memoization.",
        "metadata": {"task_category": "Programming"},
        "expected_output": {"format": "code"}
    }
    resp_1 = pipeline.route_and_execute(raw_request=req_1)
    event_1 = service.record_gateway_response(
        response=resp_1,
        request_prompt=req_1["prompt"],
        task_category="Programming"
    )
    print(f"  [TELEMETRY INGESTED] Event ID       : {event_1.event_id}")
    print(f"  [REQUEST CORRELATION] Request ID    : {event_1.request_id}")
    print(f"  [ROUTED SELECTION] Model / Provider : {event_1.model_id} ({event_1.provider})")
    print(f"  [COMPLEXITY AUDIT] Complexity Tier  : {event_1.complexity_tier} (Score: {event_1.complexity_score})")
    print(f"  [EXECUTION METRICS] Status / Mode   : {event_1.execution_status} ({event_1.execution_mode})")
    print(f"  [LATENCY / TOKENS] Latency / Tokens : {event_1.latency_ms:.2f} ms | Total Tokens: {event_1.total_tokens}")

    # =========================================================================
    # SCENARIO 2: Policy-Governed Fallback Telemetry Ingestion
    # =========================================================================
    print_section("Scenario 2: Policy-Governed Fallback Telemetry Ingestion")
    print("  Context: Budget cap of 2.0 units rejects Rank #1 (High Cost). Policy Engine selects Rank #2.")
    print("  Action: Ingest fallback execution telemetry into Module 8 repository.")
    req_2 = {
        "request_id": "REQ-DEMO-M8-002",
        "prompt": "Write a Python function to validate email addresses using regex.",
        "metadata": {"task_category": "Programming"},
        "expected_output": {"format": "code"}
    }
    tight_budget_ctx = RuntimePolicyContext(
        tenant_id="budget_constrained_tenant",
        budget_limit=2.0,
        fallback_enabled=True,
        max_fallback_attempts=3
    )
    resp_2 = pipeline.route_and_execute(
        raw_request=req_2,
        rule_context=RulePolicyContext(allowed_providers={"Anthropic"}),
        ranking_config=RankingConfig(prefer_lower_cost=False),
        runtime_policy_context=tight_budget_ctx
    )
    event_2 = service.record_gateway_response(
        response=resp_2,
        request_prompt=req_2["prompt"],
        task_category="Programming"
    )
    print(f"  [TELEMETRY INGESTED] Event ID       : {event_2.event_id}")
    print(f"  [ROUTED SELECTION] Model / Provider : {event_2.model_id} ({event_2.provider})")
    print(f"  [DECISION STATE] Decision State     : {event_2.decision_state}")
    print(f"  [FALLBACK AUDIT] Fallback Used      : {event_2.fallback_used}")

    # =========================================================================
    # SCENARIO 3: Policy Engine Rejection Telemetry Ingestion
    # =========================================================================
    print_section("Scenario 3: Policy Engine Rejection Telemetry Ingestion")
    print("  Context: Tenant daily request quota is exhausted.")
    print("  Action: Ingest policy rejection telemetry into Module 8 repository.")
    req_3 = {
        "request_id": "REQ-DEMO-M8-003",
        "prompt": "Summarize attached meeting notes.",
        "metadata": {"task_category": "General Prompting"}
    }
    quota_exhausted_ctx = RuntimePolicyContext(
        tenant_id="exhausted_quota_tenant",
        daily_request_limit=10
    )
    initial_usage = UsageState(tenant_id="exhausted_quota_tenant", daily_requests_used=10)
    resp_3 = pipeline.route_and_execute(
        raw_request=req_3,
        runtime_policy_context=quota_exhausted_ctx,
        usage_state=initial_usage
    )
    event_3 = service.record_gateway_response(
        response=resp_3,
        request_prompt=req_3["prompt"],
        task_category="General Prompting"
    )
    print(f"  [TELEMETRY INGESTED] Event ID       : {event_3.event_id}")
    print(f"  [EXECUTION STATUS] Status           : {event_3.execution_status}")
    print(f"  [AUDIT TRACE] Error / Reason        : {event_3.error_message}")

    # =========================================================================
    # SCENARIO 4: User & Evaluator Quality Feedback Attachment
    # =========================================================================
    print_section("Scenario 4: User & Evaluator Quality Feedback Attachment")
    print("  Action: Client applications and evaluators attach post-execution quality ratings to events.")

    fb_1 = service.submit_feedback(
        event_id=event_1.event_id,
        rating=5,
        quality_category="accurate",
        comment="Generated clean memoized recursive solution. Excellent.",
        evaluator_id="evaluator_alice"
    )
    print(f"  [FEEDBACK ATTACHED] Linked Event: {event_1.event_id[:8]}... | Rating: {fb_1.rating}/5 | Category: {fb_1.quality_category}")
    print(f"                      Comment: '{fb_1.comment}'")

    fb_2 = service.submit_feedback(
        event_id=event_2.event_id,
        rating=4,
        quality_category="accurate",
        comment="Fallback model answered correctly with slightly simplified regex.",
        evaluator_id="evaluator_bob"
    )
    print(f"  [FEEDBACK ATTACHED] Linked Event: {event_2.event_id[:8]}... | Rating: {fb_2.rating}/5 | Category: {fb_2.quality_category}")

    # Query event bundle with feedback
    event_trace = service.get_event_with_feedback(event_1.event_id)
    print(f"\n  [PERSISTED EVENT TRACE] Querying Event ID '{event_1.event_id}':")
    print(f"    Request ID: {event_trace['event']['request_id']}, Model: {event_trace['event']['model_id']}")
    print(f"    Attached Feedback Items: {len(event_trace['feedback'])}")

    # =========================================================================
    # SCENARIO 5: Historical Telemetry & Feedback Analytics Dashboard
    # =========================================================================
    print_section("Scenario 5: Historical Telemetry & Feedback Analytics Dashboard")
    summary = analytics.get_summary_metrics()
    routing_dist = analytics.get_routing_distribution()
    quality = analytics.get_quality_metrics()
    model_perf = analytics.get_model_performance_summary()

    print("  --- SYSTEM HEALTH & VOLUME SUMMARY ---")
    print(f"    Total Requests Handled   : {summary['total_requests']}")
    print(f"    Successful Requests      : {summary['successful_requests']}")
    print(f"    Failed / Blocked Requests: {summary['failed_requests']}")
    print(f"    Overall Success Rate     : {summary['success_rate_pct']:.1f}%")
    print(f"    Average Routing Latency  : {summary['avg_latency_ms']:.2f} ms")
    print(f"    Total Tokens Processed   : {summary['total_tokens']}")

    print("\n  --- ROUTING & POLICY DISTRIBUTION ---")
    print(f"    Fallback Trigger Rate    : {routing_dist['fallback_rate_pct']:.1f}% ({routing_dist['fallback_count']} events)")
    print(f"    Model Selection Frequency: {routing_dist['model_usage']}")
    print(f"    Provider Breakdown       : {routing_dist['provider_usage']}")
    print(f"    Complexity Tiers         : {routing_dist['complexity_distribution']}")

    print("\n  --- QUALITATIVE EVALUATION & SATISFACTION ---")
    print(f"    Total Feedback Captured  : {quality['total_feedback_count']}")
    print(f"    Average User Rating      : {quality['average_rating']:.2f} / 5.0")
    print(f"    Satisfaction Rate (>= 4) : {quality['satisfaction_rate_pct']:.1f}%")
    print(f"    Rating Distribution      : {quality['rating_distribution']}")

    print("\n  --- PER-MODEL HISTORICAL PERFORMANCE ---")
    for m in model_perf:
        rating_str = f"{m['avg_rating']:.2f}/5.0 ({m['feedback_count']} reviews)" if m['avg_rating'] is not None else "No ratings"
        print(f"    * Model: {m['model_id']:<18} | Provider: {m['provider']:<10} | Requests: {m['request_count']} | Success: {m['success_rate_pct']:.0f}% | Avg Latency: {m['avg_latency_ms']:.1f}ms | Avg Rating: {rating_str}")

    print_section("Feedback Pipeline Demonstration Complete")


if __name__ == "__main__":
    main()
