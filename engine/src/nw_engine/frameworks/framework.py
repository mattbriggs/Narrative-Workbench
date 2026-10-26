"""Structural frameworks and their registry.

A :class:`StructuralFramework` is a versioned configuration, not engine code
(SRS REQ-031, AD-08). The :class:`FrameworkRegistry` holds several frameworks
(and versions) so one narrative graph can be evaluated under each without
duplication (SRS REQ-030).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nw_engine.domain.vocabulary import RelationshipType
from nw_engine.graph import GraphKernel


@dataclass(frozen=True)
class FrameworkViolation:
    """A unit that breaks a framework's rules.

    :ivar unit_id: the offending unit.
    :ivar rule: ``"unit_type"`` or ``"containment"``.
    :ivar detail: a human-readable explanation.
    """

    unit_id: str
    rule: str
    detail: str


@dataclass
class StructuralFramework:
    """A versioned structural configuration.

    :ivar name: framework name (e.g. ``"mckee"``, ``"contour-44"``, ``"open"``).
    :ivar version: independent version string (SRS REQ-031).
    :ivar permitted_unit_types: unit kinds this framework allows.
    :ivar containment: child kind -> set of allowed parent kinds. A child kind
        absent from the map is unconstrained (open frameworks).
    :ivar milestones: unit ids treated as milestones.
    """

    name: str
    version: str
    permitted_unit_types: set[str]
    containment: dict[str, set[str]] = field(default_factory=dict)
    milestones: set[str] = field(default_factory=set)
    soft_goals: list[str] = field(default_factory=list)

    def evaluate(self, kernel: GraphKernel) -> list[FrameworkViolation]:
        """Evaluate a graph's units against this framework.

        :param kernel: the graph kernel to read units and ``PART_OF`` edges from.
        :returns: a list of :class:`FrameworkViolation`; empty when the graph
            conforms. The graph is never modified (SRS REQ-030).
        """

        violations: list[FrameworkViolation] = []
        child_to_parent = {src: dst for src, dst in kernel.edges_of(RelationshipType.PART_OF)}
        for node_id, data in kernel.graph.nodes(data=True):
            if data.get("ntype") != "unit":
                continue
            kind = data.get("kind")
            if kind not in self.permitted_unit_types:
                violations.append(
                    FrameworkViolation(node_id, "unit_type", f"{kind!r} not permitted by {self.name}")
                )
                continue
            allowed_parents = self.containment.get(kind)
            if allowed_parents is not None:
                parent = child_to_parent.get(node_id)
                parent_kind = kernel.graph.nodes[parent].get("kind") if parent else None
                if parent_kind not in allowed_parents:
                    violations.append(
                        FrameworkViolation(
                            node_id,
                            "containment",
                            f"{kind!r} may not be contained by {parent_kind!r} under {self.name}",
                        )
                    )
        return sorted(violations, key=lambda v: (v.unit_id, v.rule))

    def is_milestone(self, unit_id: str) -> bool:
        """Return whether a unit is a milestone in this framework."""

        return unit_id in self.milestones


class FrameworkRegistry:
    """Holds frameworks keyed by ``(name, version)`` (SRS REQ-031)."""

    def __init__(self) -> None:
        self._frameworks: dict[tuple[str, str], StructuralFramework] = {}

    def register(self, framework: StructuralFramework) -> None:
        """Register a framework version.

        :raises ValueError: if the same name+version is registered twice
            (versions are immutable).
        """

        key = (framework.name, framework.version)
        if key in self._frameworks:
            raise ValueError(f"framework {key} already registered")
        self._frameworks[key] = framework

    def get(self, name: str, version: str) -> StructuralFramework:
        """Return a registered framework by name and version."""

        return self._frameworks[(name, version)]

    def evaluate_all(self, kernel: GraphKernel) -> dict[tuple[str, str], list[FrameworkViolation]]:
        """Evaluate one graph under every registered framework (SRS REQ-030).

        :returns: a map of ``(name, version)`` -> violations, so the same graph
            is compared across frameworks without duplication.
        """

        return {key: fw.evaluate(kernel) for key, fw in self._frameworks.items()}
