#!/usr/bin/env python3
"""
Database Schema Fix Script
This script manually adds the missing columns to the devices table.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database configuration
DB_CONFIG = {
    'host': 'vas_db',  # Use the service name in Docker Compose
    'port': 5432,
    'database': 'vas_db',
    'user': 'vas_user',
    'password': 'vas_password'
}

def add_missing_columns():
    """Add missing columns to the devices table"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔧 Adding missing columns to devices table...")
        
        # Add columns one by one
        columns_to_add = [
            ("name", "VARCHAR(255)"),
            ("device_type", "VARCHAR(50)"),
            ("manufacturer", "VARCHAR(100)"),
            ("port", "INTEGER DEFAULT 554"),
            ("username", "VARCHAR(100)"),
            ("password", "TEXT"),
            ("location", "VARCHAR(255)"),
            ("description", "TEXT"),
            ("tags", "TEXT"),
            ("device_metadata", "TEXT")
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE devices ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
                print(f"✅ Added column: {column_name}")
            except Exception as e:
                print(f"⚠️  Column {column_name} might already exist: {e}")
        
        # Update existing records with default values
        print("🔄 Updating existing records with default values...")
        cursor.execute("UPDATE devices SET name = 'Unknown Device' WHERE name IS NULL;")
        cursor.execute("UPDATE devices SET device_type = 'ip_camera' WHERE device_type IS NULL;")
        cursor.execute("UPDATE devices SET manufacturer = 'Unknown' WHERE manufacturer IS NULL;")
        cursor.execute("UPDATE devices SET port = 554 WHERE port IS NULL;")
        
        # Make required columns non-nullable
        print("🔒 Making required columns non-nullable...")
        try:
            cursor.execute("ALTER TABLE devices ALTER COLUMN name SET NOT NULL;")
            cursor.execute("ALTER TABLE devices ALTER COLUMN device_type SET NOT NULL;")
            cursor.execute("ALTER TABLE devices ALTER COLUMN manufacturer SET NOT NULL;")
            cursor.execute("ALTER TABLE devices ALTER COLUMN rtsp_url SET NOT NULL;")
            print("✅ Made required columns non-nullable")
        except Exception as e:
            print(f"⚠️  Could not make columns non-nullable: {e}")
        
        cursor.close()
        conn.close()
        
        print("🎉 Database schema updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        return False

if __name__ == "__main__":
    add_missing_columns() 