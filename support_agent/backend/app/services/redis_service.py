import json
import logging
from typing import List, Dict, Optional
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        self.host = settings.REDIS_HOST
        self.port = settings.REDIS_PORT
        self.db = settings.REDIS_DB
        self.client = None
        self.is_connected = False
        self._fallback_memory: Dict[str, List[str]] = {}
        self.connect()

    def connect(self) -> None:
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                socket_timeout=2.0,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            self.is_connected = True
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {str(e)}. Falling back to in-memory cache.")
            self.is_connected = False
            self.client = None

    def get_session_history(self, session_key: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Retrieves the last `limit` messages from the chat session history.
        """
        key = f"chat_history:{session_key}"
        if self.is_connected and self.client:
            try:
                raw_messages = self.client.lrange(key, 0, limit - 1)
                return [json.loads(msg) for msg in raw_messages]
            except Exception as e:
                logger.error(f"Redis get_session_history failed: {str(e)}")
        
        # Fallback to local memory
        fallback_list = self._fallback_memory.get(key, [])
        return [json.loads(msg) for msg in fallback_list[:limit]]

    def add_session_message(self, session_key: str, role: str, content: str, limit: int = 20) -> None:
        """
        Appends a message to the chat session history and prunes old items.
        """
        key = f"chat_history:{session_key}"
        message_data = json.dumps({"role": role, "content": content})
        
        if self.is_connected and self.client:
            try:
                # Store message (newest on left)
                self.client.lpush(key, message_data)
                # Trim list to keep only the recent limit
                self.client.ltrim(key, 0, limit - 1)
                return
            except Exception as e:
                logger.error(f"Redis add_session_message failed: {str(e)}")
        
        # Fallback to local memory
        if key not in self._fallback_memory:
            self._fallback_memory[key] = []
        self._fallback_memory[key].insert(0, message_data)
        self._fallback_memory[key] = self._fallback_memory[key][:limit]

    def add_recent_search(self, user_id: str, query: str, limit: int = 5) -> None:
        """
        Adds a search query to the user's recent searches list.
        """
        key = f"recent_searches:{user_id}"
        if self.is_connected and self.client:
            try:
                # Remove exact duplicate if it exists to refresh position
                self.client.lrem(key, 0, query)
                # Push to top of list
                self.client.lpush(key, query)
                # Prune list
                self.client.ltrim(key, 0, limit - 1)
                return
            except Exception as e:
                logger.error(f"Redis add_recent_search failed: {str(e)}")

        # Fallback to local memory
        if key not in self._fallback_memory:
            self._fallback_memory[key] = []
        if query in self._fallback_memory[key]:
            self._fallback_memory[key].remove(query)
        self._fallback_memory[key].insert(0, query)
        self._fallback_memory[key] = self._fallback_memory[key][:limit]

    def get_recent_searches(self, user_id: str) -> List[str]:
        """
        Retrieves the list of recent search queries.
        """
        key = f"recent_searches:{user_id}"
        if self.is_connected and self.client:
            try:
                return self.client.lrange(key, 0, -1)
            except Exception as e:
                logger.error(f"Redis get_recent_searches failed: {str(e)}")
        
        return self._fallback_memory.get(key, [])

    def clear_session_history(self, session_key: str) -> None:
        key = f"chat_history:{session_key}"
        if self.is_connected and self.client:
            try:
                self.client.delete(key)
                return
            except Exception as e:
                logger.error(f"Redis delete session key failed: {str(e)}")
        
        if key in self._fallback_memory:
            del self._fallback_memory[key]

redis_service = RedisService()
