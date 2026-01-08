"""Combined LLM extraction for passport and G-28 documents."""

import json
from typing import Tuple
from datetime import datetime
import google.generativeai as genai

from models.passport_data import PassportData
from models.g28_data import G28Data, AttorneyInfo, EligibilityInfo, ClientInfo
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME
from utils.logger import logger

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def extract_data(passport_text: str, g28_text: str) -> Tuple[PassportData, G28Data]:
    """Extract both passport and G-28 data using combined LLM call.
    
    This provides better accuracy through cross-validation and full context.
    
    Args:
        passport_text: OCR text from passport (may span multiple pages)
        g28_text: OCR text from G-28 form
        
    Returns:
        Tuple of (PassportData, G28Data) objects
        
    Raises:
        ValueError: If extraction fails with detailed error message
    """
    try:
        # Create comprehensive prompt for Gemini
        prompt = f"""Extract structured data from passport and G-28 form text.

IMPORTANT: Cross-validate data - the client name in G-28 should match 
the passport holder name. If there are discrepancies, give the passport data and note them in validation_notes, 

Passport Text:
{passport_text}

G-28 Form Text:
{g28_text}

Return ONLY valid JSON with no additional text, comments, or markdown formatting.

The JSON must have this exact structure:
{{
  "passport": {{
    "surname": "string or null",
    "given_names": "string or null",
    "middle_names": "string or null",
    "passport_number": "string or null",
    "country_of_issue": "string or null",
    "nationality": "string or null",
    "date_of_birth": "YYYY-MM-DD or null",
    "place_of_birth": "string or null",
    "sex": "M/F/X or null",
    "issue_date": "YYYY-MM-DD or null",
    "expiry_date": "YYYY-MM-DD or null"
  }},
  "g28": {{
    "attorney": {{
      "first_name": "string or null",
      "middle_name": "string or null",
      "last_name": "string or null",
      "street": "string or null",
      "city": "string or null",
      "state": "string or null (use state abbreviation if available)",
      "zip": "string or null",
      "country": "string or null",
      "phone": "string or null",
      "email": "string or null",
      "fax": "string or null",
      "online_account": "string or null"
    }},
    "eligibility": {{
      "licensing_authority": "string or null",
      "bar_number": "string or null",
      "law_firm": "string or null",
      "is_not_subject_to_orders": true or false or null
    }},
    "client": {{
      "first_name": "string or null",
      "middle_name": "string or null",
      "last_name": "string or null",
      "street": "string or null",
      "city": "string or null",
      "state": "string or null",
      "zip": "string or null",
      "country": "string or null",
      "phone": "string or null",
      "email": "string or null",
      "a_number": "string or null"
    }}
  }},
  "validation_notes": "string or null - any discrepancies or validation issues"
}}"""

        # Log the full prompt
        # Log the full prompt
        
        # Initialize model
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        # Generate content
        logger.info("Sending request to Gemini API...")
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text.strip()
        logger.debug(f"Gemini raw response:\n{response_text}")
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse JSON from Gemini response: {json_err}")
            logger.error(f"Response text (first 500 chars): {response_text[:500]}")
            raise ValueError(
                f"Gemini API returned invalid JSON format. "
                f"JSON parsing error: {str(json_err)}"
            )
        
        # Create PassportData object
        passport_dict = data.get("passport", {})
        
        # Convert date strings to date objects
        for date_field in ['date_of_birth', 'issue_date', 'expiry_date']:
            if passport_dict.get(date_field) and isinstance(passport_dict[date_field], str):
                try:
                    passport_dict[date_field] = datetime.strptime(
                        passport_dict[date_field],
                        '%Y-%m-%d'
                    ).date()
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse {date_field}: {e}")
                    passport_dict[date_field] = None
        
        passport_data = PassportData(**passport_dict)
        logger.info(f"Passport data extracted: {passport_data.model_dump_json()}")
        
        # Create G28Data object
        g28_dict = data.get("g28", {})
        attorney = AttorneyInfo(**g28_dict.get("attorney", {})) if g28_dict.get("attorney") else None
        eligibility = EligibilityInfo(**g28_dict.get("eligibility", {})) if g28_dict.get("eligibility") else None
        client = ClientInfo(**g28_dict.get("client", {})) if g28_dict.get("client") else None
        
        g28_data = G28Data(
            attorney=attorney,
            eligibility=eligibility,
            client=client
        )
        logger.info(f"G-28 data extracted: {g28_data.model_dump_json()}")
        
        # Log validation notes if present
        validation_notes = data.get("validation_notes")
        if validation_notes:
            logger.info(f"LLM validation notes: {validation_notes}")
        
        logger.info("Successfully extracted both passport and G-28 data using LLM")
        return passport_data, g28_data
        
    except ValueError:
        # Re-raise ValueError (already has detailed error message)
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"LLM extraction failed: {error_msg}")
        
        # Provide detailed error information
        if "API key" in error_msg or "authentication" in error_msg.lower():
            raise ValueError(
                "Gemini API authentication failed. "
                "Please verify your GEMINI_API_KEY in .env file."
            )
        elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            raise ValueError(
                "Gemini API quota exceeded or rate limit reached. "
                "Please try again later."
            )
        elif "model" in error_msg.lower():
            raise ValueError(
                f"Invalid Gemini model name: {GEMINI_MODEL_NAME}. "
                "Please check GEMINI_MODEL_NAME in .env file."
            )
        else:
            raise ValueError(
                f"LLM extraction error: {error_msg}. "
                "Please check your API key and model configuration."
            )

