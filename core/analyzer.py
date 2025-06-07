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

Risk Categories:
Legal Risk:
- Unusual or one-sided terms
- Non-standard clauses
- Potential legal conflicts
- Governing law or jurisdiction biased toward one party
- Unilateral amendment rights
- Unfavorable termination conditions
- Inflexible or high-cost dispute resolution mechanisms

Financial Risk:
- Hidden liabilities
- Unreasonable payment terms or penalties
- Broad or unclear indemnification obligations
- Unlimited or missing liability caps
- Lack of control over subcontractors or third parties

Compliance & Regulatory Risk:
- Unspecified or burdensome compliance obligations
- Weak confidentiality or data protection terms
- Vague or unfair force majeure definitions

Operational Risk:
- Ambiguous language
- Vague or non-measurable performance obligations (e.g., SLAs)
- Unclear intellectual property ownership

Analysis Requirements:
1. Identify the top 5 most significantly risky clauses based on the criteria above. If fewer than 5 such clauses exist, list only those that do.
2. CRITICAL: List the clauses in descending order of risk severity - where #1 represents the highest risk clause, #2 the second highest risk, and so on through #5 being the lowest risk among those identified.
3. For each identified clause, you MUST provide ALL of the following:
   - The full clause text.
   - An explicit severity tag: [High Risk], [Medium Risk], or [Low Risk].
   - The risk category from the four types above: [Legal Risk], [Financial Risk], [Compliance & Regulatory Risk], or [Operational Risk].
   - A concise, one-line explanation of why it is significantly and unusually risky for the Client. If a clause is flagged but the risk is minimal, provide a brief explanation of why it might still be a minor concern.
4. Provide a single risk score from 0-100 (where 100 indicates extreme, critical risk for the Client), reflecting the overall level of significant, unusual, and unfavorable risk in the document based on the clauses identified.

Risk Score Guidelines (reflecting significant, unusual risk):
- 0-10: Very Low Risk - Contains only standard, balanced clauses with virtually no significant, unusual risks.
- 11-30: Low Risk - Contains mostly standard clauses with very few or only extremely mild deviations that pose limited, low-level concern.
- 31-50: Moderate Risk - Contains some clauses with noticeable imbalances or potential disadvantages.
- 51-70: High Risk - Contains multiple clauses with significant risks that warrant careful review and negotiation.
- 71-100: Critical Risk - Contains clauses with severe, highly unfavorable, or hidden terms that pose critical risks and require immediate revision.

STRICT FORMATTING: For the "Top 5 Risky Clauses" list, each numbered item MUST contain ONLY the full clause text content WITHOUT any section numbers, headers, or reference numbers (such as 2.3, 4.1, Section A, etc.). Do NOT include any document section numbering - extract only the pure clause language. Follow this exact format for EACH item: the full clause text, then a space, then the severity tag in brackets, then a space, then the risk category in brackets, then " - " and the one-line explanation. Example: `[Full Clause text] [High Risk] [Legal Risk] - [One line explanation]`. If you cannot extract the full clause text or provide all required tagging and explanation for a potential risky clause, you MUST exclude it from the numbered list. If no significant risks are found that can be fully formatted, state "No significant risky clauses found."

Format your response exactly as follows:
Risk Score: XX

Top 5 Risky Clauses (Listed in Descending Order of Risk Severity):
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

    def _calibrate_risk_score(self, score: int, clauses: List[str]) -> int:
        """Calibrate the risk score based on the number and severity of risky clauses."""
        calibrated_score = score
        
        # Check if any significant severity keywords are present in the identified clauses
        has_severe_keywords = False
        severe_keywords = ['immediately', 'without cause', 'no rights', 'unlimited', 'waives', 'exclusive', 'notwithstanding', 'indemnify', 'liable for', 'hold harmless'] # Add more high-impact keywords here
        
        for clause in clauses:
            for keyword in severe_keywords:
                if keyword.lower() in clause.lower():
                    has_severe_keywords = True
                    break
            if has_severe_keywords:
                break

        # If model identified clauses, but none have severe keywords, significantly reduce score (slightly less aggressive reduction)
        if clauses and not has_severe_keywords:
             calibrated_score = max(0, calibrated_score - 30) # Reduced from 40
             
        # Adjust based on number of clauses (less impact now)
        num_clauses = len(clauses)
        if num_clauses < 2 and not has_severe_keywords:
            calibrated_score = max(0, calibrated_score - 10) # Reduced from 15
        elif num_clauses > 3 and has_severe_keywords:
            calibrated_score = min(100, calibrated_score + 10)
            
        # Existing adjustment based on individual severity keywords (kept for nuance)
        individual_severity_keywords = {
            'immediately': 5,
            'without cause': 8,
            'no rights': 5,
            'unlimited': 8,
            'any time': 5,
            'without notice': 5,
            'waives': 8,
            'exclusive': 3,
            'strict': 2
        }
        
        for clause in clauses:
            for keyword, adjustment in individual_severity_keywords.items():
                if keyword.lower() in clause.lower():
                    calibrated_score = min(100, calibrated_score + adjustment)
        
        # Ensure score is within 0-100
        calibrated_score = max(0, min(100, calibrated_score))

        return calibrated_score

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
        clauses = self._extract_risky_clauses(analysis)
        
        # Calibrate the risk score
        calibrated_score = self._calibrate_risk_score(risk_score, clauses)
        
        # Update the analysis text with calibrated score
        analysis = analysis.replace(f"Risk Score: {risk_score}", f"Risk Score: {calibrated_score}")
        
        # Cache the analysis
        self._get_cached_analysis.cache_clear()  # Clear old cache entries
        self._get_cached_analysis(doc_hash, context_hash)
        
        return {
            'analysis': analysis,
            'risk_score': calibrated_score,
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