"""Form automation using Playwright."""

from typing import Dict, List, Any
from playwright.sync_api import sync_playwright, Page
from config import FORM_URL, HEADLESS_MODE
from utils.logger import logger

# Global store to keep visual browsers open to prevent garbage collection
_visual_sessions: List[Any] = []

def _fill_page(page: Page, fields: Dict[str, str], checkboxes: Dict[str, bool], generate_pdf: bool) -> dict:
    """Core logic to fill the form on a given page."""
    filled_fields = []
    failed_fields = []
    screenshot_path = None
    pdf_path = None

    # Navigate to form
    logger.info(f"Navigating to form: {FORM_URL}")
    page.goto(FORM_URL)
    page.wait_for_load_state("networkidle")
    
    # Fill text fields and select dropdowns
    logger.info(f"Filling {len(fields)} text fields...")
    for field_id, value in fields.items():
        if not value:
            continue
        try:
            # Handle duplicate/virtual IDs
            if field_id == "passport-given-names":
                element = page.locator(f"#{field_id}").nth(0)
            elif field_id == "passport-middle-name":
                element = page.locator("#passport-given-names").nth(1)
            else:
                element = page.locator(f"#{field_id}")

            if element.count() > 0:
                tag_name = element.evaluate("el => el.tagName.toLowerCase()")
                if tag_name == "select":
                    element.select_option(value)
                    logger.debug(f"Selected '{value}' in '{field_id}'")
                else:
                    element.fill(value)
                    logger.debug(f"Filled '{field_id}': {value}")
                filled_fields.append(field_id)
            else:
                failed_fields.append(field_id)
                logger.warning(f"Field '{field_id}' not found")
        except Exception as e:
            failed_fields.append(field_id)
            logger.warning(f"Failed to fill '{field_id}': {e}")
    
    # Handle checkboxes
    logger.info(f"Setting {len(checkboxes)} checkboxes...")
    for field_id, checked in checkboxes.items():
        try:
            element = page.locator(f"#{field_id}")
            if element.count() > 0:
                if checked:
                    element.check()
                else:
                    element.uncheck()
                filled_fields.append(field_id)
            else:
                failed_fields.append(field_id)
        except Exception as e:
            failed_fields.append(field_id)
            logger.warning(f"Failed to set checkbox '{field_id}': {e}")
    
    # Take screenshot
    screenshot_path = "uploads/form_populated.png"
    page.screenshot(path=screenshot_path)
    logger.info(f"Screenshot saved to {screenshot_path}")
    
    # Save as PDF (Only if requested/supported)
    if generate_pdf:
        pdf_path = "uploads/form_filled.pdf"
        page.pdf(path=pdf_path)
        logger.info(f"PDF saved to {pdf_path}")
    
    return {
        "success": len(filled_fields) > 0,
        "total_filled": len(filled_fields),
        "total_failed": len(failed_fields),
        "filled_fields": filled_fields,
        "failed_fields": failed_fields,
        "screenshot_path": screenshot_path,
        "pdf_path": pdf_path,
        "error": None
    }

def populate_form(fields: Dict[str, str], checkboxes: Dict[str, bool]) -> dict:
    """Populate form using Playwright.
    
    If HEADLESS_MODE is True: Runs headless, generates PDF, closes browser.
    If HEADLESS_MODE is False: Runs visible (slow_mo), NO PDF, keeps browser open.
    """
    try:
        logger.info(f"Launching browser (HEADLESS_MODE={HEADLESS_MODE})...")
        
        if HEADLESS_MODE:
            # HEADLESS: Use context manager, auto-close
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                result = _fill_page(page, fields, checkboxes, generate_pdf=True)
                browser.close()
                return result
        else:
            # VISUAL: Manual start, keep open
            p = sync_playwright().start()
            browser = p.chromium.launch(headless=False, slow_mo=50)
            page = browser.new_page()
            
            result = _fill_page(page, fields, checkboxes, generate_pdf=False)
            
            # Keep reference to prevent closure
            _visual_sessions.append((p, browser))
            logger.info("Visual Mode: Browser window left open.")
            
            return result

    except Exception as e:
        error_msg = f"Form population failed: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "total_filled": 0,
            "total_failed": 0,
            "filled_fields": [],
            "failed_fields": [],
            "screenshot_path": None,
            "pdf_path": None,
            "error": error_msg
        }

