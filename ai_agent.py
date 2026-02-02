"""
AI Agent Module

Uses Google GenAI SDK to tailor resumes based on job descriptions.
Includes Pydantic models for structured output.
"""

import json
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

### Professional Summary (3 Sentences)
1. Years of experience + core tech stack matching JD
2. Biggest SPECIFIC achievement (with precise metrics)
3. Key differentiator (security expertise, mentorship, system design)

**EXAMPLE:**
"Results-driven Software Engineer with 4+ years building scalable distributed systems using Node.js, React.js, and AWS. Reduced P99 API latency by 35% and achieved 99.97% uptime across 15 production microservices. Recognized as Secure Code Warrior Champion (Rank 1/500+) for expertise in OWASP Top 10 vulnerability remediation."

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

## 1-PAGE CONSTRAINT (CRITICAL)
**The resume MUST fit on exactly 1 page. NO spillover to page 2.**
- Experience: 8-10 bullets maximum
- Projects: 1-2 bullets each
- Achievements: 3 items only
- Keep bullets to 1-2 lines maximum

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
    
    return tailored_resume


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
