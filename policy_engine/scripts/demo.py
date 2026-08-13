"""
Demonstration script for Module 6 — Policy Engine prototype.
Illustrates runtime governance policy evaluation, quota enforcement, and ordered fallback dispatch across 6 real-world scenarios.
"""

import sys
from pathlib import Path

# Setup Python sys.path to enable imports across modules
ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from capability_matcher.src import CapabilityMatcher
from rule_engine.src import RuleEngine, PolicyContext as RulePolicyContext
from ranking_engine.src import RankingEngine, RankingConfig
from src import PolicyEngine, PolicyContext, UsageState


def print_header(title: str) -> None:
    """Print styled section header."""
    print("\n" + "=" * 85)
    print(f" {title.upper()} ")
    print("=" * 85)


def print_decision_summary(decision) -> None:
    """Print formatted terminal output for a PolicyDecision."""
    print(f"\n  [REQUEST ID]            : {decision.request_id}")
    print(f"  [DISPATCH DECISION]     : {decision.decision}")
    print(f"  [FALLBACK USED]         : {'YES' if decision.fallback_used else 'NO'} (Attempts: {decision.fallback_attempts})")

    if decision.selected_model:
        sel = decision.selected_model
        print(f"  [SELECTED TARGET MODEL] : Rank #{decision.selected_rank} - {sel.model_id} ({sel.provider}) [Cost Tier: {sel.candidate.model_info.cost_tier}]")
    else:
        print("  [SELECTED TARGET MODEL] : None (Dispatch Rejected)")

    usage = decision.usage_state_snapshot
    print(f"  [USAGE SNAPSHOT]        : Budget Consumed={usage.get('budget_consumed', 0):.2f}, Daily Req={usage.get('daily_requests_used', 0)}, Daily Tokens={usage.get('daily_tokens_used', 0)}")

    print("\n  [CANDIDATE EVALUATION AUDIT TRACE (ORDERED RANK EVALUATION)]:")
    if not decision.evaluated_candidates:
        print("     (None - No ranked candidates available for evaluation)")
    else:
        for eval_item in decision.evaluated_candidates:
            status_str = "APPROVED" if eval_item.allowed else "REJECTED"
            reasons_str = "; ".join(eval_item.explanations) if eval_item.explanations else "Satisfied"
            print(f"     - Rank #{eval_item.rank_position:<2} [{eval_item.provider:<10}] {eval_item.model_id:<20} => [{status_str}] (Est Cost: {eval_item.estimated_cost:.1f} units) -> {reasons_str}")


def main() -> None:
    print_header("AI Model Router — Policy Engine Demonstration (Module 6)")

    # Initialize pipeline modules (Modules 3, 4, 5, 6)
    capability_matcher = CapabilityMatcher()
    rule_engine = RuleEngine()
    ranking_engine = RankingEngine()
    policy_engine = PolicyEngine()

    request_payload = {
        "request_id": "REQ-POL-001",
        "prompt": "Analyze code repository and design system architecture diagrams.",
        "attachments": [{"file_name": "architecture_diagram.png", "file_type": "image", "size_mb": 2.0}],
        "metadata": {"task_category": "Programming"},
        "expected_output": {"format": "code"}
    }
    complexity_profile = {"complexity": "MEDIUM", "complexity_score": 55, "confidence": 0.92}

    # Step 1: Run Modules 3 -> 4 -> 5 to produce pre-ranked candidate set
    cap_result = capability_matcher.match(request_payload, complexity_profile=complexity_profile)
    rule_result = rule_engine.evaluate(cap_result, context=RulePolicyContext(tenant_id="tenant_main"))
    ranking_result = ranking_engine.rank(rule_result, config=RankingConfig(cost_weight=0.30, latency_weight=0.25, suitability_weight=0.25, headroom_weight=0.20))

    # --- SCENARIO 1: Normal Dispatch Approval ---
    print_header("Scenario 1: Normal Dispatch Approval (Rank #1 Model Satisfies All Policies)")
    ctx_1 = PolicyContext(tenant_id="tenant_standard", budget_limit=50.0)
    res_1 = policy_engine.evaluate(ranking_result, context=ctx_1)
    print_decision_summary(res_1)

    # --- SCENARIO 2: Budget Exceeded -> Ordered Fallback Approval ---
    print_header("Scenario 2: Runtime Budget Exceeded -> Ordered Fallback Dispatch Approval")
    # Using suitability & headroom focused ranking where Rank #1 is high-cost (gemini-1.5-pro, 7.0 units) and Rank #2 is low-cost (gpt-4o-mini, 1.0 unit)
    suitability_ranking_result = ranking_engine.rank(rule_result, config=RankingConfig(suitability_weight=0.50, headroom_weight=0.30, cost_weight=0.10, latency_weight=0.10))
    ctx_2 = PolicyContext(tenant_id="tenant_budget_test", budget_limit=5.0)
    res_2 = policy_engine.evaluate(suitability_ranking_result, context=ctx_2)
    print_decision_summary(res_2)

    # --- SCENARIO 3: Request Quota Exceeded ---
    print_header("Scenario 3: Daily Request Quota Exceeded (Dispatch Rejected)")
    ctx_3 = PolicyContext(tenant_id="tenant_quota", daily_request_limit=10)
    usage_3 = UsageState(tenant_id="tenant_quota", daily_requests_used=10)
    res_3 = policy_engine.evaluate(ranking_result, context=ctx_3, usage_state=usage_3)
    print_decision_summary(res_3)

    # --- SCENARIO 4: Token Limit Exceeded ---
    print_header("Scenario 4: Token Quota Exceeded (Request Token Bound Reached)")
    ctx_4 = PolicyContext(tenant_id="tenant_tokens", max_tokens_per_request=2000, requested_tokens=5000)
    res_4 = policy_engine.evaluate(ranking_result, context=ctx_4)
    print_decision_summary(res_4)

    # --- SCENARIO 5: Rate Limit Exceeded ---
    print_header("Scenario 5: Request Rate Limit Exceeded (Time Window Cap)")
    ctx_5 = PolicyContext(tenant_id="tenant_rate", max_requests_per_window=5)
    usage_5 = UsageState(tenant_id="tenant_rate", requests_in_window=5)
    res_5 = policy_engine.evaluate(ranking_result, context=ctx_5, usage_state=usage_5)
    print_decision_summary(res_5)

    # --- SCENARIO 6: All Candidates Rejected / Fallback Limit Reached ---
    print_header("Scenario 6: All Ranked Candidates Rejected by Policy (Unsatisfiable Dispatch)")
    ctx_6 = PolicyContext(tenant_id="tenant_strict", budget_limit=0.5, fallback_enabled=True, max_fallback_attempts=1)
    res_6 = policy_engine.evaluate(ranking_result, context=ctx_6)
    print_decision_summary(res_6)

    print("\n" + "=" * 85)
    print(" Policy Engine Demonstration Complete ")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()
