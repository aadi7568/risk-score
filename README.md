# Contract Risk Analyzer

A powerful web application that analyzes contracts and legal documents to identify potential risks and provide detailed insights. Using advanced AI technology, it helps legal professionals, businesses, and individuals quickly assess the risk level of their contracts and identify potentially problematic clauses.

## Features

- **Risk Score Analysis**: Get an overall risk score (0-100%) for your contract
- **Smart Clause Detection**: Automatically identifies potentially risky clauses in the document
- **Detailed Explanations**: Each risky clause comes with a clear explanation of the potential issues
- **Risk Categorization**: Clauses are categorized by type (e.g., liability, termination, confidentiality)
- **Severity Levels**: Each identified risk is classified as High, Medium, or Low severity
- **Modern Web Interface**: User-friendly interface for easy document upload and analysis
- **Multiple File Support**: Analyzes PDF, Word documents, and text files
- **Real-time Analysis**: Quick processing with immediate results
- **Reference Document Comparison**: Optional feature to compare against reference documents

## Directory Structure

```text
risk-score/
├── legal_docs/              # Place your documents to analyze here
├── reference_docs/          # Place your reference documents here
├── web_interface/          # Frontend HTML, CSS, and JS files
│   ├── index.html         # Main web interface
│   ├── style.css          # Styling
│   └── script.js          # Frontend logic
├── core/                   # Core application files
│   ├── analyzer.py        # Main analysis logic
│   ├── doc_processor.py   # Document processing utilities
│   └── vector_store.py    # Vector database management
├── vector_db/             # Vector database storage
├── server.py              # FastAPI server
├── cli.py                 # Command-line interface
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## Prerequisites

- Python 3.7+
- Google API Key for Gemini AI

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd risk-score
   ```

2. **Set up a virtual environment and install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Set up your environment:**
   - Create a `.env` file in the root directory
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

4. **Place your documents (Optional):**
   - You can place documents you want to analyze in the `legal_docs/` directory. The API also supports uploading files directly.
   - You can place reference documents in the `reference_docs/` directory if you want to use the similarity feature.

## Running the API

To run the FastAPI server and access the web interface:

1. **Ensure your virtual environment is activated** (see Setup step 2).
2. **Start the FastAPI server:**
   ```bash
   uvicorn server:app --reload
   ```

   The API will be running at `http://localhost:8000/`.

## Accessing the Web Interface

Open your web browser and go to `http://localhost:8000/`.

From the web interface, you can upload a document and generate its risk score.

## Running the CLI (Optional)

If you want to use the command-line interface:

1. **Ensure your virtual environment is activated** (see Setup step 2).
2. **Run the analysis:**
   ```bash
   python cli.py --document legal_docs/sample_contract.txt
   ```

   If you have reference documents, you can include them:
   ```bash
   python cli.py --document legal_docs/sample_contract.txt --reference_dir reference_docs
   ```

## Supported Document Types

- PDF (.pdf)
- Word (.docx, .doc)
- Text (.txt)

## Output

The API will return a JSON object with:
- Risk score (0-100)
- List of risky clauses with their explanations
- Risk categories for each clause
- Severity levels (High, Medium, Low) for each clause

## Troubleshooting

1. **API Key Issues:**
   - Ensure your `.env` file contains the correct API key.
   - Verify the API key has access to Gemini AI.

2. **Dependency Issues:**
   - Make sure all dependencies are installed using `pip install -r requirements.txt`.

3. **Server Not Running:**
   - Ensure you have started the FastAPI server using `uvicorn server:app --reload`.

## Development

To modify the application:

1. Make your changes to the Python files.
2. The `uvicorn server:app --reload` command will automatically restart the server when code changes are detected.
3. Refresh your web browser to see frontend changes.

## License

[Your License Here] 