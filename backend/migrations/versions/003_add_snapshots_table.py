# Snapshot Feature - Database Migration

## Migration: Add snapshots table

Revision ID: 003_add_snapshots_table
Revises: 002_add_device_fields
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_snapshots_table'
down_revision = '002_add_device_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create snapshots table
    op.create_table('snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('image_data', sa.LargeBinary(), nullable=False),
        sa.Column('image_format', sa.String(length=10), nullable=False, default='jpeg'),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('captured_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_snapshots_device_id', 'snapshots', ['device_id'])
    op.create_index('idx_snapshots_captured_at', 'snapshots', ['captured_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_snapshots_captured_at', table_name='snapshots')
    op.drop_index('idx_snapshots_device_id', table_name='snapshots')
    
    # Drop table
    op.drop_table('snapshots')
