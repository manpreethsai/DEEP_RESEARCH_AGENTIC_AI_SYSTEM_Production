"""
Tests for the Research Agent module.
"""

import pytest
from unittest.mock import Mock, patch
from src.agents.research_agent import ResearchAgent
from src.models.state import AgentState


class TestResearchAgent:
    """Test cases for ResearchAgent."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.agent = ResearchAgent()
        self.test_topic = "Test Research Topic"
    
    def test_create_agent_state(self):
        """Test agent state creation."""
        state = self.agent.create_agent_state(self.test_topic)
        
        assert isinstance(state, AgentState)
        assert state.topic == self.test_topic
        assert state.status == "initialized"
        assert state.created_at is not None
    
    @patch('src.agents.research_agent.llm_service')
    def test_generate_planning_queries(self, mock_llm):
        """Test planning query generation."""
        # Mock LLM response
        mock_llm.generate_content.return_value = """
        1. What are the key aspects of the topic?
        2. How does it compare to alternatives?
        3. What are the main challenges?
        """
        
        state = self.agent.create_agent_state(self.test_topic)
        updated_state = self.agent.generate_planning_queries(state)
        
        assert len(updated_state.plan_queries) > 0
        assert updated_state.status == "planning_queries_generated"
    
    @patch('src.agents.research_agent.search_service')
    @patch('src.agents.research_agent.llm_service')
    def test_generate_report_outline(self, mock_llm, mock_search):
        """Test report outline generation."""
        # Mock search results
        mock_search.search.return_value = [
            Mock(title="Test Result", content="Test content", url="http://test.com")
        ]
        
        # Mock LLM response
        mock_llm.generate_content.return_value = """
        - **Name:** Test Section
        - **Description:** Test description
        - **Research:** True
        - **Content:** [blank]
        """
        
        state = self.agent.create_agent_state(self.test_topic)
        state.plan_queries = ["Test query 1", "Test query 2"]
        
        updated_state = self.agent.generate_report_outline(state)
        
        assert updated_state.report_outline is not None
        assert updated_state.status == "outline_generated"
    
    def test_run_research_pipeline_basic(self):
        """Test basic pipeline execution."""
        # This is a basic test - in production you'd mock external dependencies
        with patch('src.agents.research_agent.llm_service') as mock_llm, \
             patch('src.agents.research_agent.search_service') as mock_search:
            
            # Mock all external calls
            mock_llm.generate_content.return_value = "Mock response"
            mock_search.search.return_value = [
                Mock(title="Test", content="Test", url="http://test.com")
            ]
            
            # Run pipeline
            state = self.agent.run_research_pipeline("Test Topic")
            
            # Basic assertions
            assert state is not None
            assert hasattr(state, 'topic')
            assert hasattr(state, 'status')
    
    def test_error_handling(self):
        """Test error handling in pipeline."""
        with patch('src.agents.research_agent.llm_service') as mock_llm:
            # Mock LLM to raise exception
            mock_llm.generate_content.side_effect = Exception("API Error")
            
            state = self.agent.run_research_pipeline("Test Topic")
            
            # Should handle error gracefully
            assert state is not None
            assert len(state.error_messages) > 0


if __name__ == "__main__":
    pytest.main([__file__]) 