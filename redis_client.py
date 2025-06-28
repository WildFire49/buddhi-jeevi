import os
import json
import redis
from typing import Any, Dict, List, Optional, Union


class RedisClient:
    """
    A simple Redis client wrapper for set and get operations.
    Supports JSON serialization/deserialization and configurable expiration.
    """
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 6379, 
        db: int = 0, 
        password: Optional[str] = None,
        default_ttl: int = 3600  # Default TTL of 1 hour
    ):
        """
        Initialize the Redis client.
        
        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
            password: Redis password if required
            default_ttl: Default time-to-live for keys in seconds
        """
        # Get configuration from environment variables if available
        redis_host = os.getenv("REDIS_HOST", host)
        redis_port = int(os.getenv("REDIS_PORT", port))
        redis_db = int(os.getenv("REDIS_DB", db))
        redis_password = os.getenv("REDIS_PASSWORD", password)
        
        # Connect to Redis
        self.client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=False  # Keep as bytes for proper serialization handling
        )
        self.default_ttl = int(os.getenv("REDIS_DEFAULT_TTL", default_ttl))
        
        # Test connection
        try:
            self.client.ping()
            print(f"Connected to Redis at {redis_host}:{redis_port}/{redis_db}")
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}")
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None, 
        serialize: bool = True
    ) -> bool:
        """
        Set a value in Redis with optional TTL.
        
        Args:
            key: The key to store the value under
            value: The value to store
            ttl: Time-to-live in seconds (uses default_ttl if None)
            serialize: Whether to serialize the value as JSON
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Serialize value if needed
            if serialize and not isinstance(value, (str, bytes)):
                value = json.dumps(value)
            
            # Convert string to bytes if needed
            if isinstance(value, str):
                value = value.encode('utf-8')
                
            # Set the value with expiration
            expiry = ttl if ttl is not None else self.default_ttl
            return self.client.setex(key, expiry, value)
        except Exception as e:
            print(f"Error setting key {key}: {e}")
            return False
    
    def get(
        self, 
        key: str, 
        deserialize: bool = True,
        default: Any = None
    ) -> Any:
        """
        Get a value from Redis.
        
        Args:
            key: The key to retrieve
            deserialize: Whether to deserialize the value from JSON
            default: Default value to return if key doesn't exist
            
        Returns:
            The value if found, otherwise the default value
        """
        try:
            value = self.client.get(key)
            
            if value is None:
                return default
                
            # Deserialize if requested
            if deserialize:
                try:
                    # Decode bytes to string first
                    value_str = value.decode('utf-8')
                    return json.loads(value_str)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # If not valid JSON or not valid UTF-8, return as is
                    return value
            
            return value
        except Exception as e:
            print(f"Error getting key {key}: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: The key to delete
            
        Returns:
            bool: True if key was deleted, False otherwise
        """
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Error deleting key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: The key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Error checking if key {key} exists: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get the remaining time-to-live of a key in seconds.
        
        Args:
            key: The key to check
            
        Returns:
            int: TTL in seconds, -1 if key has no TTL, -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            print(f"Error getting TTL for key {key}: {e}")
            return -2


# Singleton instance for easy import
_redis_client = None

def get_redis_client() -> RedisClient:
    """
    Get or create a singleton Redis client instance.
    
    Returns:
        RedisClient: The Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


# Convenience functions
def set_value(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    Set a value in Redis.
    
    Args:
        key: The key to store the value under
        value: The value to store
        ttl: Time-to-live in seconds
        
    Returns:
        bool: True if successful, False otherwise
    """
    return get_redis_client().set(key, value, ttl)


def get_value(key: str, default: Any = None) -> Any:
    """
    Get a value from Redis.
    
    Args:
        key: The key to retrieve
        default: Default value to return if key doesn't exist
        
    Returns:
        The value if found, otherwise the default value
    """
    return get_redis_client().get(key, default=default)


def delete_key(key: str) -> bool:
    """
    Delete a key from Redis.
    
    Args:
        key: The key to delete
        
    Returns:
        bool: True if key was deleted, False otherwise
    """
    return get_redis_client().delete(key)


if __name__ == "__main__":
    # Example usage
    client = get_redis_client()
    
    # Set a string value
    client.set("test_string", "Hello Redis!")
    
    # Set a JSON value
    client.set("test_json", {"name": "Redis", "type": "database"})
    
    # Get values
    print(client.get("test_string"))  # "Hello Redis!"
    print(client.get("test_json"))    # {"name": "Redis", "type": "database"}
    
    # Using convenience functions
    set_value("user:123", {"id": 123, "name": "John Doe"})
    user = get_value("user:123")
    print(user)  # {"id": 123, "name": "John Doe"}
