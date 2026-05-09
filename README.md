# HR Resume & LinkedIn Shortlisting Agent

This is an AI agent prototype designed to assist HR teams in evaluating candidates efficiently. It ingests a Job Description (JD) and a batch of resumes, parses them, and produces a ranked shortlist with a transparent scoring rubric.

## Setup Instructions

1. Clone the repository or navigate to the project directory.
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your Groq API key.
6. Start the Streamlit app: `streamlit run frontend/main.py`

## Mandatory Technical Disclosures

### 1. LLM Chosen
- **Model:** Groq API (`llama-3.3-70b-versatile`)
- **Rationale:** Chosen for its extremely fast inference speed (crucial for processing batches of resumes), large context window, and excellent support for tool calling / structured output (JSON mode via LangChain's `with_structured_output`). It is also highly cost-effective for prototype development.

### 2. Agent Framework
- **Framework:** LangChain (v0.2.x) with Pydantic for structured outputs.
- **Architecture:** The agent uses a linear extraction and scoring pipeline. It parses documents -> structured extraction via LLM -> strict evaluation against a rubric via LLM.
- **Agent Flow:**
  1. `Document Parser`: Extracts raw text from PDF/DOCX.
  2. `Extraction Agent`: Uses Llama 3.3 to map raw JD/Resume text to strict Pydantic schemas.
  3. `Evaluator`: Compares the structured candidate profile against the structured JD using a strict zero-shot prompt that enforces the 5-dimension rubric (0, 5, 10 scores).

### 3. Prompt Design
- **System Prompts:** 
  - Extraction prompts focus on role assumption ("expert HR assistant") and explicitly tell the model to reasonably infer or leave empty fields not found.
  - The Evaluation prompt contains the strict scoring rubric matrix injected directly into the system prompt. It enforces that the model MUST output exactly 0, 5, or 10.
- **Guardrails:** Pydantic schemas are enforced at the LangChain level using `with_structured_output`, which severely limits the model's ability to hallucinate structure or drift from the required keys.

## Security Risk Mitigation

| Risk Description | Mitigation Strategy |
| :--- | :--- |
| **Prompt Injection** | Input sanitisation implemented. Used structured output schemas (Pydantic) to force the LLM to return strictly typed data, validating all outputs against schemas. |
| **Data Privacy / PII** | Processing happens locally in-memory. A `mask_pii` function is implemented to redact emails and phone numbers before sending plaintext prompts to the cloud LLM. Data masking is used in audit logs. |
| **API Key Exposure** | Used `python-dotenv` and `.env` file for API keys; keys are never hardcoded. Included `.env` in the `.gitignore` file. Secrets manager should be used in prod. |
| **Hallucination Risk** | Mitigated via LangChain structured parsing (JSON mode/Pydantic) to enforce output limits, confidence thresholds, and a human-in-the-loop review step built into the UI. |
| **Unauthorised Access** | API Key / OAuth authentication required for any exposed endpoint. Rate limiting should be applied to the scoring endpoint. |
