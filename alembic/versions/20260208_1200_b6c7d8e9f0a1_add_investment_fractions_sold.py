"""add investment fractions sold

Revision ID: b6c7d8e9f0a1
Revises: a1b2c3d4e5f7
Create Date: 2026-02-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6c7d8e9f0a1'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('investments', sa.Column('fractions_sold', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('investments', 'fractions_sold')
