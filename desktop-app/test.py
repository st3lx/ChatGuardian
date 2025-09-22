# desktop-app/test.py
import sys
import logging
from pathlib import Path

# Setup basic logging to see the debug messages
logging.basicConfig(level=logging.INFO)

sys.path.append(str(Path(__file__).parent / "src"))

from src.core.archiver import Archiver

def main():
    print("🧪 Testing ChatGuardian Core + WeChat Plugin...")
    archiver = Archiver()

    # Replace this with the ACTUAL path to your iOS backup
    # On macOS: ~/Library/Application Support/MobileSync/Backup/
    # On Windows: \Users\[USERNAME]\AppData\Roaming\Apple Computer\MobileSync\Backup\
    real_backup_path = Path("/Users/YourUserName/Library/Application Support/MobileSync/Backup/abcd1234.../") 

    if real_backup_path.exists():
        archiver.run(real_backup_path)
    else:
        print(f"⚠️  Backup path not found: {real_backup_path}")
        print("Please update 'real_backup_path' in test.py to point to your iOS backup folder.")

if __name__ == "__main__":
    main()