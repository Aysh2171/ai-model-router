"""
AI Model Router — Interactive System Console & CLI Entry Point.
Primary human-facing terminal interface for operating and demonstrating the 8-module AI Model Router framework.

Execution Environment: Local Prototype (Zero Commercial API Calls / Zero Cloud Spending / Mock Execution Mode).
"""

import sys
import os
import uuid
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure project root and module directories are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
COMPLEXITY_DIR = PROJECT_ROOT / "complexity_predictor"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(COMPLEXITY_DIR) not in sys.path:
    sys.path.insert(0, str(COMPLEXITY_DIR))

from gateway_router.src.orchestrator import PipelineRouter
from gateway_router.src.models import GatewayRequest, GatewayResponse, ExecutionStatus, ExecutionMode
from gateway_router.src.gateway import GatewayRouter
from model_registry.src import ModelRegistry, ModelInfo
from capability_matcher.src import CapabilityMatcher, TASK_CATEGORY_ALIAS_MAP
from rule_engine.src import RuleEngine, PolicyContext as RulePolicyContext
from ranking_engine.src import RankingEngine, RankingConfig
from policy_engine.src import PolicyEngine, PolicyContext as RuntimePolicyContext, UsageState
from feedback_pipeline.src import FeedbackService, FeedbackAnalytics, SQLAlchemyFeedbackRepository, FeedbackConfig

# Category selection mapping: display label -> raw category string
AVAILABLE_CATEGORIES: List[Tuple[str, str]] = [
    ("General Question Answering", "General Question Answering"),
    ("Programming", "Programming"),
    ("Reasoning", "Reasoning"),
    ("Analysis & Review (Alias -> Reasoning)", "Analysis & Review"),
    ("Data Processing (Alias -> Data Extraction)", "Data Processing"),
    ("Document Processing (Alias -> Document Analysis)", "Document Processing"),
    ("System Architecture (Alias -> Software Architecture)", "System Architecture"),
    ("Multimodal (Alias -> Vision Analysis)", "Multimodal"),
    ("Mathematical Reasoning", "Mathematical Reasoning"),
    ("Code Review", "Code Review"),
    ("Vision Analysis", "Vision Analysis"),
]

EXPECTED_OUTPUT_FORMATS: List[Tuple[str, str]] = [
    ("Text", "text"),
    ("Code", "code"),
    ("JSON", "json"),
]


# =============================================================================
# CLI HELPER FUNCTIONS
# =============================================================================

def clear_screen() -> None:
    """Clear terminal screen if appropriate, otherwise print subtle separation."""
    # We do not force destructive terminal clear to preserve scrollback in PowerShell
    pass


def print_banner() -> None:
    """Display standard application header banner."""
    print("\n" + "=" * 78)
    print("                      AI MODEL ROUTER FRAMEWORK                       ")
    print("                      Interactive System Console                      ")
    print("=" * 78)
    print("  Execution Environment : Local Prototype")
    print("  Provider Execution    : MockProviderAdapter (Deterministic Local Simulation)")
    print("  External Calls        : ZERO Commercial API Calls | ZERO Cloud Spending")
    print("=" * 78)


def print_section(title: str) -> None:
    """Print formatted section header."""
    print("\n" + "-" * 78)
    print(f" {title.upper()}")
    print("-" * 78)


def prompt_string(prompt_text: str, default: str = "", allow_empty: bool = True) -> str:
    """Prompt user for text input with optional default value."""
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"{prompt_text}{suffix}: ").strip()
        if not val and default:
            return default
        if not val and not allow_empty:
            while not val:
                print("  Input cannot be empty. Please enter a value.")
                val = input(f"{prompt_text}{suffix}: ").strip()
                if not val and default:
                    return default
        return val
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user.")
        return default


def prompt_freeform(header_text: str = "Enter your prompt.", example_text: str = "") -> str:
    """Prompt user for a long free-form text with an example displayed separately."""
    print(f"\n{header_text}")
    if example_text:
        print("Press Enter without typing anything to use the example below.\n")
        print("Example:")
        print(f"  {example_text}\n")
    try:
        val = input("> ").strip()
        if not val and example_text:
            return example_text
        return val
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user.")
        return example_text


def prompt_int(prompt_text: str, default: int = 0, min_val: int = 0) -> int:
    """Prompt user for an integer with robust validation."""
    while True:
        raw = prompt_string(prompt_text, default=str(default), allow_empty=True)
        try:
            val = int(raw)
            if val < min_val:
                print(f"  Please enter a non-negative integer (>= {min_val}).")
                continue
            return val
        except ValueError:
            print("  Please enter a valid integer.")


def prompt_choice(prompt_text: str, options: List[str], default_idx: int = 1) -> int:
    """Display numbered list of options and prompt user for selection."""
    print(f"\n{prompt_text}")
    for idx, opt in enumerate(options, 1):
        print(f"  {idx}. {opt}")
    while True:
        raw = prompt_string(f"Select an option (1-{len(options)})", default=str(default_idx))
        try:
            choice = int(raw)
            if 1 <= choice <= len(options):
                return choice
            print(f"  Please select a number between 1 and {len(options)}.")
        except ValueError:
            print(f"  Please enter a valid number between 1 and {len(options)}.")


def print_gateway_response(resp: GatewayResponse) -> None:
    """Display structured summary of a GatewayResponse."""
    status_str = resp.status.value if hasattr(resp.status, "value") else str(resp.status)
    print("\n" + "=" * 78)
    print("                              ROUTING RESULT                              ")
    print("=" * 78)
    print(f"  Status            : {status_str}")
    print(f"  Decision State    : {resp.decision_state or 'N/A'}")
    print(f"  Selected Model    : {resp.model_id or 'None'}")
    print(f"  Provider          : {resp.provider or 'None'}")
    print(f"  Execution Mode    : {resp.execution_mode.upper()} (Local Simulation)")
    print(f"  Retry Count       : {resp.retry_count}")
    print(f"  Fallback Used     : {resp.fallback_used}")
    print(f"  Latency           : {resp.latency_ms:.2f} ms")

    if resp.usage:
        p_tok = resp.usage.get("prompt_tokens", 0)
        c_tok = resp.usage.get("completion_tokens", 0)
        t_tok = resp.usage.get("total_tokens", 0)
        print(f"  Token Usage       : Prompt={p_tok}, Completion={c_tok}, Total={t_tok}")
    else:
        print("  Token Usage       : N/A")

    if resp.error_message:
        print(f"  Error / Audit     : {resp.error_message}")

    print("-" * 78)
    print(" MODEL RESPONSE CONTENT")
    print("-" * 78)
    if resp.content:
        print(f"  {resp.content}")
    else:
        print("  [No response content generated — Execution blocked or failed]")
    print("=" * 78)


# =============================================================================
# CLI STATE & CONTEXT
# =============================================================================

class CLIContext:
    """Singleton context maintaining shared pipeline and telemetry service instances."""

    def __init__(self):
        self.pipeline = PipelineRouter()
        self.feedback_config = FeedbackConfig(database_url="sqlite:///:memory:")
        self.feedback_repo = SQLAlchemyFeedbackRepository(database_url=self.feedback_config.database_url)
        self.feedback_service = FeedbackService(repository=self.feedback_repo, config=self.feedback_config)
        self.feedback_analytics = FeedbackAnalytics(repository=self.feedback_repo)

    def record_response(self, resp: GatewayResponse, prompt: str, task_category: str = "General Prompting") -> Any:
        """Persist execution telemetry into Module 8 repository."""
        try:
            return self.feedback_service.record_gateway_response(
                response=resp,
                request_prompt=prompt,
                task_category=task_category
            )
        except Exception as e:
            # Telemetry logging failure should not crash CLI
            return None


# =============================================================================
# MENU HANDLERS
# =============================================================================

def handle_new_request(ctx: CLIContext) -> None:
    """Handle interactive creation and routing of a new request."""
    print_section("Option 1: Route a New Request")

    # 1. Request ID
    auto_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
    req_id = prompt_string("Request ID", default=auto_id)

    # 2. Prompt
    default_prompt = "Explain the difference between synchronous and asynchronous execution in Python."
    prompt = prompt_freeform("Enter your prompt.", example_text=default_prompt)

    # 3. Task Category
    cat_options = [c[0] for c in AVAILABLE_CATEGORIES] + ["Enter custom category...", "No category (default)"]
    cat_idx = prompt_choice("Select Task Category:", cat_options, default_idx=1)

    if cat_idx <= len(AVAILABLE_CATEGORIES):
        task_category = AVAILABLE_CATEGORIES[cat_idx - 1][1]
    elif cat_idx == len(AVAILABLE_CATEGORIES) + 1:
        task_category = prompt_string("Enter custom category name (e.g. QuantumTeleportation)", default="General")
    else:
        task_category = "General Prompting"

    # 4. Expected Output Format
    fmt_options = [f[0] for f in EXPECTED_OUTPUT_FORMATS] + ["Custom format..."]
    fmt_idx = prompt_choice("Select Expected Output Format:", fmt_options, default_idx=1)

    if fmt_idx <= len(EXPECTED_OUTPUT_FORMATS):
        out_format = EXPECTED_OUTPUT_FORMATS[fmt_idx - 1][1]
    else:
        out_format = prompt_string("Enter expected output format name", default="text")

    # 5. Conversation Context
    turns = prompt_int("Conversation turns history count", default=0, min_val=0)

    # Construct request payload
    request_payload: Dict[str, Any] = {
        "request_id": req_id,
        "prompt": prompt,
        "metadata": {"task_category": task_category},
        "expected_output": {"format": out_format},
        "conversation_context": {"turns": turns},
        "attachments": []
    }

    # Execute pipeline
    print("\nExecuting routing pipeline...")
    try:
        resp = ctx.pipeline.route_and_execute(request_payload)
        ctx.record_response(resp, prompt=prompt, task_category=task_category)
        print_gateway_response(resp)
    except Exception as e:
        print(f"\n[!] Routing error: {type(e).__name__}: {str(e)}")


def handle_attachment_request(ctx: CLIContext) -> None:
    """Handle routing of a request containing local file attachments."""
    print_section("Option 2: Route Request with File Attachment")

    auto_id = f"REQ-ATT-{uuid.uuid4().hex[:8].upper()}"
    req_id = prompt_string("Request ID", default=auto_id)

    default_prompt = "Analyze the attached document and summarize key architectural components."
    prompt = prompt_freeform("Enter your prompt.", example_text=default_prompt)

    # Task category (default to Document Processing / Multimodal)
    cat_options = [c[0] for c in AVAILABLE_CATEGORIES] + ["Enter custom category...", "No category"]
    cat_idx = prompt_choice("Select Task Category:", cat_options, default_idx=6)  # Default: Document Processing
    if cat_idx <= len(AVAILABLE_CATEGORIES):
        task_category = AVAILABLE_CATEGORIES[cat_idx - 1][1]
    elif cat_idx == len(AVAILABLE_CATEGORIES) + 1:
        task_category = prompt_string("Enter custom category", default="Document Processing")
    else:
        task_category = "Document Processing"

    # Attachment collection loop
    attachments: List[Dict[str, Any]] = []
    print("\n" + "-" * 40)
    print(" ATTACHMENT CONFIGURATION")
    print("-" * 40)
    print("  Note: File metadata (type and size) will be extracted locally.")
    print("  Execution is local mock simulation (no files are uploaded or sent over network).")

    while True:
        file_path_str = prompt_string("\nEnter local file path (or press Enter to finish adding files)")
        if not file_path_str:
            if not attachments:
                print("  No attachments added. Proceeding with text-only request.")
            break

        path = Path(file_path_str).expanduser()
        if not path.exists():
            print(f"  [!] File not found: '{file_path_str}'. Please enter a valid file path.")
            continue
        if path.is_dir():
            print(f"  [!] The supplied path '{file_path_str}' is a directory, not a file.")
            continue

        size_bytes = path.stat().st_size
        size_mb = max(0.01, round(size_bytes / (1024 * 1024), 2))
        ext = path.suffix.lstrip(".").lower() or "bin"

        att_entry = {
            "type": ext,
            "file_type": ext,
            "size_mb": size_mb,
            "filename": path.name,
            "path": str(path.resolve())
        }
        attachments.append(att_entry)
        print(f"  [+] Added Attachment [{len(attachments)}]: {path.name} (Type: {ext}, Size: {size_mb} MB)")

        another = prompt_string("Add another file? [y/N]", default="N").lower()
        if another not in ["y", "yes"]:
            break

    request_payload: Dict[str, Any] = {
        "request_id": req_id,
        "prompt": prompt,
        "metadata": {"task_category": task_category},
        "expected_output": {"format": "text"},
        "conversation_context": {"turns": 0},
        "attachments": attachments
    }

    print(f"\nExecuting routing pipeline with {len(attachments)} attachment(s)...")
    try:
        resp = ctx.pipeline.route_and_execute(request_payload)
        ctx.record_response(resp, prompt=prompt, task_category=task_category)
        print_gateway_response(resp)
    except Exception as e:
        print(f"\n[!] Routing error: {type(e).__name__}: {str(e)}")


def handle_diagnostics(ctx: CLIContext) -> None:
    """Perform step-by-step diagnostic execution exposing intermediate state across all 8 modules."""
    print_section("Option 3: Routing Diagnostics (Deep Module Inspection)")

    default_prompt = "Write a Python thread-safe LRU cache."
    prompt = prompt_freeform("Enter prompt for diagnostic trace.", example_text=default_prompt)
    
    cat_options = [c[0] for c in AVAILABLE_CATEGORIES] + ["Custom category..."]
    cat_idx = prompt_choice("Select Task Category:", cat_options, default_idx=2)
    if cat_idx <= len(AVAILABLE_CATEGORIES):
        task_category = AVAILABLE_CATEGORIES[cat_idx - 1][1]
    else:
        task_category = prompt_string("Enter custom category", default="Programming")

    raw_request = {
        "request_id": f"REQ-DIAG-{uuid.uuid4().hex[:6].upper()}",
        "prompt": prompt,
        "metadata": {"task_category": task_category},
        "expected_output": {"format": "code"},
        "conversation_context": {"turns": 1},
        "attachments": []
    }

    print("\n" + "=" * 78)
    print("                    INTERMEDIATE PIPELINE TRACE TRACE                     ")
    print("=" * 78)

    # 1. Module 1 — Complexity Predictor
    print("\n[ MODULE 1 — COMPLEXITY PREDICTOR ]")
    comp_profile = ctx.pipeline.predictor.predict_complexity(raw_request)
    print(f"  Predicted Complexity  : {comp_profile.get('complexity')}")
    print(f"  Complexity Score      : {comp_profile.get('complexity_score'):.2f} / 100")
    print(f"  Prediction Confidence : {comp_profile.get('confidence', 0.0):.2f}")
    if "probabilities" in comp_profile:
        print(f"  Class Probabilities   : {comp_profile['probabilities']}")

    # 2. Module 2 — Model Registry
    print("\n[ MODULE 2 — MODEL REGISTRY ]")
    all_models = ctx.pipeline.registry.get_all_models()
    providers = sorted(list(set(m.provider for m in all_models)))
    print(f"  Total Catalog Models  : {len(all_models)}")
    print(f"  Registered Providers  : {', '.join(providers)}")

    # 3. Module 3 — Capability Matcher
    print("\n[ MODULE 3 — CAPABILITY MATCHER ]")
    match_res = ctx.pipeline.matcher.match(raw_request, comp_profile)
    reqs = match_res.requirements
    print(f"  Required Modalities   : {sorted(list(reqs.required_modalities))}")
    print(f"  Required Use Cases    : {sorted(list(reqs.required_use_cases))}")
    print(f"  Min Context Window    : {reqs.min_context_window:,} tokens")
    print(f"  Satisfiable           : {match_res.is_satisfiable}")
    print(f"  Eligible Candidates   : {match_res.eligible_count} / {match_res.total_registered}")
    if match_res.eligible_candidates:
        cand_names = [c.model_id for c in match_res.eligible_candidates]
        print(f"  Eligible Model IDs    : {', '.join(cand_names[:6])}{'...' if len(cand_names) > 6 else ''}")
    if match_res.excluded_models and not match_res.is_satisfiable:
        print("  Sample Exclusion Reas.:")
        for exc in match_res.excluded_models[:2]:
            print(f"    * {exc.model_id}: {'; '.join(exc.exclusion_reasons)}")

    # 4. Module 4 — Rule Engine
    print("\n[ MODULE 4 — RULE ENGINE ]")
    rule_eval = ctx.pipeline.rule_engine.evaluate(match_res)
    print(f"  Allowed Candidates    : {rule_eval.allowed_count} / {len(match_res.eligible_candidates)}")
    print(f"  Policy Excluded Count : {rule_eval.policy_excluded_count}")

    # 5. Module 5 — Ranking Engine
    print("\n[ MODULE 5 — RANKING ENGINE ]")
    ranking_res = ctx.pipeline.ranking_engine.rank(rule_eval)
    print(f"  Ranked Candidates     : {ranking_res.total_candidates}")
    for rm in ranking_res.ranked_candidates[:4]:
        print(f"    Rank #{rm.rank_position}: {rm.model_id:<18} (Score: {rm.overall_score:.4f} | Provider: {rm.provider})")

    # 6. Module 6 — Policy Engine
    print("\n[ MODULE 6 — POLICY ENGINE ]")
    policy_dec = ctx.pipeline.policy_engine.evaluate(ranking_res)
    print(f"  Policy Decision State : {policy_dec.decision.value}")
    print(f"  Selected Model        : {policy_dec.selected_model.model_id if policy_dec.selected_model else 'None'}")
    print(f"  Fallback Attempts     : {policy_dec.fallback_attempts}")

    # 7. Module 7 — Gateway Router
    print("\n[ MODULE 7 — GATEWAY ROUTER ]")
    gw_req = GatewayRequest(
        request_id=raw_request["request_id"],
        prompt=prompt,
        policy_decision=policy_dec,
        metadata={"complexity_profile": comp_profile}
    )
    gw_resp = ctx.pipeline.gateway.execute(gw_req)
    print(f"  Execution Status      : {gw_resp.status.value}")
    print(f"  Execution Mode        : {gw_resp.execution_mode.upper()} (Local Simulation)")
    print(f"  Simulated Latency     : {gw_resp.latency_ms:.2f} ms")
    print(f"  Retry Count           : {gw_resp.retry_count}")

    # 8. Module 8 — Feedback Pipeline
    print("\n[ MODULE 8 — FEEDBACK PIPELINE ]")
    event = ctx.record_response(gw_resp, prompt=prompt, task_category=task_category)
    if event:
        print(f"  Telemetry Recorded    : SUCCESS")
        print(f"  Event Record ID       : {event.event_id}")
        print(f"  Database Storage      : SQLite In-Memory Repository")
    else:
        print("  Telemetry Recorded    : N/A")

    print("\n" + "=" * 78)
    print("                     DIAGNOSTIC TRACE COMPLETE                            ")
    print("=" * 78)


def handle_fault_demo(ctx: CLIContext) -> None:
    """Demonstrate Module 7 deterministic fault injection and retry state isolation."""
    print_section("Option 4: Fault Injection & Retry Demonstration")
    print("  Demonstrates MockProviderAdapter fault simulation & request-scoped retry isolation.")
    print("  Zero external API calls are made.")

    options = [
        "Transient Failure -> Retry -> Success (fail_mode='transient_then_success')",
        "Permanent Failure -> Immediate Abort (fail_mode='permanent')",
        "Timeout Glitch Simulation (fail_mode='timeout')",
        "Clean Execution (No faults)",
        "Request-Scoped State Isolation Test (REQ-A vs REQ-B on same adapter)",
        "Back to Main Menu"
    ]
    choice = prompt_choice("Select Fault Simulation Scenario:", options, default_idx=1)

    if choice == 1:
        req_id = f"REQ-SIM-RETRY-{uuid.uuid4().hex[:6].upper()}"
        print(f"\n[+] Executing Request '{req_id}' with 'transient_then_success' (threshold=1)...")
        print("    Expected: Attempt 1 fails with transient glitch -> Gateway retries -> Attempt 2 succeeds.")
        resp = ctx.pipeline.route_and_execute(
            raw_request={"request_id": req_id, "prompt": "Test fault injection retry", "metadata": {"task_category": "Programming"}},
            simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 1}
        )
        print_gateway_response(resp)

    elif choice == 2:
        req_id = f"REQ-SIM-PERM-{uuid.uuid4().hex[:6].upper()}"
        print(f"\n[+] Executing Request '{req_id}' with 'permanent' error...")
        print("    Expected: Attempt 1 fails with 400 Bad Request -> Gateway aborts immediately (0 retries).")
        resp = ctx.pipeline.route_and_execute(
            raw_request={"request_id": req_id, "prompt": "Test permanent abort", "metadata": {"task_category": "Programming"}},
            simulation_options={"fail_mode": "permanent"}
        )
        print_gateway_response(resp)

    elif choice == 3:
        req_id = f"REQ-SIM-TIMEOUT-{uuid.uuid4().hex[:6].upper()}"
        print(f"\n[+] Executing Request '{req_id}' with 'timeout'...")
        print("    Expected: Gateway retries up to max_retries and returns TIMEOUT.")
        resp = ctx.pipeline.route_and_execute(
            raw_request={"request_id": req_id, "prompt": "Test timeout", "metadata": {"task_category": "Programming"}},
            simulation_options={"fail_mode": "timeout"}
        )
        print_gateway_response(resp)

    elif choice == 4:
        req_id = f"REQ-SIM-CLEAN-{uuid.uuid4().hex[:6].upper()}"
        print(f"\n[+] Executing Request '{req_id}' with clean simulation...")
        resp = ctx.pipeline.route_and_execute(
            raw_request={"request_id": req_id, "prompt": "Clean prompt execution", "metadata": {"task_category": "General Prompting"}}
        )
        print_gateway_response(resp)

    elif choice == 5:
        print("\n[+] Executing Request-Scoped State Isolation Test...")
        print("    Context: Running two distinct requests sequentially on the SAME adapter instance.")
        print("    Both requests configure fail_count_before_success=1.")
        
        req_a_id = "REQ-ISOLATION-A"
        req_b_id = "REQ-ISOLATION-B"

        print(f"\n  [Step 1] Executing Request A: '{req_a_id}'...")
        resp_a = ctx.pipeline.route_and_execute(
            raw_request={"request_id": req_a_id, "prompt": "Prompt A", "metadata": {"task_category": "Programming"}},
            simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 1}
        )
        print(f"           Result A: Status={resp_a.status.value}, Retries={resp_a.retry_count}")

        print(f"\n  [Step 2] Executing Request B: '{req_b_id}' on the SAME adapter...")
        resp_b = ctx.pipeline.route_and_execute(
            raw_request={"request_id": req_b_id, "prompt": "Prompt B", "metadata": {"task_category": "Programming"}},
            simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 1}
        )
        print(f"           Result B: Status={resp_b.status.value}, Retries={resp_b.retry_count}")

        isolation_passed = (resp_a.retry_count == 1 and resp_b.retry_count == 1 and 
                            resp_a.status == ExecutionStatus.SUCCESS and resp_b.status == ExecutionStatus.SUCCESS)

        print("\n" + "-" * 50)
        if isolation_passed:
            print("  STATE ISOLATION VERDICT: [PASS] (Zero State Leakage)")
            print("  Explanation: Request B independently experienced Attempt 1 failure and Attempt 2 retry,")
            print("               proving it did NOT inherit Request A's completed state counter.")
        else:
            print("  STATE ISOLATION VERDICT: [FAIL] (State leakage detected)")
        print("-" * 50)


def handle_model_catalogue(ctx: CLIContext) -> None:
    """View and search the 17-model catalog in Module 2 Model Registry."""
    print_section("Option 5: View Model Catalogue")

    registry = ctx.pipeline.registry
    models = registry.get_all_models()
    print(f"Total Registered Foundation Models: {len(models)}")

    while True:
        print("\n" + "=" * 78)
        print(f"{'Model ID':<22} {'Provider':<12} {'Cost Tier':<10} {'Latency Tier':<12} {'Context':<10} {'Status':<8}")
        print("-" * 78)
        for m in models:
            ctx_str = f"{m.context_window // 1000}k" if m.context_window >= 1000 else str(m.context_window)
            print(f"{m.model_id:<22} {m.provider:<12} {m.cost_tier:<10} {m.latency_tier:<12} {ctx_str:<10} {m.status:<8}")
        print("=" * 78)

        sub_opts = [
            "View Full Details for a Specific Model",
            "Filter Models by Provider",
            "Filter Models by Cost Tier",
            "Filter Models by Latency Tier",
            "Search Models (Keyword Search)",
            "Reset Filters (Show All Models)",
            "Back to Main Menu"
        ]
        sub_choice = prompt_choice("Catalogue Actions:", sub_opts, default_idx=7)

        if sub_choice == 1:
            mid = prompt_string("Enter Model ID to inspect", default="gpt-4o")
            m = registry.get_model(mid)
            if m:
                print("\n" + "-" * 60)
                print(f" MODEL METADATA: {m.display_name} ({m.model_id})")
                print("-" * 60)
                print(f"  Provider             : {m.provider}")
                print(f"  Family               : {m.family}")
                print(f"  Status               : {m.status} (Default: {m.is_default})")
                print(f"  Cost Tier            : {m.cost_tier}")
                print(f"  Latency Tier         : {m.latency_tier}")
                print(f"  Context Window       : {m.context_window:,} tokens")
                print(f"  Max Output Tokens    : {m.max_output_tokens:,} tokens")
                print(f"  Supported Modalities : {', '.join(m.supported_modalities)}")
                print(f"  Supported Use Cases  : {', '.join(m.supported_use_cases)}")
                print(f"  Capabilities         : Vision={m.supports_vision}, Code={m.supports_code}, FunctionCalling={m.supports_function_calling}")
                print(f"  Description          : {m.description}")
                print("-" * 60)
            else:
                print(f"  [!] Model ID '{mid}' not found in registry.")

        elif sub_choice == 2:
            prov = prompt_string("Enter provider name (e.g. OpenAI, Anthropic, Google, Meta)", default="OpenAI")
            filtered = registry.get_models_by_provider(prov)
            if filtered:
                models = filtered
                print(f"  Found {len(models)} model(s) for provider '{prov}'.")
            else:
                print(f"  No models found for provider '{prov}'.")

        elif sub_choice == 3:
            tier_opts = ["low", "medium", "high", "premium"]
            t_idx = prompt_choice("Select Cost Tier:", tier_opts, default_idx=1)
            tier = tier_opts[t_idx - 1]
            models = registry.get_models_by_cost_tier(tier)
            print(f"  Found {len(models)} model(s) matching cost tier '{tier}'.")

        elif sub_choice == 4:
            lat_opts = ["fast", "medium", "slow"]
            l_idx = prompt_choice("Select Latency Tier:", lat_opts, default_idx=1)
            tier = lat_opts[l_idx - 1]
            models = registry.get_models_by_latency_tier(tier)
            print(f"  Found {len(models)} model(s) matching latency tier '{tier}'.")

        elif sub_choice == 5:
            q = prompt_string("Enter search keyword", default="vision")
            models = registry.search_models(q)
            print(f"  Search for '{q}' returned {len(models)} model(s).")

        elif sub_choice == 6:
            models = registry.get_all_models()
            print("  Catalogue filter reset. Showing all 17 models.")

        elif sub_choice == 7:
            break


def handle_full_demo(ctx: CLIContext) -> None:
    """Run the complete 8-module demonstration script from feedback_pipeline."""
    print_section("Option 6: Run Complete System Demonstration")
    print("  Executing predefined multi-scenario demonstration from 'feedback_pipeline/scripts/demo.py'.")
    print("  Covers: Normal Routing, Policy Fallback, Policy Rejection, Feedback Attachment, Analytics Scorecard.")
    print("-" * 78)

    try:
        import feedback_pipeline.scripts.demo as feedback_demo
        feedback_demo.main()
    except Exception as e:
        print(f"[!] Error running system demonstration: {type(e).__name__}: {str(e)}")


# =============================================================================
# MAIN INTERACTIVE LOOP
# =============================================================================

def main_menu() -> None:
    """Main terminal loop for the interactive console."""
    ctx = CLIContext()

    while True:
        print_banner()
        print("\nMAIN MENU:")
        print("  1. Route a New Request")
        print("  2. Route Request with File Attachment")
        print("  3. Routing Diagnostics (Deep Step-by-Step Module Trace)")
        print("  4. Fault Injection & Retry Demonstration (Gateway Resilience)")
        print("  5. View Model Catalogue (17 Registered Foundation Models)")
        print("  6. Run Complete System Demonstration (5 Predefined Scenarios)")
        print("  7. Exit Console")
        print("-" * 78)

        choice_str = prompt_string("Select an option (1-7)", default="1")
        try:
            choice = int(choice_str)
        except ValueError:
            print("  [!] Please enter a valid number between 1 and 7.")
            input("\nPress Enter to continue...")
            continue

        if choice == 1:
            handle_new_request(ctx)
        elif choice == 2:
            handle_attachment_request(ctx)
        elif choice == 3:
            handle_diagnostics(ctx)
        elif choice == 4:
            handle_fault_demo(ctx)
        elif choice == 5:
            handle_model_catalogue(ctx)
        elif choice == 6:
            handle_full_demo(ctx)
        elif choice == 7:
            print("\n" + "=" * 78)
            print("  Thank you for using the AI Model Router Framework.")
            print("  Execution completed locally (Zero commercial API calls / Zero cloud spending).")
            print("=" * 78 + "\n")
            sys.exit(0)
        else:
            print(f"  [!] Invalid choice '{choice}'. Please select a number from 1 to 7.")

        input("\nPress Enter to return to the main menu...")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nSession terminated by user. Goodbye.")
        sys.exit(0)
