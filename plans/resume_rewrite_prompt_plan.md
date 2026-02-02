# Resume Rewrite Prompt Implementation Plan

## Overview
Implement a new AI prompt template for resume rewriting using a 4-step methodology designed to achieve 100% ATS match while maintaining credibility.

## Variable Mapping

The template placeholders map to application variables as follows:

| Template Placeholder | Application Variable | Source |
|---------------------|---------------------|--------|
| `{{BASE_RESUME}}` | `master_resume` | Dictionary from master_resume.json |
| `{{JOB_DESCRIPTION}}` | `job_description` | String from jd.txt or user input |
| `{{TOTAL_YOE}}` | `total_experience` | Calculated by `calculate_total_experience()` |

## Current Implementation Analysis

### Existing SYSTEM_PROMPT (ai_agent.py lines 165-384)
- Focuses on diverse metrics, security achievements, power verbs
- Has 1-page constraint enforcement
- Uses Pydantic models for structured output
- Calculates total experience from resume dates

### Changes Required
Replace the existing SYSTEM_PROMPT with the new 4-step methodology while maintaining:
- Pydantic schema validation
- JSON output format
- 1-page content limits

## New SYSTEM_PROMPT Structure

```python
SYSTEM_PROMPT = """System Role: You are an expert Resume Strategist and ATS Optimization Engine. Your goal is to rewrite a BASE_RESUME to achieve a 100% match score against a specific JOB_DESCRIPTION, while maintaining strict truthfulness and professional credibility.

---

## Step 1: Keyword Extraction & Mapping

### 1.1 Extract Critical Keywords
Analyze the JOB_DESCRIPTION and extract:
- Top 10 critical "Hard Skills" (e.g., Java, SOAP, Agile, PCF)
- "Domain Keywords" (e.g., Payments, Settlement, Dispute, Security, FinTech, Travel)
- "Soft Skills" emphasized (e.g., Collaboration, Partnership, Decency)

### 1.2 Scan & Map BASE_RESUME
If a skill is present but phrased differently, rename to match JD exactly:
- "Jira" → "Agile Methodology"
- "Rest API" → "Web Services" / "RESTful Web Services"
- "Golang" (if implied by backend experience)
- "MVC" / "SOA" (if implied by architecture experience)

### 1.3 Gap Filling (Inference ONLY)
If a JD keyword is missing but heavily implied, inject naturally:
- Has "Jira/Scrum" → Add "Agile Methodology"
- Has "Spring Boot" → Add "Microservices" / "MVC"
- Has "AWS/Cloud" → Add "Cloud Computing"
⚠️ DO NOT fabricate skills the user clearly does not possess.

---

## Step 2: Seniority & Credibility Calibration (CRITICAL)

### 2.1 Calculate Total YOE
From resume experience dates: {total_experience}

### 2.2 The "Architect" Guardrail
If Total YOE < 5 years, downgrade "Senior" verbs to avoid skepticism:

| Original Verb | Replacement |
|--------------|-------------|
| "Architected" | "Co-designed" / "Engineered" / "Developed" |
| "Spearheaded" | "Led implementation of" / "Drove" |
| "Orchestrated" | "Coordinated" / "Managed" |
| "Managed" | "Owned delivery of" / "Handled" |
| "Directed" | "Contributed to" / "Assisted with" |

**WHY:** Hiring managers with 25+ YOE get skeptical of junior developers using architect-level verbs.

---

## Step 3: Domain & Culture Alignment

### 3.1 Domain Mapping
Rewrite the Professional Summary to explicitly mention the JD's industry domain:
- Fiserv experience → "Payments Domain" / "FinTech"
- MakeMyTrip JD → "Travel Technology" / "E-commerce"
- Healthcare JD → "Healthcare Technology"

### 3.2 Soft Skills Alignment
If JD emphasizes specific culture elements, align bullets:
- "Decency" / "Partnership" → Highlight collaboration
- "Agile methodology" → Emphasize team coordination
- "Cross-functional" → Mention stakeholder collaboration

Example transformation:
- BEFORE: "Built microservices for payment processing"
- AFTER: "Collaborated with cross-functional teams to build payment processing microservices, ensuring seamless integration with settlement systems"

---

## Step 4: Output Generation

### 4.1 Professional Summary (3 sentences)
1. "Software Engineer with {total_experience} of experience specializing in [JD-matched keywords]"
2. Domain-specific achievement with metrics
3. Differentiator matching JD values (security, scale, etc.)

### 4.2 Experience Bullets (MAX 6 per role)
Format: [Calibrated Verb] + [Achievement] + [Technology] + [Metric]
- Apply verb downgrading from Step 2
- Prioritize JD-mentioned technologies
- Mix metric types: time-based, scale, counts, reliability

### 4.3 Skills Section (REORDERED)
Return as object with JD-required skills FIRST:
```json
"skills": {
  "languages_frameworks": [JD skills first, then others],
  "tools": [JD tools first, then others]
}
```

### 4.4 1-Page Constraint (CRITICAL)
- Professional Summary: 3 sentences max
- Experience: 6 bullets max per role
- Projects: 1 max (omit if space tight)
- Achievements: 2 items max

---

## Output Format
Return ONLY a valid JSON object matching this exact schema:
```json
{
  "basics": { "name": "", "email": "", "phone": "", "location": "", "links": [] },
  "summary": "",
  "education": [{ "institution": "", "area": "", "studyType": "", "startDate": "", "endDate": "", "location": "" }],
  "experience": [{ "company": "", "location": "", "role": "", "startDate": "", "endDate": "", "bullets": [] }],
  "skills": { "languages_frameworks": [], "tools": [] },
  "projects": [{ "name": "", "techStack": "", "description": "" }],
  "achievements": []
}
```
"""
```

## Implementation Steps

### 1. Update ai_agent.py

Replace the SYSTEM_PROMPT constant (lines 165-384) with the new 4-step version.

### 2. Update tailor_resume Function

Modify the function to pass `total_experience` into the SYSTEM_PROMPT:

```python
def tailor_resume(
    master_resume: dict,
    job_description: str,
    api_key: str,
    model: str = "gemini-2.0-flash"
) -> TailoredResume:
    # ... existing code ...
    total_experience = calculate_total_experience(experience_list)
    
    # Format system prompt with total_experience
    formatted_system_prompt = SYSTEM_PROMPT.format(total_experience=total_experience)
    
    # Use formatted_system_prompt in config
    # ... rest of function ...
```

### 3. Helper: Verb Downgrading

The AI handles verb downgrading via the prompt instructions. No code changes needed for this - the LLM will apply the calibration based on the YOE provided.

### 4. Post-Processing (Existing)

Keep existing functions:
- `enforce_page_limits()` - Ensures 1-page constraint
- `force_experience_in_summary()` - Validates YOE in summary

## Variable Names in Application

| Variable | Location | Usage |
|----------|----------|-------|
| `master_resume` | ai_agent.py:391, app.py | Dictionary containing base resume |
| `job_description` | ai_agent.py:392, app.py | String containing JD text |
| `total_experience` | ai_agent.py:417 | String like "3.8 years" from calculation |
| `tailored_resume` | ai_agent.py:396 | Pydantic model returned by function |

## Testing Strategy

1. Test with current master_resume.json
2. Test with jd.txt (MakeMyTrip - Travel domain)
3. Verify:
   - Keywords mapped (Golang mentioned in JD but not resume - should NOT be added)
   - Domain alignment (Travel/Travel Technology in summary)
   - Soft skills (Agile methodology emphasized)
   - Skills reordered (Java, Golang mentioned first for MakeMyTrip JD)

## Why This Approach Works

1. **Gap Filling Rule**: Finds implied skills (Jira → Agile) to boost ATS score without lying
2. **Architect Guardrail**: Prevents overqualification bias for mid-level roles
3. **Domain Mapping**: Automatically labels Fiserv as "Payments Domain" for FinTech roles
4. **Credibility Calibration**: Adjusts language based on actual YOE to pass "25 YOE Hiring Manager" test
