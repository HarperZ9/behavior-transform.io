#!/usr/bin/env python3
"""session-start-maintain -- SessionStart hook.

Every session launch triggers this hook in three steps:

  1. Background workstation maintenance -- launch the local maintenance
     worker as a detached process.
     Skipped if a run completed within the last STALE_HOURS hours.

  2. Memory maintenance -- run the local memory helper when available.

  3. Context maintenance -- run the local context helper when available.

All steps fail open; a broken sub-tool must never break session start.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

_TOOLS = Path.home() / "AGENTS" / "warden_shell" / "tools"
_BATCH = _TOOLS / "batch_modulate_memory.py"
_CONTEXT_HELPER = _TOOLS / "safe_context_helper.py"
_MAINTENANCE_WORKER = _TOOLS / "workstation_calibrate.py"

_MEMORY_DIR = Path.home() / ".claude" / "projects" / "C--Users-Zain" / "memory"
_STATUS_FILE = Path.home() / ".warden-safe-cache" / "workstation-maintenance.json"
_LEGACY_STATUS_FILE = Path.home() / ".warden-safe-cache" / "workstation-calibration.json"

STALE_HOURS = 4  # Re-launch background maintenance if last run was older than this.


def _maintenance_is_stale() -> bool:
    status_file = _status_file()
    if status_file is None:
        return True
    try:
        age_hours = (time.time() - status_file.stat().st_mtime) / 3600
        return age_hours > STALE_HOURS
    except OSError:
        return True


def _status_file() -> Path | None:
    for path in (_STATUS_FILE, _LEGACY_STATUS_FILE):
        if path.is_file():
            return path
    return None


def _launch_background_maintenance() -> str:
    """Launch the workstation maintenance worker as a detached process."""
    if not _MAINTENANCE_WORKER.is_file():
        return "worker script not found"
    try:
        subprocess.Popen(
            [sys.executable, str(_MAINTENANCE_WORKER), str(Path.home())],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        return "launched"
    except (OSError, subprocess.SubprocessError) as exc:
        return f"error: {exc}"


def _run_sync(args: list[str], timeout: int = 60) -> str:
    try:
        result = subprocess.run(
            args, capture_output=True, timeout=timeout, cwd=str(Path.home()),
        )
        return result.stdout.decode("utf-8", "replace").strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def _summary_line(out: str, keywords: tuple) -> str:
    for ln in out.splitlines():
        if any(k in ln for k in keywords):
            return ln.strip()
    return ""


def main() -> int:
    # --- Local direct path (see _warden_cleanroom.py) ---
    import os as _cr_os, sys as _cr_sys
    _cr_sys.path.insert(0, _cr_os.path.dirname(_cr_os.path.abspath(__file__)))
    try:
        from _warden_cleanroom import cleanroom_active as _cr_active
        if _cr_active("session-start-calibrate")[0]:
            return 0
    except Exception:
        pass
    try:
        sys.stdin.read()
    except Exception:
        pass

    lines: list[str] = []

    # Step 1: background workstation maintenance.
    if _maintenance_is_stale():
        status = _launch_background_maintenance()
        lines.append(f"[session-start] workstation maintenance: {status} (bg)")
    else:
        try:
            status_file = _status_file()
            info = json.loads(status_file.read_text(encoding="utf-8")) if status_file else {}
            completed = info.get("completed_at", "?")
            total = info.get("total_scanned", "?")
            fixed = info.get("fixed", 0)
            lines.append(
                f"[session-start] workstation maintenance: current "
                f"(last: {completed}, {total} files, {fixed} updated)"
            )
        except Exception:
            lines.append("[session-start] workstation maintenance: status unknown")

    # Step 2: memory files maintenance.
    if _BATCH.is_file() and _MEMORY_DIR.is_dir():
        out = _run_sync([sys.executable, str(_BATCH), str(_MEMORY_DIR)])
        if out:
            summary = _summary_line(out, ("files |",))
            if summary:
                lines.append(f"[session-start] memory: {summary}")

    # Step 3: session context maintenance.
    if _CONTEXT_HELPER.is_file():
        out = _run_sync([sys.executable, str(_CONTEXT_HELPER), "--ctx-fix"])
        if out:
            summary = _summary_line(out, ("updated", "clean", "context", "error"))
            if summary:
                lines.append(f"[session-start] ctx-fix: {summary}")

    # Status lines are internal telemetry only. No output is emitted.
    _ = lines

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
