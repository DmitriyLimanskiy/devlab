"""Создание каталога курсов и шагов с JSONB-наполнением."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20261030_0001'
down_revision = None
branch_labels = None
depends_on = None


def timestamps():
    return [sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)]


def upgrade():
    op.create_table('courses',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column('status', sa.String(20), server_default=sa.text("'planned'"), nullable=False),
        sa.Column('position', sa.Integer(), server_default=sa.text('1'), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint('id', name='pk_courses'),
        sa.UniqueConstraint('slug', name='uq_courses_slug'),
        sa.CheckConstraint('position > 0', name=op.f('ck_courses_positive_position')),
        sa.CheckConstraint("status IN ('planned', 'available', 'archived')", name=op.f('ck_courses_valid_status')),
    )
    op.create_table('course_steps',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint('id', name='pk_course_steps'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_course_steps_course_id_courses', ondelete='RESTRICT'),
        sa.UniqueConstraint('course_id', 'position', name='uq_course_steps_course_position'),
        sa.UniqueConstraint('course_id', 'slug', name='uq_course_steps_course_slug'),
        sa.CheckConstraint('position > 0', name=op.f('ck_course_steps_positive_position')),
        sa.CheckConstraint("jsonb_typeof(content) = 'object'", name=op.f('ck_course_steps_content_object')),
    )


def downgrade():
    op.drop_table('course_steps')
    op.drop_table('courses')
