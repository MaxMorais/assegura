# Quickstart Guide: ERPNext Test Automation Meta-Framework

**Feature**: ERPNext Test Automation Meta-Framework  
**Date**: 2025-10-15  
**Purpose**: Getting started guide for consultants using the test automation system

## Overview

This guide walks ERPNext consultants through creating their first automated test using the meta-framework's Persona → Activity → Journey → Test Generation workflow.

## Prerequisites

- Active ERPNext instance with API access
- ERPNext API key and secret
- Basic understanding of ERPNext business processes
- Access to the Assegura test automation platform

## Quick Start Workflow

### Step 1: Configure ERPNext Instance Connection

1. **Navigate to ERPNext Instances**
   - Go to "Configuration" → "ERPNext Instances" 
   - Click "Add New Instance"

2. **Enter Connection Details**
   ```
   Name: "My ERPNext Production"
   URL: "https://your-erpnext-site.com"
   API Key: [Your ERPNext API Key]
   API Secret: [Your ERPNext API Secret]
   ```

3. **Test Connection**
   - Click "Test Connection" to verify setup
   - Save configuration when successful

### Step 2: Create Your First Persona

1. **Navigate to Personas**
   - Go to "Test Design" → "Personas"
   - Click "Create New Persona"

2. **Define Persona Details**
   ```
   Name: "Sales Manager"
   Description: "Regional sales manager with full sales module access"
   ERPNext Roles: 
     - Sales Manager
     - Sales User
     - Item Manager
   User Permissions:
     - Company: All Companies
     - Territory: North Region
   ```

3. **Save Persona**
   - Review role assignments
   - Click "Create Persona"

### Step 3: Define Business Activity

1. **Navigate to Activities**
   - Select your "Sales Manager" persona
   - Click "Add Activity"

2. **Create Sales Order Activity**
   ```
   Name: "Create Customer Sales Order"
   Description: "Process a new sales order from customer inquiry to order confirmation"
   ERPNext Module: "Sales"
   Business Context: "Standard B2B sales process with credit check and inventory validation"
   ```

3. **Save Activity**
   - Ensure description captures business value
   - Link to appropriate ERPNext module

### Step 4: Build Test Journey

1. **Navigate to Journeys**
   - Select your "Create Customer Sales Order" activity
   - Click "Build Journey"

2. **Add Journey Steps Using Action Library**

   **Given Steps (Test Setup)**
   ```
   1. Action: "Customer Exists in System"
      Parameters:
        - customer_name: "Test Customer Corp"
        - customer_group: "Commercial"
        - territory: "North Region"
   
   2. Action: "Items Available in Stock"
      Parameters:
        - item_code: "ITEM-001"
        - quantity: 100
        - warehouse: "Main Store"
   ```

   **When Steps (User Actions)**
   ```
   3. Action: "Create New Sales Order"
      Parameters:
        - customer: "Test Customer Corp"
        - delivery_date: "+7 days"
   
   4. Action: "Add Order Items"
      Parameters:
        - item_code: "ITEM-001"
        - quantity: 10
        - rate: 150.00
   
   5. Action: "Submit Sales Order"
      Parameters:
        - validate_stock: true
        - check_credit_limit: true
   ```

   **Then Steps (Validations)**
   ```
   6. Action: "Sales Order Status Is"
      Parameters:
        - expected_status: "To Deliver and Bill"
   
   7. Action: "Stock Reserved For Order"
      Parameters:
        - item_code: "ITEM-001"
        - quantity: 10
   ```

3. **Set Expected Outcome**
   ```
   Expected Outcome: "Sales order created successfully with status 'To Deliver and Bill' and stock reserved for ordered items"
   ```

4. **Save Journey**
   - Review step sequence for logical flow
   - Ensure all parameters are configured

### Step 5: Generate and Execute Tests

1. **Generate Robot Framework Tests**
   - Select your completed journey
   - Click "Generate Tests"
   - Wait for generation completion (~60 seconds)

2. **Review Generated Test Suite**
   - Examine generated Robot Framework code
   - Verify test data requirements
   - Check action parameter mapping

3. **Execute Tests in Cloud**
   - Select target ERPNext instance
   - Click "Execute Tests"
   - Monitor real-time execution progress

4. **Review Results**
   - View pass/fail status for each step
   - Analyze execution log for failures
   - Check test data cleanup status

## Sample Test Execution Flow

```
Test: Create Customer Sales Order
├── GIVEN Customer Exists in System ✓
├── GIVEN Items Available in Stock ✓
├── WHEN Create New Sales Order ✓
├── WHEN Add Order Items ✓
├── WHEN Submit Sales Order ✓
├── THEN Sales Order Status Is ✓
└── THEN Stock Reserved For Order ✓

Result: PASSED (7/7 steps)
Duration: 45 seconds
Data Cleanup: Completed
```

## Integration Test Scenarios

### Scenario 1: End-to-End Sales Process
**Journey Flow**: Customer → Quotation → Sales Order → Delivery Note → Sales Invoice
**Validation Points**: Document status transitions, stock movements, accounting entries

### Scenario 2: Purchase Procurement Cycle
**Journey Flow**: Material Request → Purchase Order → Purchase Receipt → Purchase Invoice
**Validation Points**: Approval workflows, supplier selection, cost accounting

### Scenario 3: Manufacturing Work Order
**Journey Flow**: Sales Order → Production Plan → Work Order → Material Consumption → Finished Goods
**Validation Points**: BOM validation, capacity planning, inventory updates

## Action Library Categories

### Given Actions (Test Setup)
- **Data Creation**: Create customers, items, suppliers, warehouses
- **System State**: Set user permissions, configure modules, initialize data
- **Preconditions**: Ensure required master data exists

### When Actions (User Interactions)
- **Document Creation**: Create orders, invoices, receipts, requests
- **Workflow Actions**: Submit, approve, cancel, amend documents
- **Data Entry**: Fill forms, update fields, attach files

### Then Actions (Validations)
- **Status Checks**: Verify document status, workflow state
- **Data Validation**: Confirm calculations, field values, relationships
- **System State**: Check stock levels, account balances, notifications

## Best Practices

### Journey Design
- **Keep journeys focused**: One business process per journey
- **Use realistic test data**: Mirror production scenarios
- **Include error cases**: Test validation and error handling
- **Validate end state**: Confirm expected business outcome

### Test Data Management
- **Use parameterized data**: Enable test reuse across contexts
- **Separate test environments**: Avoid production data contamination
- **Clean data lifecycle**: Ensure proper cleanup after execution
- **Version test datasets**: Track data changes over time

### Performance Optimization
- **Batch related tests**: Group similar scenarios for efficiency
- **Parallel execution**: Run independent journeys simultaneously
- **Resource management**: Monitor cloud execution usage
- **Result caching**: Reuse validation data where appropriate

## Troubleshooting Common Issues

### Connection Problems
- **API Authentication Failed**: Verify API key/secret in ERPNext
- **Network Timeout**: Check ERPNext instance accessibility
- **Permission Denied**: Ensure API user has required roles

### Test Generation Issues
- **Invalid Action Parameters**: Review parameter schema requirements
- **Missing Dependencies**: Ensure all referenced actions are available
- **Generation Timeout**: Simplify complex journeys, reduce step count

### Execution Failures
- **Data Setup Failed**: Check ERPNext master data requirements
- **Validation Failed**: Review expected vs actual outcomes
- **Resource Cleanup**: Investigate test data cleanup processes

## Next Steps

1. **Explore Advanced Features**
   - Custom action development
   - Multi-instance testing
   - Performance benchmarking

2. **Scale Your Testing**
   - Create persona libraries for your team
   - Build reusable activity templates
   - Establish testing standards and practices

3. **Integration & CI/CD**
   - Schedule automated test runs
   - Integrate with deployment pipelines
   - Set up notification and reporting

For detailed documentation and advanced features, refer to the complete user guide and API documentation.