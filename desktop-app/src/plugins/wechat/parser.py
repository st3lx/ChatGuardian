# desktop-app/src/plugins/wechat/parser.py
import sqlite3
import plistlib
from pathlib import Path
from typing import List, Optional
import logging

# Import the core structure we built
from src.plugins.interface import ChatPlugin
from src.core.models import ParsedData, Chat, Message

# Set up logging to see what's happening (very useful for debugging)
logger = logging.getLogger(__name__)

class WeChatPlugin(ChatPlugin):

    @property
    def name(self) -> str:
        return "WeChat"

    def find_data_paths(self, backup_path: Path) -> List[Path]:
        """
        Hunts for the WeChat database inside an iOS backup.
        iOS backups have a obfuscated folder structure, but we can crack it.
        """
        logger.info(f"🔍 Searching for WeChat data in backup: {backup_path}")
        found_paths = []

        # 1. Check if this is an iOS backup
        # iOS backups have a manifest.plist file and a bunch of named folders
        manifest_file = backup_path / "manifest.plist"
        if not manifest_file.exists():
            logger.warning("This doesn't look like an iOS backup (no manifest.plist). Android support TBD.")
            return found_paths

        # 2. Parse the manifest to get app list and mapping
        try:
            with open(manifest_file, 'rb') as f:
                manifest = plistlib.load(f)
        except Exception as e:
            logger.error(f"Failed to parse manifest.plist: {e}")
            return found_paths

        # 3. Look for WeChat's app ID in the manifest
        # WeChat's bundle ID is 'com.tencent.xin'
        wechat_app_id = 'com.tencent.xin'
        applications = manifest.get('Applications', {})

        if wechat_app_id not in applications:
            logger.warning("WeChat (com.tencent.xin) not found in backup.")
            return found_paths

        # 4. Get the WeChat-specific folder ID (the obfuscated name)
        wechat_folder_id = applications[wechat_app_id]
        wechat_app_domain = f"AppDomain-{wechat_app_id}"
        wechat_data_path = backup_path / wechat_folder_id / wechat_app_domain

        if not wechat_data_path.exists():
            logger.warning(f"WeChat data path not found: {wechat_data_path}")
            return found_paths

        logger.info(f"✅ Found WeChat data at: {wechat_data_path}")

        # 5. Now look for the specific database file within the WeChat folder
        # The path can vary by version, but this is a common location
        possible_db_paths = [
            wechat_data_path / "Documents" / "MM.sqlite",
            wechat_data_path / "Documents" / "MM.sqlite" / "MM.sqlite",
            wechat_data_path / "Library" / "WeChatPrivate" / "MM.sqlite",
            wechat_data_path / "ChatStorage.sqlite", # Another common name
        ]

        for db_path in possible_db_paths:
            if db_path.exists():
                logger.info(f"✅ Found WeChat database: {db_path}")
                found_paths.append(db_path)
                # Let's just take the first one we find for now
                break
        else:
            logger.warning("Could not find WeChat database file in expected locations.")

        return found_paths

    def parse_message_db(self, db_path: Path) -> ParsedData:
        """
        The magic happens here. We crack open the WeChat SQLite database
        and extract messages in our standard format.
        """
        logger.info(f"🗃️ Opening WeChat database: {db_path}")
        chats = []

        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) # 'ro' for read-only
            conn.row_factory = sqlite3.Row  # This allows us to access columns by name
            cursor = conn.cursor()

            # 1. First, let's just see what tables are in there (for exploration)
            logger.info("Exploring database tables...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                logger.debug(f"Found table: {table['name']}")

            # 2. Try to get chats. Table name might be 'Chat' or something similar.
            # This is where the real reverse-engineering begins!
            try:
                # Common table name for chats
                cursor.execute("SELECT * FROM Chat LIMIT 5;")
                chat_rows = cursor.fetchall()
                logger.info(f"Found {len(chat_rows)} chat records.")

                # Let's create a simple chat for each one
                for row in chat_rows:
                    # This is HIGHLY dependent on the WeChat version.
                    # You'll need to inspect the database to find the right column names.
                    chat_name = row.get('displayname') or row.get('UserName') or f"Chat_{row.get('id', 'Unknown')}"
                    chat_id = row.get('id') or row.get('UserName') or 'Unknown'

                    # 3. Now try to get messages for this chat
                    # The message table is often named 'Message' or 'Chat_<somehash>'
                    try:
                        # This query will need to be adapted based on your database schema!
                        cursor.execute(
                            "SELECT * FROM Message WHERE chatId = ? ORDER BY createTime ASC;",
                            (chat_id,)
                        )
                        message_rows = cursor.fetchall()
                        messages = []

                        for msg_row in message_rows:
                            # Extract message content. This is the hacky part!
                            # The content might be in 'content', 'message', 'msgContent' etc.
                            content = msg_row.get('content', '')
                            sender = msg_row.get('sender', 'Unknown')
                            # WeChat timestamps are often in milliseconds since epoch
                            timestamp = msg_row.get('createTime', 0) / 1000  # Convert to seconds

                            # Create a Message object
                            message = Message(
                                timestamp=timestamp,
                                sender=sender,
                                content=content,
                                # media_path and media_type would require more complex logic
                                # to find the actual files in the backup.
                            )
                            messages.append(message)

                        # Create a Chat object for this conversation
                        chat = Chat(chat_id=chat_id, chat_name=chat_name, messages=messages)
                        chats.append(chat)
                        logger.info(f"Parsed chat '{chat_name}' with {len(messages)} messages.")

                    except sqlite3.Error as e:
                        logger.error(f"Error fetching messages for chat {chat_id}: {e}")
                        continue

            except sqlite3.Error as e:
                logger.error(f"Error reading from Chat table: {e}. Table name might be different.")
                # Fallback: create at least one chat with a warning message
                fallback_chat = Chat(
                    chat_id="error",
                    chat_name="Error Parsing Chats",
                    messages=[Message(timestamp=0, sender="System", content=f"Database error: {e}")]
                )
                chats = [fallback_chat]

        except sqlite3.Error as e:
            logger.error(f"Failed to open database {db_path}: {e}")
            # Return empty data but don't crash
            fallback_chat = Chat(
                chat_id="error",
                chat_name="Failed to open database",
                messages=[Message(timestamp=0, sender="System", content=f"Failed to open DB: {e}")]
            )
            chats = [fallback_chat]

        finally:
            if 'conn' in locals():
                conn.close()

        # Return the data in the standard format
        return ParsedData(app_name=self.name, chats=chats)