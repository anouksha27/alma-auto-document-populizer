"""OCR handling utilities using PaddleOCR and Gemini."""

from pathlib import Path
from typing import Optional
from PIL import Image, ImageEnhance
import numpy as np
from paddleocr import PaddleOCR
import google.generativeai as genai
from utils.logger import logger
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME
from utils.pdf_handler import (
    extract_text_from_pdf,
    convert_pdf_page_to_image,
    get_pdf_page_count
)

# Global PaddleOCR instance (lazy initialization)
_ocr_reader = None

def _get_ocr_reader():
    """Get or initialize PaddleOCR reader (cached).
    
    Returns:
        PaddleOCR instance
    """
    global _ocr_reader
    if _ocr_reader is None:
        logger.info("Initializing PaddleOCR (this may take a moment on first run)...")
        _ocr_reader = PaddleOCR(
            use_angle_cls=True,  # Enable text line orientation classification
            use_doc_orientation_classify=True,  # Document-level orientation detection
            use_doc_unwarping=True,  # Document unwarping for curved documents
            lang='en'
        )
        logger.info("PaddleOCR initialized successfully")
    return _ocr_reader

def preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocess image to improve OCR accuracy.
    
    Args:
        image: PIL Image
        
    Returns:
        Preprocessed PIL Image
    """
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)  # Increase contrast by 20%
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.1)  # Increase sharpness by 10%
    
    return image

def extract_text_from_image(image: Image.Image) -> Optional[str]:
    """Extract text from image using PaddleOCR.
    
    Args:
        image: PIL Image
        
    Returns:
        Extracted text as string or None if extraction fails
    """
    try:
        # Preprocess image first
        image = preprocess_image(image)
        
        # Get cached reader
        ocr = _get_ocr_reader()
        
        # Convert PIL Image to numpy array
        img_array = np.array(image)
        
        # Run OCR (rotation detection handled by use_angle_cls in initialization)
        results = ocr.ocr(img_array)
        
        if not results or not results[0]:
            logger.warning("OCR returned no results")
            return None
        
        # Extract text from results
        # PaddleOCR returns: [[[bbox, (text, confidence)], ...]]
        text_parts = []
        box_count = 0
        for line in results[0]:
            if line and len(line) >= 2:
                # line format: [bbox, (text, confidence)]
                text_info = line[1]
                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                    text, confidence = text_info[0], text_info[1]
                elif isinstance(text_info, str):
                    # Sometimes it's just the text
                    text = text_info
                    confidence = 1.0
                else:
                    continue
                    
                if confidence > 0.3:  # Filter by confidence
                    text_parts.append(text)
                    box_count += 1
        
        if text_parts:
            ocr_text = " ".join(text_parts)
            logger.info(
                f"OCR extracted {len(ocr_text)} characters "
                f"({box_count} text boxes detected)"
            )
            return ocr_text
        
        logger.warning("OCR extracted no text from image")
        return None
        
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return None

def extract_text_from_pdf_or_image(file_path: Path) -> Optional[str]:
    """Extract text from PDF or image file.
    
    For PDFs: Tries direct text extraction first, falls back to OCR on ALL pages.
    For images: Uses OCR directly.
    
    Args:
        file_path: Path to PDF or image file
        
    Returns:
        Extracted text or None if extraction fails
    """
    file_ext = file_path.suffix.lower()
    
    if file_ext == '.pdf':
        logger.info(f"Processing PDF: {file_path.name}")
        
        # Try direct text extraction first
        text = extract_text_from_pdf(file_path)
        
        if text and len(text.strip()) >= 50:
            logger.info("Direct text extraction successful, using extracted text")
            return text
        
        # Fall back to OCR on all pages
        logger.info(
            "Direct text extraction yielded insufficient text, "
            "using OCR on all pages..."
        )
        
        page_count = get_pdf_page_count(file_path)
        if page_count == 0:
            logger.error("Failed to get PDF page count")
            return None
        
        logger.info(f"Processing {page_count} pages with OCR")
        
        # Extract text from all pages
        page_texts = []
        for page_num in range(page_count):
            try:
                # Convert page to image
                image = convert_pdf_page_to_image(file_path, page_num)
                if not image:
                    logger.warning(f"Failed to convert page {page_num + 1} to image")
                    continue
                
                # Extract text from image
                page_text = extract_text_from_image(image)
                if page_text:
                    page_texts.append(f"[Page {page_num + 1}]\n{page_text}")
                    logger.debug(
                        f"Extracted {len(page_text)} characters from page {page_num + 1}"
                    )
            except Exception as e:
                logger.warning(f"Failed to process page {page_num + 1}: {e}")
                continue
        
        if page_texts:
            combined_text = "\n\n".join(page_texts)
            logger.info(
                f"OCR extraction completed: {len(combined_text)} characters "
                f"from {len(page_texts)} pages"
            )
            return combined_text
        
        logger.error("Failed to extract text from any PDF page using OCR")
        return None
        
    elif file_ext in ['.jpg', '.jpeg', '.png']:
        logger.info(f"Processing image: {file_path.name}")
        
        try:
            # Load image
            image = Image.open(file_path)
            
            # Extract text
            text = extract_text_from_image(image)
            return text
            
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            return None
    
    else:
        logger.error(f"Unsupported file type: {file_ext}")
        return None

def extract_passport_text_with_gemini(file_path: Path) -> Optional[str]:
    """Extract text from passport using Gemini's multimodal OCR with File API.
    
    For PDFs: Uploads directly to Gemini using File API (v1beta).
    For images: Uses Gemini OCR directly.
    
    Args:
        file_path: Path to PDF or image file
        
    Returns:
        Extracted text or None if extraction fails
    """
    try:
        # Configure Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        prompt = """Extract ALL text from this passport document. 
Return the text exactly as it appears, preserving line breaks and structure.
Include all visible text including:
- Names (surname, given names, middle names)
- Passport number
- Date of birth
- Place of birth
- Nationality
- Country of issue
- Issue date
- Expiry date
- Sex/Gender
- Any other text visible on the page

Return ONLY the extracted text, no explanations, no formatting, no markdown.
Preserve the original structure and line breaks."""

        file_ext = file_path.suffix.lower()
        
        if file_ext == '.pdf':
            logger.info(f"Processing passport PDF with Gemini File API: {file_path.name}")
            
            # Try direct text extraction first
            text = extract_text_from_pdf(file_path)
            
            if text and len(text.strip()) >= 50:
                logger.info("Direct text extraction successful for passport")
                return text
            
            # Fall back to Gemini File API for OCR
            logger.info("Direct text insufficient, uploading PDF to Gemini...")
            
            # Upload file to Gemini
            gemini_file = genai.upload_file(path=file_path, display_name=file_path.name)
            logger.info(f"File uploaded to Gemini: {gemini_file.uri}")
            
            try:
                # Generate content using the file URI
                response = model.generate_content([prompt, gemini_file])
                
                # Cleanup: Delete the file from Gemini storage
                genai.delete_file(gemini_file.name)
                logger.info("Cleaned up file from Gemini storage")
                
                return response.text.strip() if response.text else None
                
            except Exception as e:
                # Ensure cleanup happens even on error
                try:
                    genai.delete_file(gemini_file.name)
                except:
                    pass
                raise e
            
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            logger.info(f"Processing passport image with Gemini: {file_path.name}")
            image = Image.open(file_path)
            response = model.generate_content([prompt, image])
            return response.text.strip() if response.text else None
            
        else:
            logger.error(f"Unsupported passport file type: {file_ext}")
            return None
            
    except Exception as e:
        logger.error(f"Gemini OCR extraction failed for passport: {e}")
        return None

