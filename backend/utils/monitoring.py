"""
Production monitoring and logging utilities for 3C analysis system.
Provides comprehensive logging, performance monitoring, and error tracking.
"""

import asyncio
import logging
import time
import functools
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from contextlib import asynccontextmanager

# Configure structured logging for production
def setup_production_logging():
    """Configure production-ready logging with structured format"""
    
    # Create custom formatter for structured logging
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            # Add structured fields to log record
            record.timestamp = datetime.utcnow().isoformat()
            record.service = "3c_analysis_system"
            
            # Add context if available
            if hasattr(record, 'job_id'):
                record.job_id = record.job_id
            if hasattr(record, 'analysis_type'):
                record.analysis_type = record.analysis_type
            if hasattr(record, 'target_market'):
                record.target_market = record.target_market
                
            return super().format(record)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler with structured format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = StructuredFormatter(
        '%(timestamp)s - %(service)s - %(name)s - %(levelname)s - '
        'job_id=%(job_id)s - analysis_type=%(analysis_type)s - '
        'target_market=%(target_market)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


class PerformanceMonitor:
    """Monitor performance metrics for 3C analysis operations"""
    
    def __init__(self):
        self.metrics = {}
        self.logger = logging.getLogger(__name__)
    
    def record_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a performance metric"""
        timestamp = datetime.utcnow().isoformat()
        
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        metric_entry = {
            'timestamp': timestamp,
            'value': value,
            'tags': tags or {}
        }
        
        self.metrics[metric_name].append(metric_entry)
        
        # Log metric for monitoring systems
        self.logger.info(
            f"Performance metric recorded: {metric_name}={value}",
            extra={
                'metric_name': metric_name,
                'metric_value': value,
                'metric_tags': tags or {},
                'metric_timestamp': timestamp
            }
        )
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        if metric_name not in self.metrics:
            return {}
        
        values = [entry['value'] for entry in self.metrics[metric_name]]
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1] if values else None,
            'latest_timestamp': self.metrics[metric_name][-1]['timestamp'] if self.metrics[metric_name] else None
        }
    
    def clear_metrics(self):
        """Clear all recorded metrics"""
        self.metrics.clear()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """Decorator to monitor function execution time"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                performance_monitor.record_metric(
                    f"{metric_name}_duration_seconds",
                    execution_time,
                    {**(tags or {}), 'status': 'success'}
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                performance_monitor.record_metric(
                    f"{metric_name}_duration_seconds",
                    execution_time,
                    {**(tags or {}), 'status': 'error', 'error_type': type(e).__name__}
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                performance_monitor.record_metric(
                    f"{metric_name}_duration_seconds",
                    execution_time,
                    {**(tags or {}), 'status': 'success'}
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                performance_monitor.record_metric(
                    f"{metric_name}_duration_seconds",
                    execution_time,
                    {**(tags or {}), 'status': 'error', 'error_type': type(e).__name__}
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def workflow_monitoring_context(job_id: str, analysis_type: str, target_market: str):
    """Context manager for workflow-level monitoring"""
    logger = logging.getLogger(__name__)
    
    # Add context to logger
    logger = logging.LoggerAdapter(logger, {
        'job_id': job_id,
        'analysis_type': analysis_type,
        'target_market': target_market
    })
    
    start_time = time.time()
    
    try:
        logger.info("Starting workflow execution")
        yield logger
        
        execution_time = time.time() - start_time
        performance_monitor.record_metric(
            "workflow_duration_seconds",
            execution_time,
            {
                'job_id': job_id,
                'analysis_type': analysis_type,
                'target_market': target_market,
                'status': 'success'
            }
        )
        
        logger.info(f"Workflow completed successfully in {execution_time:.2f} seconds")
        
    except Exception as e:
        execution_time = time.time() - start_time
        performance_monitor.record_metric(
            "workflow_duration_seconds",
            execution_time,
            {
                'job_id': job_id,
                'analysis_type': analysis_type,
                'target_market': target_market,
                'status': 'error',
                'error_type': type(e).__name__
            }
        )
        
        logger.error(f"Workflow failed after {execution_time:.2f} seconds: {e}", exc_info=True)
        raise


class ErrorTracker:
    """Track and categorize errors for monitoring and alerting"""
    
    def __init__(self):
        self.errors = []
        self.logger = logging.getLogger(__name__)
    
    def record_error(self, error: Exception, context: Dict[str, Any]):
        """Record an error with context for analysis"""
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'severity': self._determine_severity(error, context)
        }
        
        self.errors.append(error_entry)
        
        # Log error with context
        self.logger.error(
            f"Error recorded: {error_entry['error_type']} - {error_entry['error_message']}",
            extra={
                'error_type': error_entry['error_type'],
                'error_severity': error_entry['severity'],
                'error_context': context
            },
            exc_info=True
        )
    
    def _determine_severity(self, error: Exception, context: Dict[str, Any]) -> str:
        """Determine error severity based on error type and context"""
        # Critical errors that stop the entire workflow
        critical_errors = [
            'SystemExit',
            'KeyboardInterrupt',
            'MemoryError',
            'OSError'
        ]
        
        # High severity errors that affect major functionality
        high_severity_errors = [
            'ConnectionError',
            'TimeoutError',
            'AuthenticationError',
            'PermissionError'
        ]
        
        error_type = type(error).__name__
        
        if error_type in critical_errors:
            return 'critical'
        elif error_type in high_severity_errors:
            return 'high'
        elif 'agent' in context.get('component', '').lower():
            return 'medium'  # Agent failures are medium severity due to fallback handling
        else:
            return 'low'
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recorded errors"""
        if not self.errors:
            return {'total_errors': 0}
        
        error_counts = {}
        severity_counts = {}
        
        for error in self.errors:
            error_type = error['error_type']
            severity = error['severity']
            
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_errors': len(self.errors),
            'error_types': error_counts,
            'severity_distribution': severity_counts,
            'latest_error': self.errors[-1] if self.errors else None
        }


# Global error tracker instance
error_tracker = ErrorTracker()


def log_error_with_context(error: Exception, **context):
    """Convenience function to log errors with context"""
    error_tracker.record_error(error, context)


# Health check utilities
class HealthChecker:
    """Monitor system health and readiness"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check API dependencies
        health_status['components']['tavily_api'] = await self._check_tavily_api()
        health_status['components']['openai_api'] = await self._check_openai_api()
        
        # Check system resources
        health_status['components']['memory'] = self._check_memory_usage()
        health_status['components']['performance'] = self._check_performance_metrics()
        
        # Determine overall status
        component_statuses = [comp['status'] for comp in health_status['components'].values()]
        if 'critical' in component_statuses:
            health_status['overall_status'] = 'critical'
        elif 'degraded' in component_statuses:
            health_status['overall_status'] = 'degraded'
        
        return health_status
    
    async def _check_tavily_api(self) -> Dict[str, Any]:
        """Check Tavily API availability"""
        try:
            # This would be a simple API health check
            # For now, just check if API key is configured
            import os
            if os.getenv("TAVILY_API_KEY"):
                return {'status': 'healthy', 'message': 'API key configured'}
            else:
                return {'status': 'critical', 'message': 'API key not configured'}
        except Exception as e:
            return {'status': 'critical', 'message': f'API check failed: {e}'}
    
    async def _check_openai_api(self) -> Dict[str, Any]:
        """Check OpenAI API availability"""
        try:
            import os
            if os.getenv("OPENAI_API_KEY"):
                return {'status': 'healthy', 'message': 'API key configured'}
            else:
                return {'status': 'critical', 'message': 'API key not configured'}
        except Exception as e:
            return {'status': 'critical', 'message': f'API check failed: {e}'}
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                status = 'critical'
            elif memory.percent > 75:
                status = 'degraded'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'usage_percent': memory.percent,
                'available_gb': memory.available / (1024**3)
            }
        except ImportError:
            return {'status': 'unknown', 'message': 'psutil not available'}
        except Exception as e:
            return {'status': 'error', 'message': f'Memory check failed: {e}'}
    
    def _check_performance_metrics(self) -> Dict[str, Any]:
        """Check recent performance metrics"""
        try:
            workflow_summary = performance_monitor.get_metric_summary('workflow_duration_seconds')
            
            if not workflow_summary:
                return {'status': 'unknown', 'message': 'No performance data available'}
            
            avg_duration = workflow_summary.get('avg', 0)
            
            if avg_duration > 300:  # 5 minutes
                status = 'degraded'
            elif avg_duration > 600:  # 10 minutes
                status = 'critical'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'avg_workflow_duration': avg_duration,
                'workflow_count': workflow_summary.get('count', 0)
            }
        except Exception as e:
            return {'status': 'error', 'message': f'Performance check failed: {e}'}


# Global health checker instance
health_checker = HealthChecker()