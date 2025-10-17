*** Settings ***
Documentation    Test suite for cloud test execution
...              Validates that generated test suites can be executed in cloud
...              environments with proper resource management and result collection.

Library          RequestsLibrary
Library          Collections
Library          String
Library          DateTime
Suite Setup      Setup Test Environment
Suite Teardown   Cleanup Test Environment

*** Variables ***
${BASE_URL}              http://localhost:8000
${API_PREFIX}           /api/v1
${TEST_SUITES_ENDPOINT} ${API_PREFIX}/test-suites
${EXECUTIONS_ENDPOINT}  ${API_PREFIX}/executions
${AUTH_TOKEN}           ${EMPTY}

# Test Data
${VALID_TEST_SUITE_ID}  ${EMPTY}  # Set in setup
${EXECUTION_REQUEST}    ${EMPTY}  # Set in setup

*** Test Cases ***

Execute Test Suite Successfully
    [Documentation]    Test executing a generated test suite in cloud environment
    [Tags]             execute    positive    cloud

    ${test_suite_id}=    Set Variable    123e4567-e89b-12d3-a456-426614174000

    ${execution_data}=    Create Dictionary
    ...    erpnext_instance_id=456e7890-e89b-12d3-a456-426614174001
    ...    priority=1
    ...    timeout_minutes=30
    ...    environment_variables=${EMPTY}

    ${response}=    POST    ${BASE_URL}${TEST_SUITES_ENDPOINT}/${test_suite_id}/execute
    ...    json=${execution_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    202

    # Validate response structure
    Dictionary Should Contain Key    ${response.json()}    execution_id
    Dictionary Should Contain Key    ${response.json()}    queue_position
    Dictionary Should Contain Key    ${response.json()}    estimated_start

    # Store execution ID for monitoring
    ${execution_id}=    Get From Dictionary    ${response.json()}    execution_id
    Set Suite Variable    ${EXECUTION_ID}    ${execution_id}

Execute Test Suite With High Priority
    [Documentation]    Test executing test suite with high priority
    [Tags]             execute    priority    cloud

    ${test_suite_id}=    Set Variable    789e0123-e89b-12d3-a456-426614174002

    ${execution_data}=    Create Dictionary
    ...    erpnext_instance_id=456e7890-e89b-12d3-a456-426614174001
    ...    priority=10
    ...    timeout_minutes=15
    ...    environment_variables=${EMPTY}

    ${response}=    POST    ${BASE_URL}${TEST_SUITES_ENDPOINT}/${test_suite_id}/execute
    ...    json=${execution_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    202

    # High priority should have better queue position
    ${queue_position}=    Get From Dictionary    ${response.json()}    queue_position
    Should Be True    ${queue_position} <= 5

Execute Test Suite With Invalid Suite ID
    [Documentation]    Test error handling when executing non-existent test suite
    [Tags]             execute    negative    cloud

    ${invalid_suite_id}=    Set Variable    00000000-0000-0000-0000-000000000000

    ${execution_data}=    Create Dictionary
    ...    erpnext_instance_id=456e7890-e89b-12d3-a456-426614174001
    ...    priority=1

    ${response}=    POST    ${BASE_URL}${TEST_SUITES_ENDPOINT}/${invalid_suite_id}/execute
    ...    json=${execution_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    404

Execute Test Suite With Invalid ERPNext Instance
    [Documentation]    Test error handling when ERPNext instance doesn't exist
    [Tags]             execute    negative    erpnext

    ${test_suite_id}=    Set Variable    123e4567-e89b-12d3-a456-426614174000

    ${execution_data}=    Create Dictionary
    ...    erpnext_instance_id=00000000-0000-0000-0000-000000000000
    ...    priority=1

    ${response}=    POST    ${BASE_URL}${TEST_SUITES_ENDPOINT}/${test_suite_id}/execute
    ...    json=${execution_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    400

Execute Test Suite Without Authentication
    [Documentation]    Test that test execution requires authentication
    [Tags]             execute    security    auth

    ${test_suite_id}=    Set Variable    123e4567-e89b-12d3-a456-426614174000

    ${execution_data}=    Create Dictionary
    ...    erpnext_instance_id=456e7890-e89b-12d3-a456-426614174001
    ...    priority=1

    ${response}=    POST    ${BASE_URL}${TEST_SUITES_ENDPOINT}/${test_suite_id}/execute
    ...    json=${execution_data}

    Should Be Equal As Integers    ${response.status_code}    401

Monitor Execution Status
    [Documentation]    Test monitoring execution status and progress
    [Tags]             execute    monitor    status

    Skip If    "${EXECUTION_ID}" == "${EMPTY}"    Execution not started

    ${response}=    GET    ${BASE_URL}${EXECUTIONS_ENDPOINT}/${EXECUTION_ID}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate execution status structure
    Dictionary Should Contain Key    ${response.json()}    status
    Dictionary Should Contain Key    ${response.json()}    progress
    Dictionary Should Contain Key    ${response.json()}    start_time

    ${status}=    Get From Dictionary    ${response.json()}    status
    Should Be True    "${status}" in ["queued", "running", "completed", "failed", "cancelled"]

Get Execution Results After Completion
    [Documentation]    Test retrieving detailed execution results
    [Tags]             execute    results    complete

    Skip If    "${EXECUTION_ID}" == "${EMPTY}"    Execution not started

    # Wait for execution to complete (in real implementation)
    Sleep    5s

    ${response}=    GET    ${BASE_URL}${EXECUTIONS_ENDPOINT}/${EXECUTION_ID}/results
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate results structure
    Dictionary Should Contain Key    ${response.json()}    execution_id
    Dictionary Should Contain Key    ${response.json()}    status
    Dictionary Should Contain Key    ${response.json()}    pass_count
    Dictionary Should Contain Key    ${response.json()}    fail_count
    Dictionary Should Contain Key    ${response.json()}    execution_log

Cancel Running Execution
    [Documentation]    Test cancelling a running test execution
    [Tags]             execute    cancel    control

    Skip If    "${EXECUTION_ID}" == "${EMPTY}"    Execution not started

    ${response}=    DELETE    ${BASE_URL}${EXECUTIONS_ENDPOINT}/${EXECUTION_ID}
    ...    headers=${AUTH_HEADERS}

    # Should return 202 (accepted) or 200 (cancelled)
    Should Be True    ${response.status_code} in [200, 202]

    # Verify cancellation
    Sleep    2s
    ${status_response}=    GET    ${BASE_URL}${EXECUTIONS_ENDPOINT}/${EXECUTION_ID}
    ...    headers=${AUTH_HEADERS}

    ${status}=    Get From Dictionary    ${status_response.json()}    status
    Should Be Equal    "${status}"    "cancelled"

Execute Test Suite With Environment Variables
    [Documentation]    Test executing test suite with custom environment variables
    [Tags]             execute    environment    config

    ${test_suite_id}=    Set Variable    123e4567-e89b-12d3-a456-426614174000

    ${env_vars}=    Create Dictionary
    ...    ROBOT_OPTIONS=--loglevel DEBUG
    ...    TEST_TIMEOUT=600
    ...    ERPNext_URL=https://test.erpnext.com

    ${execution_data}=    Create Dictionary
    ...    erpnext_instance_id=456e7890-e89b-12d3-a456-426614174001
    ...    priority=1
    ...    environment_variables=${env_vars}

    ${response}=    POST    ${BASE_URL}${TEST_SUITES_ENDPOINT}/${test_suite_id}/execute
    ...    json=${execution_data}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    202

Execute Multiple Test Suites Concurrently
    [Documentation]    Test executing multiple test suites with resource management
    [Tags]             execute    concurrent    resources

    ${suite_ids}=    Create List
    ...    123e4567-e89b-12d3-a456-426614174000
    ...    789e0123-e89b-12d3-a456-426614174002
    ...    456e7890-e89b-12d3-a456-426614174003

    ${execution_ids}=    Create List

    # Start multiple executions
    FOR    ${suite_id}    IN    @{suite_ids}
        ${execution_data}=    Create Dictionary
        ...    erpnext_instance_id=456e7890-e89b-12d3-a456-426614174001
        ...    priority=1

        ${response}=    POST    ${BASE_URL}${TEST_SUITES_ENDPOINT}/${suite_id}/execute
        ...    json=${execution_data}
        ...    headers=${AUTH_HEADERS}

        Should Be Equal As Integers    ${response.status_code}    202

        ${execution_id}=    Get From Dictionary    ${response.json()}    execution_id
        Append To List    ${execution_ids}    ${execution_id}
    END

    # Verify all executions are queued
    Length Should Be    ${execution_ids}    3

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
    Set Suite Variable    ${EXECUTION_ID}    ${EMPTY}

Cleanup Test Environment
    [Documentation]    Clean up test environment
    Delete All Sessions

    # Cancel any running executions
    Run Keyword If    "${EXECUTION_ID}" != "${EMPTY}"
    ...    Cancel Execution If Running    ${EXECUTION_ID}

Cancel Execution If Running
    [Documentation]    Cancel execution if it's still running
    [Arguments]    ${execution_id}

    ${response}=    GET    ${BASE_URL}${EXECUTIONS_ENDPOINT}/${execution_id}
    ...    headers=${AUTH_HEADERS}

    Return If    ${response.status_code} != 200

    ${status}=    Get From Dictionary    ${response.json()}    status

    Run Keyword If    "${status}" in ["queued", "running"]
    ...    DELETE    ${BASE_URL}${EXECUTIONS_ENDPOINT}/${execution_id}
    ...    headers=${AUTH_HEADERS}