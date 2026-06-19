import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import argparse
import pytest
from classifier import _ci


def test_fence_check_returns_dict():
    """fence_check returns a dict."""
    result = _ci.fence_check(include_tier2=False)
    assert isinstance(result, dict)
    assert "fence_pass" in result


def test_fence_check_dict_keys():
    """fence_check result contains expected keys."""
    result = _ci.fence_check(include_tier2=False)
    assert "policy" in result
    assert "tier1_action" in result
    assert "total_t1" in result
    assert "total_t2" in result


def test_probe_cmd_returns_dict():
    """probe_cmd returns a dict."""
    result = _ci.probe_cmd()
    assert isinstance(result, dict)
    assert "ready" in result


def test_probe_cmd_has_stages():
    """probe_cmd result contains stages."""
    result = _ci.probe_cmd()
    assert "stages" in result
    assert isinstance(result["stages"], list)
    assert "stages_total" in result
    assert "stages_passed" in result


def test_status_cmd_returns_dict():
    """status_cmd returns a dict."""
    result = _ci.status_cmd()
    assert isinstance(result, dict)
    assert "layer" in result


def test_status_cmd_has_version():
    """status_cmd result contains version info."""
    result = _ci.status_cmd()
    assert "version" in result
    assert "active_policy" in result


def test_hook_install_returns_dict(tmp_path):
    """hook_install returns a dict."""
    hook_path = tmp_path / "pre-commit"
    result = _ci.hook_install(hook_path)
    assert isinstance(result, dict)
    assert "status" in result or "error" in result


def test_hook_install_creates_file(tmp_path):
    """hook_install creates the hook file."""
    hook_path = tmp_path / "pre-commit"
    result = _ci.hook_install(hook_path)
    assert result["status"] == "installed"
    assert hook_path.exists()


def test_hook_install_idempotent(tmp_path):
    """hook_install is idempotent."""
    hook_path = tmp_path / "pre-commit"
    result1 = _ci.hook_install(hook_path)
    result2 = _ci.hook_install(hook_path)
    assert result1["status"] == "installed"
    assert result2["status"] == "already-installed"


def test_hook_remove_returns_dict(tmp_path):
    """hook_remove returns a dict."""
    hook_path = tmp_path / "pre-commit"
    _ci.hook_install(hook_path)
    result = _ci.hook_remove(hook_path)
    assert isinstance(result, dict)
    assert "status" in result or "error" in result


def test_hook_remove_deletes_file(tmp_path):
    """hook_remove deletes the hook file."""
    hook_path = tmp_path / "pre-commit"
    _ci.hook_install(hook_path)
    assert hook_path.exists()
    result = _ci.hook_remove(hook_path)
    assert result["status"] == "removed"
    assert not hook_path.exists()


def test_hook_remove_not_found(tmp_path):
    """hook_remove returns not-found for missing hooks."""
    hook_path = tmp_path / "pre-commit"
    result = _ci.hook_remove(hook_path)
    assert result["status"] == "not-found"
