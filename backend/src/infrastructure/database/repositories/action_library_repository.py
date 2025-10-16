"""
Action Library Repository - Infrastructure Layer

This module implements the ActionLibraryRepository using SQLAlchemy ORM for managing
action library data persistence in the ERPNext test automation framework. It provides
comprehensive CRUD operations, advanced search capabilities, BDD classification
management, and performance-optimized queries.
"""

from typing import List, Optional, Dict, Any, Tuple, Union, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy import and_, or_, desc, asc, func, text, case, literal_column
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.dialects.postgresql import JSONB

from src.infrastructure.database.models.action_library_models import (
    ActionLibraryModel, ActionExecutionMetricsModel, ActionVersionModel, ActionRelationshipModel
)
from src.infrastructure.database.repositories.base import BaseRepository
from src.application.services.action_library_service import ActionLibraryRepositoryInterface
from src.application.dto.action_library_schemas import (
    ActionLibraryFilterSchema, ActionLibrarySortSchema, ActionLibrarySearchSchema
)
from src.domain.actions.enhanced_action_library import (
    EnhancedActionLibrary, ActionType, BDDStepType, ActionCategory,
    ActionExecutionMetrics, ActionValidationResult
)


class ActionLibraryRepositoryError(Exception):
    """Base exception for action library repository operations."""
    pass


class ActionLibraryRepository(BaseRepository, ActionLibraryRepositoryInterface):
    """SQLAlchemy implementation of action library repository."""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.model_class = ActionLibraryModel
    
    async def create(self, action: EnhancedActionLibrary) -> EnhancedActionLibrary:
        """
        Create a new action in the database.
        
        Args:
            action: Enhanced action library domain object
            
        Returns:
            Created action with database ID
            
        Raises:
            ActionLibraryRepositoryError: If creation fails
        """
        try:
            # Convert domain object to database model
            action_model = self._convert_domain_to_model(action)
            
            # Add to session and flush to get ID
            self.db_session.add(action_model)
            self.db_session.flush()
            
            # Create initial execution metrics
            metrics_model = ActionExecutionMetricsModel(
                action_id=action_model.id,
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                average_duration_seconds=0.0,
                last_execution_date=None,
                common_failure_reasons=[]
            )
            self.db_session.add(metrics_model)
            
            # Create initial version
            version_model = ActionVersionModel(
                action_id=action_model.id,
                version_number=1,
                implementation_hash=self._calculate_implementation_hash(action.implementation),
                parameters_schema_hash=self._calculate_schema_hash(action.parameters_schema),
                created_at=datetime.utcnow(),
                change_summary="Initial version"
            )
            self.db_session.add(version_model)
            
            # Commit transaction
            self.db_session.commit()
            
            # Refresh and return converted domain object
            self.db_session.refresh(action_model)
            return await self._convert_model_to_domain(action_model)
            
        except IntegrityError as e:
            self.db_session.rollback()
            if "unique constraint" in str(e).lower():
                raise ActionLibraryRepositoryError(f"Action with name '{action.name}' already exists")
            raise ActionLibraryRepositoryError(f"Action creation failed due to constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise ActionLibraryRepositoryError(f"Database error during action creation: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            raise ActionLibraryRepositoryError(f"Unexpected error during action creation: {str(e)}")
    
    async def get_by_id(self, action_id: UUID) -> Optional[EnhancedActionLibrary]:
        """
        Get action by ID with all related data.
        
        Args:
            action_id: Action UUID
            
        Returns:
            Enhanced action library or None if not found
        """
        try:
            action_model = (
                self.db_session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.execution_metrics),
                    selectinload(ActionLibraryModel.versions),
                    selectinload(ActionLibraryModel.relationships)
                )
                .filter(ActionLibraryModel.id == action_id)
                .first()
            )
            
            if not action_model:
                return None
            
            return await self._convert_model_to_domain(action_model)
            
        except SQLAlchemyError as e:
            raise ActionLibraryRepositoryError(f"Database error retrieving action {action_id}: {str(e)}")
        except Exception as e:
            raise ActionLibraryRepositoryError(f"Unexpected error retrieving action {action_id}: {str(e)}")
    
    async def get_by_name(self, name: str) -> Optional[EnhancedActionLibrary]:
        """
        Get action by name.
        
        Args:
            name: Action name
            
        Returns:
            Enhanced action library or None if not found
        """
        try:
            action_model = (
                self.db_session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.execution_metrics),
                    selectinload(ActionLibraryModel.versions)
                )
                .filter(ActionLibraryModel.name == name)
                .first()
            )
            
            if not action_model:
                return None
            
            return await self._convert_model_to_domain(action_model)
            
        except SQLAlchemyError as e:
            raise ActionLibraryRepositoryError(f"Database error retrieving action '{name}': {str(e)}")
        except Exception as e:
            raise ActionLibraryRepositoryError(f"Unexpected error retrieving action '{name}': {str(e)}")
    
    async def list_actions(
        self,
        filters: Optional[ActionLibraryFilterSchema] = None,
        sort: Optional[ActionLibrarySortSchema] = None,
        offset: int = 0,
        limit: int = 100
    ) -> Tuple[List[EnhancedActionLibrary], int]:
        """
        List actions with filtering, sorting and pagination.
        
        Args:
            filters: Filter criteria
            sort: Sort criteria  
            offset: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of (actions list, total count)
        """
        try:
            # Base query with optimized loading
            query = (
                self.db_session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.execution_metrics),
                    selectinload(ActionLibraryModel.versions)
                )
            )
            
            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply sorting
            if sort:
                query = self._apply_sorting(query, sort)
            else:
                # Default sorting by usage count desc, then name
                query = query.order_by(desc(ActionLibraryModel.usage_count), asc(ActionLibraryModel.name))
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            action_models = query.all()
            
            # Convert to domain objects
            actions = []
            for model in action_models:
                action = await self._convert_model_to_domain(model)
                actions.append(action)
            
            return actions, total_count
            
        except SQLAlchemyError as e:
            raise ActionLibraryRepositoryError(f"Database error listing actions: {str(e)}")
        except Exception as e:
            raise ActionLibraryRepositoryError(f"Unexpected error listing actions: {str(e)}")
    
    async def search_actions(self, search_criteria: ActionLibrarySearchSchema) -> List[EnhancedActionLibrary]:
        """
        Search actions by various criteria with advanced filtering.
        
        Args:
            search_criteria: Search criteria
            
        Returns:
            List of matching actions
        """
        try:
            query = (
                self.db_session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.execution_metrics),
                    selectinload(ActionLibraryModel.versions)
                )
            )
            
            # Text search across name, description, and implementation
            if search_criteria.text_query:
                text_pattern = f"%{search_criteria.text_query}%"
                text_conditions = [
                    ActionLibraryModel.name.ilike(text_pattern),
                    ActionLibraryModel.description.ilike(text_pattern)
                ]
                
                # Search in implementation JSON
                if hasattr(ActionLibraryModel.implementation, 'astext'):
                    text_conditions.append(
                        ActionLibraryModel.implementation.astext.ilike(text_pattern)
                    )
                
                query = query.filter(or_(*text_conditions))
            
            # Category filters
            if search_criteria.categories:
                category_values = [cat.value if hasattr(cat, 'value') else cat for cat in search_criteria.categories]
                query = query.filter(ActionLibraryModel.category.in_(category_values))
            
            # Action type filters
            if search_criteria.action_types:
                type_values = [at.value if hasattr(at, 'value') else at for at in search_criteria.action_types]
                query = query.filter(ActionLibraryModel.action_type.in_(type_values))
            
            # BDD step type filters
            if search_criteria.bdd_step_types:
                bdd_values = [bst.value if hasattr(bst, 'value') else bst for bst in search_criteria.bdd_step_types]
                query = query.filter(ActionLibraryModel.bdd_step_type.in_(bdd_values))
            
            # Tag search
            if search_criteria.tags:
                for tag in search_criteria.tags:
                    query = query.filter(ActionLibraryModel.tags.contains([tag]))
            
            # ERPNext doctype filter
            if search_criteria.erpnext_doctype:
                query = query.filter(ActionLibraryModel.erpnext_doctype == search_criteria.erpnext_doctype)
            
            # Active status filter
            if search_criteria.is_active is not None:
                query = query.filter(ActionLibraryModel.is_active == search_criteria.is_active)
            
            # Usage count range
            if search_criteria.min_usage_count is not None:
                query = query.filter(ActionLibraryModel.usage_count >= search_criteria.min_usage_count)
            
            if search_criteria.max_usage_count is not None:
                query = query.filter(ActionLibraryModel.usage_count <= search_criteria.max_usage_count)
            
            # Date range filters
            if search_criteria.created_after:
                query = query.filter(ActionLibraryModel.created_at >= search_criteria.created_after)
            
            if search_criteria.created_before:
                query = query.filter(ActionLibraryModel.created_at <= search_criteria.created_before)
            
            # Order by relevance (simplified - could implement more sophisticated scoring)
            if search_criteria.text_query:
                # Boost exact matches in name
                relevance_score = case(
                    (ActionLibraryModel.name.ilike(f"%{search_criteria.text_query}%"), 3),
                    (ActionLibraryModel.description.ilike(f"%{search_criteria.text_query}%"), 2),
                    else_=1
                ).label('relevance')
                
                query = query.add_columns(relevance_score).order_by(desc('relevance'), desc(ActionLibraryModel.usage_count))
                results = query.all()
                action_models = [result[0] for result in results]  # Extract model from tuple
            else:
                query = query.order_by(desc(ActionLibraryModel.usage_count), asc(ActionLibraryModel.name))
                action_models = query.all()
            
            # Apply limit if specified
            if hasattr(search_criteria, 'limit') and search_criteria.limit:
                action_models = action_models[:search_criteria.limit]
            
            # Convert to domain objects
            actions = []
            for model in action_models:
                action = await self._convert_model_to_domain(model)
                actions.append(action)
            
            return actions
            
        except SQLAlchemyError as e:
            raise ActionLibraryRepositoryError(f"Database error searching actions: {str(e)}")
        except Exception as e:
            raise ActionLibraryRepositoryError(f"Unexpected error searching actions: {str(e)}")
    
    async def update(self, action: EnhancedActionLibrary) -> EnhancedActionLibrary:
        """
        Update existing action.
        
        Args:
            action: Enhanced action with updates
            
        Returns:
            Updated action
            
        Raises:
            ActionLibraryRepositoryError: If update fails
        """
        try:
            # Get existing action model
            action_model = (
                self.db_session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.execution_metrics),
                    selectinload(ActionLibraryModel.versions)
                )
                .filter(ActionLibraryModel.id == action.action_id)
                .first()
            )
            
            if not action_model:
                raise ActionLibraryRepositoryError(f"Action {action.action_id} not found for update")
            
            # Check if significant changes require versioning
            needs_versioning = self._check_needs_versioning(action_model, action)
            
            # Update action fields
            self._update_model_from_domain(action_model, action)
            
            # Create new version if needed
            if needs_versioning:
                await self._create_new_version(action_model, action)
            
            # Commit changes
            self.db_session.commit()
            
            # Refresh and return
            self.db_session.refresh(action_model)
            return await self._convert_model_to_domain(action_model)
            
        except ActionLibraryRepositoryError:
            self.db_session.rollback()
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise ActionLibraryRepositoryError(f"Database error updating action: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            raise ActionLibraryRepositoryError(f"Unexpected error updating action: {str(e)}")
    
    async def delete(self, action_id: UUID) -> bool:
        """
        Delete action and all related data.
        
        Args:
            action_id: Action UUID
            
        Returns:
            True if deleted successfully
            
        Raises:
            ActionLibraryRepositoryError: If deletion fails
        """
        try:
            # Get action with related data
            action_model = (
                self.db_session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.execution_metrics),
                    selectinload(ActionLibraryModel.versions),
                    selectinload(ActionLibraryModel.relationships)
                )
                .filter(ActionLibraryModel.id == action_id)
                .first()
            )
            
            if not action_model:
                return False
            
            # Delete related data (metrics, versions, relationships will be deleted by cascade)
            self.db_session.delete(action_model)
            self.db_session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise ActionLibraryRepositoryError(f"Database error deleting action: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            raise ActionLibraryRepositoryError(f"Unexpected error deleting action: {str(e)}")
    
    async def get_actions_by_category(self, category: ActionCategory) -> List[EnhancedActionLibrary]:
        """
        Get actions by category.
        
        Args:
            category: Action category
            
        Returns:
            List of actions in the category
        """
        try:
            action_models = (
                self.db_session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.execution_metrics),
                    selectinload(ActionLibraryModel.versions)
                )
                .filter(ActionLibraryModel.category == category.value)
                .order_by(desc(ActionLibraryModel.usage_count), asc(ActionLibraryModel.name))
                .all()
            )
            
            actions = []
            for model in action_models:
                action = await self._convert_model_to_domain(model)
                actions.append(action)
            
            return actions
            
        except SQLAlchemyError as e:
            raise ActionLibraryRepositoryError(f"Database error getting actions by category: {str(e)}")
        except Exception as e:
            raise ActionLibraryRepositoryError(f"Unexpected error getting actions by category: {str(e)}")
    
    async def get_actions_by_bdd_type(self, bdd_type: BDDStepType) -> List[EnhancedActionLibrary]:
        """
        Get actions by BDD step type.
        
        Args:
            bdd_type: BDD step type
            
        Returns:
            List of actions with the BDD type
        """
        try:
            action_models = (
                self.db_session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.execution_metrics),
                    selectinload(ActionLibraryModel.versions)
                )
                .filter(ActionLibraryModel.bdd_step_type == bdd_type.value)
                .order_by(desc(ActionLibraryModel.usage_count), asc(ActionLibraryModel.name))
                .all()
            )
            
            actions = []
            for model in action_models:
                action = await self._convert_model_to_domain(model)
                actions.append(action)
            
            return actions
            
        except SQLAlchemyError as e:
            raise ActionLibraryRepositoryError(f"Database error getting actions by BDD type: {str(e)}")
        except Exception as e:
            raise ActionLibraryRepositoryError(f"Unexpected error getting actions by BDD type: {str(e)}")
    
    async def get_action_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive action library statistics.
        
        Returns:
            Dictionary with action statistics
        """
        try:
            # Basic counts
            total_actions = self.db_session.query(func.count(ActionLibraryModel.id)).scalar()
            active_actions = self.db_session.query(func.count(ActionLibraryModel.id)).filter(
                ActionLibraryModel.is_active == True
            ).scalar()
            
            # Category distribution
            category_stats = (
                self.db_session.query(
                    ActionLibraryModel.category,
                    func.count(ActionLibraryModel.id).label('count')
                )
                .group_by(ActionLibraryModel.category)
                .all()
            )
            
            # BDD step type distribution
            bdd_stats = (
                self.db_session.query(
                    ActionLibraryModel.bdd_step_type,
                    func.count(ActionLibraryModel.id).label('count')
                )
                .group_by(ActionLibraryModel.bdd_step_type)
                .all()
            )
            
            # Action type distribution
            type_stats = (
                self.db_session.query(
                    ActionLibraryModel.action_type,
                    func.count(ActionLibraryModel.id).label('count')
                )
                .group_by(ActionLibraryModel.action_type)
                .all()
            )
            
            # Usage statistics
            usage_stats = (
                self.db_session.query(
                    func.sum(ActionLibraryModel.usage_count).label('total_usage'),
                    func.avg(ActionLibraryModel.usage_count).label('avg_usage'),
                    func.max(ActionLibraryModel.usage_count).label('max_usage')
                )
                .first()
            )
            
            # Most used actions
            most_used = (
                self.db_session.query(ActionLibraryModel.name, ActionLibraryModel.usage_count)
                .filter(ActionLibraryModel.usage_count > 0)
                .order_by(desc(ActionLibraryModel.usage_count))
                .limit(10)
                .all()
            )
            
            # Recent activity
            recent_actions = (
                self.db_session.query(func.count(ActionLibraryModel.id))
                .filter(ActionLibraryModel.created_at >= func.now() - text("INTERVAL '7 days'"))
                .scalar()
            )
            
            # ERPNext doctype distribution
            doctype_stats = (
                self.db_session.query(
                    ActionLibraryModel.erpnext_doctype,
                    func.count(ActionLibraryModel.id).label('count')
                )
                .filter(ActionLibraryModel.erpnext_doctype.isnot(None))
                .group_by(ActionLibraryModel.erpnext_doctype)
                .order_by(desc('count'))
                .all()
            )
            
            return {
                "total_actions": total_actions,
                "active_actions": active_actions,
                "inactive_actions": total_actions - active_actions,
                "recent_actions_7_days": recent_actions,
                "category_distribution": {category: count for category, count in category_stats},
                "bdd_step_type_distribution": {bdd_type: count for bdd_type, count in bdd_stats},
                "action_type_distribution": {action_type: count for action_type, count in type_stats},
                "usage_statistics": {
                    "total_usage": int(usage_stats.total_usage or 0),
                    "average_usage": float(usage_stats.avg_usage or 0),
                    "max_usage": int(usage_stats.max_usage or 0)
                },
                "most_used_actions": [{"name": name, "usage_count": count} for name, count in most_used],
                "erpnext_doctype_distribution": {doctype: count for doctype, count in doctype_stats},
                "quality_metrics": {
                    "actions_with_parameters": 0,  # Would calculate from parameters_schema
                    "actions_with_implementations": 0,  # Would calculate from implementation field
                    "bdd_compliant_actions": 0  # Would calculate based on BDD compliance
                }
            }
            
        except SQLAlchemyError as e:
            raise ActionLibraryRepositoryError(f"Database error getting action stats: {str(e)}")
        except Exception as e:
            raise ActionLibraryRepositoryError(f"Unexpected error getting action stats: {str(e)}")
    
    async def bulk_update_status(self, action_ids: List[UUID], is_active: bool) -> Dict[UUID, bool]:
        """
        Bulk update action status.
        
        Args:
            action_ids: List of action UUIDs
            is_active: New active status
            
        Returns:
            Dictionary mapping action ID to success status
        """
        results = {}
        
        try:
            for action_id in action_ids:
                try:
                    updated_count = (
                        self.db_session.query(ActionLibraryModel)
                        .filter(ActionLibraryModel.id == action_id)
                        .update({
                            "is_active": is_active,
                            "updated_at": datetime.utcnow()
                        })
                    )
                    results[action_id] = updated_count > 0
                    
                except Exception:
                    results[action_id] = False
            
            self.db_session.commit()
            return results
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise ActionLibraryRepositoryError(f"Database error in bulk status update: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            raise ActionLibraryRepositoryError(f"Unexpected error in bulk status update: {str(e)}")
    
    async def get_duplicate_candidates(self, action: EnhancedActionLibrary) -> List[EnhancedActionLibrary]:
        """
        Find potential duplicate actions based on similarity.
        
        Args:
            action: Action to check for duplicates
            
        Returns:
            List of potential duplicate actions
        """
        try:
            # Find actions with similar names
            name_pattern = f"%{action.name.lower()}%"
            
            candidates = (
                self.db_session.query(ActionLibraryModel)
                .filter(
                    and_(
                        ActionLibraryModel.id != action.action_id,  # Exclude self if updating
                        or_(
                            ActionLibraryModel.name.ilike(name_pattern),
                            ActionLibraryModel.name.ilike(f"%{action.name.split()[0].lower()}%")  # First word match
                        )
                    )
                )
                .all()
            )
            
            # Filter by additional similarity criteria
            potential_duplicates = []
            for candidate in candidates:
                # Check category and type similarity
                if (candidate.category == action.category.value and 
                    candidate.bdd_step_type == action.bdd_step_type.value):
                    potential_duplicates.append(candidate)
                # Check ERPNext doctype similarity
                elif (candidate.erpnext_doctype and action.erpnext_doctype and
                      candidate.erpnext_doctype == action.erpnext_doctype):
                    potential_duplicates.append(candidate)
            
            # Convert to domain objects
            duplicates = []
            for model in potential_duplicates[:10]:  # Limit to top 10 candidates
                duplicate = await self._convert_model_to_domain(model)
                duplicates.append(duplicate)
            
            return duplicates
            
        except SQLAlchemyError as e:
            raise ActionLibraryRepositoryError(f"Database error finding duplicates: {str(e)}")
        except Exception as e:
            raise ActionLibraryRepositoryError(f"Unexpected error finding duplicates: {str(e)}")
    
    # Private helper methods
    
    def _apply_filters(self, query, filters: ActionLibraryFilterSchema):
        """Apply filters to the query."""
        
        if filters.categories:
            category_values = [cat.value if hasattr(cat, 'value') else cat for cat in filters.categories]
            query = query.filter(ActionLibraryModel.category.in_(category_values))
        
        if filters.action_types:
            type_values = [at.value if hasattr(at, 'value') else at for at in filters.action_types]
            query = query.filter(ActionLibraryModel.action_type.in_(type_values))
        
        if filters.bdd_step_types:
            bdd_values = [bst.value if hasattr(bst, 'value') else bst for bst in filters.bdd_step_types]
            query = query.filter(ActionLibraryModel.bdd_step_type.in_(bdd_values))
        
        if filters.is_active is not None:
            query = query.filter(ActionLibraryModel.is_active == filters.is_active)
        
        if filters.tags:
            for tag in filters.tags:
                query = query.filter(ActionLibraryModel.tags.contains([tag]))
        
        if filters.erpnext_doctype:
            query = query.filter(ActionLibraryModel.erpnext_doctype == filters.erpnext_doctype)
        
        if filters.min_usage_count is not None:
            query = query.filter(ActionLibraryModel.usage_count >= filters.min_usage_count)
        
        if filters.max_usage_count is not None:
            query = query.filter(ActionLibraryModel.usage_count <= filters.max_usage_count)
        
        if filters.created_after:
            query = query.filter(ActionLibraryModel.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.filter(ActionLibraryModel.created_at <= filters.created_before)
        
        if filters.updated_after:
            query = query.filter(ActionLibraryModel.updated_at >= filters.updated_after)
        
        if filters.updated_before:
            query = query.filter(ActionLibraryModel.updated_at <= filters.updated_before)
        
        if filters.search_text:
            search_pattern = f"%{filters.search_text}%"
            query = query.filter(
                or_(
                    ActionLibraryModel.name.ilike(search_pattern),
                    ActionLibraryModel.description.ilike(search_pattern)
                )
            )
        
        return query
    
    def _apply_sorting(self, query, sort: ActionLibrarySortSchema):
        """Apply sorting to the query."""
        
        # Map sort fields to model attributes
        sort_field_map = {
            "name": ActionLibraryModel.name,
            "created_at": ActionLibraryModel.created_at,
            "updated_at": ActionLibraryModel.updated_at,
            "usage_count": ActionLibraryModel.usage_count,
            "category": ActionLibraryModel.category,
            "action_type": ActionLibraryModel.action_type,
            "bdd_step_type": ActionLibraryModel.bdd_step_type
        }
        
        if sort.field in sort_field_map:
            field = sort_field_map[sort.field]
            if sort.direction == "desc":
                query = query.order_by(desc(field))
            else:
                query = query.order_by(asc(field))
        
        return query
    
    def _convert_domain_to_model(self, action: EnhancedActionLibrary) -> ActionLibraryModel:
        """Convert domain object to database model."""
        
        return ActionLibraryModel(
            id=action.action_id,
            name=action.name,
            description=action.description,
            action_type=action.action_type.value,
            bdd_step_type=action.bdd_step_type.value,
            category=action.category.value,
            implementation=action.implementation or {},
            parameters_schema=action.parameters_schema or {},
            expected_outputs_schema=action.expected_outputs_schema or {},
            default_timeout_seconds=action.default_timeout_seconds,
            default_retry_count=action.default_retry_count,
            is_active=action.is_active,
            prerequisites=action.prerequisites or [],
            postconditions=action.postconditions or [],
            tags=action.tags or [],
            usage_count=action.usage_count,
            last_used_date=action.last_used_date,
            metadata=action.metadata or {},
            erpnext_doctype=action.erpnext_doctype,
            ui_selectors=action.ui_selectors or {},
            created_at=action.created_at,
            updated_at=action.updated_at
        )
    
    def _update_model_from_domain(self, model: ActionLibraryModel, action: EnhancedActionLibrary) -> None:
        """Update model fields from domain object."""
        
        model.name = action.name
        model.description = action.description
        model.action_type = action.action_type.value
        model.bdd_step_type = action.bdd_step_type.value
        model.category = action.category.value
        model.implementation = action.implementation or {}
        model.parameters_schema = action.parameters_schema or {}
        model.expected_outputs_schema = action.expected_outputs_schema or {}
        model.default_timeout_seconds = action.default_timeout_seconds
        model.default_retry_count = action.default_retry_count
        model.is_active = action.is_active
        model.prerequisites = action.prerequisites or []
        model.postconditions = action.postconditions or []
        model.tags = action.tags or []
        model.usage_count = action.usage_count
        model.last_used_date = action.last_used_date
        model.metadata = action.metadata or {}
        model.erpnext_doctype = action.erpnext_doctype
        model.ui_selectors = action.ui_selectors or {}
        model.updated_at = action.updated_at or datetime.utcnow()
    
    def _check_needs_versioning(self, model: ActionLibraryModel, action: EnhancedActionLibrary) -> bool:
        """Check if changes require creating a new version."""
        
        # Check for significant changes
        implementation_changed = (
            self._calculate_implementation_hash(action.implementation) !=
            self._calculate_implementation_hash(model.implementation)
        )
        
        schema_changed = (
            self._calculate_schema_hash(action.parameters_schema) !=
            self._calculate_schema_hash(model.parameters_schema)
        )
        
        return implementation_changed or schema_changed
    
    async def _create_new_version(self, model: ActionLibraryModel, action: EnhancedActionLibrary) -> None:
        """Create a new version record."""
        
        # Get current highest version number
        latest_version = (
            self.db_session.query(func.max(ActionVersionModel.version_number))
            .filter(ActionVersionModel.action_id == model.id)
            .scalar()
        ) or 0
        
        version_model = ActionVersionModel(
            action_id=model.id,
            version_number=latest_version + 1,
            implementation_hash=self._calculate_implementation_hash(action.implementation),
            parameters_schema_hash=self._calculate_schema_hash(action.parameters_schema),
            created_at=datetime.utcnow(),
            change_summary="Updated implementation or parameters schema"
        )
        
        self.db_session.add(version_model)
    
    def _calculate_implementation_hash(self, implementation: Dict[str, Any]) -> str:
        """Calculate hash of implementation for versioning."""
        import hashlib
        import json
        
        if not implementation:
            return ""
        
        # Sort keys for consistent hashing
        impl_str = json.dumps(implementation, sort_keys=True)
        return hashlib.md5(impl_str.encode()).hexdigest()
    
    def _calculate_schema_hash(self, schema: Dict[str, Any]) -> str:
        """Calculate hash of schema for versioning."""
        import hashlib
        import json
        
        if not schema:
            return ""
        
        # Sort keys for consistent hashing
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.md5(schema_str.encode()).hexdigest()
    
    async def _convert_model_to_domain(self, model: ActionLibraryModel) -> EnhancedActionLibrary:
        """Convert database model to domain object."""
        
        # Create enhanced action
        action = EnhancedActionLibrary.create_enhanced(
            name=model.name,
            description=model.description,
            action_type=ActionType(model.action_type),
            bdd_step_type=BDDStepType(model.bdd_step_type),
            category=ActionCategory(model.category),
            implementation=model.implementation or {},
            parameters_schema=model.parameters_schema or {},
            expected_outputs_schema=model.expected_outputs_schema or {},
            default_timeout_seconds=model.default_timeout_seconds,
            default_retry_count=model.default_retry_count,
            prerequisites=model.prerequisites or [],
            postconditions=model.postconditions or [],
            tags=model.tags or [],
            metadata=model.metadata or {},
            erpnext_doctype=model.erpnext_doctype,
            ui_selectors=model.ui_selectors or {}
        )
        
        # Set additional properties
        action.action_id = model.id
        action.is_active = model.is_active
        action.usage_count = model.usage_count
        action.last_used_date = model.last_used_date
        action.created_at = model.created_at
        action.updated_at = model.updated_at
        
        # Convert execution metrics if present
        if hasattr(model, 'execution_metrics') and model.execution_metrics:
            action.execution_metrics = await self._convert_metrics_model_to_domain(model.execution_metrics)
        
        return action
    
    async def _convert_metrics_model_to_domain(
        self, metrics_model: ActionExecutionMetricsModel
    ) -> ActionExecutionMetrics:
        """Convert metrics model to domain object."""
        
        from datetime import timedelta
        
        return ActionExecutionMetrics(
            total_executions=metrics_model.total_executions,
            successful_executions=metrics_model.successful_executions,
            failed_executions=metrics_model.failed_executions,
            success_rate=metrics_model.successful_executions / max(metrics_model.total_executions, 1),
            average_duration=timedelta(seconds=metrics_model.average_duration_seconds),
            last_execution_date=metrics_model.last_execution_date,
            common_failure_reasons=metrics_model.common_failure_reasons or []
        )