"""add update comments and likes

Revision ID: a1b2c3d4e5f6
Revises: 36ab1c639166
Create Date: 2026-02-03 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '36ab1c639166'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create update_comments table
    op.create_table(
        'update_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('update_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['update_id'], ['updates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_update_comments_id'), 'update_comments', ['id'], unique=False)

    # Create update_likes table
    op.create_table(
        'update_likes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('update_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['update_id'], ['updates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_update_likes_id'), 'update_likes', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_update_likes_id'), table_name='update_likes')
    op.drop_table('update_likes')
    op.drop_index(op.f('ix_update_comments_id'), table_name='update_comments')
    op.drop_table('update_comments')
