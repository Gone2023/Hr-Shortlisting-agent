from langchain_core.prompts import ChatPromptTemplate
from app.models.schemas import JobDescription, CandidateProfile, CandidateEvaluation, DimensionScore
from app.agents.extraction_agent import get_llm

RUBRIC_INSTRUCTIONS = """
You are an expert technical recruiter evaluating a candidate against a job description.
You MUST strictly follow this scoring rubric and provide a score of exactly 0, 5, or 10 for each dimension. Do not use any other numbers.

1. Skills Match (Weight: 30%)
   - 0 (Poor): < 30% skills match
   - 5 (Average): 50–70% skills match
   - 10 (Excellent): > 85% skills match

2. Experience Relevance (Weight: 25%)
   - 0 (Poor): Unrelated domain
   - 5 (Average): Adjacent domain
   - 10 (Excellent): Exact domain & seniority

3. Education & Certs (Weight: 15%)
   - 0 (Poor): Does not meet minimum
   - 5 (Average): Meets minimum
   - 10 (Excellent): Exceeds + extra certs

4. Project / Portfolio (Weight: 20%)
   - 0 (Poor): No evidence
   - 5 (Average): 1-2 generic projects
   - 10 (Excellent): Strong relevant portfolio

5. Communication Quality (Weight: 10%)
   - 0 (Poor): Poor structure/grammar
   - 5 (Average): Adequate clarity
   - 10 (Excellent): Crisp, structured, impactful

OUTPUT REQUIREMENTS:
You must provide a structured evaluation containing exactly these 5 dimensions. 
For each dimension, output the score (0, 5, or 10) and a concise one-line justification.
Also provide an overall summary and a recommendation (Hire, No-Hire, or Interview).
The total_weighted_score will be calculated, but provide your estimate.
"""

def evaluate_candidate(jd: JobDescription, candidate: CandidateProfile) -> CandidateEvaluation:
    """Evaluates a candidate profile against a job description using the LLM."""
    llm = get_llm(temperature=0.0) # Lower temperature for more consistent scoring
    structured_llm = llm.with_structured_output(CandidateEvaluation)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", RUBRIC_INSTRUCTIONS),
        ("human", "Job Description:\n{jd}\n\nCandidate Profile:\n{candidate}\n\nProvide the structured evaluation.")
    ])
    
    chain = prompt | structured_llm
    
    evaluation = chain.invoke({
        "jd": jd.model_dump_json(),
        "candidate": candidate.model_dump_json()
    })
    
    # Recalculate total_weighted_score to ensure mathematical accuracy
    weights = {
        "Skills Match": 0.30,
        "Experience Relevance": 0.25,
        "Education & Certs": 0.15,
        "Project/Portfolio": 0.20,
        "Communication Quality": 0.10
    }
    
    total = 0.0
    for score_obj in evaluation.scores:
        # Fuzzy match dimension name just in case LLM changes casing
        dim_name = score_obj.dimension_name
        matched_weight = 0.0
        for k, v in weights.items():
            if k.lower() in dim_name.lower():
                matched_weight = v
                score_obj.dimension_name = k # Normalize name
                break
        total += score_obj.score * matched_weight
        
    evaluation.total_weighted_score = round(total * 10, 2) # convert to 100 scale (e.g. 10 * 10 = 100, 5 * 10 = 50)
    evaluation.candidate_name = candidate.name
    
    return evaluation
