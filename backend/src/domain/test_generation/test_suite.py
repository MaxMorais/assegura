"""Test Suite domain entity for ERPNext Test Automation Meta-Framework.

Represents generated Robot Framework test suites with validation and
code generation capabilities for automated test execution.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from src.domain.base_entity import BaseEntity


class TestSuite(BaseEntity):
    """Domain entity representing a generated Robot Framework test suite.

    A test suite contains the generated Robot Framework code and associated
    test data templates for executing automated tests based on journey definitions.
    """

    # Core test suite fields
    journey_id: UUID = Field(..., description="ID of the source journey")
    robot_framework_code: str = Field(..., description="Generated Robot Framework test code")
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the test was generated")
    test_data_template: Dict[str, Any] = Field(default_factory=dict, description="Test data template for execution")
    consultant_id: UUID = Field(..., description="ID of the consultant who owns this test suite")

    @field_validator('robot_framework_code')
    def validate_robot_code(cls, v):
        """Validate Robot Framework code format."""
        if not v or not v.strip():
            raise ValueError("Robot Framework code is required")

        v = v.strip()

        # Basic validation - must contain essential Robot Framework sections
        required_sections = ['*** Settings ***', '*** Test Cases ***']
        for section in required_sections:
            if section not in v:
                raise ValueError(f"Robot Framework code must contain '{section}' section")

        # Check for reasonable length
        if len(v) < 100:
            raise ValueError("Robot Framework code appears to be too short")

        if len(v) > 1000000:  # 1MB limit
            raise ValueError("Robot Framework code exceeds maximum size limit")

        return v

    @field_validator('test_data_template')
    def validate_test_data_template(cls, v):
        """Validate test data template structure."""
        if not isinstance(v, dict):
            raise ValueError("Test data template must be a dictionary")

        # Basic structure validation
        if 'entities' not in v:
            raise ValueError("Test data template must contain 'entities' key")

        if not isinstance(v['entities'], (list, dict)):
            raise ValueError("Test data template 'entities' must be a list or dictionary")

        return v

    def get_test_cases(self) -> List[str]:
        """Extract test case names from the Robot Framework code."""
        lines = self.robot_framework_code.split('\n')
        test_cases = []

        in_test_cases_section = False
        for line in lines:
            line = line.strip()
            if line.startswith('*** Test Cases ***'):
                in_test_cases_section = True
                continue
            elif line.startswith('***'):
                in_test_cases_section = False
                continue

            if in_test_cases_section and line and not line.startswith('#') and not line.startswith(' '):
                # This is likely a test case name
                test_cases.append(line)

        return test_cases

    def get_keywords(self) -> List[str]:
        """Extract keyword definitions from the Robot Framework code."""
        lines = self.robot_framework_code.split('\n')
        keywords = []

        in_keywords_section = False
        for line in lines:
            line = line.strip()
            if line.startswith('*** Keywords ***'):
                in_keywords_section = True
                continue
            elif line.startswith('***'):
                in_keywords_section = False
                continue

            if in_keywords_section and line and not line.startswith('#') and not line.startswith(' '):
                # This is likely a keyword name
                keywords.append(line)

        return keywords

    def validate_syntax(self) -> bool:
        """Perform basic syntax validation of the Robot Framework code."""
        try:
            # Check for balanced brackets and quotes
            brackets = {'(': ')', '[': ']', '{': '}'}
            stack = []

            in_multiline_string = False
            string_char = None

            for char in self.robot_framework_code:
                if char in ['"', "'"] and not in_multiline_string:
                    if string_char is None:
                        string_char = char
                    elif string_char == char:
                        string_char = None
                elif char in brackets and string_char is None:
                    stack.append(char)
                elif char in brackets.values() and string_char is None:
                    if not stack:
                        return False
                    if brackets[stack[-1]] != char:
                        return False
                    stack.pop()

            return len(stack) == 0 and string_char is None

        except Exception:
            return False

    def get_test_data_requirements(self) -> Dict[str, Any]:
        """Extract test data requirements from the template."""
        requirements = {
            'entities': [],
            'parameters': [],
            'complexity': 'simple'
        }

        try:
            entities = self.test_data_template.get('entities', [])

            if isinstance(entities, list):
                requirements['entities'] = entities
            elif isinstance(entities, dict):
                requirements['entities'] = list(entities.keys())

            # Determine complexity based on data requirements
            total_entities = len(requirements['entities'])
            if total_entities > 10:
                requirements['complexity'] = 'complex'
            elif total_entities > 5:
                requirements['complexity'] = 'medium'

            # Extract parameters
            parameters = self.test_data_template.get('parameters', {})
            if isinstance(parameters, dict):
                requirements['parameters'] = list(parameters.keys())

        except Exception:
            # Return basic requirements if parsing fails
            pass

        return requirements

    def estimate_execution_time(self) -> int:
        """Estimate execution time in seconds based on test complexity."""
        requirements = self.get_test_data_requirements()

        # Base time per test case
        base_time_per_test = 30  # seconds

        # Adjust based on complexity
        complexity_multiplier = {
            'simple': 1.0,
            'medium': 1.5,
            'complex': 2.5
        }

        multiplier = complexity_multiplier.get(requirements['complexity'], 1.0)

        # Count test cases
        test_cases = self.get_test_cases()
        estimated_time = len(test_cases) * base_time_per_test * multiplier

        # Add setup/teardown time
        estimated_time += 60  # 1 minute for setup/teardown

        return int(estimated_time)

    def to_execution_format(self) -> Dict[str, Any]:
        """Convert test suite to execution-ready format."""
        return {
            'id': str(self.id),
            'journey_id': str(self.journey_id),
            'robot_code': self.robot_framework_code,
            'test_data': self.test_data_template,
            'estimated_duration': self.estimate_execution_time(),
            'generated_at': self.generation_timestamp.isoformat(),
        }

    def __str__(self) -> str:
        """String representation of the test suite."""
        test_cases = self.get_test_cases()
        return f"TestSuite(id={self.id}, journey={self.journey_id}, test_cases={len(test_cases)})"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"TestSuite("
            f"id={self.id}, "
            f"journey_id={self.journey_id}, "
            f"consultant_id={self.consultant_id}, "
            f"generation_timestamp={self.generation_timestamp}, "
            f"code_length={len(self.robot_framework_code)}"
            f")"
        )