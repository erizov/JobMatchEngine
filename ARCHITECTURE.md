# Resume & Cover Letter Optimization System - Architecture

## 1. High-Level Summary

**System**: Ingest resume/cover letter + job posting → extract structured data → compute ATS-optimized enhancements → generate improved documents via LLM with fact preservation → output DOCX/MD/TXT (RU/EN).

## 2. Design Goals

- ✅ Windows-native (Python + FastAPI + simple web UI)
- ✅ Parse: .txt, .md, .doc, .docx, .rtf
- ✅ Accept job URL or pasted text
- ✅ Auto-detect language (RU/EN), maintain single language
- ✅ Preserve original facts and voice
- ✅ Optimize for ATS (keyword matching, structure)
- ✅ Output: Enhanced resume + cover letter (DOCX, MD, TXT)
- ✅ Configurable: Cloud LLM (OpenAI/Anthropic) or local (Ollama)

## 3. Simplified Technical Stack

### Core
- **Python 3.11+** (main runtime)
- **FastAPI** (API server + simple HTML UI)
- **uvicorn** (ASGI server)

### File Parsing
- **python-docx** (primary for .docx read/write)
- **win32com.client** (pywin32) - Word COM for .doc/.rtf (Windows)
- **pypandoc** (fallback converter, requires Pandoc)
- **markdown** (for .md files)
- **textract** (optional, for complex formats)

### Web Scraping
- **httpx** (async HTTP client)
- **beautifulsoup4** (HTML parsing)
- **readability-lxml** or **trafilatura** (content extraction)

### NLP & Analysis
- **langdetect** (language detection)
- **spaCy** (tokenization, NER) - models: `ru_core_news_sm`, `en_core_web_sm`
- **sentence-transformers** (multilingual embeddings)
- **scikit-learn** (TF-IDF, keyword extraction)
- **keyBERT** (optional, keyword extraction)

### LLM & Generation
- **openai** (GPT-4/4o/4o-mini)
- **anthropic** (Claude, optional)
- **ollama** (local LLM, optional)
- **langchain** (orchestration, optional)

### Output Generation
- **python-docx** (DOCX creation)
- **markdown2** (MD export)
- **reportlab** (PDF, optional)

### Configuration & Utils
- **pydantic** (settings management)
- **python-dotenv** (environment variables)
- **loguru** (logging)

## 4. Simplified Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  (FastAPI HTML UI + REST API endpoints)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  - /api/upload (resume file)                                 │
│  - /api/job (job URL/text)                                   │
│  - /api/optimize (generate enhanced docs)                    │
│  - /api/download (get results)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Processing Pipeline                         │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Parser     │→ │   Analyzer   │→ │   Generator  │      │
│  │              │  │              │  │              │      │
│  │ - File parse │  │ - Lang detect│  │ - LLM calls  │      │
│  │ - Extract    │  │ - Extract    │  │ - Fact check │      │
│  │   sections   │  │   keywords   │  │ - Format     │      │
│  └──────────────┘  │ - Match JD   │  └──────────────┘      │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Storage Layer                             │
│  - Temporary file cache (input/output)                       │
│  - SQLite (metadata, job cache)                              │
│  - Optional: Qdrant/FAISS (RAG, Phase 2)                     │
└─────────────────────────────────────────────────────────────┘
```

## 5. Core Components

### 5.1 Parser Module (`app/parsers/`)
- **`file_parser.py`**: Main entry point, routes to format-specific parsers
- **`docx_parser.py`**: python-docx for .docx
- **`word_com_parser.py`**: Word COM for .doc/.rtf (Windows)
- **`text_parser.py`**: .txt/.md parsing
- **`job_parser.py`**: Web scraping + text extraction for job postings

**Output Structure**:
```python
{
    "contact": {"name": str, "email": str, "phone": str, ...},
    "summary": str,
    "experience": [
        {
            "title": str,
            "company": str,
            "dates": str,
            "bullets": List[str],
            "raw_text": str
        }
    ],
    "skills": List[str],
    "education": [...],
    "language": str,  # "ru" or "en"
    "raw_text": str
}
```

### 5.2 Analyzer Module (`app/analyzers/`)
- **`language_detector.py`**: Detect RU/EN, decide output language
- **`keyword_extractor.py`**: Extract keywords from resume and JD
- **`matcher.py`**: Compute skill overlap, missing keywords, ATS score
- **`section_extractor.py`**: Parse structured sections from raw text

### 5.3 Generator Module (`app/generators/`)
- **`llm_client.py`**: Unified interface for OpenAI/Anthropic/Ollama
- **`prompt_builder.py`**: Construct prompts with constraints
- **`resume_generator.py`**: Generate enhanced resume sections
- **`cover_letter_generator.py`**: Generate tailored cover letter
- **`fact_checker.py`**: Verify no hallucinated facts

### 5.4 Output Module (`app/output/`)
- **`docx_builder.py`**: Create DOCX with proper formatting
- **`markdown_builder.py`**: Export to MD
- **`text_builder.py`**: Export to TXT
- **`change_tracker.py`**: Track and summarize changes

### 5.5 Configuration (`app/config.py`)
- Settings via Pydantic (LLM provider, API keys, paths)
- Environment variables support

## 6. Simplified Processing Pipeline

### Step 1: Input Ingestion
1. User uploads resume file → save to `temp/input/`
2. User provides job URL or text → scrape/parse → save to `temp/jobs/`

### Step 2: Parsing & Normalization
1. Detect file type → route to appropriate parser
2. Extract structured data (sections, bullets, skills)
3. Extract plain text for analysis
4. Parse job posting → extract: title, requirements, responsibilities, keywords

### Step 3: Language Detection
1. Detect language of resume and job posting
2. Decision logic:
   - If same → use that language
   - If different → use job posting language (with translation if needed)
   - User can override

### Step 4: Analysis
1. Extract keywords from resume (TF-IDF + keyBERT)
2. Extract keywords from JD (must-have vs nice-to-have)
3. Compute overlap and gaps
4. Calculate ATS score (keyword match %)

### Step 5: Generation Strategy
1. Build enhancement plan:
   - Which keywords to add (max N per section)
   - Which bullets to strengthen
   - Which skills to emphasize
2. Generate prompts with constraints:
   - Preserve all facts (dates, companies, metrics)
   - Inject keywords naturally
   - Maintain original voice (tone parameter)

### Step 6: LLM Generation
1. **Resume sections** (sequential):
   - Rewrite summary/profile (target JD)
   - Enhance experience bullets (add keywords, metrics)
   - Update skills section (add missing keywords)
2. **Cover letter**:
   - Merge candidate background + JD requirements
   - 3-4 paragraphs, professional tone

### Step 7: Post-Processing
1. Fact check: verify no new companies/dates/metrics
2. Grammar/style check (optional: LanguageTool)
3. ATS re-scoring
4. Semantic similarity check (vs original)

### Step 8: Output
1. Build DOCX with enhanced content
2. Generate MD and TXT versions
3. Create change summary (what was added/changed)
4. Return files to user

## 7. Key Algorithms & Heuristics

### A. Keyword Injection
- Max 3-5 new keywords per section (configurable)
- Prefer insertion in summary and skills sections
- Never invent new experiences

### B. Fact Preservation
- Extract canonical facts before generation
- Post-generation validation: flag any new facts
- Use retrieval of original sentences in prompts

### C. Voice Preservation
- Compute style features (sentence length, formality)
- Constrain LLM: "Keep similar sentence structure and tone"
- Tone parameter: conservative (minimal changes) → aggressive (more optimization)

### D. ATS Scoring
```
ATS Score = (
    keyword_match_count / total_jd_keywords * 0.6 +
    title_match_score * 0.2 +
    structure_score * 0.2
) * 100
```

### E. Multi-language
- Auto-detect with `langdetect`
- If languages differ:
  - Option 1: Translate resume to JD language (if user allows)
  - Option 2: Generate in JD language, keep resume language for names/companies
- Prefer single language output

## 8. Windows-Specific Handling

1. **File Parsing Priority**:
   - `.docx`: python-docx (primary)
   - `.doc/.rtf`: Word COM (if Word installed) → pypandoc (fallback)
   - `.txt/.md`: Direct read

2. **Word COM Usage**:
   ```python
   import win32com.client
   word = win32com.client.Dispatch("Word.Application")
   word.Visible = False
   doc = word.Documents.Open(file_path)
   # Extract text, paragraphs, formatting
   ```

3. **Service Mode**: Optional Windows service wrapper (Phase 3)

## 9. Configuration Structure

```python
# app/config.py
class Settings(BaseSettings):
    # LLM
    llm_provider: str = "openai"  # openai, anthropic, ollama
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "gpt-4o-mini"
    
    # Paths
    input_dir: Path = Path("temp/input")
    output_dir: Path = Path("temp/output")
    cache_dir: Path = Path("temp/cache")
    
    # Generation
    tone: str = "balanced"  # conservative, balanced, aggressive
    max_keywords_per_section: int = 3
    preserve_facts: bool = True
    
    # Language
    default_language: Optional[str] = None  # None = auto-detect
    
    class Config:
        env_file = ".env"
```

## 10. API Endpoints (FastAPI)

```python
POST /api/upload          # Upload resume file
POST /api/job             # Submit job URL or text
POST /api/optimize        # Generate enhanced documents
GET  /api/status/{job_id} # Check generation status
GET  /api/download/{job_id} # Download results
GET  /api/preview/{job_id}  # Preview changes
```

## 11. Project Structure

```
JobMatchEngine/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── models.py            # Pydantic models
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── file_parser.py
│   │   ├── docx_parser.py
│   │   ├── word_com_parser.py
│   │   ├── text_parser.py
│   │   └── job_parser.py
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── language_detector.py
│   │   ├── keyword_extractor.py
│   │   ├── matcher.py
│   │   └── section_extractor.py
│   │
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   ├── prompt_builder.py
│   │   ├── resume_generator.py
│   │   ├── cover_letter_generator.py
│   │   └── fact_checker.py
│   │
│   ├── output/
│   │   ├── __init__.py
│   │   ├── docx_builder.py
│   │   ├── markdown_builder.py
│   │   ├── text_builder.py
│   │   └── change_tracker.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       └── cache.py
│
├── temp/
│   ├── input/              # Uploaded resumes
│   ├── output/             # Generated files
│   └── cache/              # Job cache, metadata
│
├── templates/              # HTML templates (FastAPI)
│   └── index.html
│
├── static/                 # CSS, JS (if needed)
│
├── tests/
│   ├── test_parsers.py
│   ├── test_analyzers.py
│   └── test_generators.py
│
├── requirements.txt
├── .env.example
├── README.md
├── ARCHITECTURE.md
└── .gitignore
```

## 12. Implementation Phases

### Phase 1: MVP (2-3 weeks)
- ✅ File parsing (docx, txt, md)
- ✅ Job scraping
- ✅ Language detection
- ✅ Basic keyword extraction
- ✅ LLM integration (OpenAI)
- ✅ Simple resume enhancement
- ✅ DOCX output
- ✅ FastAPI + basic HTML UI

### Phase 2: Enhancement (2-3 weeks)
- ✅ Cover letter generation
- ✅ ATS scoring
- ✅ Change tracking
- ✅ Multiple variants (conservative/aggressive)
- ✅ Fact checking
- ✅ Better prompts

### Phase 3: Advanced (2-3 weeks)
- ✅ RAG with vector DB (Qdrant/FAISS)
- ✅ Local LLM support (Ollama)
- ✅ Batch processing
- ✅ Watch folder automation
- ✅ PDF export
- ✅ Desktop app (optional: Electron)

## 13. Improvements Over Original Design

1. **Simplified**: Removed Electron initially (use FastAPI HTML UI)
2. **Focused**: Start without RAG, add in Phase 2
3. **Clearer separation**: Each module has single responsibility
4. **Better config**: Pydantic settings management
5. **Simpler pipeline**: Fewer steps, clearer flow
6. **Practical**: Windows-first, Word COM prioritized
7. **Incremental**: MVP → Enhancement → Advanced

## 14. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LLM hallucination | Strict prompts, fact extraction, post-generation validation |
| Parsing errors | Word COM first, multiple fallbacks, error handling |
| Privacy | Local-first, opt-in cloud, data redaction option |
| Language quality | Multilingual models, single-language preference, translation only if needed |
| ATS effectiveness | Test with real ATS systems, keyword density optimization |

## 15. Next Steps

1. Create project structure
2. Implement file parsers (docx, text)
3. Implement job parser
4. Set up LLM client
5. Build basic generation pipeline
6. Create FastAPI endpoints
7. Build simple UI

