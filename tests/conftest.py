"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


@pytest.fixture
def examples_dir():
    """Return the examples directory path."""
    return EXAMPLES_DIR


@pytest.fixture
def tmp_output(tmp_path):
    """Return a temporary output directory path."""
    out_dir = tmp_path / "output"
    out_dir.mkdir(exist_ok=True)
    return out_dir


@pytest.fixture
def bonares_json():
    """Return path to bonares example JSON file."""
    return EXAMPLES_DIR / "example_bonares.json"


@pytest.fixture
def edal_json():
    """Return path to edal example JSON file."""
    return EXAMPLES_DIR / "example_edal.json"


@pytest.fixture
def openagrar_json():
    """Return path to openagrar example JSON file."""
    return EXAMPLES_DIR / "example_openagrar.json"


@pytest.fixture
def plabipd_json():
    """Return path to plabipd example JSON file."""
    return EXAMPLES_DIR / "example_plabipd.json"


@pytest.fixture
def bonares_json():
    """Return path to bonares example JSON file."""
    return EXAMPLES_DIR / "bonares.json"

@pytest.fixture
def edal_json():
    """Return path to edal example JSON file."""
    return EXAMPLES_DIR / "edal.json"

@pytest.fixture
def openagrar_json():
    """Return path to openagrar example JSON file."""
    return EXAMPLES_DIR / "openagrar.json"

@pytest.fixture
def plabipd_json():
    """Return path to plabipd example JSON file."""
    return EXAMPLES_DIR / "plabipd.json"

@pytest.fixture
def publisso_json():
    """Return path to publisso example JSON file."""
    return EXAMPLES_DIR / "publisso.json"