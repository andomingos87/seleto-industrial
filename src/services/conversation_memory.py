"""
Basic conversation memory service for storing and retrieving conversation history.

This is a basic in-memory implementation for MVP. A full implementation (TECH-008)
will use Supabase for persistence.
"""

from datetime import datetime
from typing import Dict, List, Optional

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
    In-memory conversation memory service.

    Stores conversation history keyed by normalized phone number.
    This is a basic implementation for MVP. Full persistence will be added in TECH-008.
    """

    def __init__(self):
        """Initialize conversation memory."""
        # Dictionary mapping phone -> list of messages
        self._conversations: Dict[str, List[ConversationMessage]] = {}
        # Dictionary mapping phone -> collected data
        self._lead_data: Dict[str, dict] = {}
        # Dictionary mapping phone -> question tracking (for rate control)
        # Tracks consecutive direct questions from assistant
        self._question_count: Dict[str, int] = {}

    def get_conversation_history(
        self, phone: str, max_messages: Optional[int] = None
    ) -> List[ConversationMessage]:
        """
        Get conversation history for a phone number.

        Args:
            phone: Phone number (will be normalized)
            max_messages: Maximum number of messages to return (None = all)

        Returns:
            List of conversation messages, most recent first
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            logger.warning(f"Invalid phone number: {phone}")
            return []

        messages = self._conversations.get(normalized_phone, [])
        if max_messages:
            return messages[-max_messages:]
        return messages

    def add_message(self, phone: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            phone: Phone number (will be normalized)
            role: Message role ("user" or "assistant")
            content: Message content
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            logger.warning(f"Invalid phone number: {phone}")
            return

        if normalized_phone not in self._conversations:
            self._conversations[normalized_phone] = []

        message = ConversationMessage(role=role, content=content)
        self._conversations[normalized_phone].append(message)

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

        Args:
            phone: Phone number (will be normalized)

        Returns:
            True if this is the first message, False otherwise
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return True

        return normalized_phone not in self._conversations or len(
            self._conversations[normalized_phone]
        ) == 0

    def get_lead_data(self, phone: str) -> dict:
        """
        Get collected data for a lead.

        Args:
            phone: Phone number (will be normalized)

        Returns:
            Dictionary with collected lead data
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return {}

        return self._lead_data.get(normalized_phone, {}).copy()

    def update_lead_data(self, phone: str, data: dict) -> None:
        """
        Update collected data for a lead.

        Args:
            phone: Phone number (will be normalized)
            data: Dictionary with data to update (will be merged with existing data)
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            logger.warning(f"Invalid phone number: {phone}")
            return

        if normalized_phone not in self._lead_data:
            self._lead_data[normalized_phone] = {}

        self._lead_data[normalized_phone].update(data)

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

