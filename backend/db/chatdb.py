"""
Chat history database management using SQLite.
Stores user conversations for persistence across sessions.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class ChatDB:
    def __init__(self, db_path: str = "data/chathistory.db"):
        """Initialize chat database connection."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations TEXT,
                    is_fallback BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_chat_id 
                ON messages(chat_id)
            """)
            
            conn.commit()
    
    def create_chat(self, chat_id: str, title: str = "New Chat") -> bool:
        """Create a new chat session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO chats (id, title) VALUES (?, ?)",
                    (chat_id, title)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_chat_title(self, chat_id: str, title: str) -> bool:
        """Update chat title."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE chats SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, chat_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def add_message(
        self, 
        chat_id: str, 
        role: str, 
        content: str,
        citations: Optional[List[Dict]] = None,
        is_fallback: bool = False
    ) -> int:
        """Add a message to a chat."""
        citations_json = json.dumps(citations) if citations else None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO messages (chat_id, role, content, citations, is_fallback)
                   VALUES (?, ?, ?, ?, ?)""",
                (chat_id, role, content, citations_json, is_fallback)
            )
            
            # Update chat's updated_at
            conn.execute(
                "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (chat_id,)
            )
            
            conn.commit()
            return cursor.lastrowid
    
    def get_chat(self, chat_id: str) -> Optional[Dict]:
        """Get chat metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM chats WHERE id = ?",
                (chat_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_chat_messages(self, chat_id: str) -> List[Dict]:
        """Get all messages for a chat."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT id, role, content, citations, is_fallback, created_at
                   FROM messages 
                   WHERE chat_id = ? 
                   ORDER BY created_at ASC""",
                (chat_id,)
            )
            
            messages = []
            for row in cursor.fetchall():
                msg = dict(row)
                if msg['citations']:
                    msg['citations'] = json.loads(msg['citations'])
                messages.append(msg)
            
            return messages
    
    def get_all_chats(self, limit: int = 50) -> List[Dict]:
        """Get all chats ordered by most recent."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT id, title, created_at, updated_at 
                   FROM chats 
                   ORDER BY updated_at DESC 
                   LIMIT ?""",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat and all its messages."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear_all_chats(self) -> bool:
        """Delete all chats and messages."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM chats")
            conn.commit()
            return True
    
    def get_chat_count(self) -> int:
        """Get total number of chats."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM chats")
            return cursor.fetchone()[0]
