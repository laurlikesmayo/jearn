"""added language to user pref

Revision ID: 7a495d91e842
Revises: 41869491ce73
Create Date: 2024-06-01 20:58:39.824462

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a495d91e842'
down_revision = '41869491ce73'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_preferences', schema=None) as batch_op:
        batch_op.add_column(sa.Column('language', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_preferences', schema=None) as batch_op:
        batch_op.drop_column('language')

    # ### end Alembic commands ###
