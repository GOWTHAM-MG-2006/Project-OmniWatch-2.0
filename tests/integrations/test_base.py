"""
OmniWatch 2.0 — Integration
Component: TestBaseIntegration & TestRegistry
Layer: Integration
Phase: 7
Purpose: Unit tests for BaseIntegration ABC and Integration Registry
Inputs: N/A
Outputs: Test results (pass/fail)
"""

import pytest
from integrations.base import BaseIntegration
from integrations.registry import INTEGRATIONS


class TestBaseIntegration:
    """Tests for the BaseIntegration abstract base class."""

    def test_cannot_instantiate_abstract(self):
        """BaseIntegration is abstract; direct instantiation must fail."""
        with pytest.raises(TypeError):
            BaseIntegration(config={})

    def test_subclass_with_all_methods(self):
        """A concrete subclass with all abstract methods implemented should work."""

        class CompleteIntegration(BaseIntegration):
            def collect_metrics(self):
                return []

            def health_check(self):
                return True

        integration = CompleteIntegration(config={"key": "value"})
        assert integration.config == {"key": "value"}
        assert integration.name == "CompleteIntegration"
        assert integration.health_check() is True
        assert integration.collect_metrics() == []

    def test_missing_collect_metrics(self):
        """Subclass missing collect_metrics must fail to instantiate."""

        class IncompleteIntegration(BaseIntegration):
            def health_check(self):
                return True

        with pytest.raises(TypeError):
            IncompleteIntegration(config={})

    def test_missing_health_check(self):
        """Subclass missing health_check must fail to instantiate."""

        class IncompleteIntegration(BaseIntegration):
            def collect_metrics(self):
                return []

        with pytest.raises(TypeError):
            IncompleteIntegration(config={})

    def test_to_kafka_default_is_noop(self):
        """Default to_kafka should not raise."""

        class MinimalIntegration(BaseIntegration):
            def collect_metrics(self):
                return [{"metric": "test", "value": 1}]

            def health_check(self):
                return True

        integration = MinimalIntegration(config={})
        # Should not raise
        integration.to_kafka(metrics=[{"metric": "test"}], topic="test.topic")

    def test_name_derived_from_class(self):
        """Integration name should match the concrete class name."""

        class MyCustomIntegration(BaseIntegration):
            def collect_metrics(self):
                return []

            def health_check(self):
                return True

        integration = MyCustomIntegration(config={})
        assert integration.name == "MyCustomIntegration"


class TestRegistry:
    """Tests for the Integration Registry."""

    def test_registry_has_entries(self):
        """Registry must contain at least 25 integrations."""
        assert len(INTEGRATIONS) >= 25

    def test_registry_entry_structure(self):
        """Every registry entry must have class, category, and config_required."""
        for name, entry in INTEGRATIONS.items():
            assert "class" in entry, f"Missing 'class' in {name}"
            assert "category" in entry, f"Missing 'category' in {name}"
            assert "config_required" in entry, f"Missing 'config_required' in {name}"
            assert isinstance(
                entry["config_required"], list
            ), f"config_required must be list in {name}"

    def test_registry_categories(self):
        """Registry entries should belong to known categories."""
        valid_categories = {
            "cloud",
            "database",
            "message_queue",
            "web_server",
            "cicd",
            "monitoring",
            "security",
        }
        for name, entry in INTEGRATIONS.items():
            assert entry["category"] in valid_categories, (
                f"Unknown category '{entry['category']}' in {name}"
            )

    def test_registry_class_names_are_strings(self):
        """All class names must be non-empty strings."""
        for name, entry in INTEGRATIONS.items():
            assert isinstance(entry["class"], str)
            assert len(entry["class"]) > 0

    def test_registry_no_duplicate_class_names(self):
        """No two integrations should share the same class name."""
        classes = [entry["class"] for entry in INTEGRATIONS.values()]
        assert len(classes) == len(set(classes)), "Duplicate class names found"
