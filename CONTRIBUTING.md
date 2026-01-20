# Contributing to General Contractor Agent Demo

Thank you for your interest in contributing to the General Contractor Agent Demo! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming and inclusive environment for all contributors. Please be respectful and constructive in all interactions.

## Getting Started

Before contributing, please:

1. Read the [README.md](README.md) to understand the project
2. Check the [QUICKSTART.md](docs/QUICKSTART.md) for setup instructions
3. Review existing [issues](../../issues) and [pull requests](../../pulls)
4. Join discussions to understand current development priorities

## Development Setup

### Prerequisites

- Python 3.13+
- [uv package manager](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 18+
- AWS Account with Bedrock access
- Git

### Setup Instructions

1. **Fork and clone the repository:**

```bash
git clone https://github.com/YOUR_USERNAME/general-contractor-agent-demo.git
cd general-contractor-agent-demo
```

1. **Set up Python environment:**

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

1. **Set up frontend:**

```bash
cd frontend
npm install
cd ..
```

1. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

1. **Verify setup:**

```bash
# Terminal 1: Start backend
python start.py

# Terminal 2: Start frontend
cd frontend && npm run dev
```

Visit <http://localhost:5173> to verify the application is running.

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes**: Fix issues identified in the issue tracker
- **New features**: Add new functionality or agents
- **Documentation**: Improve docs, guides, or code comments
- **Performance**: Optimize code or improve efficiency
- **Tests**: Add or improve test coverage
- **Examples**: Add new project types or agent templates

### Finding Issues to Work On

- Check issues labeled `good first issue` for beginner-friendly tasks
- Look for `help wanted` labels for issues that need contributors
- Review the project roadmap for upcoming features

## Coding Standards

### Python (Backend)

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use type hints for function arguments and return values
- Write docstrings for classes and functions
- Use descriptive variable names
- Maximum line length: 100 characters

**Linting:**

```bash
# Run linter
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### TypeScript/React (Frontend)

- Use TypeScript strict mode
- Follow React best practices and hooks conventions
- Use functional components with hooks
- Use meaningful component and variable names
- Maximum line length: 100 characters

**Linting:**

```bash
cd frontend
npm run lint
```

### Git Commit Messages

Write clear, descriptive commit messages:

```text
<type>: <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example:**

```text
feat: Add retry logic for failed tasks

Implement automatic retry mechanism for tasks that fail due to
transient errors. Tasks can be retried up to 3 times with
exponential backoff.

Closes #123
```

## Testing

### Backend Tests

```bash
# Run all backend tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend

# Run specific test file
uv run pytest tests/test_task_manager.py
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

### Manual Testing

Before submitting changes:

1. Test the complete user flow
2. Verify all agents work correctly
3. Check error handling and edge cases
4. Test with different project types
5. Verify UI responsiveness and accessibility

## Submitting Changes

### Pull Request Process

1. **Create a branch:**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

1. **Make your changes:**

   - Write clean, documented code
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation as needed

2. **Test thoroughly:**

   - Run all tests
   - Verify linting passes
   - Test manually

3. **Commit your changes:**

```bash
git add .
git commit -m "feat: your descriptive commit message"
```

1. **Push to your fork:**

```bash
git push origin feature/your-feature-name
```

1. **Open a Pull Request:**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template
   - Link related issues

### Pull Request Guidelines

**Your PR should:**

- Have a clear title and description
- Reference related issues (e.g., "Fixes #123")
- Include screenshots for UI changes
- Pass all CI checks
- Have no merge conflicts
- Be focused on a single change

**PR Review Process:**

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge your PR
4. Your contribution will be credited in the release notes

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the issue
- **Steps to reproduce**: Detailed steps to recreate the bug
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, Node version, etc.
- **Logs**: Relevant error messages or logs
- **Screenshots**: If applicable

### Feature Requests

For feature requests, please include:

- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches considered
- **Additional context**: Any other relevant information

## Questions?

If you have questions about contributing:

- Open a [discussion](../../discussions)
- Comment on relevant issues
- Review existing documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to General Contractor Agent Demo!
