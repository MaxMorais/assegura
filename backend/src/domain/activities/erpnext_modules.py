"""ERPNext modules and related functionality for activities.

This module defines ERPNext modules, doctypes, and validation logic
for activity creation and management.
"""

from enum import Enum


class ERPNextModule(Enum):
    """Core ERPNext modules."""

    ACCOUNTS = "Accounts"
    SELLING = "Selling"
    BUYING = "Buying"
    STOCK = "Stock"
    MANUFACTURING = "Manufacturing"
    CRM = "CRM"
    SUPPORT = "Support"
    PROJECTS = "Projects"
    HR = "HR"
    PAYROLL = "Payroll"
    ASSETS = "Assets"
    QUALITY = "Quality Management"
    AGRICULTURE = "Agriculture"
    EDUCATION = "Education"
    HEALTHCARE = "Healthcare"
    NON_PROFIT = "Non Profit"
    HOSPITALITY = "Hospitality"
    RESTAURANT = "Restaurant"
    RETAIL = "Retail"
    SETUP = "Setup"
    CUSTOM = "Custom"
    INTEGRATIONS = "Integrations"
    WEBSITE = "Website"
    PORTAL = "Portal"
    DESK = "Desk"
    PRINTING = "Printing"
    EMAIL = "Email"
    SMS = "SMS"
    SOCIAL = "Social"
    GEOLOCATION = "Geolocation"
    UTILITIES = "Utilities"
    CORE = "Core"
    CONTACTS = "Contacts"
    COMMUNICATION = "Communication"
    WORKFLOW = "Workflow"

    # Sales-specific (alias for Selling)
    SALES = "Sales"


class ERPNextModuleValidator:
    """Validator for ERPNext modules and related functionality."""

    # Core doctypes by module
    MODULE_DOCTYPES = {
        ERPNextModule.ACCOUNTS.value: [
            "Account",
            "Journal Entry",
            "Payment Entry",
            "Sales Invoice",
            "Purchase Invoice",
            "Payment Request",
            "Payment Terms",
            "Payment Term",
            "Accounting Dimension",
            "Cost Center",
            "Budget",
            "Fiscal Year",
            "Period Closing Voucher",
            "Bank",
            "Bank Account",
            "Currency",
            "Exchange Rate Revaluation",
            "Loyalty Program",
            "Pricing Rule",
        ],
        ERPNextModule.SELLING.value: [
            "Customer",
            "Sales Order",
            "Quotation",
            "Sales Invoice",
            "Delivery Note",
            "Sales Partner",
            "Customer Group",
            "Territory",
            "Sales Person",
            "Campaign",
            "Lead",
            "Opportunity",
            "Installation Note",
            "Product Bundle",
            "Blanket Order",
            "Contract",
        ],
        ERPNextModule.SALES.value: [  # Alias for Selling
            "Customer",
            "Sales Order",
            "Quotation",
            "Sales Invoice",
            "Delivery Note",
            "Sales Partner",
            "Customer Group",
            "Territory",
            "Sales Person",
            "Campaign",
            "Lead",
            "Opportunity",
            "Installation Note",
            "Product Bundle",
            "Blanket Order",
            "Contract",
        ],
        ERPNextModule.BUYING.value: [
            "Supplier",
            "Purchase Order",
            "Request for Quotation",
            "Supplier Quotation",
            "Purchase Invoice",
            "Purchase Receipt",
            "Material Request",
            "Supplier Group",
            "Purchase Taxes and Charges Template",
            "Blanket Order",
        ],
        ERPNextModule.STOCK.value: [
            "Item",
            "Item Group",
            "Warehouse",
            "Stock Entry",
            "Stock Reconciliation",
            "Delivery Note",
            "Purchase Receipt",
            "Material Request",
            "Item Price",
            "Price List",
            "UOM",
            "Brand",
            "Batch",
            "Serial No",
            "Quality Inspection",
            "Packing Slip",
            "Installation Note",
            "Landed Cost Voucher",
        ],
        ERPNextModule.MANUFACTURING.value: [
            "BOM",
            "Work Order",
            "Production Plan",
            "Job Card",
            "Routing",
            "Operation",
            "Workstation",
            "Item Alternative",
            "Sub Assembly Item",
        ],
        ERPNextModule.CRM.value: [
            "Lead",
            "Customer",
            "Opportunity",
            "Campaign",
            "Newsletter",
            "Email Group",
            "Contact",
            "Address",
            "Communication",
            "Phone Call",
            "Appointment",
            "Contract",
        ],
        ERPNextModule.SUPPORT.value: [
            "Issue",
            "Warranty Claim",
            "Maintenance Schedule",
            "Maintenance Visit",
        ],
        ERPNextModule.PROJECTS.value: [
            "Project",
            "Task",
            "Timesheet",
            "Project Template",
            "Project Type",
            "Activity Type",
            "Activity Cost",
        ],
        ERPNextModule.HR.value: [
            "Employee",
            "Employee Group",
            "Designation",
            "Department",
            "Branch",
            "Holiday List",
            "Leave Type",
            "Leave Application",
            "Leave Allocation",
            "Attendance",
            "Employee Checkin",
            "Shift Type",
            "Shift Request",
            "Shift Assignment",
            "Employee Onboarding",
            "Employee Separation",
            "Employee Transfer",
            "Employee Promotion",
            "Employee Skill Map",
            "Training Program",
            "Training Event",
            "Training Result",
            "Training Feedback",
            "Appraisal",
            "Employee Grade",
            "Employment Type",
            "Health Insurance",
            "Employee Advance",
            "Expense Claim",
            "Travel Request",
        ],
        ERPNextModule.PAYROLL.value: [
            "Salary Structure",
            "Salary Slip",
            "Payroll Entry",
            "Salary Component",
            "Additional Salary",
            "Retention Bonus",
            "Income Tax Slab",
            "Employee Tax Exemption Declaration",
            "Employee Tax Exemption Proof Submission",
            "Employee Benefit Application",
            "Employee Benefit Claim",
            "Payroll Period",
        ],
        ERPNextModule.ASSETS.value: [
            "Asset",
            "Asset Category",
            "Asset Movement",
            "Asset Maintenance",
            "Asset Repair",
            "Asset Value Adjustment",
            "Asset Depreciation Schedule",
            "Location",
        ],
        ERPNextModule.QUALITY.value: [
            "Quality Inspection",
            "Quality Inspection Template",
            "Quality Goal",
            "Quality Procedure",
            "Quality Meeting",
            "Quality Review",
            "Quality Feedback",
        ],
        ERPNextModule.WEBSITE.value: [
            "Website Settings",
            "Web Page",
            "Web Form",
            "Blog Post",
            "Blog Category",
            "Blogger",
            "Website Slideshow",
            "Website Script",
            "Website Theme",
        ],
        ERPNextModule.SETUP.value: [
            "Company",
            "Global Defaults",
            "System Settings",
            "Print Settings",
            "Email Account",
            "Email Domain",
            "Letter Head",
            "Address Template",
            "Terms and Conditions",
            "Quotation Lost Reason",
            "Sales Stage",
            "Opportunity Type",
            "Fiscal Year",
            "Currency",
            "Customer Group",
            "Territory",
            "Sales Person",
            "Item Group",
            "UOM",
            "Brand",
        ],
        ERPNextModule.CONTACTS.value: [
            "Contact",
            "Address",
            "Contact Phone",
            "Contact Email",
        ],
        ERPNextModule.COMMUNICATION.value: [
            "Communication",
            "Email Queue",
            "Email Template",
            "Newsletter",
            "Notification",
            "SMS Settings",
            "SMS Log",
        ],
    }

    @classmethod
    def get_all_modules(cls) -> list[str]:
        """Get all valid ERPNext module names."""
        return [module.value for module in ERPNextModule]

    @classmethod
    def is_valid_module(cls, module: str) -> bool:
        """Check if a module name is valid."""
        valid_modules = cls.get_all_modules()
        return module in valid_modules

    @classmethod
    def get_module_doctypes(cls, module: str) -> list[str]:
        """Get all doctypes for a specific module."""
        return cls.MODULE_DOCTYPES.get(module, [])

    @classmethod
    def is_valid_doctype_for_module(cls, module: str, doctype: str) -> bool:
        """Check if a doctype is valid for a specific module."""
        module_doctypes = cls.get_module_doctypes(module)
        return doctype in module_doctypes

    @classmethod
    def get_all_doctypes(cls) -> list[str]:
        """Get all doctypes across all modules."""
        all_doctypes = set()
        for doctypes in cls.MODULE_DOCTYPES.values():
            all_doctypes.update(doctypes)
        return sorted(list(all_doctypes))

    @classmethod
    def find_modules_for_doctype(cls, doctype: str) -> list[str]:
        """Find which modules contain a specific doctype."""
        modules = []
        for module, doctypes in cls.MODULE_DOCTYPES.items():
            if doctype in doctypes:
                modules.append(module)
        return modules

    @classmethod
    def get_core_modules(cls) -> list[str]:
        """Get core ERPNext modules (non-domain specific)."""
        core_modules = [
            ERPNextModule.ACCOUNTS.value,
            ERPNextModule.SELLING.value,
            ERPNextModule.BUYING.value,
            ERPNextModule.STOCK.value,
            ERPNextModule.CRM.value,
            ERPNextModule.HR.value,
            ERPNextModule.PROJECTS.value,
            ERPNextModule.SETUP.value,
        ]
        return core_modules

    @classmethod
    def get_domain_modules(cls) -> list[str]:
        """Get domain-specific ERPNext modules."""
        domain_modules = [
            ERPNextModule.MANUFACTURING.value,
            ERPNextModule.AGRICULTURE.value,
            ERPNextModule.EDUCATION.value,
            ERPNextModule.HEALTHCARE.value,
            ERPNextModule.NON_PROFIT.value,
            ERPNextModule.HOSPITALITY.value,
            ERPNextModule.RESTAURANT.value,
            ERPNextModule.RETAIL.value,
        ]
        return domain_modules

    @classmethod
    def get_technical_modules(cls) -> list[str]:
        """Get technical/system ERPNext modules."""
        technical_modules = [
            ERPNextModule.INTEGRATIONS.value,
            ERPNextModule.WEBSITE.value,
            ERPNextModule.PORTAL.value,
            ERPNextModule.DESK.value,
            ERPNextModule.PRINTING.value,
            ERPNextModule.EMAIL.value,
            ERPNextModule.SMS.value,
            ERPNextModule.UTILITIES.value,
            ERPNextModule.CORE.value,
        ]
        return technical_modules

    @classmethod
    def get_modules_by_category(cls, category: str) -> list[str]:
        """Get modules by category (core, domain, technical)."""
        if category.lower() == "core":
            return cls.get_core_modules()
        elif category.lower() == "domain":
            return cls.get_domain_modules()
        elif category.lower() == "technical":
            return cls.get_technical_modules()
        else:
            return []

    @classmethod
    def suggest_modules_for_activity(
        cls, activity_description: str, action_type: str
    ) -> list[dict[str, any]]:
        """Suggest appropriate modules based on activity description and action type."""
        suggestions = []
        description_lower = activity_description.lower()

        # Keywords to module mapping
        module_keywords = {
            ERPNextModule.SELLING.value: [
                "sales",
                "customer",
                "quotation",
                "order",
                "invoice",
                "delivery",
                "opportunity",
                "lead",
                "campaign",
                "territory",
            ],
            ERPNextModule.BUYING.value: [
                "purchase",
                "supplier",
                "procurement",
                "buying",
                "quotation",
                "material request",
                "receipt",
            ],
            ERPNextModule.STOCK.value: [
                "inventory",
                "warehouse",
                "item",
                "stock",
                "material",
                "batch",
                "serial",
                "quality inspection",
            ],
            ERPNextModule.ACCOUNTS.value: [
                "accounting",
                "finance",
                "payment",
                "journal",
                "budget",
                "cost center",
                "fiscal year",
                "chart of accounts",
            ],
            ERPNextModule.HR.value: [
                "employee",
                "hr",
                "human resource",
                "payroll",
                "attendance",
                "leave",
                "appraisal",
                "recruitment",
            ],
            ERPNextModule.CRM.value: [
                "customer relationship",
                "contact",
                "communication",
                "newsletter",
                "email group",
                "phone call",
            ],
            ERPNextModule.PROJECTS.value: [
                "project",
                "task",
                "timesheet",
                "milestone",
                "gantt",
            ],
            ERPNextModule.MANUFACTURING.value: [
                "production",
                "manufacturing",
                "bom",
                "work order",
                "routing",
                "workstation",
                "job card",
            ],
        }

        # Score modules based on keyword matches
        for module, keywords in module_keywords.items():
            score = 0
            matched_keywords = []

            for keyword in keywords:
                if keyword in description_lower:
                    score += 1
                    matched_keywords.append(keyword)

            if score > 0:
                suggestions.append(
                    {
                        "module": module,
                        "score": score,
                        "confidence": min(1.0, score / 3),  # Normalize to 0-1
                        "matched_keywords": matched_keywords,
                        "doctypes": cls.get_module_doctypes(module),
                    }
                )

        # Sort by score (highest first)
        suggestions.sort(key=lambda x: x["score"], reverse=True)

        return suggestions

    @classmethod
    def validate_activity_module_compatibility(
        cls, module: str, doctype: str, action_type: str
    ) -> dict[str, any]:
        """Validate if module, doctype, and action type are compatible."""
        result = {"is_valid": True, "errors": [], "warnings": [], "suggestions": []}

        # Check if module is valid
        if not cls.is_valid_module(module):
            result["is_valid"] = False
            result["errors"].append(f"Invalid module: {module}")
            result["suggestions"].extend(cls.get_all_modules()[:5])  # Top 5 suggestions

        # Check if doctype is valid for the module
        elif not cls.is_valid_doctype_for_module(module, doctype):
            result["warnings"].append(
                f"DocType '{doctype}' is not typically associated with module '{module}'"
            )
            # Find modules where this doctype exists
            correct_modules = cls.find_modules_for_doctype(doctype)
            if correct_modules:
                result["suggestions"].extend(correct_modules)

        # Action type specific validations
        readonly_actions = ["read", "search", "report", "export", "print"]
        write_actions = [
            "create",
            "update",
            "delete",
            "import",
            "approve",
            "cancel",
            "submit",
        ]

        if action_type in readonly_actions:
            result["warnings"].append(
                f"Action '{action_type}' is read-only and may not require extensive validation"
            )
        elif action_type in write_actions:
            if module in [ERPNextModule.SETUP.value, ERPNextModule.CORE.value]:
                result["warnings"].append(
                    f"Write operations on {module} module require admin privileges"
                )

        return result


class ERPNextDocTypeHelper:
    """Helper class for ERPNext DocType operations and metadata."""

    # Common field patterns by doctype
    DOCTYPE_COMMON_FIELDS = {
        "Sales Order": [
            "customer",
            "delivery_date",
            "items",
            "taxes_and_charges",
            "grand_total",
            "currency",
            "selling_price_list",
        ],
        "Purchase Order": [
            "supplier",
            "schedule_date",
            "items",
            "taxes_and_charges",
            "grand_total",
            "currency",
            "buying_price_list",
        ],
        "Customer": [
            "customer_name",
            "customer_type",
            "customer_group",
            "territory",
            "default_currency",
        ],
        "Supplier": [
            "supplier_name",
            "supplier_type",
            "supplier_group",
            "default_currency",
            "country",
        ],
        "Item": [
            "item_name",
            "item_group",
            "stock_uom",
            "is_stock_item",
            "valuation_rate",
            "standard_rate",
        ],
        "Employee": [
            "employee_name",
            "first_name",
            "last_name",
            "designation",
            "department",
            "date_of_joining",
            "status",
        ],
    }

    @classmethod
    def get_required_fields(cls, doctype: str) -> list[str]:
        """Get commonly required fields for a doctype."""
        return cls.DOCTYPE_COMMON_FIELDS.get(doctype, [])

    @classmethod
    def suggest_validation_rules(cls, doctype: str, field: str) -> dict[str, any]:
        """Suggest validation rules for specific doctype fields."""
        suggestions = {}

        # Common validation patterns
        if field in ["email", "email_id"]:
            suggestions["regex"] = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        elif field in ["phone", "mobile_no", "phone_no"]:
            suggestions["regex"] = r"^\+?[\d\s\-\(\)]{7,15}$"
        elif field in ["customer_name", "supplier_name", "employee_name", "item_name"]:
            suggestions["required"] = True
            suggestions["min_length"] = 2
            suggestions["max_length"] = 140
        elif field.endswith("_date") or field in [
            "date",
            "posting_date",
            "transaction_date",
        ]:
            suggestions["required"] = True
        elif field.endswith("_amount") or field.endswith("_total") or field == "amount":
            suggestions["min_value"] = 0
        elif field == "currency":
            suggestions["enum"] = ["USD", "EUR", "INR", "GBP", "JPY", "AUD", "CAD"]

        return suggestions
