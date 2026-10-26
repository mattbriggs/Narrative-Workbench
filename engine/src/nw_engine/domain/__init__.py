"""Fixed domain vocabulary and enumerations for Narrative Workbench.

This package defines the names that the rest of the system MUST use as written
(``CLAUDE.md`` C-3): the state-field vocabulary, the typed relationship
vocabulary, the transition classes, and the assertion levels. These are data,
not policy; the graph kernel stays framework-agnostic (SRS REQ-014).
"""

from nw_engine.domain.vocabulary import (
    AssertionLevel,
    RelationshipType,
    StateFieldTerm,
    TransitionClass,
    STATE_FIELD_GLOSSARY,
    relationship_constraint,
)

__all__ = [
    "AssertionLevel",
    "RelationshipType",
    "StateFieldTerm",
    "TransitionClass",
    "STATE_FIELD_GLOSSARY",
    "relationship_constraint",
]
