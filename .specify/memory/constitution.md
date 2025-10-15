<!--
SYNC IMPACT REPORT
==================
Version change: N/A → 1.0.0 (Initial constitution creation)

Added principles:
- I. Domain-Driven Design (DDD)
- II. Python-First Development  
- III. Streamlit-Based UI (NON-NEGOTIABLE)
- IV. Test-First with Robot Framework
- V. Git-Based Task Management

Added sections:
- Technology Standards
- Development Workflow

Template updates:
✅ plan-template.md: Updated Constitution Check section and technical context defaults
✅ tasks-template.md: Updated testing requirements from optional to mandatory per constitution
✅ spec-template.md: No changes needed (requirements-focused)
✅ agent-file-template.md: No changes needed (generic template)
✅ checklist-template.md: No changes needed (generic template)

Follow-up TODOs: None - all placeholders resolved
-->

# Assegura Constitution

## Core Principles

### I. Domain-Driven Design (DDD)
All development MUST follow Domain-Driven Design principles. Business logic MUST be encapsulated in domain entities and services. Clear bounded contexts MUST be established and maintained. Ubiquitous language MUST be used consistently across code, documentation, and communication. Domain models MUST be technology-agnostic and testable in isolation.

### II. Python-First Development
Python 3.11+ is the REQUIRED development language. Code MUST follow PEP 8 style guidelines with type hints. All modules MUST include comprehensive docstrings. Dependencies MUST be managed through requirements.txt or pyproject.toml. Virtual environments are MANDATORY for all development work.

### III. Streamlit-Based UI (NON-NEGOTIABLE)
All user interfaces MUST use Streamlit framework. UI components MUST be modular and reusable. State management MUST follow Streamlit session state patterns. Custom components are permitted only when built-in components are insufficient. Performance considerations MUST be documented for complex UI flows.

### IV. Test-First with Robot Framework
Robot Framework is MANDATORY for all acceptance tests. Test scenarios MUST be written before implementation begins. All user stories MUST have corresponding Robot Framework test suites. Test data MUST be separated from test logic using resource files. Tests MUST be executable in CI/CD pipelines.

### V. Git-Based Task Management
Every task MUST have a dedicated Git commit with descriptive messages. Commit messages MUST follow conventional commit format. Feature branches MUST be used for all development work. All commits MUST be atomic and focused on a single change. Merge requests MUST include task completion evidence.

## Technology Standards

Python 3.11+ with type hints and comprehensive documentation. Streamlit for all UI development with modular component architecture. Robot Framework for acceptance testing with clear separation of test data and logic. Git version control with conventional commits and feature branch workflow. Code quality enforced through linting, formatting, and type checking tools.

## Development Workflow

All features begin with specification creation using spec-driven development process. Implementation follows Red-Green-Refactor cycle with Robot Framework tests written first. Each task requires dedicated Git commit with clear description and completion evidence. Code reviews MUST verify DDD principles, Python standards, and test coverage. Deployment MUST include test execution and verification steps.

## Governance

This constitution supersedes all other development practices and standards. All feature specifications and implementation plans MUST demonstrate compliance with core principles. Any deviation from NON-NEGOTIABLE principles requires explicit constitution amendment. Code reviews MUST include constitutional compliance verification. Complexity decisions MUST be justified against established principles.

**Version**: 1.0.0 | **Ratified**: 2025-10-15 | **Last Amended**: 2025-10-15
