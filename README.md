# JobMatchEngine - Resume & Cover Letter Optimizer

AI-powered system to enhance resumes and generate tailored cover letters optimized for ATS (Applicant Tracking Systems) and job postings. Supports both Russian and English languages with automatic language detection and translation.

## 🚀 Features

- 📄 **Multi-format Support**: Parse `.txt`, `.md`, `.doc`, `.docx`, `.rtf` files
- 🌐 **Job Posting Integration**: Extract job requirements from URLs (hh.ru, etc.) or pasted text
- 🌍 **Multilingual**: Automatic language detection (Russian/English) with full translation support
- 🤖 **AI-Powered**: Uses LLMs (OpenAI, Anthropic, or local Ollama) for intelligent enhancement
- ✅ **Fact-Preserving**: Maintains original information while optimizing for ATS
- 📊 **ATS Optimization**: Keyword matching, structure optimization, scoring
- 📝 **Multiple Outputs**: DOCX, MD, TXT formats in both languages
- 🔄 **Dynamic Job Fetching**: Automatically fetches latest job postings from hh.ru
- 🧹 **Auto Cleanup**: Automatically removes old output files
- 💾 **LLM Response Caching**: Saves tokens by caching responses across formats
- 📈 **Token Usage Tracking**: Monitor API usage with detailed token statistics
- 🧠 **RAG Support**: Optional knowledge base file for enhanced context

## 🛠️ Technologies Used

### Core Framework
- **FastAPI** - Modern, fast web framework for building APIs
- **Uvicorn** - ASGI server for FastAPI
- **Pydantic** - Data validation and settings management
- **Python 3.11+** - Modern Python features

### File Parsing
- **python-docx** - DOCX file reading/writing
- **pywin32** - Windows COM interface for .doc/.rtf parsing
- **BeautifulSoup4** - HTML parsing for web scraping
- **trafilatura** - Content extraction from web pages

### NLP & Analysis
- **spaCy** - Natural language processing (RU/EN models)
- **langdetect** - Language detection
- **sentence-transformers** - Multilingual embeddings
- **scikit-learn** - TF-IDF keyword extraction
- **KeyBERT** - Keyword extraction using BERT

### LLM Integration
- **OpenAI** - GPT-4, GPT-4o, GPT-4o-mini
- **Anthropic** - Claude (optional)
- **Ollama** - Local LLM support (optional)

### Web Scraping
- **httpx** - Async HTTP client
- **BeautifulSoup4** - HTML parsing
- **trafilatura** - Content extraction

### Output Generation
- **python-docx** - DOCX document creation
- **reportlab** - PDF generation (optional)

## 📦 Quick Start

### Prerequisites

- Python 3.11+
- Windows 10/11 (recommended for Word COM support)
- Microsoft Word (optional, for .doc/.rtf parsing)
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/erizov/JobMatchEngine.git
cd JobMatchEngine
```

2. **Create virtual environment:**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Download spaCy models:**
```bash
python -m spacy download en_core_web_sm
python -m spacy download ru_core_news_sm
```

5. **Create `.env` file:**
```bash
# Copy example (if exists) or create new
# Add your API keys
```

6. **Configure environment variables:**
Create a `.env` file in the project root:
```env
# LLM Provider (openai, anthropic, ollama)
LLM_PROVIDER=openai

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic (optional)
ANTHROPIC_API_KEY=your_anthropic_key_here

# Ollama (optional, for local LLM)
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=gpt-4o-mini

# Paths
INPUT_DIR=temp/input
OUTPUT_DIR=temp/output
CACHE_DIR=temp/cache

# Generation Settings
TONE=balanced  # conservative, balanced, aggressive
MAX_KEYWORDS_PER_SECTION=3

# Output Cleanup (hours)
OUTPUT_CLEANUP_HOURS=24

# Test Job URL (optional, for integration tests)
TEST_JOB_URL=https://hh.ru/vacancy/123456789
```

7. **Run the server:**
```bash
uvicorn app.main:app --reload
```

8. **Open browser:**
Navigate to `http://localhost:8000`

## 📖 Usage Examples

### Web UI

1. Start the server: `uvicorn app.main:app --reload`
2. Open `http://localhost:8000` in your browser
3. Upload your resume file (.docx, .doc, .txt, .md, .rtf)
4. Paste job URL (e.g., `https://hh.ru/vacancy/123456789`) or job description text
5. Click "Optimize"
6. Download enhanced resume and cover letter in both English and Russian

### API Usage

#### Upload Resume
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@resume.docx"
```

#### Parse Job Posting
```bash
curl -X POST "http://localhost:8000/api/job" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://hh.ru/vacancy/123456789"}'
```

#### Optimize Resume
```bash
curl -X POST "http://localhost:8000/api/optimize" \
  -F "file_id=your_file_id" \
  -F "job_id=your_job_id" \
  -F "tone=balanced"
```

#### Download Results
```bash
curl -X GET "http://localhost:8000/api/download/result_id"
```

### Integration Tests

The project includes comprehensive integration tests that process real resume files:

1. **Prepare test files:**
   - Place resume files in `temp/input/` directory
   - Supported formats: `.docx`, `.doc`, `.rtf`, `.txt`, `.md`

2. **Run integration tests:**
```bash
python run_integration_tests.py
```

3. **What the tests do:**
   - Processes all files in `temp/input/`
   - Fetches latest job posting from hh.ru (with keywords: AI, Java, ML)
   - Generates enhanced resumes and cover letters
   - Creates outputs in both English and Russian
   - Generates 6 output files per input (DOCX, MD, TXT for resume + cover letter)
   - Calculates ATS scores before/after optimization
   - Cleans up old output files automatically

4. **Output files:**
   - Location: `temp/output/`
   - Format: `{filename}_enhanced_{lang}.{ext}` and `{filename}_cover_letter_{lang}.{ext}`
   - Languages: `_en` (English) and `_ru` (Russian)

### Example Test Output

```
============================================================
JobMatchEngine Integration Test
============================================================

[INFO] Cleaning up old output files...
  [OK] No old files to clean up

[INFO] LLM client available - enhancement enabled
[INFO] Found 7 resume file(s)

[INFO] Creating test job posting...
[INFO] Using job URL: https://hh.ru/vacancy/127101925
[OK] Job posting parsed from URL: Backend-разработчик
[OK] Company: Prospero agency
[OK] Language: ru

============================================================
Processing 7 file(s)...
============================================================

[1/7] resume_en.txt
  [1/6] Parsing resume...
       [OK] Parsed 1008 characters
       [OK] Experience entries: 7
       [OK] Skills: 11
  [2/6] Detecting language...
       [OK] Resume language: en
       [OK] Job language: ru
       [OK] Output language: ru
  [3/6] Analyzing match...
       [OK] ATS Score (before): 30.0/100
  [4/6] Generating enhanced resume...
       [OK] Enhanced resume generated
       [OK] ATS Score (after): 45.0/100
       [OK] Score improvement: +15.0
  [5/6] Generating cover letter...
       [OK] Cover letter generated: 535 chars
  [6/6] Generating output files in 2 languages...
       Generating EN versions...
         [OK] resume_en_enhanced_en.docx
         [OK] resume_en_enhanced_en.md
         [OK] resume_en_enhanced_en.txt
         [OK] resume_en_cover_letter_en.docx
         [OK] resume_en_cover_letter_en.md
         [OK] resume_en_cover_letter_en.txt
       Generating RU versions...
         [OK] resume_en_enhanced_ru.docx
         [OK] resume_en_enhanced_ru.md
         [OK] resume_en_enhanced_ru.txt
         [OK] resume_en_cover_letter_ru.docx
         [OK] resume_en_cover_letter_ru.md
         [OK] resume_en_cover_letter_ru.txt

============================================================
Summary
============================================================
Total files processed: 7
  [OK] Completed: 7
  [FAIL] Failed: 0
Average ATS score improvement: +12.5
```

## 🧪 Test Examples

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_integration.py

# Run with verbose output
pytest -v
```

### Integration Test Workflow

1. **Add test resumes to `temp/input/`:**
   ```
   temp/input/
   ├── resume_en.txt
   ├── resume_en.md
   ├── resume_en.docx
   ├── resume_ru.txt
   └── Rizov_Resume_Modern.docx
   ```

2. **Run integration tests:**
   ```bash
   python run_integration_tests.py
   ```

3. **Check results:**
   - Output files: `temp/output/`
   - Each input file generates 12 output files (6 formats × 2 languages)
   - English versions use: "Eugene Rizov" and "erizov@yahoo.com"
   - Russian versions are fully in Russian

### Test Configuration

The integration tests automatically:
- ✅ Fetch latest job from hh.ru (keywords: AI, Java, ML)
- ✅ Clean up files older than 24 hours
- ✅ Generate outputs in both languages
- ✅ Use real company names from job postings
- ✅ Use actual candidate names in cover letters

## 📁 Project Structure

```
JobMatchEngine/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── api.py               # API endpoints
│   ├── config.py            # Configuration (Pydantic)
│   ├── models.py            # Data models
│   ├── parsers/             # File and job parsers
│   │   ├── file_parser.py
│   │   ├── docx_parser.py
│   │   ├── word_com_parser.py
│   │   ├── text_parser.py
│   │   └── job_parser.py
│   ├── analyzers/           # Analysis modules
│   │   ├── language_detector.py
│   │   ├── keyword_extractor.py
│   │   └── matcher.py
│   ├── generators/          # LLM generators
│   │   ├── llm_client.py
│   │   ├── prompt_builder.py
│   │   ├── resume_generator.py
│   │   └── cover_letter_generator.py
│   ├── output/              # Output builders
│   │   ├── docx_builder.py
│   │   ├── markdown_builder.py
│   │   └── text_builder.py
│   └── utils/               # Utilities
│       ├── section_extractor.py
│       ├── cleanup.py
│       └── hh_ru_fetcher.py
├── tests/                   # Test files
│   ├── test_integration.py
│   └── fixtures/            # Test data
├── temp/                    # Temporary files
│   ├── input/               # Input resumes
│   └── output/              # Generated files
├── run_integration_tests.py # Integration test script
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in git)
├── .gitignore
├── README.md
├── ARCHITECTURE.md          # Detailed architecture
└── QUICKSTART.md            # Quick start guide
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (openai, anthropic, ollama) | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `MODEL_NAME` | Model name | `gpt-4o-mini` |
| `INPUT_DIR` | Input directory | `temp/input` |
| `OUTPUT_DIR` | Output directory | `temp/output` |
| `TONE` | Generation tone | `balanced` |
| `OUTPUT_CLEANUP_HOURS` | Cleanup old files after (hours) | `24` |
| `TEST_JOB_URL` | Test job URL (optional) | Auto-fetched from hh.ru |

### Generation Tones

- **conservative**: Minimal changes, preserve original wording
- **balanced**: Optimize for ATS while preserving voice (recommended)
- **aggressive**: Heavy optimization for maximum keyword density

## 🌍 Multilingual Support

The system automatically:
- Detects language of resume and job posting
- Generates outputs in both English and Russian
- Uses appropriate greetings and closings:
  - English: "Dear Hiring Manager at [Company]"
  - Russian: "Уважаемые коллеги компании [Company]"
- Translates cover letters fully (not just keywords)
- Uses correct contact info per language:
  - English: "Eugene Rizov" / "erizov@yahoo.com"
  - Russian: Original name from resume

## 📊 ATS Optimization Features

- **Keyword Matching**: Extracts and matches keywords from job postings
- **Score Calculation**: ATS compatibility score (0-100)
- **Keyword Density**: Optimizes keyword placement and frequency
- **Structure Optimization**: Formats for ATS parsing
- **Recommendations**: Actionable suggestions for improvement

## 🚨 Important Notes

- **API Keys**: Never commit `.env` file with API keys to git
- **Windows**: Full .doc/.rtf support requires Windows + Microsoft Word
- **LLM Costs**: Using cloud LLMs (OpenAI/Anthropic) incurs API costs
- **Rate Limits**: Be aware of API rate limits when processing many files

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed system architecture
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [ARCHITECTURE_IMPROVEMENTS.md](ARCHITECTURE_IMPROVEMENTS.md) - Architecture improvements

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`
2. **spaCy models**: Download models: `python -m spacy download en_core_web_sm ru_core_news_sm`
3. **Windows COM errors**: Ensure Microsoft Word is installed for .doc/.rtf parsing
4. **API errors**: Check your API keys in `.env` file
5. **Encoding issues**: Set `PYTHONIOENCODING=utf-8` on Windows

### Getting Help

- Check existing issues on GitHub
- Review the architecture documentation
- Check test examples for usage patterns

## 🎯 Roadmap

- [ ] PDF output support
- [ ] More job site integrations
- [ ] Advanced RAG with vector databases
- [ ] Web UI improvements
- [ ] CLI tool
- [ ] Docker support
- [ ] More language support

---

Made with ❤️ by Eugene Rizov
