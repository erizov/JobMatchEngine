# JobMatchEngine - Usage Guide

## Quick Start: Optimize Resume with Job Vacancy URL

### Simple CLI Script (Recommended)

The easiest way to optimize a resume with a job vacancy URL:

```bash
python optimize_resume.py <resume_file> <job_url> [tone] [output_languages] [rag_file]
```

**Examples:**

```bash
# Basic usage (Russian only, default)
python optimize_resume.py resume.docx https://hh.ru/vacancy/127101925

# With custom tone
python optimize_resume.py resume.docx https://hh.ru/vacancy/127101925 balanced

# English only
python optimize_resume.py resume.docx https://hh.ru/vacancy/127101925 balanced en

# Both languages
python optimize_resume.py resume.docx https://hh.ru/vacancy/127101925 balanced both

# With RAG knowledge base file
python optimize_resume.py resume.docx https://hh.ru/vacancy/127101925 balanced ru knowledge_base.txt

# Different file formats
python optimize_resume.py resume.txt https://hh.ru/vacancy/127101925
python optimize_resume.py resume.md https://hh.ru/vacancy/127101925
```

**Parameters:**
- `resume_file` - Path to your resume file (required)
- `job_url` - URL to job vacancy (required)
- `tone` - Generation tone (optional, default: `balanced`)
  - `conservative` - Minimal changes, preserve original wording
  - `balanced` - Optimize for ATS while preserving voice (default)
  - `aggressive` - Heavy optimization for maximum keyword density
- `output_languages` - Output languages (optional, default: `ru`)
  - `ru` - Russian only (default)
  - `en` - English only
  - `both` - Both languages
- `rag_file` - Path to knowledge base file for RAG context (optional)

**Output:**
- Files are saved to `temp/output/` directory
- Generates 6 files per language:
  - Enhanced resume: DOCX, MD, TXT (3 formats)
  - Cover letter: DOCX, MD, TXT (3 formats)
- English versions use: "Eugene Rizov" / "erizov@yahoo.com"
- Russian versions use: Original name from resume
- Token usage statistics displayed at the end

---

## Using the API Server

### 1. Start the Server

```bash
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

### 2. Use the API

#### Option A: Using curl

```bash
# Step 1: Upload resume
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@resume.docx"

# Response: {"file_id": "abc123...", "status": "uploaded"}

# Step 2: Submit job URL
curl -X POST "http://localhost:8000/api/job" \
  -F "job_url=https://hh.ru/vacancy/127101925"

# Response: {"job_id": "def456...", "status": "parsed", "title": "...", "company": "..."}

# Step 3: Optimize
curl -X POST "http://localhost:8000/api/optimize" \
  -F "file_id=abc123..." \
  -F "job_id=def456..." \
  -F "tone=balanced"

# Response: {"result_id": "ghi789...", "status": "completed", ...}

# Step 4: Download results
curl -X GET "http://localhost:8000/api/download/ghi789...?file_type=resume_docx" \
  -o resume_enhanced.docx

curl -X GET "http://localhost:8000/api/download/ghi789...?file_type=cover_letter_docx" \
  -o cover_letter.docx
```

#### Option B: Using Python requests

```python
import requests

# Step 1: Upload resume
with open("resume.docx", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload",
        files={"file": f}
    )
file_id = response.json()["file_id"]

# Step 2: Submit job URL
response = requests.post(
    "http://localhost:8000/api/job",
    data={"job_url": "https://hh.ru/vacancy/127101925"}
)
job_id = response.json()["job_id"]

# Step 3: Optimize
response = requests.post(
    "http://localhost:8000/api/optimize",
    data={
        "file_id": file_id,
        "job_id": job_id,
        "tone": "balanced"
    }
)
result_id = response.json()["result_id"]

# Step 4: Download results
files = [
    "resume_docx", "resume_md", "resume_txt",
    "cover_letter_docx", "cover_letter_md", "cover_letter_txt"
]
for file_type in files:
    response = requests.get(
        f"http://localhost:8000/api/download/{result_id}",
        params={"file_type": file_type}
    )
    with open(f"{file_type}.{file_type.split('_')[-1]}", "wb") as f:
        f.write(response.content)
```

#### Option C: Using Swagger UI

1. Start the server: `uvicorn app.main:app --reload`
2. Open `http://localhost:8000/docs` in your browser
3. Use the interactive API documentation to test endpoints

---

## File Formats Supported

**Input (Resume):**
- `.docx` - Microsoft Word (recommended)
- `.doc` - Microsoft Word (legacy, requires Word installed)
- `.rtf` - Rich Text Format (requires Word installed)
- `.txt` - Plain text
- `.md` - Markdown

**Output:**
- `.docx` - Microsoft Word
- `.md` - Markdown
- `.txt` - Plain text

**Languages:**
- English (`_en`)
- Russian (`_ru`)

---

## Output Directory Structure

```
temp/output/
├── resume_enhanced_en.docx
├── resume_enhanced_en.md
├── resume_enhanced_en.txt
├── resume_enhanced_ru.docx
├── resume_enhanced_ru.md
├── resume_enhanced_ru.txt
├── resume_cover_letter_en.docx
├── resume_cover_letter_en.md
├── resume_cover_letter_en.txt
├── resume_cover_letter_ru.docx
├── resume_cover_letter_ru.md
└── resume_cover_letter_ru.txt
```

---

## Configuration

Edit `.env` file to configure:

```env
# LLM Provider
LLM_PROVIDER=openai

# API Keys
OPENAI_API_KEY=your_key_here

# Paths
INPUT_DIR=temp/input
OUTPUT_DIR=temp/output

# Generation Settings
TONE=balanced
MAX_KEYWORDS_PER_SECTION=3

# Cleanup
OUTPUT_CLEANUP_HOURS=24
```

---

## Troubleshooting

### Common Issues

1. **"Resume file not found"**
   - Check the file path is correct
   - Use absolute path if relative path doesn't work

2. **"Failed to parse job posting"**
   - Check the URL is accessible
   - Some job sites may require authentication
   - Try copying job description text instead

3. **"LLM enhancement failed"**
   - Check your API key in `.env`
   - Verify API quota/limits
   - System will fall back to original resume

4. **Output directory not created**
   - Check write permissions
   - Ensure `temp/` directory exists

### Getting Help

- Check API documentation: `http://localhost:8000/docs`
- Review logs for error messages
- Check `.env` configuration

