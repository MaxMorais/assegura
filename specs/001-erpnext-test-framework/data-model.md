# Data Model: ERPNext Test Automation Meta-Framework

**Feature**: ERPNext Test Automation Meta-Framework  
**Date**: 2025-10-15  
**Phase**: 1 - Data Model Design

## Domain Entities

### Persona
**Purpose**: Represents a user type with specific roles and permissions for testing

**Attributes**:
- `id`: UUID (Primary Key)
- `name`: String (required) - Human-readable persona name
- `description`: Text (optional) - Detailed persona description  
- `erpnext_roles`: List[String] - ERPNext roles assigned to this persona
- `user_permissions`: JSON - Specific user permissions in ERPNext
- `consultant_id`: UUID (Foreign Key) - Owning consultant
- `created_at`: DateTime
- `updated_at`: DateTime

**Validation Rules**:
- Name must be unique per consultant
- At least one ERPNext role required
- User permissions must be valid JSON structure

**State Transitions**:
- Draft → Active → Archived
- Cannot delete if referenced by activities

### Activity  
**Purpose**: Describes a business goal or task that a persona wants to accomplish

**Attributes**:
- `id`: UUID (Primary Key)
- `name`: String (required) - Activity name
- `description`: Text (required) - Business objective description
- `persona_id`: UUID (Foreign Key) - Associated persona
- `erpnext_module`: String - Target ERPNext module (Sales, Purchase, etc.)
- `business_context`: Text - Business process context
- `consultant_id`: UUID (Foreign Key) - Owning consultant  
- `created_at`: DateTime
- `updated_at`: DateTime

**Validation Rules**:
- Name must be unique per persona
- Description minimum 10 characters
- ERPNext module must be valid module name

**Relationships**:
- Belongs to one Persona
- Has many Journeys

### Journey
**Purpose**: Defines sequential steps to complete an activity using action library

**Attributes**:
- `id`: UUID (Primary Key)
- `name`: String (required) - Journey name
- `description`: Text (optional) - Journey purpose
- `activity_id`: UUID (Foreign Key) - Associated activity
- `step_sequence`: JSON - Ordered list of action steps with parameters
- `expected_outcome`: Text - Expected business result
- `consultant_id`: UUID (Foreign Key) - Owning consultant
- `created_at`: DateTime
- `updated_at`: DateTime

**Validation Rules**:
- Name must be unique per activity
- Step sequence must contain valid action references
- Minimum 1 step required

**Relationships**:
- Belongs to one Activity
- Has many Test Suites (generated)

### Action Library
**Purpose**: Comprehensive collection of Given/When/Then actions for test building

**Attributes**:
- `id`: UUID (Primary Key)
- `name`: String (required) - Action name
- `classification`: Enum (Given, When, Then) - BDD classification
- `description`: Text - Action purpose and behavior
- `parameters_schema`: JSON - Input parameter definitions
- `output_schema`: JSON - Output structure definition (boolean or complex)
- `implementation_type`: Enum (API_Call, UI_Interaction, Validation)
- `erpnext_module`: String - Target ERPNext module
- `is_system_action`: Boolean - System-provided vs custom action
- `created_at`: DateTime
- `updated_at`: DateTime

**Validation Rules**:
- Name must be unique per classification and module
- Parameters schema must be valid JSON Schema
- Output schema must define structure for complex outputs

**Output Structure Types**:
- Simple: Boolean (pass/fail)
- Complex: Table with columns (JSON Path, Type, Description) for definition, (Description, Value) for display

### Test Suite  
**Purpose**: Generated Robot Framework test code from journey definitions

**Attributes**:
- `id`: UUID (Primary Key)
- `journey_id`: UUID (Foreign Key) - Source journey
- `robot_framework_code`: Text - Generated test code
- `generation_timestamp`: DateTime - When generated
- `test_data_template`: JSON - Associated test data definitions
- `consultant_id`: UUID (Foreign Key) - Owning consultant
- `created_at`: DateTime

**Validation Rules**:
- Robot Framework code must be syntactically valid
- Test data template must align with journey requirements

**Relationships**:
- Belongs to one Journey  
- Has many Execution Results

### ERPNext Instance
**Purpose**: Configuration for consultant's ERPNext system connections

**Attributes**:
- `id`: UUID (Primary Key)
- `name`: String (required) - Instance identifier
- `base_url`: String (required) - ERPNext instance URL
- `api_key`: String (encrypted) - API authentication key
- `api_secret`: String (encrypted) - API secret
- `consultant_id`: UUID (Foreign Key) - Owning consultant
- `is_active`: Boolean - Connection enabled status
- `last_connected`: DateTime - Last successful connection
- `created_at`: DateTime
- `updated_at`: DateTime

**Validation Rules**:
- Name must be unique per consultant
- URL must be valid HTTP/HTTPS format
- API credentials encrypted at rest

**Security Considerations**:
- API keys encrypted using application-level encryption
- Connection validation before storing credentials

### Test Data Set
**Purpose**: Generated test data for ERPNext entities required by tests

**Attributes**:
- `id`: UUID (Primary Key)
- `name`: String (required) - Data set identifier
- `erpnext_entities`: JSON - Generated entity data (customers, items, etc.)
- `journey_id`: UUID (Foreign Key) - Associated journey
- `generation_parameters`: JSON - Parameters used for generation
- `cleanup_status`: Enum (Pending, Completed, Failed) - Cleanup state
- `consultant_id`: UUID (Foreign Key) - Owning consultant
- `created_at`: DateTime
- `cleaned_up_at`: DateTime (nullable)

**Data Lifecycle**:
- Generated before test execution
- Used during test run
- Cleaned up after execution completion

### Execution Result
**Purpose**: Captures test run outcomes and metrics from cloud execution

**Attributes**:
- `id`: UUID (Primary Key)
- `test_suite_id`: UUID (Foreign Key) - Executed test suite
- `execution_status`: Enum (Queued, Running, Completed, Failed, Cancelled)
- `start_time`: DateTime - Execution start
- `end_time`: DateTime (nullable) - Execution completion
- `pass_count`: Integer - Number of passed tests
- `fail_count`: Integer - Number of failed tests
- `execution_log`: Text - Detailed execution output
- `error_details`: JSON - Structured error information
- `consultant_id`: UUID (Foreign Key) - Owning consultant
- `created_at`: DateTime

**Metrics Tracked**:
- Execution duration
- Individual step timing
- Resource usage (memory, CPU)
- ERPNext API response times

### Cloud Execution Queue
**Purpose**: Manages test execution scheduling and resource allocation

**Attributes**:
- `id`: UUID (Primary Key)
- `test_suite_id`: UUID (Foreign Key) - Test to execute
- `priority`: Integer - Execution priority (1-10)
- `queue_status`: Enum (Pending, Processing, Completed, Failed)
- `allocated_resources`: JSON - Assigned execution resources
- `estimated_duration`: Integer - Expected runtime in seconds
- `consultant_id`: UUID (Foreign Key) - Owning consultant
- `queued_at`: DateTime
- `started_at`: DateTime (nullable)
- `completed_at`: DateTime (nullable)

## Entity Relationships

```
Consultant 1:N Persona 1:N Activity 1:N Journey 1:N TestSuite 1:N ExecutionResult
Consultant 1:N ERPNextInstance
Journey 1:N TestDataSet
Journey N:M ActionLibrary (through step_sequence)
TestSuite 1:1 CloudExecutionQueue
```

## Database Indexes

**Performance Indexes**:
- `persona.consultant_id, persona.name` (unique)
- `activity.persona_id, activity.name` (unique)  
- `journey.activity_id, journey.created_at` (chronological queries)
- `test_suite.journey_id, test_suite.generation_timestamp` (latest version)
- `execution_result.consultant_id, execution_result.created_at` (consultant history)

**Query Optimization**:
- Composite indexes for frequently joined entities
- Partial indexes on active/non-archived records
- JSON indexing for action parameters and outputs