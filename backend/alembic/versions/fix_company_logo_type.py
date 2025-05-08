"""Fix company logo column type

Revision ID: b123d456e789
Revises: 6020ebbc8773
Create Date: 2023-11-15 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import base64

# revision identifiers, used by Alembic.
revision = 'b123d456e789'
down_revision = '6020ebbc8773'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create a temporary column for the conversion
    op.add_column('companies', sa.Column('temp_logo', sa.String(), nullable=True))
    
    # Execute raw SQL to convert binary data to base64 string
    conn = op.get_bind()
    companies = conn.execute(text("SELECT id, logo FROM companies")).fetchall()
    
    for company_id, logo in companies:
        if logo is not None:
            # Convert binary to base64 string
            logo_string = base64.b64encode(logo).decode('utf-8')
            conn.execute(
                text(f"UPDATE companies SET temp_logo = '{logo_string}' WHERE id = {company_id}")
            )
    
    # Drop the old column and rename the new one
    op.drop_column('companies', 'logo')
    op.alter_column('companies', 'temp_logo', new_column_name='logo')
    
    # Update nullable status to match model
    op.alter_column('companies', 'logo', nullable=True)
    
    # Update address and website to be nullable as well, matching the model
    op.alter_column('companies', 'address', nullable=True)
    op.alter_column('companies', 'website', nullable=True)


def downgrade() -> None:
    # Note: Downgrading will lose the base64 encoding and may produce invalid binary data
    # Create a temporary column
    op.add_column('companies', sa.Column('temp_logo', sa.LargeBinary(), nullable=True))
    
    # Execute raw SQL to convert base64 string back to binary
    conn = op.get_bind()
    companies = conn.execute(text("SELECT id, logo FROM companies")).fetchall()
    
    for company_id, logo in companies:
        if logo is not None:
            try:
                # Try to convert string back to binary
                binary_data = base64.b64decode(logo)
                # Need to use parameters properly to avoid SQL injection and handle binary data
                conn.execute(
                    text("UPDATE companies SET temp_logo = :data WHERE id = :id"),
                    {"data": binary_data, "id": company_id}
                )
            except:
                # If conversion fails, set to NULL
                conn.execute(text(f"UPDATE companies SET temp_logo = NULL WHERE id = {company_id}"))
    
    # Drop the old column and rename the new one
    op.drop_column('companies', 'logo')
    op.alter_column('companies', 'temp_logo', new_column_name='logo')
    
    # Update nullable status back to original
    op.alter_column('companies', 'logo', nullable=False)
    op.alter_column('companies', 'address', nullable=False)
    op.alter_column('companies', 'website', nullable=False) 