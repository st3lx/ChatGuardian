# desktop-app/src/plugins/dummy/parser.py
from pathlib import Path
from typing import List
from datetime import datetime

# Import the interface and data models
from src.plugins.interface import ChatPlugin
from src.core.models import ParsedData, Chat, Message

class DummyPlugin(ChatPlugin):

    @property
    def name(self) -> str:
        return "DummyChat"

    def find_data_paths(self, backup_path: Path) -> List[Path]:
        # This dummy plugin doesn't need a real file.
        # Let's just return a fake path to show it works.
        fake_db_path = backup_path / "dummy" / "fake_database.db"
        return [fake_db_path]

    def parse_message_db(self, db_path: Path) -> ParsedData:
        # Let's create some fake data that matches our ParsedData structure!
        fake_messages = [
            Message(
                timestamp=datetime.now(),
                sender="ChatGuardian Bot",
                content="This is a test message from the DummyPlugin! The system is working!",
            ),
            Message(
                timestamp=datetime.now(),
                sender="ChatGuardian Bot",
                content="This is a second message.",
                media_path=Path("/fake/path/to/image.jpg"),
                media_type="image"
            ),
        ]

        fake_chat = Chat(chat_id="123", chat_name="Test Chat", messages=fake_messages)

        # Return the standardized data
        return ParsedData(app_name=self.name, chats=[fake_chat])