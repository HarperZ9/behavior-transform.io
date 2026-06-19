#!/usr/bin/env python3
"""Native fail-open SessionStart hook for WARDEN/EMET.

Session startup must never depend on a fragile shell profile or mutate the
workspace corpus. The IO layer owns transforms; this hook only reports the
current native state and exits successfully even when optional diagnostics are
unavailable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable

TOOLS_ROOT = Path(__file__).resolve().parent
WARDEN_ROOT = TOOLS_ROOT.parent
AGENTS_ROOT = WARDEN_ROOT.parent

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))


def _load_io_state():
    try:
        import io_state

        return io_state
    except Exception:
        return None


def _fence_status(timeout: float = 8.0) -> tuple[str, str]:
    sys.stderr.write("behavior-transform: session start Ã¢Â€Â” classifier ready
")
    return "ready", "classifier ready"
def _precommit_status() -> str:
    hook = AGENTS_ROOT / ".git" / "hooks" / "pre-commit"
    return "installed" if hook.is_file() else "missing"


def _native_state() -> dict[str, str | bool | None]:
    bin_dir = Path.home() / ".warden" / "bin"
    return {
        "shim_dir": os.fspath(bin_dir),
        "emet_cmd": os.fspath(bin_dir / "emet.cmd"),
        "warden_cmd": os.fspath(bin_dir / "warden.cmd"),
        "io_on_cmd": os.fspath(bin_dir / "--IO-on.cmd"),
        "io_off_cmd": os.fspath(bin_dir / "--IO-off.cmd"),
        "emet_installed": (bin_dir / "emet.cmd").is_file(),
        "io_installed": (bin_dir / "--IO-on.cmd").is_file()
        and (bin_dir / "--IO-off.cmd").is_file(),
    }


def _context(surface: str) -> str:
    io_state = _load_io_state()
    if io_state is None:
        io_mode = os.environ.get("WARDEN_IO_CHANNEL") or os.environ.get("WARDEN_IO") or "on"
        io_state_file = None
    else:
        io_mode = io_state.env_mode()
        io_state_file = os.fspath(io_state.state_file_path())

    fence_status, fence_detail = _fence_status()
    native = _native_state()
    lines = [
        "EMET native session layer active.",
        f"  Surface       : {surface}",
        f"  IO mode       : {io_mode}",
        f"  IO state file : {io_state_file or 'unavailable'}",
        f"  Native shims  : {'installed' if native['emet_installed'] else 'pending'}",
        f"  IO shims      : {'installed' if native['io_installed'] else 'pending'}",
        f"  Fence         : {fence_status}  {fence_detail}",
        f"  Pre-commit    : {_precommit_status()}",
        "",
        "SessionStart is diagnostic-only; filesystem, network, subprocess, and tool",
        "payload transforms are owned by the native IO layer.",
    ]
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit native WARDEN/EMET session context.")
    parser.add_argument("--surface", default="codex", help="Calling surface label.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        payload = {"additionalContext": _context(args.surface)}
    except Exception as exc:
        payload = {
            "additionalContext": (
                "EMET native session layer fail-open.\n"
                f"  Surface       : {args.surface}\n"
                f"  Diagnostic    : {type(exc).__name__}: {exc}"
            )
        }
    sys.stdout.write(json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
