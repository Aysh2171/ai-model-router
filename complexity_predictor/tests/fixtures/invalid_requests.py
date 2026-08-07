"""
Malformed and edge-case AI request payload fixtures for testing.
"""

EMPTY_PROMPT_REQUEST = {
    "prompt": "",
    "attachments": [],
    "conversation_context": {"turns": 0},
    "metadata": {"task_category": "General Question Answering"},
    "expected_output": {"format": "short_answer"}
}

WHITESPACE_PROMPT_REQUEST = {
    "prompt": "   \n\t  ",
    "attachments": [],
    "conversation_context": {"turns": 0},
    "metadata": {"task_category": "General Question Answering"},
    "expected_output": {"format": "short_answer"}
}

NON_STRING_PROMPT_REQUEST = {
    "prompt": 12345,
    "attachments": [],
    "conversation_context": {"turns": 0},
    "metadata": {"task_category": "General Question Answering"},
    "expected_output": {"format": "short_answer"}
}

MASSIVE_PROMPT_REQUEST = {
    "prompt": "Analyze code snippet: " + ("x = 1\n" * 50000),
    "attachments": [],
    "conversation_context": {"turns": 10},
    "metadata": {"task_category": "Programming"},
    "expected_output": {"format": "code"}
}

UNKNOWN_EXTENSION_REQUEST = {
    "prompt": "Inspect binary file attachment.",
    "attachments": [
        {"file_name": "data.unknown_xyz", "file_type": "unknown_xyz", "size_mb": 5.0}
    ],
    "conversation_context": {"turns": 0},
    "metadata": {"task_category": "Data Processing"},
    "expected_output": {"format": "summary"}
}

UNKNOWN_CATEGORY_REQUEST = {
    "prompt": "Custom specialized request.",
    "attachments": [],
    "conversation_context": {"turns": 0},
    "metadata": {"task_category": "UnseenCustomTaskCategory99"},
    "expected_output": {"format": "markdown"}
}
