@echo off
REM Frontend setup script for Admire HRMS (Windows)

echo Setting up Admire HRMS Frontend...

REM Install dependencies
echo Installing npm dependencies...
npm install

REM Copy environment file
if not exist ".env.local" (
    echo Creating .env.local from example...
    copy .env.local.example .env.local
    echo Please update .env.local with your configuration
)

REM Build the project
echo Building the project...
npm run build

echo Frontend setup completed!
echo Run 'npm run dev' to start the development server