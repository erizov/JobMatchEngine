# Quick Start Guide

## Overview

This project implements an AI-powered resume and cover letter optimization system that enhances documents to beat ATS (Applicant Tracking Systems) while preserving original facts and voice.

## Architecture Summary

### Simplified Design
- **FastAPI** backend with simple HTML UI (no Electron initially)
- **Modular structure**: parsers → analyzers → generators → output
- **Incremental complexity**: MVP → Enhancement → Advanced
- **Windows-first**: Word COM for .doc/.rtf, python-docx for .docx

### Key Components

1. **Parsers** (`app/parsers/`)
   - File parsers: DOCX, DOC, RTF, TXT, MD
   - Job parser: Web scraping + text extraction

2. **Analyzers** (`app/analyzers/`)
   - Language detection (RU/EN)
   - Keyword extraction
   - Resume-JD matching

3. **Generators** (`app/generators/`)
   - LLM client (OpenAI/Anthropic/Ollama)
   - Resume enhancement
   - Cover letter generation

4. **Output** (`app/output/`)
   - DOCX builder
   - MD/TXT exporters
   - Change tracking

## Installation

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy models
python -m spacy download en_core_web_sm
python -m spacy download ru_core_news_sm

# 4. Create .env file
cp .env.example .env
# Edit .env and add your API keys

# 5. Run server
uvicorn app.main:app --reload
```

## Current Status

✅ Project structure created
✅ Configuration system (Pydantic)
✅ Data models defined
✅ Basic parsers skeleton
✅ FastAPI app structure
⏳ Parsers implementation (in progress)
⏳ Analyzers (pending)
⏳ Generators (pending)
⏳ Output builders (pending)
⏳ API endpoints (pending)

## Next Steps

1. **Complete parsers**: Implement section extraction logic
2. **Implement analyzers**: Language detection, keyword extraction
3. **Build generators**: LLM integration, prompt engineering
4. **Create output**: DOCX/MD/TXT builders
5. **API endpoints**: Upload, optimize, download
6. **UI**: Simple HTML interface

## Key Improvements Over Original Design

1. **Simpler UI**: FastAPI HTML instead of Electron (can add later)
2. **Incremental RAG**: Start without vector DB, add in Phase 2
3. **Clear modules**: Better separation of concerns
4. **Type safety**: Pydantic models throughout
5. **Phased rollout**: MVP → Enhancement → Advanced

## Configuration

See `.env.example` for all configuration options. Key settings:

- `LLM_PROVIDER`: openai, anthropic, or ollama
- `OPENAI_API_KEY`: Your OpenAI API key
- `TONE`: conservative, balanced, or aggressive
- `MAX_KEYWORDS_PER_SECTION`: How many keywords to add

## Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app
```

## Development

```bash
# Format code
black app/

# Lint
flake8 app/

# Type check (when mypy is added)
mypy app/
```

## Documentation

- `ARCHITECTURE.md` - Full architecture details
- `ARCHITECTURE_IMPROVEMENTS.md` - Improvements and simplifications
- `README.md` - Project overview

