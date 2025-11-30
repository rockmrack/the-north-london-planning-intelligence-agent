# Contributing Guide

Thank you for your interest in contributing to the North London Planning Intelligence Agent! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (optional, for containerized development)
- Git

### Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/your-username/north-london-planning-agent.git
cd north-london-planning-agent
```

2. **Set up the backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Set up the frontend**

```bash
cd frontend
npm install
```

4. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your development credentials
```

5. **Start development servers**

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

## Development Workflow

### Branch Naming

Use descriptive branch names:

- `feature/add-new-borough` - New features
- `fix/rate-limiting-bug` - Bug fixes
- `docs/update-api-docs` - Documentation
- `refactor/cleanup-analytics` - Code refactoring
- `test/add-chat-tests` - Test additions

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(chat): add support for follow-up questions
fix(analytics): correct daily aggregation query
docs(api): update authentication examples
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, focused commits
3. Write or update tests as needed
4. Update documentation if applicable
5. Run linting and tests locally
6. Push your branch and create a PR
7. Fill out the PR template
8. Request review from maintainers

## Code Style

### Python (Backend)

We follow PEP 8 with some modifications:

```bash
# Format code
black app/

# Sort imports
isort app/

# Check types
mypy app/

# Lint
ruff check app/
```

**Style Guidelines:**
- Line length: 88 characters (Black default)
- Use type hints for function signatures
- Write docstrings for public functions and classes
- Use `async/await` for I/O operations

Example:
```python
async def process_query(
    query: str,
    session_id: str,
    *,
    include_sources: bool = True,
) -> QueryResponse:
    """
    Process a user query and return AI-generated response.

    Args:
        query: The user's planning question
        session_id: Unique session identifier
        include_sources: Whether to include document citations

    Returns:
        QueryResponse with message and optional citations
    """
    ...
```

### TypeScript (Frontend)

```bash
# Format and lint
npm run lint
npm run format

# Type check
npm run type-check
```

**Style Guidelines:**
- Use TypeScript strict mode
- Define interfaces for API responses
- Use functional components with hooks
- Prefer named exports

Example:
```typescript
interface ChatMessageProps {
  message: string;
  isUser: boolean;
  citations?: Citation[];
}

export function ChatMessage({ message, isUser, citations }: ChatMessageProps) {
  // Component implementation
}
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_chat.py

# Run tests matching pattern
pytest -k "test_query"
```

**Test Guidelines:**
- Write unit tests for business logic
- Write integration tests for API endpoints
- Mock external services (OpenAI, Supabase)
- Aim for 80%+ coverage on critical paths

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

## API Guidelines

### Endpoint Design

- Use RESTful conventions
- Version APIs (`/api/v1/`)
- Use appropriate HTTP methods
- Return consistent response formats

### Error Handling

Return structured errors:

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE",
  "context": {}
}
```

### Authentication

- Use Bearer tokens for protected endpoints
- Implement rate limiting
- Log authentication failures

## Database Guidelines

### Migrations

- Create migrations for schema changes
- Test migrations in development first
- Include rollback scripts

### Query Optimization

- Use indexes for frequently queried columns
- Avoid N+1 queries
- Use connection pooling

## Documentation

### Code Documentation

- Add docstrings to public functions
- Include type hints
- Document complex algorithms

### API Documentation

- Update OpenAPI specs when changing endpoints
- Include request/response examples
- Document error codes

### User Documentation

- Update README for major features
- Add guides in `docs/` for complex topics
- Include screenshots where helpful

## Review Checklist

Before submitting a PR, verify:

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] No sensitive data in commits
- [ ] PR description is clear

## Common Tasks

### Adding a New API Endpoint

1. Define Pydantic models in `app/models/`
2. Create endpoint in `app/api/v1/`
3. Add business logic in `app/services/`
4. Write tests in `tests/`
5. Update API documentation

### Adding a New Borough

1. Add to borough configuration
2. Update document ingestion pipeline
3. Add test data
4. Update frontend dropdown

### Adding a New Document Type

1. Define parser in `app/services/document_processor.py`
2. Update ingestion endpoint
3. Add document type to schema
4. Test with sample documents

## Getting Help

- Check existing issues and discussions
- Ask questions in PR comments
- Reach out to maintainers

## Recognition

Contributors are recognized in:
- Release notes
- Contributors list
- Project documentation

Thank you for contributing!
