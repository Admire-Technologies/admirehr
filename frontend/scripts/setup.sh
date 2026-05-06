#!/bin/bash

# Frontend setup script for Admire HRMS

echo "Setting up Admire HRMS Frontend..."

# Install dependencies
echo "Installing npm dependencies..."
npm install

# Copy environment file
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local from example..."
    cp .env.local.example .env.local
    echo "Please update .env.local with your configuration"
fi

# Build the project
echo "Building the project..."
npm run build

echo "Frontend setup completed!"
echo "Run 'npm run dev' to start the development server"