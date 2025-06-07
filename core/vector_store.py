import os
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class EmbeddingManager:
    def __init__(self, collection_name: str = "document_embeddings"):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.Client(Settings(
            persist_directory="vector_db",
            is_persistent=True
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: List[Dict]):
        """
        Add documents to the vector database.
        
        Args:
            documents (List[Dict]): List of document chunks with metadata
        """
        texts = [doc['text'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        ids = [f"{doc['source']}_{doc['chunk_id']}" for doc in documents]
        
        # Generate embeddings
        embeddings = self.model.encode(texts).tolist()
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def search_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for similar documents in the vector database.
        
        Args:
            query (str): Query text
            n_results (int): Number of results to return
            
        Returns:
            List[Dict]: List of similar documents with metadata
        """
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        similar_docs = []
        for i in range(len(results['documents'][0])):
            similar_docs.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return similar_docs

    def clear_collection(self):
        """Clear all documents from the collection."""
        self.collection.delete() 