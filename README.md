# SmartHire - AI-Powered Recruitment Assistant

SmartHire is an intelligent recruitment tool that helps HR teams filter and evaluate resumes faster using AI. Instead of just keyword matching, SmartHire reads and understands resumes to compare candidates against job descriptions, providing match scores and detailed reasoning.

## Problem Statement

Hiring is slow. HR teams often receive hundreds of resumes for a single position, making it impossible to carefully review each one. This leads to missed talent and potential bias in hiring decisions. SmartHire solves the "too many resumes, too little time" problem.

## Features

### 1. Resume Analysis
Upload PDF resumes and get AI-structured data extraction including:
- Contact information
- Summary/Objective
- Skills
- Work experience
- Education
- Certifications

### 2. Pipeline Manager
A 3-step data processing pipeline:
1. **Extract Text** - Convert PDFs to plain text using pdfplumber
2. **AI Structuring** - Use LLM to extract structured resume data
3. **Build Embeddings** - Create vector embeddings for semantic search

### 3. Browse Candidates
- View all processed candidates in a paginated list
- Search by name or candidate ID
- Skill-based filtering with semantic search

### 4. AI Search
Ask natural language questions about candidates:
- "Does any candidate know Python?"
- "Show me candidates with machine learning experience"
- "Who has worked at a startup?"
- "Find candidates with SQL and data analysis skills"

### 5. Job Matching
Paste a job description and get:
- **Match Score (0-100)** - How well each candidate fits the role
- **Strengths** - What makes the candidate a good fit
- **Gaps** - Skills or experience the candidate is missing
- **Reasoning** - Detailed explanation of the score

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit |
| **Vector Database** | ChromaDB |
| **Embeddings** | HuggingFace (sentence-transformers/all-MiniLM-L6-v2) |
| **LLM Providers** | OpenRouter (DeepSeek), Groq (Llama 3.3), Ollama (local) |
| **PDF Processing** | pdfplumber, pypdf |
| **Framework** | LangChain |

## Project Structure

```
SmartHire/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── components/               # UI components
│   ├── __init__.py
│   ├── helpers.py           # Helper functions
│   ├── styles.py            # CSS styling
│   ├── tabs.py              # Tab content renderers
│   └── ui.py                # UI widgets
├── scripts/                  # Core processing scripts
│   ├── config.py            # Centralized configuration
│   ├── pdf_extractor.py     # PDF to text extraction
│   ├── section_resumes.py   # AI-powered resume structuring
│   ├── build_vector_store.py # ChromaDB vector store builder
│   ├── query_resumes.py     # AI search functionality
│   ├── match_resumes.py     # Job matching logic
│   ├── export_chroma.py     # Database export utility
│   └── utils.py             # Shared utilities
└── data/                     # Data directory (gitignored)
    ├── raw/                  # Raw PDF resumes
    ├── processed/            # Extracted and structured data
    ├── chroma_db/            # Vector database
    └── uploads/              # User uploaded files
```

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/SmartHire.git
   cd SmartHire
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key
   GROQ_API_KEY=your_groq_api_key
   ```
   
   > **Note:** You can get free API keys from:
   > - [OpenRouter](https://openrouter.ai/) - For DeepSeek chat model
   > - [Groq](https://console.groq.com/) - For fast Llama inference

5. **Add resume data**
   
   Place PDF resumes in the `data/raw/fake_resumes/` directory.

## Usage

1. **Start the application**
   ```bash
   streamlit run app.py
   ```

2. **Process resumes**
   - Go to the **Pipeline Manager** tab
   - Click **Run Full Pipeline** to extract, structure, and embed all resumes
   - Or run each step individually

3. **Analyze individual resumes**
   - Go to the **Analyze Resume** tab
   - Upload one or more PDF files
   - Click **Analyze All Resumes with AI**

4. **Search candidates**
   - Go to the **AI Search** tab
   - Ask questions like "Who knows Python and SQL?"

5. **Match to job descriptions**
   - Go to the **Job Matching** tab
   - Paste a job description
   - Click **Match Candidates** to get ranked results with scores

## How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PDF Resume │────▶│ Text Extract│────▶│ AI Structure│
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  AI Answer  │◀────│   LLM RAG   │◀────│  ChromaDB   │
└─────────────┘     └─────────────┘     └─────────────┘
```

1. **PDF Extraction**: Raw PDFs are converted to plain text using pdfplumber
2. **AI Structuring**: LLM extracts structured data (skills, experience, education)
3. **Embedding**: Text is converted to vector embeddings using sentence-transformers
4. **Storage**: Vectors are stored in ChromaDB for efficient similarity search
5. **RAG Query**: User questions retrieve relevant resumes and generate AI answers
6. **Job Matching**: Job descriptions are compared against candidate profiles for scoring

---