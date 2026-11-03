"""In-process mock of the IcePanel REST endpoints that push_to_icepanel.py uses.

Only the shape the script depends on is modelled: each create returns an
object with a fresh id under the key the script unwraps (``modelObject``,
``modelConnection``, ``diagram``, ``flow``), and the root-object lookup
returns a single root. Every request is recorded so tests can assert on the
exact payloads the script sent.

Usage::

    with MockIcePanel() as server:
        run_script(env={"ICEPANEL_API_BASE_URL": server.base_url, ...})
        put = server.requests_matching("PUT", "/content")[0]
        api_id = server.id_of("objects", "API Server")
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT_ID = "root-0"

# path suffix -> (response key the script unwraps, id prefix)
_CREATE_ENDPOINTS = {
    "/model/objects": ("modelObject", "obj"),
    "/model/connections": ("modelConnection", "conn"),
    "/diagrams": ("diagram", "diag"),
    "/flows": ("flow", "flow"),
}


class MockIcePanel:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        # (kind, name) -> id, e.g. ("objects", "API Server") -> "obj-3"
        self.ids: dict[tuple[str, str], str] = {}
        self._counter = 0
        self._lock = threading.Lock()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    # -- lifecycle -----------------------------------------------------------

    def __enter__(self) -> "MockIcePanel":
        mock = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):  # keep test output clean
                pass

            def _reply(self, obj: dict, status: int = 200) -> None:
                body = json.dumps(obj).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _read_body(self):
                length = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(length)) if length else None

            def _record(self, body=None) -> None:
                mock.requests.append(
                    {
                        "method": self.command,
                        "path": self.path,
                        "body": body,
                        "authorization": self.headers.get("Authorization"),
                    }
                )

            def do_GET(self):
                self._record()
                if "filter[type]=root" in self.path:
                    return self._reply({"modelObjects": [{"id": ROOT_ID}]})
                self._reply({})

            def do_POST(self):
                body = self._read_body()
                self._record(body)
                for suffix, (key, prefix) in _CREATE_ENDPOINTS.items():
                    if self.path.endswith(suffix):
                        new_id = mock._create(suffix.rsplit("/", 1)[-1], body, prefix)
                        return self._reply({key: {"id": new_id}})
                self._reply({"error": f"unexpected POST {self.path}"}, status=404)

            def do_PUT(self):
                body = self._read_body()
                self._record(body)
                self._reply({})

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        assert self._server is not None
        self._server.shutdown()
        self._server.server_close()

    # -- helpers -------------------------------------------------------------

    @property
    def base_url(self) -> str:
        assert self._server is not None
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def _create(self, kind: str, body: dict, prefix: str) -> str:
        with self._lock:
            self._counter += 1
            new_id = f"{prefix}-{self._counter}"
            self.ids[(kind, body.get("name", ""))] = new_id
            return new_id

    def id_of(self, kind: str, name: str) -> str:
        """Id the mock handed out for a created thing.

        kind is one of "objects", "connections", "diagrams", "flows".
        """
        return self.ids[(kind, name)]

    def requests_matching(self, method: str, path_suffix: str) -> list[dict]:
        return [
            r for r in self.requests
            if r["method"] == method and r["path"].endswith(path_suffix)
        ]
