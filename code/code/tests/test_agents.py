import pytest
from unittest.mock import MagicMock, AsyncMock
from tools.validators import VLMAnalysis
from agents.evidence_analyzer import EvidenceAnalyzerAgent
from agents.severity_classifier import SeverityClassifierAgent
from agents.report_generator import ReportGeneratorAgent

# Test Evidence Analyzer Agent
@pytest.mark.asyncio
async def test_evidence_analyzer_sanitization():
    mock_gemini = MagicMock()
    mock_gemini.call_gemini_vision.return_value = VLMAnalysis(
        claimed_issue_type="dent", claimed_object_part="door",
        visible_issue_type="dent", visible_object_part="door",
        evidence_standard_met=True, evidence_standard_met_reason="Good",
        image_quality_flags=["none"], claim_status="supported",
        claim_status_justification="Verified", supporting_image_ids=["img_1"],
        valid_image=True, severity="low"
    )
    
    agent = EvidenceAnalyzerAgent(gemini_tool=mock_gemini)
    
    # Text with control chars and extra spacing
    dirty_text = "Claim text \x00 with  some   spaces \r\n and control chars"
    await agent.run(
        claim_object="car",
        user_claim=dirty_text,
        requirements_str="checklist",
        image_ids=["img_1"],
        images=[MagicMock()]
    )
    
    # Assert call was made with sanitized text
    mock_gemini.call_gemini_vision.assert_called_once()
    prompt_arg = mock_gemini.call_gemini_vision.call_args[1]["prompt"]
    assert "\x00" not in prompt_arg
    assert "Claim text with some spaces and control chars" in prompt_arg

# Test Severity Classifier Agent
@pytest.mark.asyncio
async def test_severity_classifier_risk_merging(mock_vlm_analysis):
    agent = SeverityClassifierAgent()
    input_row = {
        "user_id": "usr_001",
        "image_paths": "images/case_01/img_1.jpg",
        "user_claim": "Dent",
        "claim_object": "car"
    }
    
    # Test merging history flags
    result = await agent.run(
        vlm_out=mock_vlm_analysis,
        history_flags="user_history_risk;manual_review_required",
        image_ids=["img_1"],
        input_row=input_row
    )
    
    # Verify flags are merged, de-duplicated and joined
    assert "user_history_risk" in result["risk_flags"]
    assert "manual_review_required" in result["risk_flags"]
    
@pytest.mark.asyncio
async def test_severity_classifier_evidence_fallback(mock_vlm_analysis_insufficient):
    agent = SeverityClassifierAgent()
    input_row = {
        "user_id": "usr_001",
        "image_paths": "images/case_01/img_2.jpg",
        "user_claim": "Scratch",
        "claim_object": "car"
    }
    
    result = await agent.run(
        vlm_out=mock_vlm_analysis_insufficient,
        history_flags="none",
        image_ids=["img_2"],
        input_row=input_row
    )
    
    # If evidence standard met is false, status should be forced to not_enough_information
    assert result["evidence_standard_met"] == "false"
    assert result["claim_status"] == "not_enough_information"
    assert "blurry_image" in result["risk_flags"]

@pytest.mark.asyncio
async def test_severity_classifier_integrity_fallback(mock_vlm_analysis_manipulated):
    agent = SeverityClassifierAgent()
    input_row = {
        "user_id": "usr_001",
        "image_paths": "images/case_01/img_1.jpg",
        "user_claim": "Crack",
        "claim_object": "car"
    }
    
    result = await agent.run(
        vlm_out=mock_vlm_analysis_manipulated,
        history_flags="none",
        image_ids=["img_1"],
        input_row=input_row
    )
    
    # Manipulation flag should force valid_image to false
    assert result["valid_image"] == "false"
    # An invalid image cannot support a claim, forces status to not_enough_information
    assert result["claim_status"] == "not_enough_information"
