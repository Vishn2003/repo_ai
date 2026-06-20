import logging
from agents.base_agent import BaseAgent
from tools.validators import (
    VLMAnalysis, ALLOWED_ISSUE_TYPES, ALLOWED_SEVERITY, ALLOWED_RISK_FLAGS,
    ALLOWED_CAR_PARTS, ALLOWED_LAPTOP_PARTS, ALLOWED_PACKAGE_PARTS
)

logger = logging.getLogger(__name__)

class SeverityClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("SeverityClassifierAgent")

    async def run(
        self,
        vlm_out: VLMAnalysis,
        history_flags: str,
        image_ids: list,
        input_row: dict
    ) -> dict:
        """
        Processes VLM analysis, applies decision fallbacks, incorporates user history risk flags,
        and runs schema validations to output a fully compliant claim verification result.
        """
        self.log("INFO", "Running decision finalization and risk classification.")
        
        # 1. Compile and combine risk flags
        risk_list = []
        
        # Clean and add VLM detected flags
        for flag in vlm_out.image_quality_flags:
            cleaned_flag = flag.strip().lower()
            if cleaned_flag in ALLOWED_RISK_FLAGS and cleaned_flag != "none":
                risk_list.append(cleaned_flag)
                
        # Add user history flags
        if history_flags and history_flags.strip().lower() != "none":
            for flag in history_flags.split(";"):
                cleaned_flag = flag.strip().lower()
                if cleaned_flag in ALLOWED_RISK_FLAGS and cleaned_flag != "none":
                    risk_list.append(cleaned_flag)
                    
        # De-duplicate flags while preserving order
        unique_risks = []
        for r in risk_list:
            if r not in unique_risks:
                unique_risks.append(r)
                
        # 2. Programmatic fallbacks
        evidence_standard_met = vlm_out.evidence_standard_met
        claim_status = vlm_out.claim_status.strip().lower()
        
        # If evidence standard is not met, force claim_status to not_enough_information
        if not evidence_standard_met:
            claim_status = "not_enough_information"
            # If no image quality issues are flagged, mark it as damage_not_visible
            quality_indicators = ["blurry_image", "cropped_or_obstructed", "low_light_or_glare", "wrong_angle"]
            if not any(indicator in unique_risks for indicator in quality_indicators):
                if "damage_not_visible" not in unique_risks:
                    unique_risks.append("damage_not_visible")
                    
        # 3. Enforce valid_image consistency
        valid_image = vlm_out.valid_image
        unusable_flags = ["possible_manipulation", "non_original_image"]
        if any(unusable_flag in unique_risks for unusable_flag in unusable_flags):
            valid_image = False
            
        # If the image is not valid, it should lead to contradicted or not_enough_information
        if not valid_image and claim_status == "supported":
            claim_status = "not_enough_information"
            
        # 4. Severity consistency
        severity = vlm_out.severity.strip().lower()
        if claim_status == "not_enough_information" and severity == "none":
            severity = "unknown"
            
        # Re-compile risk flags string
        final_risk_flags = ";".join(unique_risks) if unique_risks else "none"
        
        # 5. Clean supporting image IDs
        # Supporting images must match the filenames without extension
        valid_names = {img_id.strip() for img_id in image_ids}
        cleaned_supporting_ids = []
        for img_id in vlm_out.supporting_image_ids:
            cleaned_id = img_id.strip()
            if cleaned_id in valid_names:
                cleaned_supporting_ids.append(cleaned_id)
                
        # If empty or explicitly ['none'], set to ['none']
        if not cleaned_supporting_ids or "none" in cleaned_supporting_ids:
            cleaned_supporting_ids = ["none"]
            
        # If claim_status is not_enough_information, supporting images should be none
        if claim_status == "not_enough_information":
            cleaned_supporting_ids = ["none"]
            
        # 6. Map to 14-column output format
        evidence_standard_met_str = str(evidence_standard_met).lower()
        valid_image_str = str(valid_image).lower()
        supporting_images_str = ";".join(cleaned_supporting_ids)
        
        # Ensure issue_type and object_part are the visible ones
        visible_issue_type = vlm_out.visible_issue_type.strip().lower()
        visible_object_part = vlm_out.visible_object_part.strip().lower()
        
        final_row = {
            "user_id": input_row["user_id"],
            "image_paths": input_row["image_paths"],
            "user_claim": input_row["user_claim"],
            "claim_object": input_row["claim_object"],
            "evidence_standard_met": evidence_standard_met_str,
            "evidence_standard_met_reason": vlm_out.evidence_standard_met_reason,
            "risk_flags": final_risk_flags,
            "issue_type": visible_issue_type,
            "object_part": visible_object_part,
            "claim_status": claim_status,
            "claim_status_justification": vlm_out.claim_status_justification,
            "supporting_image_ids": supporting_images_str,
            "valid_image": valid_image_str,
            "severity": severity
        }
        
        # 7. Validate output types/bounds to guarantee schema compatibility
        validated_row = self._validate_row(final_row)
        return validated_row

    def _validate_row(self, row_dict: dict) -> dict:
        """
        Validates that a row matches all allowed values and formats.
        Adjusts values where possible to conform to schema rather than crashing.
        """
        # 1. claim_status
        status = row_dict["claim_status"].strip().lower()
        if status not in ["supported", "contradicted", "not_enough_information"]:
            logger.warning(f"Invalid claim_status: {status}. Defaulting to not_enough_information.")
            row_dict["claim_status"] = "not_enough_information"
            
        # 2. issue_type
        issue = row_dict["issue_type"].strip().lower()
        if issue not in ALLOWED_ISSUE_TYPES:
            logger.warning(f"Invalid issue_type: {issue}. Defaulting to unknown.")
            row_dict["issue_type"] = "unknown"
            
        # 3. object_part (validated against specific object parts list)
        obj = row_dict["claim_object"].strip().lower()
        part = row_dict["object_part"].strip().lower()
        
        if obj == "car":
            allowed_parts = ALLOWED_CAR_PARTS
        elif obj == "laptop":
            allowed_parts = ALLOWED_LAPTOP_PARTS
        elif obj == "package":
            allowed_parts = ALLOWED_PACKAGE_PARTS
        else:
            allowed_parts = ["unknown"]
            
        if part not in allowed_parts:
            logger.warning(f"Invalid part {part} for object {obj}. Defaulting to unknown.")
            row_dict["object_part"] = "unknown"
            
        # 4. severity
        sev = row_dict["severity"].strip().lower()
        if sev not in ALLOWED_SEVERITY:
            logger.warning(f"Invalid severity: {sev}. Defaulting to unknown.")
            row_dict["severity"] = "unknown"
            
        # 5. risk_flags
        flags = row_dict["risk_flags"].strip().lower()
        if flags != "none":
            cleaned_flags = []
            for flag in flags.split(";"):
                f = flag.strip()
                if f in ALLOWED_RISK_FLAGS:
                    cleaned_flags.append(f)
            row_dict["risk_flags"] = ";".join(cleaned_flags) if cleaned_flags else "none"
            
        # 6. booleans format
        row_dict["evidence_standard_met"] = str(row_dict["evidence_standard_met"]).lower()
        row_dict["valid_image"] = str(row_dict["valid_image"]).lower()
        
        return row_dict
