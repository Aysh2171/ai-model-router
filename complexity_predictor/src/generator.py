"""
Scenario Generator module for the Complexity Predictor.
Generates 1,500 realistic enterprise AI Request Scenarios using randomized component-based composition
and human-centered holistic workload labeling.
Includes short-but-hard prompts, scale-heavy requests, boundary cases, and broad multi-tier task categories.
"""

import random
from typing import List, Dict, Any


class DatasetGenerator:
    """Generates realistic enterprise AI Request Scenarios by combining independent component building blocks."""

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

    def __init__(self, seed: int = 42):
        random.seed(seed)

    def _generate_low_scenario(self) -> Dict[str, Any]:
        """Generate a realistic Low complexity AI Request scenario."""
        template_choice = random.choice([
            "qa_simple", "code_simple", "trans_simple", "extract_simple", "low_boundary_explain"
        ])

        if template_choice == "qa_simple":
            prompt = random.choice([
                "What is Python?",
                "What is the boiling point of water in Celsius?",
                "What is the capital of France?",
                "Define object-oriented programming."
            ])
            task = "General Question Answering"
            fmt = "short_answer"

        elif template_choice == "code_simple":
            prompt = random.choice([
                "Write a bubble sort function in Python.",
                "Write a function to add two numbers.",
                "Write a Python script to reverse a string.",
                "Create a simple print statement in Java."
            ])
            task = "Programming"
            fmt = "code"

        elif template_choice == "trans_simple":
            prompt = random.choice([
                "Translate 'Hello' into French.",
                "Translate 'Thank you very much' to Spanish.",
                "Translate 'Good morning' to German."
            ])
            task = "Translation"
            fmt = "text"

        elif template_choice == "extract_simple":
            prompt = random.choice([
                "Extract the email address from this string: contact us at support@example.com.",
                "Extract the phone number from the invoice header.",
                "Find the date in this sentence: Paid on Jan 5."
            ])
            task = "Data Processing"
            fmt = "short_answer"

        else:  # low_boundary_explain
            prompt = random.choice([
                "Explain bubble sort with a simple example.",
                "Summarize a one-page PDF note.",
                "Explain Python decorators in two sentences."
            ])
            task = "Analysis & Review"
            fmt = "text"

        has_att = random.random() < 0.25
        attachments = [{"type": random.choice(["pdf", "txt"]), "size_mb": 0.2}] if has_att else []
        turns = random.choice([0, 0, 1])

        return {
            "request": {
                "prompt": prompt,
                "attachments": attachments,
                "conversation_context": {"turns": turns},
                "metadata": {"task_category": task},
                "expected_output": {"format": fmt}
            },
            "complexity": "Low"
        }

    def _generate_medium_scenario(self) -> Dict[str, Any]:
        """Generate a realistic Medium complexity AI Request scenario."""
        template_choice = random.choice([
            "code_detailed", "doc_summary", "transcript_review", "sql_gen", "trans_medium", "med_boundary_compare"
        ])

        if template_choice == "code_detailed":
            prompt = "Write bubble sort using recursion. Explain every step. Add detailed comments. Also give the time and space complexity."
            task = "Programming"
            fmt = "code"

        elif template_choice == "doc_summary":
            prompt = "Summarize the key points of the attached annual technical report."
            task = "Document Processing"
            fmt = "summary"

        elif template_choice == "transcript_review":
            prompt = "Review a meeting transcript and extract all assigned action items grouped by team lead."
            task = "Analysis & Review"
            fmt = "markdown"

        elif template_choice == "sql_gen":
            prompt = "Generate SQL queries from a provided schema joining user profiles with transaction audit logs."
            task = "Data Processing"
            fmt = "code"

        elif template_choice == "trans_medium":
            prompt = "Translate this 5-page product user manual into Japanese, preserving technical terminology and formatting."
            task = "Translation"
            fmt = "markdown"

        else:  # med_boundary_compare
            prompt = "Compare two research papers and summarize their structural differences and key findings."
            task = "Analysis & Review"
            fmt = "markdown"

        r_att = random.random()
        if r_att < 0.3:
            attachments = []
        elif r_att < 0.8:
            attachments = [{"type": random.choice(["pdf", "code", "csv", "docx"]), "size_mb": round(random.uniform(0.5, 3.0), 2)}]
        else:
            attachments = [
                {"type": "pdf", "size_mb": 1.5},
                {"type": random.choice(["code", "csv"]), "size_mb": 2.0}
            ]

        turns = random.randint(1, 4)

        return {
            "request": {
                "prompt": prompt,
                "attachments": attachments,
                "conversation_context": {"turns": turns},
                "metadata": {"task_category": task},
                "expected_output": {"format": fmt}
            },
            "complexity": "Medium"
        }

    def _generate_high_scenario(self) -> Dict[str, Any]:
        """Generate a realistic High complexity AI Request scenario."""
        template_choice = random.choice([
            "short_hard_systems", "scale_heavy_doc", "multi_tech_arch", "multi_doc_audit"
        ])

        if template_choice == "short_hard_systems":
            prompt = random.choice([
                "Implement a Linux scheduler.",
                "Design a compiler.",
                "Build a distributed cache.",
                "Implement Raft consensus protocol.",
                "Create a Kubernetes operator.",
                "Write a query optimizer.",
                "Implement a blockchain.",
                "Design a hypervisor."
            ])
            task = "System Design" if "Design" in prompt or "architecture" in prompt.lower() else "Programming"
            fmt = "code"

        elif template_choice == "scale_heavy_doc":
            prompt = random.choice([
                "Translate this 600-page legal document.",
                "Translate 500 pages of legal contracts into Spanish.",
                "Translate a 600-page patent document.",
                "Summarize 25 research papers on transformer acceleration.",
                "Summarize 30 technical reports across 400 pages.",
                "Review 10 vendor contracts spanning 250 pages for GDPR data liability gaps.",
                "Process 50 GB of server logs and extract error metrics."
            ])
            task = "Translation" if "Translate" in prompt else ("Document Processing" if "Summarize" in prompt else "Analysis & Review")
            fmt = "markdown"

        elif template_choice == "multi_tech_arch":
            tech_stack = random.choice([
                "FastAPI microservice with PostgreSQL, Redis, Docker, JWT authentication, and unit tests",
                "Django application with PostgreSQL, Celery, Redis, Docker, and Swagger API documentation",
                "Spring Boot service with Kafka, MySQL, Kubernetes, JWT auth, and integration test suites",
                "full-stack application with React, FastAPI, PostgreSQL, Docker, Redis caching, and Nginx"
            ])
            prompt = f"Develop a {tech_stack}."
            task = "System Design"
            fmt = "code"

        else:  # multi_doc_audit
            prompt = random.choice([
                "Perform a GDPR compliance audit across three uploaded vendor contracts spanning 300 pages, identify risks, and recommend legal refactored language.",
                "Perform a GDPR compliance audit across 10 uploaded contracts, identify risks, and recommend legal refactored language.",
                "Audit 500 pages of compliance agreements for data liability risks."
            ])
            task = "Analysis & Review"
            fmt = "json"

        if template_choice == "scale_heavy_doc":
            r_att = random.random()
            if r_att < 0.6:
                attachments = [{"type": "pdf", "size_mb": round(random.uniform(15.0, 50.0), 2)}]
            else:
                n_files = random.randint(2, 4)
                attachments = [
                    {"type": "pdf", "size_mb": round(random.uniform(10.0, 30.0), 2)}
                    for _ in range(n_files)
                ]
        else:
            r_att = random.random()
            if r_att < 0.2:
                attachments = []
            elif r_att < 0.5:
                attachments = [{"type": "pdf", "size_mb": round(random.uniform(3.0, 15.0), 2)}]
            else:
                n_files = random.randint(2, 4)
                attachments = [
                    {"type": random.choice(["pdf", "code", "csv", "docx"]), "size_mb": round(random.uniform(2.0, 12.0), 2)}
                    for _ in range(n_files)
                ]

        turns = random.randint(3, 10)

        return {
            "request": {
                "prompt": prompt,
                "attachments": attachments,
                "conversation_context": {"turns": turns},
                "metadata": {"task_category": task},
                "expected_output": {"format": fmt}
            },
            "complexity": "High"
        }

    def generate_scenarios(self, num_samples: int = 1500) -> List[Dict[str, Any]]:
        """
        Generate a balanced collection of realistic enterprise AI Request Scenarios across complexity tiers.

        Args:
            num_samples: Total number of scenarios to generate (default 1500).

        Returns:
            List of scenario dictionaries containing raw 'request' and target 'complexity'.
        """
        scenarios: List[Dict[str, Any]] = []
        samples_per_tier = num_samples // 3

        for _ in range(samples_per_tier):
            scenarios.append(self._generate_low_scenario())
            scenarios.append(self._generate_medium_scenario())
            scenarios.append(self._generate_high_scenario())

        random.shuffle(scenarios)
        return scenarios
