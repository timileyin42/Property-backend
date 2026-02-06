"""add off plan fields

Revision ID: a1b2c3d4e5f7
Revises: f1a2b3c4d5e6
Create Date: 2026-02-06 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('properties', sa.Column('is_off_plan', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('properties', sa.Column('off_plan_duration_months', sa.Integer(), nullable=True))
    op.add_column('updates', sa.Column('off_plan_only', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('updates', 'off_plan_only')
    op.drop_column('properties', 'off_plan_duration_months')
    op.drop_column('properties', 'is_off_plan')
