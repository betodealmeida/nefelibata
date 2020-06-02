# -*- coding: utf-8 -*-
import logging
import os
import socketserver
from http.server import SimpleHTTPRequestHandler
from pathlib import Path

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def run(root: Path, port: int = 8000) -> None:
    """Run a local HTTP server.
    """
    _logger.info("Previewing weblog")

    build = root / "build"
    os.chdir(build)

    with socketserver.TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        _logger.info(f"Running HTTP server on port {port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            _logger.info("Exiting")
            httpd.shutdown()
