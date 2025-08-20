# 🚀 Deep Research Production System

A production-ready, modular AI-driven research and report generation system with comprehensive MLOps and LLMOps capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [MLOps & LLMOps](#mlops--llmops)
- [Monitoring & Observability](#monitoring--observability)
- [Deployment](#deployment)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The Deep Research Production System is a comprehensive, enterprise-grade solution for automated research and report generation. It transforms the original notebook-based system into a modular, scalable, and production-ready application with full MLOps and LLMOps capabilities.

### Key Improvements from Notebook Version:

- **Modular Architecture**: Clean separation of concerns with dedicated modules
- **Production-Ready**: Docker containerization, monitoring, and error handling
- **MLOps Integration**: Model monitoring, drift detection, and performance tracking, (add: FastAPI, MLFlow), CI/CD pipelines)
- **LLMOps Features**: Prompt versioning, A/B testing, and optimization
- **Scalability**: Redis caching, Celery background tasks, and load balancing
- **Observability**: Comprehensive logging, metrics, and monitoring dashboards

## 🏗️ Architecture

```
deep_research_production/
├── src/                          # Core application code
│   ├── config/                   # Configuration management
│   ├── core/                     # Core services (LLM, Search)
│   ├── agents/                   # Research agent logic
│   ├── models/                   # Data models and state
│   ├── prompts/                  # Prompt templates
│   ├── utils/                    # Utilities (cache, monitoring, validation)
│   └── main.py                   # Application entry point
├── mlops/                        # MLOps components
│   └── model_monitoring.py       # Model performance tracking
├── llmops/                       # LLMOps components
│   └── prompt_engineering.py     # Prompt management and optimization
├── deployment/                   # Deployment configurations
├── tests/                        # Test suite
├── docs/                         # Documentation
├── data/                         # Data storage
├── logs/                         # Application logs
└── cache/                        # Cache storage
```

## ✨ Features

### 🔬 Research Capabilities
- **Automated Research**: Web search integration with Tavily API
- **Intelligent Planning**: Dynamic query generation and report structuring
- **Content Generation**: AI-powered report writing with Gemini
- **Quality Validation**: Fact-checking, coverage analysis, and readability assessment
- **Parallel Processing**: Concurrent section writing for improved performance

### 🏭 Production Features
- **Modular Design**: Clean, maintainable codebase with clear separation of concerns
- **Configuration Management**: Environment-based configuration with validation
- **Caching System**: Multi-level caching with Redis and file-based storage
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Logging**: Structured logging with multiple output formats

### 📊 MLOps Capabilities
- **Model Monitoring**: Real-time performance tracking and alerting
- **Drift Detection**: Automatic detection of model performance degradation
- **Metrics Collection**: Comprehensive metrics for model evaluation
- **Performance Optimization**: Response time and quality optimization

### 🤖 LLMOps Features
- **Prompt Versioning**: Version control for prompt templates
- **A/B Testing**: Systematic prompt comparison and optimization
- **Prompt Engineering**: Automated prompt optimization and testing
- **Quality Assessment**: Automated quality scoring and improvement

### 🔍 Monitoring & Observability
- **Metrics Dashboard**: Grafana dashboards for system monitoring
- **Performance Tracking**: Detailed performance metrics and analysis
- **Health Checks**: Comprehensive health monitoring and alerting
- **Distributed Tracing**: Request tracing across the entire pipeline

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- API Keys: Gemini, Tavily

### 1. Clone and Setup
```bash
git clone <repository-url>
cd deep_research_production

# Set environment variables
export GEMINI_API_KEY="your_gemini_api_key"
export TAVILY_API_KEY="your_tavily_api_key"
```

### 2. Run with Docker
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f deep-research
```

### 3. Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.main "Your research topic"
```

## 📦 Installation

### Option 1: Docker (Recommended)
```bash
# Clone repository
git clone <repository-url>
cd deep_research_production

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d
```

### Option 2: Local Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your_key"
export TAVILY_API_KEY="your_key"
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key

# Optional
OPENAI_API_KEY=your_openai_api_key
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379/0
```

### Configuration Files
- `src/config/settings.py`: Main configuration
- `deployment/prometheus.yml`: Monitoring configuration
- `deployment/nginx.conf`: Reverse proxy configuration

## 📖 Usage

### Command Line Interface
```bash
# Basic usage
python -m src.main "AI in Healthcare"

# With output file
python -m src.main "Machine Learning Trends" --output report.json

# With metrics export
python -m src.main "Quantum Computing" --metrics

# Disable validation
python -m src.main "Topic" --no-validation
```

### Programmatic Usage
```python
from src.agents.research_agent import research_agent

# Run research pipeline
state = research_agent.run_research_pipeline("Your topic")

# Access results
print(state.compiled_report)
print(f"Processing time: {state.processing_time:.2f}s")
```

### API Usage (if FastAPI is implemented)
```bash
# Start API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Make request
curl -X POST "http://localhost:8000/research" \
     -H "Content-Type: application/json" \
     -d '{"topic": "Your research topic"}'
```

## 🔧 API Reference

### Core Classes

#### `ResearchAgent`
Main orchestrator for research and report generation.

```python
from src.agents.research_agent import research_agent

# Run complete pipeline
state = research_agent.run_research_pipeline(topic, enable_validation=True)

# Individual steps
state = research_agent.create_agent_state(topic)
state = research_agent.generate_planning_queries(state)
state = research_agent.generate_report_outline(state)
# ... more steps
```

#### `LLMService`
Handles AI model interactions with caching and monitoring.

```python
from src.core.llm_service import llm_service

# Generate content
response = llm_service.generate_content(prompt)

# Batch generation
responses = llm_service.batch_generate(prompts)

# With fallback
response = llm_service.generate_with_fallback(prompt)
```

#### `SearchService`
Manages web search operations with caching.

```python
from src.core.search_service import search_service

# Single search
results = search_service.search(query)

# Multiple searches
results = search_service.search_multiple(queries)
```

### Configuration Classes

#### `ProductionConfig`
Main configuration class with all settings.

```python
from src.config.settings import config

# Access configuration
print(config.api.gemini_api_key)
print(config.model.gemini_model)
print(config.report.max_sections)
```

## 🏭 MLOps & LLMOps

### Model Monitoring
```python
from mlops.model_monitoring import model_monitor

# Record model call
model_monitor.record_model_call(
    response_time=1.5,
    success=True,
    token_usage=1000,
    quality_score=0.85
)

# Detect drift
drift = model_monitor.detect_drift()

# Get performance summary
summary = model_monitor.get_performance_summary()
```

### Prompt Engineering
```python
from llmops.prompt_engineering import prompt_engineer

# Register prompt
version = prompt_engineer.register_prompt(
    "research_query",
    "Generate research questions for: {topic}",
    "Research query generator"
)

# A/B test prompts
test_id = prompt_engineer.create_ab_test(
    "research_query",
    prompt_a="Generate 5 questions about {topic}",
    prompt_b="Create 5 research queries for {topic}",
    test_topic="AI"
)

results = prompt_engineer.run_ab_test(test_id)
```

## 📊 Monitoring & Observability

### Metrics Dashboard
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### Key Metrics
- **Performance**: Response times, throughput, error rates
- **Quality**: Content quality scores, validation results
- **Resource**: CPU, memory, API usage
- **Business**: Report generation success, user satisfaction

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Service health
docker-compose ps
```

## 🚀 Deployment

### Production Deployment
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale celery-worker=3

# Update configuration
docker-compose down
docker-compose up -d
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods
kubectl logs -f deployment/deep-research
```

### Environment-Specific Configurations
- `docker-compose.dev.yml`: Development environment
- `docker-compose.staging.yml`: Staging environment
- `docker-compose.prod.yml`: Production environment

## 🛠️ Development

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run linting
black src/
flake8 src/
mypy src/
```

### Code Structure
```
src/
├── config/          # Configuration management
├── core/            # Core services (LLM, Search)
├── agents/          # Business logic agents
├── models/          # Data models
├── prompts/         # Prompt templates
├── utils/           # Utilities
└── main.py          # Entry point
```

### Adding New Features
1. **Create module** in appropriate directory
2. **Add tests** in `tests/` directory
3. **Update documentation** in `docs/`
4. **Add monitoring** if needed
5. **Update configuration** if required

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_research_agent.py

# Run integration tests
pytest tests/integration/
```

### Test Structure
```
tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
├── e2e/            # End-to-end tests
└── fixtures/       # Test fixtures
```

### Test Categories
- **Unit Tests**: Individual function/class testing
- **Integration Tests**: Service interaction testing
- **E2E Tests**: Complete pipeline testing
- **Performance Tests**: Load and stress testing

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** Pull Request

### Code Standards
- **Python**: PEP 8, type hints, docstrings
- **Testing**: 90%+ coverage, meaningful tests
- **Documentation**: Clear, comprehensive docs
- **Security**: No hardcoded secrets, proper validation

### Review Process
1. **Automated Checks**: CI/CD pipeline validation
2. **Code Review**: Peer review required
3. **Testing**: All tests must pass
4. **Documentation**: Updated documentation
5. **Security**: Security review for sensitive changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini**: AI model provider
- **Tavily**: Web search API provider
- **Open Source Community**: Various libraries and tools

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: support@your-company.com

---

**Note**: This is a production-ready system designed for enterprise use. For development or testing purposes, consider using the development configuration. 