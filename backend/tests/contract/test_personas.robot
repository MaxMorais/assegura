*** Settings ***
Documentation    Test suite for persona CRUD operations
...              Validates that ERPNext consultants can create, read, update,
...              and delete test personas with proper validation and persistence.

Library          RequestsLibrary
Library          Collections
Library          String
Library          DateTime
Suite Setup      Setup Test Environment
Suite Teardown   Cleanup Test Environment

*** Variables ***
${BASE_URL}              http://localhost:8000
${API_PREFIX}           /api/v1
${PERSONAS_ENDPOINT}    ${API_PREFIX}/personas
${AUTH_TOKEN}           ${EMPTY}

# Test Data
${VALID_PERSONA_NAME}           Sales Manager
${VALID_PERSONA_DESCRIPTION}    Experienced sales manager with full sales module access
${VALID_ERPNEXT_ROLES}          Sales Manager,Sales User,Employee
${VALID_PERMISSIONS}            read:sales,write:sales,create:quotation

${UPDATED_PERSONA_NAME}         Senior Sales Manager
${UPDATED_DESCRIPTION}          Senior sales manager with additional permissions

*** Test Cases ***

Create Valid Persona
    [Documentation]    Test creating a new persona with valid data
    [Tags]             create    positive    persona
    
    ${persona_data}=    Create Dictionary
    ...    name=${VALID_PERSONA_NAME}
    ...    description=${VALID_PERSONA_DESCRIPTION}
    ...    erpnext_roles=${VALID_ERPNEXT_ROLES}
    ...    permissions=${VALID_PERMISSIONS}
    ...    is_active=${True}
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${persona_data}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    201
    
    # Validate response structure
    Dictionary Should Contain Key    ${response.json()}    id
    Dictionary Should Contain Key    ${response.json()}    name
    Dictionary Should Contain Key    ${response.json()}    created_at
    
    # Validate response data
    Should Be Equal    ${response.json()['name']}    ${VALID_PERSONA_NAME}
    Should Be Equal    ${response.json()['description']}    ${VALID_PERSONA_DESCRIPTION}
    Should Be True     ${response.json()['is_active']}
    
    # Store persona ID for later tests
    Set Suite Variable    ${CREATED_PERSONA_ID}    ${response.json()['id']}

Create Persona With Duplicate Name Should Fail
    [Documentation]    Test that creating a persona with duplicate name fails
    [Tags]             create    negative    validation    persona
    
    ${persona_data}=    Create Dictionary
    ...    name=${VALID_PERSONA_NAME}
    ...    description=Another persona with same name
    ...    erpnext_roles=User
    ...    permissions=read:basic
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${persona_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400
    Dictionary Should Contain Key    ${response.json()}    message
    Should Contain    ${response.json()['message']}    already exists

Create Persona With Invalid Data Should Fail
    [Documentation]    Test creating persona with invalid/missing required fields
    [Tags]             create    negative    validation    persona
    
    # Test missing name
    ${invalid_data}=    Create Dictionary
    ...    description=Persona without name
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400
    
    # Test empty name
    ${invalid_data}=    Create Dictionary
    ...    name=${EMPTY}
    ...    description=Persona with empty name
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400

Get All Personas
    [Documentation]    Test retrieving list of all personas
    [Tags]             read    positive    persona
    
    ${response}=    GET    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    200
    
    # Response should be a list
    Should Be True    isinstance($response.json(), list)
    
    # Should contain at least one persona (the one we created)
    ${personas_count}=    Get Length    ${response.json()}
    Should Be True    ${personas_count} >= 1
    
    # Verify our created persona is in the list
    ${persona_found}=    Set Variable    ${False}
    FOR    ${persona}    IN    @{response.json()}
        IF    '${persona['id']}' == '${CREATED_PERSONA_ID}'
            Set Variable    ${persona_found}    ${True}
            Should Be Equal    ${persona['name']}    ${VALID_PERSONA_NAME}
        END
    END
    Should Be True    ${persona_found}

Get Persona By ID
    [Documentation]    Test retrieving a specific persona by ID
    [Tags]             read    positive    persona
    
    ${response}=    GET    ${BASE_URL}${PERSONAS_ENDPOINT}/${CREATED_PERSONA_ID}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    200
    
    # Validate response structure and data
    Should Be Equal    ${response.json()['id']}    ${CREATED_PERSONA_ID}
    Should Be Equal    ${response.json()['name']}    ${VALID_PERSONA_NAME}
    Should Be Equal    ${response.json()['description']}    ${VALID_PERSONA_DESCRIPTION}
    Should Be True     ${response.json()['is_active']}

Get Nonexistent Persona Should Fail
    [Documentation]    Test retrieving a persona that doesn't exist
    [Tags]             read    negative    persona
    
    ${nonexistent_id}=    Set Variable    99999
    
    ${response}=    GET    ${BASE_URL}${PERSONAS_ENDPOINT}/${nonexistent_id}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=404
    
    Should Be Equal As Integers    ${response.status_code}    404

Update Persona
    [Documentation]    Test updating an existing persona
    [Tags]             update    positive    persona
    
    ${update_data}=    Create Dictionary
    ...    name=${UPDATED_PERSONA_NAME}
    ...    description=${UPDATED_DESCRIPTION}
    ...    erpnext_roles=Sales Manager,Sales User,Employee,System Manager
    ...    permissions=read:sales,write:sales,create:quotation,delete:quotation
    
    ${response}=    PUT    ${BASE_URL}${PERSONAS_ENDPOINT}/${CREATED_PERSONA_ID}
    ...    json=${update_data}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    200
    
    # Validate updated data
    Should Be Equal    ${response.json()['name']}    ${UPDATED_PERSONA_NAME}
    Should Be Equal    ${response.json()['description']}    ${UPDATED_DESCRIPTION}
    Should Be Equal    ${response.json()['id']}    ${CREATED_PERSONA_ID}
    
    # Verify update_at timestamp was changed
    Dictionary Should Contain Key    ${response.json()}    updated_at
    Should Not Be Equal    ${response.json()['updated_at']}    ${None}

Update Nonexistent Persona Should Fail
    [Documentation]    Test updating a persona that doesn't exist
    [Tags]             update    negative    persona
    
    ${nonexistent_id}=    Set Variable    99999
    ${update_data}=    Create Dictionary    name=Updated Name
    
    ${response}=    PUT    ${BASE_URL}${PERSONAS_ENDPOINT}/${nonexistent_id}
    ...    json=${update_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=404
    
    Should Be Equal As Integers    ${response.status_code}    404

Partial Update Persona
    [Documentation]    Test partially updating a persona (PATCH)
    [Tags]             update    positive    persona
    
    ${patch_data}=    Create Dictionary
    ...    is_active=${False}
    
    ${response}=    PATCH    ${BASE_URL}${PERSONAS_ENDPOINT}/${CREATED_PERSONA_ID}
    ...    json=${patch_data}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    200
    
    # Validate only is_active was changed
    Should Be False    ${response.json()['is_active']}
    Should Be Equal    ${response.json()['name']}    ${UPDATED_PERSONA_NAME}
    Should Be Equal    ${response.json()['description']}    ${UPDATED_DESCRIPTION}

Delete Persona
    [Documentation]    Test deleting a persona
    [Tags]             delete    positive    persona
    
    ${response}=    DELETE    ${BASE_URL}${PERSONAS_ENDPOINT}/${CREATED_PERSONA_ID}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    204
    
    # Verify persona is deleted by trying to retrieve it
    ${response}=    GET    ${BASE_URL}${PERSONAS_ENDPOINT}/${CREATED_PERSONA_ID}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=404
    
    Should Be Equal As Integers    ${response.status_code}    404

Delete Nonexistent Persona Should Fail
    [Documentation]    Test deleting a persona that doesn't exist
    [Tags]             delete    negative    persona
    
    ${nonexistent_id}=    Set Variable    99999
    
    ${response}=    DELETE    ${BASE_URL}${PERSONAS_ENDPOINT}/${nonexistent_id}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=404
    
    Should Be Equal As Integers    ${response.status_code}    404

Pagination Test
    [Documentation]    Test persona list pagination
    [Tags]             read    positive    persona    pagination
    
    # Create multiple personas for pagination test
    FOR    ${i}    IN RANGE    5
        ${persona_data}=    Create Dictionary
        ...    name=Test Persona ${i}
        ...    description=Test persona number ${i}
        ...    erpnext_roles=User
        ...    permissions=read:basic
        
        ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
        ...    json=${persona_data}
        ...    headers=${AUTH_HEADERS}
        
        Should Be Equal As Integers    ${response.status_code}    201
    END
    
    # Test pagination with page_size=2
    ${response}=    GET    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    params=page_size=2&page=1
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    200
    
    # Should return pagination metadata
    Dictionary Should Contain Key    ${response.json()}    items
    Dictionary Should Contain Key    ${response.json()}    total
    Dictionary Should Contain Key    ${response.json()}    page
    Dictionary Should Contain Key    ${response.json()}    page_size
    Dictionary Should Contain Key    ${response.json()}    has_next
    
    # Should return exactly 2 items
    ${items_count}=    Get Length    ${response.json()['items']}
    Should Be Equal As Integers    ${items_count}    2

*** Keywords ***

Setup Test Environment
    [Documentation]    Set up test environment and authentication
    
    # Create HTTP session
    Create Session    api    ${BASE_URL}
    
    # Set up authentication headers
    ${headers}=    Create Dictionary
    ...    Content-Type=application/json
    ...    Accept=application/json
    
    Set Suite Variable    ${AUTH_HEADERS}    ${headers}
    
    Log    Test environment setup complete

Cleanup Test Environment
    [Documentation]    Clean up test environment and test data
    
    # Clean up any remaining test personas
    ${response}=    GET    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    headers=${AUTH_HEADERS}
    
    IF    ${response.status_code} == 200
        FOR    ${persona}    IN    @{response.json()}
            IF    'Test Persona' in '${persona['name']}'
                DELETE    ${BASE_URL}${PERSONAS_ENDPOINT}/${persona['id']}
                ...    headers=${AUTH_HEADERS}
            END
        END
    END
    
    # Delete HTTP session
    Delete All Sessions
    
    Log    Test environment cleanup complete