import pytest
import io
from unittest.mock import Mock, patch


class TestPDFGeneration:
    """Test PDF generation functionality"""
    
    def test_resume_processor_initialization(self):
        """Test ResumeProcessor can be initialized"""
        from app.resume import ResumeProcessor
        
        processor = ResumeProcessor()
        assert processor is not None
    
    @pytest.mark.asyncio
    async def test_generate_pdf_with_valid_resume(self):
        """Test PDF generation with valid resume data"""
        from app.resume import ResumeProcessor
        from app.models import TailoredResume, Basics, Experience, Skills
        
        processor = ResumeProcessor()
        
        resume = TailoredResume(
            basics=Basics(name="John Doe", email="john@example.com"),
            experience=[
                Experience(
                    company="Google",
                    role="Software Engineer",
                    startDate="2020-01",
                    endDate="2023-12",
                    bullets=["Led team of 5 engineers", "Improved performance by 50%"]
                )
            ],
            skills=Skills(languages_frameworks=["Python", "React"], tools=["AWS", "Docker"]),
            summary="Experienced software engineer"
        )
        
        pdf_bytes = await processor.generate_pdf(resume)
        
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, io.BytesIO)
        assert pdf_bytes.tell() > 0
    
    @pytest.mark.asyncio
    async def test_generate_pdf_with_minimal_data(self):
        """Test PDF generation with minimal data"""
        from app.resume import ResumeProcessor
        from app.models import TailoredResume, Basics, Experience, Skills
        
        processor = ResumeProcessor()
        
        resume = TailoredResume(
            basics=Basics(name="Jane Smith", email="jane@example.com"),
            experience=[
                Experience(
                    company="Startup",
                    role="Developer",
                    startDate="2021-01",
                    endDate="2022-12",
                    bullets=["Built features"]
                )
            ],
            skills=Skills(languages_frameworks=["JavaScript"], tools=[])
        )
        
        pdf_bytes = await processor.generate_pdf(resume)
        
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, io.BytesIO)


class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_health_check_root(self, client):
        """Test health check at root"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuth:
    """Test authentication"""
    
    def test_get_current_user_without_token(self):
        """Test that endpoints require auth"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/api/resume/status/test-job")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]
