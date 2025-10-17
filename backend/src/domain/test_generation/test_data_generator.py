"""Test data generation logic for ERPNext Test Automation Meta-Framework.

Generates realistic test data for ERPNext entities required by automated tests,
with support for relationships, constraints, and cleanup strategies.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from faker import Faker

from .test_suite import TestSuite


class TestDataGenerator:
    """Generator for test data required by automated tests."""

    def __init__(self, locale: str = 'en_US'):
        """Initialize the test data generator.

        Args:
            locale: Locale for fake data generation
        """
        self.faker = Faker(locale)
        self.generated_ids: Set[str] = set()

    def generate_test_data(
        self,
        journey_id: UUID,
        required_entities: List[Dict[str, Any]],
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate test data for a journey's test execution.

        Args:
            journey_id: ID of the journey requiring test data
            required_entities: List of entities needed for the test
            parameters: Optional parameters for data generation

        Returns:
            Generated test data template
        """
        if parameters is None:
            parameters = {}

        test_data = {
            'journey_id': str(journey_id),
            'generated_at': datetime.utcnow().isoformat(),
            'entities': {},
            'relationships': [],
            'cleanup_required': True,
        }

        # Generate data for each required entity
        for entity_spec in required_entities:
            entity_type = entity_spec.get('type', 'unknown')
            entity_count = entity_spec.get('count', 1)
            entity_config = entity_spec.get('config', {})

            generated_entities = []
            for _ in range(entity_count):
                entity_data = self._generate_entity_data(entity_type, entity_config)
                generated_entities.append(entity_data)

            test_data['entities'][entity_type] = generated_entities

        # Establish relationships between entities
        test_data['relationships'] = self._establish_relationships(test_data['entities'])

        return test_data

    def _generate_entity_data(self, entity_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for a specific ERPNext entity type.

        Args:
            entity_type: Type of entity (Customer, Item, Sales Order, etc.)
            config: Configuration for data generation

        Returns:
            Generated entity data
        """
        generators = {
            'Customer': self._generate_customer_data,
            'Item': self._generate_item_data,
            'Sales Order': self._generate_sales_order_data,
            'Purchase Order': self._generate_purchase_order_data,
            'Supplier': self._generate_supplier_data,
            'Employee': self._generate_employee_data,
            'Warehouse': self._generate_warehouse_data,
            'Journal Entry': self._generate_journal_entry_data,
        }

        generator = generators.get(entity_type, self._generate_generic_entity_data)
        return generator(config)

    def _generate_customer_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customer entity data."""
        customer_name = self._generate_unique_name(
            self.faker.company(),
            'customer'
        )

        return {
            'doctype': 'Customer',
            'customer_name': customer_name,
            'customer_type': config.get('customer_type', 'Company'),
            'customer_group': config.get('customer_group', 'Commercial'),
            'territory': config.get('territory', 'Rest Of The World'),
            'default_currency': config.get('currency', 'USD'),
            'default_price_list': config.get('price_list', 'Standard Selling'),
            'tax_id': self.faker.ssn(),
            'website': self.faker.url(),
            'email_id': self.faker.company_email(),
            'mobile_no': self.faker.phone_number(),
        }

    def _generate_item_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate item entity data."""
        item_name = self._generate_unique_name(
            self.faker.word().title(),
            'item'
        )

        return {
            'doctype': 'Item',
            'item_code': f"TEST-{item_name.upper()}",
            'item_name': item_name,
            'item_group': config.get('item_group', 'Products'),
            'stock_uom': config.get('uom', 'Nos'),
            'is_stock_item': config.get('is_stock_item', True),
            'valuation_rate': config.get('valuation_rate', self.faker.random_int(10, 1000)),
            'standard_rate': config.get('standard_rate', self.faker.random_int(50, 2000)),
            'description': self.faker.sentence(),
            'brand': config.get('brand', self.faker.company()),
        }

    def _generate_sales_order_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sales order entity data."""
        return {
            'doctype': 'Sales Order',
            'customer': config.get('customer'),  # Will be set by relationships
            'transaction_date': datetime.utcnow().date().isoformat(),
            'delivery_date': (datetime.utcnow() + timedelta(days=7)).date().isoformat(),
            'currency': config.get('currency', 'USD'),
            'selling_price_list': config.get('price_list', 'Standard Selling'),
            'items': [],  # Will be populated by relationships
            'total_qty': 0,
            'total': 0,
        }

    def _generate_purchase_order_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate purchase order entity data."""
        return {
            'doctype': 'Purchase Order',
            'supplier': config.get('supplier'),  # Will be set by relationships
            'transaction_date': datetime.utcnow().date().isoformat(),
            'schedule_date': (datetime.utcnow() + timedelta(days=14)).date().isoformat(),
            'currency': config.get('currency', 'USD'),
            'buying_price_list': config.get('price_list', 'Standard Buying'),
            'items': [],  # Will be populated by relationships
            'total_qty': 0,
            'total': 0,
        }

    def _generate_supplier_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate supplier entity data."""
        supplier_name = self._generate_unique_name(
            self.faker.company(),
            'supplier'
        )

        return {
            'doctype': 'Supplier',
            'supplier_name': supplier_name,
            'supplier_type': config.get('supplier_type', 'Company'),
            'supplier_group': config.get('supplier_group', 'Local'),
            'default_currency': config.get('currency', 'USD'),
            'default_price_list': config.get('price_list', 'Standard Buying'),
            'tax_id': self.faker.ssn(),
            'website': self.faker.url(),
            'email_id': self.faker.company_email(),
        }

    def _generate_employee_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate employee entity data."""
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        employee_name = f"{first_name} {last_name}"

        return {
            'doctype': 'Employee',
            'employee_name': employee_name,
            'first_name': first_name,
            'last_name': last_name,
            'gender': config.get('gender', self.faker.random_element(['Male', 'Female'])),
            'date_of_birth': self.faker.date_of_birth(minimum_age=18, maximum_age=65).isoformat(),
            'date_of_joining': self.faker.date_between(start_date='-5y', end_date='today').isoformat(),
            'department': config.get('department', 'General'),
            'designation': config.get('designation', 'Employee'),
            'company': config.get('company', 'Test Company'),
            'status': 'Active',
        }

    def _generate_warehouse_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate warehouse entity data."""
        warehouse_name = self._generate_unique_name(
            f"{self.faker.city()} Warehouse",
            'warehouse'
        )

        return {
            'doctype': 'Warehouse',
            'warehouse_name': warehouse_name,
            'is_group': False,
            'company': config.get('company', 'Test Company'),
            'account': config.get('account', 'Primary Warehouse - TC'),
        }

    def _generate_journal_entry_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate journal entry entity data."""
        return {
            'doctype': 'Journal Entry',
            'posting_date': datetime.utcnow().date().isoformat(),
            'company': config.get('company', 'Test Company'),
            'accounts': [],  # Will be populated by relationships
            'total_debit': 0,
            'total_credit': 0,
        }

    def _generate_generic_entity_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic entity data for unknown types."""
        return {
            'doctype': config.get('doctype', 'Unknown'),
            'name': self._generate_unique_name('Test Entity', 'generic'),
            'description': self.faker.sentence(),
        }

    def _generate_unique_name(self, base_name: str, entity_type: str) -> str:
        """Generate a unique name for an entity.

        Args:
            base_name: Base name to make unique
            entity_type: Type of entity for uniqueness tracking

        Returns:
            Unique name
        """
        counter = 1
        unique_name = base_name

        while f"{entity_type}:{unique_name}" in self.generated_ids:
            unique_name = f"{base_name} {counter}"
            counter += 1

        self.generated_ids.add(f"{entity_type}:{unique_name}")
        return unique_name

    def _establish_relationships(self, entities: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Establish relationships between generated entities.

        Args:
            entities: Generated entity data

        Returns:
            List of established relationships
        """
        relationships = []

        # Link sales orders to customers and items
        if 'Sales Order' in entities and 'Customer' in entities:
            for so in entities['Sales Order']:
                customer = random.choice(entities['Customer'])
                so['customer'] = customer['customer_name']
                relationships.append({
                    'from_entity': 'Sales Order',
                    'from_field': 'customer',
                    'to_entity': 'Customer',
                    'to_value': customer['customer_name'],
                })

        # Link purchase orders to suppliers and items
        if 'Purchase Order' in entities and 'Supplier' in entities:
            for po in entities['Purchase Order']:
                supplier = random.choice(entities['Supplier'])
                po['supplier'] = supplier['supplier_name']
                relationships.append({
                    'from_entity': 'Purchase Order',
                    'from_field': 'supplier',
                    'to_entity': 'Supplier',
                    'to_value': supplier['supplier_name'],
                })

        # Add items to orders
        if 'Item' in entities:
            items = entities['Item']

            # Add items to sales orders
            if 'Sales Order' in entities:
                for so in entities['Sales Order']:
                    order_items = self._generate_order_items(items, 'sales')
                    so['items'] = order_items
                    so['total_qty'] = sum(item['qty'] for item in order_items)
                    so['total'] = sum(item['amount'] for item in order_items)

            # Add items to purchase orders
            if 'Purchase Order' in entities:
                for po in entities['Purchase Order']:
                    order_items = self._generate_order_items(items, 'purchase')
                    po['items'] = order_items
                    po['total_qty'] = sum(item['qty'] for item in order_items)
                    po['total'] = sum(item['amount'] for item in order_items)

        return relationships

    def _generate_order_items(self, available_items: List[Dict[str, Any]], order_type: str) -> List[Dict[str, Any]]:
        """Generate items for an order.

        Args:
            available_items: List of available items
            order_type: Type of order ('sales' or 'purchase')

        Returns:
            List of order items
        """
        if not available_items:
            return []

        # Select 1-3 random items
        num_items = random.randint(1, min(3, len(available_items)))
        selected_items = random.sample(available_items, num_items)

        order_items = []
        for item in selected_items:
            qty = random.randint(1, 10)
            rate = item.get('standard_rate', item.get('valuation_rate', 100))

            order_item = {
                'item_code': item['item_code'],
                'item_name': item['item_name'],
                'qty': qty,
                'rate': rate,
                'amount': qty * rate,
                'uom': item.get('stock_uom', 'Nos'),
            }

            # Add order-specific fields
            if order_type == 'sales':
                order_item['warehouse'] = 'Stores - TC'
            elif order_type == 'purchase':
                order_item['warehouse'] = 'Stores - TC'
                order_item['schedule_date'] = (datetime.utcnow() + timedelta(days=7)).date().isoformat()

            order_items.append(order_item)

        return order_items

    def generate_cleanup_script(self, test_data: Dict[str, Any]) -> str:
        """Generate a cleanup script for test data.

        Args:
            test_data: Test data that needs cleanup

        Returns:
            Cleanup script/commands
        """
        cleanup_commands = [
            "# Test Data Cleanup Script",
            f"# Generated: {datetime.utcnow().isoformat()}",
            "",
        ]

        entities = test_data.get('entities', {})

        # Define cleanup order (reverse of creation order)
        cleanup_order = [
            'Journal Entry',
            'Sales Order',
            'Purchase Order',
            'Employee',
            'Customer',
            'Supplier',
            'Item',
            'Warehouse',
        ]

        for entity_type in cleanup_order:
            if entity_type in entities:
                cleanup_commands.append(f"# Clean up {entity_type} entities")
                for entity in entities[entity_type]:
                    name_field = self._get_name_field_for_entity(entity_type)
                    entity_name = entity.get(name_field, entity.get('name', 'Unknown'))

                    cleanup_commands.append(
                        f"DELETE FROM `tab{entity_type}` WHERE {name_field} = '{entity_name}';"
                    )
                cleanup_commands.append("")

        return '\n'.join(cleanup_commands)

    def _get_name_field_for_entity(self, entity_type: str) -> str:
        """Get the name field for an entity type.

        Args:
            entity_type: Type of entity

        Returns:
            Name field for the entity
        """
        name_fields = {
            'Customer': 'customer_name',
            'Item': 'item_code',
            'Sales Order': 'name',
            'Purchase Order': 'name',
            'Supplier': 'supplier_name',
            'Employee': 'employee',
            'Warehouse': 'name',
            'Journal Entry': 'name',
        }

        return name_fields.get(entity_type, 'name')

    def validate_test_data(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated test data for consistency.

        Args:
            test_data: Test data to validate

        Returns:
            Validation results
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
        }

        entities = test_data.get('entities', {})

        # Check for required fields in each entity
        for entity_type, entity_list in entities.items():
            for i, entity in enumerate(entity_list):
                required_fields = self._get_required_fields_for_entity(entity_type)

                for field in required_fields:
                    if field not in entity or entity[field] is None:
                        validation_result['errors'].append(
                            f"{entity_type}[{i}]: Missing required field '{field}'"
                        )
                        validation_result['is_valid'] = False

        # Check relationships
        relationships = test_data.get('relationships', [])
        for rel in relationships:
            from_entity = rel.get('from_entity')
            to_entity = rel.get('to_entity')

            if from_entity not in entities or to_entity not in entities:
                validation_result['warnings'].append(
                    f"Relationship references non-existent entity: {from_entity} -> {to_entity}"
                )

        return validation_result

    def _get_required_fields_for_entity(self, entity_type: str) -> List[str]:
        """Get required fields for an entity type.

        Args:
            entity_type: Type of entity

        Returns:
            List of required fields
        """
        required_fields = {
            'Customer': ['customer_name', 'customer_type'],
            'Item': ['item_code', 'item_name'],
            'Sales Order': ['customer', 'transaction_date'],
            'Purchase Order': ['supplier', 'transaction_date'],
            'Supplier': ['supplier_name'],
            'Employee': ['employee_name', 'first_name', 'last_name'],
            'Warehouse': ['warehouse_name'],
            'Journal Entry': ['posting_date', 'company'],
        }

        return required_fields.get(entity_type, ['name'])