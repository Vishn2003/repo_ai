import pytest
from unittest.mock import MagicMock
from tools.validators import VLMAnalysis

@pytest.fixture
def mock_vlm_analysis():
    return VLMAnalysis(
        claimed_issue_type="dent",
        claimed_object_part="front_bumper",
        visible_issue_type="dent",
        visible_object_part="front_bumper",
        evidence_standard_met=True,
        evidence_standard_met_reason="Bumper is fully visible in img_1",
        image_quality_flags=["none"],
        claim_status="supported",
        claim_status_justification="img_1 clearly shows a 3-inch dent on the front bumper.",
        supporting_image_ids=["img_1"],
        valid_image=True,
        severity="medium"
    )

@pytest.fixture
def mock_vlm_analysis_insufficient():
    return VLMAnalysis(
        claimed_issue_type="scratch",
        claimed_object_part="side_mirror",
        visible_issue_type="unknown",
        visible_object_part="unknown",
        evidence_standard_met=False,
        evidence_standard_met_reason="Image img_2 is extremely blurry",
        image_quality_flags=["blurry_image"],
        claim_status="not_enough_information",
        claim_status_justification="Cannot evaluate claim due to blurry images.",
        supporting_image_ids=["none"],
        valid_image=True,
        severity="unknown"
    )

@pytest.fixture
def mock_vlm_analysis_manipulated():
    return VLMAnalysis(
        claimed_issue_type="crack",
        claimed_object_part="windshield",
        visible_issue_type="crack",
        visible_object_part="windshield",
        evidence_standard_met=True,
        evidence_standard_met_reason="Windshield visible in img_1",
        image_quality_flags=["possible_manipulation"],
        claim_status="supported",
        claim_status_justification="img_1 shows a crack but the metadata is anomalous.",
        supporting_image_ids=["img_1"],
        valid_image=True,
        severity="low"
    )
