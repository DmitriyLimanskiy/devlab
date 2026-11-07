revision = "b05920781370"
down_revision = "8ca2ebb96c2b"
branch_labels = None
depends_on = None


def upgrade():
    """Сохранить пустой шаг истории миграций без изменения схемы"""
    pass


def downgrade():
    """Откатить пустой шаг истории миграций без изменения схемы"""
    pass
