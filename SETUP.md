# Admire HRMS Setup Guide

This guide will help you set up the Admire HRMS development environment.

## Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.9 or higher)
- **Docker Desktop** (running) and **Docker Compose**
- **Git**

## Quick Start

### 0. Start Docker Desktop

Make sure Docker Desktop is running on your system before proceeding.

### 1. Start Database Services

First, start the PostgreSQL and Redis services using Docker:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- Redis server on port 6379

### 2. Backend Setup

Navigate to the backend directory and set up the Django application:

#### On Linux/macOS:
```bash
cd backend
chmod +x scripts/run_dev.sh
./scripts/run_dev.sh
```

#### On Windows:
```cmd
cd backend
scripts\run_dev.bat
```

This script will:
- Create a Python virtual environment
- Install Python dependencies
- Run database migrations
- Create sample development data
- Start the Django development server on port 8000

### 3. Frontend Setup

In a new terminal, navigate to the frontend directory:

#### On Linux/macOS:
```bash
cd frontend
chmod +x scripts/setup.sh
./scripts/setup.sh
npm run dev
```

#### On Windows:
```cmd
cd frontend
scripts\setup.bat
npm run dev
```

This will:
- Install Node.js dependencies
- Create environment configuration
- Build the project
- Start the Next.js development server on port 3000

## Manual Setup

If you prefer to set up manually:

### Backend Manual Setup

1. **Create virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create sample data:**
   ```bash
   python scripts/setup_dev.py
   ```

6. **Start server:**
   ```bash
   python manage.py runserver
   ```

### Frontend Manual Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your API URLs
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

## Default Credentials

After running the setup scripts, you can log in with:

- **Username:** admin
- **Password:** admin123
- **Company:** Demo Company

## API Documentation

Once the backend is running, you can access:

- **API Documentation:** http://localhost:8000/api/docs/
- **Admin Panel:** http://localhost:8000/admin/

## Development URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/v1/
- **Admin Panel:** http://localhost:8000/admin/
- **API Docs:** http://localhost:8000/api/docs/

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Ensure Docker containers are running:
   ```bash
   docker-compose ps
   ```

2. Check database logs:
   ```bash
   docker-compose logs postgres
   ```

### Port Conflicts

If ports 3000, 8000, 5432, or 6379 are already in use:

1. Stop conflicting services
2. Or modify the ports in `docker-compose.yml` and update environment variables

### Permission Issues (Linux/macOS)

If you get permission errors:

```bash
chmod +x backend/scripts/run_dev.sh
chmod +x frontend/scripts/setup.sh
```

## Next Steps

After setup is complete:

1. Explore the API documentation at http://localhost:8000/api/docs/
2. Check the admin panel at http://localhost:8000/admin/
3. Start implementing additional features according to the task list
4. Review the requirements and design documents in `.kiro/specs/admire-hrms/`

## Production Deployment

For production deployment, refer to the deployment documentation (to be created in later tasks).