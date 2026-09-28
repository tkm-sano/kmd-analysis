"""Verify relocated documents remain reachable through the public portal."""
from __future__ import annotations

import importlib.util
import json
import threading
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[3]


def test_old_document_urls_redirect_to_existing_content() -> None:
    spec = importlib.util.spec_from_file_location("portal_relocations", ROOT / "research_portal/serve.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    moves = json.loads((ROOT / "docs/ROOT_FILE_RELOCATIONS.json").read_text())["moves"]
    server = HTTPServer(("127.0.0.1", 0), module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection(*server.server_address, timeout=5)
    try:
        for item in moves:
            assert not (ROOT / item["old"]).exists()
            content = (ROOT / item["new"]).read_bytes()
            for method in ("GET", "HEAD"):
                connection.request(method, "/artifact/" + quote(item["old"]))
                response = connection.getresponse()
                assert response.status == 308
                target = response.getheader("Location")
                assert target == "/artifact/" + quote(item["new"])
                assert response.read() == b""
                connection.request(method, target)
                response = connection.getresponse()
                assert response.status == 200
                assert response.read() == (content if method == "GET" else b"")
        connection.request("GET", "/artifact/../../etc/passwd")
        response = connection.getresponse()
        assert response.status == 404
        response.read()
    finally:
        connection.close()
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
