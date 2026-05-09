import streamlit as st
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parsers.document_parser import parse_document_bytes
from app.agents.extraction_agent import extract_jd_info, extract_candidate_info
from app.scoring.evaluator import evaluate_candidate
from app.reports.generator import generate_json_report, generate_html_report, generate_pdf_report
from app.parsers.linkedin_parser import fetch_linkedin_profile
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="AI HR Agent", layout="wide")

st.title("🤖 HR Resume Shortlisting Agent")

if "evaluations" not in st.session_state:
    st.session_state.evaluations = {}
if "jd_parsed" not in st.session_state:
    st.session_state.jd_parsed = None

col1, col2 = st.columns(2)

with col1:
    st.header("1. Upload Job Description")
    jd_file = st.file_uploader("Upload JD (PDF/DOCX)", type=["pdf", "docx"], key="jd")
    if jd_file and st.button("Parse JD"):
        with st.spinner("Parsing JD..."):
            raw_jd = parse_document_bytes(jd_file.read(), jd_file.name)
            st.session_state.jd_parsed = extract_jd_info(raw_jd)
            st.success("JD Parsed successfully!")
            
    if st.session_state.jd_parsed:
        with st.expander("View Parsed JD"):
            st.json(st.session_state.jd_parsed.model_dump())

with col2:
    st.header("2. Candidate Profiles")
    resume_files = st.file_uploader("Upload Resumes (PDF/DOCX/JSON)", type=["pdf", "docx", "json"], accept_multiple_files=True, key="resumes")
    linkedin_urls_input = st.text_area("Or paste LinkedIn URLs (one per line)", key="linkedin_urls")

st.markdown("---")

if st.session_state.jd_parsed and (resume_files or linkedin_urls_input.strip()):
    if st.button("Evaluate Candidates", type="primary"):
        st.session_state.evaluations = {}
        linkedin_urls = [u.strip() for u in linkedin_urls_input.split('\n') if u.strip()]
        
        # Process files
        if resume_files:
            for r_file in resume_files:
                with st.spinner(f"Evaluating {r_file.name}..."):
                    raw_resume = parse_document_bytes(r_file.read(), r_file.name)
                    candidate_profile = extract_candidate_info(raw_resume)
                    eval_result = evaluate_candidate(st.session_state.jd_parsed, candidate_profile)
                    st.session_state.evaluations[r_file.name] = eval_result
        
        # Process LinkedIn URLs
        if linkedin_urls:
            for url in linkedin_urls:
                with st.spinner(f"Fetching and Evaluating {url}..."):
                    try:
                        raw_resume = fetch_linkedin_profile(url)
                        candidate_profile = extract_candidate_info(raw_resume)
                        eval_result = evaluate_candidate(st.session_state.jd_parsed, candidate_profile)
                        st.session_state.evaluations[url] = eval_result
                    except Exception as e:
                        st.error(f"Error processing {url}: {e}")
                        
        if st.session_state.evaluations:
            st.success("Evaluations Complete!")

if st.session_state.evaluations:
    st.header("3. Shortlist Report")
    
    st.subheader("Export Reports")
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        json_report = generate_json_report(st.session_state.evaluations)
        st.download_button("Download JSON", data=json_report, file_name="report.json", mime="application/json")
    with col_dl2:
        html_report = generate_html_report(st.session_state.evaluations)
        st.download_button("Download HTML", data=html_report, file_name="report.html", mime="text/html")
    with col_dl3:
        pdf_path = os.path.join(os.path.dirname(__file__), "temp_report.pdf")
        generate_pdf_report(st.session_state.evaluations, pdf_path)
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        st.download_button("Download PDF", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")
    
    st.markdown("---")
    # Create Summary DataFrame
    summary_data = []
    for fname, eval_obj in st.session_state.evaluations.items():
        summary_data.append({
            "Candidate": eval_obj.candidate_name,
            "File": fname,
            "Total Score": eval_obj.total_weighted_score,
            "Recommendation": eval_obj.recommendation
        })
    df_summary = pd.DataFrame(summary_data).sort_values("Total Score", ascending=False)
    st.dataframe(df_summary, use_container_width=True)
    
    st.header("Detailed Breakdown & Human-in-the-Loop Override")
    for fname, eval_obj in st.session_state.evaluations.items():
        with st.expander(f"{eval_obj.candidate_name} ({eval_obj.recommendation} - {eval_obj.total_weighted_score}/100)"):
            st.write(f"**Overall Summary:** {eval_obj.overall_summary}")
            
            for score_item in eval_obj.scores:
                st.markdown(f"**{score_item.dimension_name}:** {score_item.score}/10")
                st.caption(f"Reasoning: {score_item.justification}")
                
            st.markdown("### Override Score")
            override_reason = st.text_input("Reason for override", key=f"reason_{fname}")
            new_score = st.number_input("New Total Score (0-100)", min_value=0.0, max_value=100.0, value=float(eval_obj.total_weighted_score), key=f"score_{fname}")
            if st.button("Submit Override", key=f"btn_{fname}"):
                old_score = eval_obj.total_weighted_score
                # Update session state
                st.session_state.evaluations[fname].total_weighted_score = round(new_score, 2)
                st.session_state.evaluations[fname].recommendation = "Manual Override"
                
                # Write to audit log
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "candidate": eval_obj.candidate_name,
                    "old_score": old_score,
                    "new_score": new_score,
                    "reason": override_reason
                }
                log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, "audit_log.json")
                
                logs = []
                if os.path.exists(log_file):
                    try:
                        with open(log_file, "r") as f:
                            logs = json.load(f)
                    except:
                        pass
                logs.append(log_entry)
                with open(log_file, "w") as f:
                    json.dump(logs, f, indent=4)
                    
                st.success(f"Score for {eval_obj.candidate_name} updated successfully. Logged to {log_file}.")
                st.rerun()
