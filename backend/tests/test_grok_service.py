"""Tests for Grok service."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.grok_service import (
    analyze_focus_area,
    run_full_analysis,
    FOCUS_AREAS,
)


class TestFocusAreas:
    """Test focus area configuration."""

    def test_all_focus_areas_defined(self):
        """Verify all expected focus areas are configured."""
        expected = {"voice_ai_ux", "agent_orchestration", "durable_runtime"}
        assert set(FOCUS_AREAS.keys()) == expected

    def test_focus_areas_have_required_fields(self):
        """Verify each focus area has name and evaluation criteria."""
        for area_id, config in FOCUS_AREAS.items():
            assert "name" in config, f"{area_id} missing 'name'"
            assert "evaluation_criteria" in config, f"{area_id} missing 'evaluation_criteria'"


class TestAnalyzeFocusArea:
    """Test single focus area analysis."""

    def test_invalid_focus_area_raises_error(self):
        """Test that invalid focus area raises ValueError."""
        with pytest.raises(ValueError, match="Unknown focus area"):
            analyze_focus_area("invalid_area")

    @patch("app.services.grok_service.litellm.completion")
    def test_successful_analysis(self, mock_completion):
        """Test successful API response parsing."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """[
            {
                "tool_name": "TestTool",
                "classification": "signal",
                "confidence_score": 85,
                "technical_insight": "Great benchmarks",
                "signal_evidence": ["published benchmarks"],
                "noise_indicators": [],
                "architectural_verdict": true
            }
        ]"""
        mock_completion.return_value = mock_response

        result = analyze_focus_area("voice_ai_ux")

        assert result is not None
        assert len(result) == 1
        assert result[0]["tool_name"] == "TestTool"
        assert result[0]["focus_area"] == "voice_ai_ux"
        assert "timestamp" in result[0]

    @patch("app.services.grok_service.litellm.completion")
    def test_json_extraction_from_text(self, mock_completion):
        """Test JSON extraction when response has surrounding text."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """Here are the results:
        [{"tool_name": "Tool1", "classification": "noise", "confidence_score": 70, "technical_insight": "Hype", "signal_evidence": [], "noise_indicators": ["marketing"], "architectural_verdict": false}]
        Hope this helps!"""
        mock_completion.return_value = mock_response

        result = analyze_focus_area("agent_orchestration")

        assert result is not None
        assert len(result) == 1
        assert result[0]["tool_name"] == "Tool1"

    @patch("app.services.grok_service.litellm.completion")
    def test_invalid_json_returns_none(self, mock_completion):
        """Test that invalid JSON returns None."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is not valid JSON"
        mock_completion.return_value = mock_response

        result = analyze_focus_area("durable_runtime")

        assert result is None

    @patch("app.services.grok_service.litellm.completion")
    def test_api_error_returns_none(self, mock_completion):
        """Test that API errors return None."""
        mock_completion.side_effect = Exception("API Error")

        result = analyze_focus_area("voice_ai_ux")

        assert result is None


class TestRunFullAnalysis:
    """Test full analysis across all focus areas."""

    @patch("app.services.grok_service.analyze_focus_area")
    def test_aggregates_all_focus_areas(self, mock_analyze):
        """Test that full analysis aggregates results from all areas."""
        mock_analyze.side_effect = [
            [{"tool_name": "VoiceTool", "focus_area": "voice_ai_ux"}],
            [{"tool_name": "AgentTool", "focus_area": "agent_orchestration"}],
            [{"tool_name": "RuntimeTool", "focus_area": "durable_runtime"}],
        ]

        result = run_full_analysis()

        assert "radar_date" in result
        assert "trends" in result
        assert len(result["trends"]) == 3

    @patch("app.services.grok_service.analyze_focus_area")
    def test_handles_partial_failures(self, mock_analyze):
        """Test that partial failures don't break full analysis."""
        mock_analyze.side_effect = [
            [{"tool_name": "VoiceTool", "focus_area": "voice_ai_ux"}],
            None,  # Failed analysis
            [{"tool_name": "RuntimeTool", "focus_area": "durable_runtime"}],
        ]

        result = run_full_analysis()

        assert len(result["trends"]) == 2

    @patch("app.services.grok_service.analyze_focus_area")
    def test_returns_empty_trends_on_total_failure(self, mock_analyze):
        """Test that total failure returns empty trends list."""
        mock_analyze.return_value = None

        result = run_full_analysis()

        assert result["trends"] == []
        assert "radar_date" in result
