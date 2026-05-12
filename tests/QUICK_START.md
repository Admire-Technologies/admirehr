# Quick Start Guide - Admire HRMS Test Suite

This guide will help you quickly set up and run the comprehensive test suite.

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (running)
- Redis 7+ (running)

## 5-Minute Setup

### 1. Install Dependencies

```bash
# Install Python test dependencies
pip install -r tests/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Set Up Test Database

```bash
# Create test database
createdb admire_hrms_test

# Run migrations
cd backend
python manage.py migrate
cd ..
```

### 3. Start Required Services

```bash
# Terminal 1: Start Redis (if not running)
redis-server

# Terminal 2: Start backend server
cd backend
python manage.py runserver

# Terminal 3: Start frontend (optional for E2E tests)
cd frontend
npm run dev
```

### 4. Run Tests

**Option A: Run All Tests**
```bash
# Unix/Linux/Mac
./tests/run_all_tests.sh

# Windows
tests\run_all_tests.bat
```

**Option B: Run Specific Test Suite**
```bash
# E2E tests
pytest tests/e2e/ -v

# Performance tests
pytest tests/performance/ -v -s

# Security tests
pytest tests/security/ -v -s

# Load tests (opens web UI at http://localhost:8089)
cd tests/load
locust -f test_load.py --host=http://localhost:8000

# Integration tests
pytest tests/integration/ -v -s

# Accessibility tests
cd frontend
npm run test:accessibility
```

## Quick Test Commands

### Backend Tests
```bash
cd backend
pytest -v --cov=apps
```

### Frontend Tests
```bash
cd frontend
npm test
```

### E2E Tests
```bash
pytest tests/e2e/test_user_workflows.py -v
```

### Performance Tests
```bash
pytest tests/performance/test_performance.py -v -s
```

### Security Tests
```bash
pytest tests/security/test_security.py -v -s
```

### Load Tests (Headless)
```bash
cd tests/load
locust -f test_load.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 2m --headless
```

### Load Tests (Web UI)
```bash
cd tests/load
locust -f test_load.py --host=http://localhost:8000
# Open http://localhost:8089 in browser
```

## View Coverage Reports

### Backend Coverage
```bash
cd backend
pytest --cov=apps --cov-report=html
# Open htmlcov/index.html in browser
```

### Frontend Coverage
```bash
cd frontend
npm test -- --coverage
# Open coverage/lcov-report/index.html in browser
```

## Common Issues

### "Database does not exist"
```bash
createdb admire_hrms_test
cd backend
python manage.py migrate
```

### "Redis connection refused"
```bash
# Start Redis
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r tests/requirements.txt
cd frontend && npm install
```

### "Permission denied" (Unix/Linux/Mac)
```bash
chmod +x tests/run_all_tests.sh
chmod +x tests/load/run_load_test.sh
```

## Test Results Location

After running tests, find results in:
- `backend/htmlcov/` - Backend coverage
- `frontend/coverage/` - Frontend coverage
- `tests/load/results/` - Load test reports
- `test-results/` - Combined test results

## Next Steps

1. Review test results and coverage reports
2. Check `tests/README.md` for detailed documentation
3. Review `TASK_19_TEST_SUITE_SUMMARY.md` for complete overview
4. Integrate tests into your CI/CD pipeline

## Need Help?

- Check `tests/README.md` for detailed documentation
- Review test files for examples
- Check GitHub Actions workflow for CI/CD setup

## Quick Reference

| Test Type | Command | Duration |
|-----------|---------|----------|
| All Tests | `./tests/run_all_tests.sh` | ~10-15 min |
| Backend Unit | `cd backend && pytest` | ~2-3 min |
| Frontend Unit | `cd frontend && npm test` | ~1-2 min |
| E2E | `pytest tests/e2e/ -v` | ~2-3 min |
| Performance | `pytest tests/performance/ -v` | ~3-5 min |
| Security | `pytest tests/security/ -v` | ~2-3 min |
| Load (light) | `locust ... --users 10 --run-time 2m` | ~2 min |
| Integration | `pytest tests/integration/ -v` | ~2-3 min |
| Accessibility | `cd frontend && npm run test:accessibility` | ~2-3 min |

Happy Testing! 🚀
