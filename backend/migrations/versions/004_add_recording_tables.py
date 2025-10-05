# Live DVR Feature - Database Migration

## Migration: Add recording_segments and recording_status tables

Revision ID: 004_add_recording_tables
Revises: 003_add_snapshots_table
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_recording_tables'
down_revision = '003_add_snapshots_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create recording_segments table
    op.create_table('recording_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('segment_file_path', sa.String(length=500), nullable=False),
        sa.Column('start_timestamp', sa.DateTime(), nullable=False),
        sa.Column('end_timestamp', sa.DateTime(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create recording_status table
    op.create_table('recording_status',
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_recording', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_segment_timestamp', sa.DateTime(), nullable=True),
        sa.Column('total_segments', sa.Integer(), nullable=False, default=0),
        sa.Column('total_size_bytes', sa.BigInteger(), nullable=False, default=0),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('device_id')
    )
    
    # Create indexes for performance
    op.create_index('idx_recording_segments_device_timestamp', 'recording_segments', ['device_id', 'start_timestamp'])
    op.create_index('idx_recording_segments_timestamp_range', 'recording_segments', ['start_timestamp', 'end_timestamp'])
    op.create_index('idx_recording_segments_device_id', 'recording_segments', ['device_id'])
    op.create_index('idx_recording_status_device_id', 'recording_status', ['device_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_recording_status_device_id', table_name='recording_status')
    op.drop_index('idx_recording_segments_device_id', table_name='recording_segments')
    op.drop_index('idx_recording_segments_timestamp_range', table_name='recording_segments')
    op.drop_index('idx_recording_segments_device_timestamp', table_name='recording_segments')
    
    # Drop tables
    op.drop_table('recording_status')
    op.drop_table('recording_segments')
