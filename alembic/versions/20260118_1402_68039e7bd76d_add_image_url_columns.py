from alembic import op
import sqlalchemy as sa


revision = "68039e7bd76d"
down_revision = "6c2cfc2fbe79"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("investments", sa.Column("image_url", sa.String(), nullable=True))
    op.add_column("updates", sa.Column("image_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("updates", "image_url")
    op.drop_column("investments", "image_url")
