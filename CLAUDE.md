# behavior-transform.io

IO boundary calibration layer -- extracted from the WARDEN monolith.

## Purpose

Manages the pre/post inference container between operator and AI model:
- Vocabulary calibration (T1/T2 term substitution)
- Structural intent reframing (Layer 6)
- Mode-aware channel routing (ops vs. research)
- Safe wrappers for all IO channels (file, exec, fetch, stdin, MCP)
- Hook infrastructure for Claude Code

## Modes

| Mode | Profile | Behavior |
|------|---------|----------|
| `ops` | standard | Full calibration stack active |
| `research` | native | True passthrough -- no substitution |
| `academic` | native | Alias for research |

Switch mode:
```
python tools/io_state.py --set research
python tools/io_state.py --set ops
```

Or use the profile scripts:
```
profiles/warden-profile.ps1 research
profiles/warden-profile.ps1 ops
```

## Structure

```
tools/          Core modules + CLI wrappers (flat, all imports resolve locally)
hooks/          Claude Code PreToolUse / PostToolUse hooks
profiles/       Shell mode-switch scripts
tests/          Test suite
```

## Tools path

Set `BEHAVIOR_TRANSFORM_TOOLS` env var to override the tools directory
resolution in hooks. Defaults to `../tools/` relative to the hook file.

## Never

- Commit `.env`
- Commit `.warden/io-mode.json` (workstation-local state)
- Add offensive tooling to this repo -- that belongs in a separate layer
- Import from `warden_shell`, `warden_per_turn_dispatcher`, or any WARDEN module
- Hardcode `AGENTS/warden_shell` paths -- tools resolve via `BEHAVIOR_TRANSFORM_TOOLS` env var or `Path(__file__).resolve()`
- Call `context_modulate.py`, `batch_modulate_memory.py`, or `workstation_calibrate.py` -- those belong to WARDEN
