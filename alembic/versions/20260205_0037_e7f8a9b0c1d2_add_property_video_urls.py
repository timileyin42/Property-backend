"""add property video urls

Revision ID: e7f8a9b0c1d2
Revises: 696b427001fc
Create Date: 2026-02-05 00:37:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7f8a9b0c1d2'
down_revision = '696b427001fc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('properties', sa.Column('video_urls', sa.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    op.drop_column('properties', 'video_urls')
