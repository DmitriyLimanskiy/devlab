# Каталог команд Git и проверенность отображения DevLab

Проверено по исходникам тестов 6 ноября 2026 года. Установлен **git version 2.56.0**. Список команд получен из `git help -a`; синтаксис и названия флагов — из локальных HTML-руководств именно этой установки. Пользовательские aliases, произвольные `git-*` из PATH и расширения (например, Git LFS) в этот перечень не входят. Разделы help о форматах файлов и протоколах не являются командами и исключены.

«Все вариации» не образуют конечной шпаргалки: значения аргументов, комбинации флагов, конфигурация, hooks и исходные состояния репозитория меняют поведение. Ниже перечислены команды, документированный SYNOPSIS и названия параметров. Это не утверждение, что каждый флаг сочетается с каждым другим. Полное значение и ограничения каждого параметра доступны по ссылке на руководство. Автоматические формы `--no-*` и общие параметры могут описываться отдельно, а не отдельной строкой OPTIONS.

## Обозначения

- ✅ Проверен конкретный сценарий: настоящее выполнение Git и проверки соответствующего представления состояния/графа. Это отметка строки сценария, а не всей команды со всеми флагами и окружениями
- 🟨 У команды есть проверенные варианты, перечисленные в матрице ниже; остальные не подтверждены
- 🧪 Проверено чтение результата в state/API, но нет отдельной проверки всей отрисовки этого варианта
- 🟧 Проверена раскладка на моделях состояний; реальное выполнение всех вариантов команды и полный путь CLI → браузер не проверены
- ⚪ Отдельных проверок отображения нет
- ➖ У команды нет собственного элемента интерфейса; вывод остаётся в терминале. Это не отметка проверки отсутствия побочных изменений



## Матрица конкретных вариантов

| Команда / вариант | Статус | Что проверено и граница |
|---|---|---|
| `git init -b main` | ✅ | Пустой репозиторий, unborn HEAD, первый коммит; без bare и отдельного git-dir |
| `git add .`, `git add <file>` | ✅ | Статусы индекса и рабочей папки, оперативная доставка; без интерактивного отбора hunks |
| `git add -A`, `-u`, `-p`, `-i`, `-N`, `--renormalize` | ⚪ | Специальные варианты не проверены отдельно |
| `git commit -m <message>` | ✅ | Новый SHA, родители, перемещение ref и граф; обычный успешный коммит |
| `git commit --allow-empty -m <message>` | ✅ | Пустые коммиты участвуют в проверке структуры merge |
| `git commit --amend`, `-a`, `--fixup`, `--squash`, `-S`, `--no-verify` | ⚪ | Отдельной проверки вариантов нет |
| `git branch <name>` | ✅ | Появление ref без нового коммита |
| `git branch -d <name>` | ✅ | Удаление ref после merge, сохранность коммитов и наблюдавшейся линии |
| `git branch -D`, `-m`, `-M`, `-c`, `-C`, `--track`, `--set-upstream-to` | ⚪ | Отдельной проверки вариантов нет |
| `git switch <branch>` | ✅ | HEAD/ветка обновляются; переключение не добавляет событие истории графа |
| `git switch -c`, `-C`, `--detach`, `--orphan`, `--discard-changes`, `--merge` | ⚪ | Не приравнивать к проверенным похожим вариантам checkout |
| `git checkout <branch>`, `git checkout -b <branch>` | ✅ | Переключение и создание ветки на реальном Git |
| `git checkout --detach` | ✅ | Чтение detached HEAD и отдельная проверка его размещения в графе |
| `git checkout --orphan <branch>` | 🧪 | Unborn HEAD при сохранённых других ветках/тегах; нет отдельной проверки всей страницы |
| `git checkout -- <path>`, `--ours`, `--theirs`, `-p`, `-B`, `-f` | ⚪ | Специальные режимы не проверены отдельно |
| `git merge <branch>`: fast-forward | ✅ | Перемещение refs, отдельные отображения SHA на принимающей линии |
| `git merge --no-ff <branch> -m <message>` | ✅ | Настоящий merge-коммит и упорядоченные родители |
| `git merge <branch>`: конфликт | ✅ | Признак MERGE_HEAD и конфликты; завершённое слияние проверено на сохранённой истории пользователя |
| Вложенный `fix1 → dev → main`, переход dev через второго родителя merge | ✅ | Воспроизведена сохранённая реальная история, исправленный конец графа просмотрен в браузере |
| `git merge --ff-only`, `--squash`, `--no-commit`, `--abort`, `--continue`, `-s`, `-X`, octopus | ⚪ | Нельзя распространять отметку обычного merge на эти варианты |
| `git rebase` и перемещение dev на merge-коммит | 🟧 | Проверена раскладка соответствующего перехода refs; по снимкам нельзя подтвердить команду и флаги |
| `git rebase -i`, `--onto`, `--rebase-merges`, `--autosquash`, `--root`, `--continue`, `--abort`, `--skip` | ⚪ | Отдельных реальных сценариев с проверкой отображения нет |
| `git reset <revision>` | 🟧 | Модель перемещения ref назад и продолжения ветки; не доказательство всех режимов reset |
| `git reset --hard HEAD` | 🧪 | Использован на реальном Git в тесте сетевой модели, отдельной проверки отрисовки именно этого действия нет |
| `git reset --soft`, `--mixed`, `--merge`, `--keep`, `-p`, `-- <path>` | ⚪ | Отдельных проверок нет |
| `git mv <old> <new>` | 🧪 | Считывается original_path в сетевой модели; отдельный сценарий всей отрисовки не проверен |
| `git tag -a <name> -m <message>`; вложенный annotated tag | 🧪 | Реальное раскрытие целевого коммита; frontend отдельно проверяет привязку tag к SHA |
| `git tag <name> <tree>` | 🧪 | Тег на некоммит не включается в карту ref_commits; это не ветка графа |
| `git tag -d`, `-f`, `-s`, `-v`, lightweight tag на коммит | ⚪ | Отдельных проверок вариантов нет |
| `git clone --depth=1 <local-url> <folder>` | 🧪 | Признак shallow и ограниченная история; граф большого удалённого clone не проверен |
| `git status --short`, `git log --oneline`, неуспешный `git show missing-ref` | ✅ | Проверено, что команды не добавляют снимок при неизменившемся состоянии; их текстовый вывод остаётся в терминале |
| `git commit-tree -m ... [-p ...]`, `git mktree`, `git update-ref refs/heads/main <sha>` | 🧪 | Служебные команды формируют настоящую историю для проверки лимита 200 коммитов; не подтверждение всех режимов этих команд |
| `git restore`, `git rm`, `git clean` и их флаги | ⚪ | Нет отдельного набора проверок этих команд, хотя обычные статусы файлов читаются |
| `git stash`, `cherry-pick`, `revert`, `am`, `apply`, `bisect` и их флаги | ⚪ | Нет полного набора реальных сценариев; наличие признака операции в reader не равно проверке всей команды |
| `git fetch`, `pull`, `push`, `remote` и их флаги | ⚪ | Удалённые refs отдельно не подтверждены; reader ориентирован на локальные heads/tags и HEAD |
| `git worktree`, `submodule`, `sparse-checkout`, `git lfs` | ⚪ | За пределами подтверждённого покрытия MVP |

## Полный каталог команд этой установки

Статус в заголовке относится к покрытию команды в целом. ✅ ставится только конкретным строкам матрицы выше. «Названия параметров» извлечены из заголовков документации; раздел OPTIONS может отсылать к общим руководствам или описывать дополнительные формы в тексте. Для полного определения параметров открывайте руководство.

### Основные пользовательские команды

#### `add` — 🟨 Проверены отдельные варианты

```text
git add [--verbose | -v] [--dry-run | -n] [--force | -f] [--interactive | -i] [--patch | -p]
	[--edit | -e] [--[no-]all | -A | --[no-]ignore-removal | [--update | -u]] [--sparse]
	[--intent-to-add | -N] [--refresh] [--ignore-errors] [--ignore-missing] [--renormalize]
	[--resolved] [--chmod=(+|-)x] [--pathspec-from-file=<file> [--pathspec-file-nul]]
	[--] [<pathspec>…​]
```

Названия параметров из руководства:

- `-n`
- `--dry-run`
- `-v`
- `--verbose`
- `-f`
- `--force`
- `--sparse`
- `-i`
- `--interactive`
- `-p`
- `--patch`
- `-U<n>`
- `--unified=<n>`
- `--inter-hunk-context=<n>`
- `-e`
- `--edit`
- `-u`
- `--update`
- `-A`
- `--all`
- `--no-ignore-removal`
- `--no-all`
- `--ignore-removal`
- `-N`
- `--intent-to-add`
- `--refresh`
- `--ignore-errors`
- `--ignore-missing`
- `--no-warn-embedded-repo`
- `--renormalize`
- `--resolved`
- `--chmod=(+|-)x`
- `--pathspec-from-file=<file>`
- `--pathspec-file-nul`
- `--`

[Руководство add](https://git-scm.com/docs/git-add)

#### `am` — ⚪ Отдельно не проверено

```text
git am [--signoff] [--keep] [--[no-]keep-cr] [--[no-]utf8] [--[no-]verify]
	 [--[no-]3way] [--interactive] [--committer-date-is-author-date]
	 [--ignore-date] [--ignore-space-change | --ignore-whitespace]
	 [--whitespace=<action>] [-C<n>] [-p<n>] [--directory=<dir>]
	 [--exclude=<path>] [--include=<path>] [--reject] [-q | --quiet]
	 [--[no-]scissors] [-S[<key-id>]] [--patch-format=<format>]
	 [--quoted-cr=<action>]
	 [--empty=(stop|drop|keep)]
	 [(<mbox> | <Maildir>)…​]
git am (--continue | --skip | --abort | --quit | --retry | --show-current-patch[=(diff|raw)] | --allow-empty)
```

Названия параметров из руководства:

- `-s`
- `--signoff`
- `-k`
- `--keep`
- `--keep-non-patch`
- `--keep-cr`
- `--no-keep-cr`
- `-c`
- `--scissors`
- `--no-scissors`
- `--quoted-cr=<action>`
- `--empty=(drop|keep|stop)`
- `-m`
- `--message-id`
- `--no-message-id`
- `-q`
- `--quiet`
- `-u`
- `--utf8`
- `--no-utf8`
- `-3`
- `--3way`
- `--no-3way`
- `--rerere-autoupdate`
- `--no-rerere-autoupdate`
- `--ignore-space-change`
- `--ignore-whitespace`
- `--whitespace=<action>`
- `-C<n>`
- `-p<n>`
- `--directory=<dir>`
- `--exclude=<path>`
- `--include=<path>`
- `--reject`
- `--patch-format`
- `-i`
- `--interactive`
- `--verify`
- `-n`
- `--no-verify`
- `--committer-date-is-author-date`
- `--ignore-date`
- `--skip`
- `-S[<key-id>]`
- `--gpg-sign[=<key-id>]`
- `--no-gpg-sign`
- `--continue`
- `-r`
- `--resolved`
- `--resolvemsg=<msg>`
- `--abort`
- `--quit`
- `--retry`
- `--show-current-patch[=(diff|raw)]`
- `--allow-empty`

[Руководство am](https://git-scm.com/docs/git-am)

#### `archive` — ⚪ Отдельно не проверено

```text
git archive [--format=<fmt>] [--list] [--prefix=<prefix>/] [<extra>]
              [-o <file> | --output=<file>] [--worktree-attributes]
              [--remote=<repo> [--exec=<git-upload-archive>]] <tree-ish>
              [<path>…​]
```

Названия параметров из руководства:

- `--format=<fmt>`
- `-l`
- `--list`
- `-v`
- `--verbose`
- `--prefix=<prefix>/`
- `-o <file>`
- `--output=<file>`
- `--add-file=<file>`
- `--add-virtual-file=<path>:<content>`
- `--worktree-attributes`
- `--mtime=<time>`
- `--remote=<repo>`
- `--exec=<git-upload-archive>`
- `-<digit>`
- `-<number>`

[Руководство archive](https://git-scm.com/docs/git-archive)

#### `backfill` — ⚪ Отдельно не проверено

```text
git backfill [--min-batch-size=<n>] [--[no-]sparse] [--[no-]include-edges] [<revision-range>]
```

Названия параметров из руководства:

- `--min-batch-size=<n>`
- `--sparse`
- `--no-sparse`
- `--include-edges`
- `--no-include-edges`

[Руководство backfill](https://git-scm.com/docs/git-backfill)

#### `bisect` — ⚪ Отдельно не проверено

```text
git bisect start [--term-(bad|new)=<term-new> --term-(good|old)=<term-old>]
		 [--no-checkout] [--first-parent] [--reset-when-found[=<where>]] [<bad> [<good>…​]] [--] [<pathspec>…​]
git bisect (bad|new|<term-new>) [<rev>]
git bisect (good|old|<term-old>) [<rev>…​]
git bisect terms [--term-(good|old) | --term-(bad|new)]
git bisect skip [(<rev>|<range>)…​]
git bisect next
git bisect reset [<commit>]
git bisect (visualize|view)
git bisect replay <logfile>
git bisect log
git bisect run [--reset-when-found[=<where>]] <cmd> [<arg>…​]
git bisect help
```

Названия параметров из руководства:

- `--no-checkout`
- `--first-parent`
- `--reset-when-found[=<where>]`

[Руководство bisect](https://git-scm.com/docs/git-bisect)

#### `branch` — 🟨 Проверены отдельные варианты

```text
git branch [--color[=<when>] | --no-color] [--show-current]
	   [-v [--abbrev=<n> | --no-abbrev]]
	   [--column[=<options>] | --no-column] [--sort=<key>]
	   [--merged [<commit>]] [--no-merged [<commit>]]
	   [--contains [<commit>]] [--no-contains [<commit>]]
	   [(--forked <branch>)…​]
	   [--points-at <object>] [--format=<format>]
	   [(-r|--remotes) | (-a|--all)]
	   [--list] [<pattern>…​]
git branch [--track[=(direct|inherit)] | --no-track] [-f]
	   [--recurse-submodules] <branch-name> [<start-point>]
git branch (--set-upstream-to=<upstream>|-u <upstream>) [<branch-name>]
git branch --unset-upstream [<branch-name>]
git branch (-m|-M) [<old-branch>] <new-branch>
git branch (-c|-C) [<old-branch>] <new-branch>
git branch (-d|-D) [-r] <branch-name>…​
git branch --edit-description [<branch-name>]
git branch [--dry-run] (--delete-merged <pattern>)…​ [<branch-pattern>…​]
```

Названия параметров из руководства:

- `-d`
- `--delete`
- `-D`
- `--create-reflog`
- `-f`
- `--force`
- `-m`
- `--move`
- `-M`
- `-c`
- `--copy`
- `-C`
- `--color[=<when>]`
- `--no-color`
- `-i`
- `--ignore-case`
- `--omit-empty`
- `--column[=<options>]`
- `--no-column`
- `--sort=<key>`
- `-r`
- `--remotes`
- `-a`
- `--all`
- `-l`
- `--list`
- `--show-current`
- `--delete-merged <pattern>`
- `--dry-run`
- `-v`
- `-vv`
- `--verbose`
- `-q`
- `--quiet`
- `--abbrev=<n>`
- `--no-abbrev`
- `-t`
- `--track[=(direct|inherit)]`
- `--no-track`
- `--recurse-submodules`
- `--set-upstream`
- `-u <upstream>`
- `--set-upstream-to=<upstream>`
- `--unset-upstream`
- `--edit-description`
- `--contains [<commit>]`
- `--no-contains [<commit>]`
- `--merged [<commit>]`
- `--no-merged [<commit>]`
- `--forked <branch>`
- `--points-at <object>`
- `--format <format>`

[Руководство branch](https://git-scm.com/docs/git-branch)

#### `bundle` — ⚪ Отдельно не проверено

```text
git bundle create [-q | --quiet | --progress]
                    [--version=<version>] <file> <git-rev-list-args>
git bundle verify [-q | --quiet] <file>
git bundle list-heads <file> [<refname>…​]
git bundle unbundle [--progress] <file> [<refname>…​]
```

Названия параметров из руководства:

- `--progress`
- `--version=<version>`
- `-q`
- `--quiet`

[Руководство bundle](https://git-scm.com/docs/git-bundle)

#### `checkout` — 🟨 Проверены отдельные варианты

```text
git checkout [-q] [-f] [-m] [<branch>]
git checkout [-q] [-f] [-m] --detach [<branch>]
git checkout [-q] [-f] [-m] [--detach] <commit>
git checkout [-q] [-f] [-m] [[-b|-B|--orphan] <new-branch>] [<start-point>]
git checkout <tree-ish> [--] <pathspec>…​
git checkout <tree-ish> --pathspec-from-file=<file> [--pathspec-file-nul]
git checkout [-f|--ours|--theirs|-m|--conflict=<style>] [--] <pathspec>…​
git checkout [-f|--ours|--theirs|-m|--conflict=<style>] --pathspec-from-file=<file> [--pathspec-file-nul]
git checkout (-p|--patch) [<tree-ish>] [--] [<pathspec>…​]
```

Названия параметров из руководства:

- `-q`
- `--quiet`
- `--progress`
- `--no-progress`
- `-f`
- `--force`
- `--ours`
- `--theirs`
- `-b <new-branch>`
- `-B <new-branch>`
- `-t`
- `--track[=(direct|inherit)]`
- `--no-track`
- `--guess`
- `--no-guess`
- `-l`
- `-d`
- `--detach`
- `--orphan <new-branch>`
- `--ignore-skip-worktree-bits`
- `-m`
- `--merge`
- `--conflict=<style>`
- `-p`
- `--patch`
- `-U<n>`
- `--unified=<n>`
- `--inter-hunk-context=<n>`
- `--ignore-other-worktrees`
- `--overwrite-ignore`
- `--no-overwrite-ignore`
- `--recurse-submodules`
- `--no-recurse-submodules`
- `--overlay`
- `--no-overlay`
- `--pathspec-from-file=<file>`
- `--pathspec-file-nul`
- `--`

[Руководство checkout](https://git-scm.com/docs/git-checkout)

#### `cherry-pick` — ⚪ Отдельно не проверено

```text
git cherry-pick [--edit] [-n] [-m <parent-number>] [-s] [-x] [--ff]
                  [-S[<keyid>]] <commit>…​
git cherry-pick (--continue | --skip | --abort | --quit)
```

Названия параметров из руководства:

- `-e`
- `--edit`
- `--cleanup=<mode>`
- `-x`
- `-r`
- `-m <parent-number>`
- `--mainline <parent-number>`
- `-n`
- `--no-commit`
- `-s`
- `--signoff`
- `-S[<keyid>]`
- `--gpg-sign[=<keyid>]`
- `--no-gpg-sign`
- `--ff`
- `--allow-empty`
- `--allow-empty-message`
- `--empty=(drop|keep|stop)`
- `--keep-redundant-commits`
- `--strategy=<strategy>`
- `-X<option>`
- `--strategy-option=<option>`
- `--rerere-autoupdate`
- `--no-rerere-autoupdate`
- `--continue`
- `--skip`
- `--quit`
- `--abort`

[Руководство cherry-pick](https://git-scm.com/docs/git-cherry-pick)

#### `citool` — ⚪ Отдельно не проверено

```text
git citool
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство citool](https://git-scm.com/docs/git-citool)

#### `clean` — ⚪ Отдельно не проверено

```text
git clean [-d] [-f] [-i] [-n] [-q] [-e <pattern>] [-x | -X] [--] [<pathspec>…​]
```

Названия параметров из руководства:

- `-d`
- `-f`
- `--force`
- `-i`
- `--interactive`
- `-n`
- `--dry-run`
- `-q`
- `--quiet`
- `-e <pattern>`
- `--exclude=<pattern>`
- `-x`
- `-X`

[Руководство clean](https://git-scm.com/docs/git-clean)

#### `clone` — 🧪 Проверено чтение состояния

```text
git clone [--template=<template-directory>]
	  [-l] [-s] [--no-hardlinks] [-q] [-n] [--bare] [--mirror]
	  [-o <name>] [-b <name>] [-u <upload-pack>] [--reference <repository>]
	  [--dissociate] [--separate-git-dir <git-dir>]
	  [--depth <depth>] [--[no-]single-branch] [--[no-]tags]
	  [--recurse-submodules[=<pathspec>]] [--[no-]shallow-submodules]
	  [--[no-]remote-submodules] [--jobs <n>] [--sparse] [--[no-]reject-shallow]
	  [--filter=<filter-spec> [--also-filter-submodules]] [--] <repository>
	  [<directory>]
```

Названия параметров из руководства:

- `-l`
- `--local`
- `--no-hardlinks`
- `-s`
- `--shared`
- `--reference=<repository>`
- `--reference-if-able=<repository>`
- `--dissociate`
- `-q`
- `--quiet`
- `-v`
- `--verbose`
- `--progress`
- `--server-option=<option>`
- `-n`
- `--no-checkout`
- `--no-reject-shallow`
- `--reject-shallow`
- `--bare`
- `--sparse`
- `--filter=<filter-spec>`
- `--also-filter-submodules`
- `--mirror`
- `-o<name>`
- `--origin=<name>`
- `-b<name>`
- `--branch=<name>`
- `--revision=<rev>`
- `-u<upload-pack>`
- `--upload-pack=<upload-pack>`
- `--template=<template-directory>`
- `-c<key>=<value>`
- `--config=<key>=<value>`
- `--depth=<depth>`
- `--shallow-since=<date>`
- `--shallow-exclude=<ref>`
- `--single-branch`
- `--no-single-branch`
- `--tags`
- `--no-tags`
- `--recurse-submodules[=<pathspec>]`
- `--shallow-submodules`
- `--no-shallow-submodules`
- `--remote-submodules`
- `--no-remote-submodules`
- `--separate-git-dir=<git-dir>`
- `--ref-format=<ref-format>`
- `-j<n>`
- `--jobs=<n>`
- `--bundle-uri=<uri>`

[Руководство clone](https://git-scm.com/docs/git-clone)

#### `commit` — 🟨 Проверены отдельные варианты

```text
git commit [-a | --interactive | --patch] [-s] [-v] [-u[<mode>]] [--amend]
	   [--dry-run] [(-c | -C | --squash) <commit> | --fixup [(amend|reword):]<commit>]
	   [-F <file> | -m <msg>] [--reset-author] [--allow-empty]
	   [--allow-empty-message] [--no-verify] [-e] [--author=<author>]
	   [--date=<date>] [--cleanup=<mode>] [--[no-]status]
	   [-i | -o] [--pathspec-from-file=<file> [--pathspec-file-nul]]
	   [(--trailer <token>[(=|:)<value>])…​] [-S[<keyid>]]
	   [--] [<pathspec>…​]
```

Названия параметров из руководства:

- `-a`
- `--all`
- `-p`
- `--patch`
- `-U<n>`
- `--unified=<n>`
- `--inter-hunk-context=<n>`
- `-C <commit>`
- `--reuse-message=<commit>`
- `-c <commit>`
- `--reedit-message=<commit>`
- `--fixup=[(amend|reword):]<commit>`
- `--squash=<commit>`
- `--reset-author`
- `--short`
- `--branch`
- `--porcelain`
- `--long`
- `-z`
- `--null`
- `-F <file>`
- `--file=<file>`
- `--author=<author>`
- `--date=<date>`
- `-m <msg>`
- `--message=<msg>`
- `-t <file>`
- `--template=<file>`
- `-s`
- `--signoff`
- `--no-signoff`
- `--trailer <token>[(=|:)<value>]`
- `-n`
- `--verify`
- `--no-verify`
- `--allow-empty`
- `--allow-empty-message`
- `--cleanup=<mode>`
- `-e`
- `--edit`
- `--no-edit`
- `--amend`
- `--no-post-rewrite`
- `-i`
- `--include`
- `-o`
- `--only`
- `--pathspec-from-file=<file>`
- `--pathspec-file-nul`
- `-u[<mode>]`
- `--untracked-files[=<mode>]`
- `-v`
- `--verbose`
- `-q`
- `--quiet`
- `--dry-run`
- `--status`
- `--no-status`
- `-S[<key-id>]`
- `--gpg-sign[=<key-id>]`
- `--no-gpg-sign`
- `--`

[Руководство commit](https://git-scm.com/docs/git-commit)

#### `describe` — ➖ Нет собственного отображения

```text
git describe [--all] [--tags] [--contains] [--abbrev=<n>] [<commit-ish>…​]
git describe [--all] [--tags] [--contains] [--abbrev=<n>] --dirty[=<mark>]
git describe <blob>
```

Названия параметров из руководства:

- `--dirty[=<mark>]`
- `--broken[=<mark>]`
- `--all`
- `--tags`
- `--contains`
- `--abbrev=<n>`
- `--candidates=<n>`
- `--exact-match`
- `--debug`
- `--long`
- `--match <pattern>`
- `--exclude <pattern>`
- `--always`
- `--first-parent`

[Руководство describe](https://git-scm.com/docs/git-describe)

#### `diff` — ➖ Нет собственного отображения

```text
git diff [<options>] [<commit>] [--] [<path>…​]
git diff [<options>] --cached [--merge-base] [<commit>] [--] [<path>…​]
git diff [<options>] [--merge-base] <commit> [<commit>…​] <commit> [--] [<path>…​]
git diff [<options>] <commit>...<commit> [--] [<path>…​]
git diff [<options>] <blob> <blob>
git diff [<options>] --no-index [--] <path> <path> [<pathspec>…​]
```

Названия параметров из руководства:

- `-p`
- `-u`
- `--patch`
- `-s`
- `--no-patch`
- `-U<n>`
- `--unified=<n>`
- `--output=<file>`
- `--output-indicator-new=<char>`
- `--output-indicator-old=<char>`
- `--output-indicator-context=<char>`
- `--raw`
- `--patch-with-raw`
- `--indent-heuristic`
- `--no-indent-heuristic`
- `--minimal`
- `--patience`
- `--histogram`
- `--anchored=<text>`
- `--diff-algorithm=(patience|minimal|histogram|myers)`
- `--stat[=<width>[,<name-width>[,<count>]]]`
- `--compact-summary`
- `--numstat`
- `--shortstat`
- `-X [<param>,...]`
- `--dirstat[=<param>,...]`
- `--cumulative`
- `--dirstat-by-file[=<param>,...]`
- `--summary`
- `--patch-with-stat`
- `-z`
- `--name-only`
- `--name-status`
- `--submodule[=<format>]`
- `--color[=<when>]`
- `--no-color`
- `--color-moved[=<mode>]`
- `--no-color-moved`
- `--color-moved-ws=<mode>,...`
- `--no-color-moved-ws`
- `--word-diff[=<mode>]`
- `--word-diff-regex=<regex>`
- `--color-words[=<regex>]`
- `--no-renames`
- `--rename-empty`
- `--no-rename-empty`
- `--check`
- `--ws-error-highlight=<kind>`
- `--full-index`
- `--binary`
- `--abbrev[=<n>]`
- `-B[<n>][/<m>]`
- `--break-rewrites[=[<n>][/<m>]]`
- `-M[<n>]`
- `--find-renames[=<n>]`
- `-C[<n>]`
- `--find-copies[=<n>]`
- `--find-copies-harder`
- `-D`
- `--irreversible-delete`
- `-l<num>`
- `--diff-filter=[(A|C|D|M|R|T|U|X|B)...[*]]`
- `-S<string>`
- `-G<regex>`
- `--find-object=<object-id>`
- `--pickaxe-all`
- `--pickaxe-regex`
- `-O<orderfile>`
- `--skip-to=<file>`
- `--rotate-to=<file>`
- `-R`
- `--relative[=<path>]`
- `--no-relative`
- `-a`
- `--text`
- `--ignore-cr-at-eol`
- `--ignore-space-at-eol`
- `-b`
- `--ignore-space-change`
- `-w`
- `--ignore-all-space`
- `--ignore-blank-lines`
- `-I<regex>`
- `--ignore-matching-lines=<regex>`
- `--inter-hunk-context=<number>`
- `-W`
- `--function-context`
- `--exit-code`
- `--quiet`
- `--ext-diff`
- `--no-ext-diff`
- `--textconv`
- `--no-textconv`
- `--ignore-submodules[=(none|untracked|dirty|all)]`
- `--src-prefix=<prefix>`
- `--dst-prefix=<prefix>`
- `--no-prefix`
- `--default-prefix`
- `--line-prefix=<prefix>`
- `--ita-invisible-in-index`
- `--max-depth=<depth>`
- `-1`
- `--base`
- `-2`
- `--ours`
- `-3`
- `--theirs`
- `-0`

[Руководство diff](https://git-scm.com/docs/git-diff)

#### `fetch` — ⚪ Отдельно не проверено

```text
git fetch [<options>] [<repository> [<refspec>…​]]
git fetch [<options>] <group>
git fetch --multiple [<options>] [(<repository>|<group>)…​]
git fetch --all [<options>]
```

Названия параметров из руководства:

- `--all`
- `--no-all`
- `-a`
- `--append`
- `--atomic`
- `--depth=<depth>`
- `--deepen=<depth>`
- `--shallow-since=<date>`
- `--shallow-exclude=<ref>`
- `--unshallow`
- `--update-shallow`
- `--negotiation-restrict=(<commit>|<glob>)`
- `--negotiation-tip=(<commit>|<glob>)`
- `--negotiation-include=(<commit>|<glob>)`
- `--negotiate-only`
- `--dry-run`
- `--porcelain`
- `--filter=<filter-spec>`
- `--write-fetch-head`
- `--no-write-fetch-head`
- `-f`
- `--force`
- `-k`
- `--keep`
- `--multiple`
- `--auto-maintenance`
- `--no-auto-maintenance`
- `--auto-gc`
- `--no-auto-gc`
- `--write-commit-graph`
- `--no-write-commit-graph`
- `--prefetch`
- `-p`
- `--prune`
- `-P`
- `--prune-tags`
- `-n`
- `--no-tags`
- `--refetch`
- `--refmap=<refspec>`
- `-t`
- `--tags`
- `--recurse-submodules[=(yes|on-demand|no)]`
- `-j <n>`
- `--jobs=<n>`
- `--no-recurse-submodules`
- `--set-upstream`
- `--submodule-prefix=<path>`
- `--recurse-submodules-default=(yes|on-demand)`
- `-u`
- `--update-head-ok`
- `--upload-pack <upload-pack>`
- `-q`
- `--quiet`
- `-v`
- `--verbose`
- `--progress`
- `-o <option>`
- `--server-option=<option>`
- `--show-forced-updates`
- `--no-show-forced-updates`
- `-4`
- `--ipv4`
- `-6`
- `--ipv6`
- `--stdin`
- `-`

[Руководство fetch](https://git-scm.com/docs/git-fetch)

#### `format-patch` — ⚪ Отдельно не проверено

```text
git format-patch [-k] [(-o|--output-directory) <dir> | --stdout]
		   [--no-thread | --thread[=<style>]]
		   [(--attach|--inline)[=<boundary>] | --no-attach]
		   [-s | --signoff]
		   [--signature=<signature> | --no-signature]
		   [--signature-file=<file>]
		   [-n | --numbered | -N | --no-numbered]
		   [--start-number <n>] [--numbered-files]
		   [--in-reply-to=<message-id>] [--suffix=.<sfx>]
		   [--ignore-if-in-upstream] [--always]
		   [--cover-from-description=<mode>]
		   [--rfc[=<rfc>]] [--subject-prefix=<subject-prefix>]
		   [(--reroll-count|-v) <n>]
		   [--to=<email>] [--cc=<email>]
		   [--[no-]cover-letter] [--quiet]
		   [--commit-list-format=<format-spec>]
		   [--[no-]encode-email-headers]
		   [--no-notes | --notes[=<ref>]]
		   [--interdiff=<previous>]
		   [--range-diff=<previous> [--creation-factor=<percent>]]
		   [--filename-max-length=<n>]
		   [--progress]
		   [<common-diff-options>]
		   [ <since> | <revision-range> ]
```

Названия параметров из руководства:

- `-p`
- `--no-stat`
- `-U<n>`
- `--unified=<n>`
- `--output=<file>`
- `--output-indicator-new=<char>`
- `--output-indicator-old=<char>`
- `--output-indicator-context=<char>`
- `--indent-heuristic`
- `--no-indent-heuristic`
- `--minimal`
- `--patience`
- `--histogram`
- `--anchored=<text>`
- `--diff-algorithm=(patience|minimal|histogram|myers)`
- `--stat[=<width>[,<name-width>[,<count>]]]`
- `--compact-summary`
- `--numstat`
- `--shortstat`
- `-X [<param>,...]`
- `--dirstat[=<param>,...]`
- `--cumulative`
- `--dirstat-by-file[=<param>,...]`
- `--summary`
- `--no-renames`
- `--rename-empty`
- `--no-rename-empty`
- `--full-index`
- `--binary`
- `--abbrev[=<n>]`
- `-B[<n>][/<m>]`
- `--break-rewrites[=[<n>][/<m>]]`
- `-M[<n>]`
- `--find-renames[=<n>]`
- `-C[<n>]`
- `--find-copies[=<n>]`
- `--find-copies-harder`
- `-D`
- `--irreversible-delete`
- `-l<num>`
- `-O<orderfile>`
- `--skip-to=<file>`
- `--rotate-to=<file>`
- `--relative[=<path>]`
- `--no-relative`
- `-a`
- `--text`
- `--ignore-cr-at-eol`
- `--ignore-space-at-eol`
- `-b`
- `--ignore-space-change`
- `-w`
- `--ignore-all-space`
- `--ignore-blank-lines`
- `-I<regex>`
- `--ignore-matching-lines=<regex>`
- `--inter-hunk-context=<number>`
- `-W`
- `--function-context`
- `--ext-diff`
- `--no-ext-diff`
- `--textconv`
- `--no-textconv`
- `--ignore-submodules[=(none|untracked|dirty|all)]`
- `--src-prefix=<prefix>`
- `--dst-prefix=<prefix>`
- `--no-prefix`
- `--default-prefix`
- `--line-prefix=<prefix>`
- `--ita-invisible-in-index`
- `--max-depth=<depth>`
- `-<n>`
- `-o <dir>`
- `--output-directory=<dir>`
- `-n`
- `--numbered`
- `-N`
- `--no-numbered`
- `--start-number <n>`
- `--numbered-files`
- `-k`
- `--keep-subject`
- `-s`
- `--signoff`
- `--stdout`
- `--attach[=<boundary>]`
- `--no-attach`
- `--inline[=<boundary>]`
- `--thread[=<style>]`
- `--no-thread`
- `--in-reply-to=<message-id>`
- `--ignore-if-in-upstream`
- `--always`
- `--cover-from-description=<mode>`
- `--description-file=<file>`
- `--subject-prefix=<subject-prefix>`
- `--filename-max-length=<n>`
- `--rfc[=<rfc>]`
- `-v <n>`
- `--reroll-count=<n>`
- `--to=<email>`
- `--cc=<email>`
- `--from`
- `--from=<ident>`
- `--force-in-body-from`
- `--no-force-in-body-from`
- `--add-header=<header>`
- `--cover-letter`
- `--no-cover-letter`
- `--commit-list-format=<format-spec>`
- `--encode-email-headers`
- `--no-encode-email-headers`
- `--interdiff=<previous>`
- `--range-diff=<previous>`
- `--creation-factor=<percent>`
- `--notes[=<ref>]`
- `--no-notes`
- `--signature=<signature>`
- `--no-signature`
- `--signature-file=<file>`
- `--suffix=.<sfx>`
- `-q`
- `--quiet`
- `--no-binary`
- `--zero-commit`
- `--no-base`
- `--base[=<commit>]`
- `--root`
- `--progress`

[Руководство format-patch](https://git-scm.com/docs/git-format-patch)

#### `gc` — ⚪ Отдельно не проверено

```text
git gc [--aggressive] [--auto] [--[no-]detach] [--quiet] [--prune=<date> | --no-prune] [--force] [--keep-largest-pack]
```

Названия параметров из руководства:

- `--aggressive`
- `--auto`
- `--detach`
- `--no-detach`
- `--cruft`
- `--no-cruft`
- `--max-cruft-size=<n>`
- `--expire-to=<dir>`
- `--prune=<date>`
- `--no-prune`
- `--quiet`
- `--force`
- `--keep-largest-pack`

[Руководство gc](https://git-scm.com/docs/git-gc)

#### `gitk` — ⚪ Отдельно не проверено

```text
gitk [<options>] [<revision-range>] [--] [<path>…​]
```

Названия параметров из руководства:

- `--all`
- `--branches[=<pattern>]`
- `--tags[=<pattern>]`
- `--remotes[=<pattern>]`
- `--since=<date>`
- `--until=<date>`
- `--date-order`
- `--merge`
- `--left-right`
- `--full-history`
- `--simplify-merges`
- `--ancestry-path`
- `-L<start>,<end>:<file>`
- `-L:<funcname>:<file>`
- `--argscmd=<command>`
- `--select-commit=<ref>`

[Руководство gitk](https://git-scm.com/docs/gitk)

#### `grep` — ➖ Нет собственного отображения

```text
git grep [-a | --text] [-I] [--textconv] [-i | --ignore-case] [-w | --word-regexp]
	   [-v | --invert-match] [-h|-H] [--full-name]
	   [-E | --extended-regexp] [-G | --basic-regexp]
	   [-P | --perl-regexp]
	   [-F | --fixed-strings] [-n | --line-number] [--column]
	   [-l | --files-with-matches] [-L | --files-without-match]
	   [(-O | --open-files-in-pager) [<pager>]]
	   [-z | --null]
	   [ -o | --only-matching ] [-c | --count] [--all-match] [-q | --quiet]
	   [--max-depth <depth>] [--[no-]recursive]
	   [--color[=<when>] | --no-color]
	   [--break] [--heading] [-p | --show-function]
	   [-A <post-context>] [-B <pre-context>] [-C <context>]
	   [-W | --function-context]
	   [(-m | --max-count) <num>]
	   [--threads <num>]
	   [-f <file>] [-e] <pattern>
	   [--and|--or|--not|(|)|-e <pattern>…​]
	   [--recurse-submodules] [--parent-basename <basename>]
	   [ [--[no-]exclude-standard] [--cached | --untracked | --no-index] | <tree>…​]
	   [--] [<pathspec>…​]
```

Названия параметров из руководства:

- `--cached`
- `--untracked`
- `--no-index`
- `--no-exclude-standard`
- `--exclude-standard`
- `--recurse-submodules`
- `-a`
- `--text`
- `--textconv`
- `--no-textconv`
- `-i`
- `--ignore-case`
- `-I`
- `--max-depth <depth>`
- `-r`
- `--recursive`
- `--no-recursive`
- `-w`
- `--word-regexp`
- `-v`
- `--invert-match`
- `-h`
- `-H`
- `--full-name`
- `-E`
- `--extended-regexp`
- `-G`
- `--basic-regexp`
- `-P`
- `--perl-regexp`
- `-F`
- `--fixed-strings`
- `-n`
- `--line-number`
- `--column`
- `-l`
- `--files-with-matches`
- `--name-only`
- `-L`
- `--files-without-match`
- `-O[<pager>]`
- `--open-files-in-pager[=<pager>]`
- `-z`
- `--null`
- `-o`
- `--only-matching`
- `-c`
- `--count`
- `--color[=<when>]`
- `--no-color`
- `--break`
- `--heading`
- `-p`
- `--show-function`
- `-<num>`
- `-C <num>`
- `--context <num>`
- `-A <num>`
- `--after-context <num>`
- `-B <num>`
- `--before-context <num>`
- `-W`
- `--function-context`
- `-m <num>`
- `--max-count <num>`
- `--threads <num>`
- `-f <file>`
- `-e`
- `--and`
- `--or`
- `--not`
- `--all-match`
- `-q`
- `--quiet`
- `--`

[Руководство grep](https://git-scm.com/docs/git-grep)

#### `gui` — ⚪ Отдельно не проверено

```text
git gui [<command>] [<arguments>]
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство gui](https://git-scm.com/docs/git-gui)

#### `history` — ⚪ Отдельно не проверено

```text
git history drop <commit> [--dry-run] [--update-refs=(branches|head)] [--empty=(drop|keep|abort)]
git history fixup <commit> [--dry-run] [--update-refs=(branches|head)] [--reedit-message] [--empty=(drop|keep|abort)]
git history reword <commit> [--dry-run] [--update-refs=(branches|head)]
git history split <commit> [--dry-run] [--update-refs=(branches|head)] [--] [<pathspec>…​]
```

Названия параметров из руководства:

- `--dry-run`
- `--reedit-message`
- `--empty=(drop|keep|abort)`
- `--update-refs=(branches|head)`

[Руководство history](https://git-scm.com/docs/git-history)

#### `init` — 🟨 Проверены отдельные варианты

```text
git init [-q | --quiet] [--bare] [--template=<template-directory>]
	 [--separate-git-dir <git-dir>] [--object-format=<format>]
	 [--ref-format=<format>]
	 [-b <branch-name> | --initial-branch=<branch-name>]
	 [--shared[=<permissions>]] [<directory>]
```

Названия параметров из руководства:

- `-q`
- `--quiet`
- `--bare`
- `--object-format=<format>`
- `--ref-format=<format>`
- `--template=<template-directory>`
- `--separate-git-dir=<git-dir>`
- `-b <branch-name>`
- `--initial-branch=<branch-name>`
- `--shared[=(false|true|umask|group|all|world|everybody|<perm>)]`

[Руководство init](https://git-scm.com/docs/git-init)

#### `log` — 🟨 Проверены отдельные варианты

```text
git log [<options>] [<revision-range>] [[--] <path>…​]
```

Названия параметров из руководства:

- `--follow`
- `--no-decorate`
- `--decorate[=(short|full|auto|no)]`
- `--decorate-refs=<pattern>`
- `--decorate-refs-exclude=<pattern>`
- `--clear-decorations`
- `--source`
- `--mailmap`
- `--no-mailmap`
- `--use-mailmap`
- `--no-use-mailmap`
- `--full-diff`
- `--log-size`
- `-L<start>,<end>:<file>`
- `-L:<funcname>:<file>`
- `-<number>`
- `-n <number>`
- `--max-count=<number>`
- `--max-count-oldest=<number>`
- `--skip=<number>`
- `--since=<date>`
- `--after=<date>`
- `--since-as-filter=<date>`
- `--until=<date>`
- `--before=<date>`
- `--author=<pattern>`
- `--committer=<pattern>`
- `--grep-reflog=<pattern>`
- `--grep=<pattern>`
- `--all-match`
- `--invert-grep`
- `-i`
- `--regexp-ignore-case`
- `--basic-regexp`
- `-E`
- `--extended-regexp`
- `-F`
- `--fixed-strings`
- `-P`
- `--perl-regexp`
- `--remove-empty`
- `--merges`
- `--no-merges`
- `--min-parents=<number>`
- `--max-parents=<number>`
- `--no-min-parents`
- `--no-max-parents`
- `--first-parent`
- `--exclude-first-parent-only`
- `--maximal-only`
- `--not`
- `--all`
- `--branches[=<pattern>]`
- `--tags[=<pattern>]`
- `--remotes[=<pattern>]`
- `--glob=<glob-pattern>`
- `--exclude=<glob-pattern>`
- `--exclude-hidden=(fetch|receive|uploadpack)`
- `--reflog`
- `--alternate-refs`
- `--single-worktree`
- `--ignore-missing`
- `--bisect`
- `--stdin`
- `--cherry-mark`
- `--cherry-pick`
- `--left-only`
- `--right-only`
- `--cherry`
- `-g`
- `--walk-reflogs`
- `--merge`
- `--boundary`
- `--simplify-by-decoration`
- `--show-pulls`
- `--full-history`
- `--dense`
- `--sparse`
- `--simplify-merges`
- `--ancestry-path[=<commit>]`
- `--full-history without parent rewriting`
- `--full-history with parent rewriting`
- `--date-order`
- `--author-date-order`
- `--topo-order`
- `--reverse`
- `--no-walk[=(sorted|unsorted)]`
- `--do-walk`
- `--pretty[=<format>]`
- `--format=<format>`
- `--abbrev-commit`
- `--no-abbrev-commit`
- `--oneline`
- `--encoding=<encoding>`
- `--expand-tabs=<n>`
- `--expand-tabs`
- `--no-expand-tabs`
- `--notes[=<ref>]`
- `--no-notes`
- `--show-notes-by-default`
- `--show-notes[=<ref>]`
- `--standard-notes`
- `--no-standard-notes`
- `--show-signature`
- `--relative-date`
- `--date=<format>`
- `--parents`
- `--children`
- `--left-right`
- `--graph`
- `--show-linear-break[=<barrier>]`
- `--graph-lane-limit=<n>`
- `--no-graph-indent`
- `--graph-indent`
- `-p`
- `-u`
- `--patch`
- `-s`
- `--no-patch`
- `-m`
- `-c`
- `--cc`
- `--dd`
- `--remerge-diff`
- `--no-diff-merges`
- `--diff-merges=<format>`
- `--combined-all-paths`
- `-U<n>`
- `--unified=<n>`
- `--output=<file>`
- `--output-indicator-new=<char>`
- `--output-indicator-old=<char>`
- `--output-indicator-context=<char>`
- `--raw`
- `--patch-with-raw`
- `-t`
- `--indent-heuristic`
- `--no-indent-heuristic`
- `--minimal`
- `--patience`
- `--histogram`
- `--anchored=<text>`
- `--diff-algorithm=(patience|minimal|histogram|myers)`
- `--stat[=<width>[,<name-width>[,<count>]]]`
- `--compact-summary`
- `--numstat`
- `--shortstat`
- `-X [<param>,...]`
- `--dirstat[=<param>,...]`
- `--cumulative`
- `--dirstat-by-file[=<param>,...]`
- `--summary`
- `--patch-with-stat`
- `-z`
- `--name-only`
- `--name-status`
- `--submodule[=<format>]`
- `--color[=<when>]`
- `--no-color`
- `--color-moved[=<mode>]`
- `--no-color-moved`
- `--color-moved-ws=<mode>,...`
- `--no-color-moved-ws`
- `--word-diff[=<mode>]`
- `--word-diff-regex=<regex>`
- `--color-words[=<regex>]`
- `--no-renames`
- `--rename-empty`
- `--no-rename-empty`
- `--check`
- `--ws-error-highlight=<kind>`
- `--full-index`
- `--binary`
- `--abbrev[=<n>]`
- `-B[<n>][/<m>]`
- `--break-rewrites[=[<n>][/<m>]]`
- `-M[<n>]`
- `--find-renames[=<n>]`
- `-C[<n>]`
- `--find-copies[=<n>]`
- `--find-copies-harder`
- `-D`
- `--irreversible-delete`
- `-l<num>`
- `--diff-filter=[(A|C|D|M|R|T|U|X|B)...[*]]`
- `-S<string>`
- `-G<regex>`
- `--find-object=<object-id>`
- `--pickaxe-all`
- `--pickaxe-regex`
- `-O<orderfile>`
- `--skip-to=<file>`
- `--rotate-to=<file>`
- `-R`
- `--relative[=<path>]`
- `--no-relative`
- `-a`
- `--text`
- `--ignore-cr-at-eol`
- `--ignore-space-at-eol`
- `-b`
- `--ignore-space-change`
- `-w`
- `--ignore-all-space`
- `--ignore-blank-lines`
- `-I<regex>`
- `--ignore-matching-lines=<regex>`
- `--inter-hunk-context=<number>`
- `-W`
- `--function-context`
- `--ext-diff`
- `--no-ext-diff`
- `--textconv`
- `--no-textconv`
- `--ignore-submodules[=(none|untracked|dirty|all)]`
- `--src-prefix=<prefix>`
- `--dst-prefix=<prefix>`
- `--no-prefix`
- `--default-prefix`
- `--line-prefix=<prefix>`
- `--ita-invisible-in-index`
- `--max-depth=<depth>`

[Руководство log](https://git-scm.com/docs/git-log)

#### `maintenance` — ⚪ Отдельно не проверено

```text
git maintenance run [<options>]
git maintenance start [--scheduler=<scheduler>]
git maintenance (stop|register|unregister) [<options>]
git maintenance is-needed [<options>]
```

Названия параметров из руководства:

- `--auto`
- `--schedule`
- `--quiet`
- `--task=<task>`
- `--scheduler=auto|crontab|systemd-timer|launchctl|schtasks`

[Руководство maintenance](https://git-scm.com/docs/git-maintenance)

#### `merge` — 🟨 Проверены отдельные варианты

```text
git merge [-n] [--stat] [--compact-summary] [--no-commit] [--squash] [--[no-]edit]
	[--no-verify] [-s <strategy>] [-X <strategy-option>] [-S[<keyid>]]
	[--[no-]allow-unrelated-histories]
	[--[no-]rerere-autoupdate] [-m <msg>] [-F <file>]
	[--into-name <branch>] [<commit>…​]
git merge (--continue | --abort | --quit)
```

Названия параметров из руководства:

- `--commit`
- `--no-commit`
- `--edit`
- `-e`
- `--no-edit`
- `--cleanup=<mode>`
- `--ff`
- `--no-ff`
- `--ff-only`
- `-S[<key-id>]`
- `--gpg-sign[=<key-id>]`
- `--no-gpg-sign`
- `--log[=<n>]`
- `--no-log`
- `--signoff`
- `--no-signoff`
- `--stat`
- `-n`
- `--no-stat`
- `--compact-summary`
- `--squash`
- `--no-squash`
- `--verify`
- `--no-verify`
- `-s <strategy>`
- `--strategy=<strategy>`
- `-X <option>`
- `--strategy-option=<option>`
- `--verify-signatures`
- `--no-verify-signatures`
- `--summary`
- `--no-summary`
- `-q`
- `--quiet`
- `-v`
- `--verbose`
- `--progress`
- `--no-progress`
- `--autostash`
- `--no-autostash`
- `--allow-unrelated-histories`
- `-m <msg>`
- `--into-name <branch>`
- `-F <file>`
- `--file=<file>`
- `--rerere-autoupdate`
- `--no-rerere-autoupdate`
- `--overwrite-ignore`
- `--no-overwrite-ignore`
- `--abort`
- `--quit`
- `--continue`

[Руководство merge](https://git-scm.com/docs/git-merge)

#### `mv` — 🧪 Проверено чтение состояния

```text
git mv [-v] [-f] [-n] [-k] <source> <destination>
git mv [-v] [-f] [-n] [-k] <source>…​ <destination-directory>
```

Названия параметров из руководства:

- `-f`
- `--force`
- `-k`
- `-n`
- `--dry-run`
- `-v`
- `--verbose`

[Руководство mv](https://git-scm.com/docs/git-mv)

#### `notes` — ⚪ Отдельно не проверено

```text
git notes [list [<object>]]
git notes add [-f] [--allow-empty] [--[no-]separator | --separator=<paragraph-break>] [--[no-]stripspace] [-F <file> | -m <msg> | (-c | -C) <object>] [-e] [<object>]
git notes copy [-f] ( --stdin | <from-object> [<to-object>] )
git notes append [--allow-empty] [--[no-]separator | --separator=<paragraph-break>] [--[no-]stripspace] [-F <file> | -m <msg> | (-c | -C) <object>] [-e] [<object>]
git notes edit [--allow-empty] [<object>] [--[no-]stripspace]
git notes show [<object>]
git notes merge [-v | -q] [-s <strategy> ] <notes-ref>
git notes merge --commit [-v | -q]
git notes merge --abort [-v | -q]
git notes remove [--ignore-missing] [--stdin] [<object>…​]
git notes prune [-n] [-v]
git notes get-ref
```

Названия параметров из руководства:

- `-f`
- `--force`
- `-m <msg>`
- `--message=<msg>`
- `-F <file>`
- `--file=<file>`
- `-C <object>`
- `--reuse-message=<object>`
- `-c <object>`
- `--reedit-message=<object>`
- `--allow-empty`
- `--separator=<paragraph-break>`
- `--separator`
- `--no-separator`
- `--stripspace`
- `--no-stripspace`
- `--ref=<ref>`
- `--ignore-missing`
- `--stdin`
- `-n`
- `--dry-run`
- `-s <strategy>`
- `--strategy=<strategy>`
- `--commit`
- `--abort`
- `-q`
- `--quiet`
- `-v`
- `--verbose`

[Руководство notes](https://git-scm.com/docs/git-notes)

#### `pull` — ⚪ Отдельно не проверено

```text
git pull [<options>] [<repository> [<refspec>…​]]
```

Названия параметров из руководства:

- `-q`
- `--quiet`
- `-v`
- `--verbose`
- `--recurse-submodules[=(yes|on-demand|no)]`
- `--no-recurse-submodules`
- `--commit`
- `--no-commit`
- `--edit`
- `-e`
- `--no-edit`
- `--cleanup=<mode>`
- `--ff-only`
- `--ff`
- `--no-ff`
- `-S[<key-id>]`
- `--gpg-sign[=<key-id>]`
- `--no-gpg-sign`
- `--log[=<n>]`
- `--no-log`
- `--signoff`
- `--no-signoff`
- `--stat`
- `-n`
- `--no-stat`
- `--compact-summary`
- `--squash`
- `--no-squash`
- `--verify`
- `--no-verify`
- `-s <strategy>`
- `--strategy=<strategy>`
- `-X <option>`
- `--strategy-option=<option>`
- `--verify-signatures`
- `--no-verify-signatures`
- `--summary`
- `--no-summary`
- `--autostash`
- `--no-autostash`
- `--allow-unrelated-histories`
- `-r`
- `--rebase[=(true|merges|false|interactive)]`
- `--no-rebase`
- `--all`
- `--no-all`
- `-a`
- `--append`
- `--atomic`
- `--depth=<depth>`
- `--deepen=<depth>`
- `--shallow-since=<date>`
- `--shallow-exclude=<ref>`
- `--unshallow`
- `--update-shallow`
- `--negotiation-restrict=(<commit>|<glob>)`
- `--negotiation-tip=(<commit>|<glob>)`
- `--negotiation-include=(<commit>|<glob>)`
- `--negotiate-only`
- `--dry-run`
- `--porcelain`
- `--filter=<filter-spec>`
- `-f`
- `--force`
- `-k`
- `--keep`
- `--prefetch`
- `-p`
- `--prune`
- `--no-tags`
- `--refmap=<refspec>`
- `-t`
- `--tags`
- `-j <n>`
- `--jobs=<n>`
- `--set-upstream`
- `--upload-pack <upload-pack>`
- `--progress`
- `-o <option>`
- `--server-option=<option>`
- `--show-forced-updates`
- `--no-show-forced-updates`
- `-4`
- `--ipv4`
- `-6`
- `--ipv6`

[Руководство pull](https://git-scm.com/docs/git-pull)

#### `push` — ⚪ Отдельно не проверено

```text
git push [--all | --branches | --mirror | --tags] [--follow-tags] [--atomic] [-n | --dry-run] [--receive-pack=<git-receive-pack>]
	 [--repo=<repository>] [-f | --force] [-d | --delete] [--prune] [-q | --quiet] [-v | --verbose]
	 [-u | --set-upstream] [-o <string> | --push-option=<string>]
	 [--[no-]signed | --signed=(true|false|if-asked)]
	 [--force-with-lease[=<refname>[:<expect>]] [--force-if-includes]]
	 [--no-verify] [<repository> [<refspec>…​]]
```

Названия параметров из руководства:

- `--all`
- `--branches`
- `--prune`
- `--mirror`
- `-n`
- `--dry-run`
- `--porcelain`
- `-d`
- `--delete`
- `--tags`
- `--follow-tags`
- `--signed`
- `--no-signed`
- `--signed=(true|false|if-asked)`
- `--atomic`
- `--no-atomic`
- `-o <option>`
- `--push-option=<option>`
- `--receive-pack=<git-receive-pack>`
- `--exec=<git-receive-pack>`
- `--force-with-lease`
- `--no-force-with-lease`
- `--force-with-lease=<refname>`
- `--force-with-lease=<refname>:<expect>`
- `-f`
- `--force`
- `--force-if-includes`
- `--no-force-if-includes`
- `--repo=<repository>`
- `-u`
- `--set-upstream`
- `--thin`
- `--no-thin`
- `-q`
- `--quiet`
- `-v`
- `--verbose`
- `--progress`
- `--no-recurse-submodules`
- `--recurse-submodules=(check|on-demand|only|no)`
- `--verify`
- `--no-verify`
- `-4`
- `--ipv4`
- `-6`
- `--ipv6`
- `-`

[Руководство push](https://git-scm.com/docs/git-push)

#### `range-diff` — ➖ Нет собственного отображения

```text
git range-diff [--color=[<when>]] [--no-color] [<diff-options>]
	[--no-dual-color] [--creation-factor=<factor>]
	[--left-only | --right-only] [--diff-merges=<format>]
	[--remerge-diff] [--no-notes | --notes[=<ref>]]
	( <range1> <range2> | <rev1>...<rev2> | <base> <rev1> <rev2> )
	[[--] <path>…​]
```

Названия параметров из руководства:

- `--no-dual-color`
- `--creation-factor=<percent>`
- `--left-only`
- `--right-only`
- `--diff-merges=<format>`
- `--remerge-diff`
- `--notes[=<ref>]`
- `--no-notes`

[Руководство range-diff](https://git-scm.com/docs/git-range-diff)

#### `rebase` — 🟧 Проверена модель раскладки

```text
git rebase [-i | --interactive] [<options>] [--exec <cmd>]
        [--onto <newbase> | --keep-base] [<upstream> [<branch>]]
git rebase [-i | --interactive] [<options>] [--exec <cmd>] [--onto <newbase>]
        --root [<branch>]
git rebase (--continue|--skip|--abort|--quit|--edit-todo|--show-current-patch)
```

Названия параметров из руководства:

- `--continue`
- `--skip`
- `--abort`
- `--quit`
- `--edit-todo`
- `--show-current-patch`
- `--onto <newbase>`
- `--keep-base`
- `--apply`
- `--empty=(drop|keep|stop)`
- `--no-keep-empty`
- `--keep-empty`
- `--reapply-cherry-picks`
- `--no-reapply-cherry-picks`
- `--allow-empty-message`
- `-m`
- `--merge`
- `-s <strategy>`
- `--strategy=<strategy>`
- `-X <strategy-option>`
- `--strategy-option=<strategy-option>`
- `--rerere-autoupdate`
- `--no-rerere-autoupdate`
- `-S[<keyid>]`
- `--gpg-sign[=<keyid>]`
- `--no-gpg-sign`
- `-q`
- `--quiet`
- `-v`
- `--verbose`
- `--stat`
- `-n`
- `--no-stat`
- `--no-verify`
- `--verify`
- `-C<n>`
- `--no-ff`
- `--force-rebase`
- `-f`
- `--fork-point`
- `--no-fork-point`
- `--ignore-whitespace`
- `--whitespace=<option>`
- `--committer-date-is-author-date`
- `--ignore-date`
- `--reset-author-date`
- `--signoff`
- `--trailer=<trailer>`
- `-i`
- `--interactive`
- `-r`
- `--rebase-merges[=(rebase-cousins|no-rebase-cousins)]`
- `--no-rebase-merges`
- `-x <cmd>`
- `--exec <cmd>`
- `--root`
- `--autosquash`
- `--no-autosquash`
- `--autostash`
- `--no-autostash`
- `--reschedule-failed-exec`
- `--no-reschedule-failed-exec`
- `--update-refs`
- `--no-update-refs`

[Руководство rebase](https://git-scm.com/docs/git-rebase)

#### `reset` — 🟧 Проверена модель раскладки

```text
git reset [--soft | --mixed [-N] | --hard | --merge | --keep] [-q] [<commit>]
git reset [-q] [<tree-ish>] [--] <pathspec>…​
git reset [-q] [--pathspec-from-file=<file> [--pathspec-file-nul]] [<tree-ish>]
git reset (--patch | -p) [<tree-ish>] [--] [<pathspec>…​]
```

Названия параметров из руководства:

- `--mixed`
- `--soft`
- `--hard`
- `--merge`
- `--keep`
- `--recurse-submodules`
- `--no-recurse-submodules`
- `-q`
- `--quiet`
- `--refresh`
- `--no-refresh`
- `--pathspec-from-file=<file>`
- `--pathspec-file-nul`
- `-U<n>`
- `--unified=<n>`
- `--inter-hunk-context=<n>`
- `--`

[Руководство reset](https://git-scm.com/docs/git-reset)

#### `restore` — ⚪ Отдельно не проверено

```text
git restore [<options>] [--source=<tree>] [--staged] [--worktree] [--] <pathspec>…​
git restore [<options>] [--source=<tree>] [--staged] [--worktree] --pathspec-from-file=<file> [--pathspec-file-nul]
git restore (-p|--patch) [<options>] [--source=<tree>] [--staged] [--worktree] [--] [<pathspec>…​]
```

Названия параметров из руководства:

- `-s <tree>`
- `--source=<tree>`
- `-p`
- `--patch`
- `-U<n>`
- `--unified=<n>`
- `--inter-hunk-context=<n>`
- `-W`
- `--worktree`
- `-S`
- `--staged`
- `-q`
- `--quiet`
- `--progress`
- `--no-progress`
- `--ours`
- `--theirs`
- `-m`
- `--merge`
- `--conflict=<style>`
- `--ignore-unmerged`
- `--ignore-skip-worktree-bits`
- `--recurse-submodules`
- `--no-recurse-submodules`
- `--overlay`
- `--no-overlay`
- `--pathspec-from-file=<file>`
- `--pathspec-file-nul`
- `--`

[Руководство restore](https://git-scm.com/docs/git-restore)

#### `revert` — ⚪ Отдельно не проверено

```text
git revert [--[no-]edit] [-n] [-m <parent-number>] [-s] [-S[<keyid>]] <commit>…​
git revert (--continue | --skip | --abort | --quit)
```

Названия параметров из руководства:

- `-e`
- `--edit`
- `-m parent-number`
- `--mainline parent-number`
- `--no-edit`
- `--cleanup=<mode>`
- `-n`
- `--no-commit`
- `-S[<keyid>]`
- `--gpg-sign[=<keyid>]`
- `--no-gpg-sign`
- `-s`
- `--signoff`
- `--strategy=<strategy>`
- `-X<option>`
- `--strategy-option=<option>`
- `--rerere-autoupdate`
- `--no-rerere-autoupdate`
- `--reference`
- `--continue`
- `--skip`
- `--quit`
- `--abort`

[Руководство revert](https://git-scm.com/docs/git-revert)

#### `rm` — ⚪ Отдельно не проверено

```text
git rm [-f | --force] [-n] [-r] [--cached] [--ignore-unmatch]
       [--quiet] [--pathspec-from-file=<file> [--pathspec-file-nul]]
       [--] [<pathspec>…​]
```

Названия параметров из руководства:

- `-f`
- `--force`
- `-n`
- `--dry-run`
- `-r`
- `--`
- `--cached`
- `--ignore-unmatch`
- `--sparse`
- `-q`
- `--quiet`
- `--pathspec-from-file=<file>`
- `--pathspec-file-nul`

[Руководство rm](https://git-scm.com/docs/git-rm)

#### `scalar` — ⚪ Отдельно не проверено

```text
scalar clone [--single-branch] [--branch <main-branch>] [--full-clone]
        [--[no-]src] [--[no-]tags] [--[no-]maintenance] <url> [<enlistment>]
scalar list
scalar register [--[no-]maintenance] [<enlistment>]
scalar unregister [<enlistment>]
scalar run ( all | config | commit-graph | fetch | loose-objects | pack-files ) [<enlistment>]
scalar reconfigure [--maintenance=(enable|disable|keep)] [ --all | <enlistment> ]
scalar diagnose [<enlistment>]
scalar delete <enlistment>
```

Названия параметров из руководства:

- `-C <directory>`
- `-c <key>=<value>`
- `-b <name>`
- `--branch <name>`
- `--single-branch`
- `--no-single-branch`
- `--src`
- `--no-src`
- `--tags`
- `--no-tags`
- `--full-clone`
- `--no-full-clone`
- `--maintenance`
- `--no-maintenance`
- `--all`
- `--maintenance=(enable|disable|keep)`

[Руководство scalar](https://git-scm.com/docs/scalar)

#### `shortlog` — ➖ Нет собственного отображения

```text
git shortlog [<options>] [<revision-range>] [[--] <path>…​]
git log --pretty=short | git shortlog [<options>]
```

Названия параметров из руководства:

- `-n`
- `--numbered`
- `-s`
- `--summary`
- `-e`
- `--email`
- `--format[=<format>]`
- `--date=<format>`
- `--group=<type>`
- `-c`
- `--committer`
- `-w[<width>[,<indent1>[,<indent2>]]]`
- `-<number>`
- `-n <number>`
- `--max-count=<number>`
- `--max-count-oldest=<number>`
- `--skip=<number>`
- `--since=<date>`
- `--after=<date>`
- `--since-as-filter=<date>`
- `--until=<date>`
- `--before=<date>`
- `--author=<pattern>`
- `--committer=<pattern>`
- `--grep-reflog=<pattern>`
- `--grep=<pattern>`
- `--all-match`
- `--invert-grep`
- `-i`
- `--regexp-ignore-case`
- `--basic-regexp`
- `-E`
- `--extended-regexp`
- `-F`
- `--fixed-strings`
- `-P`
- `--perl-regexp`
- `--remove-empty`
- `--merges`
- `--no-merges`
- `--min-parents=<number>`
- `--max-parents=<number>`
- `--no-min-parents`
- `--no-max-parents`
- `--first-parent`
- `--exclude-first-parent-only`
- `--maximal-only`
- `--not`
- `--all`
- `--branches[=<pattern>]`
- `--tags[=<pattern>]`
- `--remotes[=<pattern>]`
- `--glob=<glob-pattern>`
- `--exclude=<glob-pattern>`
- `--exclude-hidden=(fetch|receive|uploadpack)`
- `--reflog`
- `--alternate-refs`
- `--single-worktree`
- `--ignore-missing`
- `--bisect`
- `--stdin`
- `--cherry-mark`
- `--cherry-pick`
- `--left-only`
- `--right-only`
- `--cherry`
- `-g`
- `--walk-reflogs`
- `--merge`
- `--boundary`
- `--simplify-by-decoration`
- `--show-pulls`
- `--full-history`
- `--dense`
- `--sparse`
- `--simplify-merges`
- `--ancestry-path[=<commit>]`
- `--full-history without parent rewriting`
- `--full-history with parent rewriting`

[Руководство shortlog](https://git-scm.com/docs/git-shortlog)

#### `show` — ➖ Нет собственного отображения

```text
git show [<options>] [<object>…​]
```

Названия параметров из руководства:

- `--pretty[=<format>]`
- `--format=<format>`
- `--abbrev-commit`
- `--no-abbrev-commit`
- `--oneline`
- `--encoding=<encoding>`
- `--expand-tabs=<n>`
- `--expand-tabs`
- `--no-expand-tabs`
- `--notes[=<ref>]`
- `--no-notes`
- `--show-notes-by-default`
- `--show-notes[=<ref>]`
- `--standard-notes`
- `--no-standard-notes`
- `--show-signature`
- `-p`
- `-u`
- `--patch`
- `-s`
- `--no-patch`
- `-m`
- `-c`
- `--cc`
- `--dd`
- `--remerge-diff`
- `--no-diff-merges`
- `--diff-merges=<format>`
- `--combined-all-paths`
- `-U<n>`
- `--unified=<n>`
- `--output=<file>`
- `--output-indicator-new=<char>`
- `--output-indicator-old=<char>`
- `--output-indicator-context=<char>`
- `--raw`
- `--patch-with-raw`
- `-t`
- `--indent-heuristic`
- `--no-indent-heuristic`
- `--minimal`
- `--patience`
- `--histogram`
- `--anchored=<text>`
- `--diff-algorithm=(patience|minimal|histogram|myers)`
- `--stat[=<width>[,<name-width>[,<count>]]]`
- `--compact-summary`
- `--numstat`
- `--shortstat`
- `-X [<param>,...]`
- `--dirstat[=<param>,...]`
- `--cumulative`
- `--dirstat-by-file[=<param>,...]`
- `--summary`
- `--patch-with-stat`
- `-z`
- `--name-only`
- `--name-status`
- `--submodule[=<format>]`
- `--color[=<when>]`
- `--no-color`
- `--color-moved[=<mode>]`
- `--no-color-moved`
- `--color-moved-ws=<mode>,...`
- `--no-color-moved-ws`
- `--word-diff[=<mode>]`
- `--word-diff-regex=<regex>`
- `--color-words[=<regex>]`
- `--no-renames`
- `--rename-empty`
- `--no-rename-empty`
- `--check`
- `--ws-error-highlight=<kind>`
- `--full-index`
- `--binary`
- `--abbrev[=<n>]`
- `-B[<n>][/<m>]`
- `--break-rewrites[=[<n>][/<m>]]`
- `-M[<n>]`
- `--find-renames[=<n>]`
- `-C[<n>]`
- `--find-copies[=<n>]`
- `--find-copies-harder`
- `-D`
- `--irreversible-delete`
- `-l<num>`
- `--diff-filter=[(A|C|D|M|R|T|U|X|B)...[*]]`
- `-S<string>`
- `-G<regex>`
- `--find-object=<object-id>`
- `--pickaxe-all`
- `--pickaxe-regex`
- `-O<orderfile>`
- `--skip-to=<file>`
- `--rotate-to=<file>`
- `-R`
- `--relative[=<path>]`
- `--no-relative`
- `-a`
- `--text`
- `--ignore-cr-at-eol`
- `--ignore-space-at-eol`
- `-b`
- `--ignore-space-change`
- `-w`
- `--ignore-all-space`
- `--ignore-blank-lines`
- `-I<regex>`
- `--ignore-matching-lines=<regex>`
- `--inter-hunk-context=<number>`
- `-W`
- `--function-context`
- `--ext-diff`
- `--no-ext-diff`
- `--textconv`
- `--no-textconv`
- `--ignore-submodules[=(none|untracked|dirty|all)]`
- `--src-prefix=<prefix>`
- `--dst-prefix=<prefix>`
- `--no-prefix`
- `--default-prefix`
- `--line-prefix=<prefix>`
- `--ita-invisible-in-index`
- `--max-depth=<depth>`

[Руководство show](https://git-scm.com/docs/git-show)

#### `sparse-checkout` — ⚪ Отдельно не проверено

```text
git sparse-checkout (init | list | set | add | reapply | disable | check-rules | clean) [<options>]
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство sparse-checkout](https://git-scm.com/docs/git-sparse-checkout)

#### `stash` — ⚪ Отдельно не проверено

```text
git stash list [<log-options>]
git stash show [-u | --include-untracked | --only-untracked] [<diff-options>] [<stash>]
git stash drop [-q | --quiet] [<stash>]
git stash pop [--index] [-q | --quiet] [<stash>]
git stash apply [--index] [-q | --quiet] [--label-ours=<label>] [--label-theirs=<label>] [--label-base=<label>] [<stash>]
git stash branch <branchname> [<stash>]
git stash [push] [-p | --patch] [-S | --staged] [-k | --[no-]keep-index] [-q | --quiet]
	     [-u | --include-untracked] [-a | --all] [(-m | --message) <message>]
	     [--pathspec-from-file=<file> [--pathspec-file-nul]]
	     [--] [<pathspec>…​]
git stash save [-p | --patch] [-S | --staged] [-k | --[no-]keep-index] [-q | --quiet]
           [-u | --include-untracked] [-a | --all] [<message>]
git stash clear
git stash create [<message>]
git stash store [(-m | --message) <message>] [-q | --quiet] <commit>
git stash export (--print | --to-ref <ref>) [<stash>…​]
git stash import <commit>
```

Названия параметров из руководства:

- `-a`
- `--all`
- `-u`
- `--include-untracked`
- `--no-include-untracked`
- `--only-untracked`
- `--index`
- `--label-ours=<label>`
- `--label-theirs=<label>`
- `--label-base=<label>`
- `-k`
- `--keep-index`
- `--no-keep-index`
- `-p`
- `--patch`
- `-U<n>`
- `--unified=<n>`
- `--inter-hunk-context=<n>`
- `-S`
- `--staged`
- `--pathspec-from-file=<file>`
- `--pathspec-file-nul`
- `-q`
- `--quiet`
- `--print`
- `--to-ref`
- `--`

[Руководство stash](https://git-scm.com/docs/git-stash)

#### `status` — 🟨 Проверены отдельные варианты

```text
git status [<options>] [--] [<pathspec>…​]
```

Названия параметров из руководства:

- `-s`
- `--short`
- `-b`
- `--branch`
- `--show-stash`
- `--porcelain[=<version>]`
- `--long`
- `-v`
- `--verbose`
- `-u[<mode>]`
- `--untracked-files[=<mode>]`
- `--ignore-submodules[=<when>]`
- `--ignored[=<mode>]`
- `-z`
- `--column[=<options>]`
- `--no-column`
- `--ahead-behind`
- `--no-ahead-behind`
- `--renames`
- `--no-renames`
- `--find-renames[=<n>]`

[Руководство status](https://git-scm.com/docs/git-status)

#### `submodule` — ⚪ Отдельно не проверено

```text
git submodule [--quiet] [--cached]
git submodule [--quiet] add [<options>] [--] <repository> [<path>]
git submodule [--quiet] status [--cached] [--recursive] [--] [<path>…​]
git submodule [--quiet] init [--] [<path>…​]
git submodule [--quiet] deinit [-f|--force] (--all|[--] <path>...)
git submodule [--quiet] update [<options>] [--] [<path>…​]
git submodule [--quiet] set-branch [<options>] [--] <path>
git submodule [--quiet] set-url [--] <path> <newurl>
git submodule [--quiet] summary [<options>] [--] [<path>…​]
git submodule [--quiet] foreach [--recursive] <command>
git submodule [--quiet] sync [--recursive] [--] [<path>…​]
git submodule [--quiet] absorbgitdirs [--] [<path>…​]
```

Названия параметров из руководства:

- `-q`
- `--quiet`
- `--progress`
- `--all`
- `-b<branch>`
- `--branch=<branch>`
- `-f`
- `--force`
- `--cached`
- `--files`
- `-n<n>`
- `--summary-limit=<n>`
- `--remote`
- `-N`
- `--no-fetch`
- `--checkout`
- `--merge`
- `--rebase`
- `--init`
- `--name=<name>`
- `--reference=<repository>`
- `--dissociate`
- `--recursive`
- `--depth=<depth>`
- `--recommend-shallow`
- `--no-recommend-shallow`
- `-j<n>`
- `--jobs=<n>`
- `--single-branch`
- `--no-single-branch`

[Руководство submodule](https://git-scm.com/docs/git-submodule)

#### `switch` — 🟨 Проверены отдельные варианты

```text
git switch [<options>] [--no-guess] <branch>
git switch [<options>] --detach [<start-point>]
git switch [<options>] (-c|-C) <new-branch> [<start-point>]
git switch [<options>] --orphan <new-branch>
```

Названия параметров из руководства:

- `-c <new-branch>`
- `--create <new-branch>`
- `-C <new-branch>`
- `--force-create <new-branch>`
- `-d`
- `--detach`
- `--guess`
- `--no-guess`
- `-f`
- `--force`
- `--discard-changes`
- `-m`
- `--merge`
- `--conflict=<style>`
- `-q`
- `--quiet`
- `--progress`
- `--no-progress`
- `-t`
- `--track[ (direct|inherit)]`
- `--no-track`
- `--orphan <new-branch>`
- `--ignore-other-worktrees`
- `--recurse-submodules`
- `--no-recurse-submodules`

[Руководство switch](https://git-scm.com/docs/git-switch)

#### `tag` — 🧪 Проверено чтение состояния

```text
git tag [-a | -s | -u <key-id>] [-f] [-m <msg> | -F <file>] [-e]
	[(--trailer <token>[(=|:)<value>])…​]
	<tagname> [<commit> | <object>]
git tag -d <tagname>…​
git tag [-n[<num>]] -l [--contains <commit>] [--no-contains <commit>]
	[--points-at <object>] [--column[=<options>] | --no-column]
	[--create-reflog] [--sort=<key>] [--format=<format>]
	[--merged <commit>] [--no-merged <commit>] [<pattern>…​]
git tag -v [--format=<format>] <tagname>…​
```

Названия параметров из руководства:

- `-a`
- `--annotate`
- `-s`
- `--sign`
- `--no-sign`
- `-u <key-id>`
- `--local-user=<key-id>`
- `-f`
- `--force`
- `-d`
- `--delete`
- `-v`
- `--verify`
- `-n<num>`
- `-l`
- `--list`
- `--sort=<key>`
- `--color[=<when>]`
- `-i`
- `--ignore-case`
- `--omit-empty`
- `--column[=<options>]`
- `--no-column`
- `--contains [<commit>]`
- `--no-contains [<commit>]`
- `--merged [<commit>]`
- `--no-merged [<commit>]`
- `--points-at [<object>]`
- `-m <msg>`
- `--message=<msg>`
- `-F <file>`
- `--file=<file>`
- `--trailer <token>[(=|:)<value>]`
- `-e`
- `--edit`
- `--cleanup=<mode>`
- `--create-reflog`
- `--format=<format>`

[Руководство tag](https://git-scm.com/docs/git-tag)

#### `worktree` — ⚪ Отдельно не проверено

```text
git worktree add [-f] [--detach] [--checkout] [--lock [--reason <string>]]
		 [--orphan] [(-b | -B) <new-branch>] <path> [<commit-ish>]
git worktree list [-v | --porcelain [-z]]
git worktree lock [--reason <string>] <worktree>
git worktree move <worktree> <new-path>
git worktree prune [-n] [-v] [--expire <expire>]
git worktree remove [-f] <worktree>
git worktree repair [<path>…​]
git worktree unlock <worktree>
```

Названия параметров из руководства:

- `-f`
- `--force`
- `-b <new-branch>`
- `-B <new-branch>`
- `-d`
- `--detach`
- `--checkout`
- `--no-checkout`
- `--guess-remote`
- `--no-guess-remote`
- `--relative-paths`
- `--no-relative-paths`
- `--track`
- `--no-track`
- `--lock`
- `-n`
- `--dry-run`
- `--orphan`
- `--porcelain`
- `-z`
- `-q`
- `--quiet`
- `-v`
- `--verbose`
- `--expire <time>`
- `--reason <string>`

[Руководство worktree](https://git-scm.com/docs/git-worktree)

### Дополнительные команды изменения

#### `config` — ⚪ Отдельно не проверено

```text
git config list [<file-option>] [<display-option>] [--includes]
git config get [<file-option>] [<display-option>] [--includes] [--all] [--regexp] [--value=<pattern>] [--fixed-value] [--default=<default>] [--url=<url>] <name>
git config set [<file-option>] [--type=<type>] [--all] [--value=<pattern>] [--fixed-value] <name> <value>
git config unset [<file-option>] [--all] [--value=<pattern>] [--fixed-value] <name>
git config rename-section [<file-option>] <old-name> <new-name>
git config remove-section [<file-option>] <name>
git config edit [<file-option>]
git config [<file-option>] --get-colorbool <name> [<stdout-is-tty>]
```

Названия параметров из руководства:

- `--replace-all`
- `--append`
- `--comment <message>`
- `--all`
- `--regexp`
- `--url=<URL>`
- `--global`
- `--system`
- `--local`
- `--worktree`
- `-f <config-file>`
- `--file <config-file>`
- `--blob <blob>`
- `--value=<pattern>`
- `--no-value`
- `--fixed-value`
- `--type <type>`
- `--bool`
- `--int`
- `--bool-or-int`
- `--path`
- `--expiry-date`
- `--no-type`
- `-z`
- `--null`
- `--name-only`
- `--show-names`
- `--no-show-names`
- `--show-origin`
- `--show-scope`
- `--get-colorbool <name> [<stdout-is-tty>]`
- `--includes`
- `--no-includes`
- `--default <value>`
- `-l`
- `--list`
- `--get <name> [<value-pattern>]`
- `--get-all <name> [<value-pattern>]`
- `--get-regexp <name-regexp>`
- `--get-urlmatch <name> <URL>`
- `--get-color <name> [<default>]`
- `--add <name> <value>`
- `--unset <name> [<value-pattern>]`
- `--unset-all <name> [<value-pattern>]`
- `--rename-section <old-name> <new-name>`
- `--remove-section <name>`
- `-e`
- `--edit`

[Руководство config](https://git-scm.com/docs/git-config)

#### `fast-export` — ⚪ Отдельно не проверено

```text
git fast-export [<options>] [<revision-range>] [[--] <path>…​]
```

Названия параметров из руководства:

- `--progress=<n>`
- `--signed-tags=(verbatim|warn-verbatim|warn-strip|strip|abort)`
- `--signed-commits=(verbatim|warn-verbatim|warn-strip|strip|abort)`
- `--tag-of-filtered-object=(abort|drop|rewrite)`
- `-M`
- `-C`
- `--export-marks=<file>`
- `--import-marks=<file>`
- `--mark-tags`
- `--fake-missing-tagger`
- `--use-done-feature`
- `--no-data`
- `--full-tree`
- `--anonymize`
- `--anonymize-map=<from>[:<to>]`
- `--reference-excluded-parents`
- `--show-original-ids`
- `--reencode=(yes|no|abort)`
- `--refspec`

[Руководство fast-export](https://git-scm.com/docs/git-fast-export)

#### `fast-import` — ⚪ Отдельно не проверено

```text
git fast-import [<options>]
```

Названия параметров из руководства:

- `--force`
- `--quiet`
- `--stats`
- `--allow-unsafe-features`
- `--signed-tags=<mode>`
- `--signed-commits=<mode>`
- `--cat-blob-fd=<fd>`
- `--date-format=<fmt>`
- `--done`
- `--export-marks=<file>`
- `--import-marks=<file>`
- `--import-marks-if-exists=<file>`
- `--relative-marks`
- `--no-relative-marks`
- `--rewrite-submodules-from=<name>:<file>`
- `--rewrite-submodules-to=<name>:<file>`
- `--active-branches=<n>`
- `--big-file-threshold=<n>`
- `--depth=<n>`
- `--export-pack-edges=<file>`
- `--max-pack-size=<n>`

[Руководство fast-import](https://git-scm.com/docs/git-fast-import)

#### `filter-branch` — ⚪ Отдельно не проверено

```text
git filter-branch [--setup <command>] [--subdirectory-filter <directory>]
        [--env-filter <command>] [--tree-filter <command>]
        [--index-filter <command>] [--parent-filter <command>]
        [--msg-filter <command>] [--commit-filter <command>]
        [--tag-name-filter <command>] [--prune-empty]
        [--original <namespace>] [-d <directory>] [-f | --force]
        [--state-branch <branch>] [--] [<rev-list-options>…​]
```

Названия параметров из руководства:

- `--setup <command>`
- `--subdirectory-filter <directory>`
- `--env-filter <command>`
- `--tree-filter <command>`
- `--index-filter <command>`
- `--parent-filter <command>`
- `--msg-filter <command>`
- `--commit-filter <command>`
- `--tag-name-filter <command>`
- `--prune-empty`
- `--original <namespace>`
- `-d <directory>`
- `-f`
- `--force`
- `--state-branch <branch>`

[Руководство filter-branch](https://git-scm.com/docs/git-filter-branch)

#### `mergetool` — ⚪ Отдельно не проверено

```text
git mergetool [--tool=<tool>] [-y | --[no-]prompt] [<file>…​]
```

Названия параметров из руководства:

- `-t <tool>`
- `--tool=<tool>`
- `--tool-help`
- `-y`
- `--no-prompt`
- `--prompt`
- `-g`
- `--gui`
- `--no-gui`
- `-O<orderfile>`

[Руководство mergetool](https://git-scm.com/docs/git-mergetool)

#### `pack-refs` — ⚪ Отдельно не проверено

```text
git pack-refs [--all] [--no-prune] [--auto] [--include <pattern>] [--exclude <pattern>]
```

Названия параметров из руководства:

- `--all`
- `--no-prune`
- `--auto`
- `--include <pattern>`
- `--exclude <pattern>`

[Руководство pack-refs](https://git-scm.com/docs/git-pack-refs)

#### `prune` — ⚪ Отдельно не проверено

```text
git prune [-n] [-v] [--progress] [--expire <time>] [--] [<head>…​]
```

Названия параметров из руководства:

- `-n`
- `--dry-run`
- `-v`
- `--verbose`
- `--progress`
- `--expire <time>`
- `--`

[Руководство prune](https://git-scm.com/docs/git-prune)

#### `reflog` — ⚪ Отдельно не проверено

```text
git reflog [show] [<log-options>] [<ref>]
git reflog list
git reflog exists <ref>
git reflog write <ref> <old-oid> <new-oid> <message>
git reflog delete [--rewrite] [--updateref]
	[--dry-run | -n] [--verbose] <ref>@{<specifier>}…​
git reflog drop [--all [--single-worktree] | <refs>…​]
git reflog expire [--expire=<time>] [--expire-unreachable=<time>]
	[--rewrite] [--updateref] [--stale-fix]
	[--dry-run | -n] [--verbose] [--all [--single-worktree] | <refs>…​]
```

Названия параметров из руководства:

- `--all`
- `--single-worktree`
- `--expire=<time>`
- `--expire-unreachable=<time>`
- `--updateref`
- `--rewrite`
- `--stale-fix`
- `-n`
- `--dry-run`
- `--verbose`

[Руководство reflog](https://git-scm.com/docs/git-reflog)

#### `refs` — ⚪ Отдельно не проверено

```text
git refs migrate --ref-format=<format> [--no-reflog] [--dry-run]
git refs verify [--strict] [--verbose]
git refs list [--count=<count>] [--shell|--perl|--python|--tcl]
		   [(--sort=<key>)…​] [--format=<format>]
		   [--include-root-refs] [--points-at=<object>]
		   [--merged[=<object>]] [--no-merged[=<object>]]
		   [--contains[=<object>]] [--no-contains[=<object>]]
		   [(--exclude=<pattern>)…​] [--start-after=<marker>]
		   [ --stdin | (<pattern>...)]
git refs exists <ref>
git refs optimize [--all] [--no-prune] [--auto] [--include <pattern>] [--exclude <pattern>]
git refs create [--message=<reason>] [--no-deref] [--create-reflog] <ref> <new-value>
git refs delete [--message=<reason>] [--no-deref] <ref> [<old-value>]
git refs update [--message=<reason>] [--no-deref] [--create-reflog] <ref> <new-value> [<old-value>]
git refs rename [--message=<reason>] <old-ref> <new-ref>
```

Названия параметров из руководства:

- `--ref-format=<format>`
- `--dry-run`
- `--reflog`
- `--no-reflog`
- `--strict`
- `--verbose`
- `--stdin`
- `--count=<count>`
- `--sort=<key>`
- `--format[=<format>]`
- `--color[=<when>]`
- `--shell`
- `--perl`
- `--python`
- `--tcl`
- `--points-at=<object>`
- `--merged[=<object>]`
- `--no-merged[=<object>]`
- `--contains[=<object>]`
- `--no-contains[=<object>]`
- `--ignore-case`
- `--omit-empty`
- `--exclude=<excluded-pattern>`
- `--include-root-refs`
- `--start-after=<marker>`
- `--all`
- `--no-prune`
- `--auto`
- `--include <pattern>`
- `--exclude <pattern>`
- `--create-reflog`
- `--message=<reason>`
- `--no-deref`

[Руководство refs](https://git-scm.com/docs/git-refs)

#### `remote` — ⚪ Отдельно не проверено

```text
git remote [-v | --verbose]
git remote add [-t <branch>] [-m <master>] [-f] [--[no-]tags] [--mirror=(fetch|push)] <name> <URL>
git remote rename [--[no-]progress] <old> <new>
git remote remove <name>
git remote set-head <name> (-a | --auto | -d | --delete | <branch>)
git remote set-branches [--add] <name> <branch>…​
git remote get-url [--push] [--all] <name>
git remote set-url [--push] <name> <newurl> [<oldurl>]
git remote set-url --add [--push] <name> <newurl>
git remote set-url --delete [--push] <name> <URL>
git remote [-v | --verbose] show [-n] <name>…​
git remote prune [-n | --dry-run] <name>…​
git remote [-v | --verbose] update [-p | --prune] [(<group> | <remote>)…​]
```

Названия параметров из руководства:

- `-v`
- `--verbose`

[Руководство remote](https://git-scm.com/docs/git-remote)

#### `repack` — ⚪ Отдельно не проверено

```text
git repack [-a] [-A] [-d] [-f] [-F] [-l] [-n] [-q] [-b] [-m]
        [--window=<n>] [--depth=<n>] [--threads=<n>] [--keep-pack=<pack-name>]
        [--write-midx[=<mode>]] [--name-hash-version=<n>] [--path-walk]
        [--filter=<filter-spec>] [--drop-filtered [--dry-run]]
```

Названия параметров из руководства:

- `-a`
- `-A`
- `-d`
- `--cruft`
- `--cruft-expiration=<approxidate>`
- `--max-cruft-size=<n>`
- `--combine-cruft-below-size=<n>`
- `--expire-to=<dir>`
- `-l`
- `-f`
- `-F`
- `-q`
- `--quiet`
- `-n`
- `--window=<n>`
- `--depth=<n>`
- `--threads=<n>`
- `--window-memory=<n>`
- `--max-pack-size=<n>`
- `--filter=<filter-spec>`
- `--filter-to=<dir>`
- `--drop-filtered`
- `--dry-run`
- `-b`
- `--write-bitmap-index`
- `--pack-kept-objects`
- `--keep-pack=<pack-name>`
- `--unpack-unreachable=<when>`
- `-k`
- `--keep-unreachable`
- `-i`
- `--delta-islands`
- `-g<factor>`
- `--geometric=<factor>`
- `-m`
- `--write-midx[=<mode>]`
- `--name-hash-version=<n>`
- `--path-walk`

[Руководство repack](https://git-scm.com/docs/git-repack)

#### `replace` — ⚪ Отдельно не проверено

```text
git replace [-f] <object> <replacement>
git replace [-f] --edit <object>
git replace [-f] --graft <commit> [<parent>…​]
git replace [-f] --convert-graft-file
git replace -d <object>…​
git replace [--format=<format>] [-l [<pattern>]]
```

Названия параметров из руководства:

- `-f`
- `--force`
- `-d`
- `--delete`
- `--edit <object>`
- `--raw`
- `--graft <commit> [<parent>…​]`
- `--convert-graft-file`
- `-l <pattern>`
- `--list <pattern>`
- `--format=<format>`

[Руководство replace](https://git-scm.com/docs/git-replace)

### Дополнительные команды исследования

#### `annotate` — ➖ Нет собственного отображения

```text
git annotate [<options>] [<rev-opts>] [<rev>] [--] <file>
```

Названия параметров из руководства:

- `-b`
- `--root`
- `--show-stats`
- `-L <start>,<end>`
- `-L :<funcname>`
- `-l`
- `-t`
- `-S <revs-file>`
- `--reverse <start>..<end>`
- `--first-parent`
- `-p`
- `--porcelain`
- `--line-porcelain`
- `--incremental`
- `--encoding=<encoding>`
- `--contents <file>`
- `--date <format>`
- `--progress`
- `--no-progress`
- `-M[<num>]`
- `-C[<num>]`
- `--ignore-rev <rev>`
- `--ignore-revs-file <file>`
- `--color-lines`
- `--color-by-age`
- `-h`

[Руководство annotate](https://git-scm.com/docs/git-annotate)

#### `blame` — ➖ Нет собственного отображения

```text
git blame [-c] [-b] [-l] [--root] [-t] [-f] [-n] [-s] [-e] [-p] [-w] [--incremental]
	  [-L <range>] [-S <revs-file>] [-M] [-C] [-C] [-C] [--since=<date>]
	  [--ignore-rev <rev>] [--ignore-revs-file <file>]
	  [--color-lines] [--color-by-age] [--progress] [--abbrev=<n>]
	  [ --contents <file> ] [<rev> | --reverse <rev>..<rev>] [--] <file>
```

Названия параметров из руководства:

- `-b`
- `--root`
- `--show-stats`
- `-L <start>,<end>`
- `-L :<funcname>`
- `-l`
- `-t`
- `-S <revs-file>`
- `--reverse <start>..<end>`
- `--first-parent`
- `-p`
- `--porcelain`
- `--line-porcelain`
- `--incremental`
- `--encoding=<encoding>`
- `--contents <file>`
- `--date <format>`
- `--progress`
- `--no-progress`
- `-M[<num>]`
- `-C[<num>]`
- `--ignore-rev <rev>`
- `--ignore-revs-file <file>`
- `--color-lines`
- `--color-by-age`
- `-h`
- `-c`
- `--score-debug`
- `-f`
- `--show-name`
- `-n`
- `--show-number`
- `-s`
- `-e`
- `--show-email`
- `-w`
- `--diff-algorithm=(patience|minimal|histogram|myers)`
- `--abbrev=<n>`

[Руководство blame](https://git-scm.com/docs/git-blame)

#### `bugreport` — ⚪ Отдельно не проверено

```text
git bugreport [(-o | --output-directory) <path>]
                [(-s | --suffix) <format> | --no-suffix]
                [--diagnose[=<mode>]]
```

Названия параметров из руководства:

- `-o <path>`
- `--output-directory <path>`
- `-s <format>`
- `--suffix <format>`
- `--no-suffix`
- `--no-diagnose`
- `--diagnose[=<mode>]`

[Руководство bugreport](https://git-scm.com/docs/git-bugreport)

#### `count-objects` — ➖ Нет собственного отображения

```text
git count-objects [-v] [-H | --human-readable]
```

Названия параметров из руководства:

- `-v`
- `--verbose`
- `-H`
- `--human-readable`

[Руководство count-objects](https://git-scm.com/docs/git-count-objects)

#### `diagnose` — ⚪ Отдельно не проверено

```text
git diagnose [(-o | --output-directory) <path>] [(-s | --suffix) <format>]
               [--mode=<mode>]
```

Названия параметров из руководства:

- `-o <path>`
- `--output-directory <path>`
- `-s <format>`
- `--suffix <format>`
- `--mode=(stats|all)`

[Руководство diagnose](https://git-scm.com/docs/git-diagnose)

#### `difftool` — ⚪ Отдельно не проверено

```text
git difftool [<options>] [<commit> [<commit>]] [--] [<path>…​]
```

Названия параметров из руководства:

- `-d`
- `--dir-diff`
- `-y`
- `--no-prompt`
- `--prompt`
- `--rotate-to=<file>`
- `--skip-to=<file>`
- `-t <tool>`
- `--tool=<tool>`
- `--tool-help`
- `--symlinks`
- `--no-symlinks`
- `-x <command>`
- `--extcmd=<command>`
- `-g`
- `--gui`
- `--no-gui`
- `--trust-exit-code`
- `--no-trust-exit-code`

[Руководство difftool](https://git-scm.com/docs/git-difftool)

#### `fsck` — ⚪ Отдельно не проверено

```text
git fsck [--tags] [--root] [--unreachable] [--cache] [--no-reflogs]
         [--[no-]full] [--strict] [--verbose] [--lost-found]
         [--[no-]dangling] [--[no-]progress] [--connectivity-only]
         [--[no-]name-objects] [--[no-]references] [<object>…​]
```

Названия параметров из руководства:

- `--unreachable`
- `--dangling`
- `--no-dangling`
- `--root`
- `--tags`
- `--cache`
- `--no-reflogs`
- `--full`
- `--connectivity-only`
- `--strict`
- `--verbose`
- `--lost-found`
- `--name-objects`
- `--progress`
- `--no-progress`
- `--references`
- `--no-references`

[Руководство fsck](https://git-scm.com/docs/git-fsck)

#### `gitweb` — ⚪ Отдельно не проверено

Локальный SYNOPSIS не найден; см. руководство команды.

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство gitweb](https://git-scm.com/docs/gitweb)

#### `help` — ➖ Нет собственного отображения

```text
git help [-a|--all] [--[no-]verbose] [--[no-]external-commands] [--[no-]aliases]
git help [[-i|--info] [-m|--man] [-w|--web]] [<command>|<doc>]
git help [-g|--guides]
git help [-c|--config]
git help [--user-interfaces]
git help [--developer-interfaces]
```

Названия параметров из руководства:

- `-a`
- `--all`
- `--no-external-commands`
- `--no-aliases`
- `--verbose`
- `-c`
- `--config`
- `-g`
- `--guides`
- `--user-interfaces`
- `--developer-interfaces`
- `-i`
- `--info`
- `-m`
- `--man`
- `-w`
- `--web`

[Руководство help](https://git-scm.com/docs/git-help)

#### `instaweb` — ⚪ Отдельно не проверено

```text
git instaweb [--local] [--httpd=<httpd>] [--port=<port>]
               [--browser=<browser>]
git instaweb [--start] [--stop] [--restart]
```

Названия параметров из руководства:

- `-l`
- `--local`
- `-d`
- `--httpd`
- `-m`
- `--module-path`
- `-p`
- `--port`
- `-b`
- `--browser`
- `--start`
- `--stop`
- `--restart`

[Руководство instaweb](https://git-scm.com/docs/git-instaweb)

#### `merge-tree` — ⚪ Отдельно не проверено

```text
git merge-tree [--write-tree] [<options>] <branch1> <branch2>
git merge-tree [--trivial-merge] <base-tree> <branch1> <branch2> (deprecated)
```

Названия параметров из руководства:

- `--stdin`
- `-z`
- `--name-only`
- `--messages`
- `--no-messages`
- `--quiet`
- `--allow-unrelated-histories`
- `--merge-base=<tree-ish>`
- `-X<option>`
- `--strategy-option=<option>`

[Руководство merge-tree](https://git-scm.com/docs/git-merge-tree)

#### `rerere` — ⚪ Отдельно не проверено

```text
git rerere [clear | forget <pathspec>…​ | diff | status | remaining | gc]
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство rerere](https://git-scm.com/docs/git-rerere)

#### `show-branch` — ➖ Нет собственного отображения

```text
git show-branch [-a | --all] [-r | --remotes] [--topo-order | --date-order]
                [--current] [--color[=<when>] | --no-color] [--sparse]
                [--more=<n> | --list | --independent | --merge-base]
                [--no-name | --sha1-name] [--topics]
                [(<rev> | <glob>)…​]
git show-branch (-g | --reflog)[=<n>[,<base>]] [--list] [<ref>]
```

Названия параметров из руководства:

- `-r`
- `--remotes`
- `-a`
- `--all`
- `--current`
- `--topo-order`
- `--date-order`
- `--sparse`
- `--more=<n>`
- `--list`
- `--merge-base`
- `--independent`
- `--no-name`
- `--sha1-name`
- `--topics`
- `-g`
- `--reflog[=<n>[,<base>]] [<ref>]`
- `--color[=<when>]`
- `--no-color`

[Руководство show-branch](https://git-scm.com/docs/git-show-branch)

#### `verify-commit` — ⚪ Отдельно не проверено

```text
git verify-commit [-v | --verbose] [--raw] <commit>…​
```

Названия параметров из руководства:

- `--raw`
- `-v`
- `--verbose`

[Руководство verify-commit](https://git-scm.com/docs/git-verify-commit)

#### `verify-tag` — ⚪ Отдельно не проверено

```text
git verify-tag [-v | --verbose] [--format=<format>] [--raw] <tag>…​
```

Названия параметров из руководства:

- `--raw`
- `-v`
- `--verbose`

[Руководство verify-tag](https://git-scm.com/docs/git-verify-tag)

#### `version` — ➖ Нет собственного отображения

```text
git version [--build-options]
```

Названия параметров из руководства:

- `--build-options`

[Руководство version](https://git-scm.com/docs/git-version)

#### `whatchanged` — ➖ Нет собственного отображения

```text
git whatchanged <option>…​
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство whatchanged](https://git-scm.com/docs/git-whatchanged)

### Интеграции и обмен

#### `archimport` — ⚪ Отдельно не проверено

```text
git archimport [-h] [-v] [-o] [-a] [-f] [-T] [-D <depth>] [-t <tempdir>]
               <archive>/<branch>[:<git-branch>]…​
```

Названия параметров из руководства:

- `-h`
- `-v`
- `-T`
- `-f`
- `-o`
- `-D <depth>`
- `-a`
- `-t <tmpdir>`

[Руководство archimport](https://git-scm.com/docs/git-archimport)

#### `cvsexportcommit` — ⚪ Отдельно не проверено

```text
git cvsexportcommit [-h] [-u] [-v] [-c] [-P] [-p] [-a] [-d <cvsroot>]
        [-w <cvs-workdir>] [-W] [-f] [-m <msgprefix>] [<parent-commit>] <commit-id>
```

Названия параметров из руководства:

- `-c`
- `-p`
- `-a`
- `-d`
- `-f`
- `-P`
- `-m`
- `-u`
- `-k`
- `-w`
- `-W`
- `-v`

[Руководство cvsexportcommit](https://git-scm.com/docs/git-cvsexportcommit)

#### `cvsimport` — ⚪ Отдельно не проверено

```text
git cvsimport [-o <branch-for-HEAD>] [-h] [-v] [-d <CVSROOT>]
              [-A <author-conv-file>] [-p <options-for-cvsps>] [-P <file>]
              [-C <git-repository>] [-z <fuzz>] [-i] [-k] [-u] [-s <subst>]
              [-a] [-m] [-M <regex>] [-S <regex>] [-L <commit-limit>]
              [-r <remote>] [-R] [<CVS-module>]
```

Названия параметров из руководства:

- `-v`
- `-d <CVSROOT>`
- `-C <target-dir>`
- `-r <remote>`
- `-o <branch-for-HEAD>`
- `-i`
- `-k`
- `-u`
- `-s <subst>`
- `-p <options-for-cvsps>`
- `-z <fuzz>`
- `-P <cvsps-output-file>`
- `-m`
- `-M <regex>`
- `-S <regex>`
- `-a`
- `-L <limit>`
- `-A <author-conv-file>`
- `-R`
- `-h`

[Руководство cvsimport](https://git-scm.com/docs/git-cvsimport)

#### `cvsserver` — ⚪ Отдельно не проверено

```text
export CVS_SERVER="git cvsserver"
cvs -d :ext:user@server/path/repo.git co <HEAD_name>
cvspserver stream tcp nowait nobody /usr/bin/git-cvsserver git-cvsserver pserver
git-cvsserver [<options>] [pserver|server] [<directory> …​]
```

Названия параметров из руководства:

- `--base-path <path>`
- `--strict-paths`
- `--export-all`
- `-V`
- `--version`
- `-h`
- `-H`
- `--help`

[Руководство cvsserver](https://git-scm.com/docs/git-cvsserver)

#### `imap-send` — ⚪ Отдельно не проверено

```text
git imap-send [-v] [-q] [--[no-]curl] [--[no-]draft] [(--folder|-f) <folder>]
git imap-send --list
```

Названия параметров из руководства:

- `-v`
- `--verbose`
- `-q`
- `--quiet`
- `-f <folder>`
- `--folder=<folder>`
- `--curl`
- `--no-curl`
- `--draft`
- `--no-draft`
- `--list`

[Руководство imap-send](https://git-scm.com/docs/git-imap-send)

#### `p4` — ⚪ Отдельно не проверено

```text
git p4 clone [<sync-options>] [<clone-options>] <p4-depot-path>…​
git p4 sync [<sync-options>] [<p4-depot-path>…​]
git p4 rebase
git p4 submit [<submit-options>] [<master-branch-name>]
```

Названия параметров из руководства:

- `--git-dir <dir>`
- `-v`
- `--verbose`
- `--branch <ref>`
- `--detect-branches`
- `--changesfile <file>`
- `--silent`
- `--detect-labels`
- `--import-labels`
- `--import-local`
- `--max-changes <n>`
- `--changes-block-size <n>`
- `--keep-path`
- `--use-client-spec`
- `-/ <path>`
- `--destination <directory>`
- `--bare`
- `--origin <commit>`
- `-M`
- `--preserve-user`
- `--export-labels`
- `-n`
- `--dry-run`
- `--prepare-p4-only`
- `--shelve`
- `--update-shelve CHANGELIST`
- `--conflict=(ask|skip|quit)`
- `--branch <branch>`
- `--commit (<sha1>|<sha1>..<sha1>)`
- `--disable-rebase`
- `--disable-p4sync`
- `--origin`

[Руководство p4](https://git-scm.com/docs/git-p4)

#### `quiltimport` — ⚪ Отдельно не проверено

```text
git quiltimport [--dry-run | -n] [--author <author>] [--patches <dir>]
                [--series <file>] [--keep-non-patch]
```

Названия параметров из руководства:

- `-n`
- `--dry-run`
- `--author Author Name <Author Email>`
- `--patches <dir>`
- `--series <file>`
- `--keep-non-patch`

[Руководство quiltimport](https://git-scm.com/docs/git-quiltimport)

#### `request-pull` — ⚪ Отдельно не проверено

```text
git request-pull [-p] <start> <URL> [<end>]
```

Названия параметров из руководства:

- `-p`

[Руководство request-pull](https://git-scm.com/docs/git-request-pull)

#### `send-email` — ⚪ Отдельно не проверено

```text
git send-email [<options>] (<file>|<directory>)…​
git send-email [<options>] <format-patch-options>
git send-email --dump-aliases
git send-email --translate-aliases
```

Названия параметров из руководства:

- `--annotate`
- `--bcc=<address>,...`
- `--cc=<address>,...`
- `--compose`
- `--from=<address>`
- `--reply-to=<address>`
- `--in-reply-to=<identifier>`
- `--outlook-id-fix`
- `--no-outlook-id-fix`
- `--subject=<string>`
- `--to=<address>,...`
- `--8bit-encoding=<encoding>`
- `--compose-encoding=<encoding>`
- `--transfer-encoding=(7bit|8bit|quoted-printable|base64|auto)`
- `--xmailer`
- `--no-xmailer`
- `--envelope-sender=<address>`
- `--sendmail-cmd=<command>`
- `--smtp-encryption=<encryption>`
- `--smtp-domain=<FQDN>`
- `--smtp-auth=<mechanisms>`
- `--smtp-pass[=<password>]`
- `--no-smtp-auth`
- `--smtp-server=<host>`
- `--smtp-server-port=<port>`
- `--smtp-server-option=<option>`
- `--smtp-ssl`
- `--smtp-ssl-cert-path <path>`
- `--smtp-ssl-client-cert <path>`
- `--smtp-ssl-client-key <path>`
- `--smtp-user=<user>`
- `--smtp-debug=(0|1)`
- `--imap-sent-folder=<folder>`
- `--use-imap-only`
- `--no-use-imap-only`
- `--batch-size=<num>`
- `--relogin-delay=<int>`
- `--no-to`
- `--no-cc`
- `--no-bcc`
- `--no-identity`
- `--to-cmd=<command>`
- `--cc-cmd=<command>`
- `--header-cmd=<command>`
- `--no-header-cmd`
- `--chain-reply-to`
- `--no-chain-reply-to`
- `--identity=<identity>`
- `--signed-off-by-cc`
- `--no-signed-off-by-cc`
- `--cc-cover`
- `--no-cc-cover`
- `--to-cover`
- `--no-to-cover`
- `--suppress-cc=<category>`
- `--suppress-from`
- `--no-suppress-from`
- `--thread`
- `--no-thread`
- `--mailmap`
- `--no-mailmap`
- `--confirm=<mode>`
- `--dry-run`
- `--format-patch`
- `--no-format-patch`
- `--quiet`
- `--validate`
- `--no-validate`
- `--force`
- `--dump-aliases`
- `--translate-aliases`

[Руководство send-email](https://git-scm.com/docs/git-send-email)

#### `svn` — ⚪ Отдельно не проверено

```text
git svn <command> [<options>] [<arguments>]
```

Названия параметров из руководства:

- `-T<trunk-subdir>`
- `--trunk=<trunk-subdir>`
- `-t<tags-subdir>`
- `--tags=<tags-subdir>`
- `-b<branches-subdir>`
- `--branches=<branches-subdir>`
- `-s`
- `--stdlayout`
- `--no-metadata`
- `--use-svm-props`
- `--use-svnsync-props`
- `--rewrite-root=<URL>`
- `--rewrite-uuid=<UUID>`
- `--username=<user>`
- `--prefix=<prefix>`
- `--ignore-refs=<regex>`
- `--ignore-paths=<regex>`
- `--include-paths=<regex>`
- `--no-minimize-url`
- `--localtime`
- `--parent`
- `--log-window-size=<n>`
- `--preserve-empty-dirs`
- `--placeholder-filename=<filename>`
- `-l`
- `--local`
- `--no-rebase`
- `--commit-url <URL>`
- `--mergeinfo=<mergeinfo>`
- `--interactive`
- `-m`
- `--message`
- `-t`
- `--tag`
- `-d<path>`
- `--destination=<path>`
- `--username`
- `--commit-url`
- `--parents`
- `-r <n>[:<n>]`
- `--revision=<n>[:<n>]`
- `-v`
- `--verbose`
- `--limit=<n>`
- `--incremental`
- `--show-commit`
- `--oneline`
- `--git-format`
- `-B`
- `--before`
- `-A`
- `--after`
- `-m <msg>`
- `--message=<msg>`
- `-F <filename>`
- `--file=<filename>`
- `-r <n>`
- `--revision=<n>`
- `-p`
- `--shared[=(false|true|umask|group|all|world|everybody)]`
- `--template=<template-directory>`
- `-r <arg>`
- `--revision <arg>`
- `-`
- `--stdin`
- `--rmdir`
- `-e`
- `--edit`
- `-l<num>`
- `--find-copies-harder`
- `-A<filename>`
- `--authors-file=<filename>`
- `--authors-prog=<filename>`
- `-q`
- `--quiet`
- `--merge`
- `-s<strategy>`
- `--strategy=<strategy>`
- `--rebase-merges`
- `-n`
- `--dry-run`
- `--use-log-author`
- `--add-author-from`
- `-i<GIT_SVN_ID>`
- `--id <GIT_SVN_ID>`
- `-R<remote-name>`
- `--svn-remote <remote-name>`
- `--follow-parent`

[Руководство svn](https://git-scm.com/docs/git-svn)

### Низкоуровневые команды изменения

#### `apply` — ⚪ Отдельно не проверено

```text
git apply [--stat] [--numstat] [--summary] [--check]
	  [--index | --intent-to-add] [--3way] [--ours | --theirs | --union]
	  [--apply] [--no-add] [--build-fake-ancestor=<file>] [-R | --reverse]
	  [--allow-binary-replacement | --binary] [--reject] [-z]
	  [-p<n>] [-C<n>] [--inaccurate-eof] [--recount] [--cached]
	  [--ignore-space-change | --ignore-whitespace]
	  [--whitespace=(nowarn|warn|fix|error|error-all)]
	  [--exclude=<path>] [--include=<path>] [--directory=<root>]
	  [--verbose | --quiet] [--unsafe-paths] [--allow-empty] [<patch>…​]
```

Названия параметров из руководства:

- `--stat`
- `--numstat`
- `--summary`
- `--check`
- `--index`
- `--cached`
- `-N`
- `--intent-to-add`
- `-3`
- `--3way`
- `--ours`
- `--theirs`
- `--union`
- `--build-fake-ancestor=<file>`
- `-R`
- `--reverse`
- `--reject`
- `-z`
- `-p<n>`
- `-C<n>`
- `--unidiff-zero`
- `--apply`
- `--no-add`
- `--allow-binary-replacement`
- `--binary`
- `--exclude=<path-pattern>`
- `--include=<path-pattern>`
- `--ignore-space-change`
- `--ignore-whitespace`
- `--whitespace=<action>`
- `--inaccurate-eof`
- `-v`
- `--verbose`
- `-q`
- `--quiet`
- `--recount`
- `--directory=<root>`
- `--unsafe-paths`
- `--allow-empty`

[Руководство apply](https://git-scm.com/docs/git-apply)

#### `checkout-index` — ⚪ Отдельно не проверено

```text
git checkout-index [-u] [-q] [-a] [-f] [-n] [--prefix=<string>]
                   [--stage=<number>|all]
                   [--temp]
                   [--ignore-skip-worktree-bits]
                   [-z] [--stdin]
                   [--] [<file>…​]
```

Названия параметров из руководства:

- `-u`
- `--index`
- `-q`
- `--quiet`
- `-f`
- `--force`
- `-a`
- `--all`
- `-n`
- `--no-create`
- `--prefix=<string>`
- `--stage=<number>|all`
- `--temp`
- `--ignore-skip-worktree-bits`
- `--stdin`
- `-z`
- `--`

[Руководство checkout-index](https://git-scm.com/docs/git-checkout-index)

#### `commit-graph` — ⚪ Отдельно не проверено

```text
git commit-graph verify [--object-dir <dir>] [--shallow] [--[no-]progress]
git commit-graph write [--object-dir <dir>] [--append]
                        [--split[=<strategy>]] [--reachable | --stdin-packs | --stdin-commits]
                        [--changed-paths] [--[no-]max-new-filters <n>] [--[no-]progress]
                        <split-options>
```

Названия параметров из руководства:

- `--object-dir`
- `--progress`
- `--no-progress`

[Руководство commit-graph](https://git-scm.com/docs/git-commit-graph)

#### `commit-tree` — 🧪 Проверено чтение состояния

```text
git commit-tree <tree> [(-p <parent>)…​]
git commit-tree [(-p <parent>)…​] [-S[<keyid>]] [(-m <message>)…​]
                  [(-F <file>)…​] <tree>
```

Названия параметров из руководства:

- `-p <parent>`
- `-m <message>`
- `-F <file>`
- `-S[<keyid>]`
- `--gpg-sign[=<keyid>]`
- `--no-gpg-sign`

[Руководство commit-tree](https://git-scm.com/docs/git-commit-tree)

#### `hash-object` — ⚪ Отдельно не проверено

```text
git hash-object [-t <type>] [-w] [--path=<file> | --no-filters]
                [--stdin [--literally]] [--] <file>…​
git hash-object [-t <type>] [-w] --stdin-paths [--no-filters]
```

Названия параметров из руководства:

- `-t <type>`
- `-w`
- `--stdin`
- `--stdin-paths`
- `--path`
- `--no-filters`
- `--literally`

[Руководство hash-object](https://git-scm.com/docs/git-hash-object)

#### `index-pack` — ⚪ Отдельно не проверено

```text
git index-pack [-v] [-o <index-file>] [--[no-]rev-index] <pack-file>
git index-pack --stdin [--fix-thin] [--keep] [-v] [-o <index-file>]
                  [--[no-]rev-index] [<pack-file>]
```

Названия параметров из руководства:

- `-v`
- `-o <index-file>`
- `--rev-index`
- `--no-rev-index`
- `--stdin`
- `--fix-thin`
- `--keep`
- `--keep=<msg>`
- `--index-version=<version>[,<offset>]`
- `--strict[=<msg-id>=<severity>…​]`
- `--progress-title`
- `--check-self-contained-and-connected`
- `--fsck-objects[=<msg-id>=<severity>…​]`
- `--threads=<n>`
- `--max-input-size=<size>`
- `--object-format=<hash-algorithm>`
- `--promisor[=<message>]`

[Руководство index-pack](https://git-scm.com/docs/git-index-pack)

#### `merge-file` — ⚪ Отдельно не проверено

```text
git merge-file [-L <current-name> [-L <base-name> [-L <other-name>]]]
        [--ours|--theirs|--union] [-p|--stdout] [-q|--quiet] [--marker-size=<n>]
        [--[no-]diff3] [--object-id] <current> <base> <other>
```

Названия параметров из руководства:

- `--object-id`
- `-L <label>`
- `-p`
- `-q`
- `--diff3`
- `--zdiff3`
- `--ours`
- `--theirs`
- `--union`
- `--diff-algorithm={patience|minimal|histogram|myers}`

[Руководство merge-file](https://git-scm.com/docs/git-merge-file)

#### `merge-index` — ⚪ Отдельно не проверено

```text
git merge-index [-o] [-q] <merge-program> (-a | ( [--] <file>…​) )
```

Названия параметров из руководства:

- `--`
- `-a`
- `-o`
- `-q`

[Руководство merge-index](https://git-scm.com/docs/git-merge-index)

#### `mktag` — ⚪ Отдельно не проверено

```text
git mktag
```

Названия параметров из руководства:

- `--strict`

[Руководство mktag](https://git-scm.com/docs/git-mktag)

#### `mktree` — 🧪 Проверено чтение состояния

```text
git mktree [-z] [--missing] [--batch]
```

Названия параметров из руководства:

- `-z`
- `--missing`
- `--batch`

[Руководство mktree](https://git-scm.com/docs/git-mktree)

#### `multi-pack-index` — ⚪ Отдельно не проверено

```text
git multi-pack-index [<options>] write [--preferred-pack=<pack>]
                         [--[no-]bitmap] [--[no-]incremental] [--[no-]stdin-packs]
                         [--refs-snapshot=<path>] [--[no-]write-chain-file]
                         [--base=<checksum>]
git multi-pack-index [<options>] compact [--[no-]incremental]
                         [--[no-]bitmap] [--base=<checksum>] [--[no-]write-chain-file]
                         <from> <to>
git multi-pack-index [<options>] verify
git multi-pack-index [<options>] expire
git multi-pack-index [<options>] repack [--batch-size=<size>]
```

Названия параметров из руководства:

- `--object-dir=<dir>`
- `--progress`
- `--no-progress`
- `--preferred-pack=<pack>`
- `--[no-]bitmap`
- `--stdin-packs`
- `--refs-snapshot=<path>`
- `--incremental`
- `--[no-]write-chain-file`
- `--base=<checksum>`

[Руководство multi-pack-index](https://git-scm.com/docs/git-multi-pack-index)

#### `pack-objects` — ⚪ Отдельно не проверено

```text
git pack-objects [-q | --progress | --all-progress] [--all-progress-implied]
                   [--no-reuse-delta] [--delta-base-offset] [--non-empty]
                   [--local] [--incremental] [--window=<n>] [--depth=<n>]
                   [--revs [--unpacked | --all]] [--keep-pack=<pack-name>]
                   [--cruft] [--cruft-expiration=<time>]
                   [--stdout [--filter=<filter-spec>] | <base-name>]
                   [--shallow] [--keep-true-parents] [--[no-]sparse]
                   [--name-hash-version=<n>] [--path-walk] < <object-list>
```

Названия параметров из руководства:

- `--stdout`
- `--revs`
- `--unpacked`
- `--all`
- `--include-tag`
- `--stdin-packs[=<mode>]`
- `--cruft`
- `--cruft-expiration=<approxidate>`
- `--window=<n>`
- `--depth=<n>`
- `--window-memory=<n>`
- `--max-pack-size=<n>`
- `--honor-pack-keep`
- `--keep-pack=<pack-name>`
- `--incremental`
- `--local`
- `--non-empty`
- `--progress`
- `--all-progress`
- `--all-progress-implied`
- `-q`
- `--no-reuse-delta`
- `--no-reuse-object`
- `--compression=<n>`
- `--sparse`
- `--no-sparse`
- `--thin`
- `--shallow`
- `--delta-base-offset`
- `--threads=<n>`
- `--index-version=<version>[,<offset>]`
- `--keep-true-parents`
- `--filter=<filter-spec>`
- `--no-filter`
- `--missing=<missing-action>`
- `--exclude-promisor-objects`
- `--keep-unreachable`
- `--pack-loose-unreachable`
- `--unpack-unreachable`
- `--delta-islands`
- `--name-hash-version=<n>`
- `--path-walk`

[Руководство pack-objects](https://git-scm.com/docs/git-pack-objects)

#### `prune-packed` — ⚪ Отдельно не проверено

```text
git prune-packed [-n | --dry-run] [-q | --quiet]
```

Названия параметров из руководства:

- `-n`
- `--dry-run`
- `-q`
- `--quiet`

[Руководство prune-packed](https://git-scm.com/docs/git-prune-packed)

#### `read-tree` — ⚪ Отдельно не проверено

```text
git read-tree [(-m [--trivial] [--aggressive] | --reset | --prefix=<prefix>)
                [-u | -i]] [--index-output=<file>] [--no-sparse-checkout]
                (--empty | <tree-ish1> [<tree-ish2> [<tree-ish3>]])
```

Названия параметров из руководства:

- `-m`
- `--reset`
- `-u`
- `-i`
- `-n`
- `--dry-run`
- `-v`
- `--trivial`
- `--aggressive`
- `--prefix=<prefix>`
- `--index-output=<file>`
- `--recurse-submodules`
- `--no-recurse-submodules`
- `--no-sparse-checkout`
- `--empty`
- `-q`
- `--quiet`

[Руководство read-tree](https://git-scm.com/docs/git-read-tree)

#### `replay` — ⚪ Отдельно не проверено

```text
(EXPERIMENTAL!) git replay ([--contained] --onto=<newbase> | --advance=<branch> | --revert=<branch>)
                             [--ref=<ref>] [--ref-action=<mode>] [--linearize] <revision-range>
```

Названия параметров из руководства:

- `--onto=<newbase>`
- `--advance=<branch>`
- `--revert=<branch>`
- `--contained`
- `--ref=<ref>`
- `--ref-action[=<mode>]`
- `--linearize`
- `-<number>`
- `-n <number>`
- `--max-count=<number>`
- `--max-count-oldest=<number>`
- `--skip=<number>`
- `--since=<date>`
- `--after=<date>`
- `--since-as-filter=<date>`
- `--until=<date>`
- `--before=<date>`
- `--author=<pattern>`
- `--committer=<pattern>`
- `--grep-reflog=<pattern>`
- `--grep=<pattern>`
- `--all-match`
- `--invert-grep`
- `-i`
- `--regexp-ignore-case`
- `--basic-regexp`
- `-E`
- `--extended-regexp`
- `-F`
- `--fixed-strings`
- `-P`
- `--perl-regexp`
- `--remove-empty`
- `--merges`
- `--no-merges`
- `--min-parents=<number>`
- `--max-parents=<number>`
- `--no-min-parents`
- `--no-max-parents`
- `--first-parent`
- `--exclude-first-parent-only`
- `--maximal-only`
- `--not`
- `--all`
- `--branches[=<pattern>]`
- `--tags[=<pattern>]`
- `--remotes[=<pattern>]`
- `--glob=<glob-pattern>`
- `--exclude=<glob-pattern>`
- `--exclude-hidden=(fetch|receive|uploadpack)`
- `--reflog`
- `--alternate-refs`
- `--single-worktree`
- `--ignore-missing`
- `--bisect`
- `--stdin`
- `--cherry-mark`
- `--cherry-pick`
- `--left-only`
- `--right-only`
- `--cherry`
- `-g`
- `--walk-reflogs`
- `--merge`
- `--boundary`
- `--simplify-by-decoration`
- `--show-pulls`
- `--full-history`
- `--dense`
- `--sparse`
- `--simplify-merges`
- `--ancestry-path[=<commit>]`
- `--full-history without parent rewriting`
- `--full-history with parent rewriting`
- `--date-order`
- `--author-date-order`
- `--topo-order`
- `--reverse`
- `--no-walk[=(sorted|unsorted)]`
- `--do-walk`

[Руководство replay](https://git-scm.com/docs/git-replay)

#### `symbolic-ref` — ⚪ Отдельно не проверено

```text
git symbolic-ref [-m <reason>] <name> <ref>
git symbolic-ref [-q] [--short] [--no-recurse] <name>
git symbolic-ref --delete [-q] <name>
```

Названия параметров из руководства:

- `-d`
- `--delete`
- `-q`
- `--quiet`
- `--short`
- `--recurse`
- `--no-recurse`
- `-m`

[Руководство symbolic-ref](https://git-scm.com/docs/git-symbolic-ref)

#### `unpack-objects` — ⚪ Отдельно не проверено

```text
git unpack-objects [-n] [-q] [-r] [--strict]
```

Названия параметров из руководства:

- `-n`
- `-q`
- `-r`
- `--strict`
- `--max-input-size=<size>`

[Руководство unpack-objects](https://git-scm.com/docs/git-unpack-objects)

#### `update-index` — ⚪ Отдельно не проверено

```text
git update-index
             [--add] [--remove | --force-remove] [--replace]
             [--refresh] [-q] [--unmerged] [--ignore-missing]
             [(--cacheinfo <mode>,<object>,<file>)…​]
             [--chmod=(+|-)x]
             [--[no-]assume-unchanged]
             [--[no-]skip-worktree]
             [--[no-]ignore-skip-worktree-entries]
             [--[no-]fsmonitor-valid]
             [--ignore-submodules]
             [--[no-]split-index]
             [--[no-|test-|force-]untracked-cache]
             [--[no-]fsmonitor]
             [--really-refresh] [--unresolve] [--again | -g]
             [--info-only] [--index-info]
             [-z] [--stdin] [--index-version <n>]
             [--show-index-version]
             [--verbose]
             [--] [<file>…​]
```

Названия параметров из руководства:

- `--add`
- `--remove`
- `--refresh`
- `-q`
- `--ignore-submodules`
- `--unmerged`
- `--ignore-missing`
- `--cacheinfo <mode>,<object>,<path>`
- `--cacheinfo <mode> <object> <path>`
- `--index-info`
- `--chmod=(+|-)x`
- `--assume-unchanged`
- `--no-assume-unchanged`
- `--really-refresh`
- `--skip-worktree`
- `--no-skip-worktree`
- `--ignore-skip-worktree-entries`
- `--no-ignore-skip-worktree-entries`
- `--fsmonitor-valid`
- `--no-fsmonitor-valid`
- `-g`
- `--again`
- `--unresolve`
- `--info-only`
- `--force-remove`
- `--replace`
- `--stdin`
- `--verbose`
- `--index-version <n>`
- `--show-index-version`
- `-z`
- `--split-index`
- `--no-split-index`
- `--untracked-cache`
- `--no-untracked-cache`
- `--test-untracked-cache`
- `--force-untracked-cache`
- `--fsmonitor`
- `--no-fsmonitor`
- `--`

[Руководство update-index](https://git-scm.com/docs/git-update-index)

#### `update-ref` — 🧪 Проверено чтение состояния

```text
git update-ref [-m <reason>] [--no-deref] -d <ref> [<old-oid>]
git update-ref [-m <reason>] [--no-deref] [--create-reflog] <ref> <new-oid> [<old-oid>]
git update-ref [-m <reason>] [--no-deref] --stdin [-z] [--batch-updates]
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство update-ref](https://git-scm.com/docs/git-update-ref)

#### `write-tree` — ⚪ Отдельно не проверено

```text
git write-tree [--missing-ok] [--prefix=<prefix>/]
```

Названия параметров из руководства:

- `--missing-ok`
- `--prefix=<prefix>/`

[Руководство write-tree](https://git-scm.com/docs/git-write-tree)

### Низкоуровневые команды исследования

#### `cat-file` — ➖ Нет собственного отображения

```text
git cat-file <type> <object>
git cat-file (-e | -p | -t | -s) <object>
git cat-file (--textconv | --filters)
             [<rev>:<path|tree-ish> | --path=<path|tree-ish> <rev>]
git cat-file (--batch | --batch-check | --batch-command) [--batch-all-objects]
             [--buffer] [--follow-symlinks] [--unordered]
             [--textconv | --filters] [-Z]
```

Названия параметров из руководства:

- `-t`
- `-s`
- `-e`
- `-p`
- `--mailmap`
- `--no-mailmap`
- `--use-mailmap`
- `--no-use-mailmap`
- `--textconv`
- `--filters`
- `--filter=<filter-spec>`
- `--no-filter`
- `--path=<path>`
- `--batch`
- `--batch=<format>`
- `--batch-check`
- `--batch-check=<format>`
- `--batch-command`
- `--batch-command=<format>`
- `--batch-all-objects`
- `--buffer`
- `--unordered`
- `--follow-symlinks`
- `-Z`
- `-z`

[Руководство cat-file](https://git-scm.com/docs/git-cat-file)

#### `cherry` — ➖ Нет собственного отображения

```text
git cherry [-v] [<upstream> [<head> [<limit>]]]
```

Названия параметров из руководства:

- `-v`

[Руководство cherry](https://git-scm.com/docs/git-cherry)

#### `diff-files` — ➖ Нет собственного отображения

```text
git diff-files [-q] [-0 | -1 | -2 | -3 | -c | --cc] [<common-diff-options>] [<path>…​]
```

Названия параметров из руководства:

- `-p`
- `-u`
- `--patch`
- `-s`
- `--no-patch`
- `-U<n>`
- `--unified=<n>`
- `--output=<file>`
- `--output-indicator-new=<char>`
- `--output-indicator-old=<char>`
- `--output-indicator-context=<char>`
- `--raw`
- `--patch-with-raw`
- `--indent-heuristic`
- `--no-indent-heuristic`
- `--minimal`
- `--patience`
- `--histogram`
- `--anchored=<text>`
- `--diff-algorithm=(patience|minimal|histogram|myers)`
- `--stat[=<width>[,<name-width>[,<count>]]]`
- `--compact-summary`
- `--numstat`
- `--shortstat`
- `-X [<param>,...]`
- `--dirstat[=<param>,...]`
- `--cumulative`
- `--dirstat-by-file[=<param>,...]`
- `--summary`
- `--patch-with-stat`
- `-z`
- `--name-only`
- `--name-status`
- `--submodule[=<format>]`
- `--color[=<when>]`
- `--no-color`
- `--color-moved[=<mode>]`
- `--no-color-moved`
- `--color-moved-ws=<mode>,...`
- `--no-color-moved-ws`
- `--word-diff[=<mode>]`
- `--word-diff-regex=<regex>`
- `--color-words[=<regex>]`
- `--no-renames`
- `--rename-empty`
- `--no-rename-empty`
- `--check`
- `--ws-error-highlight=<kind>`
- `--full-index`
- `--binary`
- `--abbrev[=<n>]`
- `-B[<n>][/<m>]`
- `--break-rewrites[=[<n>][/<m>]]`
- `-M[<n>]`
- `--find-renames[=<n>]`
- `-C[<n>]`
- `--find-copies[=<n>]`
- `--find-copies-harder`
- `-D`
- `--irreversible-delete`
- `-l<num>`
- `--diff-filter=[(A|C|D|M|R|T|U|X|B)...[*]]`
- `-S<string>`
- `-G<regex>`
- `--find-object=<object-id>`
- `--pickaxe-all`
- `--pickaxe-regex`
- `-O<orderfile>`
- `--skip-to=<file>`
- `--rotate-to=<file>`
- `-R`
- `--relative[=<path>]`
- `--no-relative`
- `-a`
- `--text`
- `--ignore-cr-at-eol`
- `--ignore-space-at-eol`
- `-b`
- `--ignore-space-change`
- `-w`
- `--ignore-all-space`
- `--ignore-blank-lines`
- `-I<regex>`
- `--ignore-matching-lines=<regex>`
- `--inter-hunk-context=<number>`
- `-W`
- `--function-context`
- `--exit-code`
- `--quiet`
- `--ext-diff`
- `--no-ext-diff`
- `--textconv`
- `--no-textconv`
- `--ignore-submodules[=(none|untracked|dirty|all)]`
- `--src-prefix=<prefix>`
- `--dst-prefix=<prefix>`
- `--no-prefix`
- `--default-prefix`
- `--line-prefix=<prefix>`
- `--ita-invisible-in-index`
- `--max-depth=<depth>`
- `-1 --base`
- `-2 --ours`
- `-3 --theirs`
- `-0`
- `-c`
- `--cc`
- `-q`

[Руководство diff-files](https://git-scm.com/docs/git-diff-files)

#### `diff-index` — ➖ Нет собственного отображения

```text
git diff-index [-m] [--cached] [--merge-base] [<common-diff-options>] <tree-ish> [<path>…​]
```

Названия параметров из руководства:

- `-p`
- `-u`
- `--patch`
- `-s`
- `--no-patch`
- `-U<n>`
- `--unified=<n>`
- `--output=<file>`
- `--output-indicator-new=<char>`
- `--output-indicator-old=<char>`
- `--output-indicator-context=<char>`
- `--raw`
- `--patch-with-raw`
- `--indent-heuristic`
- `--no-indent-heuristic`
- `--minimal`
- `--patience`
- `--histogram`
- `--anchored=<text>`
- `--diff-algorithm=(patience|minimal|histogram|myers)`
- `--stat[=<width>[,<name-width>[,<count>]]]`
- `--compact-summary`
- `--numstat`
- `--shortstat`
- `-X [<param>,...]`
- `--dirstat[=<param>,...]`
- `--cumulative`
- `--dirstat-by-file[=<param>,...]`
- `--summary`
- `--patch-with-stat`
- `-z`
- `--name-only`
- `--name-status`
- `--submodule[=<format>]`
- `--color[=<when>]`
- `--no-color`
- `--color-moved[=<mode>]`
- `--no-color-moved`
- `--color-moved-ws=<mode>,...`
- `--no-color-moved-ws`
- `--word-diff[=<mode>]`
- `--word-diff-regex=<regex>`
- `--color-words[=<regex>]`
- `--no-renames`
- `--rename-empty`
- `--no-rename-empty`
- `--check`
- `--ws-error-highlight=<kind>`
- `--full-index`
- `--binary`
- `--abbrev[=<n>]`
- `-B[<n>][/<m>]`
- `--break-rewrites[=[<n>][/<m>]]`
- `-M[<n>]`
- `--find-renames[=<n>]`
- `-C[<n>]`
- `--find-copies[=<n>]`
- `--find-copies-harder`
- `-D`
- `--irreversible-delete`
- `-l<num>`
- `--diff-filter=[(A|C|D|M|R|T|U|X|B)...[*]]`
- `-S<string>`
- `-G<regex>`
- `--find-object=<object-id>`
- `--pickaxe-all`
- `--pickaxe-regex`
- `-O<orderfile>`
- `--skip-to=<file>`
- `--rotate-to=<file>`
- `-R`
- `--relative[=<path>]`
- `--no-relative`
- `-a`
- `--text`
- `--ignore-cr-at-eol`
- `--ignore-space-at-eol`
- `-b`
- `--ignore-space-change`
- `-w`
- `--ignore-all-space`
- `--ignore-blank-lines`
- `-I<regex>`
- `--ignore-matching-lines=<regex>`
- `--inter-hunk-context=<number>`
- `-W`
- `--function-context`
- `--exit-code`
- `--quiet`
- `--ext-diff`
- `--no-ext-diff`
- `--textconv`
- `--no-textconv`
- `--ignore-submodules[=(none|untracked|dirty|all)]`
- `--src-prefix=<prefix>`
- `--dst-prefix=<prefix>`
- `--no-prefix`
- `--default-prefix`
- `--line-prefix=<prefix>`
- `--ita-invisible-in-index`
- `--max-depth=<depth>`
- `--cached`
- `--merge-base`
- `-m`

[Руководство diff-index](https://git-scm.com/docs/git-diff-index)

#### `diff-pairs` — ➖ Нет собственного отображения

```text
git diff-pairs -z [<diff-options>]
```

Названия параметров из руководства:

- `-p`
- `-u`
- `--patch`
- `-s`
- `--no-patch`
- `-U<n>`
- `--unified=<n>`
- `--output=<file>`
- `--output-indicator-new=<char>`
- `--output-indicator-old=<char>`
- `--output-indicator-context=<char>`
- `--raw`
- `--patch-with-raw`
- `--indent-heuristic`
- `--no-indent-heuristic`
- `--minimal`
- `--patience`
- `--histogram`
- `--anchored=<text>`
- `--diff-algorithm=(patience|minimal|histogram|myers)`
- `--stat[=<width>[,<name-width>[,<count>]]]`
- `--compact-summary`
- `--numstat`
- `--shortstat`
- `-X [<param>,...]`
- `--dirstat[=<param>,...]`
- `--cumulative`
- `--dirstat-by-file[=<param>,...]`
- `--summary`
- `--patch-with-stat`
- `-z`
- `--name-only`
- `--name-status`
- `--submodule[=<format>]`
- `--color[=<when>]`
- `--no-color`
- `--color-moved[=<mode>]`
- `--no-color-moved`
- `--color-moved-ws=<mode>,...`
- `--no-color-moved-ws`
- `--word-diff[=<mode>]`
- `--word-diff-regex=<regex>`
- `--color-words[=<regex>]`
- `--no-renames`
- `--rename-empty`
- `--no-rename-empty`
- `--check`
- `--ws-error-highlight=<kind>`
- `--full-index`
- `--binary`
- `--abbrev[=<n>]`
- `-B[<n>][/<m>]`
- `--break-rewrites[=[<n>][/<m>]]`
- `-M[<n>]`
- `--find-renames[=<n>]`
- `-C[<n>]`
- `--find-copies[=<n>]`
- `--find-copies-harder`
- `-D`
- `--irreversible-delete`
- `-l<num>`
- `--diff-filter=[(A|C|D|M|R|T|U|X|B)...[*]]`
- `-S<string>`
- `-G<regex>`
- `--find-object=<object-id>`
- `--pickaxe-all`
- `--pickaxe-regex`
- `-O<orderfile>`
- `--skip-to=<file>`
- `--rotate-to=<file>`
- `-R`
- `--relative[=<path>]`
- `--no-relative`
- `-a`
- `--text`
- `--ignore-cr-at-eol`
- `--ignore-space-at-eol`
- `-b`
- `--ignore-space-change`
- `-w`
- `--ignore-all-space`
- `--ignore-blank-lines`
- `-I<regex>`
- `--ignore-matching-lines=<regex>`
- `--inter-hunk-context=<number>`
- `-W`
- `--function-context`
- `--exit-code`
- `--quiet`
- `--ext-diff`
- `--no-ext-diff`
- `--textconv`
- `--no-textconv`
- `--ignore-submodules[=(none|untracked|dirty|all)]`
- `--src-prefix=<prefix>`
- `--dst-prefix=<prefix>`
- `--no-prefix`
- `--default-prefix`
- `--line-prefix=<prefix>`
- `--ita-invisible-in-index`
- `--max-depth=<depth>`

[Руководство diff-pairs](https://git-scm.com/docs/git-diff-pairs)

#### `diff-tree` — ➖ Нет собственного отображения

```text
git diff-tree [--stdin] [-m] [-s] [-v] [--no-commit-id] [--pretty]
              [-t] [-r] [-c | --cc] [--combined-all-paths] [--root] [--merge-base]
              [<common-diff-options>] <tree-ish> [<tree-ish>] [<path>…​]
```

Названия параметров из руководства:

- `-p`
- `-u`
- `--patch`
- `-s`
- `--no-patch`
- `-U<n>`
- `--unified=<n>`
- `--output=<file>`
- `--output-indicator-new=<char>`
- `--output-indicator-old=<char>`
- `--output-indicator-context=<char>`
- `--raw`
- `--patch-with-raw`
- `--indent-heuristic`
- `--no-indent-heuristic`
- `--minimal`
- `--patience`
- `--histogram`
- `--anchored=<text>`
- `--diff-algorithm=(patience|minimal|histogram|myers)`
- `--stat[=<width>[,<name-width>[,<count>]]]`
- `--compact-summary`
- `--numstat`
- `--shortstat`
- `-X [<param>,...]`
- `--dirstat[=<param>,...]`
- `--cumulative`
- `--dirstat-by-file[=<param>,...]`
- `--summary`
- `--patch-with-stat`
- `-z`
- `--name-only`
- `--name-status`
- `--submodule[=<format>]`
- `--color[=<when>]`
- `--no-color`
- `--color-moved[=<mode>]`
- `--no-color-moved`
- `--color-moved-ws=<mode>,...`
- `--no-color-moved-ws`
- `--word-diff[=<mode>]`
- `--word-diff-regex=<regex>`
- `--color-words[=<regex>]`
- `--no-renames`
- `--rename-empty`
- `--no-rename-empty`
- `--check`
- `--ws-error-highlight=<kind>`
- `--full-index`
- `--binary`
- `--abbrev[=<n>]`
- `-B[<n>][/<m>]`
- `--break-rewrites[=[<n>][/<m>]]`
- `-M[<n>]`
- `--find-renames[=<n>]`
- `-C[<n>]`
- `--find-copies[=<n>]`
- `--find-copies-harder`
- `-D`
- `--irreversible-delete`
- `-l<num>`
- `--diff-filter=[(A|C|D|M|R|T|U|X|B)...[*]]`
- `-S<string>`
- `-G<regex>`
- `--find-object=<object-id>`
- `--pickaxe-all`
- `--pickaxe-regex`
- `-O<orderfile>`
- `--skip-to=<file>`
- `--rotate-to=<file>`
- `-R`
- `--relative[=<path>]`
- `--no-relative`
- `-a`
- `--text`
- `--ignore-cr-at-eol`
- `--ignore-space-at-eol`
- `-b`
- `--ignore-space-change`
- `-w`
- `--ignore-all-space`
- `--ignore-blank-lines`
- `-I<regex>`
- `--ignore-matching-lines=<regex>`
- `--inter-hunk-context=<number>`
- `-W`
- `--function-context`
- `--exit-code`
- `--quiet`
- `--ext-diff`
- `--no-ext-diff`
- `--textconv`
- `--no-textconv`
- `--ignore-submodules[=(none|untracked|dirty|all)]`
- `--src-prefix=<prefix>`
- `--dst-prefix=<prefix>`
- `--no-prefix`
- `--default-prefix`
- `--line-prefix=<prefix>`
- `--ita-invisible-in-index`
- `--max-depth=<depth>`
- `-r`
- `-t`
- `--root`
- `--merge-base`
- `--stdin`
- `-m`
- `-v`
- `--pretty[=<format>]`
- `--format=<format>`
- `--abbrev-commit`
- `--no-abbrev-commit`
- `--oneline`
- `--encoding=<encoding>`
- `--expand-tabs=<n>`
- `--expand-tabs`
- `--no-expand-tabs`
- `--notes[=<ref>]`
- `--no-notes`
- `--show-notes-by-default`
- `--show-notes[=<ref>]`
- `--standard-notes`
- `--no-standard-notes`
- `--show-signature`
- `--no-commit-id`
- `-c`
- `--cc`
- `--combined-all-paths`
- `--always`

[Руководство diff-tree](https://git-scm.com/docs/git-diff-tree)

#### `for-each-ref` — ➖ Нет собственного отображения

```text
git for-each-ref [--count=<count>] [--shell|--perl|--python|--tcl]
		   [(--sort=<key>)…​] [--format=<format>]
		   [--include-root-refs] [--points-at=<object>]
		   [--merged[=<object>]] [--no-merged[=<object>]]
		   [--contains[=<object>]] [--no-contains[=<object>]]
		   [(--exclude=<pattern>)…​] [--start-after=<marker>]
		   [ --stdin | (<pattern>...)]
```

Названия параметров из руководства:

- `--stdin`
- `--count=<count>`
- `--sort=<key>`
- `--format[=<format>]`
- `--color[=<when>]`
- `--shell`
- `--perl`
- `--python`
- `--tcl`
- `--points-at=<object>`
- `--merged[=<object>]`
- `--no-merged[=<object>]`
- `--contains[=<object>]`
- `--no-contains[=<object>]`
- `--ignore-case`
- `--omit-empty`
- `--exclude=<excluded-pattern>`
- `--include-root-refs`
- `--start-after=<marker>`

[Руководство for-each-ref](https://git-scm.com/docs/git-for-each-ref)

#### `for-each-repo` — ⚪ Отдельно не проверено

```text
git for-each-repo --config=<config> [--] <arguments>
```

Названия параметров из руководства:

- `--config=<config>`
- `--keep-going`

[Руководство for-each-repo](https://git-scm.com/docs/git-for-each-repo)

#### `format-rev` — ➖ Нет собственного отображения

```text
(EXPERIMENTAL!) git format-rev --stdin-mode=<mode> --format=<pretty> [--[no-]notes=<ref>] [-z] [--[no-]null-output] [--[no-]null-input]
```

Названия параметров из руководства:

- `--stdin-mode=<mode>`
- `--format=<pretty>`
- `--notes=<ref>`
- `--no-notes`
- `-z`
- `--null`
- `--null-output`
- `--no-null-output`
- `--null-input`
- `--no-null-input`

[Руководство format-rev](https://git-scm.com/docs/git-format-rev)

#### `get-tar-commit-id` — ➖ Нет собственного отображения

```text
git get-tar-commit-id
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство get-tar-commit-id](https://git-scm.com/docs/git-get-tar-commit-id)

#### `last-modified` — ➖ Нет собственного отображения

```text
git last-modified [--recursive] [--show-trees] [--max-depth=<depth>] [-z]
		  [<revision-range>] [[--] <pathspec>…​]
```

Названия параметров из руководства:

- `-r`
- `--recursive`
- `-t`
- `--show-trees`
- `--max-depth=<depth>`
- `-z`

[Руководство last-modified](https://git-scm.com/docs/git-last-modified)

#### `ls-files` — ➖ Нет собственного отображения

```text
git ls-files [-z] [-t] [-v] [-f]
                [-c|--cached] [-d|--deleted] [-o|--others] [-i|--ignored]
                [-s|--stage] [-u|--unmerged] [-k|--killed] [-m|--modified]
                [--resolve-undo]
                [--directory [--no-empty-directory]] [--eol]
                [--deduplicate]
                [-x <pattern>|--exclude=<pattern>]
                [-X <file>|--exclude-from=<file>]
                [--exclude-per-directory=<file>]
                [--exclude-standard]
                [--error-unmatch] [--with-tree=<tree-ish>]
                [--full-name] [--recurse-submodules]
                [--abbrev[=<n>]] [--format=<format>] [--] [<file>…​]
```

Названия параметров из руководства:

- `-c`
- `--cached`
- `-d`
- `--deleted`
- `-m`
- `--modified`
- `-o`
- `--others`
- `-i`
- `--ignored`
- `-s`
- `--stage`
- `--directory`
- `--no-empty-directory`
- `-u`
- `--unmerged`
- `-k`
- `--killed`
- `--resolve-undo`
- `-z`
- `--deduplicate`
- `-x <pattern>`
- `--exclude=<pattern>`
- `-X <file>`
- `--exclude-from=<file>`
- `--exclude-per-directory=<file>`
- `--exclude-standard`
- `--error-unmatch`
- `--with-tree=<tree-ish>`
- `-t`
- `-v`
- `-f`
- `--full-name`
- `--recurse-submodules`
- `--abbrev[=<n>]`
- `--debug`
- `--eol`
- `--sparse`
- `--format=<format>`
- `--`

[Руководство ls-files](https://git-scm.com/docs/git-ls-files)

#### `ls-remote` — ➖ Нет собственного отображения

```text
git ls-remote [--branches] [--tags] [--refs] [--upload-pack=<exec>]
              [-q | --quiet] [--exit-code] [--get-url] [--sort=<key>]
              [--symref] [<repository> [<patterns>…​]]
```

Названия параметров из руководства:

- `-b`
- `--branches`
- `-t`
- `--tags`
- `--refs`
- `-q`
- `--quiet`
- `--upload-pack=<exec>`
- `--exit-code`
- `--get-url`
- `--symref`
- `--sort=<key>`
- `-o <option>`
- `--server-option=<option>`

[Руководство ls-remote](https://git-scm.com/docs/git-ls-remote)

#### `ls-tree` — ➖ Нет собственного отображения

```text
git ls-tree [-d] [-r] [-t] [-l] [-z]
            [--name-only] [--name-status] [--object-only] [--full-name] [--full-tree] [--abbrev[=<n>]] [--format=<format>]
            <tree-ish> [<path>…​]
```

Названия параметров из руководства:

- `-d`
- `-r`
- `-t`
- `-l`
- `--long`
- `-z`
- `--name-only`
- `--name-status`
- `--object-only`
- `--abbrev[=<n>]`
- `--full-name`
- `--full-tree`
- `--format=<format>`

[Руководство ls-tree](https://git-scm.com/docs/git-ls-tree)

#### `merge-base` — ➖ Нет собственного отображения

```text
git merge-base [-a | --all] <commit> <commit>…​
git merge-base [-a | --all] --octopus <commit>…​
git merge-base --is-ancestor <commit> <commit>
git merge-base --independent <commit>…​
git merge-base --fork-point <ref> [<commit>]
```

Названия параметров из руководства:

- `--octopus`
- `--independent`
- `--is-ancestor`
- `--fork-point`
- `-a`
- `--all`

[Руководство merge-base](https://git-scm.com/docs/git-merge-base)

#### `name-rev` — ➖ Нет собственного отображения

```text
git name-rev [--tags] [--refs=<pattern>]
               ( --all | --annotate-stdin | <commit-ish>…​ )
```

Названия параметров из руководства:

- `--tags`
- `--refs=<pattern>`
- `--exclude=<pattern>`
- `--all`
- `--annotate-stdin`
- `--name-only`
- `--no-undefined`
- `--always`

[Руководство name-rev](https://git-scm.com/docs/git-name-rev)

#### `pack-redundant` — ⚪ Отдельно не проверено

```text
git pack-redundant [--verbose] [--alt-odb] (--all | <pack-filename>…​)
```

Названия параметров из руководства:

- `--all`
- `--alt-odb`
- `--verbose`

[Руководство pack-redundant](https://git-scm.com/docs/git-pack-redundant)

#### `repo` — ➖ Нет собственного отображения

```text
git repo info [--format=(lines|nul) | -z] [--all | <key>…​]
git repo info --keys [--format=(lines|nul) | -z]
git repo structure [--format=(table|lines|nul) | -z]
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство repo](https://git-scm.com/docs/git-repo)

#### `rev-list` — ➖ Нет собственного отображения

```text
git rev-list [<options>] <commit>…​ [--] [<path>…​]
```

Названия параметров из руководства:

- `-<number>`
- `-n <number>`
- `--max-count=<number>`
- `--max-count-oldest=<number>`
- `--skip=<number>`
- `--since=<date>`
- `--after=<date>`
- `--since-as-filter=<date>`
- `--until=<date>`
- `--before=<date>`
- `--max-age=<timestamp>`
- `--min-age=<timestamp>`
- `--author=<pattern>`
- `--committer=<pattern>`
- `--grep-reflog=<pattern>`
- `--grep=<pattern>`
- `--all-match`
- `--invert-grep`
- `-i`
- `--regexp-ignore-case`
- `--basic-regexp`
- `-E`
- `--extended-regexp`
- `-F`
- `--fixed-strings`
- `-P`
- `--perl-regexp`
- `--remove-empty`
- `--merges`
- `--no-merges`
- `--min-parents=<number>`
- `--max-parents=<number>`
- `--no-min-parents`
- `--no-max-parents`
- `--first-parent`
- `--exclude-first-parent-only`
- `--maximal-only`
- `--not`
- `--all`
- `--branches[=<pattern>]`
- `--tags[=<pattern>]`
- `--remotes[=<pattern>]`
- `--glob=<glob-pattern>`
- `--exclude=<glob-pattern>`
- `--exclude-hidden=(fetch|receive|uploadpack)`
- `--reflog`
- `--alternate-refs`
- `--single-worktree`
- `--ignore-missing`
- `--stdin`
- `--quiet`
- `--disk-usage`
- `--disk-usage=human`
- `--cherry-mark`
- `--cherry-pick`
- `--left-only`
- `--right-only`
- `--cherry`
- `-g`
- `--walk-reflogs`
- `--merge`
- `--boundary`
- `--use-bitmap-index`
- `--progress=<header>`
- `-z`
- `--simplify-by-decoration`
- `--show-pulls`
- `--full-history`
- `--dense`
- `--sparse`
- `--simplify-merges`
- `--ancestry-path[=<commit>]`
- `--full-history without parent rewriting`
- `--full-history with parent rewriting`
- `--bisect`
- `--bisect-vars`
- `--bisect-all`
- `--date-order`
- `--author-date-order`
- `--topo-order`
- `--reverse`
- `--objects`
- `--in-commit-order`
- `--objects-edge`
- `--objects-edge-aggressive`
- `--indexed-objects`
- `--unpacked`
- `--object-names`
- `--no-object-names`
- `--filter=<filter-spec>`
- `--no-filter`
- `--filter-provided-objects`
- `--filter-print-omitted`
- `--missing=<missing-action>`
- `--missing-only`
- `--exclude-promisor-objects`
- `--no-walk[=(sorted|unsorted)]`
- `--do-walk`
- `--pretty[=<format>]`
- `--format=<format>`
- `--abbrev-commit`
- `--no-abbrev-commit`
- `--oneline`
- `--encoding=<encoding>`
- `--expand-tabs=<n>`
- `--expand-tabs`
- `--no-expand-tabs`
- `--show-signature`
- `--relative-date`
- `--date=<format>`
- `--header`
- `--no-commit-header`
- `--commit-header`
- `--parents`
- `--children`
- `--timestamp`
- `--left-right`
- `--graph`
- `--show-linear-break[=<barrier>]`
- `--graph-lane-limit=<n>`
- `--no-graph-indent`
- `--graph-indent`
- `--count`

[Руководство rev-list](https://git-scm.com/docs/git-rev-list)

#### `rev-parse` — ➖ Нет собственного отображения

```text
git rev-parse [<options>] <arg>…​
```

Названия параметров из руководства:

- `--parseopt`
- `--sq-quote`
- `--keep-dashdash`
- `--stop-at-non-option`
- `--stuck-long`
- `--revs-only`
- `--no-revs`
- `--flags`
- `--no-flags`
- `--default <arg>`
- `--prefix <arg>`
- `--verify`
- `-q`
- `--quiet`
- `--sq`
- `--short[=<length>]`
- `--not`
- `--abbrev-ref[=(strict|loose)]`
- `--symbolic`
- `--symbolic-full-name`
- `--output-object-format=(sha1|sha256|storage)`
- `--all`
- `--branches[=<pattern>]`
- `--tags[=<pattern>]`
- `--remotes[=<pattern>]`
- `--glob=<pattern>`
- `--exclude=<glob-pattern>`
- `--exclude-hidden=(fetch|receive|uploadpack)`
- `--disambiguate=<prefix>`
- `--local-env-vars`
- `--path-format=(absolute|relative)`
- `--git-dir`
- `--git-common-dir`
- `--resolve-git-dir <path>`
- `--git-path <path>`
- `--show-toplevel`
- `--show-superproject-working-tree`
- `--shared-index-path`
- `--absolute-git-dir`
- `--is-inside-git-dir`
- `--is-inside-work-tree`
- `--is-bare-repository`
- `--is-shallow-repository`
- `--show-cdup`
- `--show-prefix`
- `--show-object-format[=(storage|input|output|compat)]`
- `--show-ref-format`
- `--since=<datestring>`
- `--after=<datestring>`
- `--until=<datestring>`
- `--before=<datestring>`

[Руководство rev-parse](https://git-scm.com/docs/git-rev-parse)

#### `show-index` — ➖ Нет собственного отображения

```text
git show-index [--object-format=<hash-algorithm>] < <pack-idx-file>
```

Названия параметров из руководства:

- `--object-format=<hash-algorithm>`

[Руководство show-index](https://git-scm.com/docs/git-show-index)

#### `show-ref` — ➖ Нет собственного отображения

```text
git show-ref [--head] [-d | --dereference]
             [-s | --hash[=<n>]] [--abbrev[=<n>]] [--branches] [--tags]
             [--] [<pattern>…​]
git show-ref --verify [-q | --quiet] [-d | --dereference]
             [-s | --hash[=<n>]] [--abbrev[=<n>]]
             [--] [<ref>…​]
git show-ref --exclude-existing[=<pattern>]
git show-ref --exists <ref>
```

Названия параметров из руководства:

- `--head`
- `--branches`
- `--tags`
- `-d`
- `--dereference`
- `-s`
- `--hash[=<n>]`
- `--verify`
- `--exists`
- `--abbrev[=<n>]`
- `-q`
- `--quiet`
- `--exclude-existing[=<pattern>]`

[Руководство show-ref](https://git-scm.com/docs/git-show-ref)

#### `unpack-file` — ⚪ Отдельно не проверено

```text
git unpack-file <blob>
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство unpack-file](https://git-scm.com/docs/git-unpack-file)

#### `var` — ➖ Нет собственного отображения

```text
git var (-l | <variable>)
```

Названия параметров из руководства:

- `-l`

[Руководство var](https://git-scm.com/docs/git-var)

#### `verify-pack` — ⚪ Отдельно не проверено

```text
git verify-pack [-v | --verbose] [-s | --stat-only] [--] <pack>.idx…​
```

Названия параметров из руководства:

- `-v`
- `--verbose`
- `-s`
- `--stat-only`
- `--`

[Руководство verify-pack](https://git-scm.com/docs/git-verify-pack)

### Низкоуровневая синхронизация

#### `daemon` — ⚪ Отдельно не проверено

```text
git daemon [--verbose] [--syslog] [--export-all]
	   [--timeout=<n>] [--init-timeout=<n>] [--max-connections=<n>]
	   [--strict-paths] [--base-path=<path>] [--base-path-relaxed]
	   [--user-path | --user-path=<path>]
	   [--interpolated-path=<pathtemplate>]
	   [--reuseaddr] [--detach] [--pid-file=<file>]
	   [--enable=<service>] [--disable=<service>]
	   [--allow-override=<service>] [--forbid-override=<service>]
	   [--access-hook=<path>] [--[no-]informative-errors]
	   [--inetd |
	     [--listen=<host-or-ipaddr>] [--port=<n>]
	     [--user=<user> [--group=<group>]]]
	   [--log-destination=(stderr|syslog|none)]
	   [<directory>…​]
```

Названия параметров из руководства:

- `--strict-paths`
- `--base-path=<path>`
- `--base-path-relaxed`
- `--interpolated-path=<pathtemplate>`
- `--export-all`
- `--inetd`
- `--listen=<host-or-ipaddr>`
- `--port=<n>`
- `--init-timeout=<n>`
- `--timeout=<n>`
- `--max-connections=<n>`
- `--syslog`
- `--log-destination=<destination>`
- `--user-path`
- `--user-path=<path>`
- `--verbose`
- `--reuseaddr`
- `--detach`
- `--pid-file=<file>`
- `--user=<user>`
- `--group=<group>`
- `--enable=<service>`
- `--disable=<service>`
- `--allow-override=<service>`
- `--forbid-override=<service>`
- `--informative-errors`
- `--no-informative-errors`
- `--access-hook=<path>`

[Руководство daemon](https://git-scm.com/docs/git-daemon)

#### `fetch-pack` — ⚪ Отдельно не проверено

```text
git fetch-pack [--all] [--quiet|-q] [--keep|-k] [--thin] [--include-tag]
        [--upload-pack=<git-upload-pack>]
        [--depth=<n>] [--no-progress]
        [-v] <repository> [<refs>…​]
```

Названия параметров из руководства:

- `--all`
- `--stdin`
- `-q`
- `--quiet`
- `-k`
- `--keep`
- `--thin`
- `--include-tag`
- `--upload-pack=<git-upload-pack>`
- `--exec=<git-upload-pack>`
- `--depth=<n>`
- `--shallow-since=<date>`
- `--shallow-exclude=<ref>`
- `--deepen-relative`
- `--refetch`
- `--no-progress`
- `--check-self-contained-and-connected`
- `-v`

[Руководство fetch-pack](https://git-scm.com/docs/git-fetch-pack)

#### `http-backend` — ⚪ Отдельно не проверено

```text
git http-backend
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство http-backend](https://git-scm.com/docs/git-http-backend)

#### `send-pack` — ⚪ Отдельно не проверено

```text
git send-pack [--mirror] [--dry-run] [--force]
                [--receive-pack=<git-receive-pack>]
                [--verbose] [--thin] [--atomic]
                [--[no-]signed | --signed=(true|false|if-asked)]
                [<host>:]<directory> (--all | <ref>…​)
```

Названия параметров из руководства:

- `--receive-pack=<git-receive-pack>`
- `--exec=<git-receive-pack>`
- `--all`
- `--stdin`
- `--dry-run`
- `--force`
- `--verbose`
- `--thin`
- `--atomic`
- `--signed`
- `--no-signed`
- `--signed=(true|false|if-asked)`
- `--push-option=<string>`

[Руководство send-pack](https://git-scm.com/docs/git-send-pack)

#### `update-server-info` — ⚪ Отдельно не проверено

```text
git update-server-info [-f | --force]
```

Названия параметров из руководства:

- `-f`
- `--force`

[Руководство update-server-info](https://git-scm.com/docs/git-update-server-info)

### Внутренние вспомогательные команды

#### `check-attr` — ➖ Нет собственного отображения

```text
git check-attr [--source <tree-ish>] [-a | --all | <attr>…​] [--] <pathname>…​
git check-attr --stdin [-z] [--source <tree-ish>] [-a | --all | <attr>…​]
```

Названия параметров из руководства:

- `-a`
- `--all`
- `--cached`
- `--stdin`
- `-z`
- `--source=<tree-ish>`
- `--`

[Руководство check-attr](https://git-scm.com/docs/git-check-attr)

#### `check-ignore` — ➖ Нет собственного отображения

```text
git check-ignore [<options>] <pathname>…​
git check-ignore [<options>] --stdin
```

Названия параметров из руководства:

- `-q`
- `--quiet`
- `-v`
- `--verbose`
- `--stdin`
- `-z`
- `-n`
- `--non-matching`
- `--no-index`

[Руководство check-ignore](https://git-scm.com/docs/git-check-ignore)

#### `check-mailmap` — ➖ Нет собственного отображения

```text
git check-mailmap [<options>] <contact>…​
```

Названия параметров из руководства:

- `--stdin`
- `--mailmap-file=<file>`
- `--mailmap-blob=<blob>`

[Руководство check-mailmap](https://git-scm.com/docs/git-check-mailmap)

#### `check-ref-format` — ➖ Нет собственного отображения

```text
git check-ref-format [--normalize]
       [--[no-]allow-onelevel] [--refspec-pattern]
       <refname>
git check-ref-format --branch <branchname-shorthand>
```

Названия параметров из руководства:

- `--allow-onelevel`
- `--no-allow-onelevel`
- `--refspec-pattern`
- `--normalize`

[Руководство check-ref-format](https://git-scm.com/docs/git-check-ref-format)

#### `column` — ⚪ Отдельно не проверено

```text
git column [--command=<name>] [--[raw-]mode=<mode>] [--width=<width>]
             [--indent=<string>] [--nl=<string>] [--padding=<n>]
```

Названия параметров из руководства:

- `--command=<name>`
- `--mode=<mode>`
- `--raw-mode=<n>`
- `--width=<width>`
- `--indent=<string>`
- `--nl=<string>`
- `--padding=<N>`

[Руководство column](https://git-scm.com/docs/git-column)

#### `credential` — ⚪ Отдельно не проверено

```text
'git credential' (fill|approve|reject|capability)
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство credential](https://git-scm.com/docs/git-credential)

#### `credential-cache` — ⚪ Отдельно не проверено

```text
git config credential.helper 'cache [<options>]'
```

Названия параметров из руководства:

- `--timeout <seconds>`
- `--socket <path>`

[Руководство credential-cache](https://git-scm.com/docs/git-credential-cache)

#### `credential-store` — ⚪ Отдельно не проверено

```text
git config credential.helper 'store [<options>]'
```

Названия параметров из руководства:

- `--file=<path>`

[Руководство credential-store](https://git-scm.com/docs/git-credential-store)

#### `fmt-merge-msg` — ⚪ Отдельно не проверено

```text
git fmt-merge-msg [-m <message>] [--into-name <branch>] [--log[=<n>] | --no-log]
git fmt-merge-msg [-m <message>] [--log[=<n>] | --no-log] -F <file>
```

Названия параметров из руководства:

- `--log[=<n>]`
- `--no-log`
- `--summary`
- `--no-summary`
- `-m <message>`
- `--message <message>`
- `--into-name <branch>`
- `-F <file>`
- `--file <file>`

[Руководство fmt-merge-msg](https://git-scm.com/docs/git-fmt-merge-msg)

#### `hook` — ⚪ Отдельно не проверено

```text
git hook run [--allow-unknown-hook-name] [--ignore-missing] [--to-stdin=<path>] [(-j|--jobs) <n>]
        <hook-name> [-- <hook-args>]
git hook list [--allow-unknown-hook-name] [-z] [--show-scope] <hook-name>
```

Названия параметров из руководства:

- `--allow-unknown-hook-name`
- `--to-stdin`
- `--ignore-missing`
- `-z`
- `--show-scope`
- `-j`
- `--jobs`

[Руководство hook](https://git-scm.com/docs/git-hook)

#### `interpret-trailers` — ⚪ Отдельно не проверено

```text
git interpret-trailers [--in-place] [--trim-empty]
			[(--trailer (<key>|<key-alias>)[(=|:)<value>])…​]
			[--parse] [<file>…​]
```

Названия параметров из руководства:

- `--in-place`
- `--no-in-place`
- `--trim-empty`
- `--no-trim-empty`
- `--trailer=<key>[(=|:)<value>]`
- `--no-trailer`
- `--where=<placement>`
- `--no-where`
- `--if-exists=<action>`
- `--no-if-exists`
- `--if-missing=<action>`
- `--no-if-missing`
- `--only-trailers`
- `--no-only-trailers`
- `--only-input`
- `--no-only-input`
- `--unfold`
- `--no-unfold`
- `--parse`
- `--divider`
- `--no-divider`

[Руководство interpret-trailers](https://git-scm.com/docs/git-interpret-trailers)

#### `mailinfo` — ⚪ Отдельно не проверено

```text
git mailinfo [-k|-b] [-u | --encoding=<encoding> | -n]
               [--[no-]scissors] [--quoted-cr=<action>]
               <msg> <patch>
```

Названия параметров из руководства:

- `-k`
- `-b`
- `-u`
- `--encoding=<encoding>`
- `-n`
- `-m`
- `--message-id`
- `--scissors`
- `--no-scissors`
- `--quoted-cr=<action>`

[Руководство mailinfo](https://git-scm.com/docs/git-mailinfo)

#### `mailsplit` — ⚪ Отдельно не проверено

```text
git mailsplit [-b] [-f<nn>] [-d<prec>] [--keep-cr] [--mboxrd]
                -o<directory> [--] [(<mbox>|<Maildir>)…​]
```

Названия параметров из руководства:

- `-o<directory>`
- `-b`
- `-d<prec>`
- `-f<nn>`
- `--keep-cr`
- `--mboxrd`

[Руководство mailsplit](https://git-scm.com/docs/git-mailsplit)

#### `merge-one-file` — ⚪ Отдельно не проверено

```text
git merge-one-file
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство merge-one-file](https://git-scm.com/docs/git-merge-one-file)

#### `patch-id` — ➖ Нет собственного отображения

```text
git patch-id [--stable | --unstable | --verbatim]
```

Названия параметров из руководства:

- `--verbatim`
- `--stable`
- `--unstable`

[Руководство patch-id](https://git-scm.com/docs/git-patch-id)

#### `sh-i18n` — ⚪ Отдельно не проверено

```text
. "$(git --exec-path)/git-sh-i18n"
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство sh-i18n](https://git-scm.com/docs/git-sh-i18n)

#### `sh-setup` — ⚪ Отдельно не проверено

```text
. "$(git --exec-path)/git-sh-setup"
```

Отдельные заголовки параметров не извлечены; это не означает отсутствие опций или подкоманд.

[Руководство sh-setup](https://git-scm.com/docs/git-sh-setup)

#### `stripspace` — ⚪ Отдельно не проверено

```text
git stripspace [-s | --strip-comments]
git stripspace [-c | --comment-lines]
```

Названия параметров из руководства:

- `-s`
- `--strip-comments`
- `-c`
- `--comment-lines`

[Руководство stripspace](https://git-scm.com/docs/git-stripspace)

#### `url-parse` — ⚪ Отдельно не проверено

```text
git url-parse [-c <component>] [--] <url>…​
```

Названия параметров из руководства:

- `-c <component>`
- `--component <component>`

[Руководство url-parse](https://git-scm.com/docs/git-url-parse)

## Общие параметры Git

```text
git [-v | --version] [-h | --help] [-C <path>] [-c <name>=<value>]
    [--exec-path[=<path>]] [--html-path] [--man-path] [--info-path]
    [-p | --paginate | -P | --no-pager] [--no-replace-objects] [--no-lazy-fetch]
    [--no-optional-locks] [--no-advice] [--bare] [--git-dir=<path>]
    [--work-tree=<path>] [--namespace=<name>] [--config-env=<name>=<envvar>]
    <command> [<args>]
```

Наличие общего флага не означает отдельной проверки DevLab. Особенно требуют проверки `-C`, `--git-dir`, `--work-tree`, `--namespace`, `--bare` и `-c`: выбранная CLI папка и чтение её репозитория могут отличаться от репозитория, на который направлена команда.

Источники: локальные руководства установленного Git; [официальный справочник Git](https://git-scm.com/docs/git). Дата аудита и статусы относятся к текущим исходникам DevLab, а не ко всем будущим изменениям.
