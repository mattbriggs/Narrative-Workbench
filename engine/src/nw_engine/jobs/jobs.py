"""Job records and the event-driven job runner.

The runner advances a job only on real lifecycle events (SRS REQ-111). It
refuses illegal transitions and links a retry attempt to the failure it follows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from nw_engine.contracts.models import JobState
from nw_engine.errors import UnhandledEventError

# Permitted job transitions (SRS REQ-110), mirroring the UI job statechart.
_TRANSITIONS: dict[tuple[JobState, str], JobState] = {
    (JobState.IDLE, "enqueue"): JobState.QUEUED,
    (JobState.QUEUED, "worker_started"): JobState.RUNNING,
    (JobState.RUNNING, "partial_result"): JobState.PARTIAL,
    (JobState.PARTIAL, "more_work"): JobState.RUNNING,
    (JobState.RUNNING, "completed"): JobState.COMPLETE,
    (JobState.RUNNING, "failed"): JobState.FAILED,
    (JobState.QUEUED, "cancel"): JobState.CANCELLED,
    (JobState.RUNNING, "cancel_acknowledged"): JobState.CANCELLED,
    (JobState.FAILED, "retry"): JobState.QUEUED,
}


@dataclass
class Job:
    """A single job and its lifecycle state.

    :ivar id: stable job id.
    :ivar kind: ``extraction`` | ``simulation`` | ``realization`` | ``comparison``.
    :ivar state: the current :class:`JobState`.
    :ivar attempt: 1-based attempt number; incremented on retry.
    :ivar prior_failure: the attempt id this attempt follows, if any.
    """

    id: str
    kind: str
    state: JobState = JobState.IDLE
    attempt: int = 1
    prior_failure: Optional[str] = None
    inputs: dict = field(default_factory=dict)


class JobRunner:
    """Manages jobs and advances them on real events."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def enqueue(self, job_id: str, kind: str, inputs: Optional[dict] = None) -> Job:
        """Create and queue a job (records inputs for reproducibility)."""

        job = Job(id=job_id, kind=kind, inputs=inputs or {})
        self._jobs[job_id] = job
        return self.dispatch(job_id, "enqueue")

    def dispatch(self, job_id: str, event: str) -> Job:
        """Advance a job on a real event.

        :raises UnhandledEventError: if the event is not permitted from the
            current state (no silent timer-driven change, SRS REQ-111).
        """

        job = self._jobs[job_id]
        key = (job.state, event)
        if key not in _TRANSITIONS:
            raise UnhandledEventError(
                f"job {job_id} cannot handle {event!r} from {job.state.value}",
                scope=job_id,
            )
        job.state = _TRANSITIONS[key]
        return job

    def retry(self, job_id: str, new_job_id: str) -> Job:
        """Create a new attempt linked to a failed job (SRS REQ-113).

        :raises UnhandledEventError: if the job has not failed.
        """

        failed = self._jobs[job_id]
        if failed.state is not JobState.FAILED:
            raise UnhandledEventError(f"job {job_id} is not failed", scope=job_id)
        attempt = Job(
            id=new_job_id,
            kind=failed.kind,
            attempt=failed.attempt + 1,
            prior_failure=failed.id,
            inputs=dict(failed.inputs),
        )
        self._jobs[new_job_id] = attempt
        return self.dispatch(new_job_id, "enqueue")

    @staticmethod
    def may_show_committed(job: Job) -> bool:
        """Partial output must never be shown as committed (SRS REQ-112)."""

        return job.state is JobState.COMPLETE

    def get(self, job_id: str) -> Job:
        """Return a job by id."""

        return self._jobs[job_id]
