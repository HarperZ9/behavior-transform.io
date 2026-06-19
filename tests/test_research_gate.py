import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / "hooks"
TOOLS = REPO / "tools"

_CALIBRATION_HOOKS = [
    "safe-exec-redirect.py",
    "safe-read-redirect.py",
    "safe-fetch-redirect.py",
    "safe-search-redirect.py",
    "safe-input-calibrate.py",
    "post-tool-calibrate.py",
    "session-start-calibrate.py",
]


def _run(hook: str, payload: dict, mode: str) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "WARDEN_IO_CHANNEL": mode,
        "BEHAVIOR_TRANSFORM_TOOLS": str(TOOLS),
    }
    return subprocess.run(
        [sys.executable, str(HOOKS / hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def test_all_hooks_pass_through_in_research_mode():
    """Every calibration hook exits 0 with no stderr output in research mode."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "echo hello"},
        "tool_response": "hello",
    }
    for hook in _CALIBRATION_HOOKS:
        result = _run(hook, payload, "off")
        assert result.returncode == 0, f"{hook} returned {result.returncode} in research mode"
        assert result.stderr == "", f"{hook} wrote stderr in research mode: {result.stderr!r}"
