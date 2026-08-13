"""
Demonstration script for Module 5 — Ranking Engine prototype.
Illustrates preference-based scoring and model candidate ordering across 6 real-world scenarios.
"""

import sys
from pathlib import Path

# Setup Python sys.path to enable imports across modules
ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from capability_matcher.src import CapabilityMatcher
from rule_engine.src import RuleEngine, PolicyContext
from src import RankingEngine, RankingConfig


def print_header(title: str) -> None:
    """Print styled section header."""
    print("\n" + "=" * 85)
    print(f" {title.upper()} ")
    print("=" * 85)


def print_ranking_summary(result) -> None:
    """Print formatted terminal output for a RankingResult."""
    print(f"\n  [REQUEST ID]            : {result.request_id}")
    print(f"  [RANKING SATISFIABLE]   : {'YES (True)' if result.is_satisfiable else 'NO (False - Empty Candidates)'}")
    print(f"  [TOTAL INPUT CANDIDATES]: {result.total_candidates} Allowed Candidates")

    if result.selected_model:
        sel = result.selected_model
        print(f"  [TOP SELECTED MODEL]    : #{sel.rank_position} {sel.model_id} ({sel.provider}) - Score: {sel.overall_score:.4f}")
    else:
        print("  [TOP SELECTED MODEL]    : None")

    policy = result.ranking_policy_applied
    weights_str = f"Cost={policy.get('cost_weight', 0):.2f}, Latency={policy.get('latency_weight', 0):.2f}, Suitability={policy.get('suitability_weight', 0):.2f}, Headroom={policy.get('headroom_weight', 0):.2f}"
    print(f"  [APPLIED WEIGHTS]       : {weights_str}")

    print("\n  [RANKED CANDIDATES ORDER]:")
    if not result.ranked_candidates:
        print("     (None - No candidates available to rank)")
    else:
        print(f"     {'RANK':<5} | {'MODEL ID':<22} | {'PROVIDER':<10} | {'SCORE':<7} | {'COST SCR':<8} | {'LAT SCR':<8} | {'SUIT SCR':<8} | {'HEADROOM SCR':<8}")
        print("     " + "-" * 95)
        for model in result.ranked_candidates:
            cs = model.component_scores
            print(
                f"     #{model.rank_position:<4} | {model.model_id:<22} | {model.provider:<10} | "
                f"{model.overall_score:<7.4f} | {cs.get('cost', 0):<8.2f} | {cs.get('latency', 0):<8.2f} | "
                f"{cs.get('suitability', 0):<8.2f} | {cs.get('headroom', 0):<8.2f}"
            )


def main() -> None:
    print_header("AI Model Router — Ranking Engine Demonstration (Module 5)")

    capability_matcher = CapabilityMatcher()
    rule_engine = RuleEngine()
    ranking_engine = RankingEngine()

    # Base Request Payload (Coding + Vision Task)
    request_payload = {
        "request_id": "REQ-RANK-001",
        "prompt": "Analyze code repository and design system architecture diagrams.",
        "attachments": [{"file_name": "architecture_diagram.png", "file_type": "image", "size_mb": 2.0}],
        "metadata": {"task_category": "Programming"},
        "expected_output": {"format": "code"}
    }
    complexity_profile = {"complexity": "MEDIUM", "complexity_score": 55, "confidence": 0.92}

    # Step 1: Run Module 3 (Feasibility Matcher)
    cap_result = capability_matcher.match(request_payload, complexity_profile=complexity_profile)

    # Step 2: Run Module 4 (Rule Engine) with standard policy
    pol_ctx = PolicyContext(tenant_id="tenant_main", tenant_tier="standard")
    rule_result = rule_engine.evaluate(cap_result, context=pol_ctx)

    # --- SCENARIO 1: Balanced Ranking Policy ---
    print_header("Scenario 1: Balanced Ranking Policy (Cost: 0.30, Latency: 0.25, Suitability: 0.25, Headroom: 0.20)")
    cfg_1 = RankingConfig(cost_weight=0.30, latency_weight=0.25, suitability_weight=0.25, headroom_weight=0.20)
    res_1 = ranking_engine.rank(rule_result, config=cfg_1)
    print_ranking_summary(res_1)

    # --- SCENARIO 2: Cost-Focused Ranking Policy ---
    print_header("Scenario 2: Cost-Focused Ranking Policy (Cost: 0.70, Latency: 0.10, Suitability: 0.10, Headroom: 0.10)")
    cfg_2 = RankingConfig(cost_weight=0.70, latency_weight=0.10, suitability_weight=0.10, headroom_weight=0.10)
    res_2 = ranking_engine.rank(rule_result, config=cfg_2)
    print_ranking_summary(res_2)

    # --- SCENARIO 3: Latency-Focused Ranking Policy ---
    print_header("Scenario 3: Latency-Focused Ranking Policy (Latency: 0.70, Cost: 0.10, Suitability: 0.10, Headroom: 0.10)")
    cfg_3 = RankingConfig(latency_weight=0.70, cost_weight=0.10, suitability_weight=0.10, headroom_weight=0.10)
    res_3 = ranking_engine.rank(rule_result, config=cfg_3)
    print_ranking_summary(res_3)

    # --- SCENARIO 4: Suitability & Context-Focused Policy ---
    print_header("Scenario 4: Suitability & Context-Focused Policy (Suitability: 0.50, Headroom: 0.30, Cost/Latency: 0.10)")
    cfg_4 = RankingConfig(suitability_weight=0.50, headroom_weight=0.30, cost_weight=0.10, latency_weight=0.10)
    res_4 = ranking_engine.rank(rule_result, config=cfg_4)
    print_ranking_summary(res_4)

    # --- SCENARIO 5: Deterministic Tie-Breaking Demonstration ---
    print_header("Scenario 5: Deterministic Tie-Breaking Order Verification")
    cfg_5 = RankingConfig(cost_weight=0.25, latency_weight=0.25, suitability_weight=0.25, headroom_weight=0.25)
    res_5 = ranking_engine.rank(rule_result, config=cfg_5)
    print_ranking_summary(res_5)

    # --- SCENARIO 6: Unsatisfiable / Empty Candidates State ---
    print_header("Scenario 6: Unsatisfiable Policy State (Empty Candidate Ranking)")
    strict_pol = PolicyContext(allowed_providers={"NonExistentProvider"})
    empty_rule_result = rule_engine.evaluate(cap_result, context=strict_pol)
    res_6 = ranking_engine.rank(empty_rule_result)
    print_ranking_summary(res_6)

    print("\n" + "=" * 85)
    print(" Ranking Engine Demonstration Complete ")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()
