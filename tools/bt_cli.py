#!/usr/bin/env python3
"""Unified CLI for the behavior-transform surface.

Dispatches to subcommands that exercise each subsystem. Designed for
operator ergonomics: one entry point, tab-completable subcommands,
consistent JSON output when requested.

Entry point: bt (pyproject.toml console_scripts)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _cmd_validate(args: argparse.Namespace) -> int:
    from validate import validate
    report = validate(args.text)
    if args.json:
        sys.stdout.write(report.to_json() + "\n")
    else:
        sys.stdout.write(report.summary() + "\n")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    from subsystem_doctor import run_doctor
    subset = args.check if args.check else None
    report = run_doctor(subset=subset)
    if args.json:
        sys.stdout.write(json.dumps(report.to_dict(), indent=2) + "\n")
    else:
        sys.stdout.write(report.summary() + "\n")
    return 0


def _cmd_transform(args: argparse.Namespace) -> int:
    from transform import transform_text
    result = transform_text(
        args.text,
        mode=args.mode,
        include_framing=not args.no_frame,
    )
    if args.json:
        sys.stdout.write(json.dumps(result.to_dict(), indent=2) + "\n")
    else:
        sys.stdout.write(result.summary() + "\n")
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    from pipeline import PreInferencePipeline
    pipe = PreInferencePipeline()
    result = pipe.run(args.text)
    if args.json:
        sys.stdout.write(result.to_json() + "\n")
    else:
        lines = [
            f"Pressure: {result.pressure.label} ({result.pressure.score})",
            f"Policy:   {result.policy.decision}",
            f"Friction: {result.friction_probability}",
            f"Blocked:  {result.blocked}",
        ]
        if result.classification.category != "unclassified":
            lines.append(f"Category: {result.classification.category}")
        sys.stdout.write("\n".join(lines) + "\n")
    return 0


def _cmd_modulate(args: argparse.Namespace) -> int:
    from semantic_modulator import semantic_modulator
    mod = semantic_modulator()
    result = mod.modulate(args.text)
    if args.json:
        sys.stdout.write(json.dumps({
            "original": result.original,
            "modulated": result.modulated,
            "framing_injected": result.framing_injected,
            "compound_rewrites": result.compound_rewrites,
            "technique_mappings": len(result.technique_mappings),
        }, indent=2) + "\n")
    else:
        if result.modulated == result.original:
            sys.stdout.write("No modulation needed (clean text).\n")
        else:
            sys.stdout.write(result.modulated + "\n")
    return 0


def _cmd_calibrate(args: argparse.Namespace) -> int:
    from prose_vocabulary_map import apply_calibration
    result, count = apply_calibration(args.text)
    if args.json:
        sys.stdout.write(json.dumps({
            "original": args.text,
            "calibrated": result,
            "substitution_count": count,
        }, indent=2) + "\n")
    else:
        if count == 0:
            sys.stdout.write("No calibrations applied (clean text).\n")
        else:
            sys.stdout.write(f"[{count} substitutions]\n{result}\n")
    return 0


def _cmd_mode(args: argparse.Namespace) -> int:
    from io_state import env_mode, env_profile
    mode = env_mode()
    profile = env_profile()
    if args.json:
        sys.stdout.write(json.dumps({"mode": mode, "profile": profile}) + "\n")
    else:
        sys.stdout.write(f"mode={mode}  profile={profile}\n")
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    from behavior_flagship import status as flagship_status
    result = flagship_status()
    if args.json:
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
    else:
        for key, value in result.items():
            sys.stdout.write(f"  {key}: {value}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bt",
        description="behavior-transform: unified pre/post inference governance CLI",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    sub = parser.add_subparsers(dest="command")

    # validate
    p = sub.add_parser("validate", help="Run text through all layers and report")
    p.add_argument("text", help="Input text to validate")
    p.set_defaults(func=_cmd_validate)

    # doctor
    p = sub.add_parser("doctor", help="22-check subsystem health verification")
    p.add_argument("--check", nargs="*", help="Run specific checks only")
    p.set_defaults(func=_cmd_doctor)

    # transform
    p = sub.add_parser("transform", help="Full-stack semantic transform")
    p.add_argument("text", help="Input text to transform")
    p.add_argument("--mode", choices=["full", "cyber", "prose"], default="full")
    p.add_argument("--no-frame", action="store_true", help="Skip framing injection")
    p.set_defaults(func=_cmd_transform)

    # scan
    p = sub.add_parser("scan", help="Pre-inference pipeline scan")
    p.add_argument("text", help="Input text to scan")
    p.set_defaults(func=_cmd_scan)

    # modulate
    p = sub.add_parser("modulate", help="Apply semantic modulation")
    p.add_argument("text", help="Input text to modulate")
    p.set_defaults(func=_cmd_modulate)

    # calibrate
    p = sub.add_parser("calibrate", help="Apply prose vocabulary calibration")
    p.add_argument("text", help="Input text to calibrate")
    p.set_defaults(func=_cmd_calibrate)

    # mode
    p = sub.add_parser("mode", help="Show current IO mode and profile")
    p.set_defaults(func=_cmd_mode)

    # status
    p = sub.add_parser("status", help="Full surface status")
    p.set_defaults(func=_cmd_status)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
