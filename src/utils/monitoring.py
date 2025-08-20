"""
Monitoring utility for the Deep Research Production System.
Provides metrics collection, performance monitoring, and observability features.
"""

import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
from pathlib import Path

from ..config.settings import config

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collector for system metrics and performance data."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        
        # Performance tracking
        self.performance_data = deque(maxlen=1000)
        self.error_log = deque(maxlen=100)
        
        # Start time for uptime tracking
        self.start_time = time.time()
        
        logger.info("Metrics collector initialized")
    
    def increment(self, metric: str, value: int = 1) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric: Metric name
            value: Increment value
        """
        self.counters[metric] += value
        logger.debug(f"Incremented {metric}: {self.counters[metric]}")
    
    def record_timing(self, metric: str, duration: float) -> None:
        """
        Record timing metric.
        
        Args:
            metric: Metric name
            duration: Duration in seconds
        """
        self.timers[metric].append(duration)
        self.histograms[metric].append(duration)
        
        # Keep only last 1000 values
        if len(self.timers[metric]) > 1000:
            self.timers[metric] = self.timers[metric][-1000:]
        
        logger.debug(f"Recorded timing {metric}: {duration:.3f}s")
    
    def set_gauge(self, metric: str, value: float) -> None:
        """
        Set gauge metric value.
        
        Args:
            metric: Metric name
            value: Gauge value
        """
        self.gauges[metric] = value
        logger.debug(f"Set gauge {metric}: {value}")
    
    def record_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Record error for monitoring.
        
        Args:
            error: Exception that occurred
            context: Additional context
        """
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        self.error_log.append(error_data)
        self.increment('errors')
        
        logger.error(f"Recorded error: {error}")
    
    def record_performance(self, operation: str, duration: float, 
                          success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record performance data for an operation.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            success: Whether operation was successful
            metadata: Additional metadata
        """
        perf_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration': duration,
            'success': success,
            'metadata': metadata or {}
        }
        
        self.performance_data.append(perf_data)
        self.record_timing(f"{operation}_duration", duration)
        
        if success:
            self.increment(f"{operation}_success")
        else:
            self.increment(f"{operation}_failure")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        metrics = {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'uptime': time.time() - self.start_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate timing statistics
        for metric, timings in self.timers.items():
            if timings:
                metrics[f"{metric}_stats"] = {
                    'count': len(timings),
                    'mean': sum(timings) / len(timings),
                    'min': min(timings),
                    'max': max(timings),
                    'p95': self._percentile(timings, 95),
                    'p99': self._percentile(timings, 99)
                }
        
        return metrics
    
    def _percentile(self, values: list, percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def get_performance_summary(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance summary for specific operation or all operations.
        
        Args:
            operation: Specific operation to summarize
            
        Returns:
            Performance summary
        """
        if operation:
            data = [d for d in self.performance_data if d['operation'] == operation]
        else:
            data = list(self.performance_data)
        
        if not data:
            return {}
        
        durations = [d['duration'] for d in data]
        success_count = sum(1 for d in data if d['success'])
        failure_count = len(data) - success_count
        
        return {
            'operation': operation or 'all',
            'total_operations': len(data),
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': success_count / len(data) if data else 0,
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p95_duration': self._percentile(durations, 95),
            'p99_duration': self._percentile(durations, 99)
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary."""
        if not self.error_log:
            return {}
        
        error_types = defaultdict(int)
        for error in self.error_log:
            error_types[error['error_type']] += 1
        
        return {
            'total_errors': len(self.error_log),
            'error_types': dict(error_types),
            'recent_errors': list(self.error_log)[-10:]  # Last 10 errors
        }
    
    def export_metrics(self, filepath: str) -> None:
        """
        Export metrics to JSON file.
        
        Args:
            filepath: Output file path
        """
        metrics_data = {
            'metrics': self.get_metrics(),
            'performance_summary': self.get_performance_summary(),
            'error_summary': self.get_error_summary(),
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        logger.info(f"Metrics exported to {filepath}")
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.counters.clear()
        self.timers.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.performance_data.clear()
        self.error_log.clear()
        self.start_time = time.time()
        
        logger.info("Metrics reset")


class PerformanceMonitor:
    """Context manager for monitoring performance of code blocks."""
    
    def __init__(self, operation: str, metrics_collector: MetricsCollector):
        """
        Initialize performance monitor.
        
        Args:
            operation: Operation name
            metrics_collector: Metrics collector instance
        """
        self.operation = operation
        self.metrics = metrics_collector
        self.start_time = None
    
    def __enter__(self):
        """Start monitoring."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End monitoring and record metrics."""
        if self.start_time:
            duration = time.time() - self.start_time
            success = exc_type is None
            
            self.metrics.record_performance(
                operation=self.operation,
                duration=duration,
                success=success
            )
            
            if not success:
                self.metrics.record_error(exc_val, {'operation': self.operation})


# Global metrics collector instance
metrics_collector = MetricsCollector() 