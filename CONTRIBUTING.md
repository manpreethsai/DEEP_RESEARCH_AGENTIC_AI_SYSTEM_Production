# Contributing to Deep Research Production System

Thank you for your interest in contributing to the Deep Research Production System! This document provides guidelines and information for contributors.

## 📚 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Security](#security)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

## 🤝 Code of Conduct

This project adheres to a Code of Conduct that we expect all contributors to follow:

- **Be respectful** and inclusive in all communications
- **Be collaborative** and help others learn and grow
- **Be constructive** in feedback and discussions
- **Be patient** with newcomers and different skill levels
- **Be professional** in all project-related interactions

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ (3.11 recommended)
- Docker and Docker Compose
- Git
- API keys for Gemini and Tavily

### Setting Up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/deep-research-production.git
   cd deep-research-production
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set Up Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

6. **Start Development Services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

## 🔄 Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/`: Feature development branches
- `bugfix/`: Bug fix branches
- `hotfix/`: Critical production fixes

### Workflow Steps

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following our coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Locally**
   ```bash
   # Run all tests
   pytest tests/ -v --cov=src
   
   # Run linting
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   
   # Run security checks
   bandit -r src/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create PR through GitHub UI
   ```

## 📝 Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) Python style guide
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [Flake8](https://flake8.pycqa.org/) for linting
- Use [MyPy](http://mypy-lang.org/) for type checking

### Code Organization

```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import requests
from dataclasses import dataclass

# Local imports
from src.config.settings import Config
from src.models.state import AgentState
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `ResearchAgent`)
- **Functions/Variables**: `snake_case` (e.g., `generate_report`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private methods**: `_leading_underscore` (e.g., `_internal_method`)

### Documentation

- Use **docstrings** for all public functions and classes
- Follow [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) docstrings
- Include type hints for all function parameters and return values

```python
def generate_report(topic: str, max_sections: int = 5) -> Dict[str, Any]:
    """Generate a comprehensive research report on the given topic.
    
    Args:
        topic: The research topic to investigate
        max_sections: Maximum number of sections to include
        
    Returns:
        A dictionary containing the generated report data
        
    Raises:
        ValueError: If topic is empty or invalid
        APIError: If external API calls fail
    """
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for system components
├── performance/    # Performance and benchmark tests
├── fixtures/       # Test data and fixtures
└── conftest.py     # Pytest configuration
```

### Writing Tests

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions
- **Mocking**: Use `unittest.mock` for external dependencies

```python
import pytest
from unittest.mock import Mock, patch
from src.agents.research_agent import ResearchAgent

class TestResearchAgent:
    def test_generate_planning_queries(self):
        """Test planning query generation."""
        agent = ResearchAgent()
        result = agent.generate_planning_queries("AI in healthcare")
        assert len(result) > 0
        assert all(isinstance(q, str) for q in result)
    
    @patch('src.core.llm_service.LLMService.generate_content')
    def test_with_mocked_llm(self, mock_llm):
        """Test with mocked LLM service."""
        mock_llm.return_value = "Mocked response"
        # Test implementation
```

### Test Coverage

- Maintain minimum **80% test coverage**
- Critical components should have **90%+ coverage**
- Use `pytest --cov=src --cov-report=html` to generate coverage reports

## 📖 Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings and inline comments
2. **API Documentation**: Function and class documentation
3. **User Documentation**: Usage guides and tutorials
4. **Developer Documentation**: Architecture and design docs

### Documentation Standards

- Keep documentation **up-to-date** with code changes
- Use **clear, concise language**
- Include **examples** where helpful
- Link to **relevant resources**

## 🔒 Security

### Security Guidelines

- **Never commit** API keys, passwords, or sensitive data
- Use **environment variables** for configuration
- **Validate inputs** to prevent injection attacks
- **Review dependencies** for security vulnerabilities
- **Report security issues** privately to maintainers

### Security Tools

Our CI/CD pipeline includes:
- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner
- **Trivy**: Container security scanner
- **Gitleaks**: Secret detection

## 🔄 Pull Request Process

### Before Submitting

- [ ] **Tests pass**: All automated tests are passing
- [ ] **Code quality**: Linting and formatting checks pass
- [ ] **Documentation**: Updated relevant documentation
- [ ] **Security**: No security issues introduced
- [ ] **Breaking changes**: Documented and justified

### PR Template

Use our [PR template](.github/PULL_REQUEST_TEMPLATE.md) when creating pull requests. Include:

- **Clear description** of changes
- **Related issues** links
- **Testing approach** and results
- **Breaking changes** (if any)
- **Security considerations**

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Security review** (if applicable)
4. **Performance review** (for significant changes)
5. **Documentation review**

### Merge Requirements

- ✅ All CI checks passing
- ✅ At least 2 approving reviews
- ✅ No conflicts with target branch
- ✅ Security scan passing
- ✅ Documentation updated

## 🐛 Issue Reporting

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** if possible
3. **Gather relevant information** (logs, environment, steps to reproduce)

### Issue Types

- **🐛 Bug Report**: Use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- **🚀 Feature Request**: Use our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
- **📖 Documentation**: For documentation improvements
- **🔒 Security**: Report security issues privately

### Issue Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working |
| `enhancement` | New feature or request |
| `documentation` | Improvements or additions to docs |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention is needed |
| `priority: high` | High priority issue |
| `security` | Security-related issue |

## 👥 Community

### Getting Help

- **Documentation**: Start with our comprehensive docs
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for general questions
- **Security**: Email security@example.com for security issues

### Communication Guidelines

- **Be specific** when asking questions
- **Provide context** and relevant details
- **Be patient** and respectful
- **Help others** when you can

### Recognition

Contributors are recognized through:
- **Contributor list** in README
- **Release notes** mentioning significant contributions
- **Community highlights** in project updates

## 📊 Development Metrics

We track various metrics to ensure project health:

- **Code coverage**: Target 80%+ overall
- **Performance**: Monitor response times and throughput
- **Security**: Regular vulnerability scans
- **Quality**: Code review feedback and iteration

## 🎯 Contribution Areas

Looking for ways to contribute? Consider these areas:

### 🚀 High Impact
- **Core functionality** improvements
- **Performance optimizations**
- **Security enhancements**
- **Documentation improvements**

### 🌟 Good First Issues
- **Bug fixes** with clear reproduction steps
- **Test additions** for existing functionality
- **Documentation updates**
- **Code formatting** and style improvements

### 🔬 Advanced
- **MLOps integrations**
- **LLMOps improvements**
- **Infrastructure optimizations**
- **New AI model integrations**

## 📝 License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

**Thank you for contributing to the Deep Research Production System!** 🚀

For questions about contributing, please reach out through:
- GitHub Issues for bugs and features
- GitHub Discussions for general questions
- Email for security-related concerns

Your contributions make this project better for everyone! 🎉 