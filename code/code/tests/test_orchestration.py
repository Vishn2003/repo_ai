import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import pandas as pd
from main import ClaimReviewOrchestrator, run_pipeline
from tools.validators import VLMAnalysis

@pytest.mark.asyncio
async def test_orchestration_pipeline_success(mock_vlm_analysis):
    # Mock data frames
    claims_df = pd.DataFrame([{
        "user_id": "usr_001",
        "image_paths": "images/test/case_01/img_1.jpg",
        "user_claim": "Dent on bumper",
        "claim_object": "car"
    }])
    
    history_df = pd.DataFrame([{
        "user_id": "usr_001",
        "past_claim_count": 2,
        "accept_claim": 2,
        "manual_review_claim": 0,
        "rejected_claim": 0,
        "last_90_days_claim_count": 1,
        "history_flags": "none",
        "history_summary": "Clean history"
    }])
    
    evidence_df = pd.DataFrame([{
        "requirement_id": "REQ_001",
        "claim_object": "car",
        "applies_to": "dent",
        "minimum_image_evidence": "Clear view of bumper"
    }])
    
    # Mock VLM tool
    mock_gemini = MagicMock()
    mock_gemini.call_gemini_vision.return_value = mock_vlm_analysis
    mock_gemini.load_and_preprocess_images.return_value = [MagicMock()]
    
    orchestrator = ClaimReviewOrchestrator(gemini_tool=mock_gemini)
    
    # Patch file handler loader methods
    with patch.object(orchestrator.file_handler, 'load_claims_csv', return_value=claims_df):
        with patch.object(orchestrator.file_handler, 'load_user_history', return_value=history_df):
            with patch.object(orchestrator.file_handler, 'load_evidence_requirements', return_value=evidence_df):
                with patch.object(orchestrator.reporter, 'run', return_value={"status": "success"}) as mock_report:
                    
                    result_df = await orchestrator.process_claims(
                        input_csv_path="mock_claims.csv",
                        history_csv_path="mock_history.csv",
                        evidence_requirements_csv_path="mock_evidence.csv",
                        output_csv_path="mock_output.csv",
                        sleep_time=0.0
                    )
                    
                    # Verify DataFrame is returned with expected results
                    assert not result_df.empty
                    assert result_df.iloc[0]["claim_status"] == "supported"
                    assert result_df.iloc[0]["severity"] == "medium"
                    assert result_df.iloc[0]["valid_image"] == "true"
                    assert result_df.iloc[0]["evidence_standard_met"] == "true"
                    
                    # Verify reporter was invoked
                    mock_report.assert_called_once()
