# AdmireHR

Django backend with React frontend application.

## Setup

### Backend (Django)

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend runs on: http://localhost:8000

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:5173

## API Endpoints

- Health Check: http://localhost:8000/api/health/
- Admin Panel: http://localhost:8000/admin/
