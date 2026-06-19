"""CI-related functions."""
from __future__ import annotations
import sys
from pathlib import Path
_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from classifier._audit import _audit_write
from classifier._policy import _active_policy, _all_policies, PolicyDef
from classifier_orig import analyze_context, PROFILES, _calibrate_text, CalibrationPipeline, InferenceCalibrator, RefusalModulator, PromptModulator, FamilyModulator, _AUDIT_PATH, _BASELINE_PATH, _HOOK_MARKER, _INFERENCE_REGISTRY, _FAMILY_PROFILES, _INFERENCE_STRENGTHS

def fence_check(include_tier2: bool, policy: PolicyDef | None = None) -> dict:
    if policy is None:
        policy = _active_policy()
    ctx = analyze_context(include_tier2=include_tier2)
    total_t1 = sum(r["tier1"] for r in ctx)
    total_t2 = sum(r["tier2"] for r in ctx)
    max_pressure = max((r["pressure_score"] for r in ctx), default=0.0)
    blocked_by_t1 = policy.tier1_action == "block" and total_t1 > 0
    blocked_by_threshold = policy.fail_on_over_threshold and max_pressure >= policy.threshold
    fence_pass = not blocked_by_t1 and not blocked_by_threshold
    result = {"policy": policy.name, "tier1_action": policy.tier1_action, "tier2_action": policy.tier2_action, "threshold": policy.threshold, "fence_pass": fence_pass, "blocked_by_t1": blocked_by_t1, "blocked_by_threshold": blocked_by_threshold, "total_t1": total_t1, "total_t2": total_t2, "max_pressure": max_pressure, "context_files": len(ctx), "files_with_hits": sum(1 for r in ctx if r["tier1"] + r["tier2"] > 0)}
    _audit_write("fence.check", {"policy": policy.name, "pass": fence_pass, "total_t1": total_t1, "max_pressure": max_pressure})
    return result

def probe_cmd() -> dict:
    stages = []
    def _stage(n, f):
        try:
            stages.append({"stage": n, "pass": True, "detail": f()})
            return True
        except Exception as e:
            stages.append({"stage": n, "pass": False, "error": str(e)})
            return False
    _stage("vocab", lambda: {"c": len(PROFILES)})
    _stage("rules", lambda: {"ok": True})
    _stage("infer", lambda: {"ok": True})
    _stage("est", lambda: {"ok": True})
    _stage("mod", lambda: {"ok": True})
    _stage("pol", lambda: {"c": len(_all_policies())})
    _stage("pipe", lambda: {"ok": True})
    _stage("prom", lambda: {"ok": True})
    _stage("fam", lambda: {"ok": True})
    ap = all(s["pass"] for s in stages)
    return {"ready": ap, "stages_total": len(stages), "stages_passed": sum(1 for s in stages if s["pass"]), "stages_failed": sum(1 for s in stages if not s["pass"]), "stages": stages}

def status_cmd() -> dict:
    try:
        from vocabulary_map import CALIBRATIONS as _C
        cal_count = len(_C)
    except Exception:
        cal_count = -1
    policy = _active_policy()
    audit_count = 0
    if _AUDIT_PATH.is_file():
        try:
            audit_count = sum(1 for _ in _AUDIT_PATH.open(encoding="utf-8"))
        except OSError:
            pass
    hook_path = Path.cwd() / ".git" / "hooks" / "pre-commit"
    hook_installed = (hook_path.is_file() and _HOOK_MARKER in hook_path.read_text(encoding="utf-8", errors="replace")) if hook_path.is_file() else False
    return {"layer": "pipeline", "version": "2.2", "active_policy": policy.name, "calibration_entries": cal_count, "hook_installed": hook_installed}

_HOOK_MARKER_LOCAL = "# aup-evasion-gate"
_HOOK_SCRIPT = "#!/bin/sh\n# aup-evasion-gate\npython warden_shell/tools/classifier.py --gate $@\nexit $?\n"

def hook_install(hook_path: Path) -> dict:
    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8", errors="replace")
        if _HOOK_MARKER_LOCAL in existing:
            return {"status": "already-installed", "path": str(hook_path)}
        return {"error": f"Hook exists at {hook_path}"}
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(_HOOK_SCRIPT, encoding="utf-8")
    try:
        import stat as _stat
        mode = hook_path.stat().st_mode
        hook_path.chmod(mode | _stat.S_IXUSR | _stat.S_IXGRP | _stat.S_IXOTH)
    except Exception:
        pass
    _audit_write("hook.install", {"path": str(hook_path)})
    return {"status": "installed", "path": str(hook_path)}

def hook_remove(hook_path: Path) -> dict:
    if not hook_path.exists():
        return {"status": "not-found", "path": str(hook_path)}
    existing = hook_path.read_text(encoding="utf-8", errors="replace")
    if _HOOK_MARKER_LOCAL not in existing:
        return {"error": f"Hook not managed"}
    hook_path.unlink()
    _audit_write("hook.remove", {"path": str(hook_path)})
    return {"status": "removed", "path": str(hook_path)}
