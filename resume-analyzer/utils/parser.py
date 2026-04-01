"""
parser.py — Resume PDF Text Extraction Module

Responsible for reading uploaded PDF files and extracting raw text content.
Uses PyPDF2 for reliable, dependency-light PDF parsing.
"""

import PyPDF2
import io
import re
from typing import Optional


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract all text content from an uploaded PDF file.

    Works with Streamlit's UploadedFile object by reading its byte buffer,
    iterating through every page, and concatenating the extracted text.

    Args:
        uploaded_file: A file-like object (e.g., Streamlit UploadedFile)
                       containing the PDF bytes.

    Returns:
        A single string with all text extracted from the PDF.
        Returns an empty string if no text could be extracted.

    Raises:
        ValueError: If the uploaded file is None or cannot be read.
        RuntimeError: If PDF parsing fails due to corruption or encryption.
    """
    if uploaded_file is None:
        raise ValueError("No file provided. Please upload a valid PDF.")

    try:
        # Read the uploaded file bytes into a BytesIO stream for PyPDF2
        pdf_bytes = io.BytesIO(uploaded_file.read())
        reader = PyPDF2.PdfReader(pdf_bytes)

        # Guard against encrypted PDFs that require a password
        if reader.is_encrypted:
            raise RuntimeError(
                "The uploaded PDF is encrypted. "
                "Please upload an unencrypted version."
            )

        extracted_pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text)

        full_text = "\n".join(extracted_pages)

        # Basic cleanup: collapse excessive whitespace while preserving newlines
        full_text = re.sub(r"[^\S\n]+", " ", full_text)  # horizontal whitespace
        full_text = re.sub(r"\n{3,}", "\n\n", full_text)  # excess blank lines
        full_text = full_text.strip()

        return full_text

    except PyPDF2.errors.PdfReadError as e:
        raise RuntimeError(
            f"Failed to parse PDF — the file may be corrupted or invalid. "
            f"Details: {e}"
        )
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while reading the PDF: {e}")
