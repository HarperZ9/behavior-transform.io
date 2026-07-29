"""behavior-transform.io MCP server — stdio JSON-RPC, stdlib only.

Exposes the IO-boundary safety surface (status, doctor, demo) as MCP tools so
any MCP-speaking harness (ChatGPT, Claude Code, OpenCode, ZCode) can install
behavior-transform natively and read its receipts. Matches the ecosystem's
zero-dependency stdio pattern (see opsec/scripts/aleph_mcp.py). The host is
flywheel; this is the connector every harness loads.

Run:  python tools/behavior_transform_mcp.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from behavior_flagship import demo_envelope, doctor_envelope, status_envelope

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "behavior-transform"
SERVER_VERSION = "0.1.0"

_NO_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}


def _tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "name": "behavior_transform.status",
            "description": "Report the IO-boundary surface: which operations require a receipt "
                           "(write, exec, fetch, model-boundary) and the current mode.",
            "inputSchema": _NO_ARGS,
        },
        {
            "name": "behavior_transform.doctor",
            "description": "Readiness of the boundary layer: hooks present, console script wired, "
                           "receipt path healthy. Returns MATCH / DRIFT / UNVERIFIABLE.",
            "inputSchema": _NO_ARGS,
        },
        {
            "name": "behavior_transform.demo",
            "description": "A self-contained demonstration of a boundary receipt, offline, no side effects.",
            "inputSchema": _NO_ARGS,
        },
    ]


def call_tool(name: str, args: dict[str, Any]) -> str:
    if name == "behavior_transform.status":
        return json.dumps(status_envelope(), indent=2, ensure_ascii=False)
    if name == "behavior_transform.doctor":
        return json.dumps(doctor_envelope(), indent=2, ensure_ascii=False)
    if name == "behavior_transform.demo":
        return json.dumps(demo_envelope(), indent=2, ensure_ascii=False)
    raise ValueError(f"unknown tool: {name}")


def handle_request(req: dict[str, Any]) -> dict[str, Any] | None:
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": _tool_defs()}}
    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            text = call_tool(name, args)
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text", "text": text}]}}
        except Exception as exc:  # surface errors as tool content, never crash the server
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text", "text": f"error: {exc}"}],
                               "isError": True}}
    if rid is None:
        return None  # unknown notification
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


def serve(stdin=None, stdout=None) -> int:
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle_request(req)
        if resp is not None:
            stdout.write(json.dumps(resp) + "\n")
            stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(serve())
