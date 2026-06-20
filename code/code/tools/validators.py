from pydantic import BaseModel, Field
from typing import List, Literal

ALLOWED_ISSUE_TYPES = [
    "dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part", 
    "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown"
]

ALLOWED_CAR_PARTS = [
    "front_bumper", "rear_bumper", "door", "hood", "windshield", "side_mirror", 
    "headlight", "taillight", "fender", "quarter_panel", "body", "unknown"
]

ALLOWED_LAPTOP_PARTS = [
    "screen", "keyboard", "trackpad", "hinge", "lid", "corner", "port", "base", "body", "unknown"
]

ALLOWED_PACKAGE_PARTS = [
    "box", "package_corner", "package_side", "seal", "label", "contents", "item", "unknown"
]

ALLOWED_SEVERITY = ["none", "low", "medium", "high", "unknown"]

ALLOWED_RISK_FLAGS = [
    "none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare", "wrong_angle",
    "wrong_object", "wrong_object_part", "damage_not_visible", "claim_mismatch",
    "possible_manipulation", "non_original_image", "text_instruction_present",
    "user_history_risk", "manual_review_required"
]

# Combined allowed parts list for schema validation
ALL_PARTS = list(set(ALLOWED_CAR_PARTS + ALLOWED_LAPTOP_PARTS + ALLOWED_PACKAGE_PARTS))

ALLOWED_ISSUE_TYPES_LITERAL = Literal[
    "dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part", 
    "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown"
]

ALLOWED_PARTS_LITERAL = Literal[
    "front_bumper", "rear_bumper", "door", "hood", "windshield", "side_mirror", 
    "headlight", "taillight", "fender", "quarter_panel", "body", "screen", 
    "keyboard", "trackpad", "hinge", "lid", "corner", "port", "base", "box", 
    "package_corner", "package_side", "seal", "label", "contents", "item", "unknown"
]

ALLOWED_SEVERITY_LITERAL = Literal["none", "low", "medium", "high", "unknown"]

ALLOWED_STATUS_LITERAL = Literal["supported", "contradicted", "not_enough_information"]

class VLMAnalysis(BaseModel):
    claimed_issue_type: ALLOWED_ISSUE_TYPES_LITERAL = Field(
        description="The issue type claimed by the user in the text conversation."
    )
    claimed_object_part: ALLOWED_PARTS_LITERAL = Field(
        description="The part of the object claimed by the user in the text conversation."
    )
    visible_issue_type: ALLOWED_ISSUE_TYPES_LITERAL = Field(
        description="The issue type visually visible in the images."
    )
    visible_object_part: ALLOWED_PARTS_LITERAL = Field(
        description="The part of the object visually visible in the images."
    )
    evidence_standard_met: bool = Field(
        description="Whether the submitted images meet the minimum evidence requirements to inspect the claim."
    )
    evidence_standard_met_reason: str = Field(
        description="A short reason (1 sentence) for the evidence decision."
    )
    image_quality_flags: List[str] = Field(
        description="Any quality, mismatch, or manipulation risks detected in the images. List of strings from ALLOWED_RISK_FLAGS."
    )
    claim_status: ALLOWED_STATUS_LITERAL = Field(
        description="The claim decision based on image evidence: 'supported', 'contradicted', or 'not_enough_information'."
    )
    claim_status_justification: str = Field(
        description="Concise, image-grounded explanation. MUST explicitly reference image IDs (e.g. img_1, img_2)."
    )
    supporting_image_ids: List[str] = Field(
        description="List of image IDs (filenames without extension) that support the decision, or ['none']."
    )
    valid_image: bool = Field(
        description="Whether the image set is usable and authentic (False if fake, manipulated, or wrong object)."
    )
    severity: ALLOWED_SEVERITY_LITERAL = Field(
        description="The visual severity of the damage."
    )
