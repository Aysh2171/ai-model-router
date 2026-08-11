"""
Demonstration script for Module 4 — Rule Engine prototype.
Illustrates hard-constraint organizational policy filtering across 6 real-world governance scenarios.
"""

import sys
from pathlib import Path

# Setup Python sys.path to enable imports across modules
ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from capability_matcher.src.matcher import CapabilityMatcher
from src.context import PolicyContext
from src.engine import RuleEngine


def print_header(title: str) -> None:
    """Print styled section header."""
    print("\n" + "=" * 85)
    print(f" {title.upper()} ")
    print("=" * 85)


def print_result_summary(result) -> None:
    """Print formatted terminal output for a RuleEvaluationResult."""
    print(f"\n  [REQUEST ID]            : {result.request_id}")
    print(f"  [RULE SATISFIABLE]      : {'YES (True)' if result.is_rule_satisfiable else 'NO (False - Unsatisfiable)'}")
    print(f"  [TENANT / CONTEXT]      : Tenant='{result.policy_context.tenant_id}', Tier='{result.policy_context.tenant_tier}', Region='{result.policy_context.data_residency_region or 'None'}'")
    print(f"  [FEASIBILITY TO POLICY] : {result.allowed_count} Allowed / {result.policy_excluded_count} Policy-Excluded (out of {result.total_feasible_input} feasible inputs)")
    print(f"  [APPLIED POLICIES]      : {', '.join(result.applied_policies)}")

    print("\n  [ALLOWED CANDIDATE MODELS]:")
    if not result.allowed_candidates:
        print("     (None - All feasible candidates rejected by organizational policy rules)")
    else:
        print(f"     {'MODEL ID':<22} | {'PROVIDER':<10} | {'FAMILY':<10} | {'COST':<7} | {'LATENCY':<7} | {'STATUS':<9}")
        print("     " + "-" * 80)
        for cand in result.allowed_candidates:
            info = cand.model_info
            print(f"     {cand.model_id:<22} | {cand.provider:<10} | {cand.family:<10} | {info.cost_tier:<7} | {info.latency_tier:<7} | {info.status:<9}")

    print("\n  [POLICY EXCLUDED CANDIDATES (MODULE 4 AUDIT)]:")
    if not result.policy_excluded_candidates:
        print("     (None - All feasible candidates satisfied organizational rules)")
    else:
        for excl in result.policy_excluded_candidates:
            violations_str = "; ".join(excl.violation_details)
            rules_str = ", ".join(excl.failed_rule_names)
            print(f"     - [{excl.provider}] {excl.model_id:<20} => REJECTED by [{rules_str}]: {violations_str}")

    print("\n  [CAPABILITY EXCLUDED MODELS (MODULE 3 PRESERVED AUDIT SAMPLE)]:")
    if not result.capability_excluded_models:
        print("     (None)")
    else:
        for excl in result.capability_excluded_models[:3]:
            reasons_str = "; ".join(excl.exclusion_reasons)
            print(f"     - [{excl.provider}] {excl.model_id:<20} => CAPABILITY EXCLUDED: {reasons_str}")
        if len(result.capability_excluded_models) > 3:
            print(f"     ... and {len(result.capability_excluded_models) - 3} more models excluded at Stage 3 Capability Match.")


def main() -> None:
    print_header("AI Model Router — Rule Engine Demonstration (Module 4)")

    capability_matcher = CapabilityMatcher()
    rule_engine = RuleEngine()

    # Base Feasible Input Payload (Vision + Code Request)
    request_payload = {
        "request_id": "REQ-GOV-001",
        "prompt": "Analyze UI screenshot mockup and generate React code.",
        "attachments": [{"file_name": "ui_mockup.png", "file_type": "image", "size_mb": 1.5}],
        "metadata": {"task_category": "Programming"},
        "expected_output": {"format": "code"}
    }
    complexity_profile = {"complexity": "MEDIUM", "complexity_score": 45, "confidence": 0.90}

    # Step 1: Run Module 3 to produce technically feasible candidate set
    cap_result = capability_matcher.match(request_payload, complexity_profile=complexity_profile)

    # --- SCENARIO 1: Standard Policy Pass ---
    print_header("Scenario 1: Standard Organizational Policy (Default Rules Pass)")
    ctx_1 = PolicyContext(tenant_id="tenant_alpha", tenant_tier="standard")
    res_1 = rule_engine.evaluate(cap_result, context=ctx_1)
    print_result_summary(res_1)

    # --- SCENARIO 2: Disallowed Provider Blacklist ---
    print_header("Scenario 2: Disallowed Provider Restriction (Blacklisting 'Meta' and 'Google')")
    ctx_2 = PolicyContext(
        tenant_id="tenant_beta",
        tenant_tier="standard",
        disallowed_providers={"Meta", "Google"}
    )
    res_2 = rule_engine.evaluate(cap_result, context=ctx_2)
    print_result_summary(res_2)

    # --- SCENARIO 3: Strict Data Residency Constraint (EU Region) ---
    print_header("Scenario 3: Strict Data Residency Policy (EU Data Sovereign Requirement)")
    ctx_3 = PolicyContext(
        tenant_id="tenant_eu_corp",
        tenant_tier="enterprise",
        data_residency_region="EU"
    )
    res_3 = rule_engine.evaluate(cap_result, context=ctx_3)
    print_result_summary(res_3)

    # --- SCENARIO 4: Security & Regulatory Compliance (HIPAA / SOC2 Required) ---
    print_header("Scenario 4: Security & Regulatory Compliance Policy (HIPAA + SOC2 Required)")
    ctx_4 = PolicyContext(
        tenant_id="tenant_health",
        tenant_tier="enterprise",
        required_compliance_tags={"hipaa", "soc2"}
    )
    res_4 = rule_engine.evaluate(cap_result, context=ctx_4)
    print_result_summary(res_4)

    # --- SCENARIO 5: Cost Tier Cap Governance ---
    print_header("Scenario 5: Cost Governance Policy (Max Cost Tier = 'low')")
    ctx_5 = PolicyContext(
        tenant_id="tenant_budget",
        tenant_tier="standard",
        max_cost_tier="low"
    )
    res_5 = rule_engine.evaluate(cap_result, context=ctx_5)
    print_result_summary(res_5)

    # --- SCENARIO 6: Complete Policy Exclusion (Unsatisfiable State) ---
    print_header("Scenario 6: Unsatisfiable Policy Combination (Restricted Provider Whitelist)")
    ctx_6 = PolicyContext(
        tenant_id="tenant_restricted",
        tenant_tier="standard",
        allowed_providers={"NonExistentProvider"}
    )
    res_6 = rule_engine.evaluate(cap_result, context=ctx_6)
    print_result_summary(res_6)

    print("\n" + "=" * 85)
    print(" Rule Engine Demonstration Complete ")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()
