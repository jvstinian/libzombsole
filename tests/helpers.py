# tests/helpers.py
from contextlib import contextmanager
import pytest


@contextmanager
def not_raises(exception):
    try:
        yield
    except exception as ex:
        raise pytest.fail("DID RAISE {0}".format(ex))

