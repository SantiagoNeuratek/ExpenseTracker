"""fix company_id nullable

Revision ID: abcdef123456
Revises: 123abc456def
Create Date: 2025-05-08 03:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abcdef123456'
down_revision = '123abc456def'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Explicitly make company_id nullable in users table
    op.alter_column('users', 'company_id', nullable=True)


def downgrade() -> None:
    # Revert company_id back to not null
    op.alter_column('users', 'company_id', nullable=False) 