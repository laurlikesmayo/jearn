"""changed to date

Revision ID: 05cf5897c181
Revises: 1132e523c9c2
Create Date: 2024-07-27 14:55:51.943390

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05cf5897c181'
down_revision = '1132e523c9c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ddoe', schema=None) as batch_op:
        batch_op.alter_column('last_updated',
               existing_type=sa.DATETIME(),
               type_=sa.Date(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ddoe', schema=None) as batch_op:
        batch_op.alter_column('last_updated',
               existing_type=sa.Date(),
               type_=sa.DATETIME(),
               existing_nullable=True)

    # ### end Alembic commands ###
