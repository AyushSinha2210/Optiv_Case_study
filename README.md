# Optiv Case Study: Text Analysis & PII Detection

A secure document ingestion and PII (Personally Identifiable Information) redaction pipeline built for **Cadence Financial Group** as part of the Optiv Cyber Strategy Case Study.

The system extracts text from diverse document formats (`.pdf`, `.docx`, `.pptx`), detects and classifies sensitive personal and financial entities, and redacts them prior to downstream LLM processing.

---

## Key Features

- **Multi-Format Extraction:** Preserves document structure and context across PDFs, Word documents, and PowerPoint presentations.
- **Accurate PII Detection:** Combines regex patterns and NLP/NER (Named Entity Recognition) to identify names, emails, phone numbers, employee IDs, SSNs, and banking details.
- **Pre-LLM Redaction:** Replaces sensitive entities with contextual tokens (e.g., `<PERSON_1>`, `<EMP_ID_1>`) so AI models can process text safely.
- **Audit Logging:** Generates a structured summary of identified PII entities and risk exposure for compliance review.

---

## Project Structure

```text
├── README.md
├── requirements.txt
├── .gitignore
├── app/
│   └── streamlit_app.py        # Interactive demo UI
├── src/
│   ├── parsers/                # PDF, DOCX, and PPTX text extractors
│   ├── detector/               # PII detection engine & patterns
│   └── redactor/               # Masking and tokenization logic
├── notebooks/                  # Walkthrough & analysis notebooks
└── data/                       # Sample test documents
```

---

## Quickstart

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/AyushSinha2210/Optive_Case_study.git
cd Optive_Case_study

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Run the Demonstration UI
```bash
streamlit run app/streamlit_app.py
```

---

## Tech Stack

- **Document Parsing:** `pdfplumber`, `pypdf`, `python-docx`, `python-pptx`
- **PII Detection:** `presidio-analyzer`, `presidio-anonymizer`, `spacy`
- **Data & UI:** `pandas`, `streamlit`
