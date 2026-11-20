"""Headless smoke test of the Streamlit UI using Streamlit's AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


def test_app_renders_and_analyzes_pasted_code():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    at.text_area(key="pasted").set_value("import os\nexec('1')\n")
    at.button[0].click().run()
    assert not at.exception
    labels = " ".join(e.label for e in at.expander)
    assert "F401" in labels and "B102" in labels


def test_app_shows_error_for_empty_input():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.button[0].click().run()
    assert any("empty" in e.value.lower() for e in at.error)
