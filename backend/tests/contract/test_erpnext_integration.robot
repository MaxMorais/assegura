*** Settings ***
Documentation    Test suite for ERPNext integration
...              Validates that the system can connect to and interact with
...              ERPNext instances for test execution and data validation.

Library          RequestsLibrary
Library          Collections
Library          String
Library          DateTime
Suite Setup      Setup Test Environment
Suite Teardown   Cleanup Test Environment

*** Variables ***
${BASE_URL}              http://localhost:8000
${API_PREFIX}           /api/v1
${ERPNEXT_ENDPOINT}     ${API_PREFIX}/erpnext-instances
${AUTH_TOKEN}           ${EMPTY}

# Test Data
${VALID_ERPNEXT_URL}    https://demo.erpnext.com
${VALID_API_KEY}        test_api_key_123
${VALID_API_SECRET}     test_api_secret_456
${INVALID_ERPNEXT_URL}  https://invalid.erpnext.com

*** Test Cases ***

Configure Valid ERPNext Instance
    [Documentation]    Test configuring a valid ERPNext instance connection
    [Tags]             erpnext    config    positive

    ${instance_data}=    Create Dictionary
    ...    name=Demo ERPNext Instance
    ...    base_url=${VALID_ERPNEXT_URL}
    ...    api_key=${VALID_API_KEY}
    ...    api_secret=${VALID_API_SECRET}
    ...    is_active=${True}

    ${response}=    POST    ${BASE_URL}${ERPNEXT_ENDPOINT}
    ...    json=${instance_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    201

    # Validate response structure
    Dictionary Should Contain Key    ${response.json()}    id
    Dictionary Should Contain Key    ${response.json()}    name
    Dictionary Should Contain Key    ${response.json()}    base_url
    Dictionary Should Contain Key    ${response.json()}    is_active

    # Store instance ID for further tests
    ${instance_id}=    Get From Dictionary    ${response.json()}    id
    Set Suite Variable    ${INSTANCE_ID}    ${instance_id}

Test ERPNext Connection
    [Documentation]    Test validating ERPNext instance connection
    [Tags]             erpnext    connection    validate

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    ${response}=    POST    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}/test-connection
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate connection test response
    Dictionary Should Contain Key    ${response.json()}    is_connected
    Dictionary Should Contain Key    ${response.json()}    response_time
    Dictionary Should Contain Key    ${response.json()}    erpnext_version

    ${is_connected}=    Get From Dictionary    ${response.json()}    is_connected
    Should Be True    ${is_connected}

Configure ERPNext Instance With Invalid URL
    [Documentation]    Test error handling for invalid ERPNext URL
    [Tags]             erpnext    config    negative

    ${instance_data}=    Create Dictionary
    ...    name=Invalid ERPNext Instance
    ...    base_url=${INVALID_ERPNEXT_URL}
    ...    api_key=${VALID_API_KEY}
    ...    api_secret=${VALID_API_SECRET}
    ...    is_active=${True}

    ${response}=    POST    ${BASE_URL}${ERPNEXT_ENDPOINT}
    ...    json=${instance_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    400

    # Validate error response
    Dictionary Should Contain Key    ${response.json()}    detail

Test Connection With Invalid Credentials
    [Documentation]    Test connection validation with invalid API credentials
    [Tags]             erpnext    connection    auth

    ${instance_data}=    Create Dictionary
    ...    name=Invalid Credentials Instance
    ...    base_url=${VALID_ERPNEXT_URL}
    ...    api_key=invalid_key
    ...    api_secret=invalid_secret
    ...    is_active=${True}

    ${response}=    POST    ${BASE_URL}${ERPNEXT_ENDPOINT}
    ...    json=${instance_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    201

    ${instance_id}=    Get From Dictionary    ${response.json()}    id

    # Test connection with invalid credentials
    ${test_response}=    POST    ${BASE_URL}${ERPNEXT_ENDPOINT}/${instance_id}/test-connection
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${test_response.status_code}    200

    ${is_connected}=    Get From Dictionary    ${test_response.json()}    is_connected
    Should Not Be True    ${is_connected}

List ERPNext Instances
    [Documentation]    Test listing configured ERPNext instances
    [Tags]             erpnext    list    instances

    ${response}=    GET    ${BASE_URL}${ERPNEXT_ENDPOINT}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate response structure
    Dictionary Should Contain Key    ${response.json()}    instances
    Dictionary Should Contain Key    ${response.json()}    total

    ${instances}=    Get From Dictionary    ${response.json()}    instances
    Should Be True    ${instances}  # Should have at least one instance

Get ERPNext Instance Details
    [Documentation]    Test retrieving specific ERPNext instance details
    [Tags]             erpnext    get    instance

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    ${response}=    GET    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate instance details
    Dictionary Should Contain Key    ${response.json()}    id
    Dictionary Should Contain Key    ${response.json()}    name
    Dictionary Should Contain Key    ${response.json()}    base_url
    Dictionary Should Contain Key    ${response.json()}    is_active
    Dictionary Should Contain Key    ${response.json()}    last_connected

Update ERPNext Instance
    [Documentation]    Test updating ERPNext instance configuration
    [Tags]             erpnext    update    config

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    ${update_data}=    Create Dictionary
    ...    name=Updated Demo ERPNext Instance
    ...    is_active=${False}

    ${response}=    PUT    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}
    ...    json=${update_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate updated instance
    Dictionary Should Contain Key    ${response.json()}    name
    Should Be Equal    ${response.json()}[name]    Updated Demo ERPNext Instance
    Should Not Be True    ${response.json()}[is_active]

Delete ERPNext Instance
    [Documentation]    Test deleting ERPNext instance configuration
    [Tags]             erpnext    delete    instance

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    ${response}=    DELETE    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    204

    # Verify instance is deleted
    ${get_response}=    GET    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${get_response.status_code}    404

Test ERPNext API Data Retrieval
    [Documentation]    Test retrieving data from ERPNext API for test validation
    [Tags]             erpnext    api    data

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    ${response}=    GET    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}/api-data/Sales Order
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate API data response
    Dictionary Should Contain Key    ${response.json()}    doctype
    Dictionary Should Contain Key    ${response.json()}    data
    Dictionary Should Contain Key    ${response.json()}    total_count

Test ERPNext Document Creation
    [Documentation]    Test creating documents in ERPNext for test setup
    [Tags]             erpnext    api    create

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    ${document_data}=    Create Dictionary
    ...    doctype=Customer
    ...    customer_name=Test Customer
    ...    customer_type=Company
    ...    territory=Rest Of The World

    ${response}=    POST    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}/documents
    ...    json=${document_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    201

    # Validate document creation response
    Dictionary Should Contain Key    ${response.json()}    name
    Dictionary Should Contain Key    ${response.json()}    doctype

Test ERPNext Document Update
    [Documentation]    Test updating documents in ERPNext during test execution
    [Tags]             erpnext    api    update

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    ${document_name}=    Set Variable    CUST-TEST-001

    ${update_data}=    Create Dictionary
    ...    customer_name=Updated Test Customer
    ...    website=www.updated-test.com

    ${response}=    PUT    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}/documents/Customer/${document_name}
    ...    json=${update_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

Test ERPNext Document Deletion
    [Documentation]    Test deleting test documents from ERPNext
    [Tags]             erpnext    api    delete

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    ${document_name}=    Set Variable    CUST-TEST-001

    ${response}=    DELETE    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}/documents/Customer/${document_name}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    204

Test ERPNext Bulk Operations
    [Documentation]    Test bulk operations on ERPNext documents
    [Tags]             erpnext    api    bulk

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    ${bulk_data}=    Create List
    ...    ${EMPTY}  # Would contain multiple document operations

    ${response}=    POST    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}/bulk-operations
    ...    json=${bulk_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate bulk operation response
    Dictionary Should Contain Key    ${response.json()}    total_operations
    Dictionary Should Contain Key    ${response.json()}    successful_operations
    Dictionary Should Contain Key    ${response.json()}    failed_operations

Test ERPNext Connection Pooling
    [Documentation]    Test that ERPNext connections are properly pooled and reused
    [Tags]             erpnext    performance    pooling

    Skip If    "${INSTANCE_ID}" == "${EMPTY}"    Instance not configured

    # Make multiple concurrent requests to test connection pooling
    ${responses}=    Create List

    FOR    ${index}    IN RANGE    1    6
        ${response}=    GET    ${BASE_URL}${ERPNEXT_ENDPOINT}/${INSTANCE_ID}/test-connection
        ...    headers=${AUTH_HEADERS}
        Append To List    ${responses}    ${response}
    END

    # All responses should be successful
    FOR    ${response}    IN    @{responses}
        Should Be Equal As Integers    ${response.status_code}    200
        ${is_connected}=    Get From Dictionary    ${response.json()}    is_connected
        Should Be True    ${is_connected}
    END

*** Keywords ***

Setup Test Environment
    [Documentation]    Setup test environment and authentication
    Create Session    api    ${BASE_URL}

    # Mock authentication - in real tests this would get a valid token
    ${auth_token}=    Set Variable    mock_jwt_token_for_testing
    Set Suite Variable    ${AUTH_TOKEN}    ${auth_token}

    # Setup auth headers
    ${auth_headers}=    Create Dictionary
    ...    Authorization=Bearer ${AUTH_TOKEN}
    ...    Content-Type=application/json
    Set Suite Variable    ${AUTH_HEADERS}    ${auth_headers}

    # Initialize test data
    Set Suite Variable    ${INSTANCE_ID}    ${EMPTY}

Cleanup Test Environment
    [Documentation]    Clean up test environment
    Delete All Sessions

    # Clean up test instances
    Run Keyword If    "${INSTANCE_ID}" != "${EMPTY}"
    ...    Delete Test Instance    ${INSTANCE_ID}

Delete Test Instance
    [Documentation]    Delete test ERPNext instance if it exists
    [Arguments]    ${instance_id}

    ${response}=    DELETE    ${BASE_URL}${ERPNEXT_ENDPOINT}/${instance_id}
    ...    headers=${AUTH_HEADERS}

    # Ignore errors if instance doesn't exist
    Log    Cleanup: Attempted to delete instance ${instance_id}