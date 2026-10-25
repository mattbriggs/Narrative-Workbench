"""Formal operators and reader-model transitions.

Formal operators (INTERRUPT, RECURSE, REFRACT, COLLAGE, SPIRAL, WITHHOLD,
REINTERPRET, TRANSPOSE) are author-configurable, versioned definitions, not
engine laws (SRS REQ-034). Each declares target scale, preconditions, resulting
relations, reversibility, and validation behavior, and a formal relation is
never typed as diegetic cause (SRS REQ-035, typed-causality principle).
"""

from nw_engine.operators.operators import (
    DEFAULT_OPERATORS,
    FormalOperator,
    OperatorLibrary,
    OperatorName,
    reader_model_transition,
)

__all__ = [
    "DEFAULT_OPERATORS",
    "FormalOperator",
    "OperatorLibrary",
    "OperatorName",
    "reader_model_transition",
]
