import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ai_client_loads_env_independently_of_import_order(tmp_path):
    """Regression test: importing src.ai_client directly (without src.config
    having run first) must still find GEMINI_API_KEY from a .env file.
    """
    (tmp_path / ".env").write_text("GEMINI_API_KEY=test-key-not-real\n")

    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    env.pop("GEMINI_API_KEY", None)
    env.pop("GOOGLE_API_KEY", None)

    result = subprocess.run(
        [sys.executable, "-c", "from src.ai_client import ai_client; assert ai_client is not None"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
