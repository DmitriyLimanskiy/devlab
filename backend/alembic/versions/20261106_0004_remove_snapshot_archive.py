"""Удалить избыточные полные снимки после проверки переноса

Revision ID: 20261106_0004
Revises: 20261106_0003
"""

import hashlib
import json

from alembic import op
import sqlalchemy as sa

revision = "20261106_0004"
down_revision = "20261106_0003"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    rows = (
        bind.execute(sa.text("SELECT * FROM practice_snapshots ORDER BY id"))
        .mappings()
        .all()
    )
    for row in rows:
        digest = hashlib.sha256(
            json.dumps(
                [row["schema_version"], row["state"]], sort_keys=True, ensure_ascii=True
            ).encode()
        ).hexdigest()
        receipt = bind.execute(
            sa.text(
                "SELECT digest FROM practice_snapshot_receipts WHERE session_id=:sid AND generation=:generation AND version=:version"
            ),
            dict(
                sid=row["session_id"],
                generation=row["generation"],
                version=row["version"],
            ),
        ).scalar_one_or_none()
        if receipt != digest:
            raise RuntimeError("Архив не удалён: не все снимки перенесены")
        for commit in row["state"].get("commits", []):
            found = bind.execute(
                sa.text(
                    "SELECT 1 FROM repository_commits WHERE session_id=:sid AND sha=:sha LIMIT 1"
                ),
                dict(sid=row["session_id"], sha=commit["id"]),
            ).scalar_one_or_none()
            if found is None:
                raise RuntimeError("Архив не удалён: не все коммиты перенесены")
    missing = bind.execute(
        sa.text(
            "SELECT 1 FROM practice_snapshots old WHERE NOT EXISTS "
            "(SELECT 1 FROM practice_current_states current WHERE current.session_id=old.session_id "
            "AND (current.generation,current.version)>=(old.generation,old.version)) LIMIT 1"
        )
    ).scalar_one_or_none()
    if missing:
        raise RuntimeError("Архив не удалён: отсутствует актуальное состояние")
    op.drop_table("practice_snapshots")


def downgrade():
    raise RuntimeError(
        "Полные старые снимки удалены после нормализации и не восстанавливаются автоматически"
    )
