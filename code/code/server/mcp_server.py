import os
import sys
import pandas as pd
import pathlib

# Ensure parent directory is in path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.absolute()))

from config import Config
from tools.file_handler import FileHandlerTool
from main import run_pipeline

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    # Fallback or mock FastMCP if not installed yet during bootstrap
    class FastMCP:
        def __init__(self, name):
            self.name = name
        def tool(self):
            def decorator(func):
                return func
            return decorator
        def run(self):
            print("FastMCP running (Mocked: install mcp package to run real server)")

# Create FastMCP server
mcp = FastMCP("claims-reviewer")

@mcp.tool()
def get_evidence_requirements(claim_object: str) -> str:
    """
    Get the minimum image evidence requirements checklist for a claim object (car, laptop, or package).
    """
    evidence_req_path = os.path.join(Config.DATASET_ROOT, "evidence_requirements.csv")
    if not os.path.exists(evidence_req_path):
        return f"Requirements file not found at {evidence_req_path}"
    
    file_handler = FileHandlerTool()
    evidence_df = file_handler.load_evidence_requirements(evidence_req_path)
    return file_handler.get_requirements_for_object(claim_object, evidence_df)

@mcp.tool()
def check_user_history(user_id: str) -> str:
    """
    Looks up user historical claims, rejected claims counts, and historical risk flags.
    """
    history_path = os.path.join(Config.DATASET_ROOT, "user_history.csv")
    if not os.path.exists(history_path):
        return f"History file not found at {history_path}"
    
    file_handler = FileHandlerTool()
    history_df = file_handler.load_user_history(history_path)
    context = file_handler.get_user_history_context(user_id, history_df)
    return (
        f"User History for {user_id}:\n"
        f"- Past Claims: {context['past_claim_count']}\n"
        f"- Approved Claims: {context['accept_claim']}\n"
        f"- Manual Reviews: {context['manual_review_claim']}\n"
        f"- Rejected Claims: {context['rejected_claim']}\n"
        f"- Risk Flags Triggered: {context['history_flags']}\n"
        f"- Summary: {context['history_summary']}"
    )

@mcp.tool()
def verify_claim(
    user_id: str,
    user_claim: str,
    claim_object: str,
    image_paths: str
) -> str:
    """
    Runs the multi-agent claims verification pipeline on a single claim.
    image_paths should be semicolon separated (e.g. 'images/test/case_001/img_1.jpg;images/test/case_001/img_2.jpg')
    """
    # Create a temporary single-row CSV for run_pipeline
    temp_claims_path = "temp_single_claim.csv"
    temp_output_path = "temp_single_output.csv"
    
    df = pd.DataFrame([{
        "user_id": user_id,
        "image_paths": image_paths,
        "user_claim": user_claim,
        "claim_object": claim_object
    }])
    
    df.to_csv(temp_claims_path, index=False)
    
    try:
        run_pipeline(
            input_csv_path=temp_claims_path,
            history_csv_path=os.path.join(Config.DATASET_ROOT, "user_history.csv"),
            evidence_requirements_csv_path=os.path.join(Config.DATASET_ROOT, "evidence_requirements.csv"),
            output_csv_path=temp_output_path,
            sleep_time=0.0  # single row, no need to sleep
        )
        
        # Read the output row
        out_df = pd.read_csv(temp_output_path)
        if out_df.empty:
            return "Claim processing returned empty output."
            
        row = out_df.iloc[0].to_dict()
        
        # Format a nice markdown response
        response = (
            f"### Claim Review Verification Results\n"
            f"- **Claim Status**: {str(row['claim_status']).upper()}\n"
            f"- **Severity**: {str(row['severity']).upper()}\n"
            f"- **Evidence Standard Met?**: {row['evidence_standard_met']}\n"
            f"- **Standard Met Reason**: {row['evidence_standard_met_reason']}\n"
            f"- **Visible Object Part**: {row['object_part']}\n"
            f"- **Visible Damage Issue**: {row['issue_type']}\n"
            f"- **Triggered Risk Flags**: {row['risk_flags']}\n"
            f"- **Authentic Images?**: {row['valid_image']}\n"
            f"- **Justification**: {row['claim_status_justification']}\n"
            f"- **Supporting Image IDs**: {row['supporting_image_ids']}"
        )
        return response
    except Exception as e:
        return f"Error executing claim verification: {e}"
    finally:
        # Clean up temp files
        if os.path.exists(temp_claims_path):
            os.remove(temp_claims_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

if __name__ == "__main__":
    mcp.run()
