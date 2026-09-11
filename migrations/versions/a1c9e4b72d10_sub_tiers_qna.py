"""vehicle subscription tiers + qna board

Revision ID: a1c9e4b72d10
Revises: f03b6703427c
Create Date: 2026-09-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c9e4b72d10'
down_revision = 'f03b6703427c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('vehicle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price_3m_man', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('price_6m_man', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('price_24m_man', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('deposit_man', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('prepay_man', sa.Integer(), nullable=True))

    op.create_table(
        'qna_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_private', sa.Boolean(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('answered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('qna_post', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_qna_post_user_id'), ['user_id'], unique=False)


def downgrade():
    with op.batch_alter_table('qna_post', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_qna_post_user_id'))
    op.drop_table('qna_post')

    with op.batch_alter_table('vehicle', schema=None) as batch_op:
        batch_op.drop_column('prepay_man')
        batch_op.drop_column('deposit_man')
        batch_op.drop_column('price_24m_man')
        batch_op.drop_column('price_6m_man')
        batch_op.drop_column('price_3m_man')
