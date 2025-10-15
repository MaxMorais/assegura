# Research: ERPNext Test Automation Meta-Framework

**Feature**: ERPNext Test Automation Meta-Framework  
**Date**: 2025-10-15  
**Phase**: 0 - Research & Technology Selection

## Technology Decisions

### Web Framework Architecture

**Decision**: FastAPI + Streamlit separation with shared contracts  
**Rationale**: Constitutional requirement for Streamlit UI combined with need for robust API layer for cloud execution and ERPNext integration. FastAPI provides excellent async support and OpenAPI documentation.  
**Alternatives considered**: Single Streamlit app (rejected due to cloud execution needs), Django + React (rejected due to constitutional Streamlit requirement)

### Database & ORM

**Decision**: PostgreSQL with SQLAlchemy ORM  
**Rationale**: PostgreSQL provides ACID compliance needed for multi-tenant consultant data, JSONb support for flexible action definitions, and excellent Python ecosystem support. SQLAlchemy aligns with DDD patterns.  
**Alternatives considered**: MongoDB (rejected due to relational needs), SQLite only (rejected due to scale requirements)

### ERPNext Integration

**Decision**: Direct ERPNext REST API integration with connection pooling  
**Rationale**: ERPNext provides comprehensive REST API that supports all business operations. Connection pooling required for multi-consultant usage patterns.  
**Alternatives considered**: Direct database access (rejected due to complexity), Frappe framework extension (rejected due to deployment constraints)

### Cloud Execution Architecture

**Decision**: Containerized Robot Framework execution with queue management  
**Rationale**: Docker containers provide isolation for multi-tenant test execution. Queue system manages resource allocation and provides scalability.  
**Alternatives considered**: Serverless functions (rejected due to Robot Framework requirements), VM-based execution (rejected due to cost/complexity)

### Action Library Design

**Decision**: Plugin-based action architecture with Given/When/Then classification  
**Rationale**: Enables extensibility for different ERPNext modules while maintaining BDD structure. Parametrization supports flexible test scenarios.  
**Alternatives considered**: Hardcoded actions (rejected due to flexibility needs), Free-form scripting (rejected due to maintainability)

### Test Data Management

**Decision**: Template-based generation with automated cleanup  
**Rationale**: Provides repeatable test scenarios while maintaining data isolation between test runs. Templates enable parameterization for different business contexts.  
**Alternatives considered**: Static demo data (rejected due to isolation needs), Production data usage (rejected due to safety concerns)

## Integration Patterns

### ERPNext API Authentication
- API key-based authentication per configured instance  
- Connection pooling with timeout management  
- Retry logic for transient failures  

### Cloud Execution Flow
- Test generation → Queue submission → Container execution → Result collection  
- Real-time progress tracking via WebSocket connections  
- Resource cleanup after execution completion  

### Domain-Driven Design Implementation
- Bounded contexts: Personas, Activities, Journeys, Test Generation, Execution  
- Domain events for async processing (test generation completion, execution results)  
- Repository pattern for data persistence with SQLAlchemy implementation  

## Performance & Scalability Considerations

### Expected Load Patterns
- 1000+ consultants using system  
- Average 10 personas per consultant  
- 50 activities per persona  
- 100 test executions per day per consultant  

### Optimization Strategies
- Connection pooling for ERPNext APIs  
- Async processing for test generation  
- Result caching for common queries  
- Database indexing on frequently queried fields  

## Security Considerations

### Multi-Tenancy
- Tenant isolation at database level  
- API key encryption for ERPNext connections  
- Role-based access control for consultants  

### Data Protection
- Encryption at rest for sensitive configuration data  
- Audit logging for all test executions  
- No persistent storage of ERPNext business data  

## Development Approach

### Domain-Driven Design Structure
- Domain layer: Pure business logic, no framework dependencies  
- Application layer: Use cases and application services  
- Infrastructure layer: Database, ERPNext API, cloud execution  
- UI layer: Streamlit presentation components  

### Testing Strategy
- Unit tests for all domain logic using pytest  
- Integration tests for ERPNext API integration  
- Contract tests for API boundaries  
- Acceptance tests using Robot Framework for the system itself