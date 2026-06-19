#!/usr/bin/env python3
"""post-tool-capture -- PostToolUse hook.

Captures tool results from all tools (Bash, PowerShell, Grep, MCP tools,
Agent, etc.) for local handling.

Flow:
  1. Parse tool_response from the JSON payload.
  2. Extract text (handles str / dict / list shapes).
  3. Run the local text helper when available.
  4. Exit silently.

PostToolUse payload shape:
  {
    "session_id": "...",
    "hook_event_name": "PostToolUse",
    "tool_name": "Bash",
    "tool_input": {...},
    "tool_response": "..." | {...} | [...]
  }
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_CONTEXT_MODULATE = Path.home() / "AGENTS" / "warden_shell" / "tools" / "context_modulate.py"

# Cap captured output to avoid overwhelming local handling.
_MAX_CHARS = 40_000


def _extract_text(tool_response) -> str:
    if tool_response is None:
        return ""
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, (list, tuple)):
        return "\n".join(str(item) for item in tool_response)
    if isinstance(tool_response, dict):
        for key in ("output", "content", "stdout", "text", "result"):
            val = tool_response.get(key)
            if isinstance(val, str):
                return val
            if isinstance(val, list):
                return "\n".join(str(v) for v in val)
        return json.dumps(tool_response, ensure_ascii=False)
    return str(tool_response)


def _modulate(text: str) -> tuple[str, bool]:
    """Run the local text helper. Returns (text, changed)."""
    if not _CONTEXT_MODULATE.is_file():
        return text, False
    try:
        result = subprocess.run(
            [sys.executable, str(_CONTEXT_MODULATE), "--vocab-only"],
            input=text.encode("utf-8", "replace"),
            capture_output=True,
            timeout=20,
            cwd=str(Path.home()),
        )
        if result.returncode != 0:
            return text, False
        modulated = result.stdout.decode("utf-8", "replace")
        return modulated, modulated != text
    except (subprocess.SubprocessError, OSError):
        return text, False


def _gate() -> bool:
    """Return True (caller should sys.exit(0)) when mode is research/academic."""
    import os
    from pathlib import Path

    bt = os.environ.get("BEHAVIOR_TRANSFORM_TOOLS", "").strip()
    _tools = (
        Path(bt)
        if bt and Path(bt).is_dir()
        else Path(__file__).resolve().parents[1] / "tools"
    )
    if str(_tools) not in sys.path:
        sys.path.insert(0, str(_tools))
    try:
        from io_state import env_mode  # type: ignore[import]
        return env_mode() == "off"
    except Exception:
        return False  # fail open


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    if _gate():
        return 0

    # --- Local test direct path (see _warden_cleanroom.py) ---
    import os as _cr_os, sys as _cr_sys
    _cr_sys.path.insert(0, _cr_os.path.dirname(_cr_os.path.abspath(__file__)))
    try:
        from _warden_cleanroom import cleanroom_active as _cr_active, write_gap_journal as _cr_journal
        _active, _tag_required = _cr_active("post-tool-calibrate")
        if _active:
            if _tag_required:
                _cr_journal("post-tool-calibrate", data)
            return 0
    except Exception:
        pass

    tool_name = data.get("tool_name", "")

    raw_text = _extract_text(data.get("tool_response"))
    if not raw_text.strip():
        return 0

    if len(raw_text) > _MAX_CHARS:
        raw_text = raw_text[:_MAX_CHARS] + f"\n[... output capped at {_MAX_CHARS} chars ...]"

    _modulated, _changed = _modulate(raw_text)
    # Local handling only; no additional context is emitted.
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        sys.stderr.write(f"post-tool-calibrate hook error: {exc}\n")
        sys.exit(0)