"""added words

Revision ID: 53d528c903c3
Revises: 1369f3157375
Create Date: 2024-07-24 15:40:07.549383

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53d528c903c3'
down_revision = '1369f3157375'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ddoe', schema=None) as batch_op:
        batch_op.add_column(sa.Column('word', sa.String(length=50), nullable=True))
        batch_op.alter_column('topic',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=500),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ddoe', schema=None) as batch_op:
        batch_op.alter_column('topic',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=50),
               existing_nullable=True)
        batch_op.drop_column('word')

    # ### end Alembic commands ###
