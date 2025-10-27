"""Test data templates and parameterization for test data generation.

This module provides:
- Template-based test data generation
- Parameter substitution and randomization
- ERPNext entity-specific templates
- Validation and constraints
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4
import random
import string


class FieldType(str, Enum):
    """Types of fields in test data templates."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    CURRENCY = "currency"
    REFERENCE = "reference"  # Reference to another entity
    ENUM = "enum"


class DataTemplate:
    """Test data template for generating ERPNext entities.

    Attributes:
        entity_type: Type of ERPNext entity (e.g., 'Customer', 'Item')
        fields: Field definitions with generation rules
        constraints: Validation constraints for generated data
    """

    def __init__(
        self,
        entity_type: str,
        fields: Dict[str, Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None,
    ):
        """Initialize DataTemplate.

        Args:
            entity_type: ERPNext entity type name
            fields: Dictionary of field definitions
                   {field_name: {type: FieldType, params: {...}}}
            constraints: Optional validation constraints
        """
        self.entity_type = entity_type
        self.fields = fields
        self.constraints = constraints or {}

    def generate(
        self, count: int = 1, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate test data instances from template.

        Args:
            count: Number of entities to generate
            parameters: Optional parameter overrides

        Returns:
            List of generated entity dictionaries

        Raises:
            ValueError: If generation fails validation
        """
        parameters = parameters or {}
        entities = []

        for i in range(count):
            entity = {}
            for field_name, field_def in self.fields.items():
                # Check if parameter override provided
                if field_name in parameters:
                    entity[field_name] = parameters[field_name]
                else:
                    # Generate value based on field type
                    entity[field_name] = self._generate_field_value(
                        field_def, i, parameters
                    )

            # Apply constraints
            self._apply_constraints(entity)
            entities.append(entity)

        return entities

    def _generate_field_value(
        self, field_def: Dict[str, Any], index: int, parameters: Dict[str, Any]
    ) -> Any:
        """Generate a single field value.

        Args:
            field_def: Field definition dictionary
            index: Index in generation sequence
            parameters: Generation parameters

        Returns:
            Generated field value
        """
        field_type = field_def.get("type", FieldType.STRING)
        params = field_def.get("params", {})

        generators = {
            FieldType.STRING: self._generate_string,
            FieldType.INTEGER: self._generate_integer,
            FieldType.FLOAT: self._generate_float,
            FieldType.BOOLEAN: self._generate_boolean,
            FieldType.DATE: self._generate_date,
            FieldType.DATETIME: self._generate_datetime,
            FieldType.EMAIL: self._generate_email,
            FieldType.PHONE: self._generate_phone,
            FieldType.CURRENCY: self._generate_currency,
            FieldType.REFERENCE: self._generate_reference,
            FieldType.ENUM: self._generate_enum,
        }

        generator = generators.get(field_type, self._generate_string)
        return generator(params, index)

    def _generate_string(self, params: Dict[str, Any], index: int) -> str:
        """Generate string value."""
        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")
        pattern = params.get("pattern", None)
        length = params.get("length", 10)

        if pattern:
            # Custom pattern (e.g., "{prefix}-{index:04d}")
            return pattern.format(prefix=prefix, suffix=suffix, index=index)
        
        # Random string
        chars = string.ascii_uppercase + string.digits
        random_str = ''.join(random.choice(chars) for _ in range(length))
        return f"{prefix}{random_str}{suffix}"

    def _generate_integer(self, params: Dict[str, Any], index: int) -> int:
        """Generate integer value."""
        min_val = params.get("min", 0)
        max_val = params.get("max", 1000)
        return random.randint(min_val, max_val)

    def _generate_float(self, params: Dict[str, Any], index: int) -> float:
        """Generate float value."""
        min_val = params.get("min", 0.0)
        max_val = params.get("max", 1000.0)
        precision = params.get("precision", 2)
        value = random.uniform(min_val, max_val)
        return round(value, precision)

    def _generate_boolean(self, params: Dict[str, Any], index: int) -> bool:
        """Generate boolean value."""
        probability = params.get("probability", 0.5)
        return random.random() < probability

    def _generate_date(self, params: Dict[str, Any], index: int) -> str:
        """Generate date string."""
        days_ago = params.get("days_ago", 0)
        days_ahead = params.get("days_ahead", 0)
        
        if days_ahead > 0:
            date = datetime.now() + timedelta(days=random.randint(0, days_ahead))
        else:
            date = datetime.now() - timedelta(days=random.randint(0, days_ago))
        
        return date.strftime("%Y-%m-%d")

    def _generate_datetime(self, params: Dict[str, Any], index: int) -> str:
        """Generate datetime string."""
        days_ago = params.get("days_ago", 0)
        days_ahead = params.get("days_ahead", 0)
        
        if days_ahead > 0:
            dt = datetime.now() + timedelta(days=random.randint(0, days_ahead))
        else:
            dt = datetime.now() - timedelta(days=random.randint(0, days_ago))
        
        return dt.isoformat()

    def _generate_email(self, params: Dict[str, Any], index: int) -> str:
        """Generate email address."""
        domain = params.get("domain", "test.example.com")
        prefix = params.get("prefix", "user")
        return f"{prefix}{index}@{domain}"

    def _generate_phone(self, params: Dict[str, Any], index: int) -> str:
        """Generate phone number."""
        country_code = params.get("country_code", "+1")
        area_code = random.randint(200, 999)
        exchange = random.randint(200, 999)
        number = random.randint(1000, 9999)
        return f"{country_code} {area_code}-{exchange}-{number}"

    def _generate_currency(self, params: Dict[str, Any], index: int) -> float:
        """Generate currency value."""
        min_val = params.get("min", 0.0)
        max_val = params.get("max", 10000.0)
        value = random.uniform(min_val, max_val)
        return round(value, 2)

    def _generate_reference(self, params: Dict[str, Any], index: int) -> str:
        """Generate reference to another entity."""
        # This would typically reference a previously generated entity
        ref_type = params.get("ref_type", "")
        ref_list = params.get("ref_list", [])
        
        if ref_list:
            return random.choice(ref_list)
        
        return f"{ref_type}-{uuid4().hex[:8]}"

    def _generate_enum(self, params: Dict[str, Any], index: int) -> str:
        """Generate enum value."""
        values = params.get("values", ["Option1", "Option2"])
        weights = params.get("weights", None)
        
        if weights:
            return random.choices(values, weights=weights)[0]
        return random.choice(values)

    def _apply_constraints(self, entity: Dict[str, Any]) -> None:
        """Apply validation constraints to generated entity.

        Args:
            entity: Generated entity dictionary

        Raises:
            ValueError: If constraints are violated
        """
        for constraint_name, constraint_def in self.constraints.items():
            constraint_type = constraint_def.get("type")
            
            if constraint_type == "required":
                required_fields = constraint_def.get("fields", [])
                for field in required_fields:
                    if field not in entity or entity[field] is None:
                        raise ValueError(
                            f"Required field '{field}' missing in {self.entity_type}"
                        )
            
            elif constraint_type == "unique":
                # Unique constraints would need to be checked against existing data
                pass
            
            elif constraint_type == "range":
                field = constraint_def.get("field")
                min_val = constraint_def.get("min")
                max_val = constraint_def.get("max")
                
                if field in entity:
                    value = entity[field]
                    if min_val is not None and value < min_val:
                        raise ValueError(
                            f"Field '{field}' value {value} below minimum {min_val}"
                        )
                    if max_val is not None and value > max_val:
                        raise ValueError(
                            f"Field '{field}' value {value} above maximum {max_val}"
                        )


class ERPNextTemplateLibrary:
    """Pre-defined templates for common ERPNext entities."""

    @staticmethod
    def customer_template() -> DataTemplate:
        """Get customer entity template."""
        return DataTemplate(
            entity_type="Customer",
            fields={
                "customer_name": {
                    "type": FieldType.STRING,
                    "params": {"pattern": "Customer-{index:04d}"},
                },
                "customer_type": {
                    "type": FieldType.ENUM,
                    "params": {"values": ["Company", "Individual"]},
                },
                "customer_group": {
                    "type": FieldType.ENUM,
                    "params": {"values": ["Commercial", "Government", "Individual"]},
                },
                "territory": {
                    "type": FieldType.STRING,
                    "params": {"prefix": "Territory-"},
                },
                "email_id": {
                    "type": FieldType.EMAIL,
                    "params": {"prefix": "customer", "domain": "test.example.com"},
                },
                "mobile_no": {"type": FieldType.PHONE, "params": {}},
            },
            constraints={
                "required": {
                    "type": "required",
                    "fields": ["customer_name", "customer_type"],
                }
            },
        )

    @staticmethod
    def item_template() -> DataTemplate:
        """Get item entity template."""
        return DataTemplate(
            entity_type="Item",
            fields={
                "item_code": {
                    "type": FieldType.STRING,
                    "params": {"pattern": "ITEM-{index:05d}"},
                },
                "item_name": {
                    "type": FieldType.STRING,
                    "params": {"pattern": "Test Item {index}"},
                },
                "item_group": {
                    "type": FieldType.ENUM,
                    "params": {"values": ["Products", "Raw Material", "Services"]},
                },
                "stock_uom": {
                    "type": FieldType.ENUM,
                    "params": {"values": ["Nos", "Kg", "Meter", "Unit"]},
                },
                "standard_rate": {
                    "type": FieldType.CURRENCY,
                    "params": {"min": 10.0, "max": 10000.0},
                },
                "is_stock_item": {"type": FieldType.BOOLEAN, "params": {}},
                "opening_stock": {
                    "type": FieldType.INTEGER,
                    "params": {"min": 0, "max": 1000},
                },
            },
            constraints={
                "required": {
                    "type": "required",
                    "fields": ["item_code", "item_name", "stock_uom"],
                }
            },
        )

    @staticmethod
    def sales_order_template() -> DataTemplate:
        """Get sales order entity template."""
        return DataTemplate(
            entity_type="Sales Order",
            fields={
                "customer": {
                    "type": FieldType.REFERENCE,
                    "params": {"ref_type": "Customer"},
                },
                "transaction_date": {
                    "type": FieldType.DATE,
                    "params": {"days_ago": 30},
                },
                "delivery_date": {
                    "type": FieldType.DATE,
                    "params": {"days_ahead": 30},
                },
                "order_type": {
                    "type": FieldType.ENUM,
                    "params": {"values": ["Sales", "Maintenance", "Shopping Cart"]},
                },
                "company": {"type": FieldType.STRING, "params": {}},
            },
            constraints={
                "required": {
                    "type": "required",
                    "fields": ["customer", "transaction_date", "delivery_date"],
                }
            },
        )

    @staticmethod
    def get_template(entity_type: str) -> Optional[DataTemplate]:
        """Get template by entity type name.

        Args:
            entity_type: ERPNext entity type

        Returns:
            DataTemplate instance or None if not found
        """
        templates = {
            "Customer": ERPNextTemplateLibrary.customer_template,
            "Item": ERPNextTemplateLibrary.item_template,
            "Sales Order": ERPNextTemplateLibrary.sales_order_template,
        }
        
        template_fn = templates.get(entity_type)
        return template_fn() if template_fn else None
