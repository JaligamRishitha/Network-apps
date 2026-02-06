"""
PM Workflow Caching Service
Performance optimization through caching of frequently accessed data
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json


class PMWorkflowCacheService:
    """
    Simple in-memory cache for PM Workflow data.
    In production, would use Redis or Memcached.
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache service.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if datetime.utcnow() > entry['expires_at']:
            del self._cache[key]
            return None
        
        return entry['value']
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.utcnow()
        }
    
    def delete(self, key: str) -> None:
        """Delete value from cache"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Pattern to match (simple prefix matching)
            
        Returns:
            Number of keys invalidated
        """
        keys_to_delete = [
            key for key in self._cache.keys()
            if key.startswith(pattern)
        ]
        
        for key in keys_to_delete:
            del self._cache[key]
        
        return len(keys_to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values()
            if datetime.utcnow() > entry['expires_at']
        )
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries
        }


# Global cache instance
_cache_instance: Optional[PMWorkflowCacheService] = None


def get_cache() -> PMWorkflowCacheService:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PMWorkflowCacheService()
    return _cache_instance


# Cache key generators
def order_cache_key(order_number: str) -> str:
    """Generate cache key for order"""
    return f"order:{order_number}"


def order_list_cache_key(filters: Dict[str, Any]) -> str:
    """Generate cache key for order list"""
    filter_str = json.dumps(filters, sort_keys=True)
    return f"order_list:{filter_str}"


def material_cache_key(material_number: str) -> str:
    """Generate cache key for material master data"""
    return f"material:{material_number}"


def technician_cache_key(technician_id: str) -> str:
    """Generate cache key for technician data"""
    return f"technician:{technician_id}"


def cost_center_cache_key(cost_center: str) -> str:
    """Generate cache key for cost center"""
    return f"cost_center:{cost_center}"


# Cache invalidation helpers
def invalidate_order_cache(order_number: str) -> None:
    """Invalidate all cache entries for an order"""
    cache = get_cache()
    cache.delete(order_cache_key(order_number))
    cache.invalidate_pattern("order_list:")  # Invalidate all list queries


def invalidate_material_cache(material_number: str) -> None:
    """Invalidate material cache"""
    cache = get_cache()
    cache.delete(material_cache_key(material_number))
