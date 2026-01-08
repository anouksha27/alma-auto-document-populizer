"""FastAPI main application."""

import os
import asyncio
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from config import validate_config, MAX_FILE_SIZE_MB
from utils.validators import validate_upload
from utils.logger import logger
from utils.ocr_handler import extract_text_from_pdf_or_image, extract_passport_text_with_gemini
from extractors.combined_extraction import extract_data
from utils.data_mapper import map_to_form_fields, get_checkbox_fields
from automation.form_filler import populate_form

# Validate configuration on startup
try:
    validate_config()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(title="Document Automation System")

# Ensure required directories exist
Path("static").mkdir(exist_ok=True)
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

def error_response(message: str, details: str) -> JSONResponse:
    """Create error response.
    
    Args:
        message: Error message
        details: Error details
        
    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": message,
            "error": {
                "message": message,
                "details": details,
                "suggestion": "Check logs/app.log for more details"
            }
        }
    )

def success_response(result: dict) -> JSONResponse:
    """Create success response.
    
    Args:
        result: Form population result
        
    Returns:
        JSON success response
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Documents processed and form populated successfully",
            "details": {
                "fields_filled": result["total_filled"],
                "fields_failed": result["total_failed"],
                "filled_fields": result["filled_fields"],
                "failed_fields": result["failed_fields"],
                "screenshot_url": f"/uploads/{Path(result['screenshot_path']).name}" if result.get("screenshot_path") else None,
                "pdf_url": f"/uploads/{Path(result['pdf_path']).name}" if result.get("pdf_path") else None
            }
        }
    )

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve main UI."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/process")
async def process_documents(
    passport_file: UploadFile = File(...),
    g28_file: UploadFile = File(...)
):
    """Process uploaded documents and populate form.
    
    Args:
        passport_file: Uploaded passport file
        g28_file: Uploaded G-28 file
        
    Returns:
        JSON response with processing results
    """
    passport_path = None
    g28_path = None
    
    try:
        # Step 1: Validate files
        logger.info("Validating uploaded files...")
        validate_upload(passport_file, MAX_FILE_SIZE_MB)
        validate_upload(g28_file, MAX_FILE_SIZE_MB)
        logger.info("Files validated successfully")
        
        # Step 2: Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        passport_path = UPLOADS_DIR / f"passport_{timestamp}_{passport_file.filename}"
        g28_path = UPLOADS_DIR / f"g28_{timestamp}_{g28_file.filename}"
        
        with open(passport_path, "wb") as f:
            content = await passport_file.read()
            f.write(content)
        
        with open(g28_path, "wb") as f:
            content = await g28_file.read()
            f.write(content)
        
        logger.info(f"Files saved: {passport_path.name}, {g28_path.name}")
        
        # Step 3: Extract passport text
        logger.info("Extracting text from passport (using Gemini OCR)...")
        passport_text = extract_passport_text_with_gemini(passport_path)
        
        if not passport_text:
            return error_response(
                "Failed to extract text from passport",
                "Please ensure the passport document is clear and readable"
            )
        
        logger.info(f"Passport text extracted: {len(passport_text)} characters")
        logger.debug(f"Passport text (first 500): {passport_text[:500]}")
        if len(passport_text) > 500:
            logger.debug(f"Passport text (last 500): {passport_text[-500:]}")
        
        # Step 4: Extract G-28 text
        logger.info("Extracting text from G-28...")
        g28_text = extract_text_from_pdf_or_image(g28_path)
        
        if not g28_text:
            return error_response(
                "Failed to extract text from G-28",
                "Please ensure the G-28 form is clear and readable"
            )
        
        
        # Step 5: Extract structured data with LLM
        logger.info("Extracting structured data with Gemini...")
        try:
            passport_data, g28_data = extract_data(passport_text, g28_text)
            logger.info("Data extraction completed successfully")
        except ValueError as e:
            return error_response("Data extraction failed", str(e))
        
        # Step 6: Map to form fields
        logger.info("Mapping data to form fields...")
        fields = map_to_form_fields(passport_data, g28_data)
        checkboxes = get_checkbox_fields(g28_data)
        logger.debug(f"Mapped {len(fields)} fields and {len(checkboxes)} checkboxes")
        logger.debug(f"Fields: {fields}")
        logger.debug(f"Checkboxes: {checkboxes}")
        
        # Step 7: Populate form
        logger.info("Populating form with Playwright...")
        # Use asyncio.to_thread for sync Playwright
        result = await asyncio.to_thread(populate_form, fields, checkboxes)
        
        if result["success"]:
            logger.info(
                f"Form population completed: "
                f"{result['total_filled']} filled, {result['total_failed']} failed"
            )
            return success_response(result)
        else:
            return error_response(
                "Form population failed",
                result.get("error", "Unknown error during form population")
            )
    
    except ValueError as e:
        # Validation or processing errors
        logger.error(f"Processing error: {e}")
        return error_response("Processing failed", str(e))
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return error_response("Unexpected error", str(e))
    
    finally:
        # Cleanup files
        try:
            if passport_path and passport_path.exists():
                passport_path.unlink()
                logger.debug(f"Cleaned up: {passport_path.name}")
            if g28_path and g28_path.exists():
                g28_path.unlink()
                logger.debug(f"Cleaned up: {g28_path.name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup files: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

