#!/bin/bash

# Development Setup Script for VAS Phase 1

echo "🔧 Setting up VAS Phase 1 for development..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp env.example .env
    echo "✅ .env file created. Please review configuration."
fi

# Check if PostgreSQL is running
echo "🗄️ Checking PostgreSQL..."
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "⚠️ PostgreSQL is not running. Please start PostgreSQL service."
    echo "   On Ubuntu: sudo systemctl start postgresql"
    echo "   On macOS: brew services start postgresql"
fi

# Check if Redis is running
echo "🔴 Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️ Redis is not running. Please start Redis service."
    echo "   On Ubuntu: sudo systemctl start redis"
    echo "   On macOS: brew services start redis"
fi

# Check if ffmpeg is installed
echo "🎥 Checking ffmpeg..."
if ! command -v ffprobe &> /dev/null; then
    echo "⚠️ ffmpeg is not installed. Please install ffmpeg:"
    echo "   On Ubuntu: sudo apt install ffmpeg"
    echo "   On macOS: brew install ffmpeg"
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🚀 To start the development server:"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🧪 To run tests:"
echo "   source venv/bin/activate"
echo "   pytest"
echo ""
echo "📖 API Documentation will be available at:"
echo "   http://localhost:8000/docs" 