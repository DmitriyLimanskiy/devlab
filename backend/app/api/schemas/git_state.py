from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# Git может использовать SHA-1 или SHA-256; сокращённые хеши не принимаются.
ObjectId = Annotated[str, StringConstraints(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")]
NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
FileStatus = Literal[" ", "M", "A", "D", "R", "C", "U", "?", "!", "T", "X"]
Reference = Annotated[
    str,
    StringConstraints(
        pattern=r"^refs/(?:heads|tags)/[^\s]+ (?:[0-9a-f]{40}|[0-9a-f]{64})$"
    ),
]
Operation = Literal[
    "MERGE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "rebase-merge",
    "rebase-apply",
    "BISECT_LOG",
]


class StateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CommitState(StateModel):
    id: ObjectId
    parents: list[ObjectId]


class FileState(StateModel):
    """Два столбца porcelain: индекс и рабочее дерево; пробел значим."""

    path: NonEmptyString
    index: FileStatus
    worktree: FileStatus
    conflict: bool
    original_path: NonEmptyString | None = None

    @model_validator(mode="after")
    def check_status(self):
        pair = self.index + self.worktree
        if self.conflict != (pair in {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}):
            raise ValueError("conflict должен соответствовать статусу файла")
        if ("R" in pair or "C" in pair) and self.original_path is None:
            raise ValueError("Для переименования/копирования нужен original_path")
        return self


class RepositoryState(StateModel):
    kind: Literal["repository"]
    path: NonEmptyString
    head: ObjectId | None
    branch: NonEmptyString | None
    head_kind: Literal["unborn", "branch", "detached"]
    files: list[FileState]
    # Формат CLI: "refs/heads/main <полный хеш>" или "refs/tags/v1 <хеш>".
    # Хеш annotated tag может указывать на объект тега, а не на коммит.
    refs: list[Reference]
    commits: list[CommitState]
    history_limit: int = Field(gt=0, le=200)
    operations: list[Operation]

    @model_validator(mode="after")
    def check_head_and_history(self):
        if self.head_kind == "unborn" and (
            self.head is not None or self.branch is None
        ):
            raise ValueError("До первого коммита нужны branch и пустой head")
        if self.head_kind == "branch" and (self.head is None or self.branch is None):
            raise ValueError("Для HEAD на ветке нужны head и branch")
        if self.head_kind == "detached" and (
            self.head is None or self.branch is not None
        ):
            raise ValueError("Для detached HEAD нужен head без branch")
        if len(self.commits) > self.history_limit:
            raise ValueError("Число коммитов превышает history_limit")
        # Родители могут находиться вне ограниченной истории.
        return self


class NoRepositoryState(StateModel):
    kind: Literal["no_repository"]
    path: NonEmptyString


class UnavailableState(StateModel):
    kind: Literal["unavailable"]
    path: NonEmptyString


GitState = Annotated[
    RepositoryState | NoRepositoryState | UnavailableState,
    Field(discriminator="kind"),
]
