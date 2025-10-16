"""Persona repository implementation.

SQLAlchemy implementation of the persona repository interface
for the ERPNext Test Automation Meta-Framework.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ....domain.personas import Persona, PersonaAlreadyExistsError, PersonaConcurrencyError
from ....domain.personas.persona_repository import PersonaRepository
from ..models.persona_model import PersonaModel

logger = logging.getLogger(__name__)


class SQLAlchemyPersonaRepository(PersonaRepository):
    """SQLAlchemy implementation of persona repository."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    async def save(self, persona: Persona) -> Persona:
        """Save a persona entity."""
        try:
            # Check if this is an update
            if persona.id:
                existing_model = self.session.query(PersonaModel).filter(
                    PersonaModel.id == persona.id
                ).first()
                
                if existing_model:
                    # Check for concurrent modification
                    if existing_model.version != persona.version:
                        raise PersonaConcurrencyError(
                            str(persona.id),
                            persona.version,
                            existing_model.version
                        )
                    
                    # Update existing model
                    existing_model.update_from_domain(persona)
                    existing_model.version += 1
                    
                    self.session.flush()
                    return existing_model.to_domain()
                else:
                    # Create new model for existing persona
                    model = PersonaModel.from_domain(persona)
                    self.session.add(model)
            else:
                # Create new model
                model = PersonaModel.from_domain(persona)
                self.session.add(model)
            
            self.session.flush()
            return model.to_domain()
            
        except IntegrityError as e:
            self.session.rollback()
            if "personas_name_key" in str(e):
                raise PersonaAlreadyExistsError("name", persona.name)
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving persona: {e}")
            raise
    
    async def find_by_id(self, persona_id: UUID) -> Optional[Persona]:
        """Find persona by unique identifier."""
        model = self.session.query(PersonaModel).filter(
            PersonaModel.id == persona_id
        ).first()
        
        return model.to_domain() if model else None
    
    async def find_by_name(self, name: str) -> Optional[Persona]:
        """Find persona by name."""
        model = self.session.query(PersonaModel).filter(
            PersonaModel.name == name
        ).first()
        
        return model.to_domain() if model else None
    
    async def find_all(self) -> List[Persona]:
        """Find all personas in the system."""
        models = self.session.query(PersonaModel).order_by(
            PersonaModel.created_at.desc()
        ).all()
        
        return [model.to_domain() for model in models]
    
    async def find_active(self) -> List[Persona]:
        """Find all active personas."""
        models = self.session.query(PersonaModel).filter(
            PersonaModel.is_active == True
        ).order_by(PersonaModel.name).all()
        
        return [model.to_domain() for model in models]
    
    async def find_by_role(self, erpnext_role: str) -> List[Persona]:
        """Find personas that have specific ERPNext role."""
        # Use LIKE to search within comma-separated roles
        models = self.session.query(PersonaModel).filter(
            or_(
                PersonaModel.erpnext_roles.like(f"{erpnext_role},%"),
                PersonaModel.erpnext_roles.like(f"%,{erpnext_role},%"),
                PersonaModel.erpnext_roles.like(f"%,{erpnext_role}"),
                PersonaModel.erpnext_roles == erpnext_role
            )
        ).order_by(PersonaModel.name).all()
        
        return [model.to_domain() for model in models]
    
    async def find_with_permission(self, permission: str) -> List[Persona]:
        """Find personas that have specific permission."""
        # Use LIKE to search within comma-separated permissions
        models = self.session.query(PersonaModel).filter(
            or_(
                PersonaModel.permissions.like(f"{permission},%"),
                PersonaModel.permissions.like(f"%,{permission},%"),
                PersonaModel.permissions.like(f"%,{permission}"),
                PersonaModel.permissions == permission
            )
        ).order_by(PersonaModel.name).all()
        
        return [model.to_domain() for model in models]
    
    async def search(self, query: str) -> List[Persona]:
        """Search personas by name or description."""
        search_pattern = f"%{query}%"
        
        models = self.session.query(PersonaModel).filter(
            or_(
                PersonaModel.name.ilike(search_pattern),
                PersonaModel.description.ilike(search_pattern)
            )
        ).order_by(PersonaModel.name).all()
        
        return [model.to_domain() for model in models]
    
    async def find_with_pagination(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Persona], int]:
        """Find personas with filtering, pagination, and sorting."""
        query = self.session.query(PersonaModel)
        
        # Apply filters
        if filters:
            if 'search' in filters:
                search_pattern = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        PersonaModel.name.ilike(search_pattern),
                        PersonaModel.description.ilike(search_pattern)
                    )
                )
            
            if 'is_active' in filters:
                query = query.filter(PersonaModel.is_active == filters['is_active'])
            
            if 'erpnext_roles' in filters:
                role_conditions = []
                for role in filters['erpnext_roles']:
                    role_conditions.append(
                        or_(
                            PersonaModel.erpnext_roles.like(f"{role},%"),
                            PersonaModel.erpnext_roles.like(f"%,{role},%"),
                            PersonaModel.erpnext_roles.like(f"%,{role}"),
                            PersonaModel.erpnext_roles == role
                        )
                    )
                query = query.filter(or_(*role_conditions))
            
            if 'has_permissions' in filters:
                perm_conditions = []
                for perm in filters['has_permissions']:
                    perm_conditions.append(
                        or_(
                            PersonaModel.permissions.like(f"{perm},%"),
                            PersonaModel.permissions.like(f"%,{perm},%"),
                            PersonaModel.permissions.like(f"%,{perm}"),
                            PersonaModel.permissions == perm
                        )
                    )
                query = query.filter(or_(*perm_conditions))
            
            if 'created_after' in filters:
                query = query.filter(PersonaModel.created_at >= filters['created_after'])
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(PersonaModel, sort_by, PersonaModel.created_at)
        if sort_order.lower() == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * page_size
        models = query.offset(offset).limit(page_size).all()
        
        personas = [model.to_domain() for model in models]
        
        return personas, total
    
    async def count_total(self) -> int:
        """Get total count of personas."""
        return self.session.query(PersonaModel).count()
    
    async def count_active(self) -> int:
        """Get count of active personas."""
        return self.session.query(PersonaModel).filter(
            PersonaModel.is_active == True
        ).count()
    
    async def count_by_role(self, erpnext_role: str) -> int:
        """Get count of personas with specific role."""
        return self.session.query(PersonaModel).filter(
            or_(
                PersonaModel.erpnext_roles.like(f"{erpnext_role},%"),
                PersonaModel.erpnext_roles.like(f"%,{erpnext_role},%"),
                PersonaModel.erpnext_roles.like(f"%,{erpnext_role}"),
                PersonaModel.erpnext_roles == erpnext_role
            )
        ).count()
    
    async def delete(self, persona_id: UUID) -> bool:
        """Delete a persona."""
        model = self.session.query(PersonaModel).filter(
            PersonaModel.id == persona_id
        ).first()
        
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        
        return False
    
    async def exists_by_name(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if persona with name exists."""
        query = self.session.query(PersonaModel).filter(
            PersonaModel.name == name
        )
        
        if exclude_id:
            query = query.filter(PersonaModel.id != exclude_id)
        
        return query.first() is not None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get persona statistics for analytics."""
        total = await self.count_total()
        active = await self.count_active()
        inactive = total - active
        
        # Get role distribution
        roles_dist = await self.get_role_distribution()
        
        # Get permission distribution
        perms_dist = await self.get_permission_distribution()
        
        # Get creation trend (last 30 days)
        creation_trend = await self.get_creation_trend(30)
        
        # Calculate complexity metrics
        complex_personas = self.session.query(PersonaModel).all()
        complexity_scores = []
        for model in complex_personas:
            role_count = len([r for r in model.erpnext_roles.split(',') if r.strip()])
            perm_count = len([p for p in (model.permissions or '').split(',') if p.strip()])
            complexity_scores.append(role_count * 2 + perm_count)
        
        complexity_metrics = {
            'avg_complexity': sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0,
            'max_complexity': max(complexity_scores) if complexity_scores else 0,
            'min_complexity': min(complexity_scores) if complexity_scores else 0
        }
        
        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'roles_distribution': roles_dist,
            'permissions_distribution': perms_dist,
            'creation_trend': creation_trend,
            'complexity_metrics': complexity_metrics
        }
    
    async def find_created_after(self, date: datetime) -> List[Persona]:
        """Find personas created after specific date."""
        models = self.session.query(PersonaModel).filter(
            PersonaModel.created_at >= date
        ).order_by(PersonaModel.created_at.desc()).all()
        
        return [model.to_domain() for model in models]
    
    async def find_updated_after(self, date: datetime) -> List[Persona]:
        """Find personas updated after specific date."""
        models = self.session.query(PersonaModel).filter(
            PersonaModel.updated_at >= date
        ).order_by(PersonaModel.updated_at.desc()).all()
        
        return [model.to_domain() for model in models]
    
    async def find_by_multiple_roles(self, erpnext_roles: List[str], match_all: bool = False) -> List[Persona]:
        """Find personas that have multiple ERPNext roles."""
        if not erpnext_roles:
            return []
        
        if match_all:
            # Persona must have ALL specified roles
            query = self.session.query(PersonaModel)
            for role in erpnext_roles:
                query = query.filter(
                    or_(
                        PersonaModel.erpnext_roles.like(f"{role},%"),
                        PersonaModel.erpnext_roles.like(f"%,{role},%"),
                        PersonaModel.erpnext_roles.like(f"%,{role}"),
                        PersonaModel.erpnext_roles == role
                    )
                )
        else:
            # Persona must have ANY of the specified roles
            role_conditions = []
            for role in erpnext_roles:
                role_conditions.append(
                    or_(
                        PersonaModel.erpnext_roles.like(f"{role},%"),
                        PersonaModel.erpnext_roles.like(f"%,{role},%"),
                        PersonaModel.erpnext_roles.like(f"%,{role}"),
                        PersonaModel.erpnext_roles == role
                    )
                )
            query = self.session.query(PersonaModel).filter(or_(*role_conditions))
        
        models = query.order_by(PersonaModel.name).all()
        return [model.to_domain() for model in models]
    
    async def find_complex_personas(self, min_roles: int = 3, min_permissions: int = 5) -> List[Persona]:
        """Find personas with high complexity."""
        # This is a simplified approach - in production, you might want to use
        # database functions to count array elements
        models = self.session.query(PersonaModel).all()
        
        complex_personas = []
        for model in models:
            role_count = len([r for r in model.erpnext_roles.split(',') if r.strip()])
            perm_count = len([p for p in (model.permissions or '').split(',') if p.strip()])
            
            if role_count >= min_roles or perm_count >= min_permissions:
                complex_personas.append(model.to_domain())
        
        return complex_personas
    
    async def get_role_distribution(self) -> Dict[str, int]:
        """Get distribution of ERPNext roles across personas."""
        models = self.session.query(PersonaModel).all()
        
        role_counts = {}
        for model in models:
            roles = [r.strip() for r in model.erpnext_roles.split(',') if r.strip()]
            for role in roles:
                role_counts[role] = role_counts.get(role, 0) + 1
        
        return role_counts
    
    async def get_permission_distribution(self) -> Dict[str, int]:
        """Get distribution of permissions across personas."""
        models = self.session.query(PersonaModel).all()
        
        perm_counts = {}
        for model in models:
            if model.permissions:
                perms = [p.strip() for p in model.permissions.split(',') if p.strip()]
                for perm in perms:
                    perm_counts[perm] = perm_counts.get(perm, 0) + 1
        
        return perm_counts
    
    async def get_creation_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get persona creation trend over specified period."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query to get daily creation counts
        query = self.session.query(
            func.date(PersonaModel.created_at).label('date'),
            func.count(PersonaModel.id).label('count')
        ).filter(
            PersonaModel.created_at >= start_date
        ).group_by(
            func.date(PersonaModel.created_at)
        ).order_by(
            func.date(PersonaModel.created_at)
        )
        
        results = query.all()
        
        return [
            {
                'date': result.date.isoformat(),
                'count': result.count
            }
            for result in results
        ]
    
    async def find_similar_by_roles(self, persona: Persona, similarity_threshold: float = 0.5) -> List[Persona]:
        """Find personas with similar role combinations."""
        # Get all personas except the reference one
        models = self.session.query(PersonaModel).filter(
            PersonaModel.id != persona.id
        ).all()
        
        persona_roles = set(persona.erpnext_roles)
        similar_personas = []
        
        for model in models:
            model_roles = set([r.strip() for r in model.erpnext_roles.split(',') if r.strip()])
            
            # Calculate Jaccard similarity
            intersection = len(persona_roles.intersection(model_roles))
            union = len(persona_roles.union(model_roles))
            
            if union > 0:
                similarity = intersection / union
                if similarity >= similarity_threshold:
                    similar_personas.append(model.to_domain())
        
        return similar_personas
    
    async def bulk_update_status(self, persona_ids: List[UUID], is_active: bool) -> int:
        """Bulk update active status for multiple personas."""
        result = self.session.query(PersonaModel).filter(
            PersonaModel.id.in_(persona_ids)
        ).update(
            {PersonaModel.is_active: is_active},
            synchronize_session=False
        )
        
        self.session.flush()
        return result
    
    async def cleanup_inactive(self, days_inactive: int = 90) -> int:
        """Clean up personas that have been inactive for specified period."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
        
        # Find inactive personas that haven't been updated recently
        inactive_personas = self.session.query(PersonaModel).filter(
            and_(
                PersonaModel.is_active == False,
                PersonaModel.updated_at < cutoff_date
            )
        )
        
        count = inactive_personas.count()
        
        # Delete them
        inactive_personas.delete(synchronize_session=False)
        self.session.flush()
        
        return count