# desktop-app/src/core/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from pathlib import Path

# This class represents a single message
@dataclass
class Message:
    timestamp: datetime
    sender: str
    content: str  # Could be text, or a description like "Image file"
    media_path: Optional[Path] = None  # The path to the image/video/file inside the backup
    media_type: Optional[str] = None  # 'image', 'video', 'file'

# This class represents a conversation (a chat or group)
@dataclass
class Chat:
    chat_id: str
    chat_name: str
    messages: List[Message]

# This is what every plugin MUST return
@dataclass
class ParsedData:
    app_name: str  # e.g., "WeChat"
    chats: List[Chat]