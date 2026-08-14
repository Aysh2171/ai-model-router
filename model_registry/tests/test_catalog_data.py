"""
Catalog Data Integrity Tests for models.json in Model Registry.
"""

import unittest
from model_registry.src.model_registry import ModelRegistry


class TestCatalogData(unittest.TestCase):
    """Test suite verifying models.json catalog schema integrity and constraints."""

    def setUp(self):
        self.registry = ModelRegistry()
        self.models = self.registry.get_all_models()

    def test_catalog_model_count_and_unique_ids(self):
        """Verify exactly 17 models exist and all model_ids are unique."""
        self.assertEqual(len(self.models), 17)
        model_ids = [m.model_id for m in self.models]
        self.assertEqual(len(model_ids), len(set(model_ids)))

    def test_catalog_provider_defaults(self):
        """Verify each provider defines exactly one default model and global default resolves to gpt-4o."""
        defaults = [m for m in self.models if m.is_default]
        self.assertGreater(len(defaults), 0)
        global_default = self.registry.get_default_model()
        self.assertEqual(global_default.model_id, "gpt-4o")

        # Verify each provider has at most one default model
        providers = {m.provider for m in self.models}
        for prov in providers:
            prov_defaults = [m for m in self.models if m.provider == prov and m.is_default]
            self.assertEqual(len(prov_defaults), 1)

    def test_catalog_all_models_valid(self):
        """Verify every model in catalog passes validate()."""
        for model in self.models:
            model.validate()
            self.assertGreater(model.context_window, 0)
            self.assertGreater(model.max_output_tokens, 0)
            self.assertLessEqual(model.max_output_tokens, model.context_window)

    def test_catalog_supported_use_cases_non_empty(self):
        """Verify every catalog model defines non-empty supported use cases and modalities."""
        for model in self.models:
            self.assertGreater(len(model.supported_modalities), 0)
            self.assertGreater(len(model.supported_use_cases), 0)
            self.assertIn("text", [m.lower() for m in model.supported_modalities])


if __name__ == "__main__":
    unittest.main()
