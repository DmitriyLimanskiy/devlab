import sqlalchemy as sa
from alembic import op

revision = "20261106_0001"
down_revision = "b05920781370"
branch_labels = None
depends_on = None


def upgrade():
    """Назначить отдельный числовой первичный ключ снимкам"""
    op.add_column(
        "practice_snapshots",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
    )
    op.drop_constraint("pk_practice_snapshots", "practice_snapshots", type_="primary")
    op.create_primary_key("pk_practice_snapshots", "practice_snapshots", ["id"])


def downgrade():
    """Восстановить первичный ключ снимков по сессии"""
    # Несколько снимков одной сессии не позволят восстановить старый ключ
    # PostgreSQL откатит миграцию без удаления истории
    op.drop_constraint("pk_practice_snapshots", "practice_snapshots", type_="primary")
    op.create_primary_key("pk_practice_snapshots", "practice_snapshots", ["session_id"])
    op.drop_column("practice_snapshots", "id")
