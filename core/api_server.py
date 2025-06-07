from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import os
from cli import analyze_document
import re
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"], 
    allow_headers=["*"],  
    expose_headers=["*"],  
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Serve static files from the 'web_interface' directory
app.mount("/static", StaticFiles(directory="web_interface"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("web_interface/index.html")

def parse_analysis(analysis_text: str) -> dict:
    """Parse the analysis text to extract risk score, and fully formatted risky clauses from LLM output."""
    result = {
        "risk_score": 0,
        "risky_clauses": [],
        "risk_categories": [],
        "clause_severity": []
    }

    # Extract risk score
    score_match = re.search(r"Risk Score:\s*(\d+)", analysis_text)
    if score_match:
        result["risk_score"] = int(score_match.group(1))

    # Extract fully formatted risky clauses, categories, and severity
    clauses = []
    categories = []
    severity_tags = []

    # Regex to capture: Clause Text, Severity, Category, Explanation
    # Format: [Clause Text] [Severity] [Category] - [Explanation]
    # This regex is strict and requires all parts to be present after removing leading numbers/document numbers.
    full_clause_regex = re.compile(r'(.+?)\s*\[([^\]]+)\]\s*\[([^\]]+)\]\s*-\s*(.+)')

    for line in analysis_text.split('\n'):
        # Only process lines that look like numbered list items from the LLM
        if re.match(r'^\d+\.\s*', line.strip()):
            # Remove the LLM's list number and dot prefix
            line_cleaned = re.sub(r'^\d+\.\s*', '', line.strip())

            # Remove potential original document numbering at the beginning of the line
            line_cleaned = re.sub(r'^(\d+(\.\d+)*\s+)', '', line_cleaned)

            # Attempt to match the strict full format
            match = full_clause_regex.match(line_cleaned)

            if match:
                # Extract groups: (Clause Text), (Severity), (Category), (Explanation)
                clause_text = match.group(1).strip()
                severity = match.group(2).strip()
                category = match.group(3).strip()
                explanation = match.group(4).strip()

                # Combine clause text and explanation for the risky_clauses array
                full_clause_entry = f"{clause_text} - {explanation}"

                clauses.append(full_clause_entry)
                severity_tags.append(severity)
                categories.append(category)
            # If the line is a numbered list item but doesn't match the strict regex, it's excluded.

    result["risky_clauses"] = clauses
    result["risk_categories"] = categories
    result["clause_severity"] = severity_tags

    return result

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    # Create legal_docs directory if it doesn't exist
    os.makedirs("legal_docs", exist_ok=True)
    
    # Save the uploaded file to the legal_docs folder
    file_path = os.path.join("legal_docs", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Analyze the document using the globally initialized components from cli
    analysis = analyze_document(file_path)
    
    # Parse the analysis
    result = parse_analysis(analysis['analysis'])
    
    # Return the response
    return JSONResponse(content=result)

@app.get("/health")
async def health():
    return {"status": "ok"}