# Contributing to Session Controller

Thank you for your interest in contributing to Session Controller!

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your operating system and Session Desktop version
- Python version (`python --version`)
- Session Controller version (`session-cli --version` if available)

### Suggesting Enhancements

Enhancement suggestions are welcome! When suggesting a new feature:

- Use a clear and descriptive title
- Provide a detailed description of the proposed feature
- Explain why this feature would be useful
- If possible, provide examples of how the feature would work

## Development Setup

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/session-cli.git
   cd session-cli
   ```

### Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dev dependencies
pip install -e ".[dev]"

# Or install from requirements files
pip install -r requirements-dev.txt
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=session_controller --cov-report=html

# Run specific test file
pytest tests/test_database.py
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code with black
black .

# Check code style with flake8
flake8 session_controller

# Type checking with mypy
mypy session_controller
```

## Making Changes

### Branching

Create a descriptive branch for your changes:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### Commit Messages

Follow conventional commit format:

```
type(scope): subject

body

footer
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(cli): add support for filtering by conversation type
fix(database): handle missing attachment files gracefully
docs(readme): update installation instructions for Windows
```

### Pull Requests

1. Ensure your code passes all tests
2. Format your code with black
3. Update documentation if needed
4. Create a pull request with a clear description of your changes

## Code Style

- Follow PEP 8
- Use 4 spaces for indentation
- Line length: 100 characters (Black default)
- Add docstrings to functions and classes
- Type hints are encouraged but not required

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for good test coverage (>80%)

## Documentation

- Update README.md if you change CLI behavior
- Add docstrings to new functions
- Keep examples in `examples/` updated

## Project Structure

```
session-cli/
├── session_controller/      # Main package
│   ├── __init__.py
│   ├── cli.py              # CLI implementation
│   ├── config.py           # Session configuration handling
│   ├── database.py         # Database access
│   ├── cdp.py              # CDP client
│   ├── repl.py             # Interactive REPL mode
│   ├── user_config.py      # User configuration file support
│   ├── constants.py        # SQL queries and constants
│   └── exceptions.py       # Custom exceptions
├── examples/               # Usage examples
├── tests/                 # Test suite
├── README.md
├── LICENSE
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── AGENTS.md
├── CLAUDE.md
└── TODO.md
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue for questions or discussions!
