"""Точка входа и оформление терминальной сессии."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from .project import ensure_state_ignored
from .api import ApiClient, ApiError
from .connection import choose_connection


def main() -> int:
    launch_folder = Path.cwd()
    if sys.argv[1:]:
        print(
            "Запуск: devlab. Выход из оболочки: exit или Ctrl+D.",
            file=sys.stderr,
        )
        return 2
    if sys.platform != "darwin":
        print("Версия для macOS.", file=sys.stderr)
        return 1
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Запустите devlab в интерактивном терминале.", file=sys.stderr)
        return 1
    bash = shutil.which("bash")
    if bash is None:
        print("Не найден bash в PATH.", file=sys.stderr)
        return 1

    from .terminal import run_bash

    color = "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"
    accent, reset = ("\033[36m", "\033[0m") if color else ("", "")
    print(f"\n{accent}  ◇  D E V L A B{reset}  /  0.1.0")
    print("  Локальная среда · bash")
    print("  Выход: exit или Ctrl+D\n", flush=True)

    client = connection = None
    try:
        if os.environ.get('DEVLAB_OFFLINE') != '1':
            try:
                client = ApiClient(os.environ.get('DEVLAB_SERVER_URL', 'http://127.0.0.1:8080'))
            except ApiError as error:
                print(f"  {error} Продолжаем локально.")
            if client is not None:
                connection = choose_connection(client)
        if connection is None:
            print("  Локальный режим.\n")
    except (EOFError, KeyboardInterrupt):
        print("\n  Запуск отменён.")
        return 0

    while True:
        try:
            choice = input(f"  Папка проекта [Enter — {launch_folder}]: ").strip()
            folder = Path(choice).expanduser().resolve() if choice else launch_folder
            if not folder.is_dir() or not os.access(folder, os.R_OK | os.X_OK):
                print("  Выберите существующую доступную папку.")
                continue
            break
        except (EOFError, KeyboardInterrupt):
            print("\n  Запуск отменён.")
            return 0
    if shutil.which("git") is None:
        print("Для наблюдения требуется Git в PATH.", file=sys.stderr)
        return 1

    # Временный rc не затрагивает пользовательские настройки и историю bash.
    with tempfile.TemporaryDirectory(prefix="devlab-") as directory:
        rc = Path(directory) / "bashrc"
        prompt = r"\[\e[36m\]devlab\[\e[0m\] \w > " if color else r"devlab \w > "
        snapshot = folder / "state.json"
        try:
            overwrite = True
            if snapshot.exists() or snapshot.is_symlink():
                while True:
                    answer = input("  state.json уже существует. Перезаписать сейчас? [yes/no]: ").strip().lower()
                    if answer in {'yes', 'no'}:
                        overwrite = answer == 'yes'
                        break
                    print("  Введите yes или no.")
                if snapshot.is_symlink() or not snapshot.is_file():
                    print("Нельзя перезаписать ссылку или каталог state.json.", file=sys.stderr)
                    return 1
                if not overwrite:
                    print("  Текущий state.json сохранён. Новые изменения будут записываться.")
            # Создаём файл до запуска bash, чтобы сразу проверить право записи.
            ensure_state_ignored(folder)
            if overwrite and not snapshot.exists():
                with snapshot.open('x') as stream:
                    json.dump({'generator': 'devlab-cli'}, stream)
        except (EOFError, KeyboardInterrupt):
            print("\n  Запуск отменён.")
            return 0
        except (OSError, ValueError, AttributeError) as error:
            print(f"Не удалось подготовить файлы проекта: {error}", file=sys.stderr)
            return 1
        print(f"  Локальный снимок: {snapshot}\n", flush=True)
        rc.write_text(
            f"PS1='{prompt}'\nPS2='... > '\nunset HISTFILE\n", encoding="utf-8"
        )
        sender = None
        if connection is not None:
            from .sync import SnapshotSender
            sender = SnapshotSender(client, connection, folder)
            print("  Синхронизация будет работать в фоне.\n", flush=True)
        try:
            status = run_bash(bash, str(rc), folder, snapshot, overwrite, sender=sender)
        except OSError as error:
            print(
                f"DevLab: не удалось выполнить терминальную сессию: {error}",
                file=sys.stderr,
            )
            return 1
    print("\n  Сессия DevLab завершена.")
    return status
