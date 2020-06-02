from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from nefelibata.cli.preview import run

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_run(mocker, fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)
    fs.create_dir(root / "build")

    mock_socketserver = MagicMock()
    mocker.patch("nefelibata.cli.preview.socketserver", mock_socketserver)

    run(root)

    mock_socketserver.TCPServer.assert_called_with(("", 8000), SimpleHTTPRequestHandler)
    mock_socketserver.TCPServer.return_value.__enter__.assert_called_once()
    mock_socketserver.TCPServer.return_value.__enter__.return_value.serve_forever.assert_called_once()


def test_run_keyboard_interrupt(mocker, fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)
    fs.create_dir(root / "build")

    mock_socketserver = MagicMock()
    mock_socketserver.TCPServer.return_value.__enter__.return_value.serve_forever.side_effect = (
        KeyboardInterrupt()
    )
    mocker.patch("nefelibata.cli.preview.socketserver", mock_socketserver)

    run(root)

    mock_socketserver.TCPServer.assert_called_with(("", 8000), SimpleHTTPRequestHandler)
    mock_socketserver.TCPServer.return_value.__enter__.assert_called_once()
    mock_socketserver.TCPServer.return_value.__enter__.return_value.shutdown.assert_called_once()
