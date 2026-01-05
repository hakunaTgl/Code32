# Code32 - Python Code Optimization Guide

## Overview

This guide covers the complete optimization infrastructure for Python projects, including automated testing, code quality checks, performance monitoring, and security scanning.

## Setup Instructions

### Installation

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install quality tools
pip install black isort flake8 pylint pytest pytest-cov bandit radon
```

### GitHub Actions Setup

1. Workflows run automatically on every push and PR
2. Uses Python 3.9, 3.10, 3.11, 3.12 for multi-version testing
3. Generates coverage reports and uploads to Codecov

## Tools Included

### Code Formatting

**Black** - Automatic code formatting
```bash
black .  # Format all files
black --check .  # Check without modifying
```

**isort** - Import statement organization
```bash
isort .  # Sort imports
isort --check .  # Check without modifying
```

### Linting

**Flake8** - Style guide enforcement
```bash
flake8 .  # Check for style violations
```

**Pylint** - Static code analysis
```bash
pylint **/*.py  # Detailed analysis
```

### Testing

**pytest** - Unit testing framework
```bash
pytest  # Run all tests
pytest --cov  # Run with coverage
pytest tests/  # Run specific directory
```

### Complexity Analysis

**Radon** - Cyclomatic complexity analyzer
```bash
radon cc . -a  # Show complexity ratings
radon mi . -j  # Maintainability index
```

### Performance Analysis

**Custom Script**
```bash
python .github/scripts/python-performance-analysis.py
```

Analyzes:
- Large files (>500 lines) needing refactoring
- High complexity functions
- Code structure and organization

### Security

**Bandit** - Security vulnerability scanner
```bash
bandit -r .  # Scan for security issues
```

## Pre-commit Hook Usage

Hooks automatically run before each commit:

```bash
# Normal commit (hooks run automatically)
git commit -m "message"

# Skip hooks if needed
git commit --no-verify -m "message"

# Update hooks to latest versions
pre-commit autoupdate
```

## Local Development Workflow

```bash
# 1. Format code
black .
isort .

# 2. Check code quality
flake8 .
pylint src/

# 3. Run tests
pytest --cov

# 4. Analyze complexity
radon cc . -a
radon mi .

# 5. Security scan
bandit -r .

# 6. Performance analysis
python .github/scripts/python-performance-analysis.py

# 7. Commit (hooks will run again)
git add .
git commit -m "Feature: description"
```

## Project Structure

Recommended layout:
```
Code32/
├── .github/
│   ├── workflows/
│   │   └── python-quality.yml
│   └── scripts/
│       └── python-performance-analysis.py
├── src/              # Source code
├── tests/            # Unit tests
├── .pre-commit-config.yaml
├── setup.cfg         # Python configuration
└── PYTHON_OPTIMIZATION_GUIDE.md
```

## Configuration Files

### setup.cfg
Centralized configuration for all tools:
- Black: line_length = 100
- isort: profile = black
- Flake8: max-complexity = 10
- pytest: coverage settings

### .pre-commit-config.yaml
Local hooks that run before commit:
- Black formatting
- isort import sorting
- Flake8 linting
- MyPy type checking
- Bandit security scanning

### python-quality.yml
CI/CD workflow for:
- Multi-version testing (3.9 - 3.12)
- Coverage reporting to Codecov
- Security scanning (Bandit, Safety)
- Complexity analysis (Radon)

## Optimization Best Practices

### 1. Code Structure
- Keep functions under 50 lines
- Keep cyclomatic complexity < 10
- Use descriptive variable names
- Follow DRY (Don't Repeat Yourself)

### 2. Performance
- Use `functools.lru_cache` for expensive operations
- Profile code: `python -m cProfile -s cumtime script.py`
- Use generators for large data processing
- Consider NumPy for numerical operations

### 3. Maintainability
- Write docstrings for all functions
- Keep lines under 100 characters
- Use type hints (for Python 3.9+)
- Organize imports with isort

### 4. Testing
- Aim for >80% code coverage
- Write tests before features (TDD)
- Use fixtures for setup/teardown
- Test edge cases and error conditions

## Common Issues

### Pre-commit hooks failing
```bash
# Force reformat
black .
isort .

# Then commit
git add .
git commit -m "style: auto-format"
```

### Tests not found
```bash
# Ensure tests directory exists
mkdir -p tests/
touch tests/__init__.py

# Check pytest configuration
pytest --collect-only
```

### Complexity too high
```bash
# Identify problem functions
radon cc . -a

# Refactor into smaller functions
# Extract common logic
# Use helper methods
```

## Integration with Other Repos

This Python optimization setup can be applied to:
- **BDB-SQUAD** (Python)
- **forensic-tool** (Python)
- Any other Python projects

Simply copy the configuration files and adjust paths as needed.

## CI/CD Pipeline

The pipeline runs on:
- Every push to main/develop
- Every pull request
- Generates reports for review
- Fails if coverage drops significantly
- Checks all Python versions

## Metrics Tracking

Metrics are saved to `.metrics.json`:
- Code structure analysis
- Complexity trends
- File size growth
- Historical comparisons

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [Radon Documentation](https://radon.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)

---

**Last Updated**: January 5, 2026
**Maintained by**: Hakuna (hakunaTgl)
