"""
ATS Scoring Module - FAANG/MAANG Standards
Evaluates resume against ATS compatibility requirements using Gemma AI
Returns detailed shortcomings for Kimi to fix on retry
"""

import json
import re
from typing import List, Dict, Tuple

import google.generativeai as genai

from core.models import ATSScore, ParsedResume, JobAnalysis, SeniorityLevel


class ATSScorer:
    """Calculate ATS compatibility score using Gemma AI with JD-based feedback"""
    
    def __init__(self, api_key: str):
        """Initialize scorer with Gemma API key"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemma-3-27b-it')
    
    def calculate_score(
        self,
        resume,
        job_analysis: JobAnalysis
    ) -> ATSScore:
        """
        Calculate comprehensive ATS score using Gemma AI
        Returns score breakdown with detailed shortcomings for retry
        """
        # Extract resume text for analysis
        resume_text = self._extract_resume_text(resume)
        bullets = self._extract_all_bullets(resume)
        
        # Build prompt for Gemma with full JD context
        prompt = self._build_scoring_prompt(resume_text, bullets, job_analysis)
        
        try:
            response = self.model.generate_content(prompt)
            scores = self._parse_gemma_response(response.text)
            
            return ATSScore(
                overall=scores.get('overall', 75),
                keyword_match=scores.get('keyword_match', 70),
                star_compliance=scores.get('star_compliance', 70),
                quantification=scores.get('quantification', 70),
                action_verb_strength=scores.get('action_verb_strength', 70),
                format_compliance=scores.get('format_compliance', 80),
                section_completeness=scores.get('section_completeness', 80),
                suggestions=scores.get('suggestions', []),
                shortcomings=scores.get('shortcomings', []),
                missing_keywords=scores.get('missing_keywords', []),
                weak_bullets=scores.get('weak_bullets', [])
            )
        except Exception as e:
            # Fallback to basic scores if API fails
            return ATSScore(
                overall=75,
                keyword_match=70,
                star_compliance=70,
                quantification=70,
                action_verb_strength=70,
                format_compliance=80,
                section_completeness=80,
                suggestions=[f"Error during AI scoring: {str(e)}"],
                shortcomings=[],
                missing_keywords=[],
                weak_bullets=[]
            )
    
    def _build_scoring_prompt(
        self,
        resume_text: str,
        bullets: List[str],
        job_analysis: JobAnalysis
    ) -> str:
        """Build prompt for Gemma to score the resume against JD"""
        bullets_text = "\n".join(f"- {b}" for b in bullets[:20])
        skills_required = ", ".join(job_analysis.key_skills[:15])
        nice_to_have = ", ".join(job_analysis.nice_to_have_skills[:10])
        focus_areas = ", ".join(job_analysis.role_focus_areas[:5]) if job_analysis.role_focus_areas else "N/A"
        
        return f"""You are an expert ATS (Applicant Tracking System) resume evaluator for FAANG/MAANG companies.

Evaluate this TAILORED resume against the JOB DESCRIPTION requirements. Provide scores AND detailed shortcomings.

**JOB DESCRIPTION ANALYSIS:**
- Role: {job_analysis.role_title}
- Seniority Level: {job_analysis.seniority_level.value}
- Required Skills (MUST HAVE): {skills_required}
- Nice-to-Have Skills: {nice_to_have}
- Focus Areas: {focus_areas}
- Industry: {job_analysis.industry.value}
- Company Type: {job_analysis.company_type.value}

**RESUME CONTENT:**
{resume_text[:3500]}

**RESUME BULLETS:**
{bullets_text}

**YOUR TASK:**
1. Score each dimension (0-100)
2. Identify SPECIFIC shortcomings that prevent score >90
3. List JD keywords MISSING from resume
4. Identify weak bullets that need improvement

**SCORING DIMENSIONS:**
1. **keyword_match**: Does resume include required skills from JD? (Target: 90+)
2. **star_compliance**: Do bullets follow STAR format? (Target: 85+)
3. **quantification**: Are achievements quantified with metrics? (Target: 85+)
4. **action_verb_strength**: Strong verbs (Architected, Engineered) not weak (Worked on)? (Target: 80+)
5. **format_compliance**: ATS-friendly format with standard sections? (Target: 90+)
6. **section_completeness**: All sections complete? (Target: 90+)
7. **overall**: Overall ATS score. MUST BE >90 if resume meets criteria.

Return ONLY this JSON structure:
{{
    "overall": <int>,
    "keyword_match": <int>,
    "star_compliance": <int>,
    "quantification": <int>,
    "action_verb_strength": <int>,
    "format_compliance": <int>,
    "section_completeness": <int>,
    "suggestions": ["actionable suggestion 1", "actionable suggestion 2"],
    "shortcomings": [
        "Specific issue 1 that prevents higher score",
        "Specific issue 2 based on JD requirements",
        "Specific issue 3 for Kimi to fix"
    ],
    "missing_keywords": ["keyword1 from JD not in resume", "keyword2", "keyword3"],
    "weak_bullets": ["Copy of bullet that needs improvement", "Another weak bullet"]
}}

BE SPECIFIC. The shortcomings and missing_keywords will be used to regenerate the resume.
Return valid JSON only."""
    
    def _parse_gemma_response(self, response_text: str) -> Dict:
        """Parse Gemma's JSON response"""
        # Find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback parsing - extract scores manually
        scores = {}
        score_patterns = [
            ('overall', r'overall["\s:]+(\d+)'),
            ('keyword_match', r'keyword_match["\s:]+(\d+)'),
            ('star_compliance', r'star_compliance["\s:]+(\d+)'),
            ('quantification', r'quantification["\s:]+(\d+)'),
            ('action_verb_strength', r'action_verb_strength["\s:]+(\d+)'),
            ('format_compliance', r'format_compliance["\s:]+(\d+)'),
            ('section_completeness', r'section_completeness["\s:]+(\d+)'),
        ]
        
        for key, pattern in score_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                scores[key] = min(int(match.group(1)), 100)
        
        scores['suggestions'] = []
        scores['shortcomings'] = []
        scores['missing_keywords'] = []
        scores['weak_bullets'] = []
        return scores
    
    def _extract_resume_text(self, resume: ParsedResume) -> str:
        """Extract all text from resume"""
        text_parts = []
        
        # Experience bullets
        for exp in resume.experience:
            text_parts.extend(exp.bullets)
            text_parts.append(exp.role)
            text_parts.append(exp.company)
        
        # Skills
        if resume.skills:
            text_parts.extend(resume.skills.languages_frameworks)
            text_parts.extend(resume.skills.tools)
        
        # Projects
        for proj in resume.projects:
            text_parts.append(proj.description)
            text_parts.append(proj.techStack)
        
        # Summary
        if resume.summary:
            text_parts.append(resume.summary)
        
        return ' '.join(text_parts).lower()
    
    def _extract_all_bullets(self, resume: ParsedResume) -> List[str]:
        """Extract all bullet points from resume"""
        bullets = []
        
        for exp in resume.experience:
            bullets.extend(exp.bullets)
        
        # Add project descriptions as bullets
        for proj in resume.projects:
            bullets.append(proj.description)
        
        # Add achievements
        bullets.extend(resume.achievements)
        
        return bullets
    
    def is_faang_ready(self, score: ATSScore) -> Tuple[bool, List[str]]:
        """Check if resume meets FAANG standards (>90)"""
        ready = score.overall >= 90
        issues = []
        
        if score.keyword_match < 85:
            issues.append("Keyword match below 85%")
        if score.star_compliance < 85:
            issues.append("STAR compliance below 85%")
        if score.quantification < 85:
            issues.append("Not enough quantified metrics")
        if score.action_verb_strength < 80:
            issues.append("Action verbs need strengthening")
        
        # Add Gemma's shortcomings
        issues.extend(score.shortcomings)
        
        return ready, issues
