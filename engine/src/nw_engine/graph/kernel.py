"""The typed narrative graph kernel, backed by NetworkX.

The kernel stores narrative units, state objects (**bodies**), events, and
assertions as nodes, and typed relationships as edges, in a
:class:`networkx.MultiDiGraph`. It enforces stable identity and the declared
constraint of each edge type (SRS REQ-010 to REQ-016). It performs no
validation of narrative invariants (that is the validation engine's job) and no
persistence (that is the application layer's job).

:caller contract: supply stable string ids; the kernel rejects duplicates and
    dangling edge endpoints. Containment is the ``PART_OF`` edge, never the
    node storage, so a unit may belong to several projections (SRS REQ-012).
:side effects: mutates the in-memory graph only.
:extension points: frameworks and projections read the kernel through its query
    methods; they never reach into the underlying NetworkX object.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

import networkx as nx

from nw_engine.contracts.models import Event, StateAssertion, StateObject
from nw_engine.domain.vocabulary import RelationshipType
from nw_engine.errors import GraphConstraintError

logger = logging.getLogger(__name__)

#: Required edge attributes per relationship type (SRS REQ-013). An edge missing
#: one of these is rejected with a :class:`GraphConstraintError`.
_REQUIRED_EDGE_ATTRS: dict[RelationshipType, tuple[str, ...]] = {
    RelationshipType.CAUSES: ("claim", "scope"),
    RelationshipType.REVEALS: ("recipient_model", "proposition"),
    RelationshipType.DERIVED_FROM: ("source_version",),
}

#: Node types the kernel distinguishes.
_UNIT = "unit"
_BODY = "body"
_EVENT = "event"


class GraphKernel:
    """An in-memory typed narrative graph.

    :ivar graph: the underlying :class:`networkx.MultiDiGraph`. Treat as private;
        use the query methods instead of reaching into it.
    """

    def __init__(self) -> None:
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self._assertions: dict[str, StateAssertion] = {}

    # -- node creation -----------------------------------------------------

    def add_unit(self, unit_id: str, kind: str, parent: Optional[str] = None) -> None:
        """Add a narrative unit at any scale.

        :param unit_id: stable id, unique across the graph.
        :param kind: unit kind (work, act, scene, episode, passage, ...).
        :param parent: optional parent unit id; adds a ``PART_OF`` edge.
        :raises GraphConstraintError: if the id already exists or the parent is
            unknown.
        """

        self._require_absent(unit_id)
        self.graph.add_node(unit_id, ntype=_UNIT, kind=kind)
        if parent is not None:
            self.add_edge(unit_id, parent, RelationshipType.PART_OF)

    def add_body(self, body: StateObject, unit_id: Optional[str] = None) -> None:
        """Add a state object (**body**).

        :param body: the :class:`StateObject`; ``body.mass`` is resistance.
        :param unit_id: optional unit this body is referenced by.
        :raises GraphConstraintError: on duplicate id or unknown unit.
        """

        self._require_absent(body.id)
        self.graph.add_node(body.id, ntype=_BODY, kind=body.kind, label=body.label, mass=body.mass)
        if unit_id is not None:
            self._require_present(unit_id)
            self.graph.add_edge(unit_id, body.id, key="references", rel="references")

    def add_event(self, event: Event) -> None:
        """Add an event (immutable once referenced by a REINTERPRETS edge).

        :param event: the :class:`Event`.
        :raises GraphConstraintError: on duplicate id or unknown unit.
        """

        self._require_absent(event.id)
        if event.unit_id is not None:
            self._require_present(event.unit_id)
        self.graph.add_node(
            event.id, ntype=_EVENT, description=event.description, story_time=event.story_time
        )

    def add_assertion(self, assertion: StateAssertion) -> None:
        """Record a state assertion on a body.

        Two assertions on the same body and key at the same story time conflict
        unless they carry different scopes or models, or an explicit
        ``CONTRADICTS`` edge exists (NW ADD v1.1 Table 26 invariant).

        :param assertion: the :class:`StateAssertion`.
        :raises GraphConstraintError: if the body is unknown, or a same-scope,
            same-model conflict is introduced implicitly.
        """

        self._require_present(assertion.object_id)
        for existing in self._assertions.values():
            if (
                existing.object_id == assertion.object_id
                and existing.key == assertion.key
                and existing.story_time == assertion.story_time
                and existing.model_id == assertion.model_id
                and existing.scope == assertion.scope
                and existing.value != assertion.value
            ):
                raise GraphConstraintError(
                    f"conflicting assertion for {assertion.object_id}.{assertion.key}; "
                    "use a separate scope or an explicit CONTRADICTS edge",
                    scope=assertion.object_id,
                )
        self._assertions[assertion.id] = assertion

    # -- edges -------------------------------------------------------------

    def add_edge(self, src: str, dst: str, rel: RelationshipType, **attrs: object) -> None:
        """Add a typed relationship edge, enforcing its declared constraint.

        :param src: source node id (must exist).
        :param dst: destination node id (must exist).
        :param rel: the :class:`RelationshipType`.
        :param attrs: edge attributes; some relationship types require specific
            keys (see :data:`_REQUIRED_EDGE_ATTRS`).
        :raises GraphConstraintError: on unknown endpoints or missing required
            attributes. A ``REINTERPRETS`` edge must target an existing event and
            never mutates it (SRS REQ-022).
        """

        self._require_present(src)
        self._require_present(dst)
        required = _REQUIRED_EDGE_ATTRS.get(rel, ())
        missing = [k for k in required if k not in attrs]
        if missing:
            raise GraphConstraintError(
                f"{rel.value} edge requires attribute(s) {', '.join(missing)}",
                scope=f"{src}->{dst}",
            )
        if rel is RelationshipType.REINTERPRETS and self.graph.nodes[dst].get("ntype") != _EVENT:
            raise GraphConstraintError(
                "REINTERPRETS must target an event and must not alter it",
                scope=dst,
            )
        self.graph.add_edge(src, dst, key=rel.value, rel=rel.value, **attrs)

    # -- queries -----------------------------------------------------------

    def exists(self, node_id: str) -> bool:
        """Return whether a node id is present."""

        return self.graph.has_node(node_id)

    def mass(self, body_id: str) -> float:
        """Return a body's mass (resistance to change).

        :raises GraphConstraintError: if the id is not a body.
        """

        if self.graph.nodes.get(body_id, {}).get("ntype") != _BODY:
            raise GraphConstraintError(f"{body_id} is not a body", scope=body_id)
        return float(self.graph.nodes[body_id]["mass"])

    def bodies(self) -> list[str]:
        """Return all body ids."""

        return [n for n, d in self.graph.nodes(data=True) if d.get("ntype") == _BODY]

    def events(self) -> list[str]:
        """Return all event ids, ordered by story time then id (deterministic)."""

        evs = [(d.get("story_time", 0), n) for n, d in self.graph.nodes(data=True) if d.get("ntype") == _EVENT]
        return [n for _, n in sorted(evs)]

    def assertions_for(self, object_id: str) -> list[StateAssertion]:
        """Return assertions recorded for a body, ordered by story time."""

        found = [a for a in self._assertions.values() if a.object_id == object_id]
        return sorted(found, key=lambda a: (a.story_time, a.id))

    def contained_by(self, unit_id: str) -> list[str]:
        """Return the direct children of a unit under the ``PART_OF`` projection.

        Containment is a typed relation, not node storage (SRS REQ-012), so a
        unit may appear under several parents in different frameworks.
        """

        self._require_present(unit_id)
        children: list[str] = []
        for src, dst, key in self.graph.edges(keys=True):
            if dst == unit_id and key == RelationshipType.PART_OF.value:
                children.append(src)
        return sorted(children)

    def edges_of(self, rel: RelationshipType) -> list[tuple[str, str]]:
        """Return all ``(src, dst)`` pairs for a given relationship type."""

        return sorted(
            (src, dst)
            for src, dst, key in self.graph.edges(keys=True)
            if key == rel.value
        )

    # -- internals ---------------------------------------------------------

    def _require_absent(self, node_id: str) -> None:
        if self.graph.has_node(node_id):
            raise GraphConstraintError(f"duplicate id {node_id!r}", scope=node_id)

    def _require_present(self, node_id: str) -> None:
        if not self.graph.has_node(node_id):
            raise GraphConstraintError(f"unknown node {node_id!r}", scope=node_id)

    def node_count(self, *kinds: str) -> int:
        """Return the number of nodes, optionally filtered by node type."""

        if not kinds:
            return self.graph.number_of_nodes()
        return sum(1 for _, d in self.graph.nodes(data=True) if d.get("ntype") in kinds)
