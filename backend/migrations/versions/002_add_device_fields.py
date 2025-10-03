"""Add device fields

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to devices table
    op.add_column('devices', sa.Column('name', sa.String(255), nullable=True))
    op.add_column('devices', sa.Column('device_type', sa.String(50), nullable=True))
    op.add_column('devices', sa.Column('manufacturer', sa.String(100), nullable=True))
    op.add_column('devices', sa.Column('port', sa.Integer(), nullable=True, server_default='554'))
    op.add_column('devices', sa.Column('username', sa.String(100), nullable=True))
    op.add_column('devices', sa.Column('password', sa.Text(), nullable=True))
    op.add_column('devices', sa.Column('location', sa.String(255), nullable=True))
    op.add_column('devices', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('devices', sa.Column('tags', sa.Text(), nullable=True))
    op.add_column('devices', sa.Column('device_metadata', sa.Text(), nullable=True))
    
    # Update existing records with default values
    op.execute("UPDATE devices SET name = 'Unknown Device' WHERE name IS NULL")
    op.execute("UPDATE devices SET device_type = 'ip_camera' WHERE device_type IS NULL")
    op.execute("UPDATE devices SET manufacturer = 'Unknown' WHERE manufacturer IS NULL")
    op.execute("UPDATE devices SET port = 554 WHERE port IS NULL")
    
    # Make required columns non-nullable
    op.alter_column('devices', 'name', nullable=False)
    op.alter_column('devices', 'device_type', nullable=False)
    op.alter_column('devices', 'manufacturer', nullable=False)
    op.alter_column('devices', 'rtsp_url', nullable=False)


def downgrade():
    # Remove new columns
    op.drop_column('devices', 'device_metadata')
    op.drop_column('devices', 'tags')
    op.drop_column('devices', 'description')
    op.drop_column('devices', 'location')
    op.drop_column('devices', 'password')
    op.drop_column('devices', 'username')
    op.drop_column('devices', 'port')
    op.drop_column('devices', 'manufacturer')
    op.drop_column('devices', 'device_type')
    op.drop_column('devices', 'name') 