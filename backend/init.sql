-- Initial database setup for VAS
-- This script runs when the PostgreSQL container starts

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE vas_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vas_db')\gexec

-- Connect to the vas_db database
\c vas_db;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Note: Users table will be created by the FastAPI application
-- Admin user is created programmatically in the auth service

-- Wait for tables to be created by the application before inserting devices
-- This will be handled by a separate initialization script 