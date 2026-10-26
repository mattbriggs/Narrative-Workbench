"""Export package assembly and derived-index storage."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class ExportPackage:
    """A durable export bundle.

    :ivar source_commit: the commit the export was taken from (SRS REQ-121).
    :ivar lossy: whether the export is a lossy projection.
    :ivar warnings: human-readable warnings (non-empty when lossy).
    :ivar files: file name -> contents (open JSON, Markdown, fingerprints).
    """

    source_commit: str
    lossy: bool
    warnings: list[str] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)


class ExportBuilder:
    """Assembles an :class:`ExportPackage`.

    :param source_commit: the commit being exported.
    """

    def __init__(self, source_commit: str) -> None:
        self._source_commit = source_commit
        self._files: dict[str, str] = {}
        self._fingerprints: dict[str, str] = {}

    def add_json(self, name: str, obj: object) -> None:
        """Add an open-JSON file to the package."""

        self._files[name] = json.dumps(obj, indent=2, sort_keys=True)

    def add_markdown_report(self, text: str) -> None:
        """Add the human-readable Markdown report (SRS REQ-120)."""

        self._files["report.md"] = text

    def add_source_fingerprint(self, edition_id: str, fingerprint: str) -> None:
        """Record a source edition fingerprint to include in the package."""

        self._fingerprints[edition_id] = fingerprint

    def build(self, lossy: bool = False) -> ExportPackage:
        """Build the package.

        :param lossy: whether this export drops graph semantics; when true a
            warning is attached (SRS REQ-121).
        :returns: an :class:`ExportPackage` that always includes the source
            fingerprints and, when present, the report.
        """

        self._files["source-fingerprints.json"] = json.dumps(self._fingerprints, indent=2, sort_keys=True)
        warnings: list[str] = []
        if lossy:
            warnings.append(
                f"Export from commit {self._source_commit} is a lossy projection; "
                "graph semantics may not round-trip."
            )
        return ExportPackage(
            source_commit=self._source_commit,
            lossy=lossy,
            warnings=warnings,
            files=dict(self._files),
        )


class DerivedIndexStore:
    """Holds derived indexes (search/vector) separately from works.

    Deleting an index never deletes the work it was built from (SRS REQ-122).
    """

    def __init__(self) -> None:
        self._indexes: dict[str, str] = {}
        self._works: set[str] = set()

    def add_work(self, work_id: str) -> None:
        """Register a work id (authoritative; never removed by index deletion)."""

        self._works.add(work_id)

    def build_index(self, index_id: str, work_id: str) -> None:
        """Build a derived index for a work."""

        self._indexes[index_id] = work_id

    def delete_index(self, index_id: str) -> None:
        """Delete a derived index, leaving the work intact (SRS REQ-122)."""

        self._indexes.pop(index_id, None)

    def work_exists(self, work_id: str) -> bool:
        """Return whether a work still exists."""

        return work_id in self._works
