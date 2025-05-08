"""merge heads

Revision ID: 123abc456def
Revises: b123d456e789, ee59460ffbdf
Create Date: 2025-05-08 03:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '123abc456def'
down_revision = None
branch_labels = None
depends_on = ('b123d456e789', 'ee59460ffbdf')


def upgrade() -> None:
    # This is a merge migration - it doesn't need to do anything
    # Its purpose is just to connect the two branches
    pass


def downgrade() -> None:
    # No downgrade needed for a merge migration
    pass 