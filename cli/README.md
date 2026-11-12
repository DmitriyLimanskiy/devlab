# Stack Forge CLI

CLI предлагает выбрать папку проекта, выводит выбранный путь и завершает работу.

Установка из каталога `cli/` с Python 3.11 или новее

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -e .
stackforge
```

Enter выбирает текущую папку. Можно указать абсолютный или относительный путь либо использовать `~`. Если папка недоступна, CLI предлагает повторить ввод. Ctrl+C и Ctrl+D отменяют выбор.

Из каталога `cli/` можно запустить CLI без установки.

```sh
python3 -m src
```
