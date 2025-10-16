*** Settings ***
Documentation    Test suite for Action Library integration
...              Tests the integration of action libraries with journeys and test execution
...              including Given/When/Then action classifications and parameter handling.

Library          RequestsLibrary
Library          Collections
Library          String
Library          DateTime
Library          JSONLibrary

Suite Setup      Setup Test Suite
Suite Teardown   Cleanup Test Suite

*** Variables ***
${BASE_URL}              http://localhost:8000/api/v1
${ACTIONS_ENDPOINT}      ${BASE_URL}/actions
${JOURNEYS_ENDPOINT}     ${BASE_URL}/journeys
${VALID_ACTION_NAME}     Navigate to Sales Invoice List
${VALID_DESCRIPTION}     Navigate to the Sales Invoice list page in ERPNext
${VALID_ACTION_TYPE}     given
${VALID_MODULE}          Accounts
${TEST_ACTION_ID}        ${EMPTY}
${TEST_JOURNEY_ID}       ${EMPTY}

*** Test Cases ***

Create Action With Valid Data
    [Documentation]    Test creating a new action with all required fields
    [Tags]             action    create    crud    smoke
    
    ${action_data}=    Create Dictionary
    ...    name=${VALID_ACTION_NAME}
    ...    description=${VALID_DESCRIPTION}
    ...    action_type=${VALID_ACTION_TYPE}
    ...    erpnext_module=${VALID_MODULE}
    ...    implementation_type=ui_interaction
    ...    parameters=@{EMPTY}
    ...    expected_outputs=@{EMPTY}
    ...    robot_keywords=@{EMPTY}
    ...    is_active=${True}
    ...    metadata=${EMPTY_DICT}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    
    Should Be Equal As Numbers    ${response.status_code}    201
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify response structure
    Should Contain    ${response_body}    id
    Should Contain    ${response_body}    name
    Should Contain    ${response_body}    description
    Should Contain    ${response_body}    action_type
    Should Contain    ${response_body}    created_at
    Should Contain    ${response_body}    updated_at
    
    # Verify response values
    Should Be Equal    ${response_body}[name]    ${VALID_ACTION_NAME}
    Should Be Equal    ${response_body}[description]    ${VALID_DESCRIPTION}
    Should Be Equal    ${response_body}[action_type]    ${VALID_ACTION_TYPE}
    Should Be Equal    ${response_body}[erpnext_module]    ${VALID_MODULE}
    Should Be Equal    ${response_body}[is_active]    ${True}
    
    # Store action ID for cleanup
    Set Suite Variable    ${TEST_ACTION_ID}    ${response_body}[id]

Create Action With Parameters
    [Documentation]    Test creating an action with input parameters
    [Tags]             action    create    parameters
    
    ${parameters}=    Create List
    ...    &{parameter}    name=customer_name    type=string    required=${True}    description=Name of the customer
    ...    &{parameter}    name=amount    type=number    required=${True}    description=Invoice amount    default=0
    ...    &{parameter}    name=due_date    type=date    required=${False}    description=Payment due date
    
    ${expected_outputs}=    Create List
    ...    &{output}    name=invoice_id    type=string    description=Generated invoice ID
    ...    &{output}    name=success    type=boolean    description=Whether creation was successful
    
    ${action_data}=    Create Dictionary
    ...    name=Create Sales Invoice with Parameters
    ...    description=Create a sales invoice with specified customer and amount
    ...    action_type=when
    ...    erpnext_module=Accounts
    ...    implementation_type=api_call
    ...    parameters=${parameters}
    ...    expected_outputs=${expected_outputs}
    ...    robot_keywords=@{EMPTY}
    ...    is_active=${True}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    
    Should Be Equal As Numbers    ${response.status_code}    201
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify parameters
    ${param_count}=    Get Length    ${response_body}[parameters]
    Should Be Equal As Numbers    ${param_count}    3
    
    # Verify outputs
    ${output_count}=    Get Length    ${response_body}[expected_outputs]
    Should Be Equal As Numbers    ${output_count}    2

Create Action With Robot Keywords
    [Documentation]    Test creating an action with Robot Framework keywords
    [Tags]             action    create    robot_keywords
    
    ${robot_keywords}=    Create List
    ...    Open Browser    \${BROWSER_URL}    chrome
    ...    Wait Until Page Contains Element    id:login-form
    ...    Input Text    id:username    \${USERNAME}
    ...    Input Text    id:password    \${PASSWORD}
    ...    Click Button    id:login-button
    
    ${action_data}=    Create Dictionary
    ...    name=Login to ERPNext
    ...    description=Login to ERPNext system using web interface
    ...    action_type=given
    ...    erpnext_module=Core
    ...    implementation_type=robot_framework
    ...    parameters=@{EMPTY}
    ...    expected_outputs=@{EMPTY}
    ...    robot_keywords=${robot_keywords}
    ...    is_active=${True}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    
    Should Be Equal As Numbers    ${response.status_code}    201
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify robot keywords
    ${keyword_count}=    Get Length    ${response_body}[robot_keywords]
    Should Be Equal As Numbers    ${keyword_count}    5

Create Action With Invalid Action Type
    [Documentation]    Test action creation with invalid action type
    [Tags]             action    create    validation    negative
    
    ${action_data}=    Create Dictionary
    ...    name=Invalid Action Type Test
    ...    description=Test action with invalid type
    ...    action_type=invalid_type
    ...    erpnext_module=Accounts
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422
    ${error_body}=    Set Variable    ${response.json()}
    Should Contain    ${error_body}[detail]    action_type

Create Action With Missing Required Fields
    [Documentation]    Test action creation fails with missing required fields
    [Tags]             action    create    validation    negative
    
    # Test missing name
    ${action_data}=    Create Dictionary
    ...    description=${VALID_DESCRIPTION}
    ...    action_type=${VALID_ACTION_TYPE}
    ...    erpnext_module=${VALID_MODULE}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422
    
    # Test missing action_type
    ${action_data}=    Create Dictionary
    ...    name=${VALID_ACTION_NAME}
    ...    description=${VALID_DESCRIPTION}
    ...    erpnext_module=${VALID_MODULE}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422

Get Action By ID
    [Documentation]    Test retrieving an action by its ID
    [Tags]             action    read    crud
    [Setup]            Create Test Action For Reading
    
    ${response}=    GET    ${ACTIONS_ENDPOINT}/${TEST_ACTION_ID}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify action details
    Should Be Equal    ${response_body}[id]    ${TEST_ACTION_ID}
    Should Be Equal    ${response_body}[name]    ${VALID_ACTION_NAME}
    Should Be Equal    ${response_body}[action_type]    ${VALID_ACTION_TYPE}

List Actions By Type
    [Documentation]    Test listing actions filtered by type (given/when/then)
    [Tags]             action    list    filter
    [Setup]            Create Actions Of Different Types
    
    # Test listing 'given' actions
    ${response}=    GET    ${ACTIONS_ENDPOINT}?action_type=given
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # All returned actions should be 'given' type
    FOR    ${action}    IN    @{response_body}[actions]
        Should Be Equal    ${action}[action_type]    given
    END
    
    # Test listing 'when' actions
    ${response}=    GET    ${ACTIONS_ENDPOINT}?action_type=when
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    FOR    ${action}    IN    @{response_body}[actions]
        Should Be Equal    ${action}[action_type]    when
    END
    
    # Test listing 'then' actions
    ${response}=    GET    ${ACTIONS_ENDPOINT}?action_type=then
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    FOR    ${action}    IN    @{response_body}[actions]
        Should Be Equal    ${action}[action_type]    then
    END

List Actions By Module
    [Documentation]    Test listing actions filtered by ERPNext module
    [Tags]             action    list    filter    module
    [Setup]            Create Actions For Different Modules
    
    # Test filtering by Accounts module
    ${response}=    GET    ${ACTIONS_ENDPOINT}?erpnext_module=Accounts
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    FOR    ${action}    IN    @{response_body}[actions]
        Should Be Equal    ${action}[erpnext_module]    Accounts
    END
    
    # Test filtering by Stock module
    ${response}=    GET    ${ACTIONS_ENDPOINT}?erpnext_module=Stock
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    FOR    ${action}    IN    @{response_body}[actions]
        Should Be Equal    ${action}[erpnext_module]    Stock
    END

Search Actions
    [Documentation]    Test action search functionality
    [Tags]             action    search
    [Setup]            Create Actions For Search
    
    ${search_data}=    Create Dictionary
    ...    query=invoice
    ...    page=1
    ...    per_page=10
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}/search    json=${search_data}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Should find actions containing "invoice"
    Should Be True    ${response_body}[total] >= 1
    
    # Verify search results contain the query term
    FOR    ${action}    IN    @{response_body}[actions]
        ${name_lower}=    Convert To Lower Case    ${action}[name]
        ${desc_lower}=    Convert To Lower Case    ${action}[description]
        ${contains_query}=    Run Keyword And Return Status
        ...    Should Contain Any    ${name_lower}    ${desc_lower}    invoice
        Should Be True    ${contains_query}
    END

Update Action
    [Documentation]    Test updating an existing action
    [Tags]             action    update    crud
    [Setup]            Create Test Action For Update
    
    ${update_data}=    Create Dictionary
    ...    name=Updated Action Name
    ...    description=Updated action description
    ...    is_active=${False}
    
    ${response}=    PUT    ${ACTIONS_ENDPOINT}/${TEST_ACTION_ID}    json=${update_data}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify updates
    Should Be Equal    ${response_body}[name]    Updated Action Name
    Should Be Equal    ${response_body}[description]    Updated action description
    Should Be Equal    ${response_body}[is_active]    ${False}

Delete Action
    [Documentation]    Test deleting an existing action
    [Tags]             action    delete    crud
    [Setup]            Create Test Action For Deletion
    
    ${response}=    DELETE    ${ACTIONS_ENDPOINT}/${TEST_ACTION_ID}
    
    Should Be Equal As Numbers    ${response.status_code}    204
    
    # Verify action was deleted
    ${response}=    GET    ${ACTIONS_ENDPOINT}/${TEST_ACTION_ID}    expected_status=404
    Should Be Equal As Numbers    ${response.status_code}    404

Validate Action Parameters
    [Documentation]    Test action parameter validation
    [Tags]             action    validation    parameters
    [Setup]            Create Action With Complex Parameters
    
    ${validation_data}=    Create Dictionary
    ...    customer_name=Test Customer
    ...    amount=1000
    ...    due_date=2024-12-31
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}/${TEST_ACTION_ID}/validate-parameters    json=${validation_data}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    Should Contain    ${response_body}    is_valid
    Should Contain    ${response_body}    validation_errors
    Should Be Equal    ${response_body}[is_valid]    ${True}

Test Action Parameter Validation Errors
    [Documentation]    Test parameter validation with invalid data
    [Tags]             action    validation    parameters    negative
    [Setup]            Create Action With Complex Parameters
    
    # Test missing required parameter
    ${invalid_data}=    Create Dictionary
    ...    amount=1000
    # Missing required customer_name
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}/${TEST_ACTION_ID}/validate-parameters    json=${invalid_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422
    
    # Test invalid parameter type
    ${invalid_data}=    Create Dictionary
    ...    customer_name=Test Customer
    ...    amount=not_a_number
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}/${TEST_ACTION_ID}/validate-parameters    json=${invalid_data}    expected_status=422
    Should Be Equal As Numbers    ${response.status_code}    422

Execute Action
    [Documentation]    Test action execution
    [Tags]             action    execute    integration
    [Setup]            Create Executable Test Action
    
    ${execution_data}=    Create Dictionary
    ...    parameters=&{EMPTY_DICT}
    ...    context=&{EMPTY_DICT}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}/${TEST_ACTION_ID}/execute    json=${execution_data}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    Should Contain    ${response_body}    execution_id
    Should Contain    ${response_body}    status
    Should Contain    ${response_body}    outputs
    Should Contain    ${response_body}    execution_time

Create Journey With Actions
    [Documentation]    Test creating a journey that uses actions
    [Tags]             journey    action    integration
    [Setup]            Create Actions For Journey Integration
    
    ${journey_steps}=    Create List
    ...    &{step}    step_number=1    action_id=${GIVEN_ACTION_ID}    description=Login to system
    ...    &{step}    step_number=2    action_id=${WHEN_ACTION_ID}    description=Create invoice
    ...    &{step}    step_number=3    action_id=${THEN_ACTION_ID}    description=Verify creation
    
    ${journey_data}=    Create Dictionary
    ...    name=Full Journey with Actions
    ...    description=Complete journey using action library
    ...    persona_id=550e8400-e29b-41d4-a716-446655440000
    ...    activity_id=550e8400-e29b-41d4-a716-446655440001
    ...    steps=${journey_steps}
    ...    is_active=${True}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    
    Should Be Equal As Numbers    ${response.status_code}    201
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify journey has steps with actions
    ${step_count}=    Get Length    ${response_body}[steps]
    Should Be Equal As Numbers    ${step_count}    3
    
    Set Suite Variable    ${TEST_JOURNEY_ID}    ${response_body}[id]

Validate Journey Action Sequence
    [Documentation]    Test validation of action sequence in journey
    [Tags]             journey    action    validation    sequence
    [Setup]            Create Journey With Action Sequence
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}/${TEST_JOURNEY_ID}/validate-sequence
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    Should Contain    ${response_body}    is_valid
    Should Contain    ${response_body}    validation_errors
    Should Contain    ${response_body}    sequence_issues
    
    # Valid sequence should have no issues
    Should Be Equal    ${response_body}[is_valid]    ${True}
    ${error_count}=    Get Length    ${response_body}[validation_errors]
    Should Be Equal As Numbers    ${error_count}    0

Test Invalid Action Sequence
    [Documentation]    Test invalid action sequence validation
    [Tags]             journey    action    validation    negative
    [Setup]            Create Journey With Invalid Action Sequence
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}/${TEST_JOURNEY_ID}/validate-sequence
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Invalid sequence should have issues
    Should Be Equal    ${response_body}[is_valid]    ${False}
    Should Be True    len($response_body[validation_errors]) > 0

Execute Journey With Actions
    [Documentation]    Test executing a complete journey with actions
    [Tags]             journey    action    execution    integration
    [Setup]            Create Complete Journey For Execution
    
    ${execution_data}=    Create Dictionary
    ...    parameters=&{EMPTY_DICT}
    ...    context=&{EMPTY_DICT}
    ...    dry_run=${True}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}/${TEST_JOURNEY_ID}/execute    json=${execution_data}
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    Should Contain    ${response_body}    execution_id
    Should Contain    ${response_body}    status
    Should Contain    ${response_body}    step_results
    Should Contain    ${response_body}    total_execution_time
    
    # Verify all steps were executed
    ${step_count}=    Get Length    ${response_body}[step_results]
    Should Be True    ${step_count} >= 3

Get Action Library Statistics
    [Documentation]    Test retrieving action library statistics
    [Tags]             action    statistics
    [Setup]            Create Multiple Actions For Statistics
    
    ${response}=    GET    ${ACTIONS_ENDPOINT}/statistics
    
    Should Be Equal As Numbers    ${response.status_code}    200
    ${response_body}=    Set Variable    ${response.json()}
    
    # Verify statistics structure
    Should Contain    ${response_body}    total
    Should Contain    ${response_body}    by_type
    Should Contain    ${response_body}    by_module
    Should Contain    ${response_body}    by_implementation_type
    Should Contain    ${response_body}    most_used
    
    # Verify action type distribution
    Should Contain    ${response_body}[by_type]    given
    Should Contain    ${response_body}[by_type]    when
    Should Contain    ${response_body}[by_type]    then

*** Keywords ***
Setup Test Suite
    [Documentation]    Initialize test suite with API session
    Create Session    api    ${BASE_URL}    verify=False
    Set Suite Variable    ${EMPTY_DICT}    &{EMPTY}

Cleanup Test Suite
    [Documentation]    Clean up any remaining test data
    Run Keyword And Ignore Error    Delete All Test Actions
    Run Keyword And Ignore Error    Delete All Test Journeys

Create Test Action For Reading
    [Documentation]    Create an action specifically for read tests
    ${action_data}=    Create Dictionary
    ...    name=${VALID_ACTION_NAME}
    ...    description=${VALID_DESCRIPTION}
    ...    action_type=${VALID_ACTION_TYPE}
    ...    erpnext_module=${VALID_MODULE}
    ...    implementation_type=ui_interaction
    ...    is_active=${True}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    ${action}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_ACTION_ID}    ${action}[id]

Create Test Action For Update
    [Documentation]    Create an action specifically for update tests
    ${action_data}=    Create Dictionary
    ...    name=Action To Update
    ...    description=Original description
    ...    action_type=when
    ...    erpnext_module=Accounts
    ...    implementation_type=api_call
    ...    is_active=${True}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    ${action}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_ACTION_ID}    ${action}[id]

Create Test Action For Deletion
    [Documentation]    Create an action specifically for delete tests
    ${action_data}=    Create Dictionary
    ...    name=Action To Delete
    ...    description=Will be deleted
    ...    action_type=then
    ...    erpnext_module=Stock
    ...    implementation_type=verification
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    ${action}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_ACTION_ID}    ${action}[id]

Create Actions Of Different Types
    [Documentation]    Create actions of different types (given/when/then)
    ${actions}=    Create List
    ...    &{action}    name=Given Login    action_type=given    erpnext_module=Core
    ...    &{action}    name=When Create Invoice    action_type=when    erpnext_module=Accounts
    ...    &{action}    name=Then Verify Success    action_type=then    erpnext_module=Accounts
    
    FOR    ${action_data}    IN    @{actions}
        Set To Dictionary    ${action_data}    description=Test action description
        Set To Dictionary    ${action_data}    implementation_type=ui_interaction
        ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    END

Create Actions For Different Modules
    [Documentation]    Create actions for different ERPNext modules
    ${actions}=    Create List
    ...    &{action}    name=Accounts Action    erpnext_module=Accounts
    ...    &{action}    name=Stock Action    erpnext_module=Stock
    ...    &{action}    name=CRM Action    erpnext_module=CRM
    
    FOR    ${action_data}    IN    @{actions}
        Set To Dictionary    ${action_data}    description=Module-specific action
        Set To Dictionary    ${action_data}    action_type=when
        Set To Dictionary    ${action_data}    implementation_type=api_call
        ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    END

Create Actions For Search
    [Documentation]    Create actions with specific content for search tests
    ${search_actions}=    Create List
    ...    &{action}    name=Create Sales Invoice    description=Create a new sales invoice
    ...    &{action}    name=Update Invoice Status    description=Update invoice status to paid
    ...    &{action}    name=Generate Report    description=Generate sales report
    
    FOR    ${action_data}    IN    @{search_actions}
        Set To Dictionary    ${action_data}    action_type=when
        Set To Dictionary    ${action_data}    erpnext_module=Accounts
        Set To Dictionary    ${action_data}    implementation_type=api_call
        ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    END

Create Action With Complex Parameters
    [Documentation]    Create an action with complex parameter validation
    ${parameters}=    Create List
    ...    &{param}    name=customer_name    type=string    required=${True}    description=Customer name
    ...    &{param}    name=amount    type=number    required=${True}    description=Invoice amount
    ...    &{param}    name=due_date    type=date    required=${False}    description=Due date
    
    ${action_data}=    Create Dictionary
    ...    name=Complex Parameter Action
    ...    description=Action with complex parameters
    ...    action_type=when
    ...    erpnext_module=Accounts
    ...    implementation_type=api_call
    ...    parameters=${parameters}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    ${action}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_ACTION_ID}    ${action}[id]

Create Executable Test Action
    [Documentation]    Create an action that can be executed
    ${action_data}=    Create Dictionary
    ...    name=Executable Test Action
    ...    description=Simple executable action for testing
    ...    action_type=when
    ...    erpnext_module=Core
    ...    implementation_type=robot_framework
    ...    robot_keywords=@{EMPTY}
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    ${action}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_ACTION_ID}    ${action}[id]

Create Actions For Journey Integration
    [Documentation]    Create given/when/then actions for journey integration
    # Create Given action
    ${given_action}=    Create Dictionary
    ...    name=Given User Is Logged In
    ...    description=Ensure user is logged into ERPNext
    ...    action_type=given
    ...    erpnext_module=Core
    ...    implementation_type=ui_interaction
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${given_action}
    ${given_action_data}=    Set Variable    ${response.json()}
    Set Suite Variable    ${GIVEN_ACTION_ID}    ${given_action_data}[id]
    
    # Create When action
    ${when_action}=    Create Dictionary
    ...    name=When Invoice Is Created
    ...    description=Create a new sales invoice
    ...    action_type=when
    ...    erpnext_module=Accounts
    ...    implementation_type=api_call
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${when_action}
    ${when_action_data}=    Set Variable    ${response.json()}
    Set Suite Variable    ${WHEN_ACTION_ID}    ${when_action_data}[id]
    
    # Create Then action
    ${then_action}=    Create Dictionary
    ...    name=Then Invoice Should Exist
    ...    description=Verify invoice was created successfully
    ...    action_type=then
    ...    erpnext_module=Accounts
    ...    implementation_type=verification
    
    ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${then_action}
    ${then_action_data}=    Set Variable    ${response.json()}
    Set Suite Variable    ${THEN_ACTION_ID}    ${then_action_data}[id]

Create Journey With Action Sequence
    [Documentation]    Create a journey with proper action sequence
    ${journey_steps}=    Create List
    ...    &{step}    step_number=1    action_id=${GIVEN_ACTION_ID}    description=Setup preconditions
    ...    &{step}    step_number=2    action_id=${WHEN_ACTION_ID}    description=Execute action
    ...    &{step}    step_number=3    action_id=${THEN_ACTION_ID}    description=Verify result
    
    ${journey_data}=    Create Dictionary
    ...    name=Valid Sequence Journey
    ...    description=Journey with valid action sequence
    ...    persona_id=550e8400-e29b-41d4-a716-446655440000
    ...    activity_id=550e8400-e29b-41d4-a716-446655440001
    ...    steps=${journey_steps}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    ${journey}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_JOURNEY_ID}    ${journey}[id]

Create Journey With Invalid Action Sequence
    [Documentation]    Create a journey with invalid action sequence (Then before Given)
    ${journey_steps}=    Create List
    ...    &{step}    step_number=1    action_id=${THEN_ACTION_ID}    description=Verify before setup
    ...    &{step}    step_number=2    action_id=${GIVEN_ACTION_ID}    description=Setup after verification
    ...    &{step}    step_number=3    action_id=${WHEN_ACTION_ID}    description=Execute after verification
    
    ${journey_data}=    Create Dictionary
    ...    name=Invalid Sequence Journey
    ...    description=Journey with invalid action sequence
    ...    persona_id=550e8400-e29b-41d4-a716-446655440000
    ...    activity_id=550e8400-e29b-41d4-a716-446655440001
    ...    steps=${journey_steps}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    ${journey}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_JOURNEY_ID}    ${journey}[id]

Create Complete Journey For Execution
    [Documentation]    Create a complete journey ready for execution
    ${journey_steps}=    Create List
    ...    &{step}    step_number=1    action_id=${GIVEN_ACTION_ID}    description=Login precondition
    ...    &{step}    step_number=2    action_id=${WHEN_ACTION_ID}    description=Create invoice
    ...    &{step}    step_number=3    action_id=${THEN_ACTION_ID}    description=Verify creation
    
    ${journey_data}=    Create Dictionary
    ...    name=Execution Ready Journey
    ...    description=Journey ready for execution testing
    ...    persona_id=550e8400-e29b-41d4-a716-446655440000
    ...    activity_id=550e8400-e29b-41d4-a716-446655440001
    ...    steps=${journey_steps}
    ...    is_active=${True}
    
    ${response}=    POST    ${JOURNEYS_ENDPOINT}    json=${journey_data}
    ${journey}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_JOURNEY_ID}    ${journey}[id]

Create Multiple Actions For Statistics
    [Documentation]    Create multiple actions for statistics testing
    ${actions}=    Create List
    ...    &{action}    name=Stats Given 1    action_type=given    erpnext_module=Accounts
    ...    &{action}    name=Stats Given 2    action_type=given    erpnext_module=Stock
    ...    &{action}    name=Stats When 1    action_type=when    erpnext_module=Accounts
    ...    &{action}    name=Stats When 2    action_type=when    erpnext_module=CRM
    ...    &{action}    name=Stats Then 1    action_type=then    erpnext_module=Accounts
    
    FOR    ${action_data}    IN    @{actions}
        Set To Dictionary    ${action_data}    description=Statistics test action
        Set To Dictionary    ${action_data}    implementation_type=ui_interaction
        ${response}=    POST    ${ACTIONS_ENDPOINT}    json=${action_data}
    END

Delete All Test Actions
    [Documentation]    Clean up all test actions
    ${response}=    GET    ${ACTIONS_ENDPOINT}?search=Test
    Run Keyword If    ${response.status_code} == 200
    ...    Delete Test Actions From Response    ${response.json()}

Delete All Test Journeys
    [Documentation]    Clean up all test journeys
    ${response}=    GET    ${JOURNEYS_ENDPOINT}?search=Test
    Run Keyword If    ${response.status_code} == 200
    ...    Delete Test Journeys From Response    ${response.json()}

Delete Test Actions From Response
    [Documentation]    Delete actions from API response
    [Arguments]    ${response_data}
    
    FOR    ${action}    IN    @{response_data}[actions]
        Run Keyword And Ignore Error    DELETE    ${ACTIONS_ENDPOINT}/${action}[id]
    END

Delete Test Journeys From Response
    [Documentation]    Delete journeys from API response
    [Arguments]    ${response_data}
    
    FOR    ${journey}    IN    @{response_data}[journeys]
        Run Keyword And Ignore Error    DELETE    ${JOURNEYS_ENDPOINT}/${journey}[id]
    END