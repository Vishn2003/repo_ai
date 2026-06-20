import os
import json
import logging
from datetime import datetime
import pandas as pd
from jinja2 import Template
from agents.base_agent import BaseAgent
from config import Config

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claims Verification Report</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --primary: #3b82f6;
            
            --success-glow: rgba(16, 185, 129, 0.15);
            --warning-glow: rgba(245, 158, 11, 0.15);
            --danger-glow: rgba(239, 68, 68, 0.15);
            --primary-glow: rgba(59, 130, 246, 0.15);
        }
        
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 40px;
        }
        
        h1 {
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .timestamp {
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        .stat-card .value {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .stat-card .label {
            color: var(--text-muted);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stat-card.total { border-left: 4px solid var(--primary); }
        .stat-card.supported { border-left: 4px solid var(--success); color: var(--success); }
        .stat-card.contradicted { border-left: 4px solid var(--danger); color: var(--danger); }
        .stat-card.insufficient { border-left: 4px solid var(--warning); color: var(--warning); }
        
        .claims-list {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        
        .claim-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .claim-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
        }
        
        .claim-header {
            padding: 20px 24px;
            background: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .user-id {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .claim-object {
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.08);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }
        
        .status-badge {
            padding: 6px 14px;
            border-radius: 30px;
            font-weight: 700;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .status-badge.supported {
            background: var(--success-glow);
            color: var(--success);
            border: 1px solid var(--success);
        }
        
        .status-badge.contradicted {
            background: var(--danger-glow);
            color: var(--danger);
            border: 1px solid var(--danger);
        }
        
        .status-badge.not_enough_information {
            background: var(--warning-glow);
            color: var(--warning);
            border: 1px solid var(--warning);
        }
        
        .claim-body {
            padding: 24px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }
        
        @media (max-width: 768px) {
            .claim-body {
                grid-template-columns: 1fr;
            }
        }
        
        .details-col {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .detail-item {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        
        .detail-label {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .detail-value {
            font-size: 0.95rem;
        }
        
        .claim-text-box {
            background: rgba(0, 0, 0, 0.2);
            padding: 12px 16px;
            border-radius: 8px;
            border-left: 3px solid var(--primary);
            font-style: italic;
        }
        
        .justification-box {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            padding: 16px;
            border-radius: 12px;
        }
        
        .meta-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        
        .meta-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }
        
        .meta-card .val {
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 4px;
            text-transform: uppercase;
        }
        
        .meta-card .val.true { color: var(--success); }
        .meta-card .val.false { color: var(--danger); }
        
        .flags-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 4px;
        }
        
        .flag-pill {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }
        
        .flag-pill.none {
            background: rgba(148, 163, 184, 0.1);
            color: var(--text-muted);
            border: 1px solid rgba(148, 163, 184, 0.2);
        }
        
        .images-col {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .image-paths-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .image-path-item {
            background: rgba(0, 0, 0, 0.15);
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px dashed var(--border-color);
            font-size: 0.85rem;
            word-break: break-all;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .img-badge {
            padding: 2px 6px;
            border-radius: 4px;
            background: var(--primary);
            color: white;
            font-size: 0.7rem;
            font-weight: 700;
        }
        
        .supporting-tag {
            color: var(--success);
            font-size: 0.8rem;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Claims Verification Audit Report</h1>
                <div class="timestamp">Generated: {{ timestamp }}</div>
            </div>
            <div style="text-align: right;">
                <span class="status-badge supported">Multi-Agent System</span>
            </div>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card total">
                <span class="value">{{ total_claims }}</span>
                <span class="label">Total Claims Evaluated</span>
            </div>
            <div class="stat-card supported">
                <span class="value">{{ total_supported }}</span>
                <span class="label">Supported</span>
            </div>
            <div class="stat-card contradicted">
                <span class="value">{{ total_contradicted }}</span>
                <span class="label">Contradicted</span>
            </div>
            <div class="stat-card insufficient">
                <span class="value">{{ total_insufficient }}</span>
                <span class="label">Insufficient Evidence</span>
            </div>
        </div>
        
        <h2 style="font-size: 1.4rem; margin-bottom: 24px; font-weight: 600;">Verification Case Studies</h2>
        
        <div class="claims-list">
            {% for claim in claims %}
            <div class="claim-card">
                <div class="claim-header">
                    <div class="user-info">
                        <span class="user-id">User: {{ claim.user_id }}</span>
                        <span class="claim-object">{{ claim.claim_object }}</span>
                    </div>
                    <span class="status-badge {{ claim.claim_status }}">{{ claim.claim_status.replace('_', ' ') }}</span>
                </div>
                <div class="claim-body">
                    <div class="details-col">
                        <div class="detail-item">
                            <span class="detail-label">User Claim Conversation</span>
                            <div class="claim-text-box">"{{ claim.user_claim }}"</div>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Evaluation Justification</span>
                            <div class="justification-box">{{ claim.claim_status_justification }}</div>
                        </div>
                        
                        <div class="meta-grid">
                            <div class="meta-card">
                                <span class="detail-label">Evidence Standard Met</span>
                                <div class="val {{ claim.evidence_standard_met }}">{{ claim.evidence_standard_met }}</div>
                                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">{{ claim.evidence_standard_met_reason }}</div>
                            </div>
                            <div class="meta-card">
                                <span class="detail-label">Visual Authenticity</span>
                                <div class="val {{ claim.valid_image }}">{{ 'AUTHENTIC' if claim.valid_image == 'true' else 'UNRELIABLE' }}</div>
                            </div>
                            <div class="meta-card">
                                <span class="detail-label">Issue & Part Detected</span>
                                <div class="val" style="color: var(--primary); font-size: 0.95rem; margin-top: 4px;">
                                    {{ claim.issue_type }} / {{ claim.object_part }}
                                </div>
                            </div>
                            <div class="meta-card">
                                <span class="detail-label">Damage Severity</span>
                                <div class="val" style="color: var(--warning); font-size: 0.95rem; margin-top: 4px;">
                                    {{ claim.severity }}
                                </div>
                            </div>
                        </div>
                        
                        <div class="detail-item">
                            <span class="detail-label">Risk Flags Triggered</span>
                            <div class="flags-container">
                                {% if claim.risk_flags != 'none' %}
                                    {% for flag in claim.risk_flags.split(';') %}
                                        <span class="flag-pill">{{ flag }}</span>
                                    {% endfor %}
                                {% else %}
                                    <span class="flag-pill none">None</span>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    
                    <div class="images-col">
                        <span class="detail-label">Submitted Image Files</span>
                        <div class="image-paths-list">
                            {% for img_path in claim.image_paths.split(';') %}
                                <div class="image-path-item">
                                    <span>{{ img_path.split('/')[-1] }}</span>
                                    {% set img_id = img_path.split('/')[-1].split('.')[0] %}
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <span class="img-badge">{{ img_id }}</span>
                                        {% if img_id in claim.supporting_image_ids.split(';') %}
                                            <span class="supporting-tag">✓ Supporting Evidence</span>
                                        {% endif %}
                                    </div>
                                </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

class ReportGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReportGeneratorAgent")

    async def run(
        self,
        claims_list: list,
        output_csv_path: str,
        output_html_path: str = None
    ) -> dict:
        """
        Saves predictions to output_csv_path and generates a premium HTML audit report.
        """
        self.log("INFO", f"Writing final CSV output to: {output_csv_path}")
        
        # 1. Convert to pandas DataFrame and save CSV
        output_df = pd.DataFrame(claims_list)
        
        # Enforce exact column ordering as per problem specification
        columns = [
            "user_id", "image_paths", "user_claim", "claim_object",
            "evidence_standard_met", "evidence_standard_met_reason", "risk_flags",
            "issue_type", "object_part", "claim_status", "claim_status_justification",
            "supporting_image_ids", "valid_image", "severity"
        ]
        output_df = output_df[columns]
        output_df.to_csv(output_csv_path, index=False)
        self.log("INFO", "CSV writing complete.")
        
        # 2. Compile stats for report
        total_claims = len(claims_list)
        total_supported = sum(1 for c in claims_list if c["claim_status"] == "supported")
        total_contradicted = sum(1 for c in claims_list if c["claim_status"] == "contradicted")
        total_insufficient = sum(1 for c in claims_list if c["claim_status"] == "not_enough_information")
        
        # 3. Generate HTML report if path provided
        if output_html_path:
            self.log("INFO", f"Generating HTML audit report at: {output_html_path}")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_html_path)), exist_ok=True)
            
            template = Template(HTML_TEMPLATE)
            rendered_html = template.render(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_claims=total_claims,
                total_supported=total_supported,
                total_contradicted=total_contradicted,
                total_insufficient=total_insufficient,
                claims=claims_list
            )
            
            with open(output_html_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)
            self.log("INFO", "HTML audit report generated successfully.")
            
        return {
            "total_claims": total_claims,
            "supported": total_supported,
            "contradicted": total_contradicted,
            "insufficient": total_insufficient,
            "csv_path": output_csv_path,
            "html_path": output_html_path
        }
