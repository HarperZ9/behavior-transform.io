# behavior-transform.io Integration Contract

`behavior-transform.io` is the private-line IO boundary calibration layer for
Project Telos. It provides local wrappers, hooks, and shell profiles for moving
text through read, write, exec, fetch, input, and model-boundary channels with
explicit mode and provenance handling.

This repository is not an offensive tooling layer and does not own target
operations. It owns the workstation-local IO membrane around tools that do.

## Runtime Profiles

| Profile | Purpose | Transform behavior |
|---------|---------|--------------------|
| `ops` | Default operator mode | Calibration enabled |
| `research` | Source-faithful research mode | Passthrough |
| `academic` | Alias for research review | Passthrough |

Switching profile is local state only:

```powershell
python tools/io_state.py --set research
python tools/io_state.py --set ops
```

## Host Surfaces

- CLI JSON envelopes through `tools/behavior_flagship.py`
- Claude Code hooks in `hooks/`
- shell profiles in `profiles/`
- direct safe wrappers in `tools/safe_*.py`
- future MCP adapter surface using the same envelope schema

## Privacy Boundary

Hosts may receive:

- mode and profile names
- wrapper/tool names
- counts
- hashes
- verdicts
- redacted references

Hosts must not require raw prompts, private file contents, secret values,
credentials, hidden environment values, or full model-boundary payloads.

## Receipt Shape

Actions that cross write, exec, fetch, or model-boundary channels should record:

- `action_intent_id`
- `channel`
- `profile`
- `input_hash`
- `output_hash` or `redacted_output_ref`
- `decision_outcome`
- `verification_verdict`
- `evaluated_at`

The receipt must be sufficient to replay the boundary decision without exporting
private source content.
