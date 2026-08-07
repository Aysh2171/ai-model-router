"""
Demonstration script for the Model Registry prototype.
Illustrates loading model metadata, executing lookup queries, family filtering, keyword search, and flexible criteria filtering.
"""

import sys
from pathlib import Path

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.model_registry import ModelRegistry


def print_section(title: str) -> None:
    """Print a styled section header for terminal demonstration output."""
    print("\n" + "=" * 80)
    print(f" {title.upper()} ")
    print("=" * 80)


def print_model_table(models) -> None:
    """Print formatted terminal table of ModelInfo instances."""
    if not models:
        print("  (No matching models found)")
        return

    header = f"  {'MODEL ID':<22} | {'PROVIDER':<10} | {'FAMILY':<10} | {'COST':<7} | {'LATENCY':<7} | {'CONTEXT':<9} | {'STATUS':<10}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for m in models:
        context_str = f"{m.context_window // 1000}k" if m.context_window >= 1000 else str(m.context_window)
        print(f"  {m.model_id:<22} | {m.provider:<10} | {m.family:<10} | {m.cost_tier:<7} | {m.latency_tier:<7} | {context_str:<9} | {m.status:<10}")
    print("-" * len(header))


def main() -> None:
    print_section("AI Model Router — Model Registry Demonstration")

    # 1. Initialize Registry
    registry = ModelRegistry()
    print(f"\n[INFO] Loaded Model Registry Catalog successfully.")
    print(f"  Total Registered Models : {registry.count_models()}")
    print(f"  Available Providers ({len(registry.list_providers())})   : {', '.join(registry.list_providers())}")
    print(f"  Model Families ({len(registry.list_families())})      : {', '.join(registry.list_families())}")

    # 2. Lookup Specific Model Metadata
    print_section("1. Specific Model Lookup (model_id: 'claude-3.5-sonnet')")
    claude = registry.get_model("claude-3.5-sonnet")
    if claude:
        print(f"  Display Name    : {claude.display_name}")
        print(f"  Provider        : {claude.provider}")
        print(f"  Family          : {claude.family}")
        print(f"  Description     : {claude.description}")
        print(f"  Context Window  : {claude.context_window:,} tokens")
        print(f"  Max Output      : {claude.max_output_tokens:,} tokens")
        print(f"  Cost / Latency  : Cost Tier={claude.cost_tier.upper()}, Latency Tier={claude.latency_tier.upper()}")
        print(f"  Modalities      : {', '.join(claude.supported_modalities)}")
        print(f"  Tags            : {', '.join(claude.tags)}")
        print(f"  Use Cases       : {', '.join(claude.supported_use_cases[:5])}... ({len(claude.supported_use_cases)} total)")
        print(f"  Capabilities    : Vision={claude.supports_vision}, Tools={claude.supports_tools}, Code={claude.supports_code}, Reasoning={claude.supports_reasoning}")

    # 3. Default Models by Provider and Family
    print_section("2. Default Model Selection by Provider & Family")
    openai_default = registry.get_default_model(provider="OpenAI")
    claude_default = registry.get_default_model(family="Claude")
    print(f"  Default OpenAI Model : {openai_default.display_name if openai_default else 'None'} ({openai_default.model_id if openai_default else ''})")
    print(f"  Default Claude Family: {claude_default.display_name if claude_default else 'None'} ({claude_default.model_id if claude_default else ''})")

    # 4. Provider & Family Queries
    print_section("3. Provider Query: Anthropic Foundation Models")
    anthropic_models = registry.get_models_by_provider("Anthropic")
    print_model_table(anthropic_models)

    # 5. Modality & Use Case Filtering
    print_section("4. Modality & Use Case Queries")
    print("Models supporting 'image' modality:")
    vision_models = registry.get_models_supporting("image")
    print_model_table(vision_models)

    print("\nModels supporting 'System Design' use case:")
    sys_design_models = registry.get_models_for_use_case("System Design")
    print_model_table(sys_design_models)

    # 6. Substring Keyword Search
    print_section("5. Case-Insensitive Keyword Search ('reasoning')")
    search_results = registry.search_models("reasoning")
    print_model_table(search_results)

    # 7. Complex Criteria Filtering
    print_section("6. Flexible Multi-Criteria Filtering")
    print("Criteria: Context Window >= 128k, Vision Support=True, Cost Tier in ['low', 'medium']")
    filtered = registry.filter_models(
        min_context_window=128000,
        supports_vision=True,
        cost_tier=["low", "medium"]
    )
    print_model_table(filtered)

    print("\nCriteria: Required Use Cases=['Programming'], Function Calling=True, Latency Tier='fast'")
    fast_coding = registry.filter_models(
        required_use_cases=["Programming"],
        supports_function_calling=True,
        latency_tier="fast"
    )
    print_model_table(fast_coding)

    print("\n" + "=" * 80)
    print(" Model Registry Demonstration Complete ")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
