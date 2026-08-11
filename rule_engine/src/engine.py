"""
Rule Engine Core Orchestrator.
Evaluates organizational policy rules across technically feasible candidate models.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from capability_matcher.src import CapabilityMatchResult, CandidateModel, ExcludedModel
from .context import PolicyContext
from .result import PolicyExcludedModel, RuleEvaluationResult
from .rules import BaseRule, DEFAULT_RULES

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default_policy.json"


class RuleEngine:
    """Core evaluation engine performing deterministic organizational policy filtering."""

    def __init__(self, rules: Optional[List[BaseRule]] = None, default_config_path: Optional[Path] = None):
        """Initialize RuleEngine with custom or default policy rules."""
        self.rules: List[BaseRule] = rules if rules is not None else list(DEFAULT_RULES)
        self.default_config_path = default_config_path or DEFAULT_CONFIG_PATH
        self._default_policy_data = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default declarative policy dictionary from JSON configuration file."""
        if self.default_config_path.exists():
            try:
                with open(self.default_config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def get_default_context(self) -> PolicyContext:
        """Construct PolicyContext instance from default declarative policy JSON."""
        if self._default_policy_data:
            return PolicyContext.from_dict(self._default_policy_data)
        return PolicyContext()

    def evaluate(
        self,
        capability_match_result: CapabilityMatchResult,
        context: Optional[PolicyContext] = None,
        **context_overrides: Any
    ) -> RuleEvaluationResult:
        """
        Evaluate organizational policy rules on the candidate models inside CapabilityMatchResult.

        Args:
            capability_match_result: Result object from CapabilityMatcher (Module 3).
            context: Optional PolicyContext. If omitted, constructed from default_policy.json.
            **context_overrides: Optional key-value overrides for PolicyContext.

        Returns:
            RuleEvaluationResult container with allowed candidates and audit telemetry.
        """
        # Resolve policy context
        if context is None:
            if self._default_policy_data:
                effective_context = PolicyContext.from_dict(self._default_policy_data)
            else:
                effective_context = PolicyContext()
        else:
            effective_context = context

        # Apply explicit overrides if provided
        if context_overrides:
            context_dict = effective_context.to_dict()
            context_dict.update(context_overrides)
            effective_context = PolicyContext.from_dict(context_dict)

        return self.evaluate_candidates(
            candidates=capability_match_result.eligible_candidates,
            context=effective_context,
            request_id=capability_match_result.request_id,
            complexity_profile=capability_match_result.complexity_profile,
            capability_excluded=capability_match_result.excluded_models
        )

    def evaluate_candidates(
        self,
        candidates: List[CandidateModel],
        context: PolicyContext,
        request_id: str = "REQ-000",
        complexity_profile: Optional[Dict[str, Any]] = None,
        capability_excluded: Optional[List[ExcludedModel]] = None
    ) -> RuleEvaluationResult:
        """
        Evaluate organizational rules on a list of CandidateModel objects.
        Collects ALL rule violations per candidate without stopping after the first failure.
        """
        allowed_candidates: List[CandidateModel] = []
        policy_excluded_candidates: List[PolicyExcludedModel] = []
        applied_policies = [r.name for r in self.rules]

        for candidate in candidates:
            failed_rule_names: List[str] = []
            violation_details: List[str] = []

            for rule in self.rules:
                outcome = rule.evaluate(candidate, context)
                if not outcome.passed:
                    failed_rule_names.append(outcome.rule_name)
                    if outcome.reason:
                        violation_details.append(outcome.reason)

            if failed_rule_names:
                policy_excluded_candidates.append(
                    PolicyExcludedModel(
                        model_id=candidate.model_id,
                        provider=candidate.provider,
                        failed_rule_names=failed_rule_names,
                        violation_details=violation_details
                    )
                )
            else:
                allowed_candidates.append(candidate)

        is_satisfiable = len(allowed_candidates) > 0
        profile_dict = complexity_profile or {}
        cap_excluded = capability_excluded or []

        return RuleEvaluationResult(
            request_id=request_id,
            is_rule_satisfiable=is_satisfiable,
            policy_context=context,
            allowed_candidates=allowed_candidates,
            policy_excluded_candidates=policy_excluded_candidates,
            capability_excluded_models=cap_excluded,
            complexity_profile=profile_dict,
            applied_policies=applied_policies,
            total_feasible_input=len(candidates),
            allowed_count=len(allowed_candidates),
            policy_excluded_count=len(policy_excluded_candidates),
        )
