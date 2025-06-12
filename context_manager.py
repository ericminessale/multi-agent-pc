"""
Context Manager for PC Builder Demo

Provides database-backed state management for sharing context between agents.
Based on SignalWire SDK best practices.
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from signalwire_agents.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CustomerContext:
    """Data structure for storing customer context between agent transfers"""
    call_id: str
    customer_name: Optional[str] = None
    need_type: Optional[str] = None
    basic_info: Optional[str] = None
    agent_path: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CustomerContext':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class DatabaseContextManager:
    """
    Database-backed context manager for production use.
    Uses SQLite by default but can be adapted for other databases.
    """
    def __init__(self, db_path: str = "pc_builder_context.db", ttl_hours: int = 24):
        self.db_path = db_path
        self.ttl_hours = ttl_hours
        self._init_database()
        logger.info(f"Initialized database context manager at {db_path}")
    
    def _init_database(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_contexts (
                    call_id TEXT PRIMARY KEY,
                    context_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            # Create index for efficient cleanup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON customer_contexts(expires_at)
            """)
            
            conn.commit()
    
    def save_context(self, context: CustomerContext) -> bool:
        """Save customer context to database"""
        try:
            context.updated_at = datetime.now()
            expires_at = datetime.now() + timedelta(hours=self.ttl_hours)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO customer_contexts 
                    (call_id, context_data, updated_at, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    context.call_id,
                    json.dumps(context.to_dict()),
                    context.updated_at,
                    expires_at
                ))
                conn.commit()
            
            logger.info(f"Saved context for call {context.call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving context: {e}")
            return False
    
    def get_context(self, call_id: str) -> Optional[CustomerContext]:
        """Retrieve customer context from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT context_data FROM customer_contexts
                    WHERE call_id = ? AND expires_at > ?
                """, (call_id, datetime.now()))
                
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    context = CustomerContext.from_dict(data)
                    logger.info(f"Retrieved context for call {call_id}")
                    return context
                
            logger.info(f"No context found for call {call_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return None
    
    def delete_context(self, call_id: str) -> bool:
        """Delete context from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM customer_contexts WHERE call_id = ?", (call_id,))
                conn.commit()
            
            logger.info(f"Deleted context for call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting context: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """Clean up expired contexts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM customer_contexts WHERE expires_at <= ?",
                    (datetime.now(),)
                )
                count = cursor.rowcount
                conn.commit()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired contexts")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up contexts: {e}")
            return 0


# For backward compatibility or simpler use cases
class InMemoryContextManager:
    """
    Simple in-memory context manager for development/testing.
    Data is lost when the process restarts.
    """
    def __init__(self):
        self.storage = {}
        self.ttl_hours = 1
        logger.info("Using in-memory context manager (development mode)")
    
    def save_context(self, context: CustomerContext) -> bool:
        """Save context in memory"""
        try:
            context.updated_at = datetime.now()
            self.storage[context.call_id] = context
            logger.info(f"Saved context for call {context.call_id}")
            
            # Clean up old entries
            self._cleanup_expired()
            return True
            
        except Exception as e:
            logger.error(f"Error saving context: {e}")
            return False
    
    def get_context(self, call_id: str) -> Optional[CustomerContext]:
        """Retrieve context from memory"""
        context = self.storage.get(call_id)
        
        if context:
            # Check if expired
            age = datetime.now() - context.created_at
            if age.total_seconds() > self.ttl_hours * 3600:
                del self.storage[call_id]
                logger.info(f"Context for call {call_id} has expired")
                return None
                
            logger.info(f"Retrieved context for call {call_id}")
            return context
            
        logger.info(f"No context found for call {call_id}")
        return None
    
    def delete_context(self, call_id: str) -> bool:
        """Delete context from memory"""
        if call_id in self.storage:
            del self.storage[call_id]
            logger.info(f"Deleted context for call {call_id}")
            return True
        return False
    
    def _cleanup_expired(self):
        """Remove expired entries from memory"""
        now = datetime.now()
        expired = []
        
        for call_id, context in self.storage.items():
            age = now - context.created_at
            if age.total_seconds() > self.ttl_hours * 3600:
                expired.append(call_id)
        
        for call_id in expired:
            del self.storage[call_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired contexts")


# Factory function to create appropriate manager
def create_context_manager(use_database: bool = True) -> Any:
    """
    Factory function to create the appropriate context manager.
    
    Args:
        use_database: If True, use database-backed storage. If False, use in-memory.
    
    Returns:
        Context manager instance
    """
    if use_database:
        db_path = os.getenv("CONTEXT_DB_PATH", "pc_builder_context.db")
        ttl_hours = int(os.getenv("CONTEXT_TTL_HOURS", "24"))
        return DatabaseContextManager(db_path, ttl_hours)
    else:
        return InMemoryContextManager() 