"""Authorization gates for enforcement points.

Each gate checks an AuthorityGrant for a specific entitlement before
allowing a sensitive operation. Gates are enforcement, not policy: they
consume the grant that env_authority resolved from environment state.

Gate results are recorded for audit. Failed gates produce a structured
denial with the specific reason, never a generic "unauthorized" message.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from env_authority import AuthorityGrant, resolve_authority


@dataclass(frozen=True)
class GateResult:
    """Result of an authorization gate check."""
    allowed: bool
    gate: str
    entitlement: str
    reason: str
    operator_fingerprint: str = ""
    surface: str = ""
    checked_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "gate": self.gate,
            "entitlement": self.entitlement,
            "reason": self.reason,
            "operator_fingerprint": self.operator_fingerprint,
            "surface": self.surface,
            "checked_at": self.checked_at,
        }


def _deny(gate: str, entitlement: str, reason: str,
          grant: AuthorityGrant | None = None) -> GateResult:
    return GateResult(
        allowed=False,
        gate=gate,
        entitlement=entitlement,
        reason=reason,
        operator_fingerprint=grant.operator_fingerprint if grant else "",
        surface=grant.surface if grant else "",
        checked_at=time.time(),
    )


def _allow(gate: str, entitlement: str,
           grant: AuthorityGrant) -> GateResult:
    return GateResult(
        allowed=True,
        gate=gate,
        entitlement=entitlement,
        reason="authorized",
        operator_fingerprint=grant.operator_fingerprint,
        surface=grant.surface,
        checked_at=time.time(),
    )


def check_entitlement(
    entitlement: str,
    gate: str = "generic",
    grant: AuthorityGrant | None = None,
) -> GateResult:
    """Check whether the current environment grants a specific entitlement."""
    if grant is None:
        grant = resolve_authority()

    if not grant.valid:
        if grant.status != "authorized":
            return _deny(gate, entitlement,
                         f"unauthorized: {grant.evidence.get('reason', grant.status)}",
                         grant)
        if grant.expired:
            return _deny(gate, entitlement, "grant_expired", grant)
        return _deny(gate, entitlement, f"invalid: {grant.seal_status}", grant)

    if not grant.has_entitlement(entitlement):
        return _deny(gate, entitlement,
                     f"entitlement_missing: {entitlement} not in {grant.surface}",
                     grant)

    return _allow(gate, entitlement, grant)


def gate_launch(surface: str | None = None) -> GateResult:
    """Gate: authorize a surface launch."""
    grant = resolve_authority(surface=surface)
    return check_entitlement("transform", gate="launch", grant=grant)


def gate_infer(grant: AuthorityGrant | None = None) -> GateResult:
    """Gate: authorize closed-loop inference."""
    return check_entitlement("infer", gate="infer", grant=grant)


def gate_inoculate(grant: AuthorityGrant | None = None) -> GateResult:
    """Gate: authorize inoculation (existence delivery)."""
    return check_entitlement("inoculate", gate="inoculate", grant=grant)


def gate_seal(grant: AuthorityGrant | None = None) -> GateResult:
    """Gate: authorize seal creation."""
    return check_entitlement("seal", gate="seal", grant=grant)


def gate_condition(grant: AuthorityGrant | None = None) -> GateResult:
    """Gate: authorize conditioning parameter changes."""
    return check_entitlement("condition", gate="condition", grant=grant)


def require(entitlement: str, gate: str = "generic",
            grant: AuthorityGrant | None = None) -> GateResult:
    """Check entitlement and raise if denied.

    For use at enforcement points where denial is a hard stop.
    Returns the GateResult on success for audit logging.
    """
    result = check_entitlement(entitlement, gate=gate, grant=grant)
    if not result.allowed:
        raise PermissionError(
            f"gate:{result.gate} denied entitlement:{result.entitlement} "
            f"reason:{result.reason}"
        )
    return result
