import pytest
from pydantic import ValidationError


class TestAppModels:
    """Test Pydantic models in app/models.py"""
    
    def test_basics_model_valid(self):
        """Test Basics model with valid data"""
        from app.models import Basics
        
        basics = Basics(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890"
        )
        
        assert basics.name == "John Doe"
        assert basics.email == "john@example.com"
        assert basics.phone == "+1234567890"
    
    def test_basics_model_optional_fields(self):
        """Test Basics model with optional fields"""
        from app.models import Basics
        
        basics = Basics(
            name="John Doe",
            email="john@example.com"
        )
        
        assert basics.name == "John Doe"
        assert basics.phone is None
        assert basics.linkedin is None
    
    def test_experience_model(self):
        """Test Experience model"""
        from app.models import Experience
        
        exp = Experience(
            company="Google",
            role="Software Engineer",
            startDate="2020-01",
            endDate="2023-12",
            bullets=["Led team of 5 engineers", "Improved performance by 50%"]
        )
        
        assert exp.company == "Google"
        assert exp.role == "Software Engineer"
        assert len(exp.bullets) == 2
        assert exp.is_fabricated == False
    
    def test_skills_model(self):
        """Test Skills model"""
        from app.models import Skills
        
        skills = Skills(
            languages_frameworks=["Python", "React"],
            tools=["AWS", "Docker"],
            methodologies=["Agile", "Scrum"]
        )
        
        assert len(skills.languages_frameworks) == 2
        assert len(skills.tools) == 2
        assert len(skills.methodologies) == 2
    
    def test_parsed_resume_model(self):
        """Test ParsedResume model"""
        from app.models import ParsedResume, Basics, Experience, Skills
        
        resume = ParsedResume(
            basics=Basics(name="John Doe", email="john@example.com"),
            experience=[
                Experience(
                    company="Google",
                    role="Software Engineer",
                    startDate="2020-01",
                    endDate="2023-12",
                    bullets=[]
                )
            ],
            skills=Skills(languages_frameworks=["Python"], tools=[])
        )
        
        assert resume.basics.name == "John Doe"
        assert len(resume.experience) == 1
    
    def test_generation_config_defaults(self):
        """Test GenerationConfig default values"""
        from app.models import GenerationConfig
        
        config = GenerationConfig()
        
        assert config.generation_mode.value == "tailor_with_jd"
        assert config.target_ats_score == 92
        assert config.fabrication_enabled == True
    
    def test_generation_config_custom(self):
        """Test GenerationConfig with custom values"""
        from app.models import GenerationConfig, GenerationMode
        
        config = GenerationConfig(
            generation_mode=GenerationMode.ATS_OPTIMIZE_ONLY,
            target_ats_score=90,
            fabrication_enabled=False
        )
        
        assert config.generation_mode == GenerationMode.ATS_OPTIMIZE_ONLY
        assert config.target_ats_score == 90
        assert config.fabrication_enabled == False
    
    def test_tailored_resume_model(self):
        """Test TailoredResume model"""
        from app.models import TailoredResume, Basics, Experience, Skills
        
        resume = TailoredResume(
            basics=Basics(name="John Doe", email="john@example.com"),
            experience=[
                Experience(
                    company="Google",
                    role="Software Engineer",
                    startDate="2020-01",
                    endDate="2023-12",
                    bullets=["Led team development"]
                )
            ],
            skills=Skills(languages_frameworks=["Python"], tools=[]),
            ats_score={
                "overall": 92,
                "keyword_match": 95,
                "star_compliance": 90,
                "quantification": 88,
                "action_verb_strength": 95
            }
        )
        
        assert resume.ats_score["overall"] == 92
        assert resume.basics.name == "John Doe"


class TestHealthResponse:
    """Test health check response"""
    
    def test_health_response(self):
        from app.models import HealthResponse
        
        health = HealthResponse(
            status="healthy",
            version="2.0.0",
            service="resumemaker-ai"
        )
        
        assert health.status == "healthy"
        assert health.version == "2.0.0"
