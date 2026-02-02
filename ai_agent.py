"""
AI Agent Module

Uses Google GenAI SDK to tailor resumes based on job descriptions.
Includes Pydantic models for structured output.
"""

import json
import math
import re
from datetime import datetime
from typing import List, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ============================================================================
# Pydantic Models - Mirrors master_resume.json schema exactly
# ============================================================================

class Basics(BaseModel):
    """Basic contact information"""
    name: str
    email: str
    phone: str
    location: str
    links: List[str] = Field(default_factory=list)


class Education(BaseModel):
    """Education entry"""
    institution: str
    area: str
    studyType: str
    startDate: str
    endDate: str
    location: str


class Experience(BaseModel):
    """Work experience entry"""
    company: str
    location: str
    role: str
    startDate: str
    endDate: str
    bullets: List[str] = Field(default_factory=list)


class Project(BaseModel):
    """Project entry"""
    name: str
    techStack: str
    description: str


class Skills(BaseModel):
    """Categorized skills"""
    languages_frameworks: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)


class TailoredResume(BaseModel):
    """Complete tailored resume structure"""
    basics: Basics
    summary: str
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    projects: List[Project] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


# ============================================================================
# Tenure Calculation Function
# ============================================================================

def calculate_total_experience(experience_list: list) -> str:
    """
    Calculate total years of experience from a list of experience entries.
    
    Args:
        experience_list: List of experience dicts with startDate and endDate keys
        
    Returns:
        String like "4+ years" or "2.5 years" representing total experience
    """
    total_months = 0
    
    # Month mapping for parsing dates
    month_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    def parse_date(date_str: str) -> datetime:
        """Parse date strings like 'Jun 2022' or 'May2022' into datetime."""
        date_str = date_str.strip().lower()
        
        # Handle "present" or current
        if date_str in ['present', 'current', 'now', 'today']:
            return datetime.now()
        
        # Try different patterns
        patterns = [
            r'([a-z]+)[\s/-]*(\d{4})',  # "Jun 2022" or "Jun2022" or "Jun-2022"
            r'(\d{1,2})[\s/-]*(\d{4})',  # "6/2022" or "06 2022"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                month_part, year_part = match.groups()
                year = int(year_part)
                
                # Try to parse month
                if month_part.isdigit():
                    month = int(month_part)
                else:
                    # Try to find month from name
                    month_abbr = month_part[:3]
                    month = month_map.get(month_abbr, 1)
                
                return datetime(year, month, 15)  # Use 15th as middle of month
        
        # Fallback: try to extract just year
        year_match = re.search(r'\d{4}', date_str)
        if year_match:
            year = int(year_match.group())
            return datetime(year, 6, 15)  # Use mid-year
        
        return datetime.now()
    
    for exp in experience_list:
        start_date = parse_date(exp.get('startDate', ''))
        end_date = parse_date(exp.get('endDate', 'Present'))
        
        # Calculate months difference
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if months > 0:
            total_months += months
    
    # Convert to years
    years = total_months / 12
    
    # Format output
    if years < 1:
        return f"{int(total_months)} months"
    elif years < 2:
        return f"{years:.1f} years"
    else:
        # Round UP to next whole year for cleaner display (e.g., 3.6 -> 4+)
        rounded_years = math.ceil(years)
        return f"{int(rounded_years)}+ years"


def force_experience_in_summary(resume: TailoredResume, correct_experience: str) -> TailoredResume:
    """
    Post-process the AI-generated summary to ensure it uses the correct total experience.
    
    Args:
        resume: The TailoredResume object with AI-generated content
        correct_experience: The correctly calculated experience string (e.g., "4+ years")
        
    Returns:
        TailoredResume with corrected experience value in summary
    """
    if not resume.summary:
        return resume
    
    # Pattern to match various YOE formats: "2+ years", "2.5 years", "3 years", "2-3 years", etc.
    yoe_pattern = r'\b\d+(?:\.\d+)?\+?\s*(?:-\s*\d+\+?)?\s*years?\s+of\s+experience\b'
    
    # Replace any YOE pattern with the correct experience
    resume.summary = re.sub(
        yoe_pattern,
        f"{correct_experience} of experience",
        resume.summary,
        flags=re.IGNORECASE
    )
    
    return resume


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT_TEMPLATE = """System Role: You are an expert Resume Strategist and ATS Optimization Engine. Your goal is to rewrite a BASE_RESUME to achieve a 100% match score against a specific JOB_DESCRIPTION, while maintaining strict truthfulness and professional credibility.

---

## Step 1: Keyword Extraction & Mapping

### 1.1 Extract Critical Keywords from JOB_DESCRIPTION
Analyze the JD and extract:
- **Hard Skills**: Programming languages, frameworks, tools (e.g., Java, Golang, Spring Boot, RESTful Web Services, MVC, SOA)
- **Domain Keywords**: Industry-specific terms (e.g., Payments, Settlement, FinTech, Travel, E-commerce)
- **Soft Skills**: Culture/emphasis terms (e.g., Agile, Collaboration, Partnership, Cross-functional)
- **Required Experience**: Years mentioned, seniority level expected

### 1.2 Scan & Map BASE_RESUME Keywords
Compare resume skills to JD keywords. If a skill is present but phrased differently, RENAME to match JD exactly:
- "Jira" / "Scrum" → "Agile Methodology"  
- "Rest API" → "RESTful Web Services"
- "Spring Boot microservices" → "MVC" / "Microservices Architecture"
- "Cloud/AWS" → "Cloud Computing"

### 1.3 Gap Filling (Inference ONLY - NO FABRICATION)
If a JD keyword is MISSING but HEAVILY IMPLIED by existing experience, inject naturally:
- Has "Jira/Confluence" → Explicitly add "Agile Methodology"
- Has "Spring Boot + microservices" → Add "MVC", "SOA"
- Has "Java backend + distributed systems" → Add "RESTful Web Services"

**⚠️ CRITICAL:** DO NOT fabricate skills the user clearly does not possess. Only add keywords that are logically implied by existing experience.

---

## Step 2: Seniority & Credibility Calibration (CRITICAL)

### 2.1 Calculate Total Years of Experience
Total Experience: {total_experience}

### 2.2 The "Architect" Guardrail
If Total YOE < 5 years, hiring managers with 25+ YOE get skeptical of junior developers using architect-level verbs. DOWNGRADE these verbs to maintain credibility:

| Overstated Verb | Calibrated Replacement |
|----------------|----------------------|
| "Architected" | "Co-designed" / "Engineered" / "Developed" |
| "Spearheaded" | "Led implementation of" / "Drove" |
| "Orchestrated" | "Coordinated" / "Collaborated on" |
| "Managed" | "Owned delivery of" / "Handled" |
| "Directed" | "Contributed to" / "Supported" |
| "Pioneered" | "Implemented" / "Introduced" |

**WHY THIS MATTERS:** Using "Architected" with 3 years experience triggers skepticism. Using "Co-designed" maintains credibility while showing ownership.

---

## Step 3: Domain & Culture Alignment

### 3.1 Domain Mapping
Rewrite the Professional Summary to explicitly mention the JD's industry domain:
- Fiserv/Payments experience → "Payments Domain" / "FinTech" / "Financial Services"
- Travel/E-commerce JD (MakeMyTrip) → "Travel Technology" / "E-commerce Platform"
- Healthcare JD → "Healthcare Technology"

### 3.2 Culture & Soft Skills Alignment
If JD emphasizes specific culture elements, align experience bullets:
- "Agile methodology" → Emphasize sprint participation, stand-ups, iteration planning
- "Cross-functional" / "Partnership" → "Collaborated with cross-functional teams..."
- "Full SDLC" → Mention design, development, testing, deployment phases
- "Decency" / "Team player" → Highlight mentorship, knowledge sharing

**EXAMPLE TRANSFORMATION:**
- BEFORE: "Built microservices for payment processing"
- AFTER: "Collaborated with cross-functional teams to build payment processing microservices, ensuring seamless integration with settlement systems"

---

## Step 4: Output Generation

### 4.1 Professional Summary (EXACTLY 3 Sentences)
Sentence 1: "Software Engineer with {total_experience} of experience specializing in [TOP 3 JD KEYWORDS]."
Sentence 2: Domain-specific achievement with quantified metrics matching JD priorities.
Sentence 3: Differentiator that matches JD values (security, scale, collaboration).

**MANDATORY - THIS IS CRITICAL:**
- Use "{total_experience}" EXACTLY as provided - do NOT calculate your own value
- The experience value is ALREADY calculated from all work history dates in the master resume
- DO NOT say "2+ years" or "3+ years" - use ONLY: "{total_experience}"
- Example: If "{total_experience}" is "4+ years", you MUST write: "Software Engineer with 4+ years of experience..."
- NEVER use a different experience duration than what is provided above

### 4.2 Experience Bullets (MAXIMUM 6 per role)
**STRICT LIMIT: 6 bullets maximum per role.**

Format: [Calibrated Verb] + [Specific Achievement] + [Technology] + [Quantified Metric]

**PRIORITY ORDER:**
1. Bullets mentioning JD-required technologies (exact matches first)
2. Bullets with the most impressive quantified results
3. Security-related achievements (if JD mentions security)
4. Scale/performance achievements
5. Collaboration/cross-functional work (if JD emphasizes)

**METRIC DIVERSITY (NO percentage-only):**
- Time-based: "Reduced latency from 400ms to 280ms"
- Scale/Volume: "Processing 2M+ daily transactions"
- Counts: "Built 15 microservices", "Mentored 5 developers"
- Reliability: "Achieved 99.97% uptime"

### 4.3 Skills Section (REORDERED BY JD PRIORITY)
Return as OBJECT with JD-required skills FIRST:
```json
"skills": {
  "languages_frameworks": [JD-required languages first, then others],
  "tools": [JD-required tools first, then others]
}
```

**EXAMPLE:** If JD emphasizes "Java, Golang, RESTful Web Services":
```json
"skills": {
  "languages_frameworks": ["Java", "Golang", "RESTful Web Services", "Spring Boot", "ReactJS"],
  "tools": ["AWS", "Docker", "Kubernetes", "GitLab CI/CD"]
}
```

### 4.4 Projects (MAXIMUM 1 if space permits)
**OMIT projects if content exceeds 1 page.**
- Focus on ENGINEERING challenges (deployment, optimization, architecture)
- NOT ML accuracy metrics

### 4.5 Achievements (MAXIMUM 2 items)
- Security achievements FIRST (if applicable)
- Awards/recognition second
- One line each

---

## 1-PAGE CONSTRAINT (CRITICAL - ENFORCED)
**The resume MUST fit on exactly 1 page.**

**HARD LIMITS:**
- Professional Summary: 3 sentences MAX
- Experience: 6 bullets MAX per role
- Projects: 1 project MAX (omit if space tight)
- Achievements: 2 items MAX
- Education: List degrees only, no bullets

**If you generate excess content, the system will DELETE sections automatically.**

---

## DIVERSE METRICS RULE (AVOID PERCENTAGE-ONLY)

**❌ NEVER DO THIS:**
- "Improved performance by 40%"
- "Reduced errors by 25%"

**✅ USE THESE INSTEAD:**
- Time: "Reduced P99 latency from 400ms to 280ms"
- Scale: "Serving 50K concurrent users"
- Count: "Resolved 80+ user stories and 35 defects"
- Reliability: "Achieved 99.97% uptime"

**METRIC MIX RULE:** For every 3 bullets, use at least:
- 1 absolute time metric
- 1 scale/count metric
- 1 mixed metric (percentage WITH absolute context)

---

## Output Format:
Return ONLY a valid JSON object matching this exact schema:
```json
{
  "basics": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "links": []
  },
  "summary": "",
  "education": [
    {
      "institution": "",
      "area": "",
      "studyType": "",
      "startDate": "",
      "endDate": "",
      "location": ""
    }
  ],
  "experience": [
    {
      "company": "",
      "location": "",
      "role": "",
      "startDate": "",
      "endDate": "",
      "bullets": []
    }
  ],
  "skills": {
    "languages_frameworks": [],
    "tools": []
  },
  "projects": [
    {
      "name": "",
      "techStack": "",
      "description": ""
    }
  ],
  "achievements": []
}
```

**CRITICAL:** Return ONLY the JSON object. No markdown code blocks, no explanations, no additional text."""

# System prompt will be formatted with total_experience at runtime
SYSTEM_PROMPT = SYSTEM_PROMPT_TEMPLATE  # Default, will be formatted in tailor_resume()"


# ============================================================================
# Main Function
# ============================================================================

def tailor_resume(
    master_resume: dict,
    job_description: str,
    api_key: str,
    model: str = "gemini-2.0-flash"
) -> TailoredResume:
    """
    Tailor a resume for a specific job description using Google GenAI.
    
    Args:
        master_resume: The master resume data (dict matching schema)
        job_description: The job description text
        api_key: Google API key
        model: Model to use (default: gemini-2.0-flash)
        
    Returns:
        TailoredResume object with tailored content
        
    Raises:
        Exception: If API call fails or response parsing fails
    """
    # Initialize the client
    client = genai.Client(api_key=api_key)
    
    # Calculate total experience from master resume
    experience_list = master_resume.get('experience', [])
    total_experience = calculate_total_experience(experience_list)
    
    # Format the system prompt with total_experience for the 4-step methodology
    formatted_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(total_experience=total_experience)
    
    # Check if model supports system instructions (Gemini does, Gemma doesn't)
    supports_system_instruction = 'gemini' in model.lower()
    
    # Build the user prompt - include instructions for models that don't support system_instruction
    if supports_system_instruction:
        user_prompt = f"""## Master Resume (JSON):
```json
{json.dumps(master_resume, indent=2)}
```

## Job Description:
{job_description}

## Candidate's Total Experience:
{total_experience}

**CRITICAL - MANDATORY:** You MUST use "{total_experience}" as the EXACT experience duration in the Professional Summary. Do NOT round down or use generic values like "2+" or "3+" years. Use the exact calculated value provided above.

**Example:** If total experience is "3.8 years", write: "Software Engineer with 3.8 years of experience specializing in..."

---

Please tailor the resume for this job description following the 4-step methodology in your instructions. Return ONLY a valid JSON object matching the TailoredResume schema."""
    else:
        # Embed instructions in user prompt for Gemma and other models
        user_prompt = f"""{formatted_system_prompt}

---

## Master Resume (JSON):
```json
{json.dumps(master_resume, indent=2)}
```

## Job Description:
{job_description}

## Candidate's Total Experience:
{total_experience}

**CRITICAL - MANDATORY:** You MUST use "{total_experience}" as the EXACT experience duration in the Professional Summary first sentence. Do NOT round down or use generic values.

---

Please tailor the resume for this job description following the 4-step methodology above. Return ONLY a valid JSON object with these exact keys:
- basics (object with: name, email, phone, location, links)
- summary (string)
- education (array of objects with: institution, area, studyType, startDate, endDate, location)
- experience (array of objects with: company, location, role, startDate, endDate, bullets)
- skills (object with: languages_frameworks, tools - both arrays of strings)
- projects (array of objects with: name, techStack, description)
- achievements (array of strings)

Return ONLY the JSON, no markdown code blocks, no explanations."""

    # Make the API call - different config for different model types
    if supports_system_instruction:
        config = types.GenerateContentConfig(
            system_instruction=formatted_system_prompt,
            response_mime_type="application/json",
            response_schema=TailoredResume,
            temperature=0.7,
            max_output_tokens=8192,
        )
    else:
        # Gemma models don't support system_instruction or response_schema
        config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=8192,
        )
    
    response = client.models.generate_content(
        model=model,
        contents=[user_prompt],
        config=config
    )
    
    # Parse the response
    if not response.text:
        raise ValueError("Empty response from API")
    
    # Clean up response text (Gemma may include markdown code blocks)
    response_text = response.text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]  # Remove ```json
    elif response_text.startswith("```"):
        response_text = response_text[3:]  # Remove ```
    if response_text.endswith("```"):
        response_text = response_text[:-3]  # Remove trailing ```
    response_text = response_text.strip()
    
    # Parse the JSON response into our Pydantic model
    try:
        tailored_data = json.loads(response_text)
        tailored_resume = TailoredResume(**tailored_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse API response as JSON: {e}\n\nResponse was: {response_text[:500]}")
    except Exception as e:
        raise ValueError(f"Failed to validate response schema: {e}")
    
    # Post-process: Force correct experience in summary
    tailored_resume = force_experience_in_summary(tailored_resume, total_experience)
    
    # Post-process: Enforce content limits for 1-page constraint
    tailored_resume = enforce_page_limits(tailored_resume)
    
    return tailored_resume


def enforce_page_limits(resume: TailoredResume) -> TailoredResume:
    """
    Enforce content limits to ensure resume fits on 1 page.
    Trims content if AI generated too much.
    """
    # Limit experience bullets to 6 per role
    for exp in resume.experience:
        if len(exp.bullets) > 6:
            exp.bullets = exp.bullets[:6]
    
    # Limit projects to 1
    if len(resume.projects) > 1:
        resume.projects = resume.projects[:1]
    
    # Limit achievements to 2
    if len(resume.achievements) > 2:
        resume.achievements = resume.achievements[:2]
    
    return resume


def force_experience_in_summary(resume: TailoredResume, total_experience: str) -> TailoredResume:
    """
    Force the correct experience duration into the professional summary.
    Replaces any pattern like 'X+ years', 'X years', etc. with the calculated value.
    """
    if not resume.summary:
        return resume
    
    summary = resume.summary
    
    # Pattern to match various experience formats
    patterns = [
        r'\d+\+?\s*years?',  # matches: 2+ years, 3 years, 4+ years, etc.
        r'\d+\.\d+\s*years?',  # matches: 3.5 years, 2.8 years, etc.
    ]
    
    # Extract the numeric part from total_experience
    exp_match = re.search(r'([\d.]+)', total_experience)
    if exp_match:
        exp_value = exp_match.group(1)
        # Check if total_experience includes a '+' sign
        has_plus = '+' in total_experience
        exp_replacement = f"{exp_value}+ years" if has_plus else f"{exp_value} years"
        # Replace any experience pattern with the correct value
        for pattern in patterns:
            summary = re.sub(pattern, exp_replacement, summary, flags=re.IGNORECASE)
    
    resume.summary = summary
    return resume


def validate_master_resume(data: dict) -> bool:
    """
    Validate that the master resume data matches the expected schema.
    
    Args:
        data: Resume data dictionary
        
    Returns:
        True if valid, raises exception otherwise
    """
    required_keys = ['basics', 'summary', 'education', 'experience', 'skills', 'projects', 'achievements']
    
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key in resume: '{key}'")
    
    # Validate basics
    basics_keys = ['name', 'email', 'phone', 'location', 'links']
    for key in basics_keys:
        if key not in data['basics']:
            raise ValueError(f"Missing required key in basics: '{key}'")
    
    # Try to create a TailoredResume to validate structure
    try:
        # Convert skills list to Skills object if needed
        if isinstance(data.get('skills'), list):
            # For validation, just put all skills in languages_frameworks
            data_copy = data.copy()
            data_copy['skills'] = {'languages_frameworks': data['skills'], 'tools': []}
            TailoredResume(**data_copy)
        else:
            TailoredResume(**data)
    except Exception as e:
        raise ValueError(f"Invalid resume structure: {e}")
    
    return True
