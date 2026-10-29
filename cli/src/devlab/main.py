"""Точка входа и оформление терминальной сессии."""

import os
import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
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

    # Временный rc не затрагивает пользовательские настройки и историю bash.
    with tempfile.TemporaryDirectory(prefix="devlab-") as directory:
        rc = Path(directory) / "bashrc"
        prompt = r"\[\e[36m\]devlab\[\e[0m\] \w > " if color else r"devlab \w > "
        rc.write_text(
            f"PS1='{prompt}'\nPS2='... > '\nunset HISTFILE\n", encoding="utf-8"
        )
        try:
            status = run_bash(bash, str(rc))
        except OSError as error:
            print(
                f"DevLab: не удалось выполнить терминальную сессию: {error}",
                file=sys.stderr,
            )
            return 1
    print("\n  Сессия DevLab завершена.")
    return status
