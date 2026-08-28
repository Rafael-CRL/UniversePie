import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANKI_CONNECT_URL = "http://localhost:8765"
DECK_NAME = os.getenv("ANKI_DECK_NAME", "English_Series")

STATIC_DIR = Path(__file__).parent / "static"

# Pool multiplier: how many cards to fetch relative to the requested quiz count.
# A larger pool gives the AI more material to find relationships and clusters.
POOL_MULTIPLIER = 3
