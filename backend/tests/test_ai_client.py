import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAIClient:
    """Test the AI Client with Kimi K2.5"""
    
    def test_ai_client_initialization(self):
        """Test AI client can be initialized"""
        from app.ai_client import AIClient
        
        client = AIClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.MAX_ATTEMPTS == 10
        assert client.jobs == {}
    
    @pytest.mark.asyncio
    async def test_start_generation_creates_job(self):
        """Test that starting generation creates a job"""
        from app.ai_client import AIClient
        
        client = AIClient(api_key="test-key")
        
        mock_resume = Mock()
        mock_config = Mock()
        mock_config.fabrication_enabled = True
        mock_config.target_ats_score = 92
        
        job_id = await client.start_generation(
            resume_data=mock_resume,
            job_description="Test JD",
            config=mock_config,
            user_id="user-123"
        )
        
        assert job_id is not None
        assert job_id in client.jobs
        assert client.jobs[job_id]["user_id"] == "user-123"
        assert client.jobs[job_id]["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_get_job_status_returns_correct_structure(self):
        """Test job status returns expected fields"""
        from app.ai_client import AIClient
        
        client = AIClient(api_key="test-key")
        
        mock_resume = Mock()
        mock_config = Mock()
        mock_config.fabrication_enabled = True
        mock_config.target_ats_score = 92
        
        job_id = await client.start_generation(
            resume_data=mock_resume,
            job_description="Test JD",
            config=mock_config,
            user_id="user-123"
        )
        
        status = await client.get_job_status(job_id)
        
        assert "job_id" in status
        assert "status" in status
        assert "progress" in status
        assert "message" in status
        assert "attempt" in status
        assert "ats_score" in status
    
    @pytest.mark.asyncio
    async def test_get_job_status_raises_for_unknown_job(self):
        """Test that getting status for unknown job raises error"""
        from app.ai_client import AIClient
        
        client = AIClient(api_key="test-key")
        
        with pytest.raises(ValueError, match="Job not found"):
            await client.get_job_status("unknown-job-id")


class TestImproveText:
    """Test AI text improvement"""
    
    @pytest.mark.asyncio
    async def test_improve_text_returns_improved_content(self):
        """Test improve text returns improved version"""
        from app.ai_client import AIClient
        
        client = AIClient(api_key="test-key")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value={
                "choices": [{"message": {"content": "Improved text here"}}]
            })
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await client.improve_text(
                original_text="Old text",
                user_prompt="Make it better",
                context="professional summary"
            )
            
            assert result == "Improved text here"
    
    @pytest.mark.asyncio
    async def test_improve_text_handles_api_error(self):
        """Test improve text handles API errors"""
        from app.ai_client import AIClient
        
        client = AIClient(api_key="test-key")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=Exception("API Error"))
            
            with pytest.raises(ValueError, match="AI improvement failed"):
                await client.improve_text(
                    original_text="Old text",
                    user_prompt="Make it better",
                    context="professional summary"
                )
