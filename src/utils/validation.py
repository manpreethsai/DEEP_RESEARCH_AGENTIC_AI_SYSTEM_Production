"""
Validation utility for the Deep Research Production System.
Provides content quality assessment, fact-checking, and validation features.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..core.llm_service import llm_service
from ..models.state import ValidationResult, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationCriteria:
    """Criteria for content validation."""
    min_length: int = 100
    max_length: int = 5000
    required_keywords: List[str] = None
    forbidden_keywords: List[str] = None
    min_sources: int = 1
    max_hallucination_score: float = 0.3
    min_coverage_score: float = 0.7
    min_readability_score: float = 0.6


class ContentValidator:
    """Validator for content quality and accuracy."""
    
    def __init__(self):
        """Initialize content validator."""
        self.validation_prompts = {
            'grounding': """
            Analyze the following content for factual grounding in the provided sources.
            
            Content to validate:
            {content}
            
            Source documents:
            {sources}
            
            Evaluate:
            1. Are claims in the content supported by the sources?
            2. Are there any unsupported or potentially false claims?
            3. Is the content accurately representing the source information?
            
            Provide a score from 0-1 and list any hallucinated claims.
            """,
            
            'coverage': """
            Evaluate how well the content covers the intended queries.
            
            Content:
            {content}
            
            Intended queries:
            {queries}
            
            Assess:
            1. Does the content address all the queries?
            2. Are there any gaps in coverage?
            3. Is the depth of coverage appropriate?
            
            Provide a score from 0-1 and list any coverage gaps.
            """,
            
            'readability': """
            Assess the readability and quality of the content.
            
            Content:
            {content}
            
            Evaluate:
            1. Is the writing clear and coherent?
            2. Is the grammar and structure correct?
            3. Is the tone appropriate for the audience?
            4. Is the content well-organized?
            
            Provide a score from 0-1 and list any issues.
            """
        }
    
    def validate_section_grounding(self, content: str, sources: List[SearchResult]) -> ValidationResult:
        """
        Validate if content is factually grounded in sources.
        
        Args:
            content: Content to validate
            sources: Source documents
            
        Returns:
            Validation result with grounding score
        """
        try:
            sources_text = "\n\n".join([source.to_markdown() for source in sources])
            
            prompt = self.validation_prompts['grounding'].format(
                content=content,
                sources=sources_text
            )
            
            response = llm_service.generate_content(prompt)
            
            # Parse response for score and issues
            score, issues = self._parse_validation_response(response)
            
            return ValidationResult(
                section_title="Grounding Validation",
                grounding_score=score,
                coverage_score=0.0,
                readability_score=0.0,
                hallucinated_claims=issues
            )
            
        except Exception as e:
            logger.error(f"Grounding validation failed: {e}")
            return ValidationResult(
                section_title="Grounding Validation",
                grounding_score=0.0,
                coverage_score=0.0,
                readability_score=0.0,
                hallucinated_claims=[f"Validation error: {str(e)}"]
            )
    
    def validate_section_coverage(self, content: str, queries: List[str]) -> ValidationResult:
        """
        Validate if content adequately covers the intended queries.
        
        Args:
            content: Content to validate
            queries: Intended research queries
            
        Returns:
            Validation result with coverage score
        """
        try:
            queries_text = "\n".join([f"- {query}" for query in queries])
            
            prompt = self.validation_prompts['coverage'].format(
                content=content,
                queries=queries_text
            )
            
            response = llm_service.generate_content(prompt)
            
            # Parse response for score and issues
            score, issues = self._parse_validation_response(response)
            
            return ValidationResult(
                section_title="Coverage Validation",
                grounding_score=0.0,
                coverage_score=score,
                readability_score=0.0,
                coverage_gaps=issues
            )
            
        except Exception as e:
            logger.error(f"Coverage validation failed: {e}")
            return ValidationResult(
                section_title="Coverage Validation",
                grounding_score=0.0,
                coverage_score=0.0,
                readability_score=0.0,
                coverage_gaps=[f"Validation error: {str(e)}"]
            )
    
    def validate_readability(self, content: str) -> ValidationResult:
        """
        Validate content readability and quality.
        
        Args:
            content: Content to validate
            
        Returns:
            Validation result with readability score
        """
        try:
            prompt = self.validation_prompts['readability'].format(content=content)
            
            response = llm_service.generate_content(prompt)
            
            # Parse response for score and issues
            score, issues = self._parse_validation_response(response)
            
            return ValidationResult(
                section_title="Readability Validation",
                grounding_score=0.0,
                coverage_score=0.0,
                readability_score=score,
                readability_issues=issues
            )
            
        except Exception as e:
            logger.error(f"Readability validation failed: {e}")
            return ValidationResult(
                section_title="Readability Validation",
                grounding_score=0.0,
                coverage_score=0.0,
                readability_score=0.0,
                readability_issues=[f"Validation error: {str(e)}"]
            )
    
    def validate_comprehensive(self, content: str, sources: List[SearchResult], 
                             queries: List[str]) -> ValidationResult:
        """
        Perform comprehensive validation of content.
        
        Args:
            content: Content to validate
            sources: Source documents
            queries: Intended research queries
            
        Returns:
            Comprehensive validation result
        """
        # Perform all validations
        grounding_result = self.validate_section_grounding(content, sources)
        coverage_result = self.validate_section_coverage(content, queries)
        readability_result = self.validate_readability(content)
        
        # Combine results
        combined_result = ValidationResult(
            section_title="Comprehensive Validation",
            grounding_score=grounding_result.grounding_score,
            coverage_score=coverage_result.coverage_score,
            readability_score=readability_result.readability_score,
            hallucinated_claims=grounding_result.hallucinated_claims,
            coverage_gaps=coverage_result.coverage_gaps,
            readability_issues=readability_result.readability_issues
        )
        
        # Calculate overall score
        combined_result.calculate_overall_score()
        
        return combined_result
    
    def _parse_validation_response(self, response: str) -> tuple[float, List[str]]:
        """
        Parse validation response to extract score and issues.
        
        Args:
            response: LLM validation response
            
        Returns:
            Tuple of (score, issues)
        """
        try:
            # Look for score in response
            score = 0.5  # Default score
            issues = []
            
            # Simple parsing - look for score and issues
            lines = response.split('\n')
            for line in lines:
                line = line.strip().lower()
                if 'score:' in line or 'rating:' in line:
                    try:
                        # Extract numeric score
                        import re
                        score_match = re.search(r'(\d+\.?\d*)', line)
                        if score_match:
                            score = float(score_match.group(1))
                            if score > 1.0:  # Convert percentage to decimal
                                score = score / 100.0
                    except:
                        pass
                elif 'issue:' in line or 'problem:' in line or 'gap:' in line:
                    issue = line.split(':', 1)[1].strip()
                    if issue:
                        issues.append(issue)
            
            return score, issues
            
        except Exception as e:
            logger.warning(f"Failed to parse validation response: {e}")
            return 0.5, [f"Parsing error: {str(e)}"]
    
    def validate_report_quality(self, report_content: str, criteria: ValidationCriteria) -> Dict[str, Any]:
        """
        Validate overall report quality against criteria.
        
        Args:
            report_content: Full report content
            criteria: Validation criteria
            
        Returns:
            Quality assessment results
        """
        results = {
            'length_check': len(report_content) >= criteria.min_length and len(report_content) <= criteria.max_length,
            'content_length': len(report_content),
            'word_count': len(report_content.split()),
            'issues': []
        }
        
        # Check length
        if len(report_content) < criteria.min_length:
            results['issues'].append(f"Content too short: {len(report_content)} chars (min: {criteria.min_length})")
        
        if len(report_content) > criteria.max_length:
            results['issues'].append(f"Content too long: {len(report_content)} chars (max: {criteria.max_length})")
        
        # Check required keywords
        if criteria.required_keywords:
            missing_keywords = []
            for keyword in criteria.required_keywords:
                if keyword.lower() not in report_content.lower():
                    missing_keywords.append(keyword)
            
            if missing_keywords:
                results['issues'].append(f"Missing required keywords: {missing_keywords}")
        
        # Check forbidden keywords
        if criteria.forbidden_keywords:
            found_forbidden = []
            for keyword in criteria.forbidden_keywords:
                if keyword.lower() in report_content.lower():
                    found_forbidden.append(keyword)
            
            if found_forbidden:
                results['issues'].append(f"Found forbidden keywords: {found_forbidden}")
        
        results['quality_score'] = 1.0 - (len(results['issues']) * 0.1)  # Reduce score for each issue
        results['quality_score'] = max(0.0, results['quality_score'])
        
        return results


# Global validator instance
content_validator = ContentValidator() 