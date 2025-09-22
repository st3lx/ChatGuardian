# desktop-app/src/plugins/interface.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

# Import the data structure we just made
from src.core.models import ParsedData

class ChatPlugin(ABC):
    """The abstract base class that all chat app plugins must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of the app (e.g., 'WeChat', 'WhatsApp')."""
        pass

    @abstractmethod
    def find_data_paths(self, backup_path: Path) -> List[Path]:
        """
        The core function: Given a path to a backup, find the app's database files.
        Returns a list of paths to relevant database files.
        """
        pass

    @abstractmethod
    def parse_message_db(self, db_path: Path) -> ParsedData:
        """
        Parse the specific database file and extract messages, media links, contacts.
        Returns a ParsedData object, our standardized dictionary structure.
        """
        pass