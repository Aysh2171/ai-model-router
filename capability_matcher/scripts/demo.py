"""
Demonstration script for the Capability Matcher prototype.
Illustrates hard-constraint feasibility filtering across 5 distinct real-world AI request scenarios.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from src.matcher import CapabilityMatcher


def print_header(title: str) -> None:
    """Print styled section header."""
    print("\n" + "=" * 80)
    print(f" {title.upper()} ")
    print("=" * 80)


def print_result_summary(result) -> None:
    """Print formatted terminal output for a CapabilityMatchResult."""
    print(f"\n  [REQUEST ID]     : {result.request_id}")
    print(f"  [SATISFIABLE]    : {'YES (True)' if result.is_satisfiable else 'NO (False - Unsatisfiable)'}")
    print(f"  [CATALOG SUMMARY]: {result.eligible_count} Eligible / {result.excluded_count} Excluded (out of {result.total_registered} registered models)")
    
    req_dict = result.requirements.to_dict()
    print(f"  [EXTRACTED REQUIREMENTS]:")
    print(f"     - Modalities       : {req_dict['required_modalities']}")
    print(f"     - Min Context      : {req_dict['min_context_window']:,} tokens")
    print(f"     - Min Output Limit : {req_dict['min_max_output_tokens']:,} tokens")
    print(f"     - Use Cases        : {req_dict['required_use_cases']}")
    print(f"     - Capability Flags : {req_dict['required_capabilities']}")

    print("\n  [ELIGIBLE CANDIDATE MODELS]:")
    if not result.eligible_candidates:
        print("     (None - Request cannot be satisfied by any registered model)")
    else:
        print(f"     {'MODEL ID':<22} | {'PROVIDER':<10} | {'FAMILY':<10} | {'HEADROOM':<12} | {'COST':<7} | {'LATENCY':<7}")
        print("     " + "-" * 78)
        for cand in result.eligible_candidates:
            headroom_str = f"+{cand.context_headroom // 1000}k tokens"
            info = cand.model_info
            print(f"     {cand.model_id:<22} | {cand.provider:<10} | {cand.family:<10} | {headroom_str:<12} | {info.cost_tier:<7} | {info.latency_tier:<7}")

    print("\n  [EXCLUDED MODELS AUDIT SAMPLE]:")
    if not result.excluded_models:
        print("     (None - All models satisfied technical requirements)")
    else:
        # Show first 4 excluded models as telemetry audit sample
        for excl in result.excluded_models[:4]:
            reasons_str = "; ".join(excl.exclusion_reasons)
            print(f"     - [{excl.provider}] {excl.model_id:<20} => REJECTED: {reasons_str}")
        if len(result.excluded_models) > 4:
            print(f"     ... and {len(result.excluded_models) - 4} more models excluded.")


def main() -> None:
    print_header("AI Model Router — Capability Matcher Demonstration")
    matcher = CapabilityMatcher()

    # --- SCENARIO 1: Basic Text Prompt ---
    print_header("Scenario 1: Basic Text Prompt (General Question Answering)")
    request_1 = {
        "request_id": "REQ-TEXT-001",
        "prompt": "What is the capital of France and what is its population?",
        "metadata": {"task_category": "General Question Answering"},
        "expected_output": {"format": "short_answer"}
    }
    complexity_1 = {"complexity": "LOW", "complexity_score": 15, "confidence": 0.95}
    res_1 = matcher.match(request_1, complexity_profile=complexity_1)
    print_result_summary(res_1)

    # --- SCENARIO 2: Image Attachment + Programming Query ---
    print_header("Scenario 2: Multimodal Image Attachment + Programming Request")
    request_2 = {
        "request_id": "REQ-VISION-CODE-002",
        "prompt": "Inspect this UI mockup screenshot and write a React Tailwind component matching the design.",
        "attachments": [
            {"file_name": "dashboard_mockup.png", "file_type": "image", "size_mb": 2.4}
        ],
        "metadata": {"task_category": "Programming"},
        "expected_output": {"format": "code"}
    }
    complexity_2 = {"complexity": "MEDIUM", "complexity_score": 52, "confidence": 0.88}
    res_2 = matcher.match(request_2, complexity_profile=complexity_2)
    print_result_summary(res_2)

    # --- SCENARIO 3: Massive Document Analysis (High Context Window Required) ---
    print_header("Scenario 3: Massive Document Analysis (Requires 250k+ Context Window)")
    request_3 = {
        "request_id": "REQ-LONG-DOC-003",
        "prompt": "Perform a comprehensive audit across all attached legal contracts and report GDPR compliance violations.",
        "attachments": [
            {"file_name": "contracts_bundle.pdf", "file_type": "pdf", "size_mb": 45.0}
        ],
        "conversation_context": {"turns": 12},
        "metadata": {"task_category": "Document Analysis"},
        "expected_output": {"format": "comparative_report"}
    }
    complexity_3 = {"complexity": "HIGH", "complexity_score": 85, "confidence": 0.92}
    res_3 = matcher.match(request_3, complexity_profile=complexity_3, min_context_window=250000)
    print_result_summary(res_3)

    # --- SCENARIO 4: Function Calling + JSON Schema Output Request ---
    print_header("Scenario 4: Function Calling & Structured JSON Output Requirement")
    request_4 = {
        "request_id": "REQ-TOOLS-JSON-004",
        "prompt": "Extract customer entities from the query and execute the search_database tool.",
        "tools": [{"name": "search_database", "description": "Queries customer DB"}],
        "metadata": {"task_category": "Data Extraction"},
        "expected_output": {"format": "json"}
    }
    complexity_4 = {"complexity": "MEDIUM", "complexity_score": 48, "confidence": 0.84}
    res_4 = matcher.match(request_4, complexity_profile=complexity_4)
    print_result_summary(res_4)

    # --- SCENARIO 5: Unsatisfiable Request ---
    print_header("Scenario 5: Unsatisfiable Extreme Request (5 Million Tokens Context)")
    request_5 = {
        "request_id": "REQ-UNSAT-005",
        "prompt": "Analyze entire raw repository zip dump.",
        "metadata": {"task_category": "Software Architecture"}
    }
    res_5 = matcher.match(request_5, min_context_window=5000000)
    print_result_summary(res_5)

    # --- SCENARIO 6: Stage 1 Lifecycle Status Filtering (allow_preview=False) ---
    print_header("Scenario 6: Stage 1 Lifecycle Status Filtering (allow_preview=False)")
    request_6 = {
        "request_id": "REQ-STATUS-006",
        "prompt": "Design high-level microservice system architecture.",
        "metadata": {"task_category": "System Design"}
    }
    res_6 = matcher.match(request_6, allow_preview=False)
    print_result_summary(res_6)

    print("\n" + "=" * 80)
    print(" Capability Matcher Demonstration Complete ")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
