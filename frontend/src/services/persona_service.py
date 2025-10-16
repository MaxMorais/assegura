"""Persona API client service for ERPNext Test Automation Meta-Framework.

Provides comprehensive client-side interface for persona management operations
with error handling, caching, and offline support.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID
import json

from .api_client import APIClient

logger = logging.getLogger(__name__)


class PersonaCache:
    """Simple in-memory cache for persona data."""
    
    def __init__(self, ttl_minutes: int = 30):
        """Initialize cache with TTL."""
        self.ttl_seconds = ttl_minutes * 60
        self._persona_cache = {}
        self._list_cache = {}
        self._summary_cache = {}
        self._stats_cache = {}
        self._stats_timestamp = None
    
    def _is_expired(self, timestamp: datetime) -> bool:
        """Check if cached data is expired."""
        return (datetime.now() - timestamp).total_seconds() > self.ttl_seconds
    
    def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get cached persona data."""
        entry = self._persona_cache.get(persona_id)
        if entry and not self._is_expired(entry['timestamp']):
            return entry['data']
        return None
    
    def set_persona(self, persona_data: Dict[str, Any]) -> None:
        """Cache persona data."""
        persona_id = persona_data.get('id')
        if persona_id:
            self._persona_cache[persona_id] = {
                'data': persona_data,
                'timestamp': datetime.now()
            }
    
    def remove_persona(self, persona_id: str) -> None:
        """Remove persona from cache."""
        self._persona_cache.pop(persona_id, None)
        self._summary_cache.pop(persona_id, None)
    
    def get_list(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached list data."""
        entry = self._list_cache.get(cache_key)
        if entry and not self._is_expired(entry['timestamp']):
            return entry['data']
        return None
    
    def set_list(self, cache_key: str, list_data: Dict[str, Any]) -> None:
        """Cache list data."""
        self._list_cache[cache_key] = {
            'data': list_data,
            'timestamp': datetime.now()
        }
    
    def invalidate_list_cache(self) -> None:
        """Clear all list cache entries."""
        self._list_cache.clear()
    
    def get_summary(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get cached summary data."""
        entry = self._summary_cache.get(persona_id)
        if entry and not self._is_expired(entry['timestamp']):
            return entry['data']
        return None
    
    def set_summary(self, persona_id: str, summary_data: Dict[str, Any]) -> None:
        """Cache summary data."""
        self._summary_cache[persona_id] = {
            'data': summary_data,
            'timestamp': datetime.now()
        }
    
    def get_statistics(self) -> Optional[Dict[str, Any]]:
        """Get cached statistics."""
        if self._stats_cache and self._stats_timestamp and not self._is_expired(self._stats_timestamp):
            return self._stats_cache
        return None
    
    def set_statistics(self, stats_data: Dict[str, Any]) -> None:
        """Cache statistics data."""
        self._stats_cache = stats_data
        self._stats_timestamp = datetime.now()
    
    def clear_all(self) -> None:
        """Clear all cached data."""
        self._persona_cache.clear()
        self._list_cache.clear()
        self._summary_cache.clear()
        self._stats_cache.clear()
        self._stats_timestamp = None


class PersonaAPIError(Exception):
    """Base exception for persona API operations."""
    pass


class PersonaNotFoundError(PersonaAPIError):
    """Raised when a persona is not found."""
    pass


class PersonaValidationError(PersonaAPIError):
    """Raised when persona validation fails."""
    pass


class PersonaService:
    """Client-side service for persona management operations."""
    
    def __init__(self, api_client: APIClient, cache_ttl_minutes: int = 30):
        """Initialize persona service.
        
        Args:
            api_client: Base API client instance
            cache_ttl_minutes: Cache time-to-live in minutes
        """
        self.api_client = api_client
        self.cache = PersonaCache(ttl_minutes=cache_ttl_minutes)
        self.base_url = "/personas"
    
    async def create_persona(self, persona_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new persona.
        
        Args:
            persona_data: Persona creation data
            
        Returns:
            Created persona information
            
        Raises:
            PersonaValidationError: If validation fails
            PersonaAPIError: If creation fails
        """
        try:
            logger.info(f"Creating persona: {persona_data.get('name')}")
            
            response = await self.api_client.post(
                endpoint=self.base_url,
                data=persona_data
            )
            
            # Cache the new persona
            self.cache.set_persona(response)
            
            # Invalidate list cache since we have new data
            self.cache.invalidate_list_cache()
            
            logger.info(f"Successfully created persona: {response.get('id')}")
            return response
            
        except self.api_client.ValidationError as e:
            logger.warning(f"Persona validation failed: {e}")
            raise PersonaValidationError(str(e)) from e
        except Exception as e:
            logger.error(f"Failed to create persona: {e}")
            raise PersonaAPIError(f"Failed to create persona: {str(e)}") from e
    
    async def get_persona(self, persona_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get persona by ID.
        
        Args:
            persona_id: Unique persona identifier
            use_cache: Whether to use cached data if available
            
        Returns:
            Persona information
            
        Raises:
            PersonaNotFoundError: If persona not found
            PersonaAPIError: If retrieval fails
        """
        try:
            # Check cache first if enabled
            if use_cache:
                cached = self.cache.get_persona(persona_id)
                if cached:
                    logger.debug(f"Retrieved persona {persona_id} from cache")
                    return cached
            
            logger.info(f"Fetching persona: {persona_id}")
            
            response = await self.api_client.get(
                endpoint=f"{self.base_url}/{persona_id}"
            )
            
            # Cache the result
            self.cache.set_persona(response)
            
            logger.info(f"Successfully retrieved persona: {persona_id}")
            return response
            
        except self.api_client.NotFoundError as e:
            logger.warning(f"Persona {persona_id} not found: {e}")
            raise PersonaNotFoundError(f"Persona {persona_id} not found") from e
        except Exception as e:
            logger.error(f"Failed to get persona {persona_id}: {e}")
            raise PersonaAPIError(f"Failed to retrieve persona: {str(e)}") from e
    
    async def update_persona(self, persona_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update persona information.
        
        Args:
            persona_id: Unique persona identifier
            update_data: Updated persona data
            
        Returns:
            Updated persona information
            
        Raises:
            PersonaNotFoundError: If persona not found
            PersonaValidationError: If validation fails
            PersonaAPIError: If update fails
        """
        try:
            logger.info(f"Updating persona: {persona_id}")
            
            response = await self.api_client.put(
                endpoint=f"{self.base_url}/{persona_id}",
                data=update_data
            )
            
            # Update cache
            self.cache.set_persona(response)
            
            # Invalidate list cache since data changed
            self.cache.invalidate_list_cache()
            
            logger.info(f"Successfully updated persona: {persona_id}")
            return response
            
        except self.api_client.NotFoundError as e:
            logger.warning(f"Persona {persona_id} not found for update: {e}")
            raise PersonaNotFoundError(f"Persona {persona_id} not found") from e
        except self.api_client.ValidationError as e:
            logger.warning(f"Persona update validation failed: {e}")
            raise PersonaValidationError(str(e)) from e
        except Exception as e:
            logger.error(f"Failed to update persona {persona_id}: {e}")
            raise PersonaAPIError(f"Failed to update persona: {str(e)}") from e
    
    async def delete_persona(self, persona_id: str) -> None:
        """Delete persona by ID.
        
        Args:
            persona_id: Unique persona identifier
            
        Raises:
            PersonaNotFoundError: If persona not found
            PersonaAPIError: If deletion fails
        """
        try:
            logger.info(f"Deleting persona: {persona_id}")
            
            await self.api_client.delete(
                endpoint=f"{self.base_url}/{persona_id}"
            )
            
            # Remove from cache
            self.cache.remove_persona(persona_id)
            
            # Invalidate list cache since data changed
            self.cache.invalidate_list_cache()
            
            logger.info(f"Successfully deleted persona: {persona_id}")
            
        except self.api_client.NotFoundError as e:
            logger.warning(f"Persona {persona_id} not found for deletion: {e}")
            raise PersonaNotFoundError(f"Persona {persona_id} not found") from e
        except Exception as e:
            logger.error(f"Failed to delete persona {persona_id}: {e}")
            raise PersonaAPIError(f"Failed to delete persona: {str(e)}") from e
    
    async def list_personas(self, 
                           limit: int = 50,
                           offset: int = 0,
                           search: Optional[str] = None,
                           is_active: Optional[bool] = None,
                           erpnext_role: Optional[str] = None,
                           use_cache: bool = True) -> Dict[str, Any]:
        """List personas with filtering and pagination.
        
        Args:
            limit: Maximum number of personas to return
            offset: Number of personas to skip
            search: Search term for names and descriptions
            is_active: Filter by active status
            erpnext_role: Filter by ERPNext role
            use_cache: Whether to use cached data if available
            
        Returns:
            Paginated list of personas with metadata
            
        Raises:
            PersonaAPIError: If listing fails
        """
        try:
            # Build cache key from parameters
            cache_key = self._build_list_cache_key(limit, offset, search, is_active, erpnext_role)
            
            # Check cache first if enabled
            if use_cache:
                cached = self.cache.get_list(cache_key)
                if cached:
                    logger.debug(f"Retrieved persona list from cache: {cache_key}")
                    return cached
            
            # Build query parameters
            params = {"limit": limit, "offset": offset}
            if search:
                params["search"] = search
            if is_active is not None:
                params["is_active"] = is_active
            if erpnext_role:
                params["erpnext_role"] = erpnext_role
            
            logger.info(f"Fetching persona list with params: {params}")
            
            response = await self.api_client.get(
                endpoint=self.base_url,
                params=params
            )
            
            # Cache the result
            self.cache.set_list(cache_key, response)
            
            # Also cache individual personas
            for persona in response.get("personas", []):
                self.cache.set_persona(persona)
            
            logger.info(f"Successfully retrieved {len(response.get('personas', []))} personas")
            return response
            
        except Exception as e:
            logger.error(f"Failed to list personas: {e}")
            raise PersonaAPIError(f"Failed to retrieve personas: {str(e)}") from e
    
    async def get_persona_summary(self, persona_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get persona summary information.
        
        Args:
            persona_id: Unique persona identifier
            use_cache: Whether to use cached data if available
            
        Returns:
            Persona summary information
            
        Raises:
            PersonaNotFoundError: If persona not found
            PersonaAPIError: If retrieval fails
        """
        try:
            # Check cache first if enabled
            if use_cache:
                cached = self.cache.get_summary(persona_id)
                if cached:
                    logger.debug(f"Retrieved persona summary {persona_id} from cache")
                    return cached
            
            logger.info(f"Fetching persona summary: {persona_id}")
            
            response = await self.api_client.get(
                endpoint=f"{self.base_url}/{persona_id}/summary"
            )
            
            # Cache the result
            self.cache.set_summary(persona_id, response)
            
            logger.info(f"Successfully retrieved persona summary: {persona_id}")
            return response
            
        except self.api_client.NotFoundError as e:
            logger.warning(f"Persona {persona_id} not found for summary: {e}")
            raise PersonaNotFoundError(f"Persona {persona_id} not found") from e
        except Exception as e:
            logger.error(f"Failed to get persona summary {persona_id}: {e}")
            raise PersonaAPIError(f"Failed to retrieve persona summary: {str(e)}") from e
    
    async def validate_persona_data(self, persona_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate persona data without creating.
        
        Args:
            persona_data: Persona data to validate
            
        Returns:
            Validation results with errors, warnings, and suggestions
            
        Raises:
            PersonaAPIError: If validation request fails
        """
        try:
            logger.info("Validating persona data")
            
            response = await self.api_client.post(
                endpoint=f"{self.base_url}/validate",
                data=persona_data
            )
            
            logger.info(f"Persona validation completed: {response.get('is_valid', False)}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to validate persona data: {e}")
            raise PersonaAPIError(f"Failed to validate persona data: {str(e)}") from e
    
    async def get_persona_suggestions(self, context: str, 
                                    erpnext_modules: Optional[List[str]] = None,
                                    business_process: Optional[str] = None) -> Dict[str, Any]:
        """Get intelligent persona suggestions based on context.
        
        Args:
            context: Business context description
            erpnext_modules: Target ERPNext modules
            business_process: Business process type
            
        Returns:
            Intelligent persona suggestions
            
        Raises:
            PersonaAPIError: If suggestion request fails
        """
        try:
            logger.info(f"Getting persona suggestions for context: {context[:50]}...")
            
            request_data = {"context": context}
            if erpnext_modules:
                request_data["erpnext_modules"] = erpnext_modules
            if business_process:
                request_data["business_process"] = business_process
            
            response = await self.api_client.post(
                endpoint=f"{self.base_url}/suggestions",
                data=request_data
            )
            
            logger.info(f"Retrieved {len(response.get('suggestions', []))} persona suggestions")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get persona suggestions: {e}")
            raise PersonaAPIError(f"Failed to get persona suggestions: {str(e)}") from e
    
    async def get_persona_statistics(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get persona statistics and overview.
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            Statistics about personas and their usage
            
        Raises:
            PersonaAPIError: If statistics request fails
        """
        try:
            # Check cache first if enabled
            if use_cache:
                cached = self.cache.get_statistics()
                if cached:
                    logger.debug("Retrieved persona statistics from cache")
                    return cached
            
            logger.info("Fetching persona statistics")
            
            response = await self.api_client.get(
                endpoint=f"{self.base_url}/statistics/overview"
            )
            
            # Cache the result
            self.cache.set_statistics(response)
            
            logger.info("Successfully retrieved persona statistics")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get persona statistics: {e}")
            raise PersonaAPIError(f"Failed to retrieve persona statistics: {str(e)}") from e
    
    async def activate_persona(self, persona_id: str) -> Dict[str, Any]:
        """Activate a persona.
        
        Args:
            persona_id: Unique persona identifier
            
        Returns:
            Updated persona information
            
        Raises:
            PersonaNotFoundError: If persona not found
            PersonaAPIError: If activation fails
        """
        try:
            logger.info(f"Activating persona: {persona_id}")
            
            response = await self.api_client.post(
                endpoint=f"{self.base_url}/{persona_id}/activate"
            )
            
            # Update cache
            self.cache.set_persona(response)
            self.cache.invalidate_list_cache()
            
            logger.info(f"Successfully activated persona: {persona_id}")
            return response
            
        except self.api_client.NotFoundError as e:
            logger.warning(f"Persona {persona_id} not found for activation: {e}")
            raise PersonaNotFoundError(f"Persona {persona_id} not found") from e
        except Exception as e:
            logger.error(f"Failed to activate persona {persona_id}: {e}")
            raise PersonaAPIError(f"Failed to activate persona: {str(e)}") from e
    
    async def deactivate_persona(self, persona_id: str) -> Dict[str, Any]:
        """Deactivate a persona.
        
        Args:
            persona_id: Unique persona identifier
            
        Returns:
            Updated persona information
            
        Raises:
            PersonaNotFoundError: If persona not found
            PersonaAPIError: If deactivation fails
        """
        try:
            logger.info(f"Deactivating persona: {persona_id}")
            
            response = await self.api_client.post(
                endpoint=f"{self.base_url}/{persona_id}/deactivate"
            )
            
            # Update cache
            self.cache.set_persona(response)
            self.cache.invalidate_list_cache()
            
            logger.info(f"Successfully deactivated persona: {persona_id}")
            return response
            
        except self.api_client.NotFoundError as e:
            logger.warning(f"Persona {persona_id} not found for deactivation: {e}")
            raise PersonaNotFoundError(f"Persona {persona_id} not found") from e
        except Exception as e:
            logger.error(f"Failed to deactivate persona {persona_id}: {e}")
            raise PersonaAPIError(f"Failed to deactivate persona: {str(e)}") from e
    
    async def find_similar_personas(self, persona_id: str, 
                                  similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find personas similar to the given persona.
        
        Args:
            persona_id: Reference persona identifier
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of similar personas with similarity scores
            
        Raises:
            PersonaNotFoundError: If persona not found
            PersonaAPIError: If search fails
        """
        try:
            logger.info(f"Finding similar personas to {persona_id}")
            
            params = {"similarity_threshold": similarity_threshold}
            
            response = await self.api_client.get(
                endpoint=f"{self.base_url}/{persona_id}/similar",
                params=params
            )
            
            logger.info(f"Found {len(response)} similar personas")
            return response
            
        except self.api_client.NotFoundError as e:
            logger.warning(f"Persona {persona_id} not found for similarity search: {e}")
            raise PersonaNotFoundError(f"Persona {persona_id} not found") from e
        except Exception as e:
            logger.error(f"Failed to find similar personas for {persona_id}: {e}")
            raise PersonaAPIError(f"Failed to find similar personas: {str(e)}") from e
    
    def clear_cache(self) -> None:
        """Clear all cached persona data."""
        self.cache.clear_all()
        logger.info("Cleared persona cache")
    
    def _build_list_cache_key(self, limit: int, offset: int, 
                             search: Optional[str], is_active: Optional[bool],
                             erpnext_role: Optional[str]) -> str:
        """Build cache key for list requests."""
        key_parts = [
            f"limit:{limit}",
            f"offset:{offset}"
        ]
        
        if search:
            key_parts.append(f"search:{search}")
        if is_active is not None:
            key_parts.append(f"active:{is_active}")
        if erpnext_role:
            key_parts.append(f"role:{erpnext_role}")
        
        return "|".join(key_parts)


# Convenience functions for simpler usage
def create_persona_service(api_client: APIClient, cache_ttl_minutes: int = 30) -> PersonaService:
    """Create a persona service instance.
    
    Args:
        api_client: Base API client instance
        cache_ttl_minutes: Cache time-to-live in minutes
        
    Returns:
        Configured persona service instance
    """
    return PersonaService(api_client, cache_ttl_minutes)