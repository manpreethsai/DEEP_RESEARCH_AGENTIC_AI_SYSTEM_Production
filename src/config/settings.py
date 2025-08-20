"""
Configuration settings for the Deep Research Production System.
Handles environment variables, API keys, and system configuration.
"""

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class APIConfig:
    """API configuration settings."""
    gemini_api_key: str
    tavily_api_key: str
    openai_api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Create API config from environment variables."""
        return cls(
            gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
            tavily_api_key=os.getenv('TAVILY_API_KEY', ''),
            openai_api_key=os.getenv('OPENAI_API_KEY', '')
        )


@dataclass
class ModelConfig:
    """Model configuration settings."""
    gemini_model: str = 'gemini-1.5-flash-latest'
    openai_model: str = 'gpt-4o'
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30


@dataclass
class SearchConfig:
    """Search configuration settings."""
    max_results: int = 3
    search_depth: str = 'moderate'  # basic, moderate, advanced
    include_answer: bool = False
    search_timeout: int = 30


@dataclass
class ReportConfig:
    """Report generation configuration."""
    max_sections: int = 6
    min_section_words: int = 300
    max_section_words: int = 400
    parallel_processing: bool = True
    max_workers: int = 4


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_path: Optional[str] = None


@dataclass
class ProductionConfig:
    """Main production configuration."""
    api: APIConfig
    model: ModelConfig
    search: SearchConfig
    report: ReportConfig
    logging: LoggingConfig
    
    # Paths
    base_path: Path = Path(__file__).parent.parent.parent
    data_path: Path = base_path / 'data'
    logs_path: Path = base_path / 'logs'
    cache_path: Path = base_path / 'cache'
    
    # Feature flags
    enable_caching: bool = True
    enable_monitoring: bool = True
    enable_validation: bool = True
    enable_retry: bool = True
    
    @classmethod
    def from_env(cls) -> 'ProductionConfig':
        """Create production config from environment."""
        return cls(
            api=APIConfig.from_env(),
            model=ModelConfig(),
            search=SearchConfig(),
            report=ReportConfig(),
            logging=LoggingConfig()
        )
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.api.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required")
        if not self.api.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required")
        return True
    
    def create_directories(self):
        """Create necessary directories."""
        self.data_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        self.cache_path.mkdir(exist_ok=True)


# Global configuration instance
config = ProductionConfig.from_env() 