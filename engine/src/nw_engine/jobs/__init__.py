"""Long-running job lifecycle.

Extraction, simulation, realization, and comparison run as asynchronous,
cancellable jobs whose state changes come from real events, never a timer
(SRS REQ-110/111). Partial output is never presented as committed (REQ-112); a
retry creates a new attempt linked to the prior failure (REQ-113).
"""

from nw_engine.jobs.jobs import Job, JobRunner

__all__ = ["Job", "JobRunner"]
