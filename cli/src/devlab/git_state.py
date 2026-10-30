"""Чтение Git без shell и без содержимого рабочих файлов"""
import os
import subprocess
from pathlib import Path


class UnstableRepository(Exception):
    pass


def git(folder, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', LC_ALL='C')
    result = subprocess.run(['git', '-C', str(folder), *args], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace').strip())
    return result.stdout


def _text(data):
    return data.decode('utf-8', errors='surrogateescape')


def read_state(folder):
    folder = Path(folder)
    if not folder.is_dir():
        return {'kind': 'unavailable', 'path': str(folder)}
    try:
        root = _text(git(folder, 'rev-parse', '--show-toplevel')).strip()
    except RuntimeError:
        # Отличаем отсутствие репозитория от ошибки чтения существующего .git
        if any((parent / '.git').exists() for parent in [folder, *folder.parents]):
            raise
        return {'kind': 'no_repository', 'path': str(folder)}
    branch = None
    head = None
    try:
        branch = _text(git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD')).strip()
    except RuntimeError:
        pass
    try:
        head = _text(git(root, 'rev-parse', '--verify', 'HEAD')).strip()
    except RuntimeError:
        if branch is None:
            raise
    entries = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all').split(b'\0')
    files = []
    index = 0
    while index < len(entries) and entries[index]:
        entry = entries[index]
        status = entry[:2].decode('ascii')
        item = {'path': _text(entry[3:]), 'index': status[0], 'worktree': status[1],
                'conflict': status in {'DD', 'AU', 'UD', 'UA', 'DU', 'AA', 'UU'}}
        if 'R' in status or 'C' in status:
            index += 1
            item['original_path'] = _text(entries[index])
        files.append(item)
        index += 1
    refs = _text(git(root, 'for-each-ref', '--format=%(refname) %(objectname)',
                     'refs/heads', 'refs/tags')).splitlines()
    commits = []
    if head:
        for line in git(root, 'log', '--all', 'HEAD', '-200', '--format=%H %P').splitlines():
            parts = line.decode('ascii').split()
            commits.append({'id': parts[0], 'parents': parts[1:]})
    gitdir = Path(_text(git(root, 'rev-parse', '--absolute-git-dir')).strip())
    operations = [name for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD',
                                   'rebase-merge', 'rebase-apply', 'BISECT_LOG')
                  if (gitdir / name).exists()]
    return {'kind': 'repository', 'path': root, 'head': head, 'branch': branch,
            'head_kind': 'unborn' if head is None else ('branch' if branch else 'detached'),
            'files': files, 'refs': refs, 'commits': commits, 'history_limit': 200,
            'operations': operations}


def stable_state(folder):
    first = read_state(folder)
    second = read_state(folder)
    if first != second:
        raise UnstableRepository('Репозиторий меняется во время чтения')
    return second
