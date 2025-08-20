"""
LLMOps Prompt Engineering for the Deep Research Production System.
Manages prompt versioning, optimization, and A/B testing.
"""

import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from ..src.config.settings import config
from ..src.core.llm_service import llm_service
from ..src.utils.monitoring import metrics_collector

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    """Versioned prompt template."""
    version: str
    prompt_text: str
    created_at: str
    description: str
    tags: List[str]
    performance_metrics: Dict[str, float]
    is_active: bool = False


@dataclass
class PromptTest:
    """A/B test for prompt comparison."""
    test_id: str
    prompt_a: str
    prompt_b: str
    test_topic: str
    created_at: str
    results: Dict[str, Any]
    winner: Optional[str] = None


class PromptEngineer:
    """Engineer for managing and optimizing prompts."""
    
    def __init__(self):
        """Initialize prompt engineer."""
        self.prompts: Dict[str, PromptVersion] = {}
        self.tests: Dict[str, PromptTest] = {}
        self.prompt_history: List[PromptVersion] = []
        
        logger.info("Prompt Engineer initialized")
    
    def register_prompt(self, prompt_name: str, prompt_text: str, 
                       description: str = "", tags: List[str] = None) -> str:
        """
        Register a new prompt version.
        
        Args:
            prompt_name: Name of the prompt
            prompt_text: Prompt text
            description: Description of the prompt
            tags: Tags for categorization
            
        Returns:
            Version hash
        """
        # Generate version hash
        version_hash = hashlib.md5(prompt_text.encode()).hexdigest()[:8]
        
        # Create prompt version
        prompt_version = PromptVersion(
            version=version_hash,
            prompt_text=prompt_text,
            created_at=datetime.now().isoformat(),
            description=description,
            tags=tags or [],
            performance_metrics={},
            is_active=False
        )
        
        # Store prompt
        key = f"{prompt_name}_{version_hash}"
        self.prompts[key] = prompt_version
        self.prompt_history.append(prompt_version)
        
        logger.info(f"Registered prompt: {prompt_name} v{version_hash}")
        return version_hash
    
    def activate_prompt(self, prompt_name: str, version: str) -> bool:
        """
        Activate a specific prompt version.
        
        Args:
            prompt_name: Name of the prompt
            version: Version to activate
            
        Returns:
            True if activation successful
        """
        key = f"{prompt_name}_{version}"
        if key not in self.prompts:
            logger.error(f"Prompt not found: {key}")
            return False
        
        # Deactivate all other versions
        for k, prompt in self.prompts.items():
            if k.startswith(f"{prompt_name}_"):
                prompt.is_active = False
        
        # Activate specified version
        self.prompts[key].is_active = True
        logger.info(f"Activated prompt: {prompt_name} v{version}")
        return True
    
    def get_active_prompt(self, prompt_name: str) -> Optional[PromptVersion]:
        """
        Get the currently active prompt version.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Active prompt version or None
        """
        for key, prompt in self.prompts.items():
            if key.startswith(f"{prompt_name}_") and prompt.is_active:
                return prompt
        return None
    
    def update_prompt_metrics(self, prompt_name: str, version: str, 
                             metrics: Dict[str, float]) -> None:
        """
        Update performance metrics for a prompt version.
        
        Args:
            prompt_name: Name of the prompt
            version: Version to update
            metrics: Performance metrics
        """
        key = f"{prompt_name}_{version}"
        if key in self.prompts:
            self.prompts[key].performance_metrics.update(metrics)
            logger.debug(f"Updated metrics for {prompt_name} v{version}")
    
    def create_ab_test(self, prompt_name: str, prompt_a: str, prompt_b: str,
                       test_topic: str) -> str:
        """
        Create an A/B test for prompt comparison.
        
        Args:
            prompt_name: Name of the prompt
            prompt_a: First prompt version
            prompt_b: Second prompt version
            test_topic: Topic to test with
            
        Returns:
            Test ID
        """
        test_id = f"test_{prompt_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test = PromptTest(
            test_id=test_id,
            prompt_a=prompt_a,
            prompt_b=prompt_b,
            test_topic=test_topic,
            created_at=datetime.now().isoformat(),
            results={}
        )
        
        self.tests[test_id] = test
        logger.info(f"Created A/B test: {test_id}")
        return test_id
    
    def run_ab_test(self, test_id: str) -> Dict[str, Any]:
        """
        Run an A/B test and compare results.
        
        Args:
            test_id: Test ID to run
            
        Returns:
            Test results
        """
        if test_id not in self.tests:
            raise ValueError(f"Test not found: {test_id}")
        
        test = self.tests[test_id]
        logger.info(f"Running A/B test: {test_id}")
        
        try:
            # Test prompt A
            start_time = datetime.now()
            response_a = llm_service.generate_content(test.prompt_a.format(topic=test.test_topic))
            time_a = (datetime.now() - start_time).total_seconds()
            
            # Test prompt B
            start_time = datetime.now()
            response_b = llm_service.generate_content(test.prompt_b.format(topic=test.test_topic))
            time_b = (datetime.now() - start_time).total_seconds()
            
            # Analyze results
            results = {
                "prompt_a": {
                    "response": response_a,
                    "response_time": time_a,
                    "length": len(response_a),
                    "quality_score": self._assess_quality(response_a)
                },
                "prompt_b": {
                    "response": response_b,
                    "response_time": time_b,
                    "length": len(response_b),
                    "quality_score": self._assess_quality(response_b)
                }
            }
            
            # Determine winner
            score_a = results["prompt_a"]["quality_score"]
            score_b = results["prompt_b"]["quality_score"]
            
            if score_a > score_b:
                winner = "prompt_a"
            elif score_b > score_a:
                winner = "prompt_b"
            else:
                winner = "tie"
            
            test.results = results
            test.winner = winner
            
            logger.info(f"A/B test completed. Winner: {winner}")
            return results
            
        except Exception as e:
            logger.error(f"A/B test failed: {e}")
            test.results = {"error": str(e)}
            return {"error": str(e)}
    
    def _assess_quality(self, response: str) -> float:
        """
        Assess the quality of a response.
        
        Args:
            response: Response to assess
            
        Returns:
            Quality score (0-1)
        """
        # Simple quality assessment based on length and structure
        if not response:
            return 0.0
        
        # Length score (prefer longer responses)
        length_score = min(len(response) / 1000, 1.0)
        
        # Structure score (prefer well-formatted responses)
        structure_score = 0.5
        if "\n\n" in response:  # Paragraphs
            structure_score += 0.2
        if "##" in response:  # Headers
            structure_score += 0.2
        if "(" in response and ")" in response:  # Citations
            structure_score += 0.1
        
        # Combine scores
        quality_score = (length_score + structure_score) / 2
        return min(quality_score, 1.0)
    
    def optimize_prompt(self, base_prompt: str, test_topics: List[str]) -> str:
        """
        Optimize a prompt using multiple test topics.
        
        Args:
            base_prompt: Base prompt to optimize
            test_topics: Topics to test with
            
        Returns:
            Optimized prompt
        """
        logger.info(f"Optimizing prompt with {len(test_topics)} test topics")
        
        # Test variations
        variations = [
            base_prompt,
            base_prompt + "\n\nPlease provide a comprehensive and detailed response.",
            base_prompt + "\n\nUse a professional and analytical tone.",
            base_prompt + "\n\nInclude specific examples and evidence where possible."
        ]
        
        best_prompt = base_prompt
        best_score = 0.0
        
        for i, variation in enumerate(variations):
            total_score = 0.0
            
            for topic in test_topics[:3]:  # Test with first 3 topics
                try:
                    response = llm_service.generate_content(variation.format(topic=topic))
                    score = self._assess_quality(response)
                    total_score += score
                except Exception as e:
                    logger.warning(f"Failed to test variation {i}: {e}")
                    continue
            
            avg_score = total_score / min(len(test_topics), 3)
            
            if avg_score > best_score:
                best_score = avg_score
                best_prompt = variation
            
            logger.info(f"Variation {i} score: {avg_score:.3f}")
        
        logger.info(f"Optimization complete. Best score: {best_score:.3f}")
        return best_prompt
    
    def get_prompt_analytics(self, prompt_name: str = None) -> Dict[str, Any]:
        """
        Get analytics for prompts.
        
        Args:
            prompt_name: Specific prompt name or None for all
            
        Returns:
            Analytics dictionary
        """
        if prompt_name:
            # Analytics for specific prompt
            versions = [p for k, p in self.prompts.items() if k.startswith(f"{prompt_name}_")]
        else:
            # Analytics for all prompts
            versions = list(self.prompts.values())
        
        analytics = {
            "total_prompts": len(versions),
            "active_prompts": len([p for p in versions if p.is_active]),
            "avg_performance": {},
            "recent_activity": []
        }
        
        if versions:
            # Calculate average performance metrics
            all_metrics = [p.performance_metrics for p in versions if p.performance_metrics]
            if all_metrics:
                avg_metrics = {}
                for key in all_metrics[0].keys():
                    values = [m.get(key, 0) for m in all_metrics]
                    avg_metrics[key] = sum(values) / len(values)
                analytics["avg_performance"] = avg_metrics
            
            # Recent activity
            recent_prompts = sorted(versions, key=lambda x: x.created_at, reverse=True)[:10]
            analytics["recent_activity"] = [
                {
                    "name": k.split("_")[0],
                    "version": p.version,
                    "created_at": p.created_at,
                    "is_active": p.is_active
                }
                for k, p in self.prompts.items()
                if p in recent_prompts
            ]
        
        return analytics
    
    def export_prompts(self, filepath: str) -> None:
        """
        Export prompts to JSON file.
        
        Args:
            filepath: Output file path
        """
        data = {
            "prompts": {k: asdict(v) for k, v in self.prompts.items()},
            "tests": {k: asdict(v) for k, v in self.tests.items()},
            "export_timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Prompts exported to {filepath}")


# Global prompt engineer instance
prompt_engineer = PromptEngineer() 