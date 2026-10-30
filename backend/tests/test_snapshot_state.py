"""Сетевые модели проверяются на снимках настоящего Git из CLI."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4

from pydantic import ValidationError
from app.api.schemas.snapshot import SnapshotReq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cli' / 'src'))
from devlab.git_state import read_state


class SnapshotStateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def git(self, *args, check=True):
        return subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                               '-C', str(self.folder), *args], check=check, capture_output=True)

    def validate(self, state):
        return SnapshotReq(schema_version=1, session_id=uuid4(), generation=1, version=1, state=state)

    def commit(self, text):
        (self.folder / 'file').write_text(text)
        self.git('add', '.')
        self.git('commit', '-m', 'test')

    def test_no_repository_and_unavailable(self):
        self.assertEqual(self.validate(read_state(self.folder)).state.kind, 'no_repository')
        self.assertEqual(self.validate(read_state(self.folder / 'absent')).state.kind, 'unavailable')

    def test_real_states_and_json_roundtrip(self):
        self.git('init', '-b', 'main')
        self.assertEqual(self.validate(read_state(self.folder)).state.head_kind, 'unborn')
        self.commit('base')
        self.git('tag', '-a', 'v1', '-m', 'tag')
        self.git('mv', 'file', 'renamed file')
        self.assertEqual(self.validate(read_state(self.folder)).state.files[0].original_path, 'file')
        self.git('reset', '--hard', 'HEAD')
        self.git('checkout', '--detach')
        self.assertEqual(self.validate(read_state(self.folder)).state.head_kind, 'detached')
        self.git('checkout', 'main')
        self.git('checkout', '-b', 'side')
        self.commit('side')
        self.git('checkout', 'main')
        self.commit('main')
        self.assertNotEqual(self.git('merge', 'side', check=False).returncode, 0)
        model = self.validate(read_state(self.folder))
        self.assertTrue(model.state.files[0].conflict)
        self.assertIn('MERGE_HEAD', model.state.operations)
        self.assertEqual(SnapshotReq.model_validate_json(model.model_dump_json()), model)

    def test_reject_invalid_state(self):
        self.git('init', '-b', 'main')
        self.commit('base')
        state = read_state(self.folder)
        for field, value in [('head', 'bad-hash'), ('branch', None), ('head_kind', 'detached'),
                             ('history_limit', 0), ('unknown', True)]:
            with self.subTest(field=field):
                invalid = copy.deepcopy(state)
                invalid[field] = value
                with self.assertRaises(ValidationError):
                    self.validate(invalid)
        with self.assertRaises(ValidationError):
            self.validate([])


if __name__ == '__main__':
    unittest.main()
