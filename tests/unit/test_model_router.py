"""
Test Model Router
"""
import pytest

from agentforge.llm import ModelRouter, AVAILABLE_MODELS, ModelType


class TestModelRouter:
    """Test model router"""
    
    @pytest.fixture
    def router(self):
        return ModelRouter(
            api_key="test_key",
            base_url="https://test.api.com"
        )
    
    def test_available_models(self):
        """Test available models configuration"""
        assert "glm-5" in AVAILABLE_MODELS
        assert "kimi-k2.5" in AVAILABLE_MODELS
        assert "deepseek-v3.2" in AVAILABLE_MODELS
        assert "minimax-m2.5" in AVAILABLE_MODELS
    
    def test_select_model_default(self, router):
        """Test default model selection"""
        model = router.select_model(task_type="default")
        
        assert model in AVAILABLE_MODELS
    
    def test_select_model_code(self, router):
        """Test code model selection"""
        model = router.select_model(task_type="code")
        
        assert model in AVAILABLE_MODELS
    
    def test_select_model_with_preference(self, router):
        """Test model selection with preference"""
        model = router.select_model(
            task_type="default",
            prefer_model="deepseek-v3.2"
        )
        
        assert model == "deepseek-v3.2"
    
    def test_get_usage_stats(self, router):
        """Test usage stats"""
        stats = router.get_usage_stats()
        
        assert "usage" in stats
        assert "quota_exceeded" in stats
        assert "model_errors" in stats
    
    def test_reset_daily_stats(self, router):
        """Test reset daily stats"""
        router._model_usage["glm-5"] = 100
        router.reset_daily_stats()
        
        assert router._model_usage["glm-5"] == 0
