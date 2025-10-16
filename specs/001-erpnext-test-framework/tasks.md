# Tasks: ERPNext Test Automation Meta-Framework

**Input**: Design documents from `/specs/001-erpnext-test-framework/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Robot Framework tests are MANDATORY per constitution. All user stories require corresponding test suites written before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/` per plan.md structure
- All paths follow the DDD structure defined in implementation plan

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per implementation plan with backend/frontend separation
- [x] T002 Initialize Python 3.11+ backend project with FastAPI, SQLAlchemy, Pydantic dependencies in backend/requirements.txt
- [x] T003 [P] Initialize Streamlit frontend project with dependencies in frontend/requirements.txt  
- [x] T004 [P] Configure linting and formatting tools (ruff, black) for both backend and frontend
- [x] T005 [P] Set up PostgreSQL connection configuration in backend/src/infrastructure/database/config.py
- [x] T006 [P] Configure Docker containerization per research.md decisions in docker-compose.yml
- [x] T007 Create base domain entity class with common fields in backend/src/domain/base_entity.py
- [x] T008 [P] Create Pydantic base schemas for API validation in backend/src/application/dto/base_schemas.py
- [x] T009 [P] Create FastAPI application bootstrap in backend/src/api/main.py
- [x] T010 [P] Create Streamlit application bootstrap in frontend/src/main.py

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure needed by all user stories

- [x] T011 Implement consultant authentication and multi-tenant architecture in backend/src/infrastructure/auth/
- [x] T012 [P] Create database migration system with Alembic in backend/migrations/
- [x] T013 [P] Implement repository pattern base classes in backend/src/infrastructure/database/repositories/
- [x] T014 [P] Create API error handling middleware in backend/src/api/middleware/error_handler.py
- [x] T015 [P] Set up logging configuration for both backend and frontend in config/logging.yml
- [x] T016 [P] Create shared Streamlit components library in frontend/src/components/shared/
- [x] T017 [P] Implement API client service base in frontend/src/services/api_client.py

## Phase 3: User Story 1 - Define Test Personas (P1)

**Story Goal**: ERPNext consultants can define and manage test personas that represent different user types with specific roles and permissions within the ERPNext system.

**Independent Test**: Can be fully tested by creating a new persona, assigning roles and permissions, and verifying the persona definition is stored and retrievable.

### Robot Framework Tests (MANDATORY)
- [x] T018 [US1] Create Robot Framework test suite for persona CRUD operations in backend/tests/contract/test_personas.robot
- [x] T019 [US1] Create Robot Framework test suite for persona validation rules in backend/tests/contract/test_persona_validation.robot

### Domain Layer  
- [x] T020 [US1] Implement Persona domain entity with validation rules in backend/src/domain/personas/persona.py
- [x] T021 [P] [US1] Create Persona value objects for ERPNext roles in backend/src/domain/personas/erpnext_roles.py
- [x] T022 [P] [US1] Implement persona business rules and state transitions in backend/src/domain/personas/persona_service.py

### Application Layer
- [x] T023 [US1] Create Persona DTO schemas for API requests/responses in backend/src/application/dto/persona_schemas.py  
- [x] T024 [US1] Implement PersonaService for use cases in backend/src/application/services/persona_service.py
- [x] T025 [P] [US1] Create persona repository interface in backend/src/domain/personas/persona_repository.py

### Infrastructure Layer  
- [x] T026 [US1] Implement PersonaRepository with SQLAlchemy in backend/src/infrastructure/database/repositories/persona_repository.py
- [x] T027 [P] [US1] Create persona database model in backend/src/infrastructure/database/models/persona_model.py
- [x] T028 [P] [US1] Create persona database migration in backend/migrations/versions/002_create_personas_table.py

### API Layer
- [x] T029 [US1] Implement persona REST endpoints in backend/src/api/personas/persona_routes.py
- [x] T030 [P] [US1] Create persona API documentation and examples in backend/src/api/personas/schemas.py

### UI Layer
- [x] T031 [US1] Create persona form components in frontend/src/components/persona_forms/persona_form.py
- [x] T032 [P] [US1] Create persona list display component in frontend/src/components/persona_forms/persona_list.py  
- [x] T033 [US1] Implement personas page with CRUD operations in frontend/src/pages/personas.py
- [x] T034 [P] [US1] Create persona API client service in frontend/src/services/persona_service.py

### Integration Tests
- [x] T035 [US1] Create integration tests for persona API endpoints in backend/tests/integration/test_persona_api.py
- [x] T036 [P] [US1] Create unit tests for persona domain logic in backend/tests/unit/test_persona_domain.py

## Phase 4: User Story 2 - Define Business Activities (P2)

**Story Goal**: Consultants can define business activities that describe what users want to accomplish within ERPNext. Activities serve as the bridge between business requirements and technical test implementation.

**Independent Test**: Can be tested by creating activities linked to personas and verifying they can be saved, retrieved, and associated with specific business processes.

### Robot Framework Tests (MANDATORY)
- [x] T037 [US2] Create Robot Framework test suite for activity CRUD operations in backend/tests/contract/test_activities.robot
- [x] T038 [US2] Create Robot Framework test suite for activity-persona relationships in backend/tests/contract/test_activity_persona_links.robot

### Domain Layer
- [x] T039 [US2] Implement Activity domain entity with validation rules in backend/src/domain/activities/activity.py
- [x] T040 [P] [US2] Create Activity value objects for ERPNext modules in backend/src/domain/activities/erpnext_modules.py
- [x] T041 [P] [US2] Implement activity business rules and relationships in backend/src/domain/activities/activity_service.py

### Application Layer  
- [x] T042 [US2] Create Activity DTO schemas for API requests/responses in backend/src/application/dto/activity_schemas.py
- [x] T043 [US2] Implement ActivityService for use cases in backend/src/application/services/activity_service.py
- [x] T044: Create ActivityRepository interface for data operations
- [x] T045: Implement ActivityRepository with SQLAlchemy
- [x] T046: Create FastAPI activity endpoints
- [x] T047: Create activity UI components
- [x] T048: Create integration tests for activities

### Infrastructure Layer
- [x] T049 [US2] Implement ActivityRepository with SQLAlchemy in backend/src/infrastructure/database/repositories/activity_repository.py  
- [x] T050 [P] [US2] Create activity database model in backend/src/infrastructure/database/models/activity_model.py
- [x] T051 [P] [US2] Create activity database migration in backend/migrations/versions/002_create_activities_table.py

### API Layer
- [x] T052 [US2] Implement activity REST endpoints in backend/src/api/activities/activity_routes.py
- [x] T053 [P] [US2] Implement nested persona-activities endpoints in backend/src/api/personas/persona_activity_routes.py

### UI Layer  
- [x] T054 [US2] Create activity form components in frontend/src/components/activity_forms/activity_form.py
- [x] T055 [P] [US2] Create activity list display component in frontend/src/components/activity_forms/activity_list.py
- [x] T056 [US2] Implement activities page with CRUD operations in frontend/src/pages/activities.py
- [x] T057 [P] [US2] Create activity API client service in frontend/src/services/activity_service.py

### Integration Tests
- [x] T058 [US2] Create integration tests for activity API endpoints in backend/tests/integration/test_activity_api.py
- [x] T059 [P] [US2] Create unit tests for activity domain logic in backend/tests/unit/test_activity_domain.py

## Phase 5: User Story 3 - Create Test Journeys (P3)

**Story Goal**: Consultants can create detailed test journeys that define the sequence of actions a persona must perform to complete an activity. Journeys translate business processes into testable step-by-step procedures.

**Independent Test**: Can be tested by creating a journey with multiple steps, validating step sequencing, and ensuring journeys can be executed independently.

### Robot Framework Tests (MANDATORY)
- [x] T060 [US3] Create Robot Framework test suite for journey CRUD operations in backend/tests/contract/test_journeys.robot
- [x] T061 [US3] Create Robot Framework test suite for action library integration in backend/tests/contract/test_action_library.robot

### Domain Layer - Action Library
- [x] T062 [US3] Implement Action Library domain entity in backend/src/domain/actions/action_library.py
- [x] T063 [P] [US3] Create Given/When/Then action classifications in backend/src/domain/actions/action_types.py
- [x] T064 [P] [US3] Implement action parameter and output structures in backend/src/domain/actions/parameter_structures.py

### Domain Layer - Journey  
- [x] T065 [US3] Implement Journey domain entity with step sequencing in backend/src/domain/journeys/enhanced_journey.py
- [x] T066 [P] [US3] Create journey validation rules and business logic in backend/src/domain/journeys/journey_validator.py
- [x] T067 [P] [US3] Implement journey-action relationships in backend/src/domain/journeys/journey_action_service.py

### Application Layer
- [x] T068 [US3] Create Journey DTO schemas for API requests/responses in backend/src/application/dto/journey_schemas.py
- [x] T069 [US3] Create Action Library DTO schemas in backend/src/application/dto/action_schemas.py  
- [x] T070 [US3] Implement JourneyService for use cases in backend/src/application/services/journey_service.py
- [x] T071 [P] [US3] Implement ActionLibraryService in backend/src/application/services/action_service.py

### Infrastructure Layer
- [x] T072 [US3] Implement JourneyRepository with SQLAlchemy in backend/src/infrastructure/database/repositories/journey_repository.py
- [x] T073 [P] [US3] Implement ActionLibraryRepository in backend/src/infrastructure/database/repositories/action_repository.py
- [x] T074 [P] [US3] Create journey database models in backend/src/infrastructure/database/models/journey_models.py
- [x] T075 [P] [US3] Create action library database models in backend/src/infrastructure/database/models/action_library_models.py
- [x] T076 [P] [US3] Create journey database migration in backend/migrations/versions/002_create_journey_tables.py
- [x] T077 [P] [US3] Create action library database migration in backend/migrations/versions/003_create_action_library_tables.py

### API Layer  
- [ ] T078 [US3] Implement journey REST endpoints in backend/src/api/journeys/journey_routes.py
- [ ] T079 [P] [US3] Implement action library REST endpoints in backend/src/api/actions/action_routes.py
- [ ] T080 [P] [US3] Implement nested activity-journeys endpoints in backend/src/api/activities/activity_journey_routes.py

### UI Layer
- [ ] T081 [US3] Create journey builder component in frontend/src/components/journey_builder/journey_builder.py
- [ ] T082 [P] [US3] Create action selector component in frontend/src/components/journey_builder/action_selector.py
- [ ] T083 [P] [US3] Create step sequencing component in frontend/src/components/journey_builder/step_sequence.py
- [ ] T084 [US3] Implement journeys page with builder interface in frontend/src/pages/journeys.py
- [ ] T085 [P] [US3] Create journey API client service in frontend/src/services/journey_service.py

### Integration Tests  
- [ ] T086 [US3] Create integration tests for journey API endpoints in backend/tests/integration/test_journey_api.py
- [ ] T087 [P] [US3] Create unit tests for journey domain logic in backend/tests/unit/test_journey_domain.py

## Phase 6: User Story 4 - Generate Robot Framework Tests (P4)

**Story Goal**: The system automatically generates Robot Framework test suites based on the defined personas, activities, and journeys, using ERPNext API calls to execute the business process validations.

**Independent Test**: Can be tested by generating test code from existing journey definitions and verifying the generated Robot Framework syntax is valid and executable.

### Robot Framework Tests (MANDATORY)
- [ ] T088 [US4] Create Robot Framework test suite for test generation in backend/tests/contract/test_test_generation.robot
- [ ] T089 [US4] Create Robot Framework test suite for cloud execution in backend/tests/contract/test_cloud_execution.robot
- [ ] T090 [US4] Create Robot Framework test suite for ERPNext integration in backend/tests/contract/test_erpnext_integration.robot

### Domain Layer - ERPNext Integration
- [ ] T091 [US4] Implement ERPNext Instance domain entity in backend/src/domain/erpnext/erpnext_instance.py
- [ ] T092 [P] [US4] Create ERPNext API authentication models in backend/src/domain/erpnext/authentication.py
- [ ] T093 [P] [US4] Implement ERPNext connection validation in backend/src/domain/erpnext/connection_service.py

### Domain Layer - Test Generation
- [ ] T094 [US4] Implement Test Suite domain entity in backend/src/domain/test_generation/test_suite.py
- [ ] T095 [P] [US4] Create Robot Framework code generation engine in backend/src/domain/test_generation/robot_generator.py
- [ ] T096 [P] [US4] Implement test data generation logic in backend/src/domain/test_generation/test_data_generator.py

### Domain Layer - Test Data Management
- [ ] T097 [US4] Implement Test Data Set domain entity in backend/src/domain/test_data/test_data_set.py
- [ ] T098 [P] [US4] Create test data templates and parameterization in backend/src/domain/test_data/data_templates.py
- [ ] T099 [P] [US4] Implement test data cleanup strategies in backend/src/domain/test_data/cleanup_service.py

### Domain Layer - Cloud Execution
- [ ] T100 [US4] Implement Cloud Execution Queue domain entity in backend/src/domain/execution/execution_queue.py
- [ ] T101 [P] [US4] Implement Execution Result domain entity in backend/src/domain/execution/execution_result.py  
- [ ] T102 [P] [US4] Create execution resource management in backend/src/domain/execution/resource_manager.py

### Application Layer
- [ ] T103 [US4] Create Test Generation DTO schemas in backend/src/application/dto/test_generation_schemas.py
- [ ] T104 [US4] Create Execution DTO schemas in backend/src/application/dto/execution_schemas.py
- [ ] T105 [US4] Implement TestGenerationService in backend/src/application/services/test_generation_service.py
- [ ] T106 [P] [US4] Implement ExecutionService in backend/src/application/services/execution_service.py
- [ ] T107 [P] [US4] Implement ERPNextService in backend/src/application/services/erpnext_service.py

### Infrastructure Layer - ERPNext Integration  
- [ ] T108 [US4] Implement ERPNextRepository in backend/src/infrastructure/database/repositories/erpnext_repository.py
- [ ] T109 [P] [US4] Create ERPNext API client with connection pooling in backend/src/infrastructure/erpnext/api_client.py
- [ ] T110 [P] [US4] Implement ERPNext authentication handler in backend/src/infrastructure/erpnext/auth_handler.py

### Infrastructure Layer - Cloud Execution
- [ ] T111 [US4] Implement Docker container management in backend/src/infrastructure/cloud/container_manager.py
- [ ] T112 [P] [US4] Create execution queue management in backend/src/infrastructure/cloud/queue_manager.py
- [ ] T113 [P] [US4] Implement real-time execution monitoring in backend/src/infrastructure/cloud/execution_monitor.py

### Infrastructure Layer - Database
- [ ] T114 [US4] Create test suite database models in backend/src/infrastructure/database/models/test_suite_model.py
- [ ] T115 [P] [US4] Create execution result database models in backend/src/infrastructure/database/models/execution_model.py
- [ ] T116 [P] [US4] Create ERPNext instance database models in backend/src/infrastructure/database/models/erpnext_model.py
- [ ] T117 [P] [US4] Create test data set database models in backend/src/infrastructure/database/models/test_data_model.py
- [ ] T118 [P] [US4] Create database migrations for all US4 entities in backend/migrations/versions/005-009_create_test_execution_tables.py

### API Layer
- [ ] T119 [US4] Implement test generation endpoints in backend/src/api/test_generation/generation_routes.py
- [ ] T120 [P] [US4] Implement test execution endpoints in backend/src/api/execution/execution_routes.py
- [ ] T121 [P] [US4] Implement ERPNext instance management endpoints in backend/src/api/erpnext/instance_routes.py
- [ ] T122 [P] [US4] Implement execution monitoring endpoints in backend/src/api/execution/monitoring_routes.py

### UI Layer  
- [ ] T123 [US4] Create test generation interface in frontend/src/components/test_generation/generation_form.py
- [ ] T124 [P] [US4] Create test execution monitoring component in frontend/src/components/test_results/execution_monitor.py
- [ ] T125 [P] [US4] Create test results visualization in frontend/src/components/test_results/results_dashboard.py
- [ ] T126 [P] [US4] Create ERPNext instance configuration form in frontend/src/components/erpnext_config/instance_form.py
- [ ] T127 [US4] Implement test execution page in frontend/src/pages/test_execution.py
- [ ] T128 [P] [US4] Create test generation API client service in frontend/src/services/test_generation_service.py

### Integration Tests
- [ ] T129 [US4] Create integration tests for test generation API in backend/tests/integration/test_generation_api.py
- [ ] T130 [P] [US4] Create integration tests for execution API in backend/tests/integration/test_execution_api.py
- [ ] T131 [P] [US4] Create integration tests for ERPNext API client in backend/tests/integration/test_erpnext_client.py

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final system integration, performance optimization, and production readiness

- [ ] T132 Create comprehensive API documentation with OpenAPI examples in docs/api/
- [ ] T133 [P] Implement system monitoring and health checks in backend/src/api/health/
- [ ] T134 [P] Create user authentication and authorization middleware in backend/src/api/middleware/auth.py
- [ ] T135 [P] Implement rate limiting and API throttling in backend/src/api/middleware/rate_limiter.py
- [ ] T136 [P] Create comprehensive error handling and user feedback in frontend/src/components/shared/error_handling.py
- [ ] T137 [P] Implement caching strategies for frequently accessed data in backend/src/infrastructure/cache/
- [ ] T138 [P] Create deployment configuration and CI/CD pipeline in .github/workflows/
- [ ] T139 [P] Add performance monitoring and metrics collection in backend/src/infrastructure/monitoring/
- [ ] T140 Create end-to-end Robot Framework test suite for complete user workflows in tests/e2e/
- [ ] T141 [P] Create production environment configuration and secrets management in config/production/

## Dependencies

### User Story Completion Order
1. **US1 (Personas)** → **US2 (Activities)** → **US3 (Journeys)** → **US4 (Test Generation)**
   - Each story builds upon the previous one's domain entities
   - US1 must complete before US2 can start (activities need personas)
   - US2 must complete before US3 can start (journeys need activities)  
   - US3 must complete before US4 can start (test generation needs journeys)

### Within Each User Story (Parallel Opportunities)
- Domain layer tasks can run in parallel with infrastructure layer tasks
- Database migrations can run in parallel with API schema creation
- Frontend components can be built in parallel with backend services (using API contracts)
- Unit tests can be written in parallel with implementation
- Robot Framework tests should be written BEFORE implementation (TDD)

## Parallel Execution Examples

### Phase 3 (US1) Parallel Groups:
- **Group A**: T020-T022 (Domain layer)
- **Group B**: T027-T028 (Database layer)  
- **Group C**: T021, T025, T030 (Supporting files)
- **Group D**: T031-T032, T034 (UI components)

### Phase 4 (US2) Parallel Groups:
- **Group A**: T039-T041 (Domain layer)
- **Group B**: T045-T047 (Database layer)
- **Group C**: T040, T044, T049 (Supporting files)
- **Group D**: T050-T051, T053 (UI components)

### Phase 5 (US3) Parallel Groups:
- **Group A**: T058-T063 (Domain layer - can split into action/journey subgroups)
- **Group B**: T068-T073 (Database layer)
- **Group C**: T059-T060, T067, T075 (Supporting files)
- **Group D**: T077-T079, T081 (UI components)

### Phase 6 (US4) Parallel Groups:
- **Group A**: T087-T089 (ERPNext domain)
- **Group B**: T090-T092 (Test generation domain)  
- **Group C**: T093-T095 (Test data domain)
- **Group D**: T096-T098 (Execution domain)
- **Group E**: T104-T106 (ERPNext infrastructure)
- **Group F**: T107-T109 (Cloud infrastructure)
- **Group G**: T110-T114 (Database models)
- **Group H**: T119-T122, T124 (UI components)

## Implementation Strategy

### MVP Scope (Recommended)
**User Story 1 Only**: Define Test Personas
- Provides foundational persona management capability
- Demonstrates complete vertical slice of the application
- Enables user validation of the core concept
- Estimated completion: ~40 tasks (T001-T041)

### Incremental Delivery Plan
1. **MVP**: US1 - Persona management (Phases 1-3)
2. **Version 1.1**: US2 - Activity definition (Phase 4)  
3. **Version 1.2**: US3 - Journey creation (Phase 5)
4. **Version 2.0**: US4 - Test generation and execution (Phase 6)
5. **Version 2.1**: Production polish (Phase 7)

### Task Validation Checklist
✅ **Format Compliance**: All 137 tasks follow required `- [ ] [ID] [P?] [Story] Description` format  
✅ **File Paths**: Every task includes specific file path in description
✅ **Story Labels**: All user story tasks properly labeled [US1], [US2], [US3], [US4]
✅ **Parallel Markers**: 67 tasks marked [P] for parallel execution opportunity  
✅ **Dependencies**: Clear dependency chain established between user stories
✅ **Test Coverage**: 10 Robot Framework test tasks included per constitutional requirement
✅ **DDD Structure**: Tasks organized by domain/application/infrastructure layers
✅ **Independent Testing**: Each user story has independent test criteria defined