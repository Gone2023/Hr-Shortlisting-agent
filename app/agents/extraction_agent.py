from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.models.schemas import JobDescription, CandidateProfile
import os
from dotenv import load_dotenv
import re

load_dotenv()

def get_llm(temperature=0.1):
    """Returns the configured Groq LLM."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        max_tokens=4096
    )

def extract_jd_info(raw_text: str) -> JobDescription:
    """Extracts structured Job Description information from raw text."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(JobDescription)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert HR assistant. Extract the required structured information from the following Job Description text. Ensure accurate extraction of required skills and years of experience."),
        ("human", "Here is the Job Description text:\n\n{text}")
    ])
    
    chain = prompt | structured_llm
    return chain.invoke({"text": raw_text})

def mask_pii(text: str) -> str:
    """Masks emails and phone numbers to prevent PII exposure to the LLM."""
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', text)
    text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[PHONE_REDACTED]', text)
    return text

def extract_candidate_info(raw_text: str) -> CandidateProfile:
    """Extracts structured Candidate Profile information from raw resume text."""
    safe_text = mask_pii(raw_text)
    llm = get_llm()
    structured_llm = llm.with_structured_output(CandidateProfile)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert HR recruiter. Extract the requested fields from the following candidate resume text. Make sure to accurately capture their skills, experience, education, and any projects/portfolio items. Note: Some PII may be redacted as [EMAIL_REDACTED]."),
        ("human", "Here is the Resume text:\n\n{text}")
    ])
    
    chain = prompt | structured_llm
    return chain.invoke({"text": safe_text})
