"""set default user role to investor

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-02-06 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e7f8a9b0c1d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'users',
        'role',
        existing_type=sa.Enum('PUBLIC', 'USER', 'INVESTOR', 'ADMIN', name='userrole'),
        server_default='INVESTOR'
    )
    op.execute("UPDATE users SET role = 'INVESTOR' WHERE role = 'USER'")


def downgrade() -> None:
    op.alter_column(
        'users',
        'role',
        existing_type=sa.Enum('PUBLIC', 'USER', 'INVESTOR', 'ADMIN', name='userrole'),
        server_default='USER'
    )
