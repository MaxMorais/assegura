"""Robot Framework code generation engine for ERPNext Test Automation Meta-Framework.

Generates executable Robot Framework test code from journey definitions,
action libraries, and test data templates.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from .test_suite import TestSuite


class RobotFrameworkGenerator:
    """Generator for Robot Framework test code from journey definitions."""

    def __init__(self):
        """Initialize the Robot Framework generator."""
        self.indent_size = 4
        self.max_line_length = 100

    def generate_test_suite(
        self,
        journey_id: UUID,
        journey_name: str,
        journey_description: str,
        steps: List[Dict[str, Any]],
        test_data_template: Dict[str, Any],
        consultant_id: UUID
    ) -> TestSuite:
        """Generate a complete Robot Framework test suite from journey data.

        Args:
            journey_id: Unique identifier of the journey
            journey_name: Human-readable name of the journey
            journey_description: Description of the journey
            steps: List of journey steps with actions and parameters
            test_data_template: Test data template for the journey
            consultant_id: ID of the consultant

        Returns:
            Generated TestSuite entity
        """
        # Generate Robot Framework code
        robot_code = self._generate_robot_code(
            journey_name, journey_description, steps, test_data_template
        )

        # Create test suite entity
        test_suite = TestSuite(
            journey_id=journey_id,
            robot_framework_code=robot_code,
            test_data_template=test_data_template,
            consultant_id=consultant_id,
        )

        return test_suite

    def _generate_robot_code(
        self,
        journey_name: str,
        journey_description: str,
        steps: List[Dict[str, Any]],
        test_data_template: Dict[str, Any]
    ) -> str:
        """Generate the complete Robot Framework code.

        Args:
            journey_name: Name of the journey
            journey_description: Description of the journey
            steps: Journey steps
            test_data_template: Test data template

        Returns:
            Complete Robot Framework code as string
        """
        code_parts = []

        # Settings section
        code_parts.append(self._generate_settings_section(journey_name, journey_description))

        # Variables section
        code_parts.append(self._generate_variables_section(test_data_template))

        # Test Cases section
        code_parts.append(self._generate_test_cases_section(journey_name, steps))

        # Keywords section
        code_parts.append(self._generate_keywords_section(steps))

        return '\n\n'.join(code_parts)

    def _generate_settings_section(self, journey_name: str, journey_description: str) -> str:
        """Generate the *** Settings *** section."""
        settings = [
            "*** Settings ***",
            f"Documentation    {journey_description}",
            "...              Generated test suite for journey: {journey_name}",
            "...              This test validates the complete business process flow.",
            "",
            "Library           Collections",
            "Library           String",
            "Library           DateTime",
            "Library           OperatingSystem",
            "",
            "# ERPNext Test Library",
            "Library           ERPNextTestLibrary.py",
            "",
            "# Test Setup and Teardown",
            "Test Setup        Setup Test Environment",
            "Test Teardown     Cleanup Test Environment",
        ]

        return '\n'.join(settings)

    def _generate_variables_section(self, test_data_template: Dict[str, Any]) -> str:
        """Generate the *** Variables *** section."""
        variables = ["*** Variables ***"]

        # Add test data variables
        entities = test_data_template.get('entities', {})
        if isinstance(entities, dict):
            for entity_type, entity_data in entities.items():
                if isinstance(entity_data, dict):
                    for key, value in entity_data.items():
                        var_name = f"${{{entity_type.upper()}_{key.upper()}}}"
                        var_value = self._format_variable_value(value)
                        variables.append(f"{var_name}    {var_value}")

        # Add common test variables
        variables.extend([
            "",
            "# Test Configuration",
            "${TEST_ENVIRONMENT}    qa",
            "${TIMEOUT}             30s",
            "${RETRY_ATTEMPTS}      3",
        ])

        return '\n'.join(variables)

    def _generate_test_cases_section(self, journey_name: str, steps: List[Dict[str, Any]]) -> str:
        """Generate the *** Test Cases *** section."""
        test_cases = [
            "*** Test Cases ***",
            "",
            f"{self._sanitize_test_name(journey_name)}",
        ]

        # Add test documentation
        test_cases.extend([
            f"    [Documentation]    Execute complete {journey_name} business process",
            f"    ...                This test validates all steps in the journey workflow.",
            "    [Tags]             journey    business_process    end_to_end",
            "",
        ])

        # Add test steps
        for i, step in enumerate(steps, 1):
            step_name = step.get('name', f'Step {i}')
            action = step.get('action', {})
            action_name = action.get('name', 'Unknown Action')

            # Generate step comment and action call
            test_cases.extend([
                f"    # {step_name}",
                f"    {self._generate_action_call(action, step.get('parameters', {}))}",
                "",
            ])

        # Add verification steps
        test_cases.extend([
            "    # Verify business outcomes",
            "    Verify Business Process Completion",
            "",
        ])

        return '\n'.join(test_cases)

    def _generate_keywords_section(self, steps: List[Dict[str, Any]]) -> str:
        """Generate the *** Keywords *** section."""
        keywords = [
            "*** Keywords ***",
            "",
            "Setup Test Environment",
            "    [Documentation]    Setup test environment and prerequisites",
            "    Log    Setting up test environment",
            "    Initialize ERPNext Connection",
            "    Setup Test Data",
            "    Login To ERPNext    ${USERNAME}    ${PASSWORD}",
            "",
            "Cleanup Test Environment",
            "    [Documentation]    Clean up test environment after execution",
            "    Log    Cleaning up test environment",
            "    Cleanup Test Data",
            "    Logout From ERPNext",
            "    Close All Browsers",
            "",
            "Verify Business Process Completion",
            "    [Documentation]    Verify that the business process completed successfully",
            "    Log    Verifying business process completion",
            "    # Add specific verification steps based on journey requirements",
            "    Log    Business process verification completed",
            "",
        ]

        # Generate keywords for each unique action
        action_keywords = self._generate_action_keywords(steps)
        keywords.extend(action_keywords)

        return '\n'.join(keywords)

    def _generate_action_keywords(self, steps: List[Dict[str, Any]]) -> List[str]:
        """Generate keywords for actions used in the journey."""
        keywords = []
        processed_actions = set()

        for step in steps:
            action = step.get('action', {})
            action_id = action.get('id')

            if action_id and action_id not in processed_actions:
                processed_actions.add(action_id)

                keyword_name = self._sanitize_keyword_name(action.get('name', 'Unknown Action'))
                keywords.extend([
                    f"{keyword_name}",
                    f"    [Documentation]    Execute {action.get('name', 'Unknown Action')}",
                    f"    [Arguments]    ${{parameters}}",
                    f"    Log    Executing action: {action.get('name', 'Unknown Action')}",
                    f"    # Implementation would call ERPNext API or UI automation",
                    f"    # Based on action type: {action.get('implementation_type', 'unknown')}",
                    f"    ERPNext API Call    {action.get('erpnext_module', 'unknown')}    {action.get('name', 'unknown')}    ${{parameters}}",
                    "",
                ])

        return keywords

    def _generate_action_call(self, action: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Generate a Robot Framework action call."""
        action_name = self._sanitize_keyword_name(action.get('name', 'Unknown Action'))

        # Format parameters
        param_str = self._format_parameters(parameters)

        if param_str:
            return f"{action_name}    {param_str}"
        else:
            return action_name

    def _format_parameters(self, parameters: Dict[str, Any]) -> str:
        """Format parameters for Robot Framework syntax."""
        if not parameters:
            return ""

        formatted_params = []
        for key, value in parameters.items():
            if isinstance(value, str):
                formatted_params.append(f"${{{key.upper()}}}")
            elif isinstance(value, (int, float)):
                formatted_params.append(str(value))
            else:
                formatted_params.append(f"${{{key.upper()}}}")

        return "    ".join(formatted_params)

    def _format_variable_value(self, value: Any) -> str:
        """Format a value for Robot Framework variable syntax."""
        if isinstance(value, str):
            return value
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return "[ " + "    ".join(str(item) for item in value) + " ]"
        elif isinstance(value, dict):
            return "{ " + "    ".join(f"{k}: {v}" for k, v in value.items()) + " }"
        else:
            return str(value)

    def _sanitize_test_name(self, name: str) -> str:
        """Sanitize a name for use as a Robot Framework test name."""
        # Replace spaces and special characters with underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9]', '_', name)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized or 'Test_Case'

    def _sanitize_keyword_name(self, name: str) -> str:
        """Sanitize a name for use as a Robot Framework keyword name."""
        # Similar to test name sanitization but allow spaces for readability
        import re
        # Replace special characters with spaces
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', ' ', name)
        # Remove multiple consecutive spaces
        sanitized = re.sub(r'\s+', ' ', sanitized)
        # Title case
        sanitized = sanitized.title()
        return sanitized or 'Keyword'

    def validate_generated_code(self, robot_code: str) -> Dict[str, Any]:
        """Validate the generated Robot Framework code.

        Args:
            robot_code: Generated Robot Framework code

        Returns:
            Validation results
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'sections_found': [],
        }

        # Check for required sections
        required_sections = ['*** Settings ***', '*** Test Cases ***', '*** Keywords ***']
        for section in required_sections:
            if section in robot_code:
                validation_result['sections_found'].append(section)
            else:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Missing required section: {section}")

        # Check for basic syntax issues
        lines = robot_code.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for unclosed brackets/quotes (basic check)
            if line.count('[') != line.count(']'):
                validation_result['warnings'].append(f"Line {i}: Unmatched brackets")
            if line.count('"') % 2 != 0:
                validation_result['warnings'].append(f"Line {i}: Unclosed quotes")

        return validation_result