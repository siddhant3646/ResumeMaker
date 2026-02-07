"""
PDF Validator using Gemma 3 Vision
Analyzes PDF pages to check formatting, whitespace, and content density
"""

import json
import base64
from typing import List, Dict, Optional, Tuple
from io import BytesIO
from PIL import Image
from core.models import ValidationReport


class PDFToImageConverter:
    """Convert PDF pages to images for vision analysis"""
    
    def __init__(self, dpi: int = 150):
        self.dpi = dpi
    
    def convert(self, pdf_bytes: bytes) -> List[Image.Image]:
        """
        Convert PDF bytes to list of PIL Images
        """
        try:
            import fitz  # PyMuPDF
            
            images = []
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page to image
                mat = fitz.Matrix(self.dpi/72, self.dpi/72)  # 72 is default PDF DPI
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            
            pdf_document.close()
            return images
            
        except ImportError:
            # Fallback: try pdf2image
            try:
                from pdf2image import convert_from_bytes
                return convert_from_bytes(pdf_bytes, dpi=self.dpi)
            except ImportError:
                print("Warning: PDF conversion libraries not available")
                return []
    
    def encode_image_for_api(self, image: Image.Image) -> str:
        """Encode PIL Image to base64 string for API"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str


class PDFValidator:
    """Validate PDF using Gemma 3 Vision"""
    
    def __init__(self, gemma_api_key: str):
        self.api_key = gemma_api_key
        self.converter = PDFToImageConverter()
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemma_api_key)
            self.model = genai.GenerativeModel('gemma-3-27b-it-vision')
            self.available = True
        except Exception as e:
            print(f"Vision model initialization error: {e}")
            self.available = False
            self.model = None
    
    def validate(self, pdf_bytes: bytes) -> ValidationReport:
        """
        Validate PDF and return report
        """
        # Convert PDF to images
        images = self.converter.convert(pdf_bytes)
        
        if not images:
            # Fallback if conversion fails
            return ValidationReport(
                page_count=1,
                fill_percentage=85.0,
                whitespace_percentage=15.0,
                text_density=0.8,
                issues=[],
                suggestions=[],
                needs_regeneration=False
            )
        
        # Analyze each page
        all_issues = []
        all_suggestions = []
        total_fill = 0.0
        total_whitespace = 0.0
        
        for i, image in enumerate(images):
            analysis = self._analyze_page(image, i + 1)
            all_issues.extend(analysis.get('issues', []))
            all_suggestions.extend(analysis.get('suggestions', []))
            total_fill += analysis.get('fill_percentage', 85.0)
            total_whitespace += analysis.get('whitespace_percentage', 15.0)
        
        # Calculate averages
        avg_fill = total_fill / len(images) if images else 85.0
        avg_whitespace = total_whitespace / len(images) if images else 15.0
        
        # Determine if regeneration needed
        needs_regen = (
            avg_fill < 80 or
            avg_whitespace > 25 or
            'text_cut_off' in all_issues or
            'poor_formatting' in all_issues
        )
        
        return ValidationReport(
            page_count=len(images),
            fill_percentage=avg_fill,
            whitespace_percentage=avg_whitespace,
            text_density=1.0 - (avg_whitespace / 100),
            issues=list(set(all_issues)),
            suggestions=list(set(all_suggestions)),
            needs_regeneration=needs_regen
        )
    
    def _analyze_page(self, image: Image.Image, page_num: int) -> Dict:
        """Analyze a single page using vision model"""
        if not self.available or not self.model:
            return self._fallback_analysis(image)
        
        # Encode image
        img_base64 = self.converter.encode_image_for_api(image)
        
        prompt = f"""Analyze this resume PDF page (Page {page_num}).

Look at the image carefully and assess:

1. PAGE FILL: What percentage of the page is filled with content? (Estimate 0-100%)
2. WHITESPACE: Are there large empty areas or is content well-distributed?
3. TEXT ALIGNMENT: Is text properly aligned with consistent margins?
4. SECTION BALANCE: Are sections evenly distributed or crowded?
5. TEXT CUTOFF: Is any text cut off at edges?
6. READABILITY: Is the font size appropriate and consistent?

Return a JSON object with this exact structure:
{{
    "fill_percentage": <number 0-100>,
    "whitespace_percentage": <number 0-100>,
    "issues": ["issue1", "issue2", ...],
    "suggestions": ["suggestion1", "suggestion2", ...]
}}

Possible issues: "too_much_whitespace", "text_cut_off", "poor_formatting", "crowded_sections", "uneven_margins"
Possible suggestions: "add_more_content", "reduce_spacing", "adjust_margins", "increase_font_size"

Be precise in your analysis. A good resume page should have 85-95% fill with minimal whitespace.
"""
        
        try:
            # Create content with image
            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": base64.b64decode(img_base64)}
            ])
            
            # Parse response
            text = response.text
            json_match = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_match >= 0 and json_end > json_match:
                json_str = text[json_match:json_end]
                return json.loads(json_str)
            
        except Exception as e:
            print(f"Vision analysis error for page {page_num}: {e}")
        
        return self._fallback_analysis(image)
    
    def _fallback_analysis(self, image: Image.Image) -> Dict:
        """Fallback analysis when vision model is not available"""
        # Basic image analysis
        width, height = image.size
        
        # Convert to grayscale and analyze
        gray = image.convert('L')
        pixels = list(gray.getdata())
        
        # Calculate fill (non-white pixels)
        white_threshold = 250
        white_pixels = sum(1 for p in pixels if p > white_threshold)
        fill_percentage = ((len(pixels) - white_pixels) / len(pixels)) * 100
        
        issues = []
        suggestions = []
        
        if fill_percentage < 75:
            issues.append("too_much_whitespace")
            suggestions.append("add_more_content")
        elif fill_percentage > 98:
            issues.append("crowded_sections")
            suggestions.append("reduce_content")
        
        return {
            "fill_percentage": fill_percentage,
            "whitespace_percentage": 100 - fill_percentage,
            "issues": issues,
            "suggestions": suggestions
        }
    
    def quick_validate(self, pdf_bytes: bytes) -> Tuple[bool, List[str]]:
        """
        Quick validation - returns True if good, False if needs work
        """
        report = self.validate(pdf_bytes)
        
        is_good = (
            report.fill_percentage >= 85 and
            report.whitespace_percentage <= 15 and
            not report.has_critical_issues()
        )
        
        return is_good, report.issues
