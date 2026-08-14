"""
Unit Tests for ModelInfo Data Model in Model Registry.
"""

import unittest
from model_registry.src.model import (
    ModelInfo,
    VALID_STATUSES,
    VALID_COST_TIERS,
    VALID_LATENCY_TIERS,
)


class TestModelInfo(unittest.TestCase):
    """Test suite verifying ModelInfo validation, instantiation, and serialization."""

    def test_model_info_valid_instantiation(self):
        """Verify valid ModelInfo instantiation and serialization."""
        model = ModelInfo(
            provider="OpenAI",
            family="GPT-4",
            model_id="gpt-4o",
            display_name="GPT-4o",
            description="Omni multimodal model",
            status="available",
            is_default=True,
            cost_tier="medium",
            latency_tier="fast",
            context_window=128000,
            max_output_tokens=4096,
            supported_modalities=["text", "image"],
            supported_use_cases=["Programming", "Vision Analysis"],
        )
        model.validate()
        data = model.to_dict()
        self.assertEqual(data["model_id"], "gpt-4o")
        self.assertEqual(data["provider"], "OpenAI")
        self.assertTrue(data["is_default"])

        # Test round-trip
        reloaded = ModelInfo.from_dict(data)
        self.assertEqual(reloaded.model_id, "gpt-4o")

    def test_model_info_invalid_status_raises(self):
        """Verify invalid status string raises ValueError."""
        model = ModelInfo(
            provider="OpenAI",
            family="GPT-4",
            model_id="gpt-4o",
            display_name="GPT-4o",
            description="Test",
            status="unsupported_status",
        )
        with self.assertRaises(ValueError) as ctx:
            model.validate()
        self.assertIn("Invalid status", str(ctx.exception))

    def test_model_info_invalid_cost_tier_raises(self):
        """Verify invalid cost_tier raises ValueError."""
        model = ModelInfo(
            provider="OpenAI",
            family="GPT-4",
            model_id="gpt-4o",
            display_name="GPT-4o",
            description="Test",
            cost_tier="ultra_cheap",
        )
        with self.assertRaises(ValueError) as ctx:
            model.validate()
        self.assertIn("Invalid cost_tier", str(ctx.exception))

    def test_model_info_invalid_latency_tier_raises(self):
        """Verify invalid latency_tier raises ValueError."""
        model = ModelInfo(
            provider="OpenAI",
            family="GPT-4",
            model_id="gpt-4o",
            display_name="GPT-4o",
            description="Test",
            latency_tier="hyper_speed",
        )
        with self.assertRaises(ValueError) as ctx:
            model.validate()
        self.assertIn("Invalid latency_tier", str(ctx.exception))

    def test_model_info_invalid_context_window_raises(self):
        """Verify non-positive context window raises ValueError."""
        model = ModelInfo(
            provider="OpenAI",
            family="GPT-4",
            model_id="gpt-4o",
            display_name="GPT-4o",
            description="Test",
            context_window=0,
        )
        with self.assertRaises(ValueError) as ctx:
            model.validate()
        self.assertIn("Context window", str(ctx.exception))

    def test_model_info_empty_identifiers_raises(self):
        """Verify empty model_id, provider, or family raises ValueError."""
        with self.assertRaises(ValueError):
            ModelInfo(provider="", family="GPT-4", model_id="m1", display_name="M", description="D").validate()
        with self.assertRaises(ValueError):
            ModelInfo(provider="OpenAI", family="", model_id="m1", display_name="M", description="D").validate()
        with self.assertRaises(ValueError):
            ModelInfo(provider="OpenAI", family="GPT-4", model_id="", display_name="M", description="D").validate()


if __name__ == "__main__":
    unittest.main()
