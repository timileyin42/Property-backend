"""add investment sold value fields

Revision ID: c1d2e3f4a5b6
Revises: b6c7d8e9f0a1
Create Date: 2026-02-08 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b6c7d8e9f0a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('investments', sa.Column('sold_price_per_fraction', sa.Float(), nullable=True))
    op.add_column('investments', sa.Column('sold_value_total', sa.Float(), nullable=False, server_default='0'))
    op.add_column('investments', sa.Column('sold_profit_total', sa.Float(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('investments', 'sold_profit_total')
    op.drop_column('investments', 'sold_value_total')
    op.drop_column('investments', 'sold_price_per_fraction')
