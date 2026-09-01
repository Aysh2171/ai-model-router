"""
Verification script using NORMAL PipelineRouter and NORMAL AdapterRegistry
with RulePolicyContext(allowed_providers=["NVIDIA"]) and 0 retries.
"""

from gateway_router.src.orchestrator import PipelineRouter
from gateway_router.src.gateway import GatewayRouter
from gateway_router.src.config import GatewayConfig
from rule_engine.src import PolicyContext as RulePolicyContext

def main():
    # 1. Normal Pipeline and Default Registry
    config = GatewayConfig(max_retries=0)
    gateway = GatewayRouter(config=config)
    pipeline = PipelineRouter(gateway=gateway)

    # 2. Normal Request
    raw_request = {
        "request_id": "REQ-LIVE-NVIDIA-VERIFY",
        "prompt": "Give the code for bubble sort with comments.",
        "metadata": {"task_category": "Programming"},
        "expected_output": {"format": "code"},
        "conversation_context": {"turns": 0},
        "attachments": []
    }

    # 3. Rule Policy Context: Constrain to NVIDIA
    rule_context = RulePolicyContext(allowed_providers=["NVIDIA"])

    print("=" * 78)
    print("AI MODEL ROUTER: NORMAL PIPELINE LIVE NVIDIA INTEGRATION TEST")
    print("=" * 78)
    print(f"Prompt: '{raw_request['prompt']}'")
    print("Executing standard PipelineRouter (M1 -> M3 -> M4 -> M5 -> M6 -> M7)...")

    resp = pipeline.route_and_execute(raw_request, rule_context=rule_context)

    print("\n" + "=" * 78)
    print("ROUTING & EXECUTION TELEMETRY")
    print("=" * 78)
    print(f"Status            : {resp.status.value}")
    print(f"Decision State    : {resp.decision_state}")
    print(f"Selected Model    : {resp.model_id}")
    print(f"Selected Provider : {resp.provider}")
    print(f"Execution Mode    : {resp.execution_mode}")
    print(f"Retry Count       : {resp.retry_count}")
    print(f"Latency           : {resp.latency_ms:.2f} ms")
    print(f"Token Usage       : {resp.usage}")
    print(f"Adapter Name      : {resp.metadata.get('adapter_name')}")
    print("-" * 78)
    if resp.status.value == "SUCCESS" and resp.content:
        print("LIVE GENERATED CONTENT (HTTP 200):")
        print("-" * 78)
        print(resp.content.strip())
    else:
        print("EXECUTION OUTCOME:")
        print("-" * 78)
        print(f"Error Message: {resp.error_message}")
    print("=" * 78)

if __name__ == "__main__":
    main()
