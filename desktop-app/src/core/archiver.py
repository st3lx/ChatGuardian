# desktop-app/src/core/archiver.py
import importlib
import pkgutil
from pathlib import Path
from typing import List, Type

# Import our models and interface
from .models import ParsedData
from src.plugins.interface import ChatPlugin

class Archiver:
    def __init__(self):
        self.plugins = self._discover_plugins()

    def _discover_plugins(self) -> List[Type[ChatPlugin]]:
        """Dynamically find all classes that inherit from ChatPlugin."""
        discovered_plugins = []
        # Walk through all modules in the 'plugins' package
        plugins_package = "src.plugins"
        package = importlib.import_module(plugins_package)

        for _, name, ispkg in pkgutil.iter_modules(package.__path__):
            if ispkg:  # This means it's a plugin folder (like 'dummy' or 'wechat')
                try:
                    plugin_module = importlib.import_module(f"{plugins_package}.{name}")
                    # Look for a class in that module that inherits from ChatPlugin
                    for attribute_name in dir(plugin_module):
                        attribute = getattr(plugin_module, attribute_name)
                        if (isinstance(attribute, type) and
                                issubclass(attribute, ChatPlugin) and
                                attribute is not ChatPlugin):
                            discovered_plugins.append(attribute)
                            print(f"✅ Found plugin: {attribute.name}")
                except ImportError as e:
                    print(f"❌ Could not load plugin {name}: {e}")
        return discovered_plugins

    def run(self, backup_path: Path):
        """The main function that runs the entire show."""
        print(f"🔍 Starting archive process on backup: {backup_path}")
        print(f"🔌 Found {len(self.plugins)} plugins: {[p.name for p in self.plugins]}")

        # Let's just test with our DummyPlugin for now
        for plugin_class in self.plugins:
            plugin_instance = plugin_class()
            print(f"\n--- Trying {plugin_instance.name} ---")

            # 1. Find the database files
            try:
                db_paths = plugin_instance.find_data_paths(backup_path)
                print(f"   Found data paths: {db_paths}")
            except Exception as e:
                print(f"   Error finding data: {e}")
                continue

            # 2. Parse each found database
            for db_path in db_paths:
                try:
                    parsed_data: ParsedData = plugin_instance.parse_message_db(db_path)
                    print(f"   ✅ Successfully parsed data for app: {parsed_data.app_name}")
                    print(f"   Found {len(parsed_data.chats)} chats.")
                    for chat in parsed_data.chats:
                        print(f"      Chat: '{chat.chat_name}' with {len(chat.messages)} messages.")
                except Exception as e:
                    print(f"   Error parsing {db_path}: {e}")