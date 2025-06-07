import os
from typing import List, Dict
import google.generativeai as genai
from dotenv import load_dotenv
import re
from functools import lru_cache
import hashlib

load_dotenv()

class RiskAnalyzer:
    def __init__(self):
        # Configure Gemini 2.0 Flash with optimized settings
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config={
                'temperature': 0.1,  # Lower temperature for more focused responses
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 500,  # Limit output length
            }
        )
        
        self.system_prompt = """You are an expert legal document risk analyst focused on identifying significant and unusual risks in a contract from the perspective of the Client. Your goal is to highlight terms that are severely unfavorable, highly one-sided, or represent a major deviation from common, balanced legal practice.

CRITICAL INSTRUCTION: Do NOT flag standard legal clauses (like basic payment terms, typical contract duration, standard governing law, boilerplate confidentiality with common exceptions, or general service descriptions) as 'risky' unless they contain exceptionally harsh, hidden, ambiguous, or one-sided conditions that significantly disadvantage the Client. In particular, do NOT flag standard limitation of liability clauses unless they are unusually harsh, one-sided, or remove all liability for gross negligence, willful misconduct, or breach of confidentiality.

Focus only on identifying clauses that introduce substantial risk, disproportionate liability, or severely limit the Client's rights or recourse compared to a balanced agreement.

Risk Categories and Multipliers:
1. Legal Risk (4x multiplier):
   - Unusual or one-sided terms
   - Non-standard clauses
   - Potential legal conflicts
   - Governing law or jurisdiction biased toward one party
   - Unilateral amendment rights
   - Unfavorable termination conditions
   - Inflexible or high-cost dispute resolution mechanisms

2. Financial Risk (3x multiplier):
   - Hidden liabilities
   - Unreasonable payment terms or penalties
   - Broad or unclear indemnification obligations
   - Unlimited or missing liability caps
   - Lack of control over subcontractors or third parties

3. Compliance & Regulatory Risk (2x multiplier):
   - Unspecified or burdensome compliance obligations
   - Weak confidentiality or data protection terms
   - Vague or unfair force majeure definitions

4. Operational Risk (1x multiplier):
   - Ambiguous language
   - Vague or non-measurable performance obligations (e.g., SLAs)
   - Unclear intellectual property ownership

Base Severity Scores:
- High Risk: 30 points
- Medium Risk: 20 points
- Low Risk: 10 points

Risk Score Calculation:
1. Calculate individual clause scores:
   - Base Score × Category Multiplier = Clause Score
   Example: High Risk (30) × Legal Risk (4x) = 120 points

2. Select top 5 highest-scoring clauses

3. Calculate overall risk score:
   - Sum of top 5 clause scores
   - Normalize to 0-100 scale using the formula:
     Final Score = (Sum of top 5 scores / Maximum possible score) × 100
     Where Maximum possible score = 5 × (30 × 4) = 600
     (5 clauses × Highest base score × Highest multiplier)

4. Minimum Score Rules:
   - If no risky clauses are found: Score = 5 (indicating very low risk)
   - If only Low Risk clauses found: Minimum Score = 10
   - If only Medium Risk clauses found: Minimum Score = 20
   - If High Risk clauses found: Use calculated score

Analysis Requirements:
1. Identify the top 5 most significantly risky clauses based on the criteria above. If fewer than 5 such clauses exist, list only those that do.
2. CRITICAL: List the clauses in descending order of calculated risk score - where #1 represents the highest scoring clause, #2 the second highest, and so on through #5 being the lowest among those identified.
3. For each identified clause, you MUST provide ALL of the following:
   - The full clause text.
   - An explicit severity tag: [High Risk], [Medium Risk], or [Low Risk].
   - The risk category from the four types above: [Legal Risk], [Financial Risk], [Compliance & Regulatory Risk], or [Operational Risk].
   - A concise, one-line explanation of why it is significantly and unusually risky for the Client.

4. Calculate and provide the final normalized risk score (0-100), following the minimum score rules above.

STRICT FORMATTING: For the "Top 5 Risky Clauses" list, each numbered item MUST contain ONLY the full clause text content WITHOUT any section numbers, headers, or reference numbers (such as 2.3, 4.1, Section A, etc.). Do NOT include any document section numbering - extract only the pure clause language. Follow this exact format for EACH item: `[Full Clause text] [Severity] [Risk Category] - [One line explanation]`. If you cannot extract the full clause text or provide all required tagging and explanation for a potential risky clause, you MUST exclude it from the numbered list. If no significant risks are found that can be fully formatted, state "No significant risky clauses found."

Format your response exactly as follows:
Risk Score: XX

Top 5 Risky Clauses (Listed in Descending Order of Risk Score):
1. [Full Clause text] [Severity] [Risk Category] - [One line explanation of significant risk]
2. [Full Clause text] [Severity] [Risk Category] - [One line explanation of significant risk]
3. [Full Clause text] [Severity] [Risk Category] - [One line explanation of significant risk]
4. [Full Clause text] [Severity] [Risk Category] - [One line explanation of significant risk]
5. [Full Clause text] [Severity] [Risk Category] - [One line explanation of significant risk]"""

    @lru_cache(maxsize=100)
    def _get_cached_analysis(self, document_hash: str, context_hash: str) -> str:
        """Get cached analysis for a document and context combination."""
        return None

    def _hash_content(self, content: str) -> str:
        """Generate a hash for content to use as cache key."""
        return hashlib.md5(content.encode()).hexdigest()

    def analyze_document(self, document_chunks: List[Dict], similar_docs: List[Dict]) -> Dict:
        """
        Analyze document chunks and provide risk assessment.
        
        Args:
            document_chunks (List[Dict]): List of document chunks to analyze
            similar_docs (List[Dict]): List of similar reference documents
            
        Returns:
            Dict: Risk analysis results
        """
        # Combine document chunks efficiently
        document_text = "\n\n".join(chunk['text'] for chunk in document_chunks)
        
        # Limit context to top 3 most relevant similar documents
        context = "\n\nReference Documents:\n" + "\n---\n".join([
            f"Document: {doc['metadata']['file_name']}\n{doc['text']}"
            for doc in similar_docs[:3]  # Only use top 3 similar documents
        ])
        
        # Generate hashes for caching
        doc_hash = self._hash_content(document_text)
        context_hash = self._hash_content(context)
        
        # Check cache first
        cached_analysis = self._get_cached_analysis(doc_hash, context_hash)
        if cached_analysis:
            return {
                'analysis': cached_analysis,
                'risk_score': self._extract_risk_score(cached_analysis),
                'document_chunks': document_chunks,
                'similar_docs': similar_docs
            }
        
        # Create optimized analysis prompt
        prompt = f"""System: {self.system_prompt}

Document to analyze:
{document_text}

{context}

Please analyze the document and provide the risk score and top 5 risky clauses in the exact format specified above."""

        # Get analysis from Gemini 2.0 Flash with optimized settings
        response = self.model.generate_content(prompt)
        analysis = response.text
        
        # Extract risk score and clauses
        risk_score = self._extract_risk_score(analysis)
        
        # Cache the analysis
        self._get_cached_analysis.cache_clear()  # Clear old cache entries
        self._get_cached_analysis(doc_hash, context_hash)
        
        return {
            'analysis': analysis,
            'risk_score': risk_score,
            'document_chunks': document_chunks,
            'similar_docs': similar_docs
        }

    def _extract_risk_score(self, analysis: str) -> int:
        """Extract risk score from analysis text."""
        try:
            # Try different patterns for risk score
            patterns = [
                r"Risk score:?\s*(\d+)",
                r"Risk Score:?\s*(\d+)",
                r"Score:?\s*(\d+)",
                r"(\d+)\s*out of\s*100",
                r"(\d+)/100"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, analysis)
                if match:
                    score = int(match.group(1))
                    if 0 <= score <= 100:
                        return score
            
            return 0
            
        except Exception as e:
            print(f"Error extracting risk score: {str(e)}")
            return 0

    def _extract_risky_clauses(self, analysis: str) -> List[str]:
        """Extract risky clauses from analysis text."""
        clauses = []
        for line in analysis.split('\n'):
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                # Remove the number and dot prefix
                clause = re.sub(r'^\d+\.\s*', '', line.strip())
                if clause:
                    clauses.append(clause)
        return clauses 