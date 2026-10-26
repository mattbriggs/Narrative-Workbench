"""Line-delimited JSON dispatch.

Routes application requests to engine services and returns typed responses
(SRS REQ-160). The engine returns proposals and validation results; it never
persists canonical state, so no dispatch handler commits (SRS REQ-076).
"""

from nw_engine.rpc.dispatch import Dispatcher

__all__ = ["Dispatcher"]
