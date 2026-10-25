"""Timeline projection.

Builds a story-time-ordered list of events from the graph kernel. A projection
is derived and rebuildable; it never becomes authoritative (SRS REQ-099).
"""

from __future__ import annotations

from nw_engine.graph import GraphKernel


def build_timeline(kernel: GraphKernel) -> list[dict]:
    """Return events ordered by story time.

    :param kernel: the graph kernel to read committed events from.
    :returns: a list of ``{id, story_time, description}`` dicts in story order.
    """

    rows: list[dict] = []
    for event_id in kernel.events():
        data = kernel.graph.nodes[event_id]
        rows.append(
            {
                "id": event_id,
                "story_time": data.get("story_time", 0),
                "description": data.get("description", ""),
            }
        )
    return rows
