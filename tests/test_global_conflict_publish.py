import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "guarded_snapshot_publish", ROOT / "scripts/guarded_snapshot_publish.py")
publish = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = publish
SPEC.loader.exec_module(publish)
TARGET = publish.GLOBAL_CONFLICT_PATH


def git(repo, *args, check=True):
    return subprocess.run(["git", *args], cwd=repo, check=check,
                          text=True, capture_output=True)


def snapshot(stamp, *, marker="candidate"):
    return {
        "schemaVersion": 1,
        "generatedAt": stamp,
        "status": "ok",
        "category": "Defense, Security & Cyber",
        "analyst": {"commandEligible": 0, "marker": marker},
        "sources": {
            "ucdp": {"url": "https://ucdp.uu.se/downloads/", "releases": {
                "period": {"url": "https://ucdp.uu.se/downloads/example.csv"}}},
            "rss": {"feeds": [{"url": "https://news.un.org/feed.xml"}]},
        },
        "measurement": {"latestCodedEvent": "2026-10-31", "dataAgeDays": 28},
        "summary": {"hotspots": 0},
        "zones": [],
        "limitations": ["Test fixture"],
    }


def write_snapshot(path, stamp, *, marker="candidate"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot(stamp, marker=marker), sort_keys=True) + "\n")


class LocalRemote:
    def __init__(self, initial=None):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.remote.mkdir()
        git(self.remote, "init", "--bare", "--initial-branch=main")
        seed = self.root / "seed"
        seed.mkdir()
        git(seed, "init", "--initial-branch=main")
        git(seed, "config", "user.email", "test@example.invalid")
        git(seed, "config", "user.name", "Test")
        (seed / "README.md").write_text("seed\n")
        if initial:
            write_snapshot(seed / TARGET, initial[0], marker=initial[1])
        git(seed, "add", ".")
        git(seed, "commit", "-m", "seed")
        git(seed, "remote", "add", "origin", str(self.remote))
        git(seed, "push", "-u", "origin", "main")
        self.repository = Path(self.clone("publisher"))

    def clone(self, name):
        destination = self.root / name
        git(self.root, "clone", str(self.remote), str(destination))
        git(destination, "config", "user.email", "test@example.invalid")
        git(destination, "config", "user.name", "Test")
        return destination

    def candidate(self, stamp, marker="candidate"):
        path = self.root / f"candidate-{marker}.json"
        write_snapshot(path, stamp, marker=marker)
        return path

    def advance(self, name, *, stamp=None, marker="remote", unrelated=False):
        other = Path(self.clone(name))
        if unrelated:
            (other / f"{name}.txt").write_text("unrelated\n")
            git(other, "add", f"{name}.txt")
        else:
            write_snapshot(other / TARGET, stamp, marker=marker)
            git(other, "add", TARGET)
        git(other, "commit", "-m", name)
        git(other, "push", "origin", "main")

    def show(self, spec):
        return git(self.remote, "show", spec).stdout

    def close(self):
        self.temp.cleanup()


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.sandboxes = []

    def sandbox(self, initial=None):
        value = LocalRemote(initial)
        self.sandboxes.append(value)
        return value

    def tearDown(self):
        for value in self.sandboxes:
            value.close()

    def publisher(self, box, **kwargs):
        return publish.GuardedSnapshotPublisher(
            box.repository, backoff_seconds=0, sleep=lambda _: None, **kwargs)

    def test_initial_publish_and_identical_content_noop(self):
        box = self.sandbox()
        candidate = box.candidate("2026-11-28T01:00:00Z")
        result = self.publisher(box).publish(candidate)
        self.assertEqual((result.status, result.classification), ("published", "fast_forward"))
        again = self.publisher(box).publish(candidate)
        self.assertEqual((again.status, again.classification), ("no-op", "identical_snapshot"))

    def test_older_and_equal_changed_candidates_fail_closed(self):
        box = self.sandbox(("2026-11-28T02:00:00Z", "retained"))
        with self.assertRaisesRegex(publish.PublishFailure, "older") as caught:
            self.publisher(box).publish(box.candidate("2026-11-28T01:00:00Z", "old"))
        self.assertEqual(caught.exception.classification, "candidate_older")
        with self.assertRaises(publish.PublishFailure) as caught:
            self.publisher(box).publish(box.candidate("2026-11-28T02:00:00Z", "changed"))
        self.assertEqual(caught.exception.classification, "equal_timestamp_changed_content")

    def test_unrelated_concurrent_update_rebuilds_from_latest_head(self):
        box = self.sandbox(("2026-11-28T00:00:00Z", "retained"))
        fired = []
        def race(_tree, attempt):
            if attempt == 1:
                box.advance("unrelated-race", unrelated=True)
                fired.append(attempt)
        result = self.publisher(box, before_push=race).publish(
            box.candidate("2026-11-28T01:00:00Z"))
        self.assertEqual(result.attempts, 2)
        self.assertEqual(fired, [1])
        self.assertEqual(git(box.remote, "diff-tree", "--no-commit-id", "--name-only", "-r", "main").stdout.splitlines(), [TARGET])
        self.assertIn("unrelated-race.txt", git(box.remote, "ls-tree", "-r", "--name-only", "main").stdout)

    def test_same_file_concurrency_is_revalidated_on_next_attempt(self):
        box = self.sandbox(("2026-11-28T00:00:00Z", "retained"))
        def race(_tree, attempt):
            if attempt == 1:
                box.advance("same-file-race", stamp="2026-11-28T02:00:00Z", marker="newer")
        with self.assertRaises(publish.PublishFailure) as caught:
            self.publisher(box, before_push=race).publish(
                box.candidate("2026-11-28T01:00:00Z"))
        self.assertEqual(caught.exception.classification, "candidate_older")
        self.assertIn('"marker": "newer"', box.show(f"main:{TARGET}"))

    def test_malformed_candidate_remote_and_failed_remote_read(self):
        box = self.sandbox(("2026-11-28T00:00:00Z", "retained"))
        invalid = box.root / "invalid.json"
        invalid.write_text("not json")
        with self.assertRaises(publish.PublishFailure) as caught:
            self.publisher(box).publish(invalid)
        self.assertEqual(caught.exception.classification, "malformed_snapshot")

        malformed = self.sandbox()
        other = Path(malformed.clone("malformed-writer"))
        target = other / TARGET
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}")
        git(other, "add", TARGET)
        git(other, "commit", "-m", "malformed")
        git(other, "push", "origin", "main")
        with self.assertRaises(publish.PublishFailure) as caught:
            self.publisher(malformed).publish(malformed.candidate("2026-11-28T01:00:00Z"))
        self.assertEqual(caught.exception.classification, "malformed_snapshot")

        class BrokenRemote(publish.GuardedSnapshotPublisher):
            def _remote_snapshot(self, _head):
                raise publish.PublishFailure("remote_read_failure", "controlled read failure")
        with self.assertRaises(publish.PublishFailure) as caught:
            BrokenRemote(box.repository, backoff_seconds=0).publish(
                box.candidate("2026-11-28T03:00:00Z", "read"))
        self.assertEqual(caught.exception.classification, "remote_read_failure")

    def test_missing_timestamp_and_provenance_are_rejected(self):
        box = self.sandbox()
        for name, mutation, classification in (
            ("missing", lambda doc: doc.pop("generatedAt"), "malformed_snapshot"),
            ("offset", lambda doc: doc.update(generatedAt="2026-11-28T01:00:00+01:00"), "malformed_snapshot"),
            ("source", lambda doc: doc.update(sources={}), "provenance_failure"),
            ("observation", lambda doc: doc.update(measurement={"latestCodedEvent": None, "dataAgeDays": None}), "provenance_failure"),
        ):
            document = snapshot("2026-11-28T01:00:00Z")
            mutation(document)
            path = box.root / f"{name}.json"
            path.write_text(json.dumps(document))
            with self.subTest(name=name), self.assertRaises(publish.PublishFailure) as caught:
                self.publisher(box).publish(path)
            self.assertEqual(caught.exception.classification, classification)

    def test_target_path_is_strictly_allowlisted(self):
        box = self.sandbox()
        with self.assertRaises(publish.PublishFailure) as caught:
            publish.GuardedSnapshotPublisher(box.repository, target="README.md")
        self.assertEqual(caught.exception.classification, "unauthorized_path")

    def test_tracked_staged_and_untracked_contamination_are_rejected_before_push(self):
        for kind in ("tracked", "staged", "untracked"):
            box = self.sandbox(("2026-11-28T00:00:00Z", "retained"))
            def contaminate(tree, _attempt, kind=kind):
                if kind == "tracked":
                    (tree / "README.md").write_text("changed\n")
                else:
                    (tree / "intruder.txt").write_text("intruder\n")
                    if kind == "staged":
                        git(tree, "add", "intruder.txt")
            with self.subTest(kind=kind), self.assertRaises(publish.PublishFailure) as caught:
                self.publisher(box, before_push=contaminate).publish(
                    box.candidate("2026-11-28T01:00:00Z", kind))
            self.assertEqual(caught.exception.classification, "workspace_contamination")

    def test_auth_rejection_is_not_retried(self):
        box = self.sandbox(("2026-11-28T00:00:00Z", "retained"))
        attempts = []
        def reject(_tree, attempt):
            attempts.append(attempt)
            return subprocess.CompletedProcess([], 1, "", "remote: protected branch permission denied")
        with self.assertRaises(publish.PublishFailure) as caught:
            self.publisher(box, push_override=reject).publish(
                box.candidate("2026-11-28T01:00:00Z"))
        self.assertEqual(caught.exception.classification, "authorization_or_protection")
        self.assertEqual(attempts, [1])

    def test_retry_is_bounded_for_permanent_non_fast_forward(self):
        box = self.sandbox(("2026-11-28T00:00:00Z", "retained"))
        attempts = []
        def reject(_tree, attempt):
            attempts.append(attempt)
            return subprocess.CompletedProcess([], 1, "", "rejected (non-fast-forward)")
        with self.assertRaises(publish.PublishFailure) as caught:
            self.publisher(box, max_attempts=3, push_override=reject).publish(
                box.candidate("2026-11-28T01:00:00Z"))
        self.assertEqual(caught.exception.classification, "retry_exhausted")
        self.assertEqual(attempts, [1, 2, 3])

    def test_total_deadline_prevents_backoff_past_budget(self):
        box = self.sandbox(("2026-11-28T00:00:00Z", "retained"))
        def reject(_tree, _attempt):
            return subprocess.CompletedProcess([], 1, "", "rejected (non-fast-forward)")
        publisher = publish.GuardedSnapshotPublisher(
            box.repository, max_attempts=4, deadline_seconds=1, backoff_seconds=1,
            sleep=lambda _: None, push_override=reject)
        with self.assertRaises(publish.PublishFailure) as caught:
            publisher.publish(box.candidate("2026-11-28T01:00:00Z"))
        self.assertEqual(caught.exception.classification, "deadline_exhausted")


class WorkflowIsolationTests(unittest.TestCase):
    def test_analysis_check_name_and_least_privilege_are_preserved(self):
        workflow = (ROOT / '.github/workflows/eastern-axis-global-conflict-analyst.yml').read_text()
        self.assertIn('\n  global-conflict:\n', workflow)
        self.assertRegex(workflow, r'permissions:\n  contents: read')
        self.assertRegex(workflow, r'publish-snapshot:[\s\S]+?permissions:\n      contents: write')
        self.assertIn("github.event_name != 'pull_request'", workflow)

    def test_workflow_uses_real_publisher_and_no_rebase_or_destructive_retry(self):
        workflow = (ROOT / '.github/workflows/eastern-axis-global-conflict-analyst.yml').read_text()
        self.assertIn('scripts/guarded_snapshot_publish.py', workflow)
        for forbidden in ('git rebase', 'git reset --hard', 'git stash', 'git push --force', 'git clean'):
            self.assertNotIn(forbidden, workflow)
        source = (ROOT / 'scripts/guarded_snapshot_publish.py').read_text()
        self.assertNotIn('"rebase"', source)
        self.assertIn('"worktree", "add", "--detach"', source)


if __name__ == "__main__":
    unittest.main()
