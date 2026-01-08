"""PDF handling utilities using PyMuPDF."""

from pathlib import Path
from typing import Optional
from PIL import Image
import fitz  # PyMuPDF
from utils.logger import logger

def extract_text_from_pdf(file_path: Path) -> Optional[str]:
    """Extract text directly from PDF using PyMuPDF.
    
    Extracts text from ALL pages in the PDF.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Combined text from all pages or None if extraction fails
    """
    try:
        doc = fitz.open(str(file_path))
        text_parts = []
        
        # Extract text from all pages
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text:
                text_parts.append(f"[Page {page_num + 1}]\n{text}")
        
        doc.close()
        
        if text_parts:
            full_text = "\n\n".join(text_parts)
            logger.info(
                f"Extracted {len(full_text)} characters from PDF "
                f"({len(text_parts)} pages) using direct text extraction"
            )
            return full_text
        
        logger.warning("No text extracted from PDF using direct extraction")
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return None

def convert_pdf_page_to_image(
    file_path: Path,
    page_num: int = 0,
    dpi: int = 300
) -> Optional[Image.Image]:
    """Convert PDF page to PIL Image using PyMuPDF.
    
    Args:
        file_path: Path to PDF file
        page_num: Page number to convert (0-indexed)
        dpi: Resolution for image (default: 400)
        
    Returns:
        PIL Image or None if conversion fails
    """
    try:
        doc = fitz.open(str(file_path))
        
        if page_num >= len(doc):
            logger.warning(
                f"Page {page_num} not found in PDF "
                f"(document has {len(doc)} pages)"
            )
            doc.close()
            return None
        
        # Get page
        page = doc[page_num]
        
        # Calculate zoom factor for desired DPI (default is 72 DPI)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        # Render page to pixmap
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        doc.close()
        logger.debug(
            f"Converted PDF page {page_num + 1} to image "
            f"({pix.width}x{pix.height})"
        )
        return img
        
    except Exception as e:
        logger.error(f"Failed to convert PDF page to image: {e}")
        return None

def get_pdf_page_count(file_path: Path) -> int:
    """Get the number of pages in a PDF.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Number of pages in PDF, or 0 on error
    """
    try:
        doc = fitz.open(str(file_path))
        page_count = len(doc)
        doc.close()
        return page_count
    except Exception as e:
        logger.error(f"Failed to get PDF page count: {e}")
        return 0

