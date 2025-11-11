"""RAG (Retrieval-Augmented Generation) utilities for loading knowledge base from files."""

from pathlib import Path
from typing import Optional


def load_rag_context(rag_file: Optional[str] = None) -> Optional[str]:
    """
    Load RAG context from a file to use as knowledge base.
    
    Args:
        rag_file: Path to RAG knowledge base file (optional)
        
    Returns:
        RAG context text or None if file not provided or not found
    """
    if not rag_file:
        return None
    
    rag_path = Path(rag_file)
    if not rag_path.exists():
        return None
    
    try:
        # Try UTF-8 first, then fallback to other encodings
        with open(rag_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content.strip() if content else None
    except UnicodeDecodeError:
        # Try with errors='ignore' for binary or problematic files
        try:
            with open(rag_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return content.strip() if content else None
        except Exception:
            return None
    except Exception:
        return None

