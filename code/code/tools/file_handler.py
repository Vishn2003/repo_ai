import os
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileHandlerTool:
    @staticmethod
    def load_claims_csv(filepath: str) -> pd.DataFrame:
        """Loads claims CSV file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Claims CSV file not found: {filepath}")
        return pd.read_csv(filepath)

    @staticmethod
    def load_user_history(filepath: str) -> pd.DataFrame:
        """Loads user history CSV file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"User history CSV file not found: {filepath}")
        return pd.read_csv(filepath)

    @staticmethod
    def load_evidence_requirements(filepath: str) -> pd.DataFrame:
        """Loads evidence requirements CSV file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Evidence requirements CSV file not found: {filepath}")
        return pd.read_csv(filepath)

    @staticmethod
    def get_user_history_context(user_id: str, history_df: pd.DataFrame) -> dict:
        """
        Looks up the user history record for user_id.
        Returns a dictionary of history details or defaults for new users.
        """
        user_row = history_df[history_df['user_id'] == user_id]
        if user_row.empty:
            return {
                "past_claim_count": 0,
                "accept_claim": 0,
                "manual_review_claim": 0,
                "rejected_claim": 0,
                "last_90_days_claim_count": 0,
                "history_flags": "none",
                "history_summary": "New user with no prior claim history"
            }
        row = user_row.iloc[0]
        return {
            "past_claim_count": int(row['past_claim_count']),
            "accept_claim": int(row['accept_claim']),
            "manual_review_claim": int(row['manual_review_claim']),
            "rejected_claim": int(row['rejected_claim']),
            "last_90_days_claim_count": int(row['last_90_days_claim_count']),
            "history_flags": str(row['history_flags']),
            "history_summary": str(row['history_summary'])
        }

    @staticmethod
    def get_requirements_for_object(claim_object: str, evidence_df: pd.DataFrame) -> str:
        """
        Filters and retrieves all minimum image evidence requirements
        applicable to a specific claim object (including general 'all' requirements).
        """
        df_filtered = evidence_df[evidence_df['claim_object'].isin([claim_object, 'all'])]
        req_lines = []
        for _, row in df_filtered.iterrows():
            req_lines.append(
                f"- [{row['requirement_id']}] (Applies to: {row['applies_to']}): {row['minimum_image_evidence']}"
            )
        return "\n".join(req_lines)
