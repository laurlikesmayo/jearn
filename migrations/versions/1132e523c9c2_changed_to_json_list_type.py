"""changed to json list type

Revision ID: 1132e523c9c2
Revises: 07982c0e9bff
Create Date: 2024-07-27 14:36:45.781348

"""
from alembic import op
from sqlalchemy import Text
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1132e523c9c2'
down_revision = '07982c0e9bff'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ddoe', schema=None) as batch_op:
        batch_op.alter_column('previous_topics',
               existing_type=sa.BLOB(),
               type_=postgresql.JSON(astext_type=Text()),
               existing_nullable=True)
        batch_op.alter_column('previous_words',
               existing_type=sa.BLOB(),
               type_=postgresql.JSON(astext_type=Text()),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ddoe', schema=None) as batch_op:
        batch_op.alter_column('previous_words',
               existing_type=postgresql.JSON(astext_type=Text()),
               type_=sa.BLOB(),
               existing_nullable=True)
        batch_op.alter_column('previous_topics',
               existing_type=postgresql.JSON(astext_type=Text()),
               type_=sa.BLOB(),
               existing_nullable=True)

    # ### end Alembic commands ###