from pathlib import Path

from fastapi.testclient import TestClient

from src.main import INDEX_HTML, app

STATIC_DIR = Path(__file__).resolve().parents[1] / "src" / "static"


def test_index_html_is_read_once_at_import_time():
    assert INDEX_HTML == (STATIC_DIR / "index.html").read_text(encoding="utf-8")


def test_root_serves_the_cached_index_html():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.text == INDEX_HTML
