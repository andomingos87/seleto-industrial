"""
Conversation memory service for storing and retrieving conversation history.

This service provides persistence via Supabase (TECH-008) with in-memory caching
for performance. Messages are also synced to Chatwoot for visual interface.
"""

from datetime import datetime
from typing import Dict, List, Optional

from src.services.chatwoot_sync import sync_message_to_chatwoot
from src.services.conversation_persistence import (
    get_context_from_supabase,
    get_messages_from_supabase,
    save_context_to_supabase,
    save_message_to_supabase,
)
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone

logger = get_logger(__name__)


class ConversationMessage:
    """Represents a single message in a conversation."""

    def __init__(
        self,
        role: str,  # "user" or "assistant"
        content: str,
        timestamp: Optional[datetime] = None,
    ):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


class ConversationMemory:
    """
    Conversation memory service with Supabase persistence and Chatwoot sync.

    Stores conversation history keyed by normalized phone number.
    Uses Supabase for persistence (TECH-008) with in-memory caching for performance.
    Messages are also synced to Chatwoot for visual interface.
    """

    def __init__(self):
        """Initialize conversation memory."""
        # Dictionary mapping phone -> list of messages (cache)
        self._conversations: Dict[str, List[ConversationMessage]] = {}
        # Dictionary mapping phone -> collected data (cache)
        self._lead_data: Dict[str, dict] = {}
        # Dictionary mapping phone -> question tracking (for rate control)
        # Tracks consecutive direct questions from assistant
        self._question_count: Dict[str, int] = {}
        # Track which conversations have been loaded from Supabase
        self._loaded_from_supabase: Dict[str, bool] = {}

    def get_conversation_history(
        self, phone: str, max_messages: Optional[int] = None
    ) -> List[ConversationMessage]:
        """
        Get conversation history for a phone number.

        Loads from Supabase if not already cached, then returns from cache.

        Args:
            phone: Phone number (will be normalized)
            max_messages: Maximum number of messages to return (None = all)

        Returns:
            List of conversation messages, oldest first
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            logger.warning(f"Invalid phone number: {phone}")
            return []

        # Load from Supabase if not already loaded
        if normalized_phone not in self._loaded_from_supabase:
            self._load_from_supabase(normalized_phone)

        messages = self._conversations.get(normalized_phone, [])
        if max_messages:
            return messages[-max_messages:]  # Return last N messages
        return messages

    def _load_from_supabase(self, phone: str) -> None:
        """
        Load conversation history from Supabase into cache.

        Args:
            phone: Normalized phone number
        """
        try:
            # Get messages from Supabase
            supabase_messages = get_messages_from_supabase(phone)
            if supabase_messages:
                # Convert to ConversationMessage objects
                messages = []
                for msg_dict in supabase_messages:
                    timestamp = datetime.fromisoformat(msg_dict["timestamp"].replace("Z", "+00:00"))
                    messages.append(
                        ConversationMessage(
                            role=msg_dict["role"],
                            content=msg_dict["content"],
                            timestamp=timestamp,
                        )
                    )
                self._conversations[phone] = messages
                logger.debug(
                    "Loaded conversation history from Supabase",
                    extra={"phone": phone, "message_count": len(messages)},
                )

            # Get context from Supabase
            context = get_context_from_supabase(phone)
            if context:
                self._lead_data[phone] = context
                logger.debug(
                    "Loaded context from Supabase",
                    extra={"phone": phone, "context_keys": list(context.keys())},
                )

            self._loaded_from_supabase[phone] = True
        except Exception as e:
            logger.error(
                "Failed to load from Supabase",
                extra={"phone": phone, "error": str(e)},
                exc_info=True,
            )
            # Initialize empty if load fails
            if phone not in self._conversations:
                self._conversations[phone] = []
            if phone not in self._lead_data:
                self._lead_data[phone] = {}
            self._loaded_from_supabase[phone] = True

    def add_message(self, phone: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Persists to Supabase and syncs to Chatwoot (non-blocking).

        Args:
            phone: Phone number (will be normalized)
            role: Message role ("user" or "assistant")
            content: Message content
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            logger.warning(f"Invalid phone number: {phone}")
            return

        # Load from Supabase if not already loaded
        if normalized_phone not in self._loaded_from_supabase:
            self._load_from_supabase(normalized_phone)

        if normalized_phone not in self._conversations:
            self._conversations[normalized_phone] = []

        message = ConversationMessage(role=role, content=content)
        self._conversations[normalized_phone].append(message)

        # Persist to Supabase (synchronous, but fast)
        save_message_to_supabase(normalized_phone, role, content)

        # Sync to Chatwoot (asynchronous, non-blocking)
        sync_message_to_chatwoot(normalized_phone, role, content)

        logger.debug(
            f"Message added to conversation",
            extra={
                "phone": normalized_phone,
                "role": role,
                "message_length": len(content),
                "total_messages": len(self._conversations[normalized_phone]),
            },
        )

    def is_first_message(self, phone: str) -> bool:
        """
        Check if this is the first message from this phone number.

        Loads from Supabase if not already cached.

        Args:
            phone: Phone number (will be normalized)

        Returns:
            True if this is the first message, False otherwise
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return True

        # Load from Supabase if not already loaded
        if normalized_phone not in self._loaded_from_supabase:
            self._load_from_supabase(normalized_phone)

        return normalized_phone not in self._conversations or len(
            self._conversations[normalized_phone]
        ) == 0

    def get_lead_data(self, phone: str) -> dict:
        """
        Get collected data for a lead.

        Loads from Supabase if not already cached.

        Args:
            phone: Phone number (will be normalized)

        Returns:
            Dictionary with collected lead data
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return {}

        # Load from Supabase if not already loaded
        if normalized_phone not in self._loaded_from_supabase:
            self._load_from_supabase(normalized_phone)

        return self._lead_data.get(normalized_phone, {}).copy()

    def update_lead_data(self, phone: str, data: dict) -> None:
        """
        Update collected data for a lead.

        Updates cache and persists to Supabase.

        Args:
            phone: Phone number (will be normalized)
            data: Dictionary with data to update (will be merged with existing data)
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            logger.warning(f"Invalid phone number: {phone}")
            return

        # Load from Supabase if not already loaded
        if normalized_phone not in self._loaded_from_supabase:
            self._load_from_supabase(normalized_phone)

        if normalized_phone not in self._lead_data:
            self._lead_data[normalized_phone] = {}

        # Merge with existing data
        self._lead_data[normalized_phone].update(data)

        # Persist to Supabase
        save_context_to_supabase(normalized_phone, self._lead_data[normalized_phone])

        logger.debug(
            f"Lead data updated",
            extra={
                "phone": normalized_phone,
                "updated_fields": list(data.keys()),
            },
        )

    def get_messages_for_llm(self, phone: str, max_messages: int = 20) -> List[dict]:
        """
        Get conversation messages formatted for LLM API.

        Args:
            phone: Phone number (will be normalized)
            max_messages: Maximum number of messages to return

        Returns:
            List of message dictionaries in format {"role": "...", "content": "..."}
        """
        messages = self.get_conversation_history(phone, max_messages=max_messages)
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def get_question_count(self, phone: str) -> int:
        """
        Get the count of consecutive direct questions from assistant.

        Args:
            phone: Phone number (will be normalized)

        Returns:
            Number of consecutive questions (0 if none)
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return 0
        return self._question_count.get(normalized_phone, 0)

    def increment_question_count(self, phone: str) -> None:
        """
        Increment the count of consecutive direct questions.

        Args:
            phone: Phone number (will be normalized)
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return
        self._question_count[normalized_phone] = self._question_count.get(normalized_phone, 0) + 1

    def reset_question_count(self, phone: str) -> None:
        """
        Reset the count of consecutive direct questions (when user responds).

        Args:
            phone: Phone number (will be normalized)
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return
        self._question_count[normalized_phone] = 0


# Global conversation memory instance
conversation_memory = ConversationMemory()

