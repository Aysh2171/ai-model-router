"""
Demonstration script for Module 7 — Gateway Router.
Illustrates full 7-stage routing execution, provider adapter resolution, policy-driven fallback execution,
gateway-level retries, policy rejection blocking, and local streaming generation.
"""

import sys
from pathlib import Path

# Add project root directory to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COMPLEXITY_DIR = PROJECT_ROOT / "complexity_predictor"

sys.path.insert(0, str(PROJECT_ROOT))
if str(COMPLEXITY_DIR) not in sys.path:
    sys.path.insert(0, str(COMPLEXITY_DIR))

from gateway_router.src.gateway import GatewayRouter
from gateway_router.src.orchestrator import PipelineRouter
from gateway_router.src.models import GatewayRequest, ExecutionStatus, ExecutionMode
from gateway_router.src.config import GatewayConfig
from rule_engine.src import PolicyContext as RulePolicyContext
from ranking_engine.src import RankingConfig
from policy_engine.src import PolicyContext as RuntimePolicyContext, UsageState


def print_section(title: str) -> None:
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title.upper()} ")
    print("=" * 80)


def print_gateway_response(resp) -> None:
    """Print structured terminal summary of a GatewayResponse."""
    print(f"  [EXECUTION STATUS]  : {resp.status.value if hasattr(resp.status, 'value') else resp.status}")
    print(f"  [DECISION STATE]    : {resp.decision_state or 'N/A'}")
    print(f"  [SELECTED MODEL]    : {resp.model_id or 'None'} (Provider: {resp.provider or 'None'})")
    print(f"  [EXECUTION MODE]    : {resp.execution_mode.upper()} (Local Simulation)")
    print(f"  [RETRY COUNT]       : {resp.retry_count}")
    print(f"  [FALLBACK USED]     : {resp.fallback_used}")
    print(f"  [SIMULATED LATENCY] : {resp.latency_ms:.2f} ms")
    if resp.content:
        print(f"  [RESPONSE CONTENT]  :\n    \"{resp.content}\"")
    if resp.error_message:
        print(f"  [ERROR / AUDIT]     :\n    {resp.error_message}")
    if resp.usage:
        print(f"  [USAGE ESTIMATE]    : Prompt={resp.usage.get('prompt_tokens', 0)}, Completion={resp.usage.get('completion_tokens', 0)}, Total={resp.usage.get('total_tokens', 0)} tokens")


def main() -> None:
    print_section("AI Model Router - Module 7: Gateway Router Demonstration")
    print("Execution Environment: Local Prototype (Zero Commercial API calls / Zero Cloud Spending)")

    pipeline = PipelineRouter()
    gateway = GatewayRouter()

    # =========================================================================
    # SCENARIO 1: Full End-to-End Routing to Approved Model
    # =========================================================================
    print_section("Scenario 1: Full Pipeline Dispatch to Approved Foundation Model")
    req_1 = {
        "request_id": "REQ-DEMO-001",
        "prompt": "Write a Python function to compute the Fibonacci sequence using memoization.",
        "metadata": {"task_category": "Programming"},
        "expected_output": {"format": "code"}
    }
    print(f"  Incoming Prompt: '{req_1['prompt']}'")
    resp_1 = pipeline.route_and_execute(req_1)
    print_gateway_response(resp_1)

    # =========================================================================
    # SCENARIO 2: Policy-Selected Fallback Execution
    # =========================================================================
    print_section("Scenario 2: Policy-Selected Fallback Execution (Budget Governed)")
    print("  Context: Tenant has a tight budget cap of 2.0 units. Rank #1 (High Cost) is rejected by Policy Engine.")
    print("  Action: Policy Engine selects Rank #2 (Low Cost) fallback. Gateway executes the policy's final model.")
    req_2 = {
        "request_id": "REQ-DEMO-002",
        "prompt": "Write a Python function to validate email addresses using regular expressions.",
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
    print_gateway_response(resp_2)

    # =========================================================================
    # SCENARIO 3: Policy Engine Rejection Execution Block
    # =========================================================================
    print_section("Scenario 3: Policy Rejection Execution Block (Daily Quota Reached)")
    print("  Context: Tenant daily request quota is exhausted (limit reached).")
    print("  Action: Policy Engine rejects dispatch. Gateway blocks adapter execution and returns REJECTED.")
    req_3 = {
        "request_id": "REQ-DEMO-003",
        "prompt": "Summarize attached meeting notes.",
        "metadata": {"task_category": "General Prompting"}
    }
    exhausted_ctx = RuntimePolicyContext(
        tenant_id="exhausted_tenant",
        daily_request_limit=0
    )
    exhausted_usage = UsageState(tenant_id="exhausted_tenant", daily_requests_used=0)
    resp_3 = pipeline.route_and_execute(
        raw_request=req_3,
        runtime_policy_context=exhausted_ctx,
        usage_state=exhausted_usage
    )
    print_gateway_response(resp_3)

    # =========================================================================
    # SCENARIO 4: Gateway Transient Execution Retry
    # =========================================================================
    print_section("Scenario 4: Gateway Bounded Retry on Transient Execution Failure")
    print("  Context: Provider adapter encounters transient network glitch on Attempt 1. Succeeds on Attempt 2.")
    req_4 = GatewayRequest(
        request_id="REQ-DEMO-004",
        prompt="Explain vector search indexing algorithms.",
        provider="OpenAI",
        model_id="gpt-4o",
        simulation_options={
            "fail_mode": "transient_then_success",
            "fail_count_before_success": 1
        }
    )
    resp_4 = gateway.execute(req_4)
    print_gateway_response(resp_4)

    # =========================================================================
    # SCENARIO 5: Gateway Permanent Error Non-Retryable Abort
    # =========================================================================
    print_section("Scenario 5: Gateway Permanent Error Immediate Abort (No Wasteful Retries)")
    print("  Context: Provider adapter encounters 400 Bad Request error (non-retryable).")
    print("  Action: Gateway aborts immediately without retrying (retry_count=0).")
    req_5 = GatewayRequest(
        request_id="REQ-DEMO-005",
        prompt="Execute payload with invalid token format.",
        provider="Anthropic",
        model_id="claude-3.5-sonnet",
        simulation_options={"fail_mode": "permanent"}
    )
    resp_5 = gateway.execute(req_5)
    print_gateway_response(resp_5)

    # =========================================================================
    # SCENARIO 6: Local Streaming Generation Simulation (SSE)
    # =========================================================================
    print_section("Scenario 6: Local Streaming Token Generation Simulation (SSE Compatible)")
    req_6 = GatewayRequest(
        request_id="REQ-DEMO-006",
        prompt="Generate a step-by-step tutorial on building a REST API.",
        provider="OpenAI",
        model_id="gpt-4o",
        stream=True
    )
    print(f"  Streaming Chunks for Request ID: {req_6.request_id}")
    for chunk in gateway.execute_stream(req_6):
        print(f"    [Chunk {chunk.chunk_index:<2}] (Final={chunk.is_final:<5}) -> \"{chunk.content}\"")

    print("\n" + "=" * 80)
    print(" Gateway Router Demonstration Complete ")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
