import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ContentDB:
    def __init__(self, db_path: str = "content.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database with content table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS content (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        content TEXT NOT NULL,
                        citations TEXT NOT NULL,
                        generated_at TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON content(session_id)")
                conn.commit()
                logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"DB init failed: {e}")

    def save_content(self, session_id: str, content_data: Dict[str, Any]):
        """Save generated content for a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO content 
                    (id, session_id, topic, content, citations, generated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    content_data["id"],
                    session_id,
                    content_data["topic"],
                    content_data["content"],
                    json.dumps(content_data["citations"]),
                    content_data["generated_at"].isoformat(),
                    json.dumps(content_data["metadata"])
                ))
                conn.commit()
                logger.info(f"Content saved: {content_data['id']}")
        except Exception as e:
            logger.error(f"Save content failed: {e}")

    def get_session_content(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all content for a specific session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, topic, content, citations, generated_at, metadata
                    FROM content
                    WHERE session_id = ?
                    ORDER BY created_at DESC
                """, (session_id,))
                results = []
                for row in cursor.fetchall():
                    try:
                        results.append({
                            "id": row[0],
                            "topic": row[1],
                            "content": row[2],
                            "citations": json.loads(row[3]),
                            "generated_at": datetime.fromisoformat(row[4]),
                            "metadata": json.loads(row[5])
                        })
                    except Exception as e_inner:
                        logger.warning(f"Skipping row due to parse error: {e_inner}, row={row}")
                return results
        except Exception as e:
            logger.error(f"Fetch session content failed: {e}")
            return []

    def get_all_content(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all content from all sessions, supports pagination"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, topic, content, citations, generated_at, metadata
                    FROM content
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, skip))
                results = []
                for row in cursor.fetchall():
                    try:
                        results.append({
                            "id": row[0],
                            "topic": row[1],
                            "content": row[2],
                            "citations": json.loads(row[3]),
                            "generated_at": datetime.fromisoformat(row[4]),
                            "metadata": json.loads(row[5])
                        })
                    except Exception as e_inner:
                        logger.warning(f"Skipping row due to parse error: {e_inner}, row={row}")
                return results
        except Exception as e:
            logger.error(f"Fetch all content failed: {e}")
            return []
