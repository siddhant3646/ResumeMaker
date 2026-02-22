"""
Robust JSON Extraction from AI Responses
Handles malformed, partial, and truncated JSON
"""

import json
import re
from typing import Dict, Any, Optional, List, Union
from jsonschema import validate, ValidationError
import logging

logger = logging.getLogger(__name__)


# Schema for resume validation
RESUME_SCHEMA = {
    "type": "object",
    "required": ["basics", "experience"],
    "properties": {
        "basics": {
            "type": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "email": {"type": "string", "format": "email"}
            }
        },
        "experience": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["company", "role", "bullets"],
                "properties": {
                    "company": {"type": "string"},
                    "role": {"type": "string"},
                    "bullets": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "education": {
            "type": "array",
            "items": {"type": "object"}
        },
        "skills": {"type": "object"},
        "projects": {"type": "array"},
        "achievements": {"type": "array"}
    }
}


class JSONExtractionError(Exception):
    """Exception raised when JSON extraction fails"""
    pass


class JSONExtractor:
    """
    Robust JSON extraction with multiple fallback strategies
    """
    
    @staticmethod
    def extract(
        text: str,
        schema: Optional[Dict] = None,
        required_fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text using multiple strategies
        
        Args:
            text: Text containing JSON
            schema: Optional JSON schema for validation
            required_fields: Optional list of required top-level fields
            
        Returns:
            Extracted JSON dict or None if extraction fails
        """
        if not text or not isinstance(text, str):
            return None
        
        strategies = [
            ("code_block", JSONExtractor._extract_code_block),
            ("json_object", JSONExtractor._extract_json_object),
            ("partial_json", JSONExtractor._extract_partial_json),
            ("repair_json", JSONExtractor._repair_json),
        ]
        
        last_error = None
        
        for strategy_name, strategy in strategies:
            try:
                result = strategy(text)
                
                if result is None:
                    continue
                
                # Validate required fields
                if required_fields:
                    missing = [f for f in required_fields if f not in result]
                    if missing:
                        logger.warning(f"Strategy {strategy_name} missing fields: {missing}")
                        continue
                
                # Validate against schema if provided
                if schema:
                    try:
                        validate(instance=result, schema=schema)
                    except ValidationError as e:
                        logger.warning(f"Strategy {strategy_name} failed schema validation: {e.message}")
                        continue
                
                logger.debug(f"JSON extracted successfully using {strategy_name}")
                return result
                
            except Exception as e:
                last_error = e
                continue
        
        logger.error(f"All JSON extraction strategies failed. Last error: {last_error}")
        return None
    
    @staticmethod
    def _extract_code_block(text: str) -> Optional[Dict]:
        """Extract JSON from markdown code blocks"""
        patterns = [
            (r'```json\s*([\s\S]*?)\s*```', re.DOTALL),
            (r'```\s*([\s\S]*?)\s*```', re.DOTALL),
            (r'<json>([\s\S]*?)</json>', re.DOTALL | re.IGNORECASE),
            (r'\{[\s\S]*\}', re.DOTALL),  # Fallback to raw JSON
        ]
        
        for pattern, flags in patterns:
            match = re.search(pattern, text, flags)
            if match:
                json_str = match.group(1) if match.groups() else match.group(0)
                # Clean up the string
                json_str = json_str.strip()
                if json_str:
                    return json.loads(json_str)
        
        return None
    
    @staticmethod
    def _extract_json_object(text: str) -> Optional[Dict]:
        """Extract the outermost JSON object from text"""
        # Find the first opening brace
        start = text.find('{')
        if start == -1:
            return None
        
        # Track braces to find matching closing brace
        depth = 0
        end = start
        
        for i, char in enumerate(text[start:], start=start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        
        if depth != 0:
            # Unmatched braces
            return None
        
        json_str = text[start:end]
        return json.loads(json_str)
    
    @staticmethod
    def _extract_partial_json(text: str) -> Optional[Dict]:
        """Try to extract partial/truncated JSON by finding valid subsets"""
        # Try progressively smaller chunks from the end
        json_str = text.strip()
        
        # Find the last complete object
        brace_count = 0
        last_valid_end = 0
        
        for i, char in enumerate(json_str):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    last_valid_end = i + 1
        
        if last_valid_end > 0:
            try:
                return json.loads(json_str[:last_valid_end])
            except json.JSONDecodeError:
                pass
        
        # Try finding array if object fails
        start = json_str.find('[')
        if start != -1:
            depth = 0
            for i, char in enumerate(json_str[start:], start=start):
                if char == '[':
                    depth += 1
                elif char == ']':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(json_str[start:i+1])
                        except json.JSONDecodeError:
                            pass
        
        return None
    
    @staticmethod
    def _repair_json(text: str) -> Optional[Dict]:
        """Attempt to repair broken JSON"""
        json_str = text.strip()
        
        # Remove markdown formatting
        json_str = re.sub(r'^```\w*\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)
        
        # Ensure starts with { or [
        if not json_str.startswith('{') and not json_str.startswith('['):
            obj_start = json_str.find('{')
            arr_start = json_str.find('[')
            
            if obj_start != -1 and (arr_start == -1 or obj_start < arr_start):
                json_str = json_str[obj_start:]
            elif arr_start != -1:
                json_str = json_str[arr_start:]
        
        # Balance braces
        open_braces = json_str.count('{') - json_str.count('}')
        if open_braces > 0:
            json_str += '}' * open_braces
        elif open_braces < 0:
            json_str = '{' * abs(open_braces) + json_str
        
        open_brackets = json_str.count('[') - json_str.count(']')
        if open_brackets > 0:
            json_str += ']' * open_brackets
        elif open_brackets < 0:
            json_str = '[' * abs(open_brackets) + json_str
        
        # Remove trailing commas
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        
        # Fix unquoted keys (simple cases only)
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        # Fix single quotes to double quotes
        json_str = json_str.replace("'", '"')
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def validate_resume_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate resume data structure
        
        Returns:
            (is_valid, list of issues)
        """
        issues = []
        
        if not isinstance(data, dict):
            return False, ["Data is not a dictionary"]
        
        # Check basics
        basics = data.get("basics")
        if not basics:
            issues.append("Missing 'basics' section")
        elif not isinstance(basics, dict):
            issues.append("'basics' must be an object")
        else:
            if not basics.get("name"):
                issues.append("Missing 'name' in basics")
            if not basics.get("email"):
                issues.append("Missing 'email' in basics")
        
        # Check experience
        experience = data.get("experience")
        if not experience:
            issues.append("Missing 'experience' section")
        elif not isinstance(experience, list):
            issues.append("'experience' must be an array")
        elif len(experience) == 0:
            issues.append("'experience' array is empty")
        else:
            for i, exp in enumerate(experience):
                if not isinstance(exp, dict):
                    issues.append(f"Experience[{i}] is not an object")
                    continue
                
                if not exp.get("company"):
                    issues.append(f"Experience[{i}] missing 'company'")
                if not exp.get("role"):
                    issues.append(f"Experience[{i}] missing 'role'")
                
                bullets = exp.get("bullets")
                if not bullets:
                    issues.append(f"Experience[{i}] missing 'bullets'")
                elif not isinstance(bullets, list):
                    issues.append(f"Experience[{i}] 'bullets' must be an array")
                elif len(bullets) == 0:
                    issues.append(f"Experience[{i}] 'bullets' array is empty")
        
        return len(issues) == 0, issues


def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    Safely load JSON with fallback
    
    Args:
        text: JSON string
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default
