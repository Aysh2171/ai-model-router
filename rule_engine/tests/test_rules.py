"""
Unit tests for individual Rule Engine policy rules.
Verifies AllowedProvidersRule, DisallowedProvidersRule, DataResidencyRule, SecurityComplianceRule, TenantAccessTierRule, and MaxCostTierRule.
"""

import unittest
import sys
from pathlib import Path

# Add rule_engine and ai-model-router root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from model_registry.src import ModelInfo
from capability_matcher.src import CandidateModel
from src.context import PolicyContext
from src.rules import (
    AllowedProvidersRule,
    DisallowedProvidersRule,
    DataResidencyRule,
    SecurityComplianceRule,
    TenantAccessTierRule,
    MaxCostTierRule,
)


class TestRules(unittest.TestCase):
    """Unit test cases for organizational policy rules."""

    def setUp(self):
        self.model_info_gpt4o = ModelInfo(
            provider="OpenAI",
            family="GPT",
            model_id="gpt-4o",
            display_name="GPT-4o",
            description="Test model",
            status="available",
            tags=["multimodal", "coding", "vision", "enterprise"],
            cost_tier="high",
            latency_tier="medium"
        )
        self.candidate_gpt4o = CandidateModel(
            model_id="gpt-4o",
            provider="OpenAI",
            family="GPT",
            model_info=self.model_info_gpt4o,
            context_headroom=100000
        )

        self.model_info_preview = ModelInfo(
            provider="OpenAI",
            family="GPT",
            model_id="o1-preview",
            display_name="o1 Preview",
            description="Preview model",
            status="preview",
            tags=["reasoning"],
            cost_tier="premium",
            latency_tier="slow"
        )
        self.candidate_preview = CandidateModel(
            model_id="o1-preview",
            provider="OpenAI",
            family="GPT",
            model_info=self.model_info_preview,
            context_headroom=100000
        )

    def test_allowed_providers_rule(self):
        """Verify AllowedProvidersRule whitelist logic."""
        rule = AllowedProvidersRule()

        ctx_pass = PolicyContext(allowed_providers={"OpenAI", "Anthropic"})
        outcome_pass = rule.evaluate(self.candidate_gpt4o, ctx_pass)
        self.assertTrue(outcome_pass.passed)

        ctx_fail = PolicyContext(allowed_providers={"Anthropic", "Google"})
        outcome_fail = rule.evaluate(self.candidate_gpt4o, ctx_fail)
        self.assertFalse(outcome_fail.passed)
        self.assertIn("not in allowed_providers", outcome_fail.reason)

    def test_disallowed_providers_rule(self):
        """Verify DisallowedProvidersRule blacklist logic."""
        rule = DisallowedProvidersRule()

        ctx_pass = PolicyContext(disallowed_providers={"Meta", "Google"})
        outcome_pass = rule.evaluate(self.candidate_gpt4o, ctx_pass)
        self.assertTrue(outcome_pass.passed)

        ctx_fail = PolicyContext(disallowed_providers={"OpenAI"})
        outcome_fail = rule.evaluate(self.candidate_gpt4o, ctx_fail)
        self.assertFalse(outcome_fail.passed)
        self.assertIn("in disallowed_providers", outcome_fail.reason)

    def test_security_compliance_rule(self):
        """Verify SecurityComplianceRule required tags validation."""
        rule = SecurityComplianceRule()

        ctx_pass = PolicyContext(required_compliance_tags={"enterprise", "coding"})
        outcome_pass = rule.evaluate(self.candidate_gpt4o, ctx_pass)
        self.assertTrue(outcome_pass.passed)

        ctx_fail = PolicyContext(required_compliance_tags={"hipaa", "soc2"})
        outcome_fail = rule.evaluate(self.candidate_gpt4o, ctx_fail)
        self.assertFalse(outcome_fail.passed)
        self.assertIn("lacks required security/compliance tags", outcome_fail.reason)

    def test_max_cost_tier_rule(self):
        """Verify MaxCostTierRule cost cap comparison using deterministic cost order."""
        rule = MaxCostTierRule()

        ctx_pass = PolicyContext(max_cost_tier="high")
        outcome_pass = rule.evaluate(self.candidate_gpt4o, ctx_pass)
        self.assertTrue(outcome_pass.passed)

        ctx_fail = PolicyContext(max_cost_tier="medium")
        outcome_fail = rule.evaluate(self.candidate_gpt4o, ctx_fail)
        self.assertFalse(outcome_fail.passed)
        self.assertIn("exceeds tenant max_cost_tier cap", outcome_fail.reason)

    def test_tenant_access_tier_rule(self):
        """Verify TenantAccessTierRule preview and cost tier restrictions."""
        rule = TenantAccessTierRule()

        # Preview model under standard tier should fail
        ctx_std = PolicyContext(tenant_tier="standard")
        outcome_fail = rule.evaluate(self.candidate_preview, ctx_std)
        self.assertFalse(outcome_fail.passed)

        # Preview model under enterprise tier should pass
        ctx_ent = PolicyContext(tenant_tier="enterprise", allowed_model_statuses={"available", "preview"})
        outcome_pass = rule.evaluate(self.candidate_preview, ctx_ent)
        self.assertTrue(outcome_pass.passed)


if __name__ == "__main__":
    unittest.main()
