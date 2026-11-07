import os
import sys

from devlab.cli.api import ApiClient, ApiError
from devlab.cli.connection import choose_connection
from devlab.cli.control import LocalControl


class CliCommands:
    @staticmethod
    def dispatch(args: list[str]) -> int | None:
        """Обработать справку и сброс либо передать запуск интерактивной оболочке"""
        if not args:
            return None
        if args in (["--help"], ["-h"], ["reset", "--help"], ["reset", "-h"]):
            CliCommands.print_help()
            return 0
        if args == ["reset"]:
            return CliCommands.reset_practice()
        print(
            "Неизвестная команда или аргументы — смотри devlab --help", file=sys.stderr
        )
        return 2

    @staticmethod
    def print_help() -> None:
        """Показать команды CLI и способ выхода из bash без обращения к серверу"""
        print(
            "Запуск: devlab [reset] [--help]\n\n"
            "Команды:\n"
            "  devlab         Выбрать курс и папку, затем запустить bash\n"
            "  devlab reset   Выбрать курс и очистить историю его активной сессии в БД\n"
            "  -h, --help     Показать эту справку\n\n"
            "Выход из bash: exit или Ctrl+D"
        )

    @staticmethod
    def reset_practice() -> int:
        """Подключиться к выбранному курсу и очистить историю без запуска bash"""
        if os.environ.get("DEVLAB_OFFLINE") == "1":
            print("Для сброса истории требуется подключение к серверу", file=sys.stderr)
            return 1
        try:
            if path := os.environ.get("DEVLAB_CONTROL_SOCKET"):
                LocalControl.request_reset(path)
                print("\n  История практики очищена\n")
                return 0
            client = ApiClient(
                os.environ.get("DEVLAB_SERVER_URL", "http://127.0.0.1:8080")
            )
            print(
                "\n  Сброс истории в БД выбранного курса\n"
                "  Ранее запущенный CLI этого курса потребуется перезапустить\n"
            )
            connection = choose_connection(client)
            if connection is None:
                print("\n  Сброс отменён")
                return 0
            client.reset_practice(connection)
        except (EOFError, KeyboardInterrupt):
            print("\n  Сброс отменён")
            return 0
        except ApiError as error:
            print(f"\n  {error}", file=sys.stderr)
            return 1
        print("\n  История практики очищена\n  Хорошего дня")
        return 0
