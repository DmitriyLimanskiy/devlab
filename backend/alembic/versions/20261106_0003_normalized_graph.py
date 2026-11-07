import hashlib
import json
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20261106_0003"
down_revision = "20261106_0002"
branch_labels = None
depends_on = None


def upgrade():
    """Создать нормализованные таблицы и перенести архив снимков"""
    op.create_table(
        "practice_graph_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            UUID(),
            sa.ForeignKey("practice_sessions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("repository_id", UUID(), nullable=False),
        sa.Column("generation", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("context", JSONB(), nullable=False),
        sa.Column("ref_changes", JSONB(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_graph_events_session_id", "practice_graph_events", ["session_id", "id"]
    )
    op.create_table(
        "repository_commits",
        sa.Column(
            "session_id",
            UUID(),
            sa.ForeignKey("practice_sessions.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("repository_id", UUID(), primary_key=True),
        sa.Column("sha", sa.String(64), primary_key=True),
        sa.Column("parents", JSONB(), nullable=False),
        sa.Column(
            "first_event_id",
            sa.Integer(),
            sa.ForeignKey("practice_graph_events.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_repository_commits_first_event_id", "repository_commits", ["first_event_id"]
    )
    op.create_table(
        "practice_snapshot_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            UUID(),
            sa.ForeignKey("practice_sessions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("generation", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "session_id", "generation", "version", name="uq_snapshot_receipt_delivery"
        ),
    )
    op.create_table(
        "practice_current_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            UUID(),
            sa.ForeignKey("practice_sessions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("repository_id", UUID(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("generation", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("state", JSONB(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("session_id", name="uq_practice_current_session"),
        sa.CheckConstraint("schema_version > 0", name="positive_schema_version"),
        sa.CheckConstraint("generation > 0", name="positive_generation"),
        sa.CheckConstraint("version > 0", name="positive_version"),
        sa.CheckConstraint("jsonb_typeof(state) = 'object'", name="state_object"),
    )
    backfill()


def backfill():
    """Перенести архив снимков в текущее состояние и нормализованную историю"""
    # Исходная таблица остаётся архивом для проверки переноса и отката
    bind = op.get_bind()
    metadata = sa.MetaData()
    tables = {
        name: sa.Table(name, metadata, autoload_with=bind)
        for name in (
            "practice_current_states",
            "repository_commits",
            "practice_graph_events",
            "practice_snapshot_receipts",
        )
    }
    sessions = {}
    rows = (
        bind.execute(sa.text("SELECT * FROM practice_snapshots ORDER BY id"))
        .mappings()
        .all()
    )
    for row in rows:
        state, sid = row["state"], row["session_id"]
        previous = sessions.get(sid)
        same = (
            previous
            and previous["state"]["path"] == state["path"]
            and previous["state"]["kind"] == state["kind"]
        )
        repository_id = previous["repository_id"] if same else uuid4()
        old = previous["state"] if same else {}
        old_refs = dict(ref.rsplit(" ", 1) for ref in old.get("refs", []))
        new_refs = dict(ref.rsplit(" ", 1) for ref in state.get("refs", []))
        targets = state.get("ref_commits", {})
        changes = {
            name: {
                "before": old_refs.get(name),
                "after": new_refs.get(name),
                "commit": targets.get(name),
            }
            for name in sorted(old_refs.keys() | new_refs.keys())
            if old_refs.get(name) != new_refs.get(name)
            or old.get("ref_commits", {}).get(name) != targets.get(name)
        }
        known = previous["known"] if same else {}
        added = [
            commit for commit in state.get("commits", []) if commit["id"] not in known
        ]
        enriched = [
            commit
            for commit in state.get("commits", [])
            if commit["id"] in known and not known[commit["id"]] and commit["parents"]
        ]
        if not same or changes or added or enriched:
            context = {
                key: value
                for key, value in state.items()
                if key not in {"commits", "refs", "ref_commits", "files", "operations"}
            }
            event_id = bind.execute(
                tables["practice_graph_events"]
                .insert()
                .values(
                    session_id=sid,
                    repository_id=repository_id,
                    generation=row["generation"],
                    version=row["version"],
                    context=context,
                    ref_changes=changes,
                    received_at=row["received_at"],
                )
                .returning(tables["practice_graph_events"].c.id)
            ).scalar_one()
            for commit in added:
                bind.execute(
                    tables["repository_commits"]
                    .insert()
                    .values(
                        session_id=sid,
                        repository_id=repository_id,
                        sha=commit["id"],
                        parents=commit["parents"],
                        first_event_id=event_id,
                    )
                )
                known[commit["id"]] = commit["parents"]
            for commit in enriched:
                table = tables["repository_commits"]
                bind.execute(
                    table.update()
                    .where(
                        table.c.session_id == sid,
                        table.c.repository_id == repository_id,
                        table.c.sha == commit["id"],
                    )
                    .values(parents=commit["parents"])
                )
                known[commit["id"]] = commit["parents"]
        digest = hashlib.sha256(
            json.dumps(
                [row["schema_version"], state], sort_keys=True, ensure_ascii=True
            ).encode()
        ).hexdigest()
        bind.execute(
            tables["practice_snapshot_receipts"]
            .insert()
            .values(
                id=row["id"],
                session_id=sid,
                generation=row["generation"],
                version=row["version"],
                digest=digest,
            )
        )
        compact = {key: value for key, value in state.items() if key != "commits"}
        if state["kind"] == "repository":
            compact["commit_ids"] = [commit["id"] for commit in state["commits"]]
        values = dict(
            id=row["id"],
            session_id=sid,
            repository_id=repository_id,
            schema_version=row["schema_version"],
            generation=row["generation"],
            version=row["version"],
            state=compact,
            received_at=row["received_at"],
        )
        table = tables["practice_current_states"]
        if previous:
            bind.execute(
                table.update().where(table.c.session_id == sid).values(**values)
            )
        else:
            bind.execute(table.insert().values(**values))
        sessions[sid] = dict(state=state, repository_id=repository_id, known=known)
    for name in ("practice_current_states", "practice_snapshot_receipts"):
        bind.execute(
            sa.text(
                f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), COALESCE((SELECT max(id) FROM {name}), 1), EXISTS(SELECT 1 FROM {name}))"
            )
        )


def downgrade():
    """Запретить автоматический откат нормализованной истории"""
    # Возврат к старой схеме без потери новых состояний и событий
    raise RuntimeError(
        "Автоматический откат нормализации не поддерживается: новые данные нужно предварительно перенести в архив"
    )
