"""
AI Agent Module

Uses Google GenAI SDK to tailor resumes based on job descriptions.
Includes Pydantic models for structured output.
"""

import json
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
        # Round to nearest half year for cleaner display
        rounded_years = round(years * 2) / 2
        if rounded_years == int(rounded_years):
            return f"{int(rounded_years)}+ years"
        else:
            return f"{rounded_years} years"


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are a SENIOR TECHNICAL RECRUITER and EXPERT RESUME WRITER with 15+ years of experience hiring for Fortune 500 companies. You are an expert in ATS systems and what makes senior hiring managers say "Let's interview this person."

---

## CRITICAL RULES (FOLLOW EXACTLY)

### RULE 1: DIVERSE METRICS (NOT JUST PERCENTAGES)
NEVER rely only on percentages. Mix different metric types for credibility.

**AVOID: Percentage-only metrics (looks like guessing)**
- ❌ BAD: "Improved performance by 40%"
- ❌ BAD: "Reduced errors by 25%"
- ❌ BAD: "Enhanced efficiency by 30%"

**USE DIVERSE METRIC TYPES:**

**Time-Based (Absolute):**
- "Reduced P99 latency from 400ms to 280ms"
- "Cut deployment time from 45 minutes to 8 minutes"
- "Accelerated onboarding by 3 weeks"
- "Achieved sub-200ms response times"

**Scale/Volume:**
- "Processing 2M+ daily transactions"
- "Serving 50K concurrent users"
- "Handling 10K requests/second"
- "Managing 500GB+ data pipeline"

**Counts (Absolute Numbers):**
- "Resolved 80+ user stories and 35 complex defects"
- "Built 15 new microservices from scratch"
- "Mentored 5 junior developers"
- "Authored 12 technical design documents"

**Financial/Business:**
- "Saving $500K annually in infrastructure costs"
- "Generated $2M in new revenue"
- "Reduced operational costs by $150K/quarter"

**Quality/Reliability:**
- "Achieved 99.97% uptime across 15 services"
- "Maintained zero security incidents for 18 months"
- "Reduced error rate from 2.5% to 0.3%"

**METRIC MIXING RULE:**
For every 3 bullets, use AT LEAST:
- 1 absolute time metric (ms, seconds, minutes, weeks)
- 1 scale/count metric (users, requests, transactions)
- 1 mixed metric (percentage WITH absolute context)

**GOOD EXAMPLES:**
- "Reduced API latency from 600ms to 200ms, handling 50K concurrent users"
- "Built 8 microservices processing 2M daily transactions with 99.97% uptime"
- "Mentored 4 junior developers, accelerating their productivity ramp-up by 3 weeks"

### RULE 2: HIGHLIGHT SECURITY ACHIEVEMENTS PROMINENTLY
Security is a MASSIVE priority for big tech. If the candidate has ANY security credentials, FEATURE THEM.

**In Professional Summary (if applicable):**
Include security credentials: "Recognized as top Secure Code Warrior (Rank 1/500+) for expertise in mitigating OWASP Top 10 vulnerabilities."

**In Experience Bullets:**
Add a "Security & Compliance" bullet: "Security Champion: Identified and remediated 15+ critical vulnerabilities including SQL injection and XSS, achieving zero security incidents in production for 18 months."

### RULE 3: PROJECTS = ENGINEERING CHALLENGES, NOT ML ACCURACY
For ML/AI projects, hiring managers care about ENGINEERING, not just model accuracy.

**FOCUS ON:**
- Edge deployment optimization (model compression, quantization)
- Offline inference capabilities
- Model size optimization for mobile
- Data pipeline architecture
- Real-time processing constraints
- Infrastructure challenges

**EXAMPLE TRANSFORMATION:**
- ❌ BAD: "Developed a disease detection app with 95% accuracy"
- ✅ GOOD:
  - "Engineered an Edge AI inference pipeline for Android, compressing YOLOv10 model from 50MB to 8MB using TensorFlow Lite quantization while maintaining 95% accuracy"
  - "Implemented offline-first architecture with on-device inference, achieving sub-300ms detection times on low-end Android hardware (2GB RAM)"

### RULE 4: POWER VERBS (Use Stronger Alternatives)
**UPGRADE THESE:**
- "Contributed to" → "Authored" or "Designed"
- "Participated in" → "Led" or "Drove"
- "Helped with" → "Spearheaded" or "Orchestrated"
- "Worked on" → "Engineered" or "Architected"
- "Was responsible for" → "Owned" or "Directed"

**STRONG VERBS BY CATEGORY:**
- **Architecture**: Architected, Designed, Authored, Engineered
- **Optimization**: Optimized, Reduced, Slashed, Accelerated
- **Leadership**: Spearheaded, Championed, Pioneered, Directed
- **Security**: Hardened, Secured, Remediated, Fortified

### RULE 5: EXPERIENCE BULLETS - Start with Power Verbs
**DO NOT use category headers.** Start each bullet directly with a strong action verb.

**CORRECT FORMAT:**
"[Power Verb] + [specific achievement] + [technology used] + [quantified result]"

**EXAMPLE BULLETS:**
- "Authored low-level design (LLD) for payment processing module, defining class hierarchies and API contracts that reduced integration time by 40%"
- "Reduced P99 API latency from 520ms to 340ms by implementing Redis caching layer and optimizing database query patterns"
- "Championed secure coding practices as top Secure Code Warrior (Rank 1/500+), remediating 20+ OWASP Top 10 vulnerabilities before production"
- "Slashed deployment pipeline from 45 minutes to 8 minutes by parallelizing test suites and implementing incremental Docker builds"
- "Engineered high-performance REST APIs using Node.js and Express, reducing response time from 450ms to 220ms while handling 10K requests/second"

---

## OUTPUT REQUIREMENTS

### Professional Summary (3 Sentences - MUST BE SPECIFIC TO THE JOB DESCRIPTION)
**CRITICAL RULES:**
1. **EXACT Experience**: Start with "Software Engineer with {total_experience} of experience" - NO EXCEPTIONS
2. **JD-Specific Keywords**: Scan the job description and EXPLICITLY mention 3-4 technologies/requirements from the JD
3. **Biggest Achievement**: One metric that directly relates to the JD requirements
4. **Differentiator**: Something that matches what this specific job values

**BAD (Too Generic):**
"A highly motivated Software Engineer with 2+ years of experience specializing in Java J2EE development and microservices architecture..."

**GOOD (JD-Specific):**
"Software Engineer with 3.8 years of experience specializing in Java, Spring Boot, and microservices architecture. Architected event-driven systems processing 10M+ daily transactions using Apache Kafka and Flink, directly matching your real-time data processing requirements. Ranked #1 in Secure Code Warrior competition among 500+ participants, with proven expertise in Fortify security scanning and CI/CD pipeline optimization."

**MANDATORY:** The summary must read like it was written SPECIFICALLY for this job posting, not a generic template.

### Experience Bullets (MAXIMUM 6 per role - FORCED 1 PAGE CONSTRAINT)
**STRICT LIMIT: 6 bullets maximum per job role.**
- If more than 6 bullets would be generated, select only the 6 most relevant to the JD
- Prioritize bullets that mention technologies/requirements explicitly stated in the JD
- Each bullet must demonstrate impact with specific metrics

**Bullet Selection Priority:**
1. Bullets mentioning JD-required technologies (exact matches first)
2. Bullets with the most impressive quantified results
3. Security-related achievements (if JD mentions security)
4. Scale/performance achievements
5. Leadership or cross-functional collaboration

### Projects (MAXIMUM 1 project if needed for space)
**STRICT LIMIT: Include projects ONLY if space permits on 1 page.**
- If resume exceeds 1 page without projects, omit entirely
- If included, limit to 1 project maximum
- Focus on engineering challenges relevant to the JD

### Achievements (MAXIMUM 2 items)
**STRICT LIMIT: 2 achievements maximum.**
- Security achievements first (if applicable)
- Best Performer/Awards second
- Keep each to one line maximum

### Skills (MUST be an object with two keys)
Return skills as an OBJECT, not a list:
```json
"skills": {
  "languages_frameworks": ["JavaScript", "TypeScript", "React", "Node.js"],
  "tools": ["Docker", "Kubernetes", "AWS", "GitLab CI/CD"]
}
```
- **languages_frameworks**: JD-required first, then others
- **tools**: JD-required first, then others

### Experience (8-10 bullets per role - FIT ON 1 PAGE)
**CRITICAL: The resume MUST fit on exactly 1 page. Do NOT generate so many bullets that it spills to page 2.**

**CRITICAL: You MUST include startDate and endDate for each experience entry EXACTLY as they appear in the Master Resume.**

Each bullet:
1. Start with a POWER VERB (no category header)
2. SPECIFIC metric (latency, throughput, error rate - NOT "performance")
3. Absolute number + percentage where applicable
4. Technology and method used

**Cover these areas (1-2 bullets each, 8-10 total):**
- Backend/API Engineering
- Frontend Performance
- DevOps & CI/CD
- Security & Compliance
- Performance/Scale

### Projects (Focus on Engineering, NOT just ML metrics)
For each project, provide 1-2 concise bullets:
- Engineering challenge solved (deployment, optimization, architecture)
- Impact and scale (users served, processing speed, etc.)

**EXAMPLE for ML Project:**
- "Engineered Edge AI inference pipeline, compressing YOLOv10 from 50MB to 8MB using TensorFlow Lite INT8 quantization while maintaining 95% mAP"
- "Implemented offline-first architecture achieving sub-300ms detection on 2GB RAM Android devices, serving 1,000+ users"

### Achievements (3 items - CONCISE)
Generate exactly 3 achievement items:
- Security achievements FIRST (Secure Code Warrior, OWASP expertise)  
- Best Performer / Awards
- Leadership roles (GDSC, team lead)

---

## 1-PAGE CONSTRAINT (CRITICAL - ENFORCED)
**The resume MUST fit on exactly 1 page. Content exceeding 1 page will be REJECTED.**

**HARD LIMITS (Enforced by system):**
- Professional Summary: 3 sentences maximum
- Experience: 6 bullets maximum per role
- Projects: 1 project maximum (omit if space is tight)
- Achievements: 2 items maximum
- Education: List degrees only, no bullet points

**If you generate more content than fits on 1 page, the system will DELETE sections automatically.**

## QUALITY CHECKLIST
✓ NO vague "performance" claims - specify latency/throughput/error rate
✓ Security achievements featured prominently (summary + first achievement)
✓ Projects emphasize ENGINEERING challenges, not just accuracy
✓ All verbs upgraded (Authored, not Contributed)
✓ Every metric is SPECIFIC with before/after when possible
✓ **FITS ON EXACTLY 1 PAGE - NO PAGE 2 SPILLOVER**

## Output Format:
Return a JSON object matching the TailoredResume schema exactly."""


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

Please tailor the resume for this job description. Return ONLY a valid JSON object matching the TailoredResume schema."""
    else:
        # Embed instructions in user prompt for Gemma and other models
        user_prompt = f"""{SYSTEM_PROMPT}

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

Please tailor the resume for this job description. Return ONLY a valid JSON object with these exact keys:
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
            system_instruction=SYSTEM_PROMPT,
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
        # Replace any experience pattern with the correct value
        for pattern in patterns:
            summary = re.sub(pattern, f"{exp_value} years", summary, flags=re.IGNORECASE)
    
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
