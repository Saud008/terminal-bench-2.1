"""JSON-RPC client for term-lsp over stdio Content-Length framing."""

from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Any


class LspClient:
    def __init__(self, binary: str | Path) -> None:
        self.binary = str(binary)
        self.proc: subprocess.Popen[bytes] | None = None
        self._id = 0
        self._responses: dict[int, Any] = {}
        self._lock = threading.Lock()
        self._reader: threading.Thread | None = None

    def start(self) -> None:
        self.proc = subprocess.Popen(
            [self.binary],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert self.proc.stdout is not None
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self.request("initialize", {"processId": 1, "rootUri": None, "capabilities": {}})
        self.notify("initialized", {})

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            try:
                self.request("shutdown", {})
                self.notify("exit", {})
            finally:
                self.proc.terminate()
                self.proc.wait(timeout=5)

    def _read_loop(self) -> None:
        assert self.proc and self.proc.stdout
        stdout = self.proc.stdout
        while True:
            headers: dict[str, str] = {}
            while True:
                line = stdout.readline()
                if not line:
                    return
                if line in (b"\r\n", b"\n"):
                    break
                if b":" in line:
                    k, v = line.decode("utf-8").split(":", 1)
                    headers[k.strip().lower()] = v.strip()
            length = int(headers.get("content-length", "0"))
            if length == 0:
                continue
            body = stdout.read(length)
            if not body:
                return
            msg = json.loads(body)
            if "id" in msg:
                with self._lock:
                    self._responses[int(msg["id"])] = msg

    def _write(self, payload: dict[str, Any]) -> None:
        assert self.proc and self.proc.stdin
        body = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self.proc.stdin.write(header + body)
        self.proc.stdin.flush()

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": params})

    def request(self, method: str, params: dict[str, Any], timeout: float = 30.0) -> Any:
        with self._lock:
            self._id += 1
            req_id = self._id
        self._write({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if req_id in self._responses:
                    return self._responses.pop(req_id).get("result")
            time.sleep(0.01)
        raise TimeoutError(f"no response for {method}")

    def did_open(self, uri: str, text: str, version: int = 0) -> None:
        self.notify(
            "textDocument/didOpen",
            {"textDocument": {"uri": uri, "languageId": "doclint", "version": version, "text": text}},
        )

    def did_change(self, uri: str, version: int, changes: list[dict[str, Any]]) -> None:
        self.notify(
            "textDocument/didChange",
            {"textDocument": {"uri": uri, "version": version}, "contentChanges": changes},
        )

    def did_close(self, uri: str) -> None:
        self.notify("textDocument/didClose", {"textDocument": {"uri": uri}})

    def export_snapshot(self, uri: str) -> dict[str, Any]:
        return self.request(
            "workspace/executeCommand",
            {"command": "doclint.exportSnapshot", "arguments": [uri]},
        )
