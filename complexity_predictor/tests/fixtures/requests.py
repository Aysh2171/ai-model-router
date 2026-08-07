"""
Synthetic valid AI request payload fixtures for testing.
"""

SIMPLE_TEXT_REQUEST = {
    "prompt": "What is the capital of France and what is its estimated population?",
    "attachments": [],
    "conversation_context": {"turns": 0},
    "metadata": {"task_category": "General Question Answering"},
    "expected_output": {"format": "short_answer"}
}

CODE_REQUEST = {
    "prompt": "Write a recursive bubble sort implementation in Python and analyze its time complexity.",
    "attachments": [],
    "conversation_context": {"turns": 1},
    "metadata": {"task_category": "Programming"},
    "expected_output": {"format": "code"}
}

DOCUMENT_REQUEST = {
    "prompt": "Perform a comprehensive audit across all 600 pages of legal contracts to report GDPR compliance violations.",
    "attachments": [
        {"file_name": "contracts_bundle.pdf", "file_type": "pdf", "size_mb": 45.0}
    ],
    "conversation_context": {"turns": 8},
    "metadata": {"task_category": "Document Analysis"},
    "expected_output": {"format": "comparative_report"}
}

MULTIMODAL_REQUEST = {
    "prompt": "Analyze this architectural diagram screenshot and generate a FastAPI service implementation.",
    "attachments": [
        {"file_name": "architecture.png", "file_type": "image", "size_mb": 3.2}
    ],
    "conversation_context": {"turns": 2},
    "metadata": {"task_category": "System Design"},
    "expected_output": {"format": "code"}
}
