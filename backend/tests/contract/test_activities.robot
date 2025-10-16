*** Settings ***
Documentation    Contract tests for Activity CRUD operations
...              These tests define the expected behavior of the Activity API
...              and serve as living documentation of the contract.
Library          RequestsLibrary
Library          JSONLibrary
Library          Collections
Library          String
Library          DateTime
Suite Setup      Initialize Test Environment
Suite Teardown   Cleanup Test Environment

*** Variables ***
${BASE_URL}      http://localhost:8000/api/v1
${ACTIVITIES_ENDPOINT}    ${BASE_URL}/activities
${VALID_ACTIVITY_DATA}    {"name": "Create Sales Order", "description": "Create a new sales order in ERPNext", "erpnext_module": "Sales", "action_type": "create", "target_doctype": "Sales Order", "required_fields": ["customer", "items"], "validation_rules": {"customer": "required", "items": "array_min:1"}, "success_criteria": ["order_created", "customer_notified"], "complexity_score": 5, "estimated_duration": 300, "is_active": true}

*** Keywords ***
Initialize Test Environment
    [Documentation]    Set up test environment and authentication
    Create Session    api    ${BASE_URL}
    &{headers}=    Create Dictionary    Content-Type=application/json
    Set Suite Variable    ${HEADERS}    ${headers}
    
    # Create test persona for activity relationships
    ${persona_data}=    Set Variable    {"name": "Test Sales Manager", "description": "Test persona for activities", "erpnext_roles": ["Sales Manager", "Customer"], "permissions": "read_sales_order,write_sales_order", "is_active": true}
    ${response}=    POST On Session    api    /personas    json=${persona_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    201
    ${persona_json}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_PERSONA_ID}    ${persona_json['id']}

Cleanup Test Environment
    [Documentation]    Clean up test data after all tests
    # Clean up any remaining test activities
    ${response}=    GET On Session    api    /activities    headers=${HEADERS}
    ${activities}=    Set Variable    ${response.json()['items']}
    FOR    ${activity}    IN    @{activities}
        Run Keyword And Ignore Error    DELETE On Session    api    /activities/${activity['id']}    headers=${HEADERS}
    END
    
    # Clean up test persona
    Run Keyword And Ignore Error    DELETE On Session    api    /personas/${TEST_PERSONA_ID}    headers=${HEADERS}

Create Valid Activity
    [Documentation]    Create a valid activity and return its ID
    [Arguments]    ${activity_data}=${VALID_ACTIVITY_DATA}
    ${response}=    POST On Session    api    /activities    json=${activity_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    201
    ${activity_json}=    Set Variable    ${response.json()}
    Should Not Be Empty    ${activity_json['id']}
    [Return]    ${activity_json['id']}

Validate Activity Response Schema
    [Documentation]    Validate that activity response has correct schema
    [Arguments]    ${activity_json}
    Should Not Be Empty    ${activity_json['id']}
    Should Contain    ${activity_json}    name
    Should Contain    ${activity_json}    description
    Should Contain    ${activity_json}    erpnext_module
    Should Contain    ${activity_json}    action_type
    Should Contain    ${activity_json}    target_doctype
    Should Contain    ${activity_json}    required_fields
    Should Contain    ${activity_json}    validation_rules
    Should Contain    ${activity_json}    success_criteria
    Should Contain    ${activity_json}    complexity_score
    Should Contain    ${activity_json}    estimated_duration
    Should Contain    ${activity_json}    is_active
    Should Contain    ${activity_json}    created_at
    Should Contain    ${activity_json}    updated_at
    Should Contain    ${activity_json}    version

*** Test Cases ***
AC001: Create Activity With Valid Data
    [Documentation]    Test creating an activity with valid data
    [Tags]    create    positive    contract
    
    ${activity_data}=    Evaluate    json.loads('${VALID_ACTIVITY_DATA}')    json
    
    ${response}=    POST On Session    api    /activities    json=${activity_data}    headers=${HEADERS}
    
    # Verify response status
    Should Be Equal As Strings    ${response.status_code}    201
    
    # Verify response schema
    ${activity_json}=    Set Variable    ${response.json()}
    Validate Activity Response Schema    ${activity_json}
    
    # Verify response data matches request
    Should Be Equal As Strings    ${activity_json['name']}    ${activity_data['name']}
    Should Be Equal As Strings    ${activity_json['description']}    ${activity_data['description']}
    Should Be Equal As Strings    ${activity_json['erpnext_module']}    ${activity_data['erpnext_module']}
    Should Be Equal As Strings    ${activity_json['action_type']}    ${activity_data['action_type']}
    Should Be Equal As Strings    ${activity_json['target_doctype']}    ${activity_data['target_doctype']}
    Should Be Equal As Integers    ${activity_json['complexity_score']}    ${activity_data['complexity_score']}
    Should Be Equal As Integers    ${activity_json['estimated_duration']}    ${activity_data['estimated_duration']}
    Should Be Equal    ${activity_json['is_active']}    ${activity_data['is_active']}
    
    # Verify arrays are preserved
    Lists Should Be Equal    ${activity_json['required_fields']}    ${activity_data['required_fields']}
    Lists Should Be Equal    ${activity_json['success_criteria']}    ${activity_data['success_criteria']}
    
    # Verify complex objects are preserved
    Dictionaries Should Be Equal    ${activity_json['validation_rules']}    ${activity_data['validation_rules']}
    
    # Verify metadata
    Should Be Equal As Integers    ${activity_json['version']}    1
    Should Not Be Empty    ${activity_json['created_at']}
    Should Not Be Empty    ${activity_json['updated_at']}
    
    # Cleanup
    DELETE On Session    api    /activities/${activity_json['id']}    headers=${HEADERS}

AC002: Create Activity With Minimal Required Data
    [Documentation]    Test creating an activity with only required fields
    [Tags]    create    positive    minimal    contract
    
    ${minimal_data}=    Create Dictionary
    ...    name=Minimal Activity
    ...    erpnext_module=Sales
    ...    action_type=read
    ...    target_doctype=Customer
    
    ${response}=    POST On Session    api    /activities    json=${minimal_data}    headers=${HEADERS}
    
    Should Be Equal As Strings    ${response.status_code}    201
    
    ${activity_json}=    Set Variable    ${response.json()}
    Validate Activity Response Schema    ${activity_json}
    
    # Verify required fields
    Should Be Equal As Strings    ${activity_json['name']}    Minimal Activity
    Should Be Equal As Strings    ${activity_json['erpnext_module']}    Sales
    Should Be Equal As Strings    ${activity_json['action_type']}    read
    Should Be Equal As Strings    ${activity_json['target_doctype']}    Customer
    
    # Verify defaults for optional fields
    Should Be Equal As Strings    ${activity_json['description']}    ${EMPTY}
    Should Be Empty    ${activity_json['required_fields']}
    Should Be Empty    ${activity_json['validation_rules']}
    Should Be Empty    ${activity_json['success_criteria']}
    Should Be Equal As Integers    ${activity_json['complexity_score']}    1
    Should Be Equal As Integers    ${activity_json['estimated_duration']}    60
    Should Be Equal    ${activity_json['is_active']}    ${True}
    
    # Cleanup
    DELETE On Session    api    /activities/${activity_json['id']}    headers=${HEADERS}

AC003: Create Activity With Invalid Data Should Fail
    [Documentation]    Test creating an activity with invalid data returns appropriate errors
    [Tags]    create    negative    validation    contract
    
    # Test missing required field - name
    ${invalid_data}=    Create Dictionary
    ...    erpnext_module=Sales
    ...    action_type=create
    ...    target_doctype=Sales Order
    
    ${response}=    POST On Session    api    /activities    json=${invalid_data}    headers=${HEADERS}    expected_status=422
    Should Be Equal As Strings    ${response.status_code}    422
    
    ${error_json}=    Set Variable    ${response.json()}
    Should Contain    ${error_json['detail']}    name
    
    # Test invalid ERPNext module
    ${invalid_module_data}=    Create Dictionary
    ...    name=Test Activity
    ...    erpnext_module=InvalidModule
    ...    action_type=create
    ...    target_doctype=Sales Order
    
    ${response}=    POST On Session    api    /activities    json=${invalid_module_data}    headers=${HEADERS}    expected_status=422
    Should Be Equal As Strings    ${response.status_code}    422
    
    # Test invalid action type
    ${invalid_action_data}=    Create Dictionary
    ...    name=Test Activity
    ...    erpnext_module=Sales
    ...    action_type=invalid_action
    ...    target_doctype=Sales Order
    
    ${response}=    POST On Session    api    /activities    json=${invalid_action_data}    headers=${HEADERS}    expected_status=422
    Should Be Equal As Strings    ${response.status_code}    422

AC004: Read Activity By ID
    [Documentation]    Test retrieving an activity by its ID
    [Tags]    read    positive    contract
    
    # Create test activity
    ${activity_id}=    Create Valid Activity
    
    # Retrieve the activity
    ${response}=    GET On Session    api    /activities/${activity_id}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${activity_json}=    Set Variable    ${response.json()}
    Validate Activity Response Schema    ${activity_json}
    
    Should Be Equal As Strings    ${activity_json['id']}    ${activity_id}
    Should Be Equal As Strings    ${activity_json['name']}    Create Sales Order
    
    # Cleanup
    DELETE On Session    api    /activities/${activity_id}    headers=${HEADERS}

AC005: Read Non-Existent Activity Should Return 404
    [Documentation]    Test retrieving a non-existent activity returns 404
    [Tags]    read    negative    contract
    
    ${fake_id}=    Set Variable    550e8400-e29b-41d4-a716-446655440000
    
    ${response}=    GET On Session    api    /activities/${fake_id}    headers=${HEADERS}    expected_status=404
    Should Be Equal As Strings    ${response.status_code}    404
    
    ${error_json}=    Set Variable    ${response.json()}
    Should Contain    ${error_json['detail']}    not found

AC006: List Activities With Default Pagination
    [Documentation]    Test listing activities with default pagination
    [Tags]    list    positive    contract
    
    # Create multiple test activities
    ${activity_id_1}=    Create Valid Activity
    
    ${activity_data_2}=    Evaluate    json.loads('{"name": "Update Customer", "erpnext_module": "CRM", "action_type": "update", "target_doctype": "Customer"}')    json
    ${activity_id_2}=    Create Valid Activity    ${activity_data_2}
    
    # List activities
    ${response}=    GET On Session    api    /activities    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${list_json}=    Set Variable    ${response.json()}
    Should Contain    ${list_json}    items
    Should Contain    ${list_json}    total
    Should Contain    ${list_json}    page
    Should Contain    ${list_json}    per_page
    Should Contain    ${list_json}    has_next
    Should Contain    ${list_json}    has_prev
    
    # Verify we have at least our test activities
    Should Be True    ${list_json['total']} >= 2
    Should Be True    len(${list_json['items']}) >= 2
    
    # Verify response schema for each activity
    FOR    ${activity}    IN    @{list_json['items']}
        Validate Activity Response Schema    ${activity}
    END
    
    # Cleanup
    DELETE On Session    api    /activities/${activity_id_1}    headers=${HEADERS}
    DELETE On Session    api    /activities/${activity_id_2}    headers=${HEADERS}

AC007: List Activities With Custom Pagination
    [Documentation]    Test listing activities with custom pagination parameters
    [Tags]    list    positive    pagination    contract
    
    # Create test activities
    ${activity_id_1}=    Create Valid Activity
    ${activity_data_2}=    Evaluate    json.loads('{"name": "Activity 2", "erpnext_module": "CRM", "action_type": "read", "target_doctype": "Customer"}')    json
    ${activity_id_2}=    Create Valid Activity    ${activity_data_2}
    
    # Test custom page size
    ${params}=    Create Dictionary    per_page=1    page=1
    ${response}=    GET On Session    api    /activities    params=${params}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${list_json}=    Set Variable    ${response.json()}
    Should Be Equal As Integers    ${list_json['per_page']}    1
    Should Be Equal As Integers    ${list_json['page']}    1
    Should Be True    len(${list_json['items']}) <= 1
    
    # Cleanup
    DELETE On Session    api    /activities/${activity_id_1}    headers=${HEADERS}
    DELETE On Session    api    /activities/${activity_id_2}    headers=${HEADERS}

AC008: Filter Activities By ERPNext Module
    [Documentation]    Test filtering activities by ERPNext module
    [Tags]    list    filter    positive    contract
    
    # Create activities with different modules
    ${sales_activity_data}=    Evaluate    json.loads('{"name": "Sales Activity", "erpnext_module": "Sales", "action_type": "create", "target_doctype": "Sales Order"}')    json
    ${sales_activity_id}=    Create Valid Activity    ${sales_activity_data}
    
    ${crm_activity_data}=    Evaluate    json.loads('{"name": "CRM Activity", "erpnext_module": "CRM", "action_type": "create", "target_doctype": "Customer"}')    json
    ${crm_activity_id}=    Create Valid Activity    ${crm_activity_data}
    
    # Filter by Sales module
    ${params}=    Create Dictionary    erpnext_module=Sales
    ${response}=    GET On Session    api    /activities    params=${params}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${list_json}=    Set Variable    ${response.json()}
    Should Be True    ${list_json['total']} >= 1
    
    # Verify all returned activities are from Sales module
    FOR    ${activity}    IN    @{list_json['items']}
        Should Be Equal As Strings    ${activity['erpnext_module']}    Sales
    END
    
    # Cleanup
    DELETE On Session    api    /activities/${sales_activity_id}    headers=${HEADERS}
    DELETE On Session    api    /activities/${crm_activity_id}    headers=${HEADERS}

AC009: Update Activity With Valid Data
    [Documentation]    Test updating an activity with valid data
    [Tags]    update    positive    contract
    
    # Create test activity
    ${activity_id}=    Create Valid Activity
    
    # Update the activity
    ${update_data}=    Create Dictionary
    ...    name=Updated Sales Order Activity
    ...    description=Updated description for creating sales orders
    ...    complexity_score=7
    ...    estimated_duration=450
    
    ${response}=    PUT On Session    api    /activities/${activity_id}    json=${update_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${activity_json}=    Set Variable    ${response.json()}
    Validate Activity Response Schema    ${activity_json}
    
    # Verify updates were applied
    Should Be Equal As Strings    ${activity_json['name']}    Updated Sales Order Activity
    Should Be Equal As Strings    ${activity_json['description']}    Updated description for creating sales orders
    Should Be Equal As Integers    ${activity_json['complexity_score']}    7
    Should Be Equal As Integers    ${activity_json['estimated_duration']}    450
    
    # Verify version was incremented
    Should Be Equal As Integers    ${activity_json['version']}    2
    
    # Verify unchanged fields remain the same
    Should Be Equal As Strings    ${activity_json['erpnext_module']}    Sales
    Should Be Equal As Strings    ${activity_json['action_type']}    create
    Should Be Equal As Strings    ${activity_json['target_doctype']}    Sales Order
    
    # Cleanup
    DELETE On Session    api    /activities/${activity_id}    headers=${HEADERS}

AC010: Update Non-Existent Activity Should Return 404
    [Documentation]    Test updating a non-existent activity returns 404
    [Tags]    update    negative    contract
    
    ${fake_id}=    Set Variable    550e8400-e29b-41d4-a716-446655440000
    ${update_data}=    Create Dictionary    name=Updated Name
    
    ${response}=    PUT On Session    api    /activities/${fake_id}    json=${update_data}    headers=${HEADERS}    expected_status=404
    Should Be Equal As Strings    ${response.status_code}    404

AC011: Delete Activity
    [Documentation]    Test deleting an activity
    [Tags]    delete    positive    contract
    
    # Create test activity
    ${activity_id}=    Create Valid Activity
    
    # Verify activity exists
    ${response}=    GET On Session    api    /activities/${activity_id}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    # Delete the activity
    ${response}=    DELETE On Session    api    /activities/${activity_id}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    204
    
    # Verify activity no longer exists
    ${response}=    GET On Session    api    /activities/${activity_id}    headers=${HEADERS}    expected_status=404
    Should Be Equal As Strings    ${response.status_code}    404

AC012: Delete Non-Existent Activity Should Return 404
    [Documentation]    Test deleting a non-existent activity returns 404
    [Tags]    delete    negative    contract
    
    ${fake_id}=    Set Variable    550e8400-e29b-41d4-a716-446655440000
    
    ${response}=    DELETE On Session    api    /activities/${fake_id}    headers=${HEADERS}    expected_status=404
    Should Be Equal As Strings    ${response.status_code}    404

AC013: Activity Statistics Endpoint
    [Documentation]    Test retrieving activity statistics
    [Tags]    statistics    positive    contract
    
    # Create test activities with different modules and types
    ${sales_activity_id}=    Create Valid Activity
    
    ${crm_data}=    Evaluate    json.loads('{"name": "CRM Activity", "erpnext_module": "CRM", "action_type": "read", "target_doctype": "Customer", "is_active": false}')    json
    ${crm_activity_id}=    Create Valid Activity    ${crm_data}
    
    # Get statistics
    ${response}=    GET On Session    api    /activities/statistics    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${stats_json}=    Set Variable    ${response.json()}
    Should Contain    ${stats_json}    total
    Should Contain    ${stats_json}    active
    Should Contain    ${stats_json}    inactive
    Should Contain    ${stats_json}    by_module
    Should Contain    ${stats_json}    by_action_type
    Should Contain    ${stats_json}    complexity_distribution
    
    # Verify statistics are numbers
    Should Be True    ${stats_json['total']} >= 2
    Should Be True    ${stats_json['active']} >= 1
    Should Be True    ${stats_json['inactive']} >= 1
    
    # Verify by_module contains our test modules
    Should Contain    ${stats_json['by_module']}    Sales
    Should Contain    ${stats_json['by_module']}    CRM
    
    # Cleanup
    DELETE On Session    api    /activities/${sales_activity_id}    headers=${HEADERS}
    DELETE On Session    api    /activities/${crm_activity_id}    headers=${HEADERS}

AC014: Activate and Deactivate Activity
    [Documentation]    Test activating and deactivating activities
    [Tags]    activation    positive    contract
    
    # Create inactive activity
    ${inactive_data}=    Evaluate    json.loads('{"name": "Inactive Activity", "erpnext_module": "Sales", "action_type": "create", "target_doctype": "Sales Order", "is_active": false}')    json
    ${activity_id}=    Create Valid Activity    ${inactive_data}
    
    # Activate the activity
    ${response}=    POST On Session    api    /activities/${activity_id}/activate    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${activity_json}=    Set Variable    ${response.json()}
    Should Be Equal    ${activity_json['is_active']}    ${True}
    Should Be Equal As Integers    ${activity_json['version']}    2
    
    # Deactivate the activity
    ${response}=    POST On Session    api    /activities/${activity_id}/deactivate    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${activity_json}=    Set Variable    ${response.json()}
    Should Be Equal    ${activity_json['is_active']}    ${False}
    Should Be Equal As Integers    ${activity_json['version']}    3
    
    # Cleanup
    DELETE On Session    api    /activities/${activity_id}    headers=${HEADERS}

AC015: Bulk Operations
    [Documentation]    Test bulk operations on activities
    [Tags]    bulk    positive    contract
    
    # Create multiple test activities
    ${activity_id_1}=    Create Valid Activity
    ${activity_data_2}=    Evaluate    json.loads('{"name": "Activity 2", "erpnext_module": "CRM", "action_type": "read", "target_doctype": "Customer"}')    json
    ${activity_id_2}=    Create Valid Activity    ${activity_data_2}
    
    # Test bulk activation
    ${bulk_data}=    Create Dictionary    activity_ids=${activity_id_1},${activity_id_2}    action=activate
    ${response}=    POST On Session    api    /activities/bulk    json=${bulk_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${bulk_json}=    Set Variable    ${response.json()}
    Should Contain    ${bulk_json}    updated_count
    Should Contain    ${bulk_json}    updated_ids
    Should Be Equal As Integers    ${bulk_json['updated_count']}    2
    
    # Verify activities were updated
    ${response}=    GET On Session    api    /activities/${activity_id_1}    headers=${HEADERS}
    ${activity_1}=    Set Variable    ${response.json()}
    Should Be Equal    ${activity_1['is_active']}    ${True}
    
    # Cleanup
    DELETE On Session    api    /activities/${activity_id_1}    headers=${HEADERS}
    DELETE On Session    api    /activities/${activity_id_2}    headers=${HEADERS}