"""
Inference entry point and Interactive AI Request Builder for Complexity Predictor.
Simulates how an upstream application / API builds and submits complete AI Requests.
Passes requests through the exact 8-stage pipeline:
Request Analyzer -> Feature Extractor -> Preprocessor -> ML Model -> Complexity Profile.
"""

import os
import sys
import json
from typing import Dict, Any, List

# Ensure project root is in python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.model import ComplexityPredictorModel


TASK_CATEGORIES = [
    "General Question Answering",
    "Programming",
    "System Design",
    "Document Processing",
    "Translation",
    "Mathematics & Reasoning",
    "Creative Writing",
    "Data Processing",
    "Analysis & Review",
    "General Prompting"
]

OUTPUT_FORMATS = [
    ("Short Answer", "short_answer"),
    ("Summary", "summary"),
    ("Markdown", "markdown"),
    ("Code", "code"),
    ("JSON", "json"),
    ("Comparative Report", "comparative_report")
]


def extract_file_metadata(file_path: str) -> Dict[str, Any]:
    """Extract lightweight file metadata without semantic content analysis."""
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    if not ext:
        ext = "txt"

    if ext in ["py", "cpp", "c", "java", "js", "html", "css", "ts", "json", "sh"]:
        file_type = "code"
    elif ext in ["jpg", "jpeg", "png", "gif", "bmp"]:
        file_type = "image"
    elif ext in ["pdf"]:
        file_type = "pdf"
    elif ext in ["csv", "tsv"]:
        file_type = "csv"
    elif ext in ["doc", "docx"]:
        file_type = "docx"
    else:
        file_type = ext

    size_mb = 1.5
    extra_metadata = {}

    if os.path.exists(file_path):
        try:
            file_bytes = os.path.getsize(file_path)
            size_mb = round(file_bytes / (1024 * 1024), 3)

            if file_type in ["code", "txt", "csv", "json"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = sum(1 for _ in f)
                extra_metadata["line_count"] = lines
        except Exception:
            pass

    metadata = {
        "type": file_type,
        "size_mb": size_mb,
        "path": file_path
    }
    metadata.update(extra_metadata)
    return metadata


def interactive_request_builder() -> Dict[str, Any]:
    """Guide the user through building a complete AI Request interactively."""
    print("=" * 60)
    print("      AI REQUEST COMPLEXITY PREDICTOR - REQUEST BUILDER")
    print("=" * 60)
    print("\nSimulating upstream application request submission...\n")

    # Step 1: Prompt Input
    print("Step 1: Enter User Prompt")
    prompt = input("Enter your prompt:\n> ").strip()
    if not prompt:
        prompt = "Explain the fundamental principles of artificial intelligence."
        print(f"Using default prompt: '{prompt}'")

    # Step 2: Attachments Input
    print("\nStep 2: Uploaded Attachments")
    attachments: List[Dict[str, Any]] = []
    attach_choice = input("Do you want to attach files? (Y/N):\n> ").strip().lower()

    if attach_choice in ["y", "yes"]:
        file_idx = 1
        while True:
            file_path = input(f"Enter path or name for file #{file_idx} (or press Enter to finish):\n> ").strip()
            if not file_path:
                break
            meta = extract_file_metadata(file_path)
            attachments.append(meta)
            print(f"   -> Added attachment #{file_idx}: Type='{meta['type']}', Size={meta['size_mb']} MB")
            file_idx += 1

    # Step 3: Conversation Context Input
    print("\nStep 3: Conversation Context")
    turns_input = input("Previous conversation turns (default 0):\n> ").strip()
    turns = int(turns_input) if turns_input.isdigit() else 0

    # Step 4: Task Category Selection Menu
    print("\nStep 4: Select Task Category")
    for idx, category in enumerate(TASK_CATEGORIES, 1):
        print(f"  {idx}. {category}")

    category_choice = input(f"Select category (1-{len(TASK_CATEGORIES)}, default 10):\n> ").strip()
    if category_choice.isdigit() and 1 <= int(category_choice) <= len(TASK_CATEGORIES):
        selected_category = TASK_CATEGORIES[int(category_choice) - 1]
    else:
        selected_category = "General Prompting"
    print(f"   -> Selected Category: '{selected_category}'")

    # Step 5: Expected Output Format Selection Menu
    print("\nStep 5: Select Expected Output Format")
    for idx, (label, code) in enumerate(OUTPUT_FORMATS, 1):
        print(f"  {idx}. {label}")

    output_choice = input(f"Select format (1-{len(OUTPUT_FORMATS)}, default 1):\n> ").strip()
    if output_choice.isdigit() and 1 <= int(output_choice) <= len(OUTPUT_FORMATS):
        selected_output_format = OUTPUT_FORMATS[int(output_choice) - 1][1]
    else:
        selected_output_format = "short_answer"
    print(f"   -> Selected Output Format: '{selected_output_format}'")

    # Step 6: Construct Raw AI Request Object
    raw_request = {
        "prompt": prompt,
        "attachments": attachments,
        "conversation_context": {"turns": turns},
        "metadata": {"task_category": selected_category},
        "expected_output": {"format": selected_output_format}
    }

    return raw_request


def main():
    pipeline_path = os.path.join(PROJECT_ROOT, "models", "predictor_pipeline.joblib")

    if not os.path.exists(pipeline_path):
        print(f"Error: Saved pipeline not found at {pipeline_path}.")
        print("Please run 'python scripts/train.py' first.")
        sys.exit(1)

    # Load trained model pipeline
    predictor = ComplexityPredictorModel.load_pipeline(pipeline_path)

    # Check for --demo flag or non-interactive terminal fallback
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        raw_request = {
            "prompt": "Compare these three annual reports and identify financial trends.",
            "attachments": [
                {"type": "pdf", "size_mb": 8.4, "path": "report1.pdf"},
                {"type": "pdf", "size_mb": 6.9, "path": "report2.pdf"},
                {"type": "pdf", "size_mb": 7.1, "path": "report3.pdf"}
            ],
            "conversation_context": {"turns": 4},
            "metadata": {"task_category": "Analysis & Review"},
            "expected_output": {"format": "comparative_report"}
        }
    else:
        try:
            raw_request = interactive_request_builder()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Interactive Request Builder.")
            sys.exit(0)

    # Step 7: Display Constructed AI Request Object
    print("\n" + "=" * 60)
    print("   CONSTRUCTED RAW AI REQUEST PAYLOAD")
    print("=" * 60)
    print(json.dumps(raw_request, indent=4))

    # Step 8: Pass through prediction pipeline & display Complexity Profile
    print("\nExecuting prediction pipeline (Request Analysis -> Feature Extraction -> Preprocessing -> Model)...")
    profile = predictor.predict_complexity(raw_request)

    print("\n" + "=" * 60)
    print("   GENERATED COMPLEXITY PROFILE")
    print("=" * 60)
    print(json.dumps(profile, indent=4))
    print("=" * 60)


if __name__ == "__main__":
    main()
