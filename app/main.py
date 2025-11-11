"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.config import settings

app = FastAPI(
    title="JobMatchEngine",
    description="Resume and Cover Letter Optimization System",
    version="0.1.0",
)

# Include API routes
app.include_router(api_router)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass  # Directory doesn't exist yet


@app.get("/", response_class=HTMLResponse)
async def root():
    """Main page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JobMatchEngine</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }
            .section {
                margin: 20px 0;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 4px;
            }
            .status {
                padding: 10px;
                background: #e3f2fd;
                border-left: 4px solid #2196F3;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 JobMatchEngine</h1>
            <div class="status">
                <strong>Status:</strong> API is running. UI implementation in progress.
            </div>
            <div class="section">
                <h2>API Endpoints</h2>
                <ul>
                    <li><code>POST /api/upload</code> - Upload resume file</li>
                    <li><code>POST /api/job</code> - Submit job URL or text</li>
                    <li><code>POST /api/optimize</code> - Generate enhanced documents</li>
                    <li><code>GET /api/status/{job_id}</code> - Check status</li>
                    <li><code>GET /api/download/{job_id}</code> - Download results</li>
                </ul>
            </div>
            <div class="section">
                <h2>Configuration</h2>
                <p><strong>LLM Provider:</strong> {llm_provider}</p>
                <p><strong>Model:</strong> {model_name}</p>
                <p><strong>Input Dir:</strong> {input_dir}</p>
                <p><strong>Output Dir:</strong> {output_dir}</p>
            </div>
            <div class="section">
                <h2>Documentation</h2>
                <p><a href="/docs">Swagger UI</a> | <a href="/redoc">ReDoc</a></p>
            </div>
        </div>
    </body>
    </html>
    """.format(
        llm_provider=settings.llm_provider,
        model_name=settings.model_name,
        input_dir=settings.input_dir,
        output_dir=settings.output_dir,
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


# API endpoints are in app/api.py

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

