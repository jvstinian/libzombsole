# tests/test_gym_env_imports.py
import pytest
from tests.helpers import not_raises


def test_imports():
    with not_raises(ImportError):
        import zombsole.gym_env
        import zombsole.game

