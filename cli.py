import os
import argparse
from typing import List
from core.doc_processor import DocumentProcessor
from core.vector_store import EmbeddingManager
from core.analyzer import RiskAnalyzer

# Initialize components globally
embedding_manager = EmbeddingManager()
risk_analyzer = RiskAnalyzer()

def process_reference_docs(reference_dir: str):
    """Process all reference documents and add them to the vector database."""
    doc_processor = DocumentProcessor()
    
    if not os.path.exists(reference_dir) or not os.listdir(reference_dir):
        print(f"No reference documents found in {reference_dir}. Skipping processing.")
        return
        
    print("Processing reference documents...")
    
    # Clear existing documents from the collection before adding new ones
    embedding_manager.clear_collection() 
    
    for filename in os.listdir(reference_dir):
        if filename.endswith(('.pdf', '.docx', '.doc', '.txt')):
            file_path = os.path.join(reference_dir, filename)
            print(f"Processing reference document: {filename}")
            
            # Process document
            chunks = doc_processor.process_document(file_path)
            
            # Add to vector database
            embedding_manager.add_documents(chunks)
    print("Finished processing reference documents.")

def analyze_document(file_path: str):
    """Analyze a document and provide risk assessment."""
    doc_processor = DocumentProcessor()
    
    # Process document
    print(f"Processing document: {file_path}")
    chunks = doc_processor.process_document(file_path)
    
    # Find similar documents using the globally initialized embedding_manager
    print("Finding similar documents...")
    similar_docs = []
    for chunk in chunks:
        similar_docs.extend(embedding_manager.search_similar(chunk['text']))
    
    # Analyze document using the globally initialized risk_analyzer
    print("Analyzing document...")
    analysis = risk_analyzer.analyze_document(chunks, similar_docs)
    
    return analysis

def main():
    parser = argparse.ArgumentParser(description="Document Risk Analysis System")
    parser.add_argument("--reference_dir", default="reference_docs",
                      help="Directory containing reference documents")
    parser.add_argument("--document", help="Path to document to analyze")
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs(args.reference_dir, exist_ok=True)
    os.makedirs("vector_db", exist_ok=True)
    
    # Process reference documents on startup
    process_reference_docs(args.reference_dir)
    
    # Analyze document if provided via CLI
    if args.document:
        if not os.path.exists(args.document):
            print(f"Error: Document not found: {args.document}")
            return
        
        analysis = analyze_document(args.document)
        print("\n=== Risk Analysis Results ===")
        print(f"Risk Score: {analysis['risk_score']}/100")
        print("\nDetailed Analysis:")
        print(analysis['analysis'])
    else:
        print("No document provided for CLI analysis.")

if __name__ == "__main__":
    main() 