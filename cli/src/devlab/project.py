"""Подготовка служебных файлов в выбранной папке."""

from pathlib import Path


def ensure_state_ignored(folder: Path) -> None:
    path = folder / '.gitignore'
    if path.is_symlink():
        raise OSError('Не удалось обновить .gitignore: файл является символической ссылкой')
    content = path.read_bytes() if path.exists() else b''
    rules = content.splitlines()
    # Последнее явное правило имеет приоритет над предыдущим исключением.
    relevant = [line for line in rules if line in
                (b'state.json', b'/state.json', b'!state.json', b'!/state.json')]
    if relevant and not relevant[-1].startswith(b'!'):
        return
    newline = b'\r\n' if b'\r\n' in content else b'\n'
    separator = newline if content and not content.endswith(b'\n') else b''
    with path.open('ab') as stream:
        stream.write(separator + b'state.json' + newline)
