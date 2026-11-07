import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from devlab.practice.git_state import stable_state
from devlab.practice.observer import Observer


class GitStateTest(unittest.TestCase):
    def setUp(self):
        """Подготовить временную папку и данные для независимого теста"""
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name) / "project"
        self.folder.mkdir()

    def tearDown(self):
        """Удалить временные файлы завершённого теста"""
        self.temp.cleanup()

    def git(self, *args, check=True):
        """Выполнить Git во временном тестовом репозитории"""
        return subprocess.run(
            ["git", "-C", str(self.folder), *args], check=check, capture_output=True
        )

    def initialize(self):
        """Создать временный Git-репозиторий с тестовой подписью автора"""
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")

    def commit(self, content):
        """Создать тестовый коммит в локальном репозитории"""
        (self.folder / "file").write_text(content)
        self.git("add", ".")
        self.git("commit", "-m", "test")

    def test_empty_index_detached_conflict(self):
        """Проверить пустой репозиторий, индекс, detached HEAD и конфликт слияния"""
        self.assertEqual(stable_state(self.folder)["kind"], "no_repository")
        self.initialize()
        self.assertEqual(stable_state(self.folder)["head_kind"], "unborn")
        (self.folder / "space name").write_text("new")
        self.assertEqual(stable_state(self.folder)["files"][0]["index"], "?")
        self.git("add", ".")
        self.assertEqual(stable_state(self.folder)["files"][0]["index"], "A")
        self.commit("base\n")
        self.git("checkout", "--detach")
        self.assertEqual(stable_state(self.folder)["head_kind"], "detached")
        self.git("checkout", "main")
        self.git("checkout", "-b", "side")
        self.commit("side\n")
        self.git("checkout", "main")
        self.commit("main\n")
        self.assertNotEqual(self.git("merge", "side", check=False).returncode, 0)
        state = stable_state(self.folder)
        self.assertIn("MERGE_HEAD", state["operations"])
        self.assertTrue(any(file["conflict"] for file in state["files"]))
        self.assertEqual(len(state["commits"]), 3)

    def test_rename_and_untracked_paths_preserve_porcelain_boundaries(self):
        """Проверить переименование и неотслеживаемые пути с пробелами и переносами строк"""
        self.initialize()
        original = "old name\nwith newline"
        renamed = "new name\nwith newline"
        untracked = "untracked name\nwith newline"
        (self.folder / original).write_text("content")
        self.git("add", ".")
        self.git("commit", "-m", "initial")
        self.git("mv", original, renamed)
        (self.folder / untracked).write_text("new")

        files = {item["path"]: item for item in stable_state(self.folder)["files"]}
        self.assertEqual(set(files), {renamed, untracked})
        self.assertEqual(
            files[renamed],
            {
                "path": renamed,
                "original_path": original,
                "index": "R",
                "worktree": " ",
                "conflict": False,
            },
        )
        self.assertEqual(files[untracked]["index"], "?")
        self.assertNotIn("original_path", files[untracked])

    def test_merge_graph_survives_branch_deletion(self):
        """Проверить сохранение связей слияния после удаления ветки"""
        self.initialize()
        self.commit("base")
        base = stable_state(self.folder)["head"]
        self.git("checkout", "-b", "feature")
        self.git("commit", "--allow-empty", "-m", "feature")
        feature = stable_state(self.folder)["head"]
        self.git("checkout", "main")
        self.git("commit", "--allow-empty", "-m", "main")
        main = stable_state(self.folder)["head"]
        self.git("merge", "--no-ff", "feature", "-m", "merge")
        self.git("branch", "-d", "feature")
        state = stable_state(self.folder)
        commits = {c["id"]: c["parents"] for c in state["commits"]}
        self.assertEqual(commits[state["head"]], [main, feature])
        self.assertEqual(commits[feature], [base])
        self.assertEqual(commits[main], [base])
        self.assertFalse(state["history_truncated"])
        self.assertEqual(state["history_boundary"], [])
        order = {c["id"]: i for i, c in enumerate(state["commits"])}
        for commit in state["commits"]:
            for parent in commit["parents"]:
                self.assertLess(order[commit["id"]], order[parent])

    def test_unborn_head_preserves_other_branches_and_tag_targets(self):
        """Проверить чтение других веток и целей тегов при unborn HEAD"""
        self.initialize()
        self.commit("base")
        head = stable_state(self.folder)["head"]
        self.git("tag", "-a", "v1", "-m", "release")
        self.git("tag", "-a", "nested", "v1", "-m", "nested")
        tree = self.git("rev-parse", "HEAD^{tree}").stdout.decode().strip()
        self.git("tag", "tree", tree)
        self.git("checkout", "--orphan", "empty")
        state = stable_state(self.folder)
        self.assertEqual(state["head_kind"], "unborn")
        self.assertEqual(state["commits"], [{"id": head, "parents": []}])
        self.assertEqual(state["ref_commits"]["refs/tags/v1"], head)
        self.assertEqual(state["ref_commits"]["refs/tags/nested"], head)
        self.assertNotIn("refs/tags/tree", state["ref_commits"])
        self.assertNotIn("refs/tags/v1 " + head, state["refs"])

    def test_history_limit_and_boundary(self):
        """Проверить точный лимит истории и ссылки на родителей вне снимка"""
        self.initialize()
        # commit-tree создаёт настоящую историю без сотен изменений рабочего дерева
        tree = self.git("mktree").stdout.decode().strip()
        parent = None
        for i in range(201):
            args = ["commit-tree", tree, "-m", str(i)]
            if parent:
                args += ["-p", parent]
            parent = self.git(*args).stdout.decode().strip()
            if i == 199:
                self.git("update-ref", "refs/heads/main", parent)
                self.assertFalse(stable_state(self.folder)["history_truncated"])
        self.git("update-ref", "refs/heads/main", parent)
        state = stable_state(self.folder)
        self.assertTrue(state["history_truncated"])
        self.assertEqual(len(state["commits"]), 200)
        self.assertEqual(state["history_boundary"], state["commits"][-1]["parents"])
        self.assertFalse(state["is_shallow"])

    def test_shallow_clone_marks_incomplete_history(self):
        """Проверить обозначение неполной истории shallow-клона"""
        self.initialize()
        self.commit("first")
        self.commit("second")
        clone = Path(self.temp.name) / "shallow"
        subprocess.run(
            ["git", "clone", "--depth=1", self.folder.as_uri(), str(clone)],
            check=True,
            capture_output=True,
        )
        state = stable_state(clone)
        self.assertTrue(state["is_shallow"])
        self.assertFalse(state["history_truncated"])
        self.assertEqual(len(state["commits"]), 1)

    def test_snapshot_inside_repository_does_not_change_itself(self):
        """Проверить исключение локального снимка из собственных статусов Git"""
        self.initialize()
        read, write = os.pipe()
        try:
            snapshot = self.folder / "state.json"
            observer = Observer(
                self.folder,
                read,
                snapshot,
                Path(self.temp.name) / "command-status.json",
            )
            observer.refresh()
            initial = snapshot.read_bytes()
            observer.refresh()
            observer.refresh()
            self.assertEqual(snapshot.read_bytes(), initial)
            self.assertEqual(observer.version, 1)
            self.assertEqual(observer.state["files"], [])
        finally:
            os.close(read)
            os.close(write)

    def test_preserve_existing_until_next_change(self):
        """Проверить сохранение прежнего state.json до изменения репозитория"""
        self.initialize()
        read, write = os.pipe()
        try:
            snapshot = self.folder / "state.json"
            original = '{"version": 12, "state": "previous"}'
            snapshot.write_text(original)
            observer = Observer(self.folder, read, snapshot)
            observer.preserve_existing = True
            observer.refresh()
            observer.refresh()
            self.assertEqual(snapshot.read_text(), original)
            (self.folder / "new").write_text("change")
            observer.refresh()
            self.assertEqual(json.loads(snapshot.read_text())["version"], 13)
        finally:
            os.close(read)
            os.close(write)

    def test_commands_without_git_changes_do_not_enqueue_snapshots(self):
        """Проверить отсутствие новых версий доставки после неизменяющих команд"""
        from devlab.cli.api import ApiClient, Connection
        from devlab.practice.sync import SnapshotSender

        self.initialize()
        self.commit("base")
        sender = SnapshotSender(
            ApiClient("http://127.0.0.1:8080"),
            Connection("c7e1af73-5110-4c3d-9190-f8a3ef34d4ef", 1, "test-key"),
            self.folder,
            Path(self.temp.name) / "pending",
        )
        read, write = os.pipe()
        try:
            observer = Observer(
                self.folder,
                read,
                self.folder / "state.json",
                Path(self.temp.name) / "command-status.json",
                on_state=sender.publish,
            )
            observer.refresh()
            for command in (
                "pwd",
                "git status",
                "git log --oneline",
                "git show missing-ref",
            ):
                result = subprocess.run(
                    ["bash", "-c", command],
                    cwd=self.folder,
                    capture_output=True,
                    check=False,
                )
                observer.refresh(result.returncode)
                observer.refresh()
            self.assertEqual(observer.version, 1)
            self.assertEqual(sender.version, 1)
            self.assertEqual(len(sender.queue), 1)
            (self.folder / "file").write_text("changed")
            observer.refresh(0)
            self.assertEqual(sender.version, 1)
            self.git("add", "file")
            observer.refresh(0)
            self.assertEqual(sender.version, 1)
            observer.refresh(0)
            self.assertEqual(sender.version, 1)
        finally:
            os.close(read)
            os.close(write)

    def test_file_polling_waits_for_command_before_delivery(self):
        """Проверить ожидание завершения команды перед доставкой опрошенного состояния"""
        self.initialize()
        self.commit("base")
        read, write = os.pipe()
        delivered = []
        try:
            observer = Observer(
                self.folder,
                read,
                self.folder / "state.json",
                Path(self.temp.name) / "command-status.json",
                on_state=delivered.append,
            )
            observer.refresh()
            self.assertEqual(len(delivered), 1)
            for text in ("edit one", "edit two", "edit three"):
                (self.folder / "file").write_text(text)
                observer.refresh()
            self.assertEqual(len(delivered), 1)
            self.assertEqual(observer.state["files"][0]["worktree"], "M")
            observer.refresh(0)
            self.assertEqual(len(delivered), 2)
            self.assertEqual(delivered[-1], observer.state)
        finally:
            os.close(read)
            os.close(write)

    def test_external_changes_and_deduplication(self):
        """Проверить обнаружение внешних правок без лишних версий снимка"""
        self.initialize()
        read, write = os.pipe()
        snapshot = Path(self.temp.name) / "state.json"
        observer = Observer(self.folder, read, snapshot)
        observer.refresh()
        initial = snapshot.read_bytes()
        observer.refresh(1)
        self.assertEqual(initial, snapshot.read_bytes())
        observer.thread.start()
        try:
            (self.folder / "external").write_text("IDE edit")
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                state = json.loads(snapshot.read_text())
                if state["version"] > 1:
                    break
                time.sleep(0.1)
            self.assertEqual(state["state"]["files"][0]["path"], "external")
            self.assertEqual(state["version"], 2)
        finally:
            observer.close()
            os.close(read)
            os.close(write)


if __name__ == "__main__":
    unittest.main()
