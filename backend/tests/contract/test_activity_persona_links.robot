*** Settings ***
Documentation    Contract tests for Activity-Persona relationship operations
...              These tests define the expected behavior of linking activities to personas
...              and managing the many-to-many relationships between them.
Library          RequestsLibrary
Library          JSONLibrary
Library          Collections
Library          String
Library          DateTime
Suite Setup      Initialize Test Environment
Suite Teardown   Cleanup Test Environment

*** Variables ***
${BASE_URL}      http://localhost:8000/api/v1
${PERSONAS_ENDPOINT}    ${BASE_URL}/personas
${ACTIVITIES_ENDPOINT}    ${BASE_URL}/activities
${VALID_PERSONA_DATA}    {"name": "Sales Manager", "description": "Manages sales operations", "erpnext_roles": ["Sales Manager", "Customer"], "permissions": "read_sales_order,write_sales_order", "is_active": true}
${VALID_ACTIVITY_DATA}    {"name": "Create Sales Order", "description": "Create a new sales order in ERPNext", "erpnext_module": "Sales", "action_type": "create", "target_doctype": "Sales Order", "required_fields": ["customer", "items"], "validation_rules": {"customer": "required", "items": "array_min:1"}, "success_criteria": ["order_created", "customer_notified"], "complexity_score": 5, "estimated_duration": 300, "is_active": true}

*** Keywords ***
Initialize Test Environment
    [Documentation]    Set up test environment and create test data
    Create Session    api    ${BASE_URL}
    &{headers}=    Create Dictionary    Content-Type=application/json
    Set Suite Variable    ${HEADERS}    ${headers}
    
    # Create test personas
    ${persona_1_data}=    Evaluate    json.loads('${VALID_PERSONA_DATA}')    json
    ${response}=    POST On Session    api    /personas    json=${persona_1_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    201
    ${persona_1}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_PERSONA_1_ID}    ${persona_1['id']}
    
    ${persona_2_data}=    Create Dictionary
    ...    name=Purchase Manager
    ...    description=Manages purchase operations
    ...    erpnext_roles=["Purchase Manager", "Supplier"]
    ...    permissions=read_purchase_order,write_purchase_order
    ...    is_active=true
    
    ${response}=    POST On Session    api    /personas    json=${persona_2_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    201
    ${persona_2}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_PERSONA_2_ID}    ${persona_2['id']}
    
    # Create test activities
    ${activity_1_data}=    Evaluate    json.loads('${VALID_ACTIVITY_DATA}')    json
    ${response}=    POST On Session    api    /activities    json=${activity_1_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    201
    ${activity_1}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_ACTIVITY_1_ID}    ${activity_1['id']}
    
    ${activity_2_data}=    Create Dictionary
    ...    name=Create Purchase Order
    ...    description=Create a new purchase order in ERPNext
    ...    erpnext_module=Buying
    ...    action_type=create
    ...    target_doctype=Purchase Order
    ...    required_fields=["supplier", "items"]
    ...    complexity_score=4
    ...    estimated_duration=240
    ...    is_active=true
    
    ${response}=    POST On Session    api    /activities    json=${activity_2_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    201
    ${activity_2}=    Set Variable    ${response.json()}
    Set Suite Variable    ${TEST_ACTIVITY_2_ID}    ${activity_2['id']}

Cleanup Test Environment
    [Documentation]    Clean up all test data
    # Clean up any activity-persona links first
    Run Keyword And Ignore Error    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    Run Keyword And Ignore Error    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_2_ID}    headers=${HEADERS}
    Run Keyword And Ignore Error    DELETE On Session    api    /personas/${TEST_PERSONA_2_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    Run Keyword And Ignore Error    DELETE On Session    api    /personas/${TEST_PERSONA_2_ID}/activities/${TEST_ACTIVITY_2_ID}    headers=${HEADERS}
    
    # Clean up activities
    Run Keyword And Ignore Error    DELETE On Session    api    /activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    Run Keyword And Ignore Error    DELETE On Session    api    /activities/${TEST_ACTIVITY_2_ID}    headers=${HEADERS}
    
    # Clean up personas
    Run Keyword And Ignore Error    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}    headers=${HEADERS}
    Run Keyword And Ignore Error    DELETE On Session    api    /personas/${TEST_PERSONA_2_ID}    headers=${HEADERS}

Validate Activity Persona Link Response
    [Documentation]    Validate activity-persona link response schema
    [Arguments]    ${link_json}
    Should Contain    ${link_json}    persona_id
    Should Contain    ${link_json}    activity_id
    Should Contain    ${link_json}    created_at
    Should Contain    ${link_json}    priority
    Should Contain    ${link_json}    notes
    Should Not Be Empty    ${link_json['persona_id']}
    Should Not Be Empty    ${link_json['activity_id']}
    Should Not Be Empty    ${link_json['created_at']}

Create Activity Persona Link
    [Documentation]    Helper to create an activity-persona link
    [Arguments]    ${persona_id}    ${activity_id}    ${priority}=medium    ${notes}=${EMPTY}
    ${link_data}=    Create Dictionary    priority=${priority}    notes=${notes}
    ${response}=    POST On Session    api    /personas/${persona_id}/activities/${activity_id}    json=${link_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    201
    [Return]    ${response.json()}

*** Test Cases ***
APL001: Link Activity To Persona With Valid Data
    [Documentation]    Test linking an activity to a persona with valid relationship data
    [Tags]    link    positive    contract
    
    ${link_data}=    Create Dictionary
    ...    priority=high
    ...    notes=Critical activity for sales operations
    
    ${response}=    POST On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    json=${link_data}    headers=${HEADERS}
    
    Should Be Equal As Strings    ${response.status_code}    201
    
    ${link_json}=    Set Variable    ${response.json()}
    Validate Activity Persona Link Response    ${link_json}
    
    # Verify link data
    Should Be Equal As Strings    ${link_json['persona_id']}    ${TEST_PERSONA_1_ID}
    Should Be Equal As Strings    ${link_json['activity_id']}    ${TEST_ACTIVITY_1_ID}
    Should Be Equal As Strings    ${link_json['priority']}    high
    Should Be Equal As Strings    ${link_json['notes']}    Critical activity for sales operations
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}

APL002: Link Activity To Persona With Minimal Data
    [Documentation]    Test linking with only required data (empty priority and notes)
    [Tags]    link    positive    minimal    contract
    
    ${link_data}=    Create Dictionary
    
    ${response}=    POST On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    json=${link_data}    headers=${HEADERS}
    
    Should Be Equal As Strings    ${response.status_code}    201
    
    ${link_json}=    Set Variable    ${response.json()}
    Validate Activity Persona Link Response    ${link_json}
    
    # Verify defaults
    Should Be Equal As Strings    ${link_json['priority']}    medium
    Should Be Equal As Strings    ${link_json['notes']}    ${EMPTY}
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}

APL003: Link Same Activity To Multiple Personas
    [Documentation]    Test linking the same activity to multiple personas
    [Tags]    link    positive    multiple    contract
    
    # Link activity 1 to persona 1
    ${link_1}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_1_ID}    high    Sales team activity
    
    # Link same activity to persona 2
    ${link_2}=    Create Activity Persona Link    ${TEST_PERSONA_2_ID}    ${TEST_ACTIVITY_1_ID}    low    Cross-functional activity
    
    # Verify both links exist and are independent
    Should Be Equal As Strings    ${link_1['persona_id']}    ${TEST_PERSONA_1_ID}
    Should Be Equal As Strings    ${link_1['priority']}    high
    Should Be Equal As Strings    ${link_1['notes']}    Sales team activity
    
    Should Be Equal As Strings    ${link_2['persona_id']}    ${TEST_PERSONA_2_ID}
    Should Be Equal As Strings    ${link_2['priority']}    low
    Should Be Equal As Strings    ${link_2['notes']}    Cross-functional activity
    
    # Both should link to the same activity
    Should Be Equal As Strings    ${link_1['activity_id']}    ${link_2['activity_id']}
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    DELETE On Session    api    /personas/${TEST_PERSONA_2_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}

APL004: Link Multiple Activities To Same Persona
    [Documentation]    Test linking multiple activities to the same persona
    [Tags]    link    positive    multiple    contract
    
    # Link both activities to persona 1
    ${link_1}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_1_ID}    high    Primary sales activity
    ${link_2}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_2_ID}    medium    Secondary activity
    
    # Verify both links exist for the same persona
    Should Be Equal As Strings    ${link_1['persona_id']}    ${link_2['persona_id']}
    Should Not Be Equal As Strings    ${link_1['activity_id']}    ${link_2['activity_id']}
    
    Should Be Equal As Strings    ${link_1['priority']}    high
    Should Be Equal As Strings    ${link_2['priority']}    medium
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_2_ID}    headers=${HEADERS}

APL005: Prevent Duplicate Links
    [Documentation]    Test that creating duplicate activity-persona links is prevented
    [Tags]    link    negative    duplicate    contract
    
    # Create initial link
    ${link_1}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_1_ID}    high    Initial link
    
    # Attempt to create duplicate link
    ${link_data}=    Create Dictionary    priority=low    notes=Duplicate attempt
    ${response}=    POST On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    json=${link_data}    headers=${HEADERS}    expected_status=409
    
    Should Be Equal As Strings    ${response.status_code}    409
    
    ${error_json}=    Set Variable    ${response.json()}
    Should Contain    ${error_json['detail']}    already linked
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}

APL006: Link With Non-Existent Persona Should Fail
    [Documentation]    Test linking to a non-existent persona returns 404
    [Tags]    link    negative    contract
    
    ${fake_persona_id}=    Set Variable    550e8400-e29b-41d4-a716-446655440000
    ${link_data}=    Create Dictionary    priority=medium
    
    ${response}=    POST On Session    api    /personas/${fake_persona_id}/activities/${TEST_ACTIVITY_1_ID}    json=${link_data}    headers=${HEADERS}    expected_status=404
    Should Be Equal As Strings    ${response.status_code}    404

APL007: Link With Non-Existent Activity Should Fail
    [Documentation]    Test linking to a non-existent activity returns 404
    [Tags]    link    negative    contract
    
    ${fake_activity_id}=    Set Variable    550e8400-e29b-41d4-a716-446655440000
    ${link_data}=    Create Dictionary    priority=medium
    
    ${response}=    POST On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${fake_activity_id}    json=${link_data}    headers=${HEADERS}    expected_status=404
    Should Be Equal As Strings    ${response.status_code}    404

APL008: Get Activities For Persona
    [Documentation]    Test retrieving all activities linked to a specific persona
    [Tags]    get    positive    contract
    
    # Create multiple links for persona 1
    ${link_1}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_1_ID}    high    Sales activity
    ${link_2}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_2_ID}    medium    Purchase activity
    
    # Get activities for persona 1
    ${response}=    GET On Session    api    /personas/${TEST_PERSONA_1_ID}/activities    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${activities_json}=    Set Variable    ${response.json()}
    Should Contain    ${activities_json}    items
    Should Contain    ${activities_json}    total
    
    # Verify we have at least our test activities
    Should Be True    ${activities_json['total']} >= 2
    Should Be True    len(${activities_json['items']}) >= 2
    
    # Verify each item contains both activity data and link metadata
    FOR    ${item}    IN    @{activities_json['items']}
        Should Contain    ${item}    activity
        Should Contain    ${item}    link
        Should Contain    ${item['activity']}    id
        Should Contain    ${item['activity']}    name
        Should Contain    ${item['link']}    priority
        Should Contain    ${item['link']}    notes
        Should Contain    ${item['link']}    created_at
    END
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_2_ID}    headers=${HEADERS}

APL009: Get Personas For Activity
    [Documentation]    Test retrieving all personas linked to a specific activity
    [Tags]    get    positive    contract
    
    # Create multiple links for activity 1
    ${link_1}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_1_ID}    high    Sales manager
    ${link_2}=    Create Activity Persona Link    ${TEST_PERSONA_2_ID}    ${TEST_ACTIVITY_1_ID}    low    Purchase manager
    
    # Get personas for activity 1
    ${response}=    GET On Session    api    /activities/${TEST_ACTIVITY_1_ID}/personas    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${personas_json}=    Set Variable    ${response.json()}
    Should Contain    ${personas_json}    items
    Should Contain    ${personas_json}    total
    
    # Verify we have at least our test personas
    Should Be True    ${personas_json['total']} >= 2
    Should Be True    len(${personas_json['items']}) >= 2
    
    # Verify each item contains both persona data and link metadata
    FOR    ${item}    IN    @{personas_json['items']}
        Should Contain    ${item}    persona
        Should Contain    ${item}    link
        Should Contain    ${item['persona']}    id
        Should Contain    ${item['persona']}    name
        Should Contain    ${item['link']}    priority
        Should Contain    ${item['link']}    notes
        Should Contain    ${item['link']}    created_at
    END
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    DELETE On Session    api    /personas/${TEST_PERSONA_2_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}

APL010: Filter Persona Activities By Priority
    [Documentation]    Test filtering persona activities by priority level
    [Tags]    get    filter    positive    contract
    
    # Create links with different priorities
    ${link_1}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_1_ID}    high    High priority task
    ${link_2}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_2_ID}    low    Low priority task
    
    # Filter by high priority
    ${params}=    Create Dictionary    priority=high
    ${response}=    GET On Session    api    /personas/${TEST_PERSONA_1_ID}/activities    params=${params}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${activities_json}=    Set Variable    ${response.json()}
    Should Be True    ${activities_json['total']} >= 1
    
    # Verify all returned activities have high priority
    FOR    ${item}    IN    @{activities_json['items']}
        Should Be Equal As Strings    ${item['link']['priority']}    high
    END
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_2_ID}    headers=${HEADERS}

APL011: Update Activity-Persona Link
    [Documentation]    Test updating the metadata of an activity-persona link
    [Tags]    update    positive    contract
    
    # Create initial link
    ${link_1}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_1_ID}    medium    Initial notes
    
    # Update the link
    ${update_data}=    Create Dictionary
    ...    priority=high
    ...    notes=Updated notes for this relationship
    
    ${response}=    PUT On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    json=${update_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${updated_link}=    Set Variable    ${response.json()}
    Validate Activity Persona Link Response    ${updated_link}
    
    # Verify updates
    Should Be Equal As Strings    ${updated_link['priority']}    high
    Should Be Equal As Strings    ${updated_link['notes']}    Updated notes for this relationship
    Should Be Equal As Strings    ${updated_link['persona_id']}    ${TEST_PERSONA_1_ID}
    Should Be Equal As Strings    ${updated_link['activity_id']}    ${TEST_ACTIVITY_1_ID}
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}

APL012: Update Non-Existent Link Should Fail
    [Documentation]    Test updating a non-existent activity-persona link returns 404
    [Tags]    update    negative    contract
    
    ${update_data}=    Create Dictionary    priority=high    notes=Updated notes
    
    ${response}=    PUT On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    json=${update_data}    headers=${HEADERS}    expected_status=404
    Should Be Equal As Strings    ${response.status_code}    404

APL013: Remove Activity-Persona Link
    [Documentation]    Test removing an activity-persona link
    [Tags]    delete    positive    contract
    
    # Create link to remove
    ${link_1}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_1_ID}    high    Link to remove
    
    # Verify link exists by getting persona activities
    ${response}=    GET On Session    api    /personas/${TEST_PERSONA_1_ID}/activities    headers=${HEADERS}
    ${activities_before}=    Set Variable    ${response.json()}
    ${initial_count}=    Set Variable    ${activities_before['total']}
    
    # Remove the link
    ${response}=    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    204
    
    # Verify link no longer exists
    ${response}=    GET On Session    api    /personas/${TEST_PERSONA_1_ID}/activities    headers=${HEADERS}
    ${activities_after}=    Set Variable    ${response.json()}
    Should Be True    ${activities_after['total']} < ${initial_count}

APL014: Remove Non-Existent Link Should Return 404
    [Documentation]    Test removing a non-existent activity-persona link returns 404
    [Tags]    delete    negative    contract
    
    ${response}=    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}    expected_status=404
    Should Be Equal As Strings    ${response.status_code}    404

APL015: Bulk Link Operations
    [Documentation]    Test bulk operations for linking activities to personas
    [Tags]    bulk    positive    contract
    
    # Test bulk link creation
    ${bulk_link_data}=    Create Dictionary
    ...    activity_ids=${TEST_ACTIVITY_1_ID},${TEST_ACTIVITY_2_ID}
    ...    priority=medium
    ...    notes=Bulk linked activities
    
    ${response}=    POST On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/bulk    json=${bulk_link_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    201
    
    ${bulk_result}=    Set Variable    ${response.json()}
    Should Contain    ${bulk_result}    linked_count
    Should Contain    ${bulk_result}    linked_activities
    Should Be Equal As Integers    ${bulk_result['linked_count']}    2
    
    # Verify links were created
    ${response}=    GET On Session    api    /personas/${TEST_PERSONA_1_ID}/activities    headers=${HEADERS}
    ${activities_json}=    Set Variable    ${response.json()}
    Should Be True    ${activities_json['total']} >= 2
    
    # Test bulk unlink
    ${bulk_unlink_data}=    Create Dictionary    activity_ids=${TEST_ACTIVITY_1_ID},${TEST_ACTIVITY_2_ID}
    ${response}=    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/bulk    json=${bulk_unlink_data}    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${unlink_result}=    Set Variable    ${response.json()}
    Should Contain    ${unlink_result}    unlinked_count
    Should Be Equal As Integers    ${unlink_result['unlinked_count']}    2

APL016: Activity-Persona Compatibility Check
    [Documentation]    Test checking compatibility between activities and personas
    [Tags]    compatibility    positive    contract
    
    # Check compatibility between sales activity and sales persona
    ${response}=    GET On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}/compatibility    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${compat_json}=    Set Variable    ${response.json()}
    Should Contain    ${compat_json}    is_compatible
    Should Contain    ${compat_json}    compatibility_score
    Should Contain    ${compat_json}    reasons
    Should Contain    ${compat_json}    suggestions
    
    # Sales manager should be compatible with sales order activity
    Should Be Equal    ${compat_json['is_compatible']}    ${True}
    Should Be True    ${compat_json['compatibility_score']} > 0.5
    
    # Check incompatible pairing (sales persona with purchase activity)
    ${response}=    GET On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_2_ID}/compatibility    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${compat_json}=    Set Variable    ${response.json()}
    # Sales manager might have lower compatibility with purchase activities
    Should Be True    ${compat_json['compatibility_score']} < 1.0

APL017: Get Activity-Persona Link Statistics
    [Documentation]    Test retrieving statistics about activity-persona relationships
    [Tags]    statistics    positive    contract
    
    # Create some test links
    ${link_1}=    Create Activity Persona Link    ${TEST_PERSONA_1_ID}    ${TEST_ACTIVITY_1_ID}    high    Test link 1
    ${link_2}=    Create Activity Persona Link    ${TEST_PERSONA_2_ID}    ${TEST_ACTIVITY_2_ID}    medium    Test link 2
    
    # Get overall link statistics
    ${response}=    GET On Session    api    /activity-persona-links/statistics    headers=${HEADERS}
    Should Be Equal As Strings    ${response.status_code}    200
    
    ${stats_json}=    Set Variable    ${response.json()}
    Should Contain    ${stats_json}    total_links
    Should Contain    ${stats_json}    unique_personas
    Should Contain    ${stats_json}    unique_activities
    Should Contain    ${stats_json}    by_priority
    Should Contain    ${stats_json}    avg_activities_per_persona
    Should Contain    ${stats_json}    avg_personas_per_activity
    
    # Verify statistics are reasonable
    Should Be True    ${stats_json['total_links']} >= 2
    Should Be True    ${stats_json['unique_personas']} >= 1
    Should Be True    ${stats_json['unique_activities']} >= 1
    
    # Verify priority breakdown
    Should Contain    ${stats_json['by_priority']}    high
    Should Contain    ${stats_json['by_priority']}    medium
    Should Contain    ${stats_json['by_priority']}    low
    
    # Cleanup
    DELETE On Session    api    /personas/${TEST_PERSONA_1_ID}/activities/${TEST_ACTIVITY_1_ID}    headers=${HEADERS}
    DELETE On Session    api    /personas/${TEST_PERSONA_2_ID}/activities/${TEST_ACTIVITY_2_ID}    headers=${HEADERS}