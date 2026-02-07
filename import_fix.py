# Streamlit Cloud Deployment Fix
# Add this to your app.py to handle import errors on Streamlit Cloud

import sys
import os
from pathlib import Path

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Try to import modules with fallback handling
def safe_import(module_name, fallback=None):
    """Safely import a module with fallback"""
    try:
        return __import__(module_name)
    except ImportError as e:
        print(f"Warning: Could not import {module_name}: {e}")
        return fallback

# Import required modules with fallback
pdfplumber = safe_import('pdfplumber')
cryptography = safe_import('cryptography')
google_generativeai = safe_import('google.generativeai')

# Check if all required modules are available
required_modules = {
    'pdfplumber': pdfplumber,
    'cryptography': cryptography,
    'streamlit': safe_import('streamlit')
}

missing_modules = [name for name, module in required_modules.items() if module is None]

if missing_modules:
    print(f"Missing modules: {missing_modules}")
    print("Please ensure all dependencies are installed in requirements.txt")
    sys.exit(1)

print("✅ All required modules imported successfully")