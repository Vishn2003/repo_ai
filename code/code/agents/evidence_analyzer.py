import re
import logging
from agents.base_agent import BaseAgent
from tools.gemini_tool import GeminiTool
from tools.validators import VLMAnalysis
from config import Config

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """
You are an expert multi-modal claims verification agent.
Analyze the following damage claim details and the attached images to make a structured determination.

--- CLAIM CONTEXT ---
CLAIM OBJECT: {claim_object}
USER CONVERSATION:
{user_claim}

--- MINIMUM EVIDENCE REQUIREMENTS ---
{evidence_requirements}

--- IMAGE DIRECTORY & IDS ---
The attached images correspond to the following IDs in order:
{image_ids_ordered}

--- INSTRUCTIONS ---
1. Read the USER CONVERSATION and extract:
   - What damage type does the user claim? (Must be one of the ALLOWED_ISSUE_TYPES: "dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part", "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown")
   - What part does the user claim is damaged? (Must be one of the allowed parts: "front_bumper", "rear_bumper", "door", "hood", "windshield", "side_mirror", "headlight", "taillight", "fender", "quarter_panel", "body", "screen", "keyboard", "trackpad", "hinge", "lid", "corner", "port", "base", "box", "package_corner", "package_side", "seal", "label", "contents", "item", "unknown")
   If ambiguous or not mentioned, set as 'unknown'.
   
2. Inspect the attached images. Determine:
   - What part of the object is actually visible in the images? (visible_object_part. Must be one of the allowed parts listed above)
     - Note: If the image shows a completely wrong object (e.g. food can instead of package), set visible_object_part to 'unknown'.
     - Note: If the image shows a completely different part of the object (e.g. door instead of headlight), and the claimed part is not visible at all, set visible_object_part to the CLAIMED part (e.g. 'headlight').
     - Note: If the image shows a completely different part of the object, and that different part is damaged (e.g. front bumper is smashed but the claim is for a hood scratch), set visible_object_part to the visible part (e.g. 'front_bumper').
   - What damage type is visually visible on that part? (visible_issue_type. Must be one of the ALLOWED_ISSUE_TYPES listed above)
     - Note: If the image shows the wrong object, set visible_issue_type to 'unknown'.
     - Note: If the claimed part is not visible in the image, set visible_issue_type to 'unknown'.
     - Note: If no damage is visible on the claimed/visible part, set visible_issue_type to 'none' and severity to 'none'.
   
3. Check the MINIMUM EVIDENCE REQUIREMENTS:
   - Does the submitted image set meet the minimum evidence required to evaluate this claim? (evidence_standard_met: true/false)
     - Detail the reason in evidence_standard_met_reason.
     - For missing package contents, a photo of an empty open box alone is insufficient evidence (set evidence_standard_met = false).
     - If the image is for a completely different part of the object (e.g. door instead of headlight) and that part is not damaged, set evidence_standard_met = false.
   
4. Assess the visual severity of the damage (severity):
   - 'none': no damage visible.
   - 'low': minor/cosmetic issues (small scratch, minor stain, minor shallow dent, minor cosmetic wear).
   - 'medium': noticeable, clear damage but the object/part is still largely functional or intact (e.g. windshield cracks, screen cracks, sticky keys, broken side mirror, moderate dents, minor tears in packaging). Almost all typical cracked screen, cracked glass, cracked windshield, broken side mirror, or keyboard stain claims should be graded as 'medium' (NOT 'high').
   - 'high': severe structural damage rendering the object/part completely unusable or destroyed (e.g., shattered windshield with a hole or missing glass pieces, screen completely black/dead/shattered into pieces, missing parts, water-damaged non-functioning device, completely crushed/destroyed package, massive body crumpling).
   - 'unknown': when evidence_standard_met is false, or the part is not visible, or cannot be determined.
   
5. Determine any image quality, content, or authenticity risks:
   - Add flags from ALLOWED_RISK_FLAGS to image_quality_flags (e.g., 'blurry_image', 'wrong_angle', 'wrong_object', 'damage_not_visible', 'claim_mismatch', 'possible_manipulation', 'non_original_image').
   - If the image shows a completely wrong object (e.g. food can instead of package), set valid_image to true (since the image is an authentic, reviewable photo), but include 'wrong_object' and 'claim_mismatch' in image_quality_flags.
   - Only set valid_image to false if the image is fake/manipulated or non-original.
   
6. Decide the final claim_status:
   - 'supported': if images clearly show the claimed damage on the claimed part. If at least one image clearly shows the claimed damage, and other images show the whole object undamaged from another angle, set status to supported.
   - 'contradicted':
     - If the images show the claimed part clearly but it is completely undamaged.
     - If the images show a completely different object (e.g. food can instead of shipping box).
     - If the user claims one type of damage (e.g. a dent) but the image shows a completely different type of damage (e.g. only a minor scratch, or no damage at all).
     - If the user claims the seal area was torn/opened, but the seal is intact (even if there is some other minor damage elsewhere on the package like a small dent or corner crease).
     - Note: Be conservative. Minor cosmetic scuffs, scratches, or dust reflections that do not affect functionality should be classified as issue_type = none and claim_status = contradicted (unless a scratch was explicitly claimed, in which case keep low severity).
   - 'not_enough_information': if images are blurry, cropped, wrong angle, or do not show the claimed part at all (e.g. showing door when headlight was claimed), OR if evidence_standard_met is false.
   
7. Ground your justification in the images, referencing the relevant image IDs explicitly (e.g. 'img_1 shows a 2-inch dent', 'img_2 shows the hinge is undamaged').
8. List the image IDs (filenames without extension) that directly support your decision in supporting_image_ids. If none, output ['none'].
"""

class EvidenceAnalyzerAgent(BaseAgent):
    def __init__(self, gemini_tool: GeminiTool = None):
        super().__init__("EvidenceAnalyzerAgent")
        self.gemini = gemini_tool or GeminiTool()

    async def run(
        self,
        claim_object: str,
        user_claim: str,
        requirements_str: str,
        image_ids: list,
        images: list,
        model_name: str = Config.DEFAULT_MODEL
    ) -> VLMAnalysis:
        """
        Runs multimodal vision analysis on claim details and associated images.
        """
        self.log("INFO", f"Analyzing evidence for claim object: {claim_object} with {len(images)} images.")
        
        # 1. Sanitize user claim text to prevent injection & control char issues
        sanitized_claim = self._sanitize_text(user_claim)
        
        image_ids_str = ", ".join(image_ids)
        
        # 2. Format prompt
        prompt = PROMPT_TEMPLATE.format(
            claim_object=claim_object,
            user_claim=sanitized_claim,
            evidence_requirements=requirements_str,
            image_ids_ordered=image_ids_str
        )
        
        # 3. Call Gemini VLM
        vlm_analysis = self.gemini.call_gemini_vision(
            prompt=prompt,
            images=images,
            model_name=model_name
        )
        
        self.log("INFO", f"Claim analyzer complete. Visible issue: {vlm_analysis.visible_issue_type}, Part: {vlm_analysis.visible_object_part}")
        return vlm_analysis

    def _sanitize_text(self, text: str) -> str:
        """Removes control characters and normalizes whitespace."""
        if not text:
            return ""
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Limit length (prevent token explosion/abuse)
        if len(text) > 4000:
            text = text[:4000] + " ... [Truncated]"
        return text
