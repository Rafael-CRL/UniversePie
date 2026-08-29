import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANKI_CONNECT_URL = "http://localhost:8765"
DECK_NAME = os.getenv("ANKI_DECK_NAME", "English_Series")

STATIC_DIR = Path(__file__).parent / "static"

# Provedor de IA. Ver src/providers.py para a lista completa e os nomes das
# variáveis de chave de cada um. Modelo vazio = padrão do provedor.
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()
AI_MODEL = os.getenv("AI_MODEL", "").strip()
AI_TIMEOUT_S = float(os.getenv("AI_TIMEOUT_S", "120"))
# Usados só pelos provedores 'ollama' e 'custom'.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
AI_BASE_URL = os.getenv("AI_BASE_URL", "").strip()

# Pool multiplier: how many cards to fetch relative to the requested quiz count.
# A larger pool gives the AI more material to find relationships and clusters.
POOL_MULTIPLIER = 3
