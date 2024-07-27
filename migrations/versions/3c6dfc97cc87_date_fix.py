"""date fix

Revision ID: 3c6dfc97cc87
Revises: 931ba25e3b65
Create Date: 2024-07-27 15:06:21.296121

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3c6dfc97cc87'
down_revision = '931ba25e3b65'
branch_labels = None
depends_on = None


from sqlalchemy import text

from sqlalchemy import text


def column_exists(bind, table_name, column_name):
    # Define the query for SQLite
    query = text("""
        SELECT COUNT(*)
        FROM pragma_table_info(:table_name)
        WHERE name = :column_name
    """)

    # Execute the query using a dictionary for parameters
    result = bind.execute(query, {'table_name': table_name, 'column_name': column_name})
    return result.scalar() > 0

def upgrade():
    bind = op.get_bind()
    if not column_exists(bind, 'ddoe', 'last_updated'):
        op.add_column('ddoe', sa.Column('last_updated', sa.Date(), nullable=True))
def downgrade():
    # Remove the column if you need to rollback the migration
    with op.batch_alter_table('ddoe', schema=None) as batch_op:
        batch_op.drop_column('last_updated')

    # ### end Alembic commands ###
