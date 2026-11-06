import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from app.db.models.practice.practice import PracticeSnapshot
from app.db.models.practice.repository import (
    GraphEvent,
    RepositoryCommit,
    SnapshotReceipt,
)
from fastapi import HTTPException
from sqlalchemy import select


def state_digest(schema_version, state):
    canonical = json.dumps([schema_version, state], sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def refs_by_name(state):
    return dict(ref.rsplit(" ", 1) for ref in state.get("refs", []))


async def store_state(db, snapshot):
    state = snapshot.state.model_dump(mode="json")
    digest = state_digest(snapshot.schema_version, state)
    if state["kind"] == "repository":
        state = {**state, "files": []}
    receipt = await db.scalar(
        select(SnapshotReceipt).where(
            SnapshotReceipt.session_id == snapshot.session_id,
            SnapshotReceipt.generation == snapshot.generation,
            SnapshotReceipt.version == snapshot.version,
        )
    )
    if receipt is not None:
        if receipt.digest != digest:
            raise HTTPException(409, "Эта версия уже сохранена с другим содержимым")
        return receipt, False
    current = await db.scalar(
        select(PracticeSnapshot).where(
            PracticeSnapshot.session_id == snapshot.session_id
        )
    )
    if current is not None and (snapshot.generation, snapshot.version) <= (
        current.generation,
        current.version,
    ):
        raise HTTPException(409, "Версия снимка устарела")
    old = current.state if current else {}
    same_repository = (
        old.get("path") == state["path"] and old.get("kind") == state["kind"]
    )
    repository_id = current.repository_id if current and same_repository else uuid4()
    old_refs = refs_by_name(old) if same_repository else {}
    new_refs = refs_by_name(state)
    old_targets = old.get("ref_commits", {}) if same_repository else {}
    new_targets = state.get("ref_commits", {})
    changes = {
        name: {
            "before": old_refs.get(name),
            "after": new_refs.get(name),
            "commit": new_targets.get(name),
        }
        for name in sorted(old_refs.keys() | new_refs.keys())
        if old_refs.get(name) != new_refs.get(name)
        or old_targets.get(name) != new_targets.get(name)
    }
    commits = state.get("commits", [])
    known = (
        {
            commit.sha: commit
            for commit in (
                await db.scalars(
                    select(RepositoryCommit).where(
                        RepositoryCommit.session_id == snapshot.session_id,
                        RepositoryCommit.repository_id == repository_id,
                        RepositoryCommit.sha.in_([commit["id"] for commit in commits]),
                    )
                )
            ).all()
        }
        if commits
        else {}
    )
    added = [commit for commit in commits if commit["id"] not in known]
    enriched = [
        commit
        for commit in commits
        if commit["id"] in known
        and not known[commit["id"]].parents
        and commit["parents"]
    ]
    if not same_repository or changes or added or enriched:
        context = {
            key: value
            for key, value in state.items()
            if key not in {"commits", "refs", "ref_commits", "files", "operations"}
        }
        event = GraphEvent(
            session_id=snapshot.session_id,
            repository_id=repository_id,
            generation=snapshot.generation,
            version=snapshot.version,
            context=context,
            ref_changes=changes,
        )
        db.add(event)
        await db.flush()
        for commit in added:
            db.add(
                RepositoryCommit(
                    session_id=snapshot.session_id,
                    repository_id=repository_id,
                    sha=commit["id"],
                    parents=commit["parents"],
                    first_event_id=event.id,
                )
            )
        for commit in enriched:
            known[commit["id"]].parents = commit["parents"]
    receipt = SnapshotReceipt(
        session_id=snapshot.session_id,
        generation=snapshot.generation,
        version=snapshot.version,
        digest=digest,
    )
    db.add(receipt)
    await db.flush()
    if current is None:
        current = PracticeSnapshot(session_id=snapshot.session_id)
        db.add(current)
    current.id = receipt.id
    current.repository_id = repository_id
    current.schema_version = snapshot.schema_version
    current.generation = snapshot.generation
    current.version = snapshot.version
    current.state = {key: value for key, value in state.items() if key != "commits"}
    if state["kind"] == "repository":
        current.state = {
            **current.state,
            "commit_ids": [commit["id"] for commit in commits],
        }
    current.received_at = datetime.now(UTC)
    return receipt, True


async def restore_current(db, snapshot):
    if snapshot is None:
        return None
    state = dict(snapshot.state)
    ids = state.pop("commit_ids", [])
    if state["kind"] == "repository":
        commits = {
            commit.sha: commit.parents
            for commit in (
                await db.scalars(
                    select(RepositoryCommit).where(
                        RepositoryCommit.session_id == snapshot.session_id,
                        RepositoryCommit.repository_id == snapshot.repository_id,
                        RepositoryCommit.sha.in_(ids),
                    )
                )
            ).all()
        }
        state["commits"] = [{"id": sha, "parents": commits[sha]} for sha in ids]
    return dict(
        id=snapshot.id,
        session_id=snapshot.session_id,
        schema_version=snapshot.schema_version,
        generation=snapshot.generation,
        version=snapshot.version,
        state=state,
        received_at=snapshot.received_at,
    )
