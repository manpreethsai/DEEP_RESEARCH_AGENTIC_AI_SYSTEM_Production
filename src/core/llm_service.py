"""
LLM Service for handling AI model interactions.
Provides unified interface for different LLM providers with retry logic and error handling.
"""

import time
import random
import logging
from typing import Optional, Dict, Any
from functools import wraps

import google.generativeai as genai
import requests

from ..config.settings import config
from ..utils.cache import CacheManager
from ..utils.monitoring import MetricsCollector

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying failed LLM calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.info(f"Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
                        raise
            return None
        return wrapper
    return decorator


class LLMService:
    """Service for handling LLM interactions with caching and monitoring."""
    
    def __init__(self):
        """Initialize LLM service with configuration."""
        self.config = config
        self.cache = CacheManager()
        self.metrics = MetricsCollector()
        
        # Initialize Gemini
        genai.configure(api_key=self.config.api.gemini_api_key)
        self.gemini_model = genai.GenerativeModel(
            self.config.model.gemini_model,
            generation_config={
                'temperature': self.config.model.temperature,
                'max_output_tokens': self.config.model.max_tokens,
            }
        )
        
        logger.info(f"LLM Service initialized with model: {self.config.model.gemini_model}")
    
    @retry_on_failure(max_retries=3)
    def generate_content(self, prompt: str, use_cache: bool = True) -> str:
        """
        Generate content using the configured LLM.
        
        Args:
            prompt: The input prompt
            use_cache: Whether to use caching
            
        Returns:
            Generated content string
        """
        # Check cache first
        if use_cache and self.config.enable_caching:
            cached_result = self.cache.get(prompt)
            if cached_result:
                self.metrics.increment('cache_hits')
                logger.info("Cache hit for prompt")
                return cached_result
        
        # Generate content
        start_time = time.time()
        try:
            logger.info(f"Generating content with prompt length: {len(prompt)}")
            
            response = self.gemini_model.generate_content(prompt)
            result = response.text.strip()
            
            processing_time = time.time() - start_time
            self.metrics.increment('api_calls')
            self.metrics.record_timing('llm_generation', processing_time)
            
            logger.info(f"Generated content: {len(result)} characters in {processing_time:.2f}s")
            
            # Cache the result
            if use_cache and self.config.enable_caching:
                self.cache.set(prompt, result)
            
            return result
            
        except Exception as e:
            self.metrics.increment('errors')
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def generate_with_fallback(self, prompt: str) -> str:
        """
        Generate content with fallback to different models if needed.
        
        Args:
            prompt: The input prompt
            
        Returns:
            Generated content string
        """
        models_to_try = [
            self.config.model.gemini_model,
            'gemini-1.5-pro-latest',
            'gemini-1.0-pro-latest'
        ]
        
        for model_name in models_to_try:
            try:
                logger.info(f"Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                continue
        
        raise Exception("All models failed")
    
    def generate_structured(self, prompt: str, expected_format: str = "text") -> Dict[str, Any]:
        """
        Generate structured content with specific format requirements.
        
        Args:
            prompt: The input prompt
            expected_format: Expected output format (text, json, list, etc.)
            
        Returns:
            Structured response
        """
        # Add format instructions to prompt
        format_prompt = f"{prompt}\n\nPlease respond in {expected_format} format."
        
        result = self.generate_content(format_prompt)
        
        # Parse based on expected format
        if expected_format == "json":
            try:
                import json
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response")
                return {"content": result}
        elif expected_format == "list":
            return {"items": [item.strip() for item in result.split('\n') if item.strip()]}
        else:
            return {"content": result}
    
    def batch_generate(self, prompts: list, max_concurrent: int = 4) -> list:
        """
        Generate content for multiple prompts in parallel.
        
        Args:
            prompts: List of prompts
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of generated content
        """
        import concurrent.futures
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_prompt = {
                executor.submit(self.generate_content, prompt): prompt 
                for prompt in prompts
            }
            
            for future in concurrent.futures.as_completed(future_to_prompt):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch generation failed: {e}")
                    results.append(f"Error: {str(e)}")
        
        return results
    
    def validate_response(self, response: str, criteria: Dict[str, Any]) -> bool:
        """
        Validate generated response against criteria.
        
        Args:
            response: Generated response
            criteria: Validation criteria
            
        Returns:
            True if valid, False otherwise
        """
        min_length = criteria.get('min_length', 0)
        max_length = criteria.get('max_length', float('inf'))
        required_keywords = criteria.get('required_keywords', [])
        
        # Check length
        if len(response) < min_length or len(response) > max_length:
            return False
        
        # Check required keywords
        for keyword in required_keywords:
            if keyword.lower() not in response.lower():
                return False
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current service metrics."""
        return self.metrics.get_metrics()


# Global LLM service instance
llm_service = LLMService() 