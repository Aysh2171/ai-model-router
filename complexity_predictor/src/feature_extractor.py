"""
Feature Extraction module for the Complexity Predictor.
Converts a StructuredRequest into a tabular Feature Vector containing derived numerical and categorical ML features.
Derives domain complexity scores, workload scale indicators via regex, verb objective diversity,
high-complexity domain nouns, technology diversity, and structural prompt features.
"""

import re
from typing import Dict, Any, List, Set


# Verb Categories for Objective Diversity
VERB_CATEGORIES: Dict[str, List[str]] = {
    "creation": ["write", "implement", "build", "generate", "create", "architect"],
    "analysis": ["analyze", "review", "inspect", "investigate", "audit"],
    "comparison": ["compare", "contrast", "benchmark"],
    "reasoning": ["justify", "derive", "prove", "evaluate"],
    "optimization": ["optimize", "refactor", "improve", "debug"],
    "documentation": ["explain", "summarize", "document", "comment"]
}

# Domain Complexity Vocabularies
DOMAIN_VOCABULARIES: Dict[str, List[str]] = {
    "os": ["linux", "kernel", "scheduler", "filesystem", "driver", "thread", "process", "context switch", "memory management"],
    "distributed": ["distributed", "consensus", "raft", "paxos", "replication", "cluster", "leader election", "fault tolerance"],
    "cloud": ["aws", "azure", "gcp", "terraform", "kubernetes", "docker swarm", "autoscaling", "load balancer"],
    "backend": ["microservice", "rest api", "graphql", "authentication", "authorization", "jwt", "oauth", "postgresql", "redis", "rabbitmq", "kafka"],
    "data_eng": ["etl", "spark", "hadoop", "airflow", "data warehouse", "pipeline"],
    "security": ["encryption", "cryptography", "rsa", "aes", "gdpr", "audit", "compliance", "legal", "contract", "patent", "regulatory", "litigation"],
    "compiler": ["compiler", "lexer", "parser", "llvm", "bytecode", "virtual machine", "hypervisor"],
    "ai_ml": ["transformer", "neural network", "llm", "cnn", "rnn", "fine tuning"]
}

HIGH_COMPLEXITY_NOUNS: List[str] = [
    "scheduler", "kernel", "compiler", "microservice", "architecture", "pipeline",
    "database engine", "distributed system", "hypervisor", "consensus", "gpu", "cuda",
    "cluster", "orchestration", "blockchain", "operator", "parser", "lexer"
]

TECH_KEYWORDS: List[str] = [
    "python", "java", "c++", "cpp", "fastapi", "flask", "django", "spring",
    "docker", "kubernetes", "postgresql", "mysql", "mongodb", "redis",
    "tensorflow", "pytorch", "react", "angular", "aws", "azure", "gcp",
    "jwt", "rest", "graphql", "sql", "git", "rabbitmq", "celery", "kafka",
    "pandas", "scikit-learn", "numpy", "terraform", "microservice"
]


class FeatureExtractor:
    """Derives numerical and categorical machine learning features from a StructuredRequest."""

    def extract_features(self, structured_request: StructuredRequest) -> Dict[str, Any]:
        """
        Transform a StructuredRequest domain object into a machine-learning-ready Feature Vector dictionary.

        Args:
            structured_request: Organized StructuredRequest instance.

        Returns:
            Feature Vector dictionary containing derived numerical and categorical features.
        """
        prompt = structured_request.prompt
        prompt_lower = prompt.lower()

        # 1. Lexical & Textual Features
        prompt_length = len(prompt)
        words = prompt.split()
        word_count = len(words)
        sentences = [s for s in re.split(r'[.!?]+', prompt) if s.strip()]
        sentence_count = max(1, len(sentences))

        estimated_prompt_tokens = max(1, int(prompt_length / 4.0))
        avg_word_length = round(prompt_length / max(1, word_count), 2)
        avg_sentence_length = round(word_count / sentence_count, 2)
        question_count = prompt.count("?")

        special_chars = sum(1 for c in prompt if c in "{}[]<>=;()#*_|-")
        punctuation_count = sum(1 for c in prompt if c in ".,!?:;\"'()-")
        punctuation_density = round(punctuation_count / max(1, prompt_length), 4)

        # 2. Request Structure Features (regex & string parsing)
        newline_count = prompt.count("\n")
        bullet_count = len(re.findall(r'^\s*[-*•]\s+', prompt, re.MULTILINE))
        numbered_list_count = len(re.findall(r'^\s*\d+[\.\)]\s+', prompt, re.MULTILINE))
        contains_code_block = 1 if "```" in prompt else 0
        contains_json = 1 if re.search(r'\{.*\}', prompt, re.DOTALL) and (":" in prompt) else 0
        contains_markdown = 1 if re.search(r'(#|\*\*|\*|-)', prompt) else 0
        contains_table_like_structure = 1 if ("|" in prompt and "-" in prompt) else 0
        contains_urls = 1 if re.search(r'https?://', prompt) else 0

        # 3. Domain Complexity Vocabulary Score
        domain_complexity_score = 0
        for domain, terms in DOMAIN_VOCABULARIES.items():
            domain_matches = sum(1 for t in terms if re.search(r'\b' + re.escape(t) + r'\b', prompt_lower))
            domain_complexity_score += domain_matches

        # 4. Workload Scale Features (Regex Parsing)
        large_num_match = re.search(r'\b([2-9]\d|\d{3,})\s*(-?\s*(page|pages|gb|tb|million|services|repositories|files|apis|rows|contracts|papers))\b', prompt_lower)
        contains_large_numeric_quantity = 1 if large_num_match else 0

        page_match = re.search(r'(\d+)\s*-?\s*pages?', prompt_lower)
        page_count_indicator = int(page_match.group(1)) if page_match else 0
        large_document_indicator = 1 if page_count_indicator >= 25 or ("600-page" in prompt_lower) or ("page" in prompt_lower and contains_large_numeric_quantity) else 0

        large_dataset_indicator = 1 if ("gb" in prompt_lower or "tb" in prompt_lower or "million" in prompt_lower or "rows" in prompt_lower) else 0
        large_codebase_indicator = 1 if ("repositories" in prompt_lower or "services" in prompt_lower or "files" in prompt_lower) and contains_large_numeric_quantity else 0

        # Incorporate scale indicators into total domain complexity score
        if large_document_indicator or large_dataset_indicator or large_codebase_indicator:
            domain_complexity_score += 3

        # 5. Multi-Objective Diversity (Verb Categories)
        matched_categories: Set[str] = set()
        all_verbs: List[str] = []
        for cat_name, verb_list in VERB_CATEGORIES.items():
            for v in verb_list:
                if re.search(r'\b' + re.escape(v) + r'\b', prompt_lower):
                    matched_categories.add(cat_name)
                    all_verbs.append(v)
        instruction_count = len(all_verbs)
        objective_diversity = len(matched_categories)
        multi_step_request = 1 if (instruction_count >= 2 or objective_diversity >= 2) else 0

        # 6. High-Complexity Domain Nouns
        high_complexity_domain_terms = sum(1 for noun in HIGH_COMPLEXITY_NOUNS if re.search(r'\b' + re.escape(noun) + r'\b', prompt_lower))
        if large_document_indicator or large_dataset_indicator:
            high_complexity_domain_terms += 1

        # 7. Technology Metrics (Count vs Diversity)
        matched_techs = [tech for tech in TECH_KEYWORDS if re.search(r'\b' + re.escape(tech) + r'\b', prompt_lower)]
        technology_count = len(matched_techs)
        technology_diversity = len(set(matched_techs))

        # 8. Programming Intent Features
        task_category = structured_request.metadata.get("task_category", "General Prompting")
        has_prog_kw = (high_complexity_domain_terms > 0) or (technology_count > 0) or any(w in prompt_lower for w in ["code", "function", "script", "algorithm", "class", "unit test", "api"])
        is_programming_request = 1 if (task_category in ["Programming", "System Design"] or has_prog_kw) else 0

        # 9. Attachment Features
        attachments = structured_request.attachments
        attachment_count = len(attachments)
        total_attachment_size_mb = round(sum(float(a.get("size_mb", 0.0)) for a in attachments), 2)
        primary_file_type = attachments[0].get("type", "none") if attachments else "none"

        # 10. Context Features
        turns = int(structured_request.conversation_context.get("turns", 0))
        has_context = 1 if turns > 0 else 0

        # 11. Metadata & Output Features
        component_count = 1 + (1 if attachment_count > 0 else 0) + (1 if has_context else 0)
        output_format = structured_request.expected_output.get("format", "text")
        is_structured_output = 1 if output_format in ["json", "code", "comparative_report", "markdown", "summary"] else 0

        return {
            "prompt_length": prompt_length,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "estimated_prompt_tokens": estimated_prompt_tokens,
            "avg_word_length": avg_word_length,
            "avg_sentence_length": avg_sentence_length,
            "question_count": question_count,
            "special_char_count": special_chars,
            "punctuation_density": punctuation_density,
            "newline_count": newline_count,
            "bullet_count": bullet_count,
            "numbered_list_count": numbered_list_count,
            "contains_code_block": contains_code_block,
            "contains_json": contains_json,
            "contains_markdown": contains_markdown,
            "contains_table_like_structure": contains_table_like_structure,
            "contains_urls": contains_urls,
            "domain_complexity_score": domain_complexity_score,
            "contains_large_numeric_quantity": contains_large_numeric_quantity,
            "page_count_indicator": page_count_indicator,
            "large_document_indicator": large_document_indicator,
            "large_dataset_indicator": large_dataset_indicator,
            "large_codebase_indicator": large_codebase_indicator,
            "instruction_count": instruction_count,
            "objective_diversity": objective_diversity,
            "multi_step_request": multi_step_request,
            "high_complexity_domain_terms": high_complexity_domain_terms,
            "technology_count": technology_count,
            "technology_diversity": technology_diversity,
            "is_programming_request": is_programming_request,
            "task_category": task_category,
            "attachment_count": attachment_count,
            "primary_file_type": primary_file_type,
            "total_attachment_size_mb": total_attachment_size_mb,
            "conversation_turns": turns,
            "has_context": has_context,
            "component_count": component_count,
            "expected_output_format": output_format,
            "is_structured_output": is_structured_output
        }
