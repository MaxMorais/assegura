# ERPNext Test Automation Meta-Framework - Backend

FastAPI backend for the ERPNext Test Automation Meta-Framework following Domain-Driven Design (DDD) principles.

## Requirements

- Python 3.11+
- PostgreSQL 14+
- Redis (for background tasks)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the development server:
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Development

### Code Quality
- **Linting**: `ruff check .`
- **Formatting**: `black .` 
- **Type Checking**: `mypy src/`

### Testing
- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`
- **Contract Tests**: `pytest tests/contract/` (Robot Framework)
- **All Tests**: `pytest`

### Architecture

The backend follows Domain-Driven Design (DDD) with clear layer separation:

- **Domain Layer** (`src/domain/`): Pure business logic, entities, and domain services
- **Application Layer** (`src/application/`): Use cases, application services, and DTOs
- **Infrastructure Layer** (`src/infrastructure/`): Database, external APIs, and technical concerns
- **API Layer** (`src/api/`): FastAPI endpoints and HTTP concerns

### Constitutional Compliance

This backend strictly follows the [Assegura Constitution](../../.specify/memory/constitution.md):

- ✅ **Python 3.11+**: Required development language with type hints
- ✅ **DDD Architecture**: Clear bounded contexts and ubiquitous language  
- ✅ **Robot Framework**: Mandatory acceptance testing framework
- ✅ **Git Workflow**: Conventional commits and atomic changes

## API Documentation

When running, API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json