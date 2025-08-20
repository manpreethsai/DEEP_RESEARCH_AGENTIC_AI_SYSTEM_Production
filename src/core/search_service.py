"""
Search Service for handling web search operations.
Provides unified interface for different search providers with caching and monitoring.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from functools import wraps

import requests
from tavily import TavilyClient

from ..config.settings import config
from ..models.state import SearchResult
from ..utils.cache import CacheManager
from ..utils.monitoring import MetricsCollector

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying failed search calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Search attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.info(f"Retrying search in {delay:.2f} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} search attempts failed")
                        raise
            return None
        return wrapper
    return decorator


class SearchService:
    """Service for handling web search operations with caching and monitoring."""
    
    def __init__(self):
        """Initialize search service with configuration."""
        self.config = config
        self.cache = CacheManager()
        self.metrics = MetricsCollector()
        
        # Initialize Tavily client
        self.tavily_client = TavilyClient(api_key=self.config.api.tavily_api_key)
        
        logger.info("Search Service initialized with Tavily")
    
    @retry_on_failure(max_retries=3)
    def search(self, query: str, max_results: Optional[int] = None, 
               search_depth: Optional[str] = None, use_cache: bool = True) -> List[SearchResult]:
        """
        Perform web search using Tavily.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            search_depth: Search depth (basic, moderate, advanced)
            use_cache: Whether to use caching
            
        Returns:
            List of SearchResult objects
        """
        # Use config defaults if not specified
        max_results = max_results or self.config.search.max_results
        search_depth = search_depth or self.config.search.search_depth
        
        # Check cache first
        cache_key = f"search:{query}:{max_results}:{search_depth}"
        if use_cache and self.config.enable_caching:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self.metrics.increment('cache_hits')
                logger.info(f"Cache hit for search query: {query[:50]}...")
                return [SearchResult(**result) for result in cached_result]
        
        # Perform search
        start_time = time.time()
        try:
            logger.info(f"Searching for: '{query[:50]}{'...' if len(query) > 50 else ''}'")
            
            response = self.tavily_client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=self.config.search.include_answer
            )
            
            # Convert to SearchResult objects
            results = []
            for result in response.get('results', []):
                search_result = SearchResult(
                    title=result.get('title', ''),
                    content=result.get('content', ''),
                    url=result.get('url', ''),
                    source='tavily',
                    relevance_score=result.get('score', None)
                )
                results.append(search_result)
            
            processing_time = time.time() - start_time
            self.metrics.increment('search_queries')
            self.metrics.record_timing('search_time', processing_time)
            
            logger.info(f"Search completed: {len(results)} results in {processing_time:.2f}s")
            
            # Cache the results
            if use_cache and self.config.enable_caching:
                self.cache.set(cache_key, [result.__dict__ for result in results])
            
            return results
            
        except Exception as e:
            self.metrics.increment('errors')
            logger.error(f"Search failed for query '{query}': {e}")
            raise
    
    def search_multiple(self, queries: List[str], max_concurrent: int = 4) -> Dict[str, List[SearchResult]]:
        """
        Perform multiple searches in parallel.
        
        Args:
            queries: List of search queries
            max_concurrent: Maximum concurrent searches
            
        Returns:
            Dictionary mapping queries to search results
        """
        import concurrent.futures
        
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_query = {
                executor.submit(self.search, query): query 
                for query in queries
            }
            
            for future in concurrent.futures.as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    search_results = future.result()
                    results[query] = search_results
                    logger.info(f"Completed search for: {query[:50]}... ({len(search_results)} results)")
                except Exception as e:
                    logger.error(f"Search failed for query '{query}': {e}")
                    results[query] = []
        
        return results
    
    def search_with_filters(self, query: str, filters: Dict[str, Any]) -> List[SearchResult]:
        """
        Perform search with additional filters.
        
        Args:
            query: Search query
            filters: Additional search filters
            
        Returns:
            List of SearchResult objects
        """
        # Apply filters to query
        filtered_query = query
        if filters.get('date_range'):
            filtered_query += f" {filters['date_range']}"
        if filters.get('site_restriction'):
            filtered_query += f" site:{filters['site_restriction']}"
        
        return self.search(filtered_query)
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions for a query.
        
        Args:
            query: Base query
            
        Returns:
            List of suggested queries
        """
        # This could be implemented with a suggestion API
        # For now, return basic variations
        suggestions = [
            f"{query} 2024",
            f"{query} latest",
            f"{query} analysis",
            f"{query} trends",
            f"{query} comparison"
        ]
        return suggestions
    
    def validate_search_results(self, results: List[SearchResult], criteria: Dict[str, Any]) -> bool:
        """
        Validate search results against criteria.
        
        Args:
            results: List of search results
            criteria: Validation criteria
            
        Returns:
            True if valid, False otherwise
        """
        min_results = criteria.get('min_results', 1)
        max_age_days = criteria.get('max_age_days', None)
        required_domains = criteria.get('required_domains', [])
        
        # Check minimum results
        if len(results) < min_results:
            return False
        
        # Check domain requirements
        if required_domains:
            found_domains = set()
            for result in results:
                for domain in required_domains:
                    if domain in result.url:
                        found_domains.add(domain)
            if not found_domains.issuperset(set(required_domains)):
                return False
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current service metrics."""
        return self.metrics.get_metrics()


# Global search service instance
search_service = SearchService() 