"""Реальные репозитории и внешние изменения, без подмены Git моками"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from devlab.git_state import stable_state
from devlab.observer import Observer


class GitStateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name) / 'project'
        self.folder.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args, check=True):
        return subprocess.run(['git', '-C', str(self.folder), *args], check=check,
                              capture_output=True)

    def initialize(self):
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')

    def commit(self, content):
        (self.folder / 'file').write_text(content)
        self.git('add', '.')
        self.git('commit', '-m', 'test')

    def test_empty_index_detached_conflict(self):
        self.assertEqual(stable_state(self.folder)['kind'], 'no_repository')
        self.initialize()
        self.assertEqual(stable_state(self.folder)['head_kind'], 'unborn')
        (self.folder / 'space name').write_text('new')
        self.assertEqual(stable_state(self.folder)['files'][0]['index'], '?')
        self.git('add', '.')
        self.assertEqual(stable_state(self.folder)['files'][0]['index'], 'A')
        self.commit('base\n')
        self.git('checkout', '--detach')
        self.assertEqual(stable_state(self.folder)['head_kind'], 'detached')
        self.git('checkout', 'main')
        self.git('checkout', '-b', 'side')
        self.commit('side\n')
        self.git('checkout', 'main')
        self.commit('main\n')
        self.assertNotEqual(self.git('merge', 'side', check=False).returncode, 0)
        state = stable_state(self.folder)
        self.assertIn('MERGE_HEAD', state['operations'])
        self.assertTrue(any(file['conflict'] for file in state['files']))
        self.assertEqual(len(state['commits']), 3)

    def test_snapshot_inside_repository_does_not_change_itself(self):
        self.initialize()
        read, write = os.pipe()
        try:
            snapshot = self.folder / 'state.json'
            observer = Observer(self.folder, read, snapshot,
                                Path(self.temp.name) / 'command-status.json')
            observer.refresh()
            initial = snapshot.read_bytes()
            observer.refresh()
            observer.refresh()
            self.assertEqual(snapshot.read_bytes(), initial)
            self.assertEqual(observer.version, 1)
            self.assertEqual(observer.state['files'], [])
        finally:
            os.close(read)
            os.close(write)

    def test_preserve_existing_until_next_change(self):
        self.initialize()
        read, write = os.pipe()
        try:
            snapshot = self.folder / 'state.json'
            original = '{"version": 12, "state": "previous"}'
            snapshot.write_text(original)
            observer = Observer(self.folder, read, snapshot)
            observer.preserve_existing = True
            observer.refresh()
            observer.refresh()
            self.assertEqual(snapshot.read_text(), original)
            (self.folder / 'new').write_text('change')
            observer.refresh()
            self.assertEqual(json.loads(snapshot.read_text())['version'], 13)
        finally:
            os.close(read)
            os.close(write)

    def test_external_changes_and_deduplication(self):
        self.initialize()
        read, write = os.pipe()
        snapshot = Path(self.temp.name) / 'state.json'
        observer = Observer(self.folder, read, snapshot)
        observer.refresh()
        initial = snapshot.read_bytes()
        observer.refresh(1)
        self.assertEqual(initial, snapshot.read_bytes())
        observer.thread.start()
        try:
            (self.folder / 'external').write_text('IDE edit')
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                state = json.loads(snapshot.read_text())
                if state['version'] > 1:
                    break
                time.sleep(0.1)
            self.assertEqual(state['state']['files'][0]['path'], 'external')
            self.assertEqual(state['version'], 2)
        finally:
            observer.close()
            os.close(read)
            os.close(write)


if __name__ == '__main__':
    unittest.main()
