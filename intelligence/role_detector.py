"""
Role Detection and Job Analysis Module
Analyzes job descriptions to extract role information, seniority, and requirements
"""

import json
import re
from typing import List, Dict, Optional
from core.models import JobAnalysis, SeniorityLevel, CompanyType, Industry, ParsedResume
from intelligence.ai_client import MistralAIClient


class RoleDetector:
    """Detects role information from job descriptions using AI"""
    
    # Keywords for seniority detection
    SENIORITY_KEYWORDS = {
        SeniorityLevel.ENTRY: ['entry level', 'junior', 'intern', 'trainee', 'fresh graduate', '0-1 year', '0-2 years'],
        SeniorityLevel.JUNIOR: ['junior', 'associate', '1-2 years', '1-3 years', 'entry', 'early career'],
        SeniorityLevel.MID: ['mid-level', 'mid level', 'intermediate', '2-4 years', '2-5 years', '3-5 years'],
        SeniorityLevel.SENIOR: ['senior', 'sr.', 'lead', 'staff', '4-6 years', '5+ years', '5-7 years', 'experienced'],
        SeniorityLevel.STAFF: ['staff', 'principal', 'architect', '7+ years', '8+ years', 'senior staff'],
        SeniorityLevel.PRINCIPAL: ['principal', 'distinguished', 'fellow', '10+ years', '8-10 years', 'staff+'],
        SeniorityLevel.DIRECTOR: ['director', 'head of', 'vp', 'chief', 'executive', 'manager']
    }
    
    # Company type indicators
    COMPANY_TYPE_INDICATORS = {
        CompanyType.STARTUP: ['startup', 'early stage', 'series a', 'series b', 'seed stage', 'fast-paced', 'wear many hats'],
        CompanyType.FANG: ['google', 'meta', 'facebook', 'amazon', 'apple', 'netflix', 'microsoft', 'alphabet'],
        CompanyType.FINANCE: ['bank', 'financial', 'trading', 'hedge fund', 'investment', 'fintech', 'payment'],
        CompanyType.CONSULTING: ['consulting', 'consultant', 'client', 'engagement', 'deloitte', 'accenture', 'mckinsey'],
        CompanyType.HEALTHCARE: ['health', 'medical', 'hospital', 'patient', 'clinical', 'pharma', 'biotech']
    }
    
    # Industry keywords
    INDUSTRY_KEYWORDS = {
        Industry.TECH: ['software', 'technology', 'tech', 'saas', 'platform', 'product', 'engineering'],
        Industry.FINANCE: ['finance', 'fintech', 'banking', 'trading', 'investment', 'payment', 'crypto'],
        Industry.HEALTHCARE: ['healthcare', 'health', 'medical', 'biotech', 'pharma', 'clinical'],
        Industry.E_COMMERCE: ['e-commerce', 'ecommerce', 'retail', 'marketplace', 'shopping', 'consumer'],
        Industry.EDUCATION: ['education', 'learning', 'edtech', 'training', 'academic', 'university'],
        Industry.GAMING: ['game', 'gaming', 'esports', 'unity', 'unreal', 'mobile game']
    }
    
    def __init__(self, api_key: str):
        """Initialize with Mistral AI client"""
        # Using the provided API key
        self.api_key = api_key
        self.client = MistralAIClient(self.api_key)
        self.available = True
    
    def analyze_job_description(self, jd_text: str) -> JobAnalysis:
        """
        Analyze job description and extract structured information
        Uses both rule-based detection and AI analysis
        """
        # Clean and normalize text
        jd_lower = jd_text.lower()
        
        # Rule-based detection for quick results
        seniority = self._detect_seniority(jd_lower)
        company_type = self._detect_company_type(jd_lower)
        industry = self._detect_industry(jd_lower)
        years_required = self._extract_years_experience(jd_text)
        
        # Extract skills using pattern matching
        key_skills = self._extract_skills(jd_text)
        
        # Use AI for deeper analysis
        ai_analysis = self._ai_analyze_jd(jd_text)
        
        # Merge rule-based and AI results
        return JobAnalysis(
            role_title=ai_analysis.get('role_title', 'Software Engineer'),
            seniority_level=ai_analysis.get('seniority', seniority),
            years_experience_required=ai_analysis.get('years', years_required),
            key_skills=list(set(key_skills + ai_analysis.get('skills', []))),
            nice_to_have_skills=ai_analysis.get('nice_to_have', []),
            industry=ai_analysis.get('industry', industry),
            company_type=ai_analysis.get('company_type', company_type),
            role_focus_areas=ai_analysis.get('focus_areas', []),
            company_culture_keywords=ai_analysis.get('culture_keywords', []),
            missing_from_resume=[],  # Will be filled later
            match_score=0.0  # Will be calculated later
        )
    
    def _detect_seniority(self, jd_text: str) -> SeniorityLevel:
        """Detect seniority level from keywords"""
        for level, keywords in self.SENIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in jd_text:
                    return level
        return SeniorityLevel.MID  # Default
    
    def _detect_company_type(self, jd_text: str) -> CompanyType:
        """Detect company type"""
        for comp_type, keywords in self.COMPANY_TYPE_INDICATORS.items():
            for keyword in keywords:
                if keyword in jd_text:
                    return comp_type
        return CompanyType.ENTERPRISE  # Default
    
    def _detect_industry(self, jd_text: str) -> Industry:
        """Detect industry"""
        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in jd_text:
                    return industry
        return Industry.TECH  # Default
    
    def _extract_years_experience(self, jd_text: str) -> int:
        """Extract years of experience requirement"""
        patterns = [
            r'(\d+)\+?\s*years?\s+of\s+experience',
            r'(\d+)\+?\s*-\s*\d+\+?\s*years?',
            r'minimum\s+of\s+(\d+)\s*years?',
            r'at\s+least\s+(\d+)\s*years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, jd_text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 3  # Default
    
    def _extract_skills(self, jd_text: str) -> List[str]:
        """Extract technical skills from JD"""
        # Common tech skills pattern
        skills_pattern = r'\b(Python|Java|JavaScript|TypeScript|React|Angular|Vue|Node\.js|Go|Rust|C\+\+|C#|SQL|PostgreSQL|MongoDB|Redis|AWS|Azure|GCP|Docker|Kubernetes|Terraform|Jenkins|Git|Linux|Spring|Django|Flask|Express|GraphQL|REST|gRPC|Kafka|RabbitMQ|Elasticsearch|Prometheus|Grafana|TensorFlow|PyTorch|Machine Learning|AI|Data Science|Blockchain|Solidity|Smart Contracts|iOS|Android|Swift|Kotlin|Flutter|React Native|Unity|Unreal Engine|Cybersecurity|Penetration Testing|CI/CD|Microservices|Serverless|Lambda|Kubernetes|K8s)\b'
        
        matches = re.findall(skills_pattern, jd_text, re.IGNORECASE)
        return list(set([match.lower() for match in matches]))
    
    def _ai_analyze_jd(self, jd_text: str) -> Dict:
        """Use AI for deeper JD analysis"""
        if not self.available or not self.model:
            return {}
        
        prompt = f"""Analyze this job description and extract key information. Return JSON only:

Job Description:
{jd_text[:3000]}

Extract and return JSON with these fields:
{{
    "role_title": "exact job title",
    "seniority": "entry/junior/mid/senior/staff/principal/director",
    "years": number,
    "skills": ["must-have technical skills"],
    "nice_to_have": ["preferred but not required skills"],
    "industry": "technology/finance/healthcare/e_commerce/education/gaming/other",
    "company_type": "startup/mid_size/enterprise/fang/consulting/finance/healthcare",
    "focus_areas": ["backend/frontend/devops/ml/security/etc"],
    "culture_keywords": ["keywords describing company culture"]
}}

Important:
- Be specific with role titles (e.g., "Senior Backend Engineer" not just "Engineer")
- Include all technical skills mentioned
- Identify company culture from phrases like "fast-paced", "collaborative", "innovative"
- Focus on technical focus areas (backend, frontend, ML, etc.)
"""
        
        try:
            response_text = self.client.generate_content(prompt, temperature=0.1)
            return self.client.extract_json(response_text)
        except Exception as e:
            print(f"Mistral analysis error: {e}")
        
        return {}
    
    def calculate_match_score(self, job_analysis: JobAnalysis, resume: ParsedResume) -> float:
        """Calculate match score between job and resume"""
        score = 0.0
        
        # Check skills match (40% of score)
        if resume.skills:
            user_skills = set([s.lower() for s in resume.skills.languages_frameworks + resume.skills.tools])
            required_skills = set([s.lower() for s in job_analysis.key_skills])
            
            if required_skills:
                matched = len(user_skills.intersection(required_skills))
                score += (matched / len(required_skills)) * 40
        
        # Check seniority match (20% of score)
        user_years = self._calculate_total_years(resume)
        if user_years >= job_analysis.years_experience_required:
            score += 20
        elif user_years >= job_analysis.years_experience_required * 0.7:
            score += 10
        
        # Check experience relevance (30% of score)
        relevant_exp = self._count_relevant_experience(resume, job_analysis)
        score += min(relevant_exp * 10, 30)
        
        # Check industry/focus match (10% of score)
        if self._check_focus_match(resume, job_analysis):
            score += 10
        
        return min(score, 100)
    
    def _calculate_total_years(self, resume: ParsedResume) -> int:
        """Calculate total years of experience"""
        total = 0
        for exp in resume.experience:
            # Simple calculation - in production, parse dates properly
            total += 1
        return total
    
    def _count_relevant_experience(self, resume: ParsedResume, job_analysis: JobAnalysis) -> int:
        """Count number of relevant experience entries"""
        relevant = 0
        required_skills = set([s.lower() for s in job_analysis.key_skills])
        
        for exp in resume.experience:
            # Check if experience mentions required skills
            exp_text = ' '.join(exp.bullets + [exp.role, exp.company]).lower()
            if any(skill in exp_text for skill in required_skills):
                relevant += 1
        
        return relevant
    
    def _check_focus_match(self, resume: ParsedResume, job_analysis: JobAnalysis) -> bool:
        """Check if resume focus matches job focus areas"""
        if not job_analysis.role_focus_areas:
            return True
        
        resume_text = ' '.join([
            ' '.join(exp.bullets) for exp in resume.experience
        ]).lower()
        
        focus_keywords = {
            'backend': ['api', 'server', 'backend', 'microservice', 'database', 'sql'],
            'frontend': ['react', 'angular', 'vue', 'ui', 'ux', 'frontend', 'css', 'html'],
            'devops': ['docker', 'kubernetes', 'ci/cd', 'aws', 'terraform', 'infrastructure'],
            'ml': ['machine learning', 'tensorflow', 'pytorch', 'model', 'algorithm', 'ai'],
            'security': ['security', 'encryption', 'auth', 'oauth', 'penetration', 'vulnerability']
        }
        
        for focus in job_analysis.role_focus_areas:
            keywords = focus_keywords.get(focus.lower(), [focus.lower()])
            if any(kw in resume_text for kw in keywords):
                return True
        
        return False
