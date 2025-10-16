*** Settings ***
Documentation    Test suite for persona validation rules
...              Validates business rules and constraints for test personas
...              including ERPNext role validation, permission formats,
...              and data integrity constraints.

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

# Valid ERPNext roles for testing
@{VALID_ERPNEXT_ROLES}   Administrator    System Manager    Sales Manager
...                      Sales User       Purchase Manager   Purchase User
...                      Stock Manager    Stock User         Accounts Manager
...                      Accounts User    Employee           HR Manager
...                      HR User          Projects Manager   Projects User
...                      Website Manager  Website User       Customer
...                      Supplier         Manufacturing Manager
...                      Manufacturing User    Quality Manager

# Invalid ERPNext roles
@{INVALID_ERPNEXT_ROLES}    Invalid Role    NonexistentRole    123Role

# Valid permission formats
@{VALID_PERMISSIONS}     read:sales    write:sales    create:quotation
...                      delete:customer    read:*    write:stock
...                      create:*    admin:system

# Invalid permission formats  
@{INVALID_PERMISSIONS}   invalid_format    123    role:    :action
...                      spaces in permission    special!chars

*** Test Cases ***

Validate Required Fields
    [Documentation]    Test that all required fields are validated
    [Tags]             validation    negative    required_fields
    
    # Test missing name
    ${invalid_data}=    Create Dictionary
    ...    description=Persona missing name
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400
    Validate Error Contains Field    ${response.json()}    name
    
    # Test missing description (if required)
    ${invalid_data}=    Create Dictionary
    ...    name=Test Persona
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400
    Validate Error Contains Field    ${response.json()}    description

Validate Persona Name Constraints
    [Documentation]    Test persona name validation rules
    [Tags]             validation    negative    name
    
    # Test empty name
    ${invalid_data}=    Create Dictionary
    ...    name=${EMPTY}
    ...    description=Test description
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400
    
    # Test name too long (over 255 characters)
    ${long_name}=    Set Variable    ${'x' * 256}
    ${invalid_data}=    Create Dictionary
    ...    name=${long_name}
    ...    description=Test description
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400
    
    # Test special characters in name
    ${invalid_name}=    Set Variable    Test<>Persona!@#
    ${invalid_data}=    Create Dictionary
    ...    name=${invalid_name}
    ...    description=Test description
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400

Validate ERPNext Roles Format
    [Documentation]    Test ERPNext roles validation
    [Tags]             validation    negative    erpnext_roles
    
    # Test invalid role names
    FOR    ${invalid_role}    IN    @{INVALID_ERPNEXT_ROLES}
        ${invalid_data}=    Create Dictionary
        ...    name=Test Persona Invalid Role
        ...    description=Test description
        ...    erpnext_roles=${invalid_role}
        
        ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
        ...    json=${invalid_data}
        ...    headers=${AUTH_HEADERS}
        ...    expected_status=400
        
        Should Be Equal As Integers    ${response.status_code}    400
        Log    Invalid role ${invalid_role} correctly rejected
    END
    
    # Test empty roles
    ${invalid_data}=    Create Dictionary
    ...    name=Test Persona Empty Roles
    ...    description=Test description
    ...    erpnext_roles=${EMPTY}
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400

Validate Valid ERPNext Roles
    [Documentation]    Test that valid ERPNext roles are accepted
    [Tags]             validation    positive    erpnext_roles
    
    # Test single valid role
    ${valid_data}=    Create Dictionary
    ...    name=Valid Single Role Persona
    ...    description=Test description with single role
    ...    erpnext_roles=Sales Manager
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${valid_data}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    201
    Set Test Variable    ${SINGLE_ROLE_ID}    ${response.json()['id']}
    
    # Test multiple valid roles
    ${valid_roles}=    Set Variable    Sales Manager,Sales User,Employee
    ${valid_data}=    Create Dictionary
    ...    name=Valid Multiple Roles Persona
    ...    description=Test description with multiple roles
    ...    erpnext_roles=${valid_roles}
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${valid_data}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    201
    Set Test Variable    ${MULTI_ROLE_ID}    ${response.json()['id']}

Validate Permission Format
    [Documentation]    Test permission string format validation
    [Tags]             validation    negative    permissions
    
    # Test invalid permission formats
    FOR    ${invalid_perm}    IN    @{INVALID_PERMISSIONS}
        ${invalid_data}=    Create Dictionary
        ...    name=Test Invalid Permission
        ...    description=Test description
        ...    erpnext_roles=User
        ...    permissions=${invalid_perm}
        
        ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
        ...    json=${invalid_data}
        ...    headers=${AUTH_HEADERS}
        ...    expected_status=400
        
        Should Be Equal As Integers    ${response.status_code}    400
        Log    Invalid permission ${invalid_perm} correctly rejected
    END

Validate Valid Permission Formats
    [Documentation]    Test that valid permission formats are accepted
    [Tags]             validation    positive    permissions
    
    # Test various valid permission formats
    FOR    ${valid_perm}    IN    @{VALID_PERMISSIONS}
        ${valid_data}=    Create Dictionary
        ...    name=Valid Permission Test ${valid_perm}
        ...    description=Test description with valid permission
        ...    erpnext_roles=User
        ...    permissions=${valid_perm}
        
        ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
        ...    json=${valid_data}
        ...    headers=${AUTH_HEADERS}
        
        Should Be Equal As Integers    ${response.status_code}    201
        
        # Verify permission was stored correctly
        Should Be Equal    ${response.json()['permissions']}    ${valid_perm}
        
        # Store ID for cleanup
        Append To List    ${CREATED_PERSONA_IDS}    ${response.json()['id']}
    END

Validate Description Length
    [Documentation]    Test description field validation
    [Tags]             validation    negative    description
    
    # Test very long description (over limit)
    ${long_description}=    Set Variable    ${'x' * 2001}
    ${invalid_data}=    Create Dictionary
    ...    name=Long Description Test
    ...    description=${long_description}
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400

Validate Unique Name Constraint
    [Documentation]    Test that persona names must be unique
    [Tags]             validation    negative    uniqueness
    
    # Create first persona
    ${persona_name}=    Set Variable    Unique Name Test Persona
    ${first_data}=    Create Dictionary
    ...    name=${persona_name}
    ...    description=First persona with this name
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${first_data}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    201
    Set Test Variable    ${FIRST_PERSONA_ID}    ${response.json()['id']}
    
    # Try to create second persona with same name
    ${second_data}=    Create Dictionary
    ...    name=${persona_name}
    ...    description=Second persona with same name
    ...    erpnext_roles=Administrator
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${second_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400
    Should Contain    ${response.json()['message']}    already exists

Validate Case Sensitivity In Names
    [Documentation]    Test case sensitivity in persona names
    [Tags]             validation    positive    case_sensitivity
    
    # Create persona with specific case
    ${lower_name}=    Set Variable    test persona case
    ${lower_data}=    Create Dictionary
    ...    name=${lower_name}
    ...    description=Lower case name
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${lower_data}
    ...    headers=${AUTH_HEADERS}
    
    Should Be Equal As Integers    ${response.status_code}    201
    Set Test Variable    ${LOWER_CASE_ID}    ${response.json()['id']}
    
    # Try to create persona with different case
    ${upper_name}=    Set Variable    TEST PERSONA CASE
    ${upper_data}=    Create Dictionary
    ...    name=${upper_name}
    ...    description=Upper case name
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${upper_data}
    ...    headers=${AUTH_HEADERS}
    
    # Should succeed if names are case-sensitive, fail if case-insensitive
    IF    ${response.status_code} == 201
        Log    Names are case-sensitive - both personas created
        Set Test Variable    ${UPPER_CASE_ID}    ${response.json()['id']}
    ELSE IF    ${response.status_code} == 400
        Log    Names are case-insensitive - duplicate rejected
        Should Contain    ${response.json()['message']}    already exists
    ELSE
        Fail    Unexpected status code: ${response.status_code}
    END

Validate Boolean Fields
    [Documentation]    Test boolean field validation
    [Tags]             validation    positive    boolean
    
    # Test is_active field with various values
    ${test_cases}=    Create List
    ...    ${True}    ${False}    true    false    1    0
    
    FOR    ${boolean_value}    IN    @{test_cases}
        ${test_data}=    Create Dictionary
        ...    name=Boolean Test ${boolean_value}
        ...    description=Testing boolean value
        ...    erpnext_roles=User
        ...    is_active=${boolean_value}
        
        ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
        ...    json=${test_data}
        ...    headers=${AUTH_HEADERS}
        
        Should Be Equal As Integers    ${response.status_code}    201
        
        # Verify boolean conversion
        ${expected_bool}=    Evaluate    bool($boolean_value)
        Should Be Equal    ${response.json()['is_active']}    ${expected_bool}
        
        Append To List    ${CREATED_PERSONA_IDS}    ${response.json()['id']}
    END

Validate Data Type Constraints
    [Documentation]    Test data type validation for all fields
    [Tags]             validation    negative    data_types
    
    # Test non-string name
    ${invalid_data}=    Create Dictionary
    ...    name=${123}
    ...    description=Test description
    ...    erpnext_roles=User
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400
    
    # Test non-boolean is_active
    ${invalid_data}=    Create Dictionary
    ...    name=Test Data Types
    ...    description=Test description
    ...    erpnext_roles=User
    ...    is_active=not_a_boolean
    
    ${response}=    POST    ${BASE_URL}${PERSONAS_ENDPOINT}
    ...    json=${invalid_data}
    ...    headers=${AUTH_HEADERS}
    ...    expected_status=400
    
    Should Be Equal As Integers    ${response.status_code}    400

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
    
    # Initialize list for storing created persona IDs
    ${created_ids}=    Create List
    Set Suite Variable    ${CREATED_PERSONA_IDS}    ${created_ids}
    
    Log    Test environment setup complete

Cleanup Test Environment
    [Documentation]    Clean up test environment and test data
    
    # Clean up all created personas
    FOR    ${persona_id}    IN    @{CREATED_PERSONA_IDS}
        ${response}=    DELETE    ${BASE_URL}${PERSONAS_ENDPOINT}/${persona_id}
        ...    headers=${AUTH_HEADERS}
        Log    Deleted persona ${persona_id}
    END
    
    # Clean up single role persona if exists
    IF    '${SINGLE_ROLE_ID}' != '${EMPTY}'
        DELETE    ${BASE_URL}${PERSONAS_ENDPOINT}/${SINGLE_ROLE_ID}
        ...    headers=${AUTH_HEADERS}
    END
    
    # Clean up multi role persona if exists
    IF    '${MULTI_ROLE_ID}' != '${EMPTY}'
        DELETE    ${BASE_URL}${PERSONAS_ENDPOINT}/${MULTI_ROLE_ID}
        ...    headers=${AUTH_HEADERS}
    END
    
    # Clean up unique name test persona if exists
    IF    '${FIRST_PERSONA_ID}' != '${EMPTY}'
        DELETE    ${BASE_URL}${PERSONAS_ENDPOINT}/${FIRST_PERSONA_ID}
        ...    headers=${AUTH_HEADERS}
    END
    
    # Clean up case sensitivity test personas if exist
    IF    '${LOWER_CASE_ID}' != '${EMPTY}'
        DELETE    ${BASE_URL}${PERSONAS_ENDPOINT}/${LOWER_CASE_ID}
        ...    headers=${AUTH_HEADERS}
    END
    
    IF    '${UPPER_CASE_ID}' != '${EMPTY}'
        DELETE    ${BASE_URL}${PERSONAS_ENDPOINT}/${UPPER_CASE_ID}
        ...    headers=${AUTH_HEADERS}
    END
    
    # Delete HTTP session
    Delete All Sessions
    
    Log    Test environment cleanup complete

Validate Error Contains Field
    [Arguments]    ${error_response}    ${field_name}
    [Documentation]    Validate that error response mentions specific field
    
    # Check if error response has details about the field
    ${error_message}=    Get From Dictionary    ${error_response}    message
    Should Contain    ${error_message}    ${field_name}    ignore_case=True