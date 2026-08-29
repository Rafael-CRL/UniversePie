import asyncio

import pytest
from fastapi import HTTPException

from src import anki_client
from src.anki_client import strip_html


def test_strip_html_removes_tags():
    assert strip_html("<b>hello</b> world") == "hello world"


def test_strip_html_removes_sound_refs():
    assert strip_html("word [sound:audio.mp3]") == "word"


def test_strip_html_unescapes_entities():
    assert strip_html("Tom &amp; Jerry &lt;3") == "Tom & Jerry <3"


def test_strip_html_unescapes_every_entity_not_just_a_handpicked_list():
    """Regression test: a lista manual de entidades cobria cinco e deixava
    &apos; passar, então o apóstrofo do Anki chegava literal ao prompt e à
    tela ("I&apos;m so sick of your whining.").
    """
    assert strip_html("I&apos;m sick of it") == "I'm sick of it"
    assert strip_html("caf&#233; &#39;quoted&#39;") == "café 'quoted'"


def test_strip_html_turns_nbsp_into_a_regular_space():
    """html.unescape devolve U+00A0 para &nbsp;; o colapso de espaço em
    branco precisa continuar normalizando isso."""
    assert strip_html("a&nbsp;b") == "a b"


def test_strip_html_collapses_whitespace():
    assert strip_html("a   b\n\nc") == "a b c"


def test_strip_html_does_not_reintroduce_tags_from_double_encoded_entities():
    """Regression test: decoding &amp;lt;/&amp;gt; must not resurrect a real
    tag pair after the tag-stripping regex has already run once.
    """
    result = strip_html("Tom &amp;lt;b&amp;gt;bold&amp;lt;/b&amp;gt; Jerry")
    assert "<" not in result and ">" not in result
    assert result == "Tom bold Jerry"


def test_anki_invoke_raises_clear_error_when_http_client_not_initialized(monkeypatch):
    """Regression test: calling anki_invoke before anki_client.startup() ran
    (e.g. a test or script that skips the FastAPI lifespan) must raise an
    actionable RuntimeError, not an opaque AttributeError on NoneType.
    """
    monkeypatch.setattr(anki_client, "http_client", None)

    with pytest.raises(RuntimeError, match="http_client não inicializado"):
        asyncio.run(anki_client.anki_invoke("findCards"))


def _fake_cards_info(params):
    return [
        {
            "fields": {
                "Front": {"value": f"front {i}"},
                "Back": {"value": f"back {i}"},
            }
        }
        for i in params["cards"]
    ]


def test_get_card_pool_handles_deck_smaller_than_n(monkeypatch):
    """Regression test: a deck with fewer cards than n must raise the
    friendly 'insufficient cards' HTTPException, not crash inside
    random.sample with a raw ValueError.
    """
    small_deck_ids = [1, 2, 3]

    async def fake_get_card_ids():
        return small_deck_ids

    async def fake_anki_invoke(action, params=None):
        assert action == "cardsInfo"
        return _fake_cards_info(params)

    monkeypatch.setattr(anki_client, "get_card_ids", fake_get_card_ids)
    monkeypatch.setattr(anki_client, "anki_invoke", fake_anki_invoke)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(anki_client.get_card_pool(n=5))

    assert exc_info.value.status_code == 500


def test_get_card_pool_respects_multiplier_when_deck_is_large_enough(monkeypatch):
    large_deck_ids = list(range(1, 21))

    async def fake_get_card_ids():
        return large_deck_ids

    async def fake_anki_invoke(action, params=None):
        assert action == "cardsInfo"
        return _fake_cards_info(params)

    monkeypatch.setattr(anki_client, "get_card_ids", fake_get_card_ids)
    monkeypatch.setattr(anki_client, "anki_invoke", fake_anki_invoke)

    parsed_cards = asyncio.run(anki_client.get_card_pool(n=5))

    assert len(parsed_cards) == 5 * anki_client.POOL_MULTIPLIER
