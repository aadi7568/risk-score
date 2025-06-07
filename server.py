from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from core.doc_processor import DocumentProcessor
from core.vector_store import EmbeddingManager
from core.analyzer import RiskAnalyzer
import re
from typing import Dict
from fastapi import HTTPException

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

def parse_analysis(analysis_text: str) -> Dict:
    """Parse the analysis text to extract clauses, categories, and severity."""
    clauses = []
    categories = []
    severity = []
    
    # Updated pattern to match format without score
    pattern = r'\d+\.\s*(.*?)\s*\[(High|Medium|Low)\s*Risk\]\s*\[(.*?)\]\s*-\s*(.*)'
    
    for match in re.finditer(pattern, analysis_text):
        clause_text = match.group(1).strip()
        risk_level = match.group(2).strip()
        category = match.group(3).strip()
        explanation = match.group(4).strip()
        
        # Format the clause with its explanation
        full_clause = f"{clause_text} - {explanation}"
        
        clauses.append(full_clause)
        categories.append(category)
        severity.append(f"{risk_level} Risk")
    
    return {
        'risky_clauses': clauses,
        'risk_categories': categories,
        'clause_severity': severity
    }

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    """Analyze uploaded document and return risk assessment."""
    try:
        # Save uploaded file
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document
        doc_processor = DocumentProcessor()
        chunks = doc_processor.process_document(file_path)
        
        # Get similar documents
        embedding_manager = EmbeddingManager()
        similar_docs = []
        for chunk in chunks:
            similar_docs.extend(embedding_manager.search_similar(chunk['text']))
        
        # Analyze document
        analyzer = RiskAnalyzer()
        analysis = analyzer.analyze_document(chunks, similar_docs)
        
        # Extract risk score
        risk_score = analysis['risk_score']
        
        # Parse analysis to get clauses, categories, and severity
        parsed_analysis = parse_analysis(analysis['analysis'])
        
        # Clean up temporary file
        os.remove(file_path)
        
        return {
            "risk_score": risk_score,
            "risky_clauses": parsed_analysis['risky_clauses'],
            "risk_categories": parsed_analysis['risk_categories'],
            "clause_severity": parsed_analysis['clause_severity']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 