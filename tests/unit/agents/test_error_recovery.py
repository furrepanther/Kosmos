"""
Tests for ERROR_RECOVERY action handler (D2 fix).

These are pure unit tests that do NOT require an API key.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from kosmos.agents.research_director import ResearchDirectorAgent
from kosmos.core.workflow import WorkflowState, NextAction


@pytest.fixture
def director():
    """Create a research director for error recovery testing."""
    return ResearchDirectorAgent(
        research_question="Does temperature affect enzyme kinetics?",
        domain="biochemistry",
        config={
            "model": "test-model",
            "max_iterations": 5,
        }
    )


@pytest.mark.unit
class TestErrorRecovery:
    """Test ERROR_RECOVERY action handler (D2 fix)."""

    @pytest.mark.asyncio
    async def test_error_recovery_transitions_to_generating(self, director):
        """Test that ERROR_RECOVERY transitions from ERROR to GENERATING_HYPOTHESES."""
        director.start()  # Goes to GENERATING_HYPOTHESES
        director.workflow.transition_to(WorkflowState.ERROR, "Test error")
        assert director.workflow.current_state == WorkflowState.ERROR

        director._consecutive_errors = 3

        await director._do_execute_action(NextAction.ERROR_RECOVERY)

        assert director.workflow.current_state == WorkflowState.GENERATING_HYPOTHESES
        assert director._consecutive_errors == 0

    @pytest.mark.asyncio
    async def test_error_recovery_resets_error_counter(self, director):
        """Test that error counter is reset on recovery."""
        director.start()
        director.workflow.transition_to(WorkflowState.ERROR, "Test error")
        director._consecutive_errors = 5

        await director._do_execute_action(NextAction.ERROR_RECOVERY)

        assert director._consecutive_errors == 0

    @pytest.mark.asyncio
    async def test_error_recovery_does_not_loop(self, director):
        """Test that after recovery, the next action is NOT ERROR_RECOVERY (no loop)."""
        director.start()
        director.workflow.transition_to(WorkflowState.ERROR, "Test error")

        await director._do_execute_action(NextAction.ERROR_RECOVERY)

        # Now in GENERATING_HYPOTHESES, next action should be GENERATE_HYPOTHESIS
        next_action = director.decide_next_action()
        assert next_action == NextAction.GENERATE_HYPOTHESIS
        assert next_action != NextAction.ERROR_RECOVERY
