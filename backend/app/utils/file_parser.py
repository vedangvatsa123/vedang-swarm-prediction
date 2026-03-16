"""
File parsing utilities.
Extracts plain text from PDF, Markdown and plain-text files.
"""
import os
from pathlib import Path
from typing import List


def _read_with_fallback(filepath: str) -> str:
    """Read a text file, falling back through encodings."""
    raw = Path(filepath).read_bytes()
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def extract_text(filepath: str) -> str:
    """Extract text content from a single file."""
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(filepath)
    if ext in (".md", ".markdown", ".txt"):
        return _read_with_fallback(filepath)
    raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf(filepath: str) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("Install PyMuPDF: pip install PyMuPDF")
    pages: List[str] = []
    with fitz.open(filepath) as doc:
        for page in doc:
            t = page.get_text()
            if t.strip():
                pages.append(t)
    return "\n\n".join(pages)


def extract_multiple(filepaths: List[str]) -> str:
    """Extract and concatenate text from several files."""
    parts: List[str] = []
    for i, fp in enumerate(filepaths, 1):
        try:
            text = extract_text(fp)
            name = Path(fp).name
            parts.append(f"=== Document {i}: {name} ===\n{text}")
        except Exception as exc:
            parts.append(f"=== Document {i}: {fp} (failed: {exc}) ===")
    return "\n\n".join(parts)


def chunk_text(text: str, size: int = 600, overlap: int = 80) -> List[str]:
    """Split text into overlapping chunks, preferring sentence boundaries."""
    if len(text) <= size:
        return [text] if text.strip() else []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Try to break at sentence boundary
            for sep in (".\n", "!\n", "?\n", "\n\n", ". ", "! ", "? "):
                pos = text[start:end].rfind(sep)
                if pos > size * 0.3:
                    end = start + pos + len(sep)
                    break
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        start = end - overlap if end < len(text) else len(text)
    return chunks
