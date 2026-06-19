import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _src(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def test_no_warden_in_channel_router():
    assert "warden_shell" not in _src("tools/channel_router.py")


def test_no_warden_in_text_rules():
    assert "warden_shell" not in _src("tools/text_rules.py")


def test_no_warden_in_safe_input():
    assert "warden_shell" not in _src("tools/safe_input.py")


def test_no_warden_in_mcp_calibrate():
    assert "warden_shell" not in _src("tools/mcp_calibrate.py")
    assert "context_modulate" not in _src("tools/mcp_calibrate.py")


def test_no_prefire_gate_in_io_channel():
    src = _src("tools/io_channel.py")
    assert "universal_prefire_gate" not in src
    assert "warden_shell" not in src


def test_no_aup_evasion_in_session_start():
    assert "aup_evasion" not in _src("tools/session_start.py")


def test_no_warden_in_safe_search_hook():
    src = _src("hooks/safe-search-redirect.py")
    assert "warden_shell" not in src
    assert "C:/Users" not in src


def test_no_warden_in_safe_fetch_hook():
    assert "warden_shell" not in _src("hooks/safe-fetch-redirect.py")


def test_no_warden_in_safe_exec_hook():
    assert "warden_shell" not in _src("hooks/safe-exec-redirect.py")
