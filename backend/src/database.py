"""Database module for CTLChat application."""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from loguru import logger
import uuid
from datetime import datetime


class Database:
    """SQLite database manager for CTLChat."""

    def __init__(self, db_path: str = "./ctlchat.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database with schema."""
        schema_path = Path(__file__).parent.parent / "database" / "schema.sql"

        if not schema_path.exists():
            logger.warning(f"Schema file not found at {schema_path}")
            return

        with self.get_connection() as conn:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
                conn.executescript(schema_sql)
            conn.commit()

        logger.info(f"Database initialized at {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()

    # Organization operations
    def create_organization(self, org_name: str, org_id: Optional[str] = None) -> str:
        """Create a new organization.

        Args:
            org_name: Name of the organization
            org_id: Optional organization ID (generated if not provided)

        Returns:
            str: Organization ID
        """
        org_id = org_id or str(uuid.uuid4())

        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO organizations (org_id, org_name) VALUES (?, ?)",
                (org_id, org_name)
            )
            conn.commit()

        logger.info(f"Created organization: {org_id}")
        return org_id

    def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization by ID.

        Args:
            org_id: Organization ID

        Returns:
            Dict with organization data or None
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM organizations WHERE org_id = ?",
                (org_id,)
            ).fetchone()

            return dict(row) if row else None

    # User operations
    def create_user(
        self,
        org_id: str,
        username: str,
        email: str,
        full_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Create a new user.

        Args:
            org_id: Organization ID
            username: Username
            email: Email address
            full_name: Full name (optional)
            user_id: Optional user ID (generated if not provided)

        Returns:
            str: User ID
        """
        user_id = user_id or str(uuid.uuid4())

        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO users (user_id, org_id, username, email, full_name)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, org_id, username, email, full_name)
            )
            conn.commit()

        logger.info(f"Created user: {user_id}")
        return user_id

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            Dict with user data or None
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email.

        Args:
            email: Email address

        Returns:
            Dict with user data or None
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            return dict(row) if row else None

    # Conversation operations
    def create_conversation(
        self,
        user_id: str,
        org_id: str,
        title: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """Create a new conversation.

        Args:
            user_id: User ID
            org_id: Organization ID
            title: Conversation title (optional)
            conversation_id: Optional conversation ID (generated if not provided)

        Returns:
            str: Conversation ID
        """
        conversation_id = conversation_id or str(uuid.uuid4())

        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO conversations (conversation_id, user_id, org_id, title)
                   VALUES (?, ?, ?, ?)""",
                (conversation_id, user_id, org_id, title)
            )
            conn.commit()

        logger.info(f"Created conversation: {conversation_id}")
        return conversation_id

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Dict with conversation data or None
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,)
            ).fetchone()

            return dict(row) if row else None

    def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get conversations for a user.

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List of conversation dicts
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM conversations
                   WHERE user_id = ?
                   ORDER BY updated_at DESC
                   LIMIT ? OFFSET ?""",
                (user_id, limit, offset)
            ).fetchall()

            return [dict(row) for row in rows]

    def update_conversation_title(self, conversation_id: str, title: str):
        """Update conversation title.

        Args:
            conversation_id: Conversation ID
            title: New title
        """
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE conversations SET title = ? WHERE conversation_id = ?",
                (title, conversation_id)
            )
            conn.commit()

        logger.info(f"Updated conversation title: {conversation_id}")

    def delete_conversation(self, conversation_id: str):
        """Delete a conversation and all its messages.

        Args:
            conversation_id: Conversation ID
        """
        with self.get_connection() as conn:
            conn.execute(
                "DELETE FROM conversations WHERE conversation_id = ?",
                (conversation_id,)
            )
            conn.commit()

        logger.info(f"Deleted conversation: {conversation_id}")

    # Message operations
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> str:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role ('user', 'assistant', or 'system')
            content: Message content
            metadata: Optional JSON metadata
            message_id: Optional message ID (generated if not provided)

        Returns:
            str: Message ID
        """
        message_id = message_id or str(uuid.uuid4())

        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO messages (message_id, conversation_id, role, content, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (message_id, conversation_id, role, content, metadata)
            )
            conn.commit()

        logger.debug(f"Added message to conversation {conversation_id}")
        return message_id

    def get_conversation_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all messages in a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Optional limit on number of messages

        Returns:
            List of message dicts ordered by creation time
        """
        with self.get_connection() as conn:
            if limit:
                rows = conn.execute(
                    """SELECT * FROM messages
                       WHERE conversation_id = ?
                       ORDER BY created_at ASC
                       LIMIT ?""",
                    (conversation_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM messages
                       WHERE conversation_id = ?
                       ORDER BY created_at ASC""",
                    (conversation_id,)
                ).fetchall()

            return [dict(row) for row in rows]

    def get_conversation_with_messages(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation with all its messages.

        Args:
            conversation_id: Conversation ID

        Returns:
            Dict with conversation data and messages or None
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        messages = self.get_conversation_messages(conversation_id)
        conversation['messages'] = messages

        return conversation
