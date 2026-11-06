from alembic import op

revision = "20261106_0002"
down_revision = "20261106_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_practice_snapshots_delivery",
        "practice_snapshots",
        ["session_id", "generation", "version"],
    )


def downgrade():
    op.drop_constraint(
        "uq_practice_snapshots_delivery", "practice_snapshots", type_="unique"
    )
