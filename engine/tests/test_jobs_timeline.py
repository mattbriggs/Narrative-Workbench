"""Tests for the job lifecycle and the timeline projection (SRS SS3.11, REQ-099)."""

import pytest

from nw_engine.contracts.models import Event, JobState, StateObject
from nw_engine.errors import UnhandledEventError
from nw_engine.graph import GraphKernel
from nw_engine.jobs import JobRunner
from nw_engine.projections import build_timeline


def test_job_happy_path_partial_not_committed():
    runner = JobRunner()
    job = runner.enqueue("j1", "simulation")
    assert job.state is JobState.QUEUED
    runner.dispatch("j1", "worker_started")
    job = runner.dispatch("j1", "partial_result")
    assert job.state is JobState.PARTIAL
    assert runner.may_show_committed(job) is False
    runner.dispatch("j1", "more_work")
    job = runner.dispatch("j1", "completed")
    assert runner.may_show_committed(job) is True


def test_job_illegal_event_rejected():
    runner = JobRunner()
    runner.enqueue("j2", "extraction")
    with pytest.raises(UnhandledEventError):
        runner.dispatch("j2", "completed")  # not from QUEUED


def test_job_retry_links_prior_failure():
    runner = JobRunner()
    runner.enqueue("j3", "comparison")
    runner.dispatch("j3", "worker_started")
    runner.dispatch("j3", "failed")
    attempt = runner.retry("j3", "j3b")
    assert attempt.attempt == 2 and attempt.prior_failure == "j3"
    assert attempt.state is JobState.QUEUED


def test_retry_requires_failed_state():
    runner = JobRunner()
    runner.enqueue("j4", "simulation")
    with pytest.raises(UnhandledEventError):
        runner.retry("j4", "j4b")


def test_cancel_paths():
    runner = JobRunner()
    runner.enqueue("j5", "simulation")
    job = runner.dispatch("j5", "cancel")
    assert job.state is JobState.CANCELLED
    runner.enqueue("j6", "simulation")
    runner.dispatch("j6", "worker_started")
    assert runner.dispatch("j6", "cancel_acknowledged").state is JobState.CANCELLED


def test_timeline_orders_by_story_time():
    k = GraphKernel()
    k.add_unit("w", "work")
    k.add_body(StateObject(id="b", kind="actor"))
    k.add_event(Event(id="e2", description="late", story_time=5))
    k.add_event(Event(id="e1", description="early", story_time=1))
    rows = build_timeline(k)
    assert [r["id"] for r in rows] == ["e1", "e2"]
