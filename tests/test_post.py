# -*- coding: utf-8 -*-

import pytest
from dateutil.parser import ParserError
from nefelibata.post import jinja2_formatdate

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_jinja2_formatdate():
    assert jinja2_formatdate(0, "%Y-%m-%d") == "1969-12-31"
    with pytest.raises(ParserError):
        jinja2_formatdate("invalid", "%Y-%m-%d")
