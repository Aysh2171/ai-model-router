"""
AI Model Router — Live NVIDIA NIM Provider Demonstration.
Executes an end-to-end routing workflow through the standard 7-module PipelineRouter
with organizational provider governance constrained to NVIDIA via RulePolicyContext.

Workflow:
  Raw Request -> M1 Complexity -> M2/M3 Capability Matcher -> M4 Rule Engine (NVIDIA Constrained)
             -> M5 Ranking Engine -> M6 Policy Engine -> M7 GatewayRouter -> NvidiaProviderAdapter
             -> Live NIM API (https://integrate.api.nvidia.com/v1) -> Real Response / Telemetry.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gateway_router.src.orchestrator import PipelineRouter
from gateway_router.src.gateway import GatewayRouter
from gateway_router.src.config import GatewayConfig
from gateway_router.src.models import GatewayRequest, GatewayResponse, ExecutionStatus, ExecutionMode
from rule_engine.src import PolicyContext as RulePolicyContext


def run_nvidia_live_demonstration(prompt: str = "Explain photosynthesis in two sentences.") -> GatewayResponse:
    """
    Execute full end-to-end routing pipeline constrained to NVIDIA via RulePolicyContext.
    """
    print("=" * 80)
    print("      AI MODEL ROUTER — LIVE NVIDIA PROVIDER INTEGRATION DEMONSTRATION        ")
    print("=" * 80)
    print("  Routing Engine        : Normal PipelineRouter (Modules 1 through 7)")
    print("  Provider Governance   : RulePolicyContext(allowed_providers=['NVIDIA'])")
    print("  Target Endpoint       : https://integrate.api.nvidia.com/v1")
    print("  Resolved Adapter      : NvidiaProviderAdapter (Live NIM API)")
    print("=" * 80)

    # 1. Initialize normal GatewayRouter and PipelineRouter
    config = GatewayConfig(max_retries=0, timeout_seconds=30.0)
    gateway = GatewayRouter(config=config)
    pipeline = PipelineRouter(gateway=gateway)

    # 2. Construct normal incoming client request
    raw_request: Dict[str, Any] = {
        "request_id": f"REQ-NVIDIA-LIVE-{int(time.time())}",
        "prompt": prompt,
        "metadata": {"task_category": "General Question Answering"},
        "expected_output": {"format": "text"},
        "conversation_context": {"turns": 0},
        "attachments": []
    }

    # 3. Create rule governance context restricting allowed providers to NVIDIA
    rule_context = RulePolicyContext(allowed_providers=["NVIDIA"])

    print(f"\n[1. INCOMING REQUEST]: \"{prompt}\"")
    print("\n[2. PIPELINE EXECUTION TRACE]:")

    # M1 Complexity
    comp = pipeline.predictor.predict_complexity(raw_request)
    comp_tier = comp.get("complexity", "Medium")
    comp_score = comp.get("complexity_score", 50.0)
    print(f"  - Module 1 (Complexity)  : Predicted Tier = {comp_tier} (Score: {comp_score:.1f}/100)")

    # M3 Matcher
    match_res = pipeline.matcher.match(raw_request, comp)
    print(f"  - Module 3 (Matcher)     : {match_res.eligible_count} / {match_res.total_registered} Catalog Candidates Eligible")

    # M4 Rules
    rule_eval = pipeline.rule_engine.evaluate(match_res, context=rule_context)
    allowed_names = [c.model_id for c in rule_eval.allowed_candidates]
    print(f"  - Module 4 (Rule Engine) : {rule_eval.allowed_count} Allowed Candidate(s) under NVIDIA Constraint: {allowed_names}")

    # M5 Ranking
    ranking_res = pipeline.ranking_engine.rank(rule_eval)
    top_cand = ranking_res.selected_model
    print(f"  - Module 5 (Ranking)     : Top Model = {top_cand.model_id if top_cand else 'None'} (Score: {top_cand.overall_score:.4f} if top_cand else 0)")

    # M6 Policy
    pol_dec = pipeline.policy_engine.evaluate(ranking_res)
    print(f"  - Module 6 (Policy)      : Decision = {pol_dec.decision.value}, Approved Model = {pol_dec.selected_model.model_id if pol_dec.selected_model else 'None'}")

    # M7 Gateway Execution
    print(f"  - Module 7 (Gateway)     : Dispatching via AdapterRegistry to NvidiaProviderAdapter...")
    start_time = time.perf_counter()
    response = pipeline.route_and_execute(raw_request, rule_context=rule_context)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # 4. Display Execution Telemetry
    adapter_name = response.metadata.get("adapter_name", "UNKNOWN")
    print("\n" + "=" * 80)
    print("                        ROUTING & EXECUTION TELEMETRY                         ")
    print("=" * 80)
    print(f"  Request ID            : {response.request_id}")
    print(f"  Pipeline Status       : {response.status.value}")
    print(f"  Policy Decision State : {response.decision_state}")
    print(f"  Selected Model        : {response.model_id}")
    print(f"  Selected Provider     : {response.provider}")
    print(f"  Execution Mode        : {response.execution_mode.upper()} ({'Real External API Call' if response.execution_mode == 'live' else 'Local Simulation'})")
    print(f"  Resolved Adapter      : {adapter_name}")
    print(f"  Execution Latency     : {response.latency_ms:.2f} ms (Pipeline Total: {elapsed_ms:.2f} ms)")
    print(f"  Retry Count           : {response.retry_count}")

    if response.usage:
        p_tok = response.usage.get("prompt_tokens", 0)
        c_tok = response.usage.get("completion_tokens", 0)
        t_tok = response.usage.get("total_tokens", 0)
        print(f"  Token Usage           : Prompt={p_tok}, Completion={c_tok}, Total={t_tok}")
    else:
        print(f"  Token Usage           : N/A")

    print("-" * 80)
    print(" LIVE MODEL RESPONSE CONTENT")
    print("-" * 80)
    if response.status == ExecutionStatus.SUCCESS and response.content:
        print(f"  {response.content.strip()}")
    elif "429" in (response.error_message or ""):
        print("  [PROVIDER-SIDE RATE LIMIT — HTTP 429]")
        print(f"  Details: {response.error_message}")
        print("  Note   : The request successfully routed through M1-M7 and reached NVIDIA NIM,")
        print("           which returned an HTTP 429 Too Many Requests response from the public free tier.")
    else:
        print(f"  Status : {response.status.value}")
        print(f"  Error  : {response.error_message}")
    print("=" * 80)

    return response


if __name__ == "__main__":
    prompt_arg = sys.argv[1] if len(sys.argv) > 1 else "Explain photosynthesis in two sentences."
    run_nvidia_live_demonstration(prompt=prompt_arg)
