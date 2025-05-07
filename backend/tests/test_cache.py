import pytest
import time
from app.core.cache import SimpleCache, cache


def test_cache_set_get():
    """Test setting and getting values from the cache"""
    # Arrange
    test_cache = SimpleCache()
    key = "test_key"
    value = "test_value"
    ttl = 10  # seconds
    
    # Act - Set a value
    test_cache.set(key, value, ttl)
    
    # Assert - Get returns the correct value
    assert test_cache.get(key) == value


def test_cache_ttl_expiration():
    """Test that cached values expire after their TTL"""
    # Arrange
    test_cache = SimpleCache()
    key = "expiring_key"
    value = "expiring_value"
    ttl = 1  # very short TTL (1 second)
    
    # Act - Set a value with short TTL
    test_cache.set(key, value, ttl)
    
    # Assert - Value exists initially
    assert test_cache.get(key) == value
    
    # Wait for TTL to expire
    time.sleep(1.1)
    
    # Assert - Value should be gone after TTL
    assert test_cache.get(key) is None


def test_cache_delete():
    """Test deleting values from the cache"""
    # Arrange
    test_cache = SimpleCache()
    key = "delete_key"
    value = "delete_value"
    
    # Set up cache with a value
    test_cache.set(key, value, 60)
    assert test_cache.get(key) == value
    
    # Act
    test_cache.delete(key)
    
    # Assert
    assert test_cache.get(key) is None


def test_cache_clear():
    """Test clearing all values from the cache"""
    # Arrange
    test_cache = SimpleCache()
    key1 = "key1"
    key2 = "key2"
    
    # Set multiple values
    test_cache.set(key1, "value1", 60)
    test_cache.set(key2, "value2", 60)
    assert test_cache.get(key1) == "value1"
    assert test_cache.get(key2) == "value2"
    
    # Act
    test_cache.clear()
    
    # Assert
    assert test_cache.get(key1) is None
    assert test_cache.get(key2) is None


def test_cache_get_nonexistent():
    """Test getting a nonexistent key returns None"""
    # Arrange
    test_cache = SimpleCache()
    
    # Act & Assert
    assert test_cache.get("nonexistent_key") is None


def test_cache_get_stats():
    """Test getting cache statistics"""
    # Arrange
    test_cache = SimpleCache()
    
    # Add some items
    test_cache.set("key1", "value1", 60)
    test_cache.set("key2", "value2", 60)
    test_cache.set("expired_key", "value3", 0)  # Expired immediately
    
    # Act
    stats = test_cache.get_stats()
    
    # Assert
    assert "total_items" in stats
    assert "active_items" in stats
    assert "expired_items" in stats
    assert stats["total_items"] >= 2  # At least the non-expired items


def test_global_cache_instance():
    """Test that the global cache instance exists and works"""
    # Arrange
    key = "global_test"
    value = "global_value"
    
    # Act
    cache.set(key, value, 10)
    
    # Assert
    assert cache.get(key) == value
    
    # Clean up
    cache.delete(key) 