# Implementation Plan: ERPNext Test Automation Meta-Framework

**Branch**: `001-erpnext-test-framework` | **Date**: 2025-10-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-erpnext-test-framework/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

ERPNext Test Automation Meta-Framework enables consultants to map business processes into Robot Framework tests, preventing regression issues during support phase. The system follows a Persona→Activity→Journey→Test Generation workflow using a comprehensive action library with Given/When/Then classification. Features include cloud-based execution environment, multi-tenant support, ERPNext API integration, and automated test data management. Technical approach leverages FastAPI + Streamlit separation with PostgreSQL, Docker containerization, and queue-based test execution following Domain-Driven Design principles.

## Technical Context

**Language/Version**: Python 3.11+ (REQUIRED per constitution)  
**Primary Dependencies**: Streamlit (UI), FastAPI (API), SQLAlchemy (ORM), Pydantic (data validation)  
**Storage**: PostgreSQL with JSONb support for flexible action definitions and multi-tenant data isolation  
**Testing**: Robot Framework (acceptance tests), pytest (unit tests)  
**Target Platform**: Linux server with Docker containerization for cloud execution environment  
**Project Type**: Web application (FastAPI backend + Streamlit frontend)  
**Performance Goals**: Support 1000+ consultants, 100 test executions per day per consultant, <60s test generation  
**Constraints**: Multi-tenant data isolation, <30s journey completion, 95% test execution success rate  
**Scale/Scope**: 10 personas per consultant, 50 activities per persona, comprehensive ERPNext module coverage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Phase 0 Check** ✓ PASSED  
**I. Domain-Driven Design (DDD)**: ✓ Bounded contexts: Personas, Activities, Journeys, Test Generation, Execution. Domain events for async processing. Repository pattern with SQLAlchemy.  
**II. Python-First Development**: ✓ Python 3.11+ with type hints, comprehensive docstrings, PEP 8 compliance. Virtual environments mandatory.  
**III. Streamlit-Based UI (NON-NEGOTIABLE)**: ✓ Streamlit frontend with modular components, session state management, performance considerations documented.  
**IV. Test-First with Robot Framework**: ✓ Robot Framework for acceptance tests, pytest for unit tests. Tests written before implementation, separated test data.  
**V. Git-Based Task Management**: ✓ Feature branch workflow, conventional commits, atomic changes, merge request process with task evidence.

**Phase 1 Re-Check** ✓ PASSED  
**I. Domain-Driven Design (DDD)**: ✓ 11 domain entities with clear relationships, validation rules, and state transitions. Multi-tenant architecture with bounded contexts maintained.  
**II. Python-First Development**: ✓ Data model specifies Python 3.11+ with comprehensive type hints and validation using Pydantic schemas.  
**III. Streamlit-Based UI (NON-NEGOTIABLE)**: ✓ Quickstart guide demonstrates modular Streamlit components with clear page separation and session state management.  
**IV. Test-First with Robot Framework**: ✓ API contracts include test endpoints and validation schemas. Test execution environment documented in data model.  
**V. Git-Based Task Management**: ✓ Ready for task breakdown with atomic commits planned for each entity and API endpoint.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```
# Web application (FastAPI backend + Streamlit frontend)
backend/
├── src/
│   ├── domain/               # Pure business logic, DDD entities
│   │   ├── personas/
│   │   ├── activities/
│   │   ├── journeys/
│   │   ├── actions/
│   │   ├── test_generation/
│   │   └── execution/
│   ├── application/          # Use cases and application services
│   │   ├── services/
│   │   └── dto/
│   ├── infrastructure/       # Database, ERPNext API, cloud execution
│   │   ├── database/
│   │   ├── erpnext/
│   │   └── cloud/
│   └── api/                  # FastAPI endpoints
│       ├── personas/
│       ├── activities/
│       ├── journeys/
│       └── test_generation/
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── src/
│   ├── components/           # Reusable Streamlit components
│   │   ├── persona_forms/
│   │   ├── journey_builder/
│   │   └── test_results/
│   ├── pages/                # Streamlit page modules
│   │   ├── personas.py
│   │   ├── activities.py
│   │   ├── journeys.py
│   │   └── test_execution.py
│   └── services/             # API client services
└── tests/
    ├── unit/
    └── ui/                   # Robot Framework UI tests
```

**Structure Decision**: Web application structure selected due to FastAPI backend requirement for cloud execution and ERPNext integration, combined with constitutional mandate for Streamlit frontend. Clear separation supports DDD principles with domain layer isolation and infrastructure abstraction.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No constitutional violations identified. All design decisions align with established principles.

## Phase Completion Status

**Phase 0: Research** ✓ COMPLETED
- Generated `research.md` with technology decisions and integration patterns
- Resolved all technical clarifications from initial context
- Documented cloud execution architecture and multi-tenant design

**Phase 1: Design & Contracts** ✓ COMPLETED  
- Generated `data-model.md` with 11 domain entities and relationships
- Generated `contracts/api.yaml` with comprehensive OpenAPI specification  
- Generated `quickstart.md` with step-by-step consultant onboarding
- Updated agent context successfully with new technology stack

**Ready for**: `/speckit.tasks` - Task breakdown and implementation planning

