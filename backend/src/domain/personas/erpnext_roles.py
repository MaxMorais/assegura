"""ERPNext roles value objects and validation.

Defines valid ERPNext roles and provides validation functionality
for persona role assignments in the ERPNext Test Automation Meta-Framework.
"""

from enum import Enum
from typing import List, Set, Dict
from .exceptions import PersonaValidationError


class ERPNextRole(Enum):
    """Enumeration of valid ERPNext roles.
    
    Based on standard ERPNext system roles used in typical installations.
    """
    
    # System Administration
    ADMINISTRATOR = "Administrator"
    SYSTEM_MANAGER = "System Manager"
    
    # Sales Module
    SALES_MANAGER = "Sales Manager"
    SALES_USER = "Sales User" 
    SALES_MASTER_MANAGER = "Sales Master Manager"
    
    # Purchase Module
    PURCHASE_MANAGER = "Purchase Manager"
    PURCHASE_USER = "Purchase User"
    PURCHASE_MASTER_MANAGER = "Purchase Master Manager"
    
    # Stock/Inventory Module
    STOCK_MANAGER = "Stock Manager"
    STOCK_USER = "Stock User"
    
    # Accounts Module
    ACCOUNTS_MANAGER = "Accounts Manager"
    ACCOUNTS_USER = "Accounts User"
    
    # HR Module
    HR_MANAGER = "HR Manager"
    HR_USER = "HR User"
    EMPLOYEE = "Employee"
    
    # Projects Module
    PROJECTS_MANAGER = "Projects Manager"
    PROJECTS_USER = "Projects User"
    
    # Manufacturing Module
    MANUFACTURING_MANAGER = "Manufacturing Manager"
    MANUFACTURING_USER = "Manufacturing User"
    
    # Quality Module
    QUALITY_MANAGER = "Quality Manager"
    
    # Website Module
    WEBSITE_MANAGER = "Website Manager"
    WEBSITE_USER = "Website User"
    
    # Customer and Supplier Roles
    CUSTOMER = "Customer"
    SUPPLIER = "Supplier"
    
    # Analytics and Reporting
    ANALYTICS_USER = "Analytics User"
    
    # Maintenance
    MAINTENANCE_MANAGER = "Maintenance Manager"
    MAINTENANCE_USER = "Maintenance User"
    
    # Agriculture (if enabled)
    AGRICULTURE_MANAGER = "Agriculture Manager"
    AGRICULTURE_USER = "Agriculture User"
    
    # Healthcare (if enabled)
    HEALTHCARE_ADMINISTRATOR = "Healthcare Administrator"
    LABORATORY_USER = "Laboratory User"
    NURSING_USER = "Nursing User"
    PHYSICIAN = "Physician"
    
    # Education (if enabled) 
    EDUCATION_MANAGER = "Education Manager"
    INSTRUCTOR = "Instructor"
    STUDENT = "Student"
    
    # Non Profit (if enabled)
    NON_PROFIT_MANAGER = "Non Profit Manager"
    NON_PROFIT_PORTAL_USER = "Non Profit Portal User"
    
    @classmethod
    def get_all_roles(cls) -> List[str]:
        """Get list of all valid ERPNext role names.
        
        Returns:
            List of all role names
        """
        return [role.value for role in cls]
    
    @classmethod
    def is_valid_role(cls, role_name: str) -> bool:
        """Check if role name is valid.
        
        Args:
            role_name: Role name to validate
            
        Returns:
            True if role is valid
        """
        return role_name in cls.get_all_roles()
    
    @classmethod
    def get_module_roles(cls, module: str) -> List[str]:
        """Get roles for specific ERPNext module.
        
        Args:
            module: Module name (sales, purchase, stock, etc.)
            
        Returns:
            List of role names for the module
        """
        module = module.lower()
        module_roles = {
            'sales': [cls.SALES_MANAGER.value, cls.SALES_USER.value, cls.SALES_MASTER_MANAGER.value],
            'purchase': [cls.PURCHASE_MANAGER.value, cls.PURCHASE_USER.value, cls.PURCHASE_MASTER_MANAGER.value],
            'stock': [cls.STOCK_MANAGER.value, cls.STOCK_USER.value],
            'accounts': [cls.ACCOUNTS_MANAGER.value, cls.ACCOUNTS_USER.value],
            'hr': [cls.HR_MANAGER.value, cls.HR_USER.value, cls.EMPLOYEE.value],
            'projects': [cls.PROJECTS_MANAGER.value, cls.PROJECTS_USER.value],
            'manufacturing': [cls.MANUFACTURING_MANAGER.value, cls.MANUFACTURING_USER.value],
            'quality': [cls.QUALITY_MANAGER.value],
            'website': [cls.WEBSITE_MANAGER.value, cls.WEBSITE_USER.value],
            'maintenance': [cls.MAINTENANCE_MANAGER.value, cls.MAINTENANCE_USER.value],
            'agriculture': [cls.AGRICULTURE_MANAGER.value, cls.AGRICULTURE_USER.value],
            'healthcare': [cls.HEALTHCARE_ADMINISTRATOR.value, cls.LABORATORY_USER.value, 
                          cls.NURSING_USER.value, cls.PHYSICIAN.value],
            'education': [cls.EDUCATION_MANAGER.value, cls.INSTRUCTOR.value, cls.STUDENT.value],
            'nonprofit': [cls.NON_PROFIT_MANAGER.value, cls.NON_PROFIT_PORTAL_USER.value],
            'system': [cls.ADMINISTRATOR.value, cls.SYSTEM_MANAGER.value]
        }
        
        return module_roles.get(module, [])
    
    @classmethod
    def get_role_permissions(cls, role_name: str) -> Set[str]:
        """Get default permissions for a role.
        
        Args:
            role_name: ERPNext role name
            
        Returns:
            Set of permission strings for the role
        """
        # Define role-based permissions
        role_permissions = {
            cls.ADMINISTRATOR.value: {
                'admin:*', 'read:*', 'write:*', 'create:*', 'delete:*'
            },
            cls.SYSTEM_MANAGER.value: {
                'admin:system', 'read:*', 'write:*', 'create:*', 'delete:*'
            },
            cls.SALES_MANAGER.value: {
                'read:sales', 'write:sales', 'create:quotation', 'create:sales_order',
                'create:sales_invoice', 'delete:quotation', 'admin:sales'
            },
            cls.SALES_USER.value: {
                'read:sales', 'write:sales', 'create:quotation', 'create:sales_order',
                'create:sales_invoice'
            },
            cls.PURCHASE_MANAGER.value: {
                'read:purchase', 'write:purchase', 'create:purchase_order',
                'create:supplier_quotation', 'delete:purchase_order', 'admin:purchase'
            },
            cls.PURCHASE_USER.value: {
                'read:purchase', 'write:purchase', 'create:purchase_order',
                'create:supplier_quotation'
            },
            cls.STOCK_MANAGER.value: {
                'read:stock', 'write:stock', 'create:stock_entry', 'create:delivery_note',
                'create:purchase_receipt', 'delete:stock_entry', 'admin:stock'
            },
            cls.STOCK_USER.value: {
                'read:stock', 'write:stock', 'create:stock_entry', 'create:delivery_note',
                'create:purchase_receipt'
            },
            cls.ACCOUNTS_MANAGER.value: {
                'read:accounts', 'write:accounts', 'create:journal_entry', 'create:payment_entry',
                'create:general_ledger', 'delete:journal_entry', 'admin:accounts'
            },
            cls.ACCOUNTS_USER.value: {
                'read:accounts', 'write:accounts', 'create:journal_entry', 'create:payment_entry'
            },
            cls.HR_MANAGER.value: {
                'read:hr', 'write:hr', 'create:employee', 'create:salary_slip',
                'create:leave_application', 'delete:employee', 'admin:hr'
            },
            cls.HR_USER.value: {
                'read:hr', 'write:hr', 'create:leave_application', 'create:expense_claim'
            },
            cls.EMPLOYEE.value: {
                'read:hr', 'create:leave_application', 'create:expense_claim'
            },
            cls.PROJECTS_MANAGER.value: {
                'read:projects', 'write:projects', 'create:project', 'create:task',
                'create:timesheet', 'delete:project', 'admin:projects'
            },
            cls.PROJECTS_USER.value: {
                'read:projects', 'write:projects', 'create:task', 'create:timesheet'
            },
            cls.MANUFACTURING_MANAGER.value: {
                'read:manufacturing', 'write:manufacturing', 'create:work_order',
                'create:job_card', 'delete:work_order', 'admin:manufacturing'
            },
            cls.MANUFACTURING_USER.value: {
                'read:manufacturing', 'write:manufacturing', 'create:work_order', 'create:job_card'
            },
            cls.QUALITY_MANAGER.value: {
                'read:quality', 'write:quality', 'create:quality_inspection',
                'create:quality_goal', 'admin:quality'
            },
            cls.WEBSITE_MANAGER.value: {
                'read:website', 'write:website', 'create:web_page', 'create:blog_post',
                'admin:website'
            },
            cls.WEBSITE_USER.value: {
                'read:website', 'write:website', 'create:web_page', 'create:blog_post'
            },
            cls.CUSTOMER.value: {
                'read:sales', 'read:accounts'
            },
            cls.SUPPLIER.value: {
                'read:purchase', 'read:accounts'
            }
        }
        
        return role_permissions.get(role_name, set())
    
    @classmethod
    def get_hierarchical_roles(cls, role_name: str) -> List[str]:
        """Get role hierarchy (roles that include permissions of this role).
        
        Args:
            role_name: ERPNext role name
            
        Returns:
            List of roles in hierarchy order (most to least privileged)
        """
        hierarchies = {
            cls.SALES_USER.value: [cls.SALES_MANAGER.value, cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value],
            cls.PURCHASE_USER.value: [cls.PURCHASE_MANAGER.value, cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value],
            cls.STOCK_USER.value: [cls.STOCK_MANAGER.value, cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value],
            cls.ACCOUNTS_USER.value: [cls.ACCOUNTS_MANAGER.value, cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value],
            cls.HR_USER.value: [cls.HR_MANAGER.value, cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value],
            cls.EMPLOYEE.value: [cls.HR_USER.value, cls.HR_MANAGER.value, cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value],
            cls.PROJECTS_USER.value: [cls.PROJECTS_MANAGER.value, cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value],
            cls.MANUFACTURING_USER.value: [cls.MANUFACTURING_MANAGER.value, cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value],
            cls.WEBSITE_USER.value: [cls.WEBSITE_MANAGER.value, cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value],
        }
        
        hierarchy = hierarchies.get(role_name, [])
        if cls.SYSTEM_MANAGER.value not in hierarchy and role_name != cls.ADMINISTRATOR.value:
            hierarchy.extend([cls.SYSTEM_MANAGER.value, cls.ADMINISTRATOR.value])
        elif role_name != cls.ADMINISTRATOR.value and cls.ADMINISTRATOR.value not in hierarchy:
            hierarchy.append(cls.ADMINISTRATOR.value)
        
        return hierarchy


def validate_erpnext_roles(roles: List[str]) -> None:
    """Validate list of ERPNext roles.
    
    Args:
        roles: List of role names to validate
        
    Raises:
        PersonaValidationError: If any role is invalid
    """
    if not roles:
        raise PersonaValidationError("At least one ERPNext role is required")
    
    valid_roles = ERPNextRole.get_all_roles()
    
    for role in roles:
        if not role or not role.strip():
            raise PersonaValidationError("Role name cannot be empty")
        
        role = role.strip()
        if role not in valid_roles:
            raise PersonaValidationError(
                f"Invalid ERPNext role: '{role}'. Valid roles are: {', '.join(valid_roles)}"
            )


def get_role_recommendations(module: str, user_level: str = "user") -> List[str]:
    """Get recommended roles for a module and user level.
    
    Args:
        module: ERPNext module name
        user_level: User level (user, manager, admin)
        
    Returns:
        List of recommended role names
    """
    module_roles = ERPNextRole.get_module_roles(module)
    
    if not module_roles:
        return []
    
    if user_level.lower() == "admin":
        return [ERPNextRole.SYSTEM_MANAGER.value] + module_roles
    elif user_level.lower() == "manager":
        # Return manager roles for the module
        manager_roles = [role for role in module_roles if "Manager" in role]
        return manager_roles if manager_roles else module_roles[:1]
    else:
        # Return user roles for the module
        user_roles = [role for role in module_roles if "User" in role or role == ERPNextRole.EMPLOYEE.value]
        return user_roles if user_roles else module_roles[-1:]


def validate_role_combination(roles: List[str]) -> List[str]:
    """Validate and optimize role combination.
    
    Args:
        roles: List of role names
        
    Returns:
        List of validation warnings (empty if no issues)
    """
    warnings = []
    
    if not roles:
        return ["No roles specified"]
    
    # Check for Administrator role with other roles
    if ERPNextRole.ADMINISTRATOR.value in roles and len(roles) > 1:
        warnings.append("Administrator role includes all permissions - other roles are redundant")
    
    # Check for System Manager with module manager roles
    if ERPNextRole.SYSTEM_MANAGER.value in roles:
        manager_roles = [role for role in roles if "Manager" in role and role != ERPNextRole.SYSTEM_MANAGER.value]
        if manager_roles:
            warnings.append(f"System Manager includes permissions from: {', '.join(manager_roles)}")
    
    # Check for manager roles with corresponding user roles
    for role in roles:
        if "Manager" in role:
            corresponding_user = role.replace("Manager", "User")
            if corresponding_user in roles:
                warnings.append(f"{role} includes all permissions from {corresponding_user}")
    
    # Check for conflicting roles (Customer/Supplier with internal roles)
    external_roles = [ERPNextRole.CUSTOMER.value, ERPNextRole.SUPPLIER.value]
    internal_roles = [role for role in roles if role not in external_roles]
    
    if any(role in roles for role in external_roles) and internal_roles:
        warnings.append("External roles (Customer/Supplier) typically should not be combined with internal roles")
    
    return warnings