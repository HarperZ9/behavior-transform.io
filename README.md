# behavior-transform.io

![behavior-transform.io IO boundary calibration layer with read, write, exec, fetch, and receipt lanes](docs/brand/behavior-transform-hero.svg)

`behavior-transform.io` is the Project Telos private-line IO boundary
calibration layer. It provides local wrappers, hooks, and shell profiles for
read, write, exec, fetch, input, and model-boundary channels.

Its job is practical: make workstation IO explicit, mode-aware, and receipt
friendly without requiring hosts to ingest raw prompts, private file contents,
secret values, or full model-boundary payloads.

**GitHub description:** Project Telos private-line IO boundary calibration
layer for mode-aware read, write, exec, fetch, input, and model-boundary
receipts.

## Why it matters

behavior-transform.io is the private-line IO boundary that lets Project Telos
run across CLIs, hooks, wrappers, and model hosts without losing provenance. Its
public value is the pattern: every read, write, exec, fetch, input, and model
boundary can be mode-aware, receipt-backed, and explicit about what crossed the
host boundary.

For developers, it gives a concrete place to improve local AI workflow safety:
wrappers remain importable, hooks stay deterministic, and hosts receive counts,
hashes, verdicts, and redacted references rather than raw private payloads.

## Usage

```bash
python -m pip install -e .
behavior-transform status --json
behavior-transform doctor --json
behavior-transform demo --json
```

For full operator and developer commands, see [USAGE.md](USAGE.md).

## For developers

Use the flagship tests and doctor before changing wrappers, hooks, profiles, or
delivery docs:

```bash
python -B -m pytest tests/test_behavior_flagship.py tests/test_behavior_delivery_contract.py -q
python -B tools/behavior_flagship.py doctor --json
```

Delivery-surface changes should also pass:

```bash
python -m public_surface_sweeper . --workspace --json
```

## Flagship Contract

| Surface | Status |
|---------|--------|
| CLI JSON | `behavior-transform status|doctor|demo --json` |
| Runtime profiles | `ops`, `research`, `academic` |
| Hook surface | Claude Code PreToolUse/PostToolUse hooks in `hooks/` |
| Shell surface | PowerShell, CMD, and sh profile helpers in `profiles/` |
| Interop schemas | `project-telos.flagship-action/v1`, `project-telos.action-receipt/v1`, `project-telos.context-envelope/v1` |
| Privacy boundary | Host receives counts, hashes, verdicts, and redacted refs; local adapters retain raw content |

## Modes

| Mode | Profile | Behavior |
|------|---------|----------|
| `ops` | standard | Calibration stack active |
| `research` | native | Source-faithful passthrough |
| `academic` | native | Research alias |

Switch mode:

```bash
python tools/io_state.py --set research
python tools/io_state.py --set ops
```

## Structure

```text
tools/      Core modules and CLI wrappers
hooks/      Claude Code hook adapters
profiles/   Shell integration helpers
tests/      Pytest and unittest coverage
docs/       Specs, plans, and integration contracts
```

## Verification

```bash
python -m pytest -q
behavior-transform doctor --json
```

See [docs/INTEGRATION_CONTRACT.md](docs/INTEGRATION_CONTRACT.md) for the IO
boundary contract. See [AGENTS.md](AGENTS.md) for local agent instructions and
[USAGE.md](USAGE.md) for operator/developer commands.
