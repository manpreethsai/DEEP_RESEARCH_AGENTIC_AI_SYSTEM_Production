"""
Main application entry point for the Deep Research Production System.
Provides the primary interface for running research reports.
"""

import logging
import argparse
import json
from pathlib import Path
from datetime import datetime

from .config.settings import config
from .agents.research_agent import research_agent
from .utils.monitoring import metrics_collector
from .utils.cache import cache_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format=config.logging.format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.logs_path / 'deep_research.log')
    ]
)

logger = logging.getLogger(__name__)


def setup_environment():
    """Setup the production environment."""
    logger.info("Setting up Deep Research Production Environment")
    
    # Validate configuration
    try:
        config.validate()
        logger.info("Configuration validation passed")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Create necessary directories
    config.create_directories()
    logger.info("Directory structure created")
    
    # Initialize cache cleanup
    cache_manager.cleanup_expired()
    logger.info("Cache cleanup completed")


def run_research_report(topic: str, output_file: str = None, enable_validation: bool = True) -> dict:
    """
    Run a complete research report generation.
    
    Args:
        topic: Research topic
        output_file: Optional output file path
        enable_validation: Whether to enable content validation
        
    Returns:
        Dictionary containing the report and metadata
    """
    logger.info(f"Starting research report generation for topic: {topic}")
    
    try:
        # Run the research pipeline
        state = research_agent.run_research_pipeline(topic, enable_validation)
        
        # Prepare result
        result = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'status': state.status,
            'report': state.compiled_report,
            'metrics': {
                'total_characters': state.total_characters,
                'processing_time': state.processing_time,
                'sections': len(state.section_titles),
                'errors': len(state.error_messages)
            },
            'system_metrics': metrics_collector.get_metrics(),
            'errors': state.error_messages
        }
        
        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"Report saved to: {output_path}")
        
        logger.info(f"Research report completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Research report generation failed: {e}")
        return {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'status': 'failed',
            'error': str(e),
            'system_metrics': metrics_collector.get_metrics()
        }


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='Deep Research Production System')
    parser.add_argument('topic', help='Research topic')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--no-validation', action='store_true', help='Disable content validation')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--metrics', action='store_true', help='Export metrics after completion')
    
    args = parser.parse_args()
    
    try:
        # Setup environment
        setup_environment()
        
        # Run research report
        result = run_research_report(
            topic=args.topic,
            output_file=args.output,
            enable_validation=not args.no_validation
        )
        
        # Export metrics if requested
        if args.metrics:
            metrics_file = config.data_path / f'metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            metrics_collector.export_metrics(str(metrics_file))
            logger.info(f"Metrics exported to: {metrics_file}")
        
        # Print result summary
        if result['status'] == 'completed':
            print(f"\n✅ Research report completed successfully!")
            print(f"Topic: {result['topic']}")
            print(f"Characters: {result['metrics']['total_characters']}")
            print(f"Processing time: {result['metrics']['processing_time']:.2f}s")
            print(f"Sections: {result['metrics']['sections']}")
            
            if args.output:
                print(f"Report saved to: {args.output}")
            else:
                print("\n" + "="*60)
                print(result['report'])
                print("="*60)
        else:
            print(f"\n❌ Research report failed: {result.get('error', 'Unknown error')}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"\n❌ Application failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 