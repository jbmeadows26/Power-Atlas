#!/usr/bin/env python3
"""Publish one validated public snapshot without rebasing or carrying local state.

The caller supplies an already-produced candidate outside the publication tree.
Each attempt fetches the authorized branch, validates the candidate and retained
snapshot, creates a new detached worktree at the fetched head, commits exactly
the allowlisted path, and performs a normal fast-forward push.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Callable


GLOBAL_CONFLICT_PATH = "eastern-axis/public/analysis/global-conflict-watch.json"
ALLOWED_TARGETS = {GLOBAL_CONFLICT_PATH}
SHA40 = re.compile(r"[0-9a-f]{40}")


class PublishFailure(RuntimeError):
    """A fail-closed publication outcome with a stable machine classification."""

    def __init__(self, classification: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.classification = classification
        self.retryable = retryable


@dataclass(frozen=True)
class Snapshot:
    raw: bytes
    digest: str
    generated_at: datetime
    generated_at_text: str


@dataclass(frozen=True)
class PublishResult:
    status: str
    classification: str
    attempts: int
    candidate_sha256: str
    candidate_generated_at: str
    base_commit: str
    published_commit: str | None

    def as_dict(self) -> dict:
        return {
            "schema": "eastern-axis.guarded-publication.v1",
            "status": self.status,
            "classification": self.classification,
            "attempts": self.attempts,
            "candidateSha256": self.candidate_sha256,
            "candidateGeneratedAt": self.candidate_generated_at,
            "baseCommit": self.base_commit,
            "publishedCommit": self.published_commit,
        }


def _utc_timestamp(value, field="generatedAt"):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PublishFailure("malformed_snapshot", f"{field} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PublishFailure("malformed_snapshot", f"{field} is not a valid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise PublishFailure("malformed_snapshot", f"{field} must use UTC")
    return parsed


def validate_global_conflict_snapshot(raw: bytes) -> Snapshot:
    try:
        document = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublishFailure("malformed_snapshot", "Snapshot is not valid UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise PublishFailure("malformed_snapshot", "Snapshot root must be an object")
    required = {
        "schemaVersion": int,
        "generatedAt": str,
        "status": str,
        "category": str,
        "analyst": dict,
        "sources": dict,
        "measurement": dict,
        "summary": dict,
        "zones": list,
        "limitations": list,
    }
    for key, expected in required.items():
        if not isinstance(document.get(key), expected):
            raise PublishFailure("malformed_snapshot", f"Snapshot field {key} has invalid type")
    if document["schemaVersion"] != 1 or document["category"] != "Defense, Security & Cyber":
        raise PublishFailure("malformed_snapshot", "Snapshot schema or category is not authorized")
    if document["status"] not in {"ok", "partial"}:
        raise PublishFailure("malformed_snapshot", "Snapshot status is not recognized")
    hotspots = document["summary"].get("hotspots")
    if not isinstance(hotspots, int) or hotspots < 0 or hotspots != len(document["zones"]):
        raise PublishFailure("malformed_snapshot", "Snapshot hotspot count is inconsistent")
    if not isinstance(document["analyst"].get("commandEligible"), int):
        raise PublishFailure("malformed_snapshot", "Snapshot analyst gate is missing")
    latest_observation = document["measurement"].get("latestCodedEvent")
    age = document["measurement"].get("dataAgeDays")
    if document["status"] == "ok":
        try:
            date.fromisoformat(latest_observation)
        except (TypeError, ValueError) as exc:
            raise PublishFailure("provenance_failure", "Successful snapshot lacks an observation date") from exc
        if not isinstance(age, int) or age < 0:
            raise PublishFailure("provenance_failure", "Successful snapshot lacks a valid observation age")
    elif latest_observation is not None:
        try:
            date.fromisoformat(latest_observation)
        except (TypeError, ValueError) as exc:
            raise PublishFailure("provenance_failure", "Partial snapshot observation date is malformed") from exc
    sources = document["sources"]
    if not sources:
        raise PublishFailure("provenance_failure", "Snapshot contains no source registry")
    source_urls = []
    ucdp = sources.get("ucdp")
    if isinstance(ucdp, dict):
        source_urls.append(ucdp.get("url"))
        for release in (ucdp.get("releases") or {}).values():
            if isinstance(release, dict):
                source_urls.append(release.get("url"))
    rss = sources.get("rss")
    if isinstance(rss, dict):
        source_urls.extend(feed.get("url") for feed in rss.get("feeds", []) if isinstance(feed, dict))
    if not source_urls or any(not isinstance(url, str) or not url.startswith("https://") for url in source_urls):
        raise PublishFailure("provenance_failure", "Snapshot source provenance is missing or unsafe")
    stamp = _utc_timestamp(document["generatedAt"])
    return Snapshot(raw, hashlib.sha256(raw).hexdigest(), stamp, document["generatedAt"])


def _run(args, cwd, *, check=False):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=check)


def _status_paths(repo: Path, runner=_run):
    result = runner(["git", "status", "--porcelain=v1", "--untracked-files=all"], repo)
    if result.returncode:
        raise PublishFailure("workspace_inspection_failure", result.stderr.strip() or "git status failed")
    rows = [line for line in result.stdout.splitlines() if line]
    paths = []
    for row in rows:
        value = row[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(value)
    return rows, paths


def _classify_push(stderr: str):
    text = stderr.lower()
    if any(item in text for item in ("non-fast-forward", "fetch first", "stale info")):
        return PublishFailure("concurrent_update", "Remote advanced before publication", retryable=True)
    if any(item in text for item in ("permission", "authentication", "403", "protected branch", "repository rule", "ruleset", "not authorized")):
        return PublishFailure("authorization_or_protection", "Push rejected by authorization or branch policy")
    if any(item in text for item in ("timed out", "timeout", "connection reset", "could not resolve", "network is unreachable", "remote end hung up", "http 5")):
        return PublishFailure("transient_transport", "Transient transport failure", retryable=True)
    return PublishFailure("push_rejected", "Push rejected for an unclassified reason")


class GuardedSnapshotPublisher:
    def __init__(
        self,
        repository: Path,
        *,
        remote="origin",
        branch="main",
        target=GLOBAL_CONFLICT_PATH,
        max_attempts=4,
        deadline_seconds=180,
        backoff_seconds=5,
        sleep: Callable[[float], None] = time.sleep,
        before_push: Callable[[Path, int], None] | None = None,
        push_override: Callable[[Path, int], subprocess.CompletedProcess] | None = None,
    ):
        self.repository = Path(repository).resolve()
        self.remote = remote
        self.branch = branch
        self.target = target
        self.max_attempts = max_attempts
        self.deadline_seconds = deadline_seconds
        self.backoff_seconds = backoff_seconds
        self.sleep = sleep
        self.before_push = before_push
        self.push_override = push_override
        if target not in ALLOWED_TARGETS:
            raise PublishFailure("unauthorized_path", f"Publication path is not allowlisted: {target}")
        if not 1 <= max_attempts <= 8 or not 1 <= deadline_seconds <= 900 or not 0 <= backoff_seconds <= 60:
            raise ValueError("Invalid retry policy")
        self._deadline_at = None

    def _command(self, args, cwd, *, text=True):
        remaining = self._deadline_at - time.monotonic()
        if remaining <= 0:
            raise PublishFailure("deadline_exhausted", "Publication deadline exhausted")
        try:
            return subprocess.run(args, cwd=cwd, text=text, capture_output=True,
                                  check=False, timeout=min(60, remaining))
        except subprocess.TimeoutExpired as exc:
            raise PublishFailure("deadline_exhausted", "Publication command exceeded the total deadline") from exc

    def _backoff(self, attempt):
        delay = min(self.backoff_seconds * attempt, 30)
        if time.monotonic() + delay >= self._deadline_at:
            raise PublishFailure("deadline_exhausted", "Publication deadline exhausted before retry")
        self.sleep(delay)

    def _fetch_head(self):
        ref = f"refs/remotes/{self.remote}/{self.branch}"
        result = self._command(["git", "fetch", "--no-tags", self.remote,
                                f"+refs/heads/{self.branch}:{ref}"], self.repository)
        if result.returncode:
            failure = _classify_push(result.stderr)
            if failure.classification == "authorization_or_protection":
                raise failure
            raise PublishFailure("remote_fetch_failure", str(failure), retryable=failure.retryable)
        resolved = self._command(["git", "rev-parse", "--verify", ref], self.repository)
        head = resolved.stdout.strip()
        if resolved.returncode or not SHA40.fullmatch(head):
            raise PublishFailure("remote_fetch_failure", "Fetched branch head cannot be resolved")
        return head

    def _remote_snapshot(self, head):
        exists = self._command(["git", "cat-file", "-e", f"{head}:{self.target}"], self.repository)
        if exists.returncode:
            tree = self._command(["git", "cat-file", "-e", f"{head}^{{tree}}"], self.repository)
            if tree.returncode:
                raise PublishFailure("remote_read_failure", "Fetched remote commit is unreadable")
            return None
        shown = self._command(["git", "show", f"{head}:{self.target}"], self.repository, text=False)
        if shown.returncode:
            raise PublishFailure("remote_read_failure", "Published snapshot could not be read")
        return validate_global_conflict_snapshot(shown.stdout)

    def publish(self, candidate_path: Path):
        candidate_path = Path(candidate_path).resolve()
        started = time.monotonic()
        self._deadline_at = started + self.deadline_seconds
        last_retryable = None
        for attempt in range(1, self.max_attempts + 1):
            if time.monotonic() - started >= self.deadline_seconds:
                raise PublishFailure("deadline_exhausted", "Publication deadline exhausted")
            candidate = validate_global_conflict_snapshot(candidate_path.read_bytes())
            try:
                head = self._fetch_head()
                retained = self._remote_snapshot(head)
            except PublishFailure as exc:
                if not exc.retryable or attempt == self.max_attempts:
                    raise
                last_retryable = exc
                self._backoff(attempt)
                continue
            if retained:
                if candidate.generated_at < retained.generated_at:
                    raise PublishFailure("candidate_older", "Candidate is older than the retained snapshot")
                if candidate.generated_at == retained.generated_at:
                    if candidate.digest == retained.digest:
                        return PublishResult("no-op", "identical_snapshot", attempt, candidate.digest,
                                             candidate.generated_at_text, head, head)
                    raise PublishFailure("equal_timestamp_changed_content",
                                         "Equal timestamps with different content require explicit review")
            with tempfile.TemporaryDirectory(prefix="ea-snapshot-publish-") as parent:
                tree = Path(parent) / "tree"
                self._command(["git", "worktree", "prune"], self.repository)
                added = self._command(["git", "worktree", "add", "--detach", str(tree), head], self.repository)
                if added.returncode:
                    raise PublishFailure("workspace_creation_failure", added.stderr.strip())
                try:
                    rows, _ = _status_paths(tree, self._command)
                    if rows:
                        raise PublishFailure("workspace_contamination", "Fresh publication tree is not clean")
                    # Re-read and revalidate the downloaded artifact immediately before installation.
                    candidate = validate_global_conflict_snapshot(candidate_path.read_bytes())
                    destination = tree / self.target
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(candidate_path, destination)
                    rows, paths = _status_paths(tree, self._command)
                    if not rows or set(paths) != {self.target}:
                        raise PublishFailure("workspace_contamination", "Candidate installation changed unauthorized paths")
                    staged = self._command(["git", "add", "--", self.target], tree)
                    if staged.returncode:
                        raise PublishFailure("workspace_staging_failure", staged.stderr.strip())
                    names = self._command(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"], tree)
                    if names.returncode or names.stdout.splitlines() != [self.target]:
                        raise PublishFailure("workspace_contamination", "Index contains unauthorized paths")
                    commit = self._command(["git", "-c", "user.name=github-actions[bot]",
                                            "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
                                            "commit", "-m", "data(eastern-axis): publish guarded global conflict analysis [skip ci]"], tree)
                    if commit.returncode:
                        raise PublishFailure("commit_failure", commit.stderr.strip() or commit.stdout.strip())
                    published = self._command(["git", "rev-parse", "HEAD"], tree).stdout.strip()
                    changed = self._command(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], tree)
                    rows, _ = _status_paths(tree, self._command)
                    if rows or changed.stdout.splitlines() != [self.target]:
                        raise PublishFailure("workspace_contamination", "Publication commit is not single-purpose")
                    if self.before_push:
                        self.before_push(tree, attempt)
                    rows, _ = _status_paths(tree, self._command)
                    if rows:
                        raise PublishFailure("workspace_contamination", "Publication tree changed before push")
                    push = (self.push_override(tree, attempt) if self.push_override else
                            self._command(["git", "push", self.remote, f"HEAD:refs/heads/{self.branch}"], tree))
                    if push.returncode == 0:
                        return PublishResult("published", "fast_forward", attempt, candidate.digest,
                                             candidate.generated_at_text, head, published)
                    failure = _classify_push(push.stderr)
                finally:
                    # Normal removal succeeds for a clean disposable tree. If a
                    # contamination test intentionally leaves it dirty, retain
                    # the original fail-closed classification; TemporaryDirectory
                    # removes only this new disposable path and a later prune
                    # clears the now-missing worktree registration.
                    _run(["git", "worktree", "remove", str(tree)], self.repository)
            if not failure.retryable:
                raise failure
            last_retryable = failure
            if attempt < self.max_attempts:
                self._backoff(attempt)
        message = str(last_retryable) if last_retryable else "Publication attempts exhausted"
        raise PublishFailure("retry_exhausted", message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--target", default=GLOBAL_CONFLICT_PATH)
    parser.add_argument("--max-attempts", type=int, default=4)
    parser.add_argument("--deadline-seconds", type=int, default=180)
    parser.add_argument("--backoff-seconds", type=int, default=5)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = GuardedSnapshotPublisher(
            args.repository, remote=args.remote, branch=args.branch, target=args.target,
            max_attempts=args.max_attempts, deadline_seconds=args.deadline_seconds,
            backoff_seconds=args.backoff_seconds,
        ).publish(args.candidate)
        report = result.as_dict()
        code = 0
    except (OSError, PublishFailure) as exc:
        report = {
            "schema": "eastern-axis.guarded-publication.v1",
            "status": "failed",
            "classification": getattr(exc, "classification", "local_io_failure"),
            "message": str(exc),
        }
        code = 1
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
