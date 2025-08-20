"""
MLOps Model Monitoring for the Deep Research Production System.
Tracks model performance, drift detection, and quality metrics.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np
from dataclasses import dataclass, asdict

from ..src.config.settings import config
from ..src.utils.monitoring import metrics_collector

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Model performance metrics."""
    model_name: str
    timestamp: str
    response_time: float
    success_rate: float
    error_rate: float
    token_usage: int
    quality_score: float
    hallucination_score: float
    coherence_score: float


@dataclass
class DriftMetrics:
    """Model drift detection metrics."""
    model_name: str
    timestamp: str
    response_time_drift: float
    quality_score_drift: float
    error_rate_drift: float
    drift_detected: bool
    drift_severity: str  # low, medium, high


class ModelMonitor:
    """Monitor for tracking model performance and detecting drift."""
    
    def __init__(self, model_name: str = "gemini-1.5-flash-latest"):
        """Initialize model monitor."""
        self.model_name = model_name
        self.metrics_history: List[ModelMetrics] = []
        self.drift_history: List[DriftMetrics] = []
        self.baseline_metrics: Optional[ModelMetrics] = None
        
        # Drift detection thresholds
        self.response_time_threshold = 0.2  # 20% increase
        self.quality_threshold = 0.1  # 10% decrease
        self.error_rate_threshold = 0.15  # 15% increase
        
        logger.info(f"Model monitor initialized for {model_name}")
    
    def record_model_call(self, response_time: float, success: bool, 
                         token_usage: int, quality_score: float = None) -> None:
        """
        Record a model call for monitoring.
        
        Args:
            response_time: Response time in seconds
            success: Whether the call was successful
            token_usage: Number of tokens used
            quality_score: Optional quality score
        """
        # Calculate metrics
        total_calls = len(self.metrics_history) + 1
        success_count = sum(1 for m in self.metrics_history if m.success_rate > 0.5) + (1 if success else 0)
        success_rate = success_count / total_calls
        error_rate = 1 - success_rate
        
        # Create metrics entry
        metrics = ModelMetrics(
            model_name=self.model_name,
            timestamp=datetime.now().isoformat(),
            response_time=response_time,
            success_rate=success_rate,
            error_rate=error_rate,
            token_usage=token_usage,
            quality_score=quality_score or 0.5,
            hallucination_score=0.0,  # Would need separate validation
            coherence_score=0.0  # Would need separate validation
        )
        
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        logger.debug(f"Recorded model call: {response_time:.3f}s, success: {success}")
    
    def establish_baseline(self, window_days: int = 7) -> None:
        """
        Establish baseline metrics from recent history.
        
        Args:
            window_days: Number of days to use for baseline
        """
        cutoff_date = datetime.now() - timedelta(days=window_days)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_date
        ]
        
        if not recent_metrics:
            logger.warning("No recent metrics available for baseline")
            return
        
        # Calculate baseline metrics
        avg_response_time = np.mean([m.response_time for m in recent_metrics])
        avg_success_rate = np.mean([m.success_rate for m in recent_metrics])
        avg_error_rate = np.mean([m.error_rate for m in recent_metrics])
        avg_quality_score = np.mean([m.quality_score for m in recent_metrics])
        
        self.baseline_metrics = ModelMetrics(
            model_name=self.model_name,
            timestamp=datetime.now().isoformat(),
            response_time=avg_response_time,
            success_rate=avg_success_rate,
            error_rate=avg_error_rate,
            token_usage=0,
            quality_score=avg_quality_score,
            hallucination_score=0.0,
            coherence_score=0.0
        )
        
        logger.info(f"Baseline established with {len(recent_metrics)} data points")
    
    def detect_drift(self) -> Optional[DriftMetrics]:
        """
        Detect model drift by comparing current metrics to baseline.
        
        Returns:
            Drift metrics if drift detected, None otherwise
        """
        if not self.baseline_metrics or not self.metrics_history:
            return None
        
        # Get recent metrics (last 24 hours)
        cutoff_date = datetime.now() - timedelta(hours=24)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_date
        ]
        
        if not recent_metrics:
            return None
        
        # Calculate current averages
        current_response_time = np.mean([m.response_time for m in recent_metrics])
        current_success_rate = np.mean([m.success_rate for m in recent_metrics])
        current_error_rate = np.mean([m.error_rate for m in recent_metrics])
        current_quality_score = np.mean([m.quality_score for m in recent_metrics])
        
        # Calculate drift
        response_time_drift = (current_response_time - self.baseline_metrics.response_time) / self.baseline_metrics.response_time
        quality_score_drift = (self.baseline_metrics.quality_score - current_quality_score) / self.baseline_metrics.quality_score
        error_rate_drift = (current_error_rate - self.baseline_metrics.error_rate) / self.baseline_metrics.error_rate
        
        # Check for drift
        drift_detected = (
            response_time_drift > self.response_time_threshold or
            quality_score_drift > self.quality_threshold or
            error_rate_drift > self.error_rate_threshold
        )
        
        if drift_detected:
            # Determine severity
            max_drift = max(response_time_drift, quality_score_drift, error_rate_drift)
            if max_drift > 0.5:
                severity = "high"
            elif max_drift > 0.25:
                severity = "medium"
            else:
                severity = "low"
            
            drift_metrics = DriftMetrics(
                model_name=self.model_name,
                timestamp=datetime.now().isoformat(),
                response_time_drift=response_time_drift,
                quality_score_drift=quality_score_drift,
                error_rate_drift=error_rate_drift,
                drift_detected=True,
                drift_severity=severity
            )
            
            self.drift_history.append(drift_metrics)
            logger.warning(f"Model drift detected: {severity} severity")
            
            return drift_metrics
        
        return None
    
    def get_performance_summary(self, window_days: int = 7) -> Dict[str, Any]:
        """
        Get performance summary for the specified window.
        
        Args:
            window_days: Number of days to analyze
            
        Returns:
            Performance summary dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=window_days)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_date
        ]
        
        if not recent_metrics:
            return {"error": "No metrics available for the specified window"}
        
        response_times = [m.response_time for m in recent_metrics]
        quality_scores = [m.quality_score for m in recent_metrics]
        success_rates = [m.success_rate for m in recent_metrics]
        
        return {
            "model_name": self.model_name,
            "window_days": window_days,
            "total_calls": len(recent_metrics),
            "avg_response_time": np.mean(response_times),
            "avg_quality_score": np.mean(quality_scores),
            "avg_success_rate": np.mean(success_rates),
            "min_response_time": np.min(response_times),
            "max_response_time": np.max(response_times),
            "response_time_std": np.std(response_times),
            "quality_score_std": np.std(quality_scores),
            "drift_detected": len([d for d in self.drift_history if d.drift_detected])
        }
    
    def export_metrics(self, filepath: str) -> None:
        """
        Export metrics to JSON file.
        
        Args:
            filepath: Output file path
        """
        data = {
            "model_name": self.model_name,
            "baseline_metrics": asdict(self.baseline_metrics) if self.baseline_metrics else None,
            "metrics_history": [asdict(m) for m in self.metrics_history[-100:]],  # Last 100
            "drift_history": [asdict(d) for d in self.drift_history],
            "export_timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Model metrics exported to {filepath}")
    
    def generate_alert(self, drift_metrics: DriftMetrics) -> Dict[str, Any]:
        """
        Generate alert for detected drift.
        
        Args:
            drift_metrics: Detected drift metrics
            
        Returns:
            Alert dictionary
        """
        alert = {
            "alert_type": "model_drift",
            "model_name": self.model_name,
            "timestamp": datetime.now().isoformat(),
            "severity": drift_metrics.drift_severity,
            "drift_metrics": asdict(drift_metrics),
            "recommendations": self._get_drift_recommendations(drift_metrics)
        }
        
        return alert
    
    def _get_drift_recommendations(self, drift_metrics: DriftMetrics) -> List[str]:
        """Get recommendations for addressing drift."""
        recommendations = []
        
        if drift_metrics.response_time_drift > self.response_time_threshold:
            recommendations.append("Consider model optimization or infrastructure scaling")
        
        if drift_metrics.quality_score_drift > self.quality_threshold:
            recommendations.append("Review and update training data or model parameters")
        
        if drift_metrics.error_rate_drift > self.error_rate_threshold:
            recommendations.append("Investigate error patterns and implement error handling")
        
        if not recommendations:
            recommendations.append("Monitor closely for further degradation")
        
        return recommendations


# Global model monitor instance
model_monitor = ModelMonitor() 