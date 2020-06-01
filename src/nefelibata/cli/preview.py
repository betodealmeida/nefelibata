# -*- coding: utf-8 -*-
import logging
import os
import socketserver
from http.server import SimpleHTTPRequestHandler
from pathlib import Path

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def run(root: Path, port: int = 8000) -> None:
    """Run a local HTTP server.
    """
    logging.info("Previewing weblog")

    build = root / "build"
    os.chdir(build)

    with socketserver.TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        logging.info(f"Running HTTP server on port {port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("Exiting")
            httpd.shutdown()
