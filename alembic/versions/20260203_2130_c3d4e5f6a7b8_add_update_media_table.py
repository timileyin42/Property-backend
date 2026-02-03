"""add update media table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-03 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'update_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('update_id', sa.Integer(), nullable=False),
        sa.Column('media_type', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['update_id'], ['updates.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_update_media_id'), 'update_media', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_update_media_id'), table_name='update_media')
    op.drop_table('update_media')
