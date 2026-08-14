"""
Unit Tests for ModelRegistry in Model Registry.
"""

import unittest
from model_registry.src.model_registry import ModelRegistry


class TestModelRegistry(unittest.TestCase):
    """Test suite verifying ModelRegistry lookup, filtering, and search capabilities."""

    def setUp(self):
        self.registry = ModelRegistry()

    def test_registry_load_default_catalog(self):
        """Verify default catalog loads exactly 17 models."""
        models = self.registry.get_all_models()
        self.assertEqual(len(models), 17)

    def test_registry_get_model_exact(self):
        """Verify exact model lookup."""
        model = self.registry.get_model("gpt-4o")
        self.assertIsNotNone(model)
        self.assertEqual(model.provider, "OpenAI")
        self.assertEqual(model.display_name, "GPT-4o")

    def test_registry_get_nonexistent_model(self):
        """Verify lookup of unknown model returns None."""
        self.assertIsNone(self.registry.get_model("nonexistent-model-xyz"))

    def test_registry_get_default_model(self):
        """Verify designated global default model is gpt-4o."""
        default_model = self.registry.get_default_model()
        self.assertIsNotNone(default_model)
        self.assertEqual(default_model.model_id, "gpt-4o")
        self.assertTrue(default_model.is_default)

    def test_registry_filter_by_provider(self):
        """Verify filtering models by provider."""
        anthropic_models = self.registry.get_models_by_provider("Anthropic")
        self.assertGreater(len(anthropic_models), 0)
        for m in anthropic_models:
            self.assertEqual(m.provider, "Anthropic")

    def test_registry_filter_by_cost_and_latency_tiers(self):
        """Verify filtering by cost tier and latency tier."""
        low_cost = self.registry.get_models_by_cost_tier("low")
        self.assertGreater(len(low_cost), 0)
        for m in low_cost:
            self.assertEqual(m.cost_tier, "low")

        fast_latency = self.registry.get_models_by_latency_tier("fast")
        self.assertGreater(len(fast_latency), 0)
        for m in fast_latency:
            self.assertEqual(m.latency_tier, "fast")

    def test_registry_filter_by_modality_and_use_case(self):
        """Verify filtering by supported modalities and use cases."""
        image_models = self.registry.get_models_supporting("image")
        self.assertGreater(len(image_models), 0)
        for m in image_models:
            self.assertIn("image", [mod.lower() for mod in m.supported_modalities])

        prog_models = self.registry.get_models_for_use_case("Programming")
        self.assertGreater(len(prog_models), 0)
        for m in prog_models:
            self.assertTrue(any(uc.lower() == "programming" for uc in m.supported_use_cases))

    def test_registry_search_models(self):
        """Verify search query across tags, display name, and provider."""
        results = self.registry.search_models("claude")
        self.assertGreater(len(results), 0)
        self.assertTrue(all("claude" in m.model_id.lower() or "claude" in m.display_name.lower() for m in results))

        # Empty search returns all models
        all_models = self.registry.search_models("")
        self.assertEqual(len(all_models), 17)


if __name__ == "__main__":
    unittest.main()
