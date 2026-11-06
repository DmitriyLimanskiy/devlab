import os
import subprocess
from pathlib import Path


class UnstableRepository(Exception):
    pass


def git(folder, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", LC_ALL="C")
    result = subprocess.run(
        ["git", "-C", str(folder), *args],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def _text(data):
    return data.decode("utf-8", errors="surrogateescape")


def read_state(folder):
    folder = Path(folder)
    if not folder.is_dir():
        return {"kind": "unavailable", "path": str(folder)}
    try:
        root = _text(git(folder, "rev-parse", "--show-toplevel")).strip()
    except RuntimeError:
        # Отличаем отсутствие репозитория от ошибки чтения существующего .git
        if any((parent / ".git").exists() for parent in [folder, *folder.parents]):
            raise
        return {"kind": "no_repository", "path": str(folder)}
    branch = None
    head = None
    try:
        branch = _text(git(root, "symbolic-ref", "--quiet", "--short", "HEAD")).strip()
    except RuntimeError:
        pass
    try:
        head = _text(git(root, "rev-parse", "--verify", "HEAD")).strip()
    except RuntimeError:
        if branch is None:
            raise
    entries = git(
        root, "status", "--porcelain=v1", "-z", "--untracked-files=all"
    ).split(b"\0")
    files = []
    index = 0
    while index < len(entries) and entries[index]:
        entry = entries[index]
        status = entry[:2].decode("ascii")
        item = {
            "path": _text(entry[3:]),
            "index": status[0],
            "worktree": status[1],
            "conflict": status in {"DD", "AU", "UD", "UA", "DU", "AA", "UU"},
        }
        if "R" in status or "C" in status:
            index += 1
            item["original_path"] = _text(entries[index])
        files.append(item)
        index += 1
    refs = _text(
        git(
            root,
            "for-each-ref",
            "--format=%(refname) %(objectname)",
            "refs/heads",
            "refs/tags",
        )
    ).splitlines()
    # refs сохраняют исходный объект, ref_commits раскрывает теги до коммита
    ref_commits = {}
    for ref in refs:
        name = ref.rsplit(" ", 1)[0]
        try:
            ref_commits[name] = _text(
                git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
            ).strip()
        except RuntimeError:
            # Git разрешает теги на деревья и blobs, у них нет линии коммитов
            continue
    roots = sorted(set(ref_commits.values()) | ({head} if head else set()))
    commits = []
    history_truncated = False
    if roots:
        # Дополнительный коммит отличает точное попадание в лимит от обрезки
        lines = git(
            root, "log", "--topo-order", "-201", "--format=%H %P", *roots, "--"
        ).splitlines()
        history_truncated = len(lines) > 200
        for line in lines[:200]:
            parts = line.decode("ascii").split()
            commits.append({"id": parts[0], "parents": parts[1:]})
    known = {commit["id"] for commit in commits}
    history_boundary = sorted(
        {
            parent
            for commit in commits
            for parent in commit["parents"]
            if parent not in known
        }
    )
    is_shallow = (
        _text(git(root, "rev-parse", "--is-shallow-repository")).strip() == "true"
    )
    gitdir = Path(_text(git(root, "rev-parse", "--absolute-git-dir")).strip())
    operations = [
        name
        for name in (
            "MERGE_HEAD",
            "CHERRY_PICK_HEAD",
            "REVERT_HEAD",
            "rebase-merge",
            "rebase-apply",
            "BISECT_LOG",
        )
        if (gitdir / name).exists()
    ]
    return {
        "kind": "repository",
        "path": root,
        "head": head,
        "branch": branch,
        "head_kind": "unborn" if head is None else ("branch" if branch else "detached"),
        "files": files,
        "refs": refs,
        "commits": commits,
        "ref_commits": ref_commits,
        "history_truncated": history_truncated,
        "history_boundary": history_boundary,
        "is_shallow": is_shallow,
        "history_limit": 200,
        "operations": operations,
    }


def stable_state(folder):
    first = read_state(folder)
    second = read_state(folder)
    if first != second:
        raise UnstableRepository("Репозиторий меняется во время чтения")
    return second
