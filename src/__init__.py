from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


SRC_DIR = Path(__file__).parent
PLAYER_NOTES_DIR = SRC_DIR.parent / "player_notes"

# clear the player notes directory
if PLAYER_NOTES_DIR.exists():
    for file in PLAYER_NOTES_DIR.iterdir():
        file.unlink()
    PLAYER_NOTES_DIR.rmdir()

PLAYER_NOTES_DIR.mkdir(exist_ok=True)
