"""SQLAlchemy implementation of Activity repository.

This module implements the ActivityRepository interface using SQLAlchemy
for persistence operations with PostgreSQL database.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.activities.activity import Activity
from src.domain.activities.activity_repository import (
    ActivityPersonaLinkRepository,
    ActivityRepository,
)
from src.domain.activities.activity_service import ActivityPersonaLink, ActivityPriority
from src.domain.activities.exceptions import (
    ActivityAlreadyExistsError,
    ActivityNotFoundError,
    ActivityPersonaLinkAlreadyExistsError,
    ActivityPersonaLinkNotFoundError,
)
from ..models.activity_model import ActivityModel, ActivityPersonaLinkModel
from .base import BaseRepository


class SQLAlchemyActivityRepository(BaseRepository, ActivityRepository):
    """SQLAlchemy implementation of ActivityRepository."""

    def __init__(self, session: Session):
        super().__init__(session, ActivityModel)

    def _model_to_entity(self, model: ActivityModel) -> Activity:
        """Convert ActivityModel to Activity entity."""
        if not model:
            return None
        
        # Handle UUID conversion for testing
        if os.getenv("TESTING", "false").lower() == "true":
            model_id = str(model.id) if model.id else None
        else:
            model_id = model.id
        
        return Activity(
            id=model_id,
            name=model.name,
            description=model.description,
            erpnext_module=model.erpnext_module,
            action_type=model.action_type,
            target_doctype=model.target_doctype,
            required_fields=model.required_fields if model.required_fields else [],  # JSONType deserializes to list
            validation_rules=model.validation_rules if model.validation_rules else {},  # JSONType deserializes to dict
            success_criteria=model.success_criteria.split(",") if model.success_criteria else [],  # Convert comma-separated string to list
            complexity_score=model.complexity_score,
            estimated_duration=model.estimated_duration,
            prerequisites=model.prerequisites.split(",") if model.prerequisites else [],  # Convert comma-separated string to list
            postconditions=model.postconditions.split(",") if model.postconditions else [],  # Convert comma-separated string to list
            test_data_requirements=model.test_data_requirements if model.test_data_requirements else {},  # JSONType deserializes to dict
            tags=model.tags.split(",") if model.tags else [],  # Convert comma-separated string to list
            is_active=model.is_active,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: Activity) -> ActivityModel:
        """Convert Activity entity to ActivityModel."""
        # Handle UUID conversion for testing - force string conversion
        entity_id = str(entity.id) if entity.id else None
            
        return ActivityModel(
            id=entity_id,
            name=entity.name,
            description=entity.description,
            erpnext_module=entity.erpnext_module,
            action_type=entity.action_type,
            target_doctype=entity.target_doctype,
            required_fields=entity.required_fields,  # Already a list, JSONType handles serialization
            validation_rules=entity.validation_rules,  # Already a dict, JSONType handles serialization
            success_criteria=",".join(entity.success_criteria) if entity.success_criteria else "",  # Convert list to comma-separated string
            complexity_score=entity.complexity_score,
            estimated_duration=entity.estimated_duration,
            prerequisites=",".join(entity.prerequisites) if entity.prerequisites else "",  # Convert list to comma-separated string
            postconditions=",".join(entity.postconditions) if entity.postconditions else "",  # Convert list to comma-separated string
            test_data_requirements=entity.test_data_requirements,  # Already a dict, JSONType handles serialization
            tags=",".join(entity.tags) if entity.tags else "",  # Convert list to comma-separated string
            is_active=entity.is_active,
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, activity: Activity) -> Activity:
        """Create a new activity in the repository."""
        try:
            # Check if activity with same name exists
            existing = (
                self.session.query(ActivityModel)
                .filter(ActivityModel.name == activity.name)
                .first()
            )

            if existing:
                raise ActivityAlreadyExistsError("name", activity.name)

            # Create model from entity using the conversion method
            model = self._entity_to_model(activity)

            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)

            return self._model_to_entity(model)

        except IntegrityError as e:
            self.session.rollback()
            if "name" in str(e):
                raise ActivityAlreadyExistsError("name", activity.name)
            raise SQLAlchemyError(f"Failed to create activity: {e}")

    async def get_by_id(self, activity_id: uuid.UUID) -> Optional[Activity]:
        """Get an activity by its ID."""
        model = (
            self.session.query(ActivityModel)
            .filter(ActivityModel.id == activity_id)
            .first()
        )

        return self._model_to_entity(model) if model else None

    async def get_by_name(self, name: str) -> Optional[Activity]:
        """Get an activity by its name."""
        model = (
            self.session.query(ActivityModel).filter(ActivityModel.name == name).first()
        )

        return self._model_to_entity(model) if model else None

    async def get_all(self) -> list[Activity]:
        """Get all activities."""
        models = self.session.query(ActivityModel).all()
        return [self._model_to_entity(model) for model in models]

    async def update(self, activity: Activity) -> Activity:
        """Update an existing activity."""
        try:
            model = (
                self.session.query(ActivityModel)
                .filter(ActivityModel.id == activity.id)
                .first()
            )

            if not model:
                raise ActivityNotFoundError(str(activity.id))

            # Update model fields
            model.name = activity.name
            model.description = activity.description
            model.complexity_score = activity.complexity_score
            model.estimated_duration = activity.estimated_duration
            model.prerequisites = activity.prerequisites_str
            model.postconditions = activity.postconditions_str
            model.test_data_requirements = activity.test_data_requirements
            model.tags = activity.tags_str
            model.is_active = activity.is_active
            model.version = activity.version
            model.updated_at = activity.updated_at

            self.session.commit()
            self.session.refresh(model)

            return self._model_to_entity(model)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to update activity: {e}")

    async def delete(self, activity_id: uuid.UUID) -> None:
        """Delete an activity by ID."""
        try:
            model = (
                self.session.query(ActivityModel)
                .filter(ActivityModel.id == activity_id)
                .first()
            )

            if not model:
                raise ActivityNotFoundError(str(activity_id))

            self.session.delete(model)
            self.session.commit()

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to delete activity: {e}")

    async def list_with_filters(
        self, filters: dict[str, Any], page: int = 1, per_page: int = 20
    ) -> tuple[list[Activity], int]:
        """List activities with filtering and pagination."""
        query = self.session.query(ActivityModel)

        # Apply filters
        if filters.get("erpnext_module"):
            query = query.filter(
                ActivityModel.erpnext_module == filters["erpnext_module"]
            )

        if filters.get("action_type"):
            query = query.filter(ActivityModel.action_type == filters["action_type"])

        if filters.get("target_doctype"):
            query = query.filter(
                ActivityModel.target_doctype == filters["target_doctype"]
            )

        if filters.get("complexity_score"):
            query = query.filter(
                ActivityModel.complexity_score == filters["complexity_score"]
            )

        if filters.get("is_active") is not None:
            query = query.filter(ActivityModel.is_active == filters["is_active"])

        if filters.get("tags_any"):
            # Search for any of the provided tags
            tag_filters = []
            for tag in filters["tags_any"]:
                tag_filters.append(ActivityModel.tags.contains(tag))
            query = query.filter(or_(*tag_filters))

        if filters.get("min_duration"):
            query = query.filter(
                ActivityModel.estimated_duration >= filters["min_duration"]
            )

        if filters.get("max_duration"):
            query = query.filter(
                ActivityModel.estimated_duration <= filters["max_duration"]
            )

        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    ActivityModel.name.ilike(search_term),
                    ActivityModel.description.ilike(search_term),
                )
            )

        if filters.get("created_after"):
            query = query.filter(ActivityModel.created_at >= filters["created_after"])

        if filters.get("created_before"):
            query = query.filter(ActivityModel.created_at <= filters["created_before"])

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        models = (
            query.order_by(desc(ActivityModel.updated_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )

        activities = [self._model_to_entity(model) for model in models]

        return activities, total

    async def get_by_module(self, erpnext_module: str) -> list[Activity]:
        """Get all activities for a specific ERPNext module."""
        models = (
            self.session.query(ActivityModel)
            .filter(ActivityModel.erpnext_module == erpnext_module)
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    async def get_by_action_type(self, action_type: str) -> list[Activity]:
        """Get all activities for a specific action type."""
        models = (
            self.session.query(ActivityModel)
            .filter(ActivityModel.action_type == action_type)
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    async def get_by_doctype(self, target_doctype: str) -> list[Activity]:
        """Get all activities targeting a specific DocType."""
        models = (
            self.session.query(ActivityModel)
            .filter(ActivityModel.target_doctype == target_doctype)
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    async def get_active_activities(self) -> list[Activity]:
        """Get all active activities."""
        models = (
            self.session.query(ActivityModel)
            .filter(ActivityModel.is_active == True)
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    async def get_inactive_activities(self) -> list[Activity]:
        """Get all inactive activities."""
        models = (
            self.session.query(ActivityModel)
            .filter(ActivityModel.is_active == False)
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    async def search_activities(
        self, query: str, page: int = 1, per_page: int = 20
    ) -> tuple[list[Activity], int]:
        """Search activities by name and description."""
        search_term = f"%{query}%"
        db_query = self.session.query(ActivityModel).filter(
            or_(
                ActivityModel.name.ilike(search_term),
                ActivityModel.description.ilike(search_term),
            )
        )

        total = db_query.count()

        offset = (page - 1) * per_page
        models = (
            db_query.order_by(desc(ActivityModel.updated_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )

        activities = [self._model_to_entity(model) for model in models]

        return activities, total

    async def get_by_complexity_range(
        self, min_complexity: int, max_complexity: int
    ) -> list[Activity]:
        """Get activities within a complexity score range."""
        models = (
            self.session.query(ActivityModel)
            .filter(
                and_(
                    ActivityModel.complexity_score >= min_complexity,
                    ActivityModel.complexity_score <= max_complexity,
                )
            )
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    async def get_by_duration_range(
        self, min_duration: int, max_duration: int
    ) -> list[Activity]:
        """Get activities within an estimated duration range."""
        models = (
            self.session.query(ActivityModel)
            .filter(
                and_(
                    ActivityModel.estimated_duration >= min_duration,
                    ActivityModel.estimated_duration <= max_duration,
                )
            )
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    async def get_by_tags(
        self, tags: list[str], match_any: bool = True
    ) -> list[Activity]:
        """Get activities by tags."""
        if match_any:
            # Match any tag (OR logic)
            tag_filters = []
            for tag in tags:
                tag_filters.append(ActivityModel.tags.contains(tag))
            models = self.session.query(ActivityModel).filter(or_(*tag_filters)).all()
        else:
            # Match all tags (AND logic)
            query = self.session.query(ActivityModel)
            for tag in tags:
                query = query.filter(ActivityModel.tags.contains(tag))
            models = query.all()

        return [self._model_to_entity(model) for model in models]

    async def count_total(self) -> int:
        """Get total count of all activities."""
        return self.session.query(ActivityModel).count()

    async def count_active(self) -> int:
        """Get count of active activities."""
        return (
            self.session.query(ActivityModel)
            .filter(ActivityModel.is_active == True)
            .count()
        )

    async def count_inactive(self) -> int:
        """Get count of inactive activities."""
        return (
            self.session.query(ActivityModel)
            .filter(ActivityModel.is_active == False)
            .count()
        )

    async def get_statistics(self) -> dict[str, Any]:
        """Get activity statistics."""
        # Basic counts
        total = await self.count_total()
        active = await self.count_active()
        inactive = await self.count_inactive()

        # Count by module
        module_counts = (
            self.session.query(
                ActivityModel.erpnext_module, func.count(ActivityModel.id)
            )
            .group_by(ActivityModel.erpnext_module)
            .all()
        )
        by_module = {module: count for module, count in module_counts}

        # Count by action type
        action_counts = (
            self.session.query(ActivityModel.action_type, func.count(ActivityModel.id))
            .group_by(ActivityModel.action_type)
            .all()
        )
        by_action_type = {action: count for action, count in action_counts}

        # Count by complexity
        complexity_counts = (
            self.session.query(
                ActivityModel.complexity_score, func.count(ActivityModel.id)
            )
            .group_by(ActivityModel.complexity_score)
            .all()
        )
        by_complexity = {complexity: count for complexity, count in complexity_counts}

        # Duration statistics
        duration_stats = self.session.query(
            func.avg(ActivityModel.estimated_duration),
            func.sum(ActivityModel.estimated_duration),
        ).first()

        avg_duration = float(duration_stats[0]) if duration_stats[0] else 0
        total_duration = int(duration_stats[1]) if duration_stats[1] else 0

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "by_module": by_module,
            "by_action_type": by_action_type,
            "by_complexity": by_complexity,
            "avg_duration": avg_duration,
            "total_duration": total_duration,
        }

    async def bulk_update_status(
        self, activity_ids: list[uuid.UUID], is_active: bool
    ) -> int:
        """Bulk update activity status."""
        try:
            result = (
                self.session.query(ActivityModel)
                .filter(ActivityModel.id.in_(activity_ids))
                .update(
                    {
                        ActivityModel.is_active: is_active,
                        ActivityModel.updated_at: datetime.utcnow(),
                    },
                    synchronize_session=False,
                )
            )

            self.session.commit()
            return result

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to bulk update activities: {e}")

    async def bulk_delete(self, activity_ids: list[uuid.UUID]) -> int:
        """Bulk delete activities."""
        try:
            result = (
                self.session.query(ActivityModel)
                .filter(ActivityModel.id.in_(activity_ids))
                .delete(synchronize_session=False)
            )

            self.session.commit()
            return result

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to bulk delete activities: {e}")

    async def get_activities_by_ids(
        self, activity_ids: list[uuid.UUID]
    ) -> list[Activity]:
        """Get multiple activities by their IDs."""
        models = (
            self.session.query(ActivityModel)
            .filter(ActivityModel.id.in_(activity_ids))
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    async def exists_by_name(
        self, name: str, exclude_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check if an activity with the given name exists."""
        query = self.session.query(ActivityModel).filter(ActivityModel.name == name)

        if exclude_id:
            query = query.filter(ActivityModel.id != exclude_id)

        return query.first() is not None

    async def get_recent_activities(
        self, limit: int = 10, days: int = 30
    ) -> list[Activity]:
        """Get recently created or updated activities."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        models = (
            self.session.query(ActivityModel)
            .filter(
                or_(
                    ActivityModel.created_at >= cutoff_date,
                    ActivityModel.updated_at >= cutoff_date,
                )
            )
            .order_by(desc(ActivityModel.updated_at))
            .limit(limit)
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    async def get_activities_needing_review(self) -> list[Activity]:
        """Get activities that might need review."""
        # Activities with extreme complexity scores or unusual characteristics
        models = (
            self.session.query(ActivityModel)
            .filter(
                or_(
                    ActivityModel.complexity_score == 1,  # Very low complexity
                    ActivityModel.complexity_score == 5,  # Very high complexity
                    ActivityModel.estimated_duration < 30,  # Very short duration
                    ActivityModel.estimated_duration
                    > 1800,  # Very long duration (30+ minutes)
                    ActivityModel.validation_rules == "{}",  # No validation rules
                    ActivityModel.success_criteria == "",  # No success criteria
                )
            )
            .all()
        )

        return [self._model_to_entity(model) for model in models]

    def _model_to_entity(self, model: ActivityModel) -> Activity:
        """Convert ActivityModel to Activity entity."""
        # JSON fields are already deserialized by SQLAlchemy's JSON type
        validation_rules = model.validation_rules or {}
        test_data_requirements = model.test_data_requirements or {}

        # Parse comma-separated fields
        required_fields = (
            [f.strip() for f in model.required_fields.split(",") if f.strip()]
            if model.required_fields
            else []
        )
        success_criteria = (
            [c.strip() for c in model.success_criteria.split(",") if c.strip()]
            if model.success_criteria
            else []
        )
        prerequisites = (
            [p.strip() for p in model.prerequisites.split(",") if p.strip()]
            if model.prerequisites
            else []
        )
        postconditions = (
            [p.strip() for p in model.postconditions.split(",") if p.strip()]
            if model.postconditions
            else []
        )
        tags = (
            [t.strip() for t in model.tags.split(",") if t.strip()]
            if model.tags
            else []
        )

        return Activity(
            id=model.id,
            name=model.name,
            description=model.description,
            erpnext_module=model.erpnext_module,
            action_type=model.action_type,
            target_doctype=model.target_doctype,
            required_fields=required_fields,
            validation_rules=validation_rules,
            success_criteria=success_criteria,
            complexity_score=model.complexity_score,
            estimated_duration=model.estimated_duration,
            prerequisites=prerequisites,
            postconditions=postconditions,
            test_data_requirements=test_data_requirements,
            tags=tags,
            is_active=model.is_active,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity) -> ActivityModel:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: Activity domain entity

        Returns:
            SQLAlchemy activity model
        """
        return ActivityModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            erpnext_module=entity.erpnext_module,
            action_type=entity.action_type,
            target_doctype=entity.target_doctype,
            required_fields=",".join(entity.required_fields) if entity.required_fields else None,
            validation_rules=entity.validation_rules,
            success_criteria=",".join(entity.success_criteria) if entity.success_criteria else None,
            complexity_score=entity.complexity_score,
            estimated_duration=entity.estimated_duration,
            prerequisites=",".join(entity.prerequisites) if entity.prerequisites else None,
            postconditions=",".join(entity.postconditions) if entity.postconditions else None,
            test_data_requirements=entity.test_data_requirements,
            tags=",".join(entity.tags) if entity.tags else None,
            is_active=entity.is_active,
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class SQLAlchemyActivityPersonaLinkRepository(
    BaseRepository, ActivityPersonaLinkRepository
):
    """SQLAlchemy implementation of ActivityPersonaLinkRepository."""

    def __init__(self, session: Session):
        super().__init__(session, ActivityPersonaLinkModel)

    async def create(
        self,
        persona_id: uuid.UUID,
        activity_id: uuid.UUID,
        priority: str = "medium",
        notes: str = "",
        is_primary: bool = False,
        execution_order: int = 0,
    ) -> ActivityPersonaLinkModel:
        """Create a new activity-persona link."""
        try:
            # Check if link already exists
            existing = (
                self.session.query(ActivityPersonaLinkModel)
                .filter(
                    and_(
                        ActivityPersonaLinkModel.persona_id == persona_id,
                        ActivityPersonaLinkModel.activity_id == activity_id,
                    )
                )
                .first()
            )

            if existing:
                raise ActivityPersonaLinkAlreadyExistsError(
                    str(activity_id), str(persona_id)
                )

            model = ActivityPersonaLinkModel(
                persona_id=persona_id,
                activity_id=activity_id,
                priority=priority,
                notes=notes,
                is_primary=is_primary,
                execution_order=execution_order,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)

            return model

        except IntegrityError:
            self.session.rollback()
            raise ActivityPersonaLinkAlreadyExistsError(
                str(activity_id), str(persona_id)
            )

    async def get_by_ids(
        self, persona_id: uuid.UUID, activity_id: uuid.UUID
    ) -> Optional[ActivityPersonaLinkModel]:
        """Get a link by persona and activity IDs."""
        return (
            self.session.query(ActivityPersonaLinkModel)
            .filter(
                and_(
                    ActivityPersonaLinkModel.persona_id == persona_id,
                    ActivityPersonaLinkModel.activity_id == activity_id,
                )
            )
            .first()
        )

    async def get_by_persona_id(
        self,
        persona_id: uuid.UUID,
        priority_filter: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[ActivityPersonaLinkModel]:
        """Get all links for a persona."""
        query = self.session.query(ActivityPersonaLinkModel).filter(
            ActivityPersonaLinkModel.persona_id == persona_id
        )

        if priority_filter:
            query = query.filter(ActivityPersonaLinkModel.priority == priority_filter)

        offset = (page - 1) * per_page
        return (
            query.order_by(asc(ActivityPersonaLinkModel.execution_order))
            .offset(offset)
            .limit(per_page)
            .all()
        )

    async def get_by_activity_id(
        self, activity_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> list[ActivityPersonaLinkModel]:
        """Get all links for an activity."""
        query = self.session.query(ActivityPersonaLinkModel).filter(
            ActivityPersonaLinkModel.activity_id == activity_id
        )

        offset = (page - 1) * per_page
        return (
            query.order_by(desc(ActivityPersonaLinkModel.created_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )

    async def update(self, link: ActivityPersonaLinkModel) -> ActivityPersonaLinkModel:
        """Update an activity-persona link."""
        try:
            link.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(link)
            return link

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to update activity-persona link: {e}")

    async def delete_by_ids(
        self, persona_id: uuid.UUID, activity_id: uuid.UUID
    ) -> None:
        """Delete a link by persona and activity IDs."""
        try:
            result = (
                self.session.query(ActivityPersonaLinkModel)
                .filter(
                    and_(
                        ActivityPersonaLinkModel.persona_id == persona_id,
                        ActivityPersonaLinkModel.activity_id == activity_id,
                    )
                )
                .delete()
            )

            if result == 0:
                raise ActivityPersonaLinkNotFoundError(
                    str(activity_id), str(persona_id)
                )

            self.session.commit()

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to delete activity-persona link: {e}")

    async def delete_by_persona_id(self, persona_id: uuid.UUID) -> int:
        """Delete all links for a persona."""
        try:
            result = (
                self.session.query(ActivityPersonaLinkModel)
                .filter(ActivityPersonaLinkModel.persona_id == persona_id)
                .delete()
            )

            self.session.commit()
            return result

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to delete persona links: {e}")

    async def delete_by_activity_id(self, activity_id: uuid.UUID) -> int:
        """Delete all links for an activity."""
        try:
            result = (
                self.session.query(ActivityPersonaLinkModel)
                .filter(ActivityPersonaLinkModel.activity_id == activity_id)
                .delete()
            )

            self.session.commit()
            return result

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to delete activity links: {e}")

    async def count_by_persona_id(
        self, persona_id: uuid.UUID, priority_filter: Optional[str] = None
    ) -> int:
        """Count links for a persona."""
        query = self.session.query(ActivityPersonaLinkModel).filter(
            ActivityPersonaLinkModel.persona_id == persona_id
        )

        if priority_filter:
            query = query.filter(ActivityPersonaLinkModel.priority == priority_filter)

        return query.count()

    async def count_by_activity_id(self, activity_id: uuid.UUID) -> int:
        """Count links for an activity."""
        return (
            self.session.query(ActivityPersonaLinkModel)
            .filter(ActivityPersonaLinkModel.activity_id == activity_id)
            .count()
        )

    async def get_link_statistics(self) -> dict[str, Any]:
        """Get activity-persona link statistics."""
        # Basic counts
        total_links = self.session.query(ActivityPersonaLinkModel).count()

        # Unique counts
        unique_personas = self.session.query(
            func.count(func.distinct(ActivityPersonaLinkModel.persona_id))
        ).scalar()

        unique_activities = self.session.query(
            func.count(func.distinct(ActivityPersonaLinkModel.activity_id))
        ).scalar()

        # Priority distribution
        priority_counts = (
            self.session.query(
                ActivityPersonaLinkModel.priority,
                func.count(ActivityPersonaLinkModel.id),
            )
            .group_by(ActivityPersonaLinkModel.priority)
            .all()
        )
        by_priority = {priority: count for priority, count in priority_counts}

        # Averages
        avg_activities_per_persona = (
            total_links / unique_personas if unique_personas > 0 else 0
        )
        avg_personas_per_activity = (
            total_links / unique_activities if unique_activities > 0 else 0
        )

        return {
            "total_links": total_links,
            "unique_personas": unique_personas,
            "unique_activities": unique_activities,
            "by_priority": by_priority,
            "avg_activities_per_persona": avg_activities_per_persona,
            "avg_personas_per_activity": avg_personas_per_activity,
        }

    async def bulk_create_links(
        self,
        persona_id: uuid.UUID,
        activity_ids: list[uuid.UUID],
        priority: str = "medium",
        notes: str = "",
    ) -> list[ActivityPersonaLinkModel]:
        """Bulk create activity-persona links."""
        try:
            created_links = []

            for activity_id in activity_ids:
                # Skip if link already exists
                existing = await self.get_by_ids(persona_id, activity_id)
                if not existing:
                    link = await self.create(persona_id, activity_id, priority, notes)
                    created_links.append(link)

            return created_links

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to bulk create links: {e}")

    async def bulk_delete_links(
        self, persona_id: uuid.UUID, activity_ids: list[uuid.UUID]
    ) -> int:
        """Bulk delete activity-persona links."""
        try:
            result = (
                self.session.query(ActivityPersonaLinkModel)
                .filter(
                    and_(
                        ActivityPersonaLinkModel.persona_id == persona_id,
                        ActivityPersonaLinkModel.activity_id.in_(activity_ids),
                    )
                )
                .delete(synchronize_session=False)
            )

            self.session.commit()
            return result

        except SQLAlchemyError as e:
            self.session.rollback()
            raise SQLAlchemyError(f"Failed to bulk delete links: {e}")

    def _model_to_entity(self, model: ActivityPersonaLinkModel) -> ActivityPersonaLink:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: SQLAlchemy model instance

        Returns:
            Domain entity instance
        """
        return ActivityPersonaLink(
            activity_id=model.activity_id,
            persona_id=model.persona_id,
            priority=ActivityPriority(model.priority.upper()),
            notes=model.notes or "",
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_primary=model.is_primary,
            execution_order=model.execution_order,
        )

    def _entity_to_model(self, entity: ActivityPersonaLink) -> ActivityPersonaLinkModel:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: Domain entity instance

        Returns:
            SQLAlchemy model instance
        """
        return ActivityPersonaLinkModel(
            activity_id=entity.activity_id,
            persona_id=entity.persona_id,
            priority=entity.priority.value.lower(),
            notes=entity.notes,
            is_primary=entity.is_primary,
            execution_order=entity.execution_order,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
