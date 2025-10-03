-- Add new columns to devices table
ALTER TABLE devices ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS device_type VARCHAR(50);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS manufacturer VARCHAR(100);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS port INTEGER DEFAULT 554;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS username VARCHAR(100);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS password TEXT;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS location VARCHAR(255);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS tags TEXT;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS device_metadata TEXT;

-- Update existing records with default values
UPDATE devices SET name = 'Unknown Device' WHERE name IS NULL;
UPDATE devices SET device_type = 'ip_camera' WHERE device_type IS NULL;
UPDATE devices SET manufacturer = 'Unknown' WHERE manufacturer IS NULL;
UPDATE devices SET port = 554 WHERE port IS NULL;

-- Make required columns non-nullable (after setting defaults)
ALTER TABLE devices ALTER COLUMN name SET NOT NULL;
ALTER TABLE devices ALTER COLUMN device_type SET NOT NULL;
ALTER TABLE devices ALTER COLUMN manufacturer SET NOT NULL;
ALTER TABLE devices ALTER COLUMN rtsp_url SET NOT NULL; 