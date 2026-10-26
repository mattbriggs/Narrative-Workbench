"""The narrative graph kernel.

The kernel owns stable identities, typed relationships, scopes, and graph
queries, independent of any framework (SRS REQ-014). It is deterministic and
holds no probabilistic behavior.
"""

from nw_engine.graph.kernel import GraphKernel

__all__ = ["GraphKernel"]
