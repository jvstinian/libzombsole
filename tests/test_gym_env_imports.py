# tests/test_gym_env_imports.py
from contextlib import contextmanager
import pytest


@contextmanager
def not_raises(exception):
    try:
        yield
    except exception as ex:
        raise pytest.fail("DID RAISE {0}".format(ex))


def test_imports():
    with not_raises(ImportError):
        import zombsole.gym_env
        import zombsole.game

