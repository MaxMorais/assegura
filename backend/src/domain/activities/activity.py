"""Activity domain entity for ERPNext test automation.

This module defines the core Activity entity which represents a specific business
action that can be performed within ERPNext, such as creating a sales order,
updating customer information, or generating reports.
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .exceptions import (
    ActivityValidationError,
    ActivityMultipleValidationError,
    ActivityInvalidModuleError,
    ActivityInvalidActionTypeError
)
from .erpnext_modules import ERPNextModule, ERPNextModuleValidator


class ActivityActionType(Enum):
    """Valid action types for ERPNext activities."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    REPORT = "report"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    CANCEL = "cancel"
    SUBMIT = "submit"
    DUPLICATE = "duplicate"
    PRINT = "print"
    EMAIL = "email"


class ActivityComplexity(Enum):
    """Activity complexity levels."""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


class ActivityPriority(Enum):
    """Activity priority levels for persona relationships."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ActivityValidationRule:
    """Represents a validation rule for activity execution."""
    field_name: str
    rule_type: str  # required, min_length, max_length, regex, enum, etc.
    rule_value: Any
    error_message: str
    
    def validate(self, value: Any) -> bool:
        """Validate a value against this rule."""
        if self.rule_type == "required":
            return value is not None and value != ""
        elif self.rule_type == "min_length":
            return len(str(value)) >= self.rule_value
        elif self.rule_type == "max_length":
            return len(str(value)) <= self.rule_value
        elif self.rule_type == "regex":
            import re
            return bool(re.match(self.rule_value, str(value)))
        elif self.rule_type == "enum":
            return value in self.rule_value
        elif self.rule_type == "array_min":
            return isinstance(value, list) and len(value) >= self.rule_value
        elif self.rule_type == "array_max":
            return isinstance(value, list) and len(value) <= self.rule_value
        return True


@dataclass
class ActivitySuccessCriteria:
    """Represents success criteria for activity completion."""
    name: str
    description: str
    validation_type: str  # field_exists, field_value, api_response, ui_element, etc.
    validation_config: Dict[str, Any]
    is_required: bool = True
    
    def evaluate(self, execution_context: Dict[str, Any]) -> bool:
        """Evaluate if this success criteria is met."""
        if self.validation_type == "field_exists":
            field_path = self.validation_config.get("field_path")
            return self._check_nested_field(execution_context, field_path.split("."))
        elif self.validation_type == "field_value":
            field_path = self.validation_config.get("field_path")
            expected_value = self.validation_config.get("expected_value")
            actual_value = self._get_nested_field(execution_context, field_path.split("."))
            return actual_value == expected_value
        elif self.validation_type == "api_response":
            return execution_context.get("api_response_status") == self.validation_config.get("expected_status")
        elif self.validation_type == "ui_element":
            element_locator = self.validation_config.get("element_locator")
            return execution_context.get("ui_elements", {}).get(element_locator) is not None
        return False
    
    def _check_nested_field(self, data: Dict[str, Any], path: List[str]) -> bool:
        """Check if a nested field exists in the data."""
        current = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        return True
    
    def _get_nested_field(self, data: Dict[str, Any], path: List[str]) -> Any:
        """Get a nested field value from the data."""
        current = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current


class Activity:
    """Domain entity representing a business activity in ERPNext.
    
    An Activity represents a specific action that can be performed within ERPNext,
    such as creating documents, updating records, generating reports, etc.
    Activities are linked to Personas to define test scenarios.
    """
    
    def __init__(
        self,
        name: str,
        erpnext_module: str,
        action_type: str,
        target_doctype: str,
        description: str = "",
        required_fields: Optional[List[str]] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
        success_criteria: Optional[List[str]] = None,
        complexity_score: int = 1,
        estimated_duration: int = 60,  # seconds
        prerequisites: Optional[List[str]] = None,
        postconditions: Optional[List[str]] = None,
        test_data_requirements: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        tags: Optional[List[str]] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        version: int = 1
    ):
        """Initialize an Activity entity."""
        self.id = id or uuid.uuid4()
        self.name = name
        self.description = description
        self.erpnext_module = erpnext_module
        self.action_type = action_type
        self.target_doctype = target_doctype
        self.required_fields = required_fields or []
        self.validation_rules = validation_rules or {}
        self.success_criteria = success_criteria or []
        self.complexity_score = complexity_score
        self.estimated_duration = estimated_duration
        self.prerequisites = prerequisites or []
        self.postconditions = postconditions or []
        self.test_data_requirements = test_data_requirements or {}
        self.is_active = is_active
        self.tags = tags or []
        self.version = version
        
        # Metadata
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # Validate the activity on creation
        self._validate()
    
    def _validate(self) -> None:
        """Validate the activity data."""
        errors = []
        
        # Validate name
        if not self.name or not self.name.strip():
            errors.append(ActivityValidationError("name", "Name is required and cannot be empty"))
        elif len(self.name.strip()) < 3:
            errors.append(ActivityValidationError("name", "Name must be at least 3 characters long"))
        elif len(self.name.strip()) > 100:
            errors.append(ActivityValidationError("name", "Name cannot exceed 100 characters"))
        
        # Validate ERPNext module
        if not ERPNextModuleValidator.is_valid_module(self.erpnext_module):
            errors.append(ActivityInvalidModuleError(self.erpnext_module))
        
        # Validate action type
        valid_action_types = [action.value for action in ActivityActionType]
        if self.action_type not in valid_action_types:
            errors.append(ActivityInvalidActionTypeError(self.action_type, valid_action_types))
        
        # Validate target doctype
        if not self.target_doctype or not self.target_doctype.strip():
            errors.append(ActivityValidationError("target_doctype", "Target DocType is required"))
        
        # Validate complexity score
        if not isinstance(self.complexity_score, int) or self.complexity_score < 1 or self.complexity_score > 5:
            errors.append(ActivityValidationError("complexity_score", "Complexity score must be an integer between 1 and 5"))
        
        # Validate estimated duration
        if not isinstance(self.estimated_duration, int) or self.estimated_duration <= 0:
            errors.append(ActivityValidationError("estimated_duration", "Estimated duration must be a positive integer (seconds)"))
        
        # Validate required fields
        if self.required_fields and not isinstance(self.required_fields, list):
            errors.append(ActivityValidationError("required_fields", "Required fields must be a list"))
        
        # Validate validation rules format
        if self.validation_rules and not isinstance(self.validation_rules, dict):
            errors.append(ActivityValidationError("validation_rules", "Validation rules must be a dictionary"))
        
        # Validate success criteria
        if self.success_criteria and not isinstance(self.success_criteria, list):
            errors.append(ActivityValidationError("success_criteria", "Success criteria must be a list"))
        
        if errors:
            if len(errors) == 1:
                raise errors[0]
            else:
                raise ActivityMultipleValidationError(errors)
    
    @property
    def required_fields_str(self) -> str:
        """Get required fields as comma-separated string."""
        return ",".join(self.required_fields)
    
    @property
    def success_criteria_str(self) -> str:
        """Get success criteria as comma-separated string."""
        return ",".join(self.success_criteria)
    
    @property
    def prerequisites_str(self) -> str:
        """Get prerequisites as comma-separated string."""
        return ",".join(self.prerequisites)
    
    @property
    def postconditions_str(self) -> str:
        """Get postconditions as comma-separated string."""
        return ",".join(self.postconditions)
    
    @property
    def tags_str(self) -> str:
        """Get tags as comma-separated string."""
        return ",".join(self.tags)
    
    @property
    def validation_rules_json(self) -> str:
        """Get validation rules as JSON string."""
        return json.dumps(self.validation_rules, sort_keys=True)
    
    @property
    def test_data_requirements_json(self) -> str:
        """Get test data requirements as JSON string."""
        return json.dumps(self.test_data_requirements, sort_keys=True)
    
    def get_complexity_level(self) -> ActivityComplexity:
        """Get the complexity level enum."""
        return ActivityComplexity(self.complexity_score)
    
    def get_action_type_enum(self) -> ActivityActionType:
        """Get the action type enum."""
        return ActivityActionType(self.action_type)
    
    def update_name(self, new_name: str) -> None:
        """Update the activity name."""
        if not new_name or not new_name.strip():
            raise ActivityValidationError("name", "Name cannot be empty")
        
        if len(new_name.strip()) < 3:
            raise ActivityValidationError("name", "Name must be at least 3 characters long")
        
        if len(new_name.strip()) > 100:
            raise ActivityValidationError("name", "Name cannot exceed 100 characters")
        
        self.name = new_name.strip()
        self._update_metadata()
    
    def update_description(self, new_description: str) -> None:
        """Update the activity description."""
        self.description = new_description
        self._update_metadata()
    
    def update_complexity_score(self, new_score: int) -> None:
        """Update the complexity score."""
        if not isinstance(new_score, int) or new_score < 1 or new_score > 5:
            raise ActivityValidationError("complexity_score", "Complexity score must be an integer between 1 and 5")
        
        self.complexity_score = new_score
        self._update_metadata()
    
    def update_estimated_duration(self, new_duration: int) -> None:
        """Update the estimated duration."""
        if not isinstance(new_duration, int) or new_duration <= 0:
            raise ActivityValidationError("estimated_duration", "Estimated duration must be a positive integer (seconds)")
        
        self.estimated_duration = new_duration
        self._update_metadata()
    
    def add_required_field(self, field_name: str) -> None:
        """Add a required field."""
        if field_name and field_name not in self.required_fields:
            self.required_fields.append(field_name)
            self._update_metadata()
    
    def remove_required_field(self, field_name: str) -> None:
        """Remove a required field."""
        if field_name in self.required_fields:
            self.required_fields.remove(field_name)
            self._update_metadata()
    
    def add_success_criteria(self, criteria: str) -> None:
        """Add success criteria."""
        if criteria and criteria not in self.success_criteria:
            self.success_criteria.append(criteria)
            self._update_metadata()
    
    def remove_success_criteria(self, criteria: str) -> None:
        """Remove success criteria."""
        if criteria in self.success_criteria:
            self.success_criteria.remove(criteria)
            self._update_metadata()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag."""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self._update_metadata()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag."""
        if tag in self.tags:
            self.tags.remove(tag)
            self._update_metadata()
    
    def update_validation_rules(self, new_rules: Dict[str, Any]) -> None:
        """Update validation rules."""
        if not isinstance(new_rules, dict):
            raise ActivityValidationError("validation_rules", "Validation rules must be a dictionary")
        
        self.validation_rules = new_rules
        self._update_metadata()
    
    def add_validation_rule(self, field_name: str, rule: Dict[str, Any]) -> None:
        """Add or update a validation rule for a field."""
        self.validation_rules[field_name] = rule
        self._update_metadata()
    
    def remove_validation_rule(self, field_name: str) -> None:
        """Remove a validation rule for a field."""
        if field_name in self.validation_rules:
            del self.validation_rules[field_name]
            self._update_metadata()
    
    def activate(self) -> None:
        """Activate the activity."""
        if not self.is_active:
            self.is_active = True
            self._update_metadata()
    
    def deactivate(self) -> None:
        """Deactivate the activity."""
        if self.is_active:
            self.is_active = False
            self._update_metadata()
    
    def get_validation_rules_objects(self) -> List[ActivityValidationRule]:
        """Get validation rules as objects."""
        rules = []
        for field_name, rule_config in self.validation_rules.items():
            if isinstance(rule_config, dict):
                for rule_type, rule_value in rule_config.items():
                    rule = ActivityValidationRule(
                        field_name=field_name,
                        rule_type=rule_type,
                        rule_value=rule_value,
                        error_message=f"Field {field_name} failed {rule_type} validation"
                    )
                    rules.append(rule)
        return rules
    
    def validate_execution_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate data against activity's validation rules."""
        errors = []
        validation_rules = self.get_validation_rules_objects()
        
        for rule in validation_rules:
            field_value = data.get(rule.field_name)
            if not rule.validate(field_value):
                errors.append(rule.error_message)
        
        # Check required fields
        for field_name in self.required_fields:
            if field_name not in data or data[field_name] is None or data[field_name] == "":
                errors.append(f"Required field '{field_name}' is missing or empty")
        
        return errors
    
    def is_compatible_with_module(self, module: str) -> bool:
        """Check if activity is compatible with a specific ERPNext module."""
        return self.erpnext_module == module
    
    def is_compatible_with_action_type(self, action_type: str) -> bool:
        """Check if activity is compatible with a specific action type."""
        return self.action_type == action_type
    
    def get_estimated_duration_minutes(self) -> float:
        """Get estimated duration in minutes."""
        return self.estimated_duration / 60.0
    
    def get_estimated_duration_hours(self) -> float:
        """Get estimated duration in hours."""
        return self.estimated_duration / 3600.0
    
    def calculate_similarity(self, other: 'Activity') -> float:
        """Calculate similarity score with another activity (0.0 to 1.0)."""
        if not isinstance(other, Activity):
            return 0.0
        
        similarity_factors = []
        
        # Module similarity (highest weight)
        module_similarity = 1.0 if self.erpnext_module == other.erpnext_module else 0.0
        similarity_factors.append((module_similarity, 0.3))
        
        # Action type similarity
        action_similarity = 1.0 if self.action_type == other.action_type else 0.0
        similarity_factors.append((action_similarity, 0.25))
        
        # DocType similarity
        doctype_similarity = 1.0 if self.target_doctype == other.target_doctype else 0.0
        similarity_factors.append((doctype_similarity, 0.2))
        
        # Complexity similarity
        complexity_diff = abs(self.complexity_score - other.complexity_score)
        complexity_similarity = max(0, 1 - (complexity_diff / 4))
        similarity_factors.append((complexity_similarity, 0.1))
        
        # Required fields overlap
        if self.required_fields and other.required_fields:
            common_fields = set(self.required_fields) & set(other.required_fields)
            total_fields = set(self.required_fields) | set(other.required_fields)
            fields_similarity = len(common_fields) / len(total_fields) if total_fields else 0
        else:
            fields_similarity = 1.0 if not self.required_fields and not other.required_fields else 0.0
        similarity_factors.append((fields_similarity, 0.1))
        
        # Tags overlap
        if self.tags and other.tags:
            common_tags = set(self.tags) & set(other.tags)
            total_tags = set(self.tags) | set(other.tags)
            tags_similarity = len(common_tags) / len(total_tags) if total_tags else 0
        else:
            tags_similarity = 1.0 if not self.tags and not other.tags else 0.0
        similarity_factors.append((tags_similarity, 0.05))
        
        # Calculate weighted average
        total_score = sum(score * weight for score, weight in similarity_factors)
        return min(1.0, max(0.0, total_score))
    
    def _update_metadata(self) -> None:
        """Update metadata timestamps and version."""
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def __str__(self) -> str:
        """String representation of the activity."""
        return f"Activity(id={self.id}, name='{self.name}', module={self.erpnext_module}, action={self.action_type})"
    
    def __repr__(self) -> str:
        """Developer representation of the activity."""
        return (f"Activity(id={self.id}, name='{self.name}', "
                f"module={self.erpnext_module}, action={self.action_type}, "
                f"target={self.target_doctype}, complexity={self.complexity_score})")
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on ID."""
        if not isinstance(other, Activity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash function based on ID."""
        return hash(self.id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary representation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'erpnext_module': self.erpnext_module,
            'action_type': self.action_type,
            'target_doctype': self.target_doctype,
            'required_fields': self.required_fields,
            'validation_rules': self.validation_rules,
            'success_criteria': self.success_criteria,
            'complexity_score': self.complexity_score,
            'estimated_duration': self.estimated_duration,
            'prerequisites': self.prerequisites,
            'postconditions': self.postconditions,
            'test_data_requirements': self.test_data_requirements,
            'is_active': self.is_active,
            'tags': self.tags,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Activity':
        """Create activity from dictionary representation."""
        # Convert string dates back to datetime objects
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        activity_id = uuid.UUID(data['id']) if data.get('id') else None
        
        return cls(
            id=activity_id,
            name=data['name'],
            description=data.get('description', ''),
            erpnext_module=data['erpnext_module'],
            action_type=data['action_type'],
            target_doctype=data['target_doctype'],
            required_fields=data.get('required_fields', []),
            validation_rules=data.get('validation_rules', {}),
            success_criteria=data.get('success_criteria', []),
            complexity_score=data.get('complexity_score', 1),
            estimated_duration=data.get('estimated_duration', 60),
            prerequisites=data.get('prerequisites', []),
            postconditions=data.get('postconditions', []),
            test_data_requirements=data.get('test_data_requirements', {}),
            is_active=data.get('is_active', True),
            tags=data.get('tags', []),
            version=data.get('version', 1),
            created_at=created_at,
            updated_at=updated_at
        )