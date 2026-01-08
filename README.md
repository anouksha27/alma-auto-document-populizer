# Document Automation System

A web application that automatically extracts data from Passports and G-28 forms to populate online forms.

## Features
- **Smart Extraction**: Uses Google Gemini LLM to accurately extract structured data from PDFs and images.
- **Automated Filling**: Uses Playwright to fill the web form without manual entry.
- **Visual Demo Mode**: Visualize the form filling process in real-time.
- **Drag & Drop UI**: Modern interface for easy file uploads.
- **Instant Feedback**: View screenshots and download filled forms (PDF) immediately.

## Assignment Alignment
- **File Upload**: Supports PDF/JPEG/PNG via Drag & Drop.
- **Data Extraction**: Hybrid approach using OCR and Gemini 1.5 Flash (LLM) for robustness.
- **Form Population**: "Headless" automation by default; "Visual" mode available for demo.
- **Deliverables**: Web Interface (FastAPI), Source Code, and Screen Recording artifacts.

## Setup Instructions

### 1. Installation
```bash
# Clone and enter directory
cd Alma_Project

# Create virtual environment (Optional but Recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_api_key_here
FORM_URL=https://mendrika-alma.github.io/form-submission/
HEADLESS_MODE=False  # Set to False to see the browser type!
```

### 3. Run
```bash
uvicorn app:app --reload
```
Open **http://127.0.0.1:8000/** in your browser.

## Architecture
- **Backend**: FastAPI (Python)
- **AI/LLM**: Google Gemini 3 Flash via `google-generativeai`
- **Automation**: Playwright (Sync API)
- **Frontend**: HTML5/CSS3 (No heavy framework required)
