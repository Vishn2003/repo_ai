# Multi-Agent Claims Verification System: Multimodal Evidence Audit

Welcome to the production repository for the **Multi-Agent Claims Verification System** developed for the Kaggle Capstone Project. 

This repository implements an advanced, production-grade AI system that verifies visual and textual evidence for damage claims across cars, laptops, and packages, fully adhering to the Kaggle "Agents for Business" track criteria.

---

## Key System Features

1. **Multi-Agent Orchestration**: Out-of-the-box support for modular, specialized agents (Orchestrator, Evidence Analyzer VLM, Severity Classifier, Report Generator) using clean class-based models.
2. **Multimodal VLM Analysis**: Leverages `models/gemini-3.1-flash-lite` to perform zero-shot and structured analysis on claim descriptions and multi-image sets.
3. **Robust Rate-Limiting**: Enforces a strict 12.0-second delay between VLM requests to guarantee safe execution under free-tier API limits.
4. **Local MCP Tools Integration**: Equips agents with custom tool bindings for file handling and image validation.
5. **Offline Test Suite**: Features a complete, mocked unit-testing suite running via `pytest`.
6. **Dockerized Environment**: Ships with standard `Dockerfile` and `docker-compose.yml` configs for instant, containerized deployment.
7. **Premium HTML Reports**: Generates a modern visual analytics dashboard (`outputs/report.html`) complete with metrics, data grids, and case studies.

---

## Repository Layout

```text
.
├── AGENTS.md                         # Rules for AI coding tools + transcript logging
├── problem_statement.md              # Full task description and I/O schema
├── README.md                         # You are here
├── output.csv                        # Final generated prediction outputs (44 rows, 14 columns)
├── code.zip                          # Clean source package for submission
├── claims_verifier_cover.png         # Resized Kaggle writeup cover image (560x280)
├── workflow_infographic.png          # System architecture flowchart
├── claims_auditor_dashboard.png      # Screenshot of the HTML dashboard report
├── code/                             # Production codebase
│   ├── config.py                     # API keys, model variables, rate limits
│   ├── main.py                       # Main CLI entry point (runs the pipeline)
│   ├── Dockerfile                    # Containerization config
│   ├── docker-compose.yml            # Docker Compose multi-service config
│   ├── requirements.txt              # Production python dependencies
│   ├── agents/                       # Specialized AI agent classes
│   │   ├── base_agent.py             # Abstract base agent class
│   │   ├── evidence_analyzer.py      # VLM-powered visual evidence inspector
│   │   ├── severity_classifier.py    # Risk assessment and severity classifer
│   │   └── report_generator.py      # HTML/JSON dashboard output generator
│   ├── tools/                        # Custom toolkits (MCP bindings)
│   │   ├── file_handler.py           # CSV reader and output saver
│   │   └── validators.py             # Image validation and metadata checks
│   ├── server/                       # Model Context Protocol (MCP) server
│   │   └── mcp_server.py             # Custom server exposing system tools
│   ├── tests/                        # Offline Pytest suite
│   │   ├── conftest.py               # Shared mock fixtures
│   │   ├── test_agents.py            # Unit tests for individual agents
│   │   └── test_orchestration.py     # End-to-end mocked pipeline runs
│   └── evaluation/                   # Model and strategy evaluation
│       ├── main.py                   # Strategy comparison runner
│       └── evaluation_report.json    # Strategy comparison analytics
└── dataset/                          # Datasets (CSV + images)
    ├── sample_claims.csv             # Development set (20 rows)
    ├── claims.csv                    # Evaluation set (44 rows)
    ├── user_history.csv              # User risk profile history
    ├── evidence_requirements.csv     # Minimum object verification standards
    └── images/                       # Local JPEG evidence files
```

---

## Quickstart

### 1. Installation & Environment Setup
Clone this repository and navigate to the project directory:
```bash
git clone https://github.com/Vishn2003/ai_agent.git
cd ai_agent
```

Install the required Python dependencies:
```bash
pip install -r code/requirements.txt
```

Set your Gemini API key in your environment variables:
* **Windows (PowerShell)**:
  ```powershell
  $env:GEMINI_API_KEY="your-api-key-here"
  ```
* **macOS / Linux**:
  ```bash
  export GEMINI_API_KEY="your-api-key-here"
  ```

---

### 2. Execution

#### Run the Verification Pipeline
To execute the claim verification pipeline against the evaluation dataset (`dataset/claims.csv`), run:
```bash
python code/main.py
```
This will produce the final `output.csv` file at the root, along with an interactive `outputs/report.html` dashboard showing the run results.

#### Run the Test Suite
To run the automated offline testing suite, run:
```bash
python -m pytest code/tests/ -v
```

#### Run the Evaluation Comparison
To run the strategy comparison evaluation runner:
```bash
python code/evaluation/main.py
```

---

### 3. Docker Deployment
You can build and run the entire verification agent inside an isolated Docker container:
```bash
docker-compose up --build
```
This runs the test suite and then processes the verification pipeline inside a secure, containerized sandbox.

---

## Submission & Verification checklist

Before submitting, confirm the following files exist in the `project/` directory:
- `output.csv`: Must have exactly 14 columns and 44 processed rows matching the schema.
- `code.zip`: Contains `code/` folder with `main.py`, specialized agents, tests, and configuration.
- `log.txt`: Mandatory onboarding transcript log.
- `claims_verifier_cover.png`: Writeup cover image resized to 560x280.
- `report.html`: Dashboard report.

"# AI" 
