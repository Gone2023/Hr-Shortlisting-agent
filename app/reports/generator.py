import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from app.models.schemas import CandidateEvaluation
from typing import Dict

def generate_json_report(evaluations: Dict[str, CandidateEvaluation]) -> str:
    report_data = []
    for fname, eval_obj in evaluations.items():
        data = eval_obj.model_dump()
        data['file_name'] = fname
        report_data.append(data)
    return json.dumps(report_data, indent=4)

def generate_html_report(evaluations: Dict[str, CandidateEvaluation]) -> str:
    html = "<html><head><title>HR Shortlist Report</title><style>body{font-family: Arial, sans-serif;} table{border-collapse: collapse; width: 100%;} th, td{border: 1px solid #ddd; padding: 8px;} th{padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #04AA6D; color: white;}</style></head><body>"
    html += "<h1>HR Shortlist Report</h1>"
    for fname, eval_obj in evaluations.items():
        html += f"<h2>Candidate: {eval_obj.candidate_name}</h2>"
        html += f"<p><strong>Recommendation:</strong> {eval_obj.recommendation}</p>"
        html += f"<p><strong>Total Score:</strong> {eval_obj.total_weighted_score}/100</p>"
        html += f"<p><strong>Summary:</strong> {eval_obj.overall_summary}</p>"
        html += "<table><tr><th>Dimension</th><th>Score</th><th>Justification</th></tr>"
        for score in eval_obj.scores:
            html += f"<tr><td>{score.dimension_name}</td><td>{score.score}/10</td><td>{score.justification}</td></tr>"
        html += "</table><br/><hr/>"
    html += "</body></html>"
    return html

def generate_pdf_report(evaluations: Dict[str, CandidateEvaluation], output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("HR Shortlist Report", styles['Title']))
    story.append(Spacer(1, 12))
    
    for fname, eval_obj in evaluations.items():
        story.append(Paragraph(f"Candidate: {eval_obj.candidate_name}", styles['Heading2']))
        story.append(Paragraph(f"<b>Recommendation:</b> {eval_obj.recommendation}", styles['Normal']))
        story.append(Paragraph(f"<b>Total Score:</b> {eval_obj.total_weighted_score}/100", styles['Normal']))
        story.append(Paragraph(f"<b>Summary:</b> {eval_obj.overall_summary}", styles['Normal']))
        story.append(Spacer(1, 6))
        
        # Create table data
        data = [["Dimension", "Score", "Justification"]]
        for score in eval_obj.scores:
            # Wrap justification text in Paragraph to avoid running off the page
            justification_p = Paragraph(score.justification, styles['Normal'])
            data.append([score.dimension_name, f"{score.score}/10", justification_p])
            
        t = Table(data, colWidths=[100, 50, 300])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        story.append(t)
        story.append(Spacer(1, 20))
        
    doc.build(story)
