"""
Test Chat API
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestChatAPI:
    """Test chat API endpoints"""
    
    @pytest.fixture
    def mock_agent(self):
        agent = Mock()
        agent.agent_id = "test_agent"
        agent.name = "TestAgent"
        agent.conversation_history = []
        agent.process_message = AsyncMock(return_value="Test response")
        return agent
    
    @pytest.mark.asyncio
    async def test_chat_request_structure(self):
        """Test chat request structure"""
        from integrations.api.chat import ChatRequest
        
        request = ChatRequest(
            message="Hello",
            conversation_id="test_conv",
            agent="default"
        )
        
        assert request.message == "Hello"
        assert request.conversation_id == "test_conv"
        assert request.agent == "default"
    
    @pytest.mark.asyncio
    async def test_chat_response_structure(self):
        """Test chat response structure"""
        from integrations.api.chat import ChatResponse
        
        response = ChatResponse(
            response="Test response",
            conversation_id="test_conv",
            agent="default",
            model="glm-5"
        )
        
        assert response.response == "Test response"
        assert response.conversation_id == "test_conv"
    
    @pytest.mark.asyncio
    async def test_conversation_history_structure(self):
        """Test conversation history structure"""
        from integrations.api.chat import ConversationHistory
        
        history = ConversationHistory(
            messages=[{"role": "user", "content": "Hello"}],
            total=1
        )
        
        assert len(history.messages) == 1
        assert history.total == 1
    
    @pytest.mark.asyncio
    async def test_generate_conversation_id(self):
        """Test conversation ID generation"""
        from integrations.api.chat import generate_conversation_id
        
        conv_id = generate_conversation_id()
        
        assert conv_id.startswith("conv_")
        assert len(conv_id) > 10
