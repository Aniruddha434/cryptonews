"""
Database schema fix script.
Adds missing tables and columns.
"""

import sqlite3
import logging
from config import DATABASE_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_database():
    """Fix database schema issues."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Add command_logs table
        logger.info("Creating command_logs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                command TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 1,
                error_message TEXT
            )
        """)

        # Check if chat_id column exists in command_logs table
        logger.info("Checking command_logs table schema...")
        cursor.execute("PRAGMA table_info(command_logs)")
        cmd_columns = [col[1] for col in cursor.fetchall()]

        if 'chat_id' not in cmd_columns:
            logger.info("Adding chat_id column to command_logs table...")
            cursor.execute("""
                ALTER TABLE command_logs ADD COLUMN chat_id INTEGER
            """)
        
        # Check if last_active column exists in users table
        logger.info("Checking users table schema...")
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'last_active' not in columns:
            logger.info("Adding last_active column to users table...")
            cursor.execute("""
                ALTER TABLE users ADD COLUMN last_active TIMESTAMP
            """)
            # Update existing rows with current timestamp
            cursor.execute("""
                UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE last_active IS NULL
            """)
        
        # Create indexes
        logger.info("Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_command_logs_user ON command_logs(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_command_logs_timestamp ON command_logs(timestamp)
        """)
        
        conn.commit()
        logger.info("✅ Database schema fixed successfully!")
        
    except Exception as e:
        logger.error(f"Error fixing database: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    fix_database()

