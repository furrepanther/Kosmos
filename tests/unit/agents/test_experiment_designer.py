"""Tests for experiment designer Variable parsing (D1 fix)."""

import pytest
from kosmos.models.experiment import Variable, VariableType


@pytest.mark.unit
class TestVariableValuesParsing:
    """Test that Variable.values handles various LLM output types."""

    def test_values_as_list(self):
        """Test values as a proper list (normal case)."""
        var = Variable(
            name="temperature",
            type=VariableType.INDEPENDENT,
            description="Temperature values to test in experiment",
            values=[25, 30, 37, 42],
        )
        assert var.values == [25, 30, 37, 42]

    def test_values_as_none(self):
        """Test values as None (no values specified)."""
        var = Variable(
            name="growth_rate",
            type=VariableType.DEPENDENT,
            description="Measured growth rate of the culture",
            values=None,
        )
        assert var.values is None

    def test_values_as_string_crashes_pydantic(self):
        """Test that a raw string for values crashes Pydantic validation.

        This is the D1 bug: LLMs return strings like 'Variable (from dataset)'
        instead of lists. Without coercion in _parse_claude_protocol, this crashes.
        """
        with pytest.raises(Exception):
            Variable(
                name="substrate",
                type=VariableType.INDEPENDENT,
                description="Substrate concentration from experimental dataset",
                values="Variable (from dataset)",  # type: ignore
            )

    def test_values_as_empty_list(self):
        """Test values as empty list."""
        var = Variable(
            name="pH",
            type=VariableType.INDEPENDENT,
            description="pH levels for the experiment buffer",
            values=[],
        )
        assert var.values == []

    def test_values_as_mixed_types(self):
        """Test values with mixed types in list."""
        var = Variable(
            name="treatment",
            type=VariableType.INDEPENDENT,
            description="Treatment conditions to apply in study",
            values=["control", "low", "medium", "high"],
        )
        assert var.values == ["control", "low", "medium", "high"]


@pytest.mark.unit
class TestVariableValuesCoercion:
    """Test the coercion logic used in _parse_claude_protocol.

    These tests validate the coercion that happens BEFORE the Variable constructor,
    matching the fix in experiment_designer.py.
    """

    @staticmethod
    def _coerce_values(raw_values):
        """Mirror the coercion logic from _parse_claude_protocol."""
        if raw_values is None:
            return None
        elif isinstance(raw_values, list):
            return raw_values
        elif isinstance(raw_values, str):
            return None  # Description strings aren't usable as values
        else:
            return [raw_values]  # Single scalar value

    def test_coerce_none(self):
        assert self._coerce_values(None) is None

    def test_coerce_list(self):
        assert self._coerce_values([1, 2, 3]) == [1, 2, 3]

    def test_coerce_string_returns_none(self):
        """String descriptions should be coerced to None."""
        assert self._coerce_values("Variable (from dataset)") is None
        assert self._coerce_values("measured values") is None

    def test_coerce_scalar_wraps_in_list(self):
        assert self._coerce_values(42) == [42]
        assert self._coerce_values(3.14) == [3.14]

    def test_coerce_empty_string_returns_none(self):
        assert self._coerce_values("") is None

    def test_coerced_values_create_valid_variable(self):
        """End-to-end: coerced values should always produce a valid Variable."""
        test_cases = [
            None,
            [1, 2, 3],
            "Variable (from dataset)",
            42,
            "",
        ]
        for raw in test_cases:
            coerced = self._coerce_values(raw)
            # Should not raise
            var = Variable(
                name="test_var",
                type=VariableType.INDEPENDENT,
                description="A test variable for coercion validation",
                values=coerced,
            )
            assert isinstance(var, Variable)
