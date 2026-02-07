# Fix for missing dependencies on Streamlit Cloud
# Run this in the Streamlit Cloud environment

import subprocess
import sys

# Install missing packages
packages = [
    'pdfplumber',
    'cryptography',
    'google-generativeai',
    'requests',
    'Pillow'
]

for package in packages:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Installed {package}")
    except Exception as e:
        print(f"❌ Failed to install {package}: {e}")

print("Package installation complete!")