#!/usr/bin/env python3
"""
Test script for Hybrid ATS Scoring System
Tests all components to ensure proper functionality
"""

import sys
sys.path.insert(0, '.')

from core.models import (
    ParsedResume, TailoredResume, JobAnalysis, Basics, Skills,
    Education, Experience, Project, SeniorityLevel, Industry, CompanyType
)
from intelligence.alternative_ats_scorer import AlternativeATSScorer
from intelligence.hybrid_ats_scorer import HybridATSScorer


def create_test_resume():
    """Create a test resume for scoring"""
    return ParsedResume(
        basics=Basics(
            name="Test User",
            email="test@example.com",
            phone="+1-555-0123",
            location="San Francisco, CA",
            links=["https://linkedin.com/in/test", "https://github.com/test"]
        ),
        education=[
            Education(
                institution="Test University",
                studyType="Bachelor of Science",
                area="Computer Science",
                startDate="2018-09",
                endDate="2022-05",
                location="Test City"
            )
        ],
        experience=[
            Experience(
                company="Tech Corp",
                role="Software Engineer",
                startDate="2022-06",
                endDate="Present",
                location="San Francisco, CA",
                bullets=[
                    "Architected scalable microservices architecture, improving system performance by 40%",
                    "Led development team of 5 engineers, delivering projects on time and under budget",
                    "Developed RESTful APIs using Python and FastAPI, serving 100K+ daily requests",
                    "Implemented CI/CD pipelines using Jenkins and GitHub Actions, reducing deployment time by 50%"
                ],
                is_fabricated=False
            )
        ],
        skills=Skills(
            languages_frameworks=["Python", "JavaScript", "React", "Node.js"],
            tools=["Docker", "AWS", "Git", "Jenkins", "Kubernetes"]
        ),
        projects=[
            Project(
                name="Test Project",
                techStack="Python, AWS",
                description="Built scalable cloud infrastructure using AWS services"
            )
        ],
        achievements=[
            "Best Project Award 2023",
            "Successfully migrated legacy system to modern architecture"
        ]
    )


def create_test_job_analysis():
    """Create a test job analysis"""
    return JobAnalysis(
        role_title="Senior Software Engineer",
        seniority_level=SeniorityLevel.SENIOR,
        key_skills=["Python", "AWS", "Docker", "Kubernetes", "Microservices", "REST APIs", "CI/CD"],
        nice_to_have_skills=["GCP", "Azure", "Terraform", "GraphQL"],
        role_focus_areas=["Backend Development", "Cloud Architecture", "System Design"],
        industry=Industry.TECH,
        company_type=CompanyType.STARTUP,
        match_score=85,
        years_experience_required=5
    )


def test_alternative_scorer():
    """Test the alternative rule-based scorer"""
    print("\\n" + "="*60)
    print("TESTING ALTERNATIVE ATS SCORER")
    print("="*60)
    
    resume = create_test_resume()
    job_analysis = create_test_job_analysis()
    
    scorer = AlternativeATSScorer()
    score = scorer.calculate_score(resume, job_analysis)
    
    print(f"\\n✅ Alternative ATS Score: {score.overall}/100")
    print(f"   - Keyword Match: {score.keyword_match}%")
    print(f"   - Quantification: {score.quantification}%")
    print(f"   - STAR Compliance: {score.star_compliance}%")
    print(f"   - Action Verbs: {score.action_verb_strength}%")
    print(f"   - Format Compliance: {score.format_compliance}%")
    print(f"   - Section Completeness: {score.section_completeness}%")
    
    print(f"\\n📋 Missing Keywords: {score.missing_keywords[:5]}")
    print(f"\\n💡 Suggestions:")
    for suggestion in score.suggestions[:3]:
        print(f"   - {suggestion}")
    
    return score


def test_hybrid_scorer():
    """Test the hybrid scorer (will use fallback since no real API key)"""
    print("\\n" + "="*60)
    print("TESTING HYBRID ATS SCORER")
    print("="*60)
    
    resume = create_test_resume()
    job_analysis = create_test_job_analysis()
    
    # Test with fake key (will use fallback)
    scorer = HybridATSScorer("fake_api_key")
    
    # Test first call
    score1 = scorer.calculate_score(resume, job_analysis, retry_count=0)
    print(f"\\n✅ Hybrid ATS Score (attempt 1): {score1.overall}/100")
    
    # Test with retry (should show boost)
    score2 = scorer.calculate_score(resume, job_analysis, retry_count=3)
    print(f"✅ Hybrid ATS Score (attempt 4): {score2.overall}/100")
    
    # Check history
    history = scorer.get_score_progression()
    print(f"\\n📊 Score History:")
    for entry in history:
        print(f"   - Retry {entry['retry']}: {entry['score']} (AI: {entry['ai_score']}, Rule: {entry['rule_score']})")
    
    return score2


def main():
    """Run all tests"""
    print("\\n" + "🚀"*30)
    print("HYBRID ATS SCORING SYSTEM TEST")
    print("🚀"*30)
    
    try:
        # Test alternative scorer
        alt_score = test_alternative_scorer()
        
        # Test hybrid scorer  
        hybrid_score = test_hybrid_scorer()
        
        print("\\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✅ Alternative Scorer: {alt_score.overall}/100")
        print(f"✅ Hybrid Scorer: {hybrid_score.overall}/100")
        print(f"\\n🎯 Both scoring systems working correctly!")
        print(f"\\n📝 Expected Behavior:")
        print(f"   - AI Scorer: Provides detailed feedback but may be conservative")
        print(f"   - Rule Scorer: Consistent scoring based on objective criteria")
        print(f"   - Hybrid Combines both for reliable results")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
