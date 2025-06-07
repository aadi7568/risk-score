from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from core.doc_processor import DocumentProcessor
from core.vector_store import EmbeddingManager
from core.analyzer import RiskAnalyzer
import re

app = FastAPI()

# Initialize components
embedding_manager = EmbeddingManager()
risk_analyzer = RiskAnalyzer()
doc_processor = DocumentProcessor()

# Mount static files
app.mount("/static", StaticFiles(directory="web_interface"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("web_interface/index.html")

def parse_analysis(analysis_text):
    """Parse the analysis text to extract clauses, categories, and severity."""
    clauses = []
    categories = []
    severities = []
    
    # Regular expressions for matching
    clause_pattern = r'\d+\.\s*(.*?)\s*\[(High|Medium|Low)\s*Risk\]\s*\[(.*?)\]\s*-\s*(.*)'
    
    # Find all matches
    matches = re.finditer(clause_pattern, analysis_text)
    for match in matches:
        clause_text = match.group(1).strip()
        severity = match.group(2).strip()
        category = match.group(3).strip()
        
        # Format the clause with its explanation
        full_clause = f"{clause_text} - {match.group(4).strip()}"
        
        clauses.append(full_clause)
        severities.append(f"{severity} Risk")
        categories.append(category)
    
    return clauses, categories, severities

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    # Save uploaded file temporarily
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document
        chunks = doc_processor.process_document(temp_path)
        
        # Find similar documents
        similar_docs = []
        for chunk in chunks:
            similar_docs.extend(embedding_manager.search_similar(chunk['text']))
        
        # Analyze document
        analysis_result = risk_analyzer.analyze_document(chunks, similar_docs)
        
        # Parse the analysis text to extract clauses, categories, and severity
        risky_clauses, risk_categories, clause_severity = parse_analysis(analysis_result['analysis'])
        
        # Return the formatted response
        return {
            'risk_score': analysis_result['risk_score'],
            'risky_clauses': risky_clauses,
            'risk_categories': risk_categories,
            'clause_severity': clause_severity
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 