#!/bin/bash

# Development startup script for Admire HRMS backend

echo "Starting Admire HRMS Development Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist
echo "Setting up development data..."
python scripts/setup_dev.py

# Start development server
echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000