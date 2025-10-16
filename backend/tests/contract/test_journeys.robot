*** Settings ***
Documentation    Test suite for Journey CRUD operations
...              Tests the creation, reading, updating, and deletion of test journeys
...              through the ERPNext Test Framework API and domain services.

Library          RequestsLibrary
Library          Collections
Library          String
Library          DateTime
Library          JSONLibrary

Suite Setup      Setup Test Suite
Suite Teardown   Cleanup Test Suite

*** Variables ***
${BASE_URL}              http://localhost:8000/api/v1
${JOURNEYS_ENDPOINT}     ${BASE_URL}/journeys
${VALID_JOURNEY_NAME}    Test Customer Onboarding Journey
${VALID_DESCRIPTION}     Complete customer onboarding process from registration to first sale
${VALID_PERSONA_ID}      550e8400-e29b-41d4-a716-446655440000
${VALID_ACTIVITY_ID}     550e8400-e29b-41d4-a716-446655440001
${TEST_JOURNEY_ID}       ${EMPTY}

*** Test Cases ***

Create Journey With Valid Data
    [Documentation]    Test creating a new journey with all required fields
    [Tags]             journey    create    crud    smoke
    
    ${journey_data}=    Create Dictionary
    ...    name=${VALID_JOURNEY_NAME}
    ...    description=${VALID_DESCRIPTION}
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    ...    steps=@{EMPTY}
    ...    prerequisites=@{EMPTY}
    ...    expected_outcomes=@{EMPTY}
    ...    is_active=${True}
    ...    metadata=${EMPTY_DICT}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    
    Should Be Equal As Numbers    ${response.status_code}    201
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify response structure
    Should Contain    ${response_body}    id
    Should Contain    ${response_body}    name
    Should Contain    ${response_body}    description
    Should Contain    ${response_body}    created_at
    Should Contain    ${response_body}    updated_at
    
    # Verify response values
    Should Be Equal    ${response_body}[name]    ${VALID_JOURNEY_NAME}
    Should Be Equal    ${response_body}[description]    ${VALID_DESCRIPTION}
    Should Be Equal    ${response_body}[persona_id]    ${VALID_PERSONA_ID}
    Should Be Equal    ${response_body}[activity_id]    ${VALID_ACTIVITY_ID}
    Should Be Equal    ${response_body}[is_active]    ${True}
    
    # Store journey ID for cleanup
    Set Suite Variable    ${TEST_JOURNEY_ID}    ${response_body}[id]

Create Journey With Missing Required Fields
    [Documentation]    Test that journey creation fails with missing required fields
    [Tags]             journey    create    validation    negative
    
    # Test missing name
    ${journey_data}=    Create Dictionary
    ...    description=${VALID_DESCRIPTION}
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422
    ${error_body}=    Set Variable    ${response.json()}
    Should Contain    ${error_body}[detail]    name
    
    # Test missing description
    ${journey_data}=    Create Dictionary
    ...    name=${VALID_JOURNEY_NAME}
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422
    
    # Test missing persona_id
    ${journey_data}=    Create Dictionary
    ...    name=${VALID_JOURNEY_NAME}
    ...    description=${VALID_DESCRIPTION}
    ...    activity_id=${VALID_ACTIVITY_ID}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422

Create Journey With Invalid Data
    [Documentation]    Test journey creation with invalid data formats
    [Tags]             journey    create    validation    negative
    
    # Test empty name
    ${journey_data}=    Create Dictionary
    ...    name=${EMPTY}
    ...    description=${VALID_DESCRIPTION}
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422
    
    # Test invalid persona_id format
    ${journey_data}=    Create Dictionary
    ...    name=${VALID_JOURNEY_NAME}
    ...    description=${VALID_DESCRIPTION}
    ...    persona_id=invalid-uuid
    ...    activity_id=${VALID_ACTIVITY_ID}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422
    
    # Test name too long
    ${long_name}=    Generate Random String    300
    ${journey_data}=    Create Dictionary
    ...    name=${long_name}
    ...    description=${VALID_DESCRIPTION}
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422

Create Duplicate Journey Name
    [Documentation]    Test that journey creation fails with duplicate name
    [Tags]             journey    create    validation    negative
    [Setup]            Create Test Journey For Duplication
    
    ${journey_data}=    Create Dictionary
    ...    name=Duplicate Test Journey
    ...    description=Second journey with same name
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}    expected_status=409
    Should Be Equal As Numbers    ${response.status_code}    409
    ${error_body}=    Set Variable    ${response.json()}
    Should Contain    ${error_body}[detail]    already exists

Get Journey By ID
    [Documentation]    Test retrieving a journey by its ID
    [Tags]             journey    read    crud
    [Setup]            Create Test Journey For Reading
    
    ${response}=    GET    ${JOURNEYS_ENDPOINT}/${TEST_JOURNEY_ID}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify journey details
    Should Be Equal    ${response_body}[id]    ${TEST_JOURNEY_ID}
    Should Be Equal    ${response_body}[name]    ${VALID_JOURNEY_NAME}
    Should Be Equal    ${response_body}[description]    ${VALID_DESCRIPTION}
    Should Be Equal    ${response_body}[persona_id]    ${VALID_PERSONA_ID}
    Should Be Equal    ${response_body}[activity_id]    ${VALID_ACTIVITY_ID}

Get Nonexistent Journey
    [Documentation]    Test retrieving a journey that doesn't exist
    [Tags]             journey    read    negative
    
    ${fake_id}=    Set Variable    550e8400-e29b-41d4-a716-999999999999
    ${response}=    GET    ${JOURNEYS_ENDPOINT}/${fake_id}    expected_status=404
    
    Should Be Equal As Numbers    ${response.status_code}    404
    ${error_body}=    Set Variable    ${response.json()}
    Should Contain    ${error_body}[detail]    not found

Get Journey With Invalid UUID
    [Documentation]    Test retrieving journey with invalid UUID format
    [Tags]             journey    read    validation    negative
    
    ${response}=    GET    ${JOURNEYS_ENDPOINT}/invalid-uuid    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422

List Journeys Without Filters
    [Documentation]    Test listing all journeys without filters
    [Tags]             journey    list    crud
    [Setup]            Create Multiple Test Journeys
    
    ${response}=    GET    ${JOURNEYS_ENDPOINT}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify response structure
    Should Contain    ${response_body}    journeys
    Should Contain    ${response_body}    total
    Should Contain    ${response_body}    page
    Should Contain    ${response_body}    per_page
    
    # Verify we have journeys
    ${journey_count}=    Get Length    ${response_body}[journeys]
    Should Be True    ${journey_count} >= 3

List Journeys With Filters
    [Documentation]    Test listing journeys with various filters
    [Tags]             journey    list    filter
    [Setup]            Create Multiple Test Journeys
    
    # Filter by persona_id
    ${response}=    GET    ${JOURNEYS_ENDPOINT}?persona_id=${VALID_PERSONA_ID}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # All returned journeys should have the specified persona_id
    FOR    ${journey}    IN    @{response_body}[journeys]
        Should Be Equal    ${journey}[persona_id]    ${VALID_PERSONA_ID}
    END
    
    # Filter by active status
    ${response}=    GET    ${JOURNEYS_ENDPOINT}?is_active=true
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # All returned journeys should be active
    FOR    ${journey}    IN    @{response_body}[journeys]
        Should Be Equal    ${journey}[is_active]    ${True}
    END

List Journeys With Pagination
    [Documentation]    Test journey listing with pagination
    [Tags]             journey    list    pagination
    [Setup]            Create Multiple Test Journeys
    
    # Test first page
    ${response}=    GET    ${JOURNEYS_ENDPOINT}?page=1&per_page=2
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    Should Be Equal As Numbers    ${response_body}[page]    1
    Should Be Equal As Numbers    ${response_body}[per_page]    2
    ${journey_count}=    Get Length    ${response_body}[journeys]
    Should Be Equal As Numbers    ${journey_count}    2

Search Journeys
    [Documentation]    Test journey search functionality
    [Tags]             journey    search
    [Setup]            Create Test Journeys For Search
    
    ${search_data}=    Create Dictionary
    ...    query=customer
    ...    page=1
    ...    per_page=10
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}/search    json=${search_data}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Should find journeys containing "customer"
    Should Be True    ${response_body}[total] >= 1
    
    # Verify search results contain the query term
    FOR    ${journey}    IN    @{response_body}[journeys]
        ${name_lower}=    Convert To Lower Case    ${journey}[name]
        ${desc_lower}=    Convert To Lower Case    ${journey}[description]
        ${contains_query}=    Run Keyword And Return Status
        ...    Should Contain Any    ${name_lower}    ${desc_lower}    customer
        Should Be True    ${contains_query}
    END

Update Journey
    [Documentation]    Test updating an existing journey
    [Tags]             journey    update    crud
    [Setup]            Create Test Journey For Update
    
    ${update_data}=    Create Dictionary
    ...    name=Updated Journey Name
    ...    description=Updated journey description with new requirements
    ...    is_active=${False}
    ...    expected_outcomes=@{EMPTY}
    
    ${response}=    PUT    ${JOURNEYS_ENDPOINT}/${TEST_JOURNEY_ID}    json=${update_data}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify updates
    Should Be Equal    ${response_body}[name]    Updated Journey Name
    Should Be Equal    ${response_body}[description]    Updated journey description with new requirements
    Should Be Equal    ${response_body}[is_active]    ${False}
    Should Be Equal    ${response_body}[id]    ${TEST_JOURNEY_ID}
    
    # Verify updated_at timestamp changed
    Should Not Be Equal    ${response_body}[updated_at]    ${response_body}[created_at]

Update Nonexistent Journey
    [Documentation]    Test updating a journey that doesn't exist
    [Tags]             journey    update    negative
    
    ${fake_id}=    Set Variable    550e8400-e29b-41d4-a716-999999999999
    ${update_data}=    Create Dictionary    name=Should Not Work
    
    ${response}=    PUT    ${JOURNEYS_ENDPOINT}/${fake_id}    json=${update_data}    expected_status=404
    Should Be Equal As Numbers    ${response.status_code}    404

Update Journey With Invalid Data
    [Documentation]    Test updating journey with invalid data
    [Tags]             journey    update    validation    negative
    [Setup]            Create Test Journey For Update
    
    # Test empty name
    ${update_data}=    Create Dictionary    name=${EMPTY}
    ${response}=    PUT    ${JOURNEYS_ENDPOINT}/${TEST_JOURNEY_ID}    json=${update_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422
    
    # Test invalid persona_id
    ${update_data}=    Create Dictionary    persona_id=invalid-uuid
    ${response}=    PUT    ${JOURNEYS_ENDPOINT}/${TEST_JOURNEY_ID}    json=${update_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422

Delete Journey
    [Documentation]    Test deleting an existing journey
    [Tags]             journey    delete    crud
    [Setup]            Create Test Journey For Deletion
    
    ${response}=    DELETE    ${JOURNEYS_ENDPOINT}/${TEST_JOURNEY_ID}
    
    Should Be Equal As Numbers    ${response.status_code}    204
    
    # Verify journey was deleted
    ${response}=    GET    ${JOURNEYS_ENDPOINT}/${TEST_JOURNEY_ID}    expected_status=404
    Should Be Equal As Numbers    ${response.status_code}    404

Delete Nonexistent Journey
    [Documentation]    Test deleting a journey that doesn't exist
    [Tags]             journey    delete    negative
    
    ${fake_id}=    Set Variable    550e8400-e29b-41d4-a716-999999999999
    ${response}=    DELETE    ${JOURNEYS_ENDPOINT}/${fake_id}    expected_status=404
    Should Be Equal As Numbers    ${response.status_code}    404

Get Journey Statistics
    [Documentation]    Test retrieving journey statistics
    [Tags]             journey    statistics
    [Setup]            Create Multiple Test Journeys
    
    ${response}=    GET    ${JOURNEYS_ENDPOINT}/statistics
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify statistics structure
    Should Contain    ${response_body}    total
    Should Contain    ${response_body}    active
    Should Contain    ${response_body}    inactive
    Should Contain    ${response_body}    by_persona
    Should Contain    ${response_body}    by_activity
    Should Contain    ${response_body}    avg_steps
    
    # Verify data types
    Should Be True    isinstance($response_body[total], int)
    Should Be True    isinstance($response_body[active], int)
    Should Be True    isinstance($response_body[inactive], int)

Bulk Update Journey Status
    [Documentation]    Test bulk updating journey status
    [Tags]             journey    bulk    update
    [Setup]            Create Multiple Test Journeys For Bulk Operations
    
    ${journey_ids}=    Create List    ${TEST_JOURNEY_ID}    ${TEST_JOURNEY_ID_2}    ${TEST_JOURNEY_ID_3}
    ${bulk_data}=    Create Dictionary
    ...    journey_ids=${journey_ids}
    ...    is_active=${False}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}/bulk/update-status    json=${bulk_data}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    Should Be Equal As Numbers    ${response_body}[updated_count]    3
    
    # Verify updates
    FOR    ${journey_id}    IN    @{journey_ids}
        ${response}=    GET    ${JOURNEYS_ENDPOINT}/${journey_id}
        ${journey}=    Set Variable    ${response.json()}
        Should Be Equal    ${journey}[is_active]    ${False}
    END

Bulk Delete Journeys
    [Documentation]    Test bulk deleting journeys
    [Tags]             journey    bulk    delete
    [Setup]            Create Multiple Test Journeys For Bulk Operations
    
    ${journey_ids}=    Create List    ${TEST_JOURNEY_ID}    ${TEST_JOURNEY_ID_2}
    
    ${response}=    DELETE    ${JOURNEYS_ENDPOINT}/bulk    json=${journey_ids}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    Should Be Equal As Numbers    ${response_body}[deleted_count]    2
    
    # Verify deletions
    FOR    ${journey_id}    IN    @{journey_ids}
        ${response}=    GET    ${JOURNEYS_ENDPOINT}/${journey_id}    expected_status=404
        Should Be Equal As Numbers    ${response.status_code}    404
    END

*** Keywords ***
Setup Test Suite
    [Documentation]    Initialize test suite with API session
    Create Session    api    ${BASE_URL}    verify=False
    Set Suite Variable    ${EMPTY_DICT}    &{EMPTY}

Cleanup Test Suite
    [Documentation]    Clean up any remaining test data
    Run Keyword And Ignore Error    Delete All Test Journeys

Create Test Journey For Reading
    [Documentation]    Create a journey specifically for read tests
    ${journey_data}=    Create Dictionary
    ...    name=${VALID_JOURNEY_NAME}
    ...    description=${VALID_DESCRIPTION}
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    ...    steps=@{EMPTY}
    ...    is_active=${True}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    ${journey}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_JOURNEY_ID}    ${journey}[id]

Create Test Journey For Update
    [Documentation]    Create a journey specifically for update tests
    ${journey_data}=    Create Dictionary
    ...    name=Journey To Update
    ...    description=Original description
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    ...    is_active=${True}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    ${journey}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_JOURNEY_ID}    ${journey}[id]

Create Test Journey For Deletion
    [Documentation]    Create a journey specifically for delete tests
    ${journey_data}=    Create Dictionary
    ...    name=Journey To Delete
    ...    description=Will be deleted
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    ${journey}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_JOURNEY_ID}    ${journey}[id]

Create Test Journey For Duplication
    [Documentation]    Create a journey to test duplicate name validation
    ${journey_data}=    Create Dictionary
    ...    name=Duplicate Test Journey
    ...    description=Original journey
    ...    persona_id=${VALID_PERSONA_ID}
    ...    activity_id=${VALID_ACTIVITY_ID}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}

Create Multiple Test Journeys
    [Documentation]    Create multiple journeys for list/filter tests
    ${journeys}=    Create List
    ...    &{journey_data}    name=List Test Journey 1    description=First test journey
    ...    &{journey_data}    name=List Test Journey 2    description=Second test journey
    ...    &{journey_data}    name=List Test Journey 3    description=Third test journey    is_active=${False}
    
    FOR    ${journey_data}    IN    @{journeys}
        Set To Dictionary    ${journey_data}    persona_id=${VALID_PERSONA_ID}
        Set To Dictionary    ${journey_data}    activity_id=${VALID_ACTIVITY_ID}
        ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    END

Create Test Journeys For Search
    [Documentation]    Create journeys with specific content for search tests
    ${search_journeys}=    Create List
    ...    &{journey_data}    name=Customer Onboarding Journey    description=Process for new customers
    ...    &{journey_data}    name=Sales Process Journey    description=Standard sales workflow
    ...    &{journey_data}    name=Customer Support Journey    description=Customer issue resolution
    
    FOR    ${journey_data}    IN    @{search_journeys}
        Set To Dictionary    ${journey_data}    persona_id=${VALID_PERSONA_ID}
        Set To Dictionary    ${journey_data}    activity_id=${VALID_ACTIVITY_ID}
        ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    END

Create Multiple Test Journeys For Bulk Operations
    [Documentation]    Create multiple journeys for bulk operation tests
    ${bulk_journeys}=    Create List
    ...    &{journey_data}    name=Bulk Test Journey 1    description=First bulk test
    ...    &{journey_data}    name=Bulk Test Journey 2    description=Second bulk test
    ...    &{journey_data}    name=Bulk Test Journey 3    description=Third bulk test
    
    ${journey_ids}=    Create List
    
    FOR    ${i}    ${journey_data}    IN ENUMERATE    @{bulk_journeys}    start=1
        Set To Dictionary    ${journey_data}    persona_id=${VALID_PERSONA_ID}
        Set To Dictionary    ${journey_data}    activity_id=${VALID_ACTIVITY_ID}
        ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
        ${journey}=    Set Variable    ${response.json()}
        Append To List    ${journey_ids}    ${journey}[id]
        Set Suite Variable    ${TEST_JOURNEY_ID_${i}}    ${journey}[id]
    END

Delete All Test Journeys
    [Documentation]    Clean up all test journeys
    ${response}=    GET    ${JOURNEYS_ENDPOINT}?search=Test
    Run Keyword If    ${response.status_code} == 200
    ...    Delete Test Journeys From Response    ${response.json()}

Delete Test Journeys From Response
    [Documentation]    Delete journeys from API response
    [Arguments]    ${response_data}
    
    FOR    ${journey}    IN    @{response_data}[journeys]
        Run Keyword And Ignore Error    DELETE    ${JOURNEYS_ENDPOINT}/${journey}[id]
    END