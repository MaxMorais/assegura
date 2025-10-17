*** Settings ***
Documentation    Test suite for Robot Framework test generation
...              Validates that the system can generate executable Robot Framework
...              test suites from defined journeys with proper syntax and structure.

Library          RequestsLibrary
Library          Collections
Library          String
Library          DateTime
Suite Setup      Setup Test Environment
Suite Teardown   Cleanup Test Environment

*** Variables ***
${BASE_URL}              http://localhost:8000
${API_PREFIX}           /api/v1
${JOURNEYS_ENDPOINT}    ${API_PREFIX}/journeys
${TEST_SUITES_ENDPOINT} ${API_PREFIX}/test-suites
${AUTH_TOKEN}           ${EMPTY}

# Test Data - Journey ID (would be created by journey tests)
${VALID_JOURNEY_ID}     ${EMPTY}  # Set in setup

*** Test Cases ***

Generate Tests From Valid Journey
    [Documentation]    Test generating Robot Framework tests from a complete journey
    [Tags]             generate    positive    journey

    # Create a test journey first (simplified - in real tests this would be done by journey tests)
    ${journey_id}=    Set Variable    123e4567-e89b-12d3-a456-426614174000  # Mock UUID

    ${response}=    POST    ${BASE_URL}${JOURNEYS_ENDPOINT}/${journey_id}/generate-tests
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    202

    # Validate response structure
    Dictionary Should Contain Key    ${response.json()}    task_id
    Dictionary Should Contain Key    ${response.json()}    estimated_completion

    # Store task ID for status checking
    ${task_id}=    Get From Dictionary    ${response.json()}    task_id
    Set Suite Variable    ${GENERATION_TASK_ID}    ${task_id}

Generate Tests With Invalid Journey ID
    [Documentation]    Test error handling when generating tests from non-existent journey
    [Tags]             generate    negative    journey

    ${invalid_journey_id}=    Set Variable    00000000-0000-0000-0000-000000000000

    ${response}=    POST    ${BASE_URL}${JOURNEYS_ENDPOINT}/${invalid_journey_id}/generate-tests
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    404

    # Validate error response
    Dictionary Should Contain Key    ${response.json()}    detail
    Should Contain    ${response.json()}[detail]    not found

Generate Tests Without Authentication
    [Documentation]    Test that test generation requires authentication
    [Tags]             generate    security    auth

    ${journey_id}=    Set Variable    123e4567-e89b-12d3-a456-426614174000

    ${response}=    POST    ${BASE_URL}${JOURNEYS_ENDPOINT}/${journey_id}/generate-tests

    Should Be Equal As Integers    ${response.status_code}    401

Check Generation Task Status
    [Documentation]    Test checking the status of a test generation task
    [Tags]             generate    status    async

    Skip If    "${GENERATION_TASK_ID}" == "${EMPTY}"    Generation task not created

    ${response}=    GET    ${BASE_URL}${API_PREFIX}/tasks/${GENERATION_TASK_ID}
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate task status structure
    Dictionary Should Contain Key    ${response.json()}    status
    Dictionary Should Contain Key    ${response.json()}    progress

    ${status}=    Get From Dictionary    ${response.json()}    status
    Should Be True    "${status}" in ["pending", "running", "completed", "failed"]

Retrieve Generated Test Suite
    [Documentation]    Test retrieving the generated Robot Framework test suite
    [Tags]             generate    retrieve    robot

    Skip If    "${GENERATION_TASK_ID}" == "${EMPTY}"    Generation task not completed

    # Wait for generation to complete (in real implementation)
    Sleep    2s

    ${response}=    GET    ${BASE_URL}${TEST_SUITES_ENDPOINT}/${GENERATION_TASK_ID}
    ...    headers=${AUTH_HEADERS}

    # Should return 200 if completed, 202 if still processing
    Should Be True    ${response.status_code} in [200, 202]

    Run Keyword If    ${response.status_code} == 200
    ...    Validate Generated Test Suite    ${response.json()}

Validate Generated Robot Framework Syntax
    [Documentation]    Test that generated Robot Framework code is syntactically valid
    [Tags]             generate    validate    robot

    Skip If    "${GENERATION_TASK_ID}" == "${EMPTY}"    Generation task not completed

    ${response}=    GET    ${BASE_URL}${TEST_SUITES_ENDPOINT}/${GENERATION_TASK_ID}/validate
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    200

    # Validate validation response
    Dictionary Should Contain Key    ${response.json()}    is_valid
    Dictionary Should Contain Key    ${response.json()}    syntax_errors

    ${is_valid}=    Get From Dictionary    ${response.json()}    is_valid
    Should Be True    ${is_valid}

Generate Tests With Complex Journey
    [Documentation]    Test generating tests from journey with multiple steps and actions
    [Tags]             generate    complex    journey

    ${complex_journey_id}=    Set Variable    456e7890-e89b-12d3-a456-426614174001

    ${response}=    POST    ${BASE_URL}${JOURNEYS_ENDPOINT}/${complex_journey_id}/generate-tests
    ...    headers=${AUTH_HEADERS}

    Should Be Equal As Integers    ${response.status_code}    202

    # Validate response contains additional metadata for complex journeys
    Dictionary Should Contain Key    ${response.json()}    task_id
    Dictionary Should Contain Key    ${response.json()}    estimated_completion
    Dictionary Should Contain Key    ${response.json()}    complexity_score

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
    Set Suite Variable    ${GENERATION_TASK_ID}    ${EMPTY}

Cleanup Test Environment
    [Documentation]    Clean up test environment
    Delete All Sessions

Validate Generated Test Suite
    [Documentation]    Validate the structure of a generated test suite
    [Arguments]    ${test_suite}

    Dictionary Should Contain Key    ${test_suite}    id
    Dictionary Should Contain Key    ${test_suite}    journey_id
    Dictionary Should Contain Key    ${test_suite}    robot_framework_code
    Dictionary Should Contain Key    ${test_suite}    generated_at
    Dictionary Should Contain Key    ${test_suite}    test_data_template

    # Validate Robot Framework code structure
    ${robot_code}=    Get From Dictionary    ${test_suite}    robot_framework_code
    Should Contain    ${robot_code}    *** Settings ***
    Should Contain    ${robot_code}    *** Test Cases ***
    Should Contain    ${robot_code}    *** Keywords ***

    # Validate test data template
    ${test_data}=    Get From Dictionary    ${test_suite}    test_data_template
    Dictionary Should Contain Key    ${test_data}    entities
    Dictionary Should Contain Key    ${test_data}    parameters