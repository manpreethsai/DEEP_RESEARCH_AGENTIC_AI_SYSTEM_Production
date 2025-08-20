"""
Deep Research Production System

A production-ready, modular AI-driven research and report generation system
with comprehensive MLOps and LLMOps capabilities.
"""

__version__ = "1.0.0"
__author__ = "Deep Research Team"
__email__ = "support@your-company.com"

from .config.settings import config
from .agents.research_agent import research_agent
from .core.llm_service import llm_service
from .core.search_service import search_service
from .utils.monitoring import metrics_collector
from .utils.cache import cache_manager

__all__ = [
    'config',
    'research_agent',
    'llm_service',
    'search_service',
    'metrics_collector',
    'cache_manager'
] 