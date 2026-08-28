from src.anki_client import strip_html


def test_strip_html_removes_tags():
    assert strip_html("<b>hello</b> world") == "hello world"


def test_strip_html_removes_sound_refs():
    assert strip_html("word [sound:audio.mp3]") == "word"


def test_strip_html_unescapes_entities():
    assert strip_html("Tom &amp; Jerry &lt;3") == "Tom & Jerry <3"


def test_strip_html_collapses_whitespace():
    assert strip_html("a   b\n\nc") == "a b c"
