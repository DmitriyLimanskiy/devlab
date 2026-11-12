import argparse
import os
from pathlib import Path

from .api.cagalog import Catalog


def main() -> int:
    """Предложить выбрать папку проекта"""
    parser = argparse.ArgumentParser(
        prog="stackforge", description="Выбор папки проекта"
    )
    parser.parse_args()
    launch_folder = Path.cwd()

    print("Stack Forge\n")
    while True:
        try:
            choice = input(f"Папка проекта [Enter — {launch_folder}]: ").strip()
            folder = Path(choice).expanduser().resolve() if choice else launch_folder
            if folder.is_dir() and os.access(folder, os.R_OK | os.X_OK):
                print(f"\nВыбрана папка: {folder}\n")
                print("\nКурсы\n")
                for number, course in enumerate(Catalog.get_catalog(), start=1):
                    print(f"{number}. {course['title']}")
                return 0

        except (EOFError, KeyboardInterrupt):
            print("\nВыбор папки отменён")
            return 0
        except (OSError, RuntimeError, ValueError):
            pass

        print("Выберите существующую доступную папку\n")
