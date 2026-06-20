import os
import time
import logging
import asyncio
import argparse
import pandas as pd
import pathlib

from config import Config
from tools.validators import VLMAnalysis
from tools.gemini_tool import GeminiTool
from tools.file_handler import FileHandlerTool
from agents.evidence_analyzer import EvidenceAnalyzerAgent
from agents.severity_classifier import SeverityClassifierAgent
from agents.report_generator import ReportGeneratorAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ClaimReviewOrchestrator:
    def __init__(self, gemini_tool: GeminiTool = None):
        self.file_handler = FileHandlerTool()
        self.gemini_tool = gemini_tool or GeminiTool()
        
        self.analyzer = EvidenceAnalyzerAgent(self.gemini_tool)
        self.classifier = SeverityClassifierAgent()
        self.reporter = ReportGeneratorAgent()

    async def process_claims(
        self,
        input_csv_path: str,
        history_csv_path: str,
        evidence_requirements_csv_path: str,
        output_csv_path: str,
        model_name: str = Config.DEFAULT_MODEL,
        dataset_root: str = Config.DATASET_ROOT,
        sleep_time: float = Config.SLEEP_TIME,
        use_history: bool = True
    ) -> pd.DataFrame:
        """
        Runs the end-to-end multi-agent verification pipeline.
        """
        logger.info(f"Starting Multi-Agent Claim Verification Pipeline using VLM model: {model_name}")
        
        # 1. Load data
        claims_df = self.file_handler.load_claims_csv(input_csv_path)
        history_df = self.file_handler.load_user_history(history_csv_path)
        evidence_df = self.file_handler.load_evidence_requirements(evidence_requirements_csv_path)
        
        logger.info(f"Loaded {len(claims_df)} claims, {len(history_df)} history, {len(evidence_df)} evidence requirements.")
        
        results = []
        
        # 2. Loop through claims
        for idx, row in claims_df.iterrows():
            user_id = row['user_id']
            image_paths_str = str(row['image_paths'])
            user_claim = row['user_claim']
            claim_object = row['claim_object']
            
            logger.info(f"[{idx+1}/{len(claims_df)}] Processing claim for User: {user_id}, Object: {claim_object}")
            
            # Parse image paths
            image_paths = [p.strip() for p in image_paths_str.split(";") if p.strip()]
            image_ids = [pathlib.Path(p).stem for p in image_paths]
            
            # Match history
            if use_history:
                history_context = self.file_handler.get_user_history_context(user_id, history_df)
            else:
                history_context = {
                    "history_flags": "none",
                    "history_summary": "none"
                }
                
            requirements_str = self.file_handler.get_requirements_for_object(claim_object, evidence_df)
            
            images = []
            load_failed = False
            fail_reason = ""
            
            # Load images
            try:
                images = self.gemini_tool.load_and_preprocess_images(image_paths, dataset_root=dataset_root)
                if not images:
                    load_failed = True
                    fail_reason = "No image paths provided"
            except Exception as e:
                load_failed = True
                fail_reason = str(e)
                logger.error(f"Image loading failed for claim {idx}: {fail_reason}")
                
            if load_failed:
                # Direct fallback when loading fails
                fallback_vlm = VLMAnalysis(
                    claimed_issue_type="unknown",
                    claimed_object_part="unknown",
                    visible_issue_type="unknown",
                    visible_object_part="unknown",
                    evidence_standard_met=False,
                    evidence_standard_met_reason=f"Failed to load images: {fail_reason}",
                    image_quality_flags=["blurry_image"],
                    claim_status="not_enough_information",
                    claim_status_justification=f"Image review could not be completed. Error: {fail_reason}",
                    supporting_image_ids=["none"],
                    valid_image=False,
                    severity="unknown"
                )
                csv_row = await self.classifier.run(
                    vlm_out=fallback_vlm,
                    history_flags=history_context["history_flags"],
                    image_ids=image_ids,
                    input_row=row.to_dict()
                )
            else:
                try:
                    # Agent 1: Vision Evidence Analysis
                    vlm_out = await self.analyzer.run(
                        claim_object=claim_object,
                        user_claim=user_claim,
                        requirements_str=requirements_str,
                        image_ids=image_ids,
                        images=images,
                        model_name=model_name
                    )
                    
                    # Agent 2: Severity Classification and Risk Scoring
                    csv_row = await self.classifier.run(
                        vlm_out=vlm_out,
                        history_flags=history_context["history_flags"],
                        image_ids=image_ids,
                        input_row=row.to_dict()
                    )
                except Exception as e:
                    logger.error(f"Agent processing failed for claim {idx}: {e}. Using safety fallback.")
                    fallback_vlm = VLMAnalysis(
                        claimed_issue_type="unknown",
                        claimed_object_part="unknown",
                        visible_issue_type="unknown",
                        visible_object_part="unknown",
                        evidence_standard_met=False,
                        evidence_standard_met_reason="Analyzer failed or timed out",
                        image_quality_flags=["manual_review_required"],
                        claim_status="not_enough_information",
                        claim_status_justification=f"Service error during execution: {e}",
                        supporting_image_ids=["none"],
                        valid_image=False,
                        severity="unknown"
                    )
                    csv_row = await self.classifier.run(
                        vlm_out=fallback_vlm,
                        history_flags=history_context["history_flags"],
                        image_ids=image_ids,
                        input_row=row.to_dict()
                    )
                    
            results.append(csv_row)
            
            # Rate limit throttle sleep
            if idx < len(claims_df) - 1:
                logger.info(f"Sleeping for {sleep_time}s to respect rate limits...")
                time.sleep(sleep_time)
                
        # 3. Agent 3: CSV and HTML Report Generation
        # Write output HTML report to outputs/report.html
        html_out_path = os.path.join(os.path.dirname(output_csv_path) or ".", "outputs", "report.html")
        await self.reporter.run(
            claims_list=results,
            output_csv_path=output_csv_path,
            output_html_path=html_out_path
        )
        
        return pd.DataFrame(results)

def run_pipeline(
    input_csv_path: str,
    history_csv_path: str,
    evidence_requirements_csv_path: str,
    output_csv_path: str,
    model_name: str = Config.DEFAULT_MODEL,
    dataset_root: str = Config.DATASET_ROOT,
    sleep_time: float = Config.SLEEP_TIME,
    use_history: bool = True
) -> pd.DataFrame:
    """Synchronous pipeline wrapper to maintain compatibility with evaluation frameworks."""
    orchestrator = ClaimReviewOrchestrator()
    
    # Run async function in sync wrapper
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop and loop.is_running():
        # If loop is already running, schedule as a task and run it
        return asyncio.run_coroutine_threadsafe(
            orchestrator.process_claims(
                input_csv_path=input_csv_path,
                history_csv_path=history_csv_path,
                evidence_requirements_csv_path=evidence_requirements_csv_path,
                output_csv_path=output_csv_path,
                model_name=model_name,
                dataset_root=dataset_root,
                sleep_time=sleep_time,
                use_history=use_history
            ),
            loop
        ).result()
    else:
        # Standard run if loop not running
        return asyncio.run(
            orchestrator.process_claims(
                input_csv_path=input_csv_path,
                history_csv_path=history_csv_path,
                evidence_requirements_csv_path=evidence_requirements_csv_path,
                output_csv_path=output_csv_path,
                model_name=model_name,
                dataset_root=dataset_root,
                sleep_time=sleep_time,
                use_history=use_history
            )
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Agent Claims Verification System")
    parser.add_argument("--input", default="dataset/claims.csv", help="Path to input claims.csv")
    parser.add_argument("--history", default="dataset/user_history.csv", help="Path to user_history.csv")
    parser.add_argument("--evidence", default="dataset/evidence_requirements.csv", help="Path to evidence_requirements.csv")
    parser.add_argument("--output", default="output.csv", help="Path to save output.csv")
    parser.add_argument("--model", default=Config.DEFAULT_MODEL, help="Model name to use")
    parser.add_argument("--sleep", type=float, default=Config.SLEEP_TIME, help="Rate limit sleep time in seconds")
    parser.add_argument("--no-history", action="store_true", help="Disable using historical user context")
    
    args = parser.parse_args()
    
    run_pipeline(
        input_csv_path=args.input,
        history_csv_path=args.history,
        evidence_requirements_csv_path=args.evidence,
        output_csv_path=args.output,
        model_name=args.model,
        dataset_root="dataset",
        sleep_time=args.sleep,
        use_history=not args.no_history
    )
