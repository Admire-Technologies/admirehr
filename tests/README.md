# Admire HRMS Comprehensive Test Suite

This directory contains the complete test suite for the Admire HRMS system, covering all aspects of quality assurance including unit tests, integration tests, E2E tests, performance tests, security tests, load tests, and accessibility tests.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Setup](#setup)
4. [Running Tests](#running-tests)
5. [Test Types](#test-types)
6. [Coverage Reports](#coverage-reports)
7. [CI/CD Integration](#cicd-integration)
8. [Best Practices](#best-practices)

## Overview

The test suite validates:
- ✅ All user workflows (E2E)
- ✅ API performance under load
- ✅ Security vulnerabilities
- ✅ Concurrent user scenarios
- ✅ Accessibility compliance (WCAG 2.1)
- ✅ Third-party service integrations
- ✅ Code coverage (backend and frontend)

## Test Structure

```
tests/
├── e2e/                          # End-to-end tests
│   └── test_user_workflows.py   # Complete user workflow tests
├── performance/                  # Performance tests
│   ├── test_performance.py      # API performance tests
│   └── requirements.txt
├── security/                     # Security tests
│   ├── test_security.py         # Security vulnerability tests
│   └── requirements.txt
├── load/                         # Load tests
│   ├── test_load.py             # Locust load tests
│   └── requirements.txt
├── integration/                  # Integration tests
│   ├── test_third_party_integrations.py
│   └── requirements.txt
├── deployment/                   # Deployment tests
│   └── test_deployment.py       # Production deployment tests
├── requirements.txt              # Main test requirements
├── run_all_tests.sh             # Unix test runner
├── run_all_tests.bat            # Windows test runner
└── README.md                    # This file
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker (optional, for containerized testing)

### Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r tests/requirements.txt
   ```

2. **Install Node.js dependencies:**
   ```bash
   cd frontend
   npm install
   ```

3. **Set up test database:**
   ```bash
   createdb admire_hrms_test
   cd backend
   python manage.py migrate --settings=admire_hrms.settings_test
   ```

4. **Start required services:**
   ```bash
   # Start Redis
   redis-server
   
   # Start Celery workers
   cd backend
   celery -A admire_hrms worker -l info
   ```

## Running Tests

### Run All Tests

**Unix/Linux/Mac:**
```bash
chmod +x tests/run_all_tests.sh
./tests/run_all_tests.sh
```

**Windows:**
```cmd
tests\run_all_tests.bat
```

### Run Specific Test Suites

**Backend Unit Tests:**
```bash
cd backend
pytest -v --cov=apps --cov-report=html
```

**Frontend Unit Tests:**
```bash
cd frontend
npm test
```

**E2E Tests:**
```bash
pytest tests/e2e/ -v
```

**Performance Tests:**
```bash
pytest tests/performance/ -v -s
```

**Security Tests:**
```bash
pytest tests/security/ -v -s
```

**Load Tests:**
```bash
cd tests/load
locust -f test_load.py --host=http://localhost:8000
```

**Integration Tests:**
```bash
pytest tests/integration/ -v -s
```

**Accessibility Tests:**
```bash
cd frontend
npm run test:accessibility
```

## Test Types

### 1. End-to-End Tests (`tests/e2e/`)

Tests complete user workflows from start to finish:
- Authentication workflow (login, token refresh, logout)
- Employee CRUD operations
- Attendance check-in/check-out
- Leave request and approval
- Payroll generation
- Dashboard metrics
- RBAC functionality

**Run:**
```bash
pytest tests/e2e/test_user_workflows.py -v
```

### 2. Performance Tests (`tests/performance/`)

Tests system performance under various conditions:
- API response times
- Database query performance
- Concurrent request handling
- Cache effectiveness
- Pagination performance

**Run:**
```bash
pytest tests/performance/test_performance.py -v -s
```

**Expected Performance:**
- Employee list: < 2s
- Attendance list: < 2s
- Dashboard metrics: < 3s
- Concurrent requests: 95%+ success rate

### 3. Security Tests (`tests/security/`)

Tests security measures and vulnerability protection:
- Authentication security (invalid credentials, SQL injection)
- Authorization and RBAC
- Multi-tenant data isolation
- XSS protection
- Command injection protection
- Data encryption
- Security headers
- Rate limiting
- Input validation

**Run:**
```bash
pytest tests/security/test_security.py -v -s
```

### 4. Load Tests (`tests/load/`)

Tests system behavior under high concurrent load using Locust:
- Simulates multiple user types (regular users, managers, HR admins)
- Tests concurrent operations
- Measures throughput and response times
- Identifies bottlenecks

**Run:**
```bash
cd tests/load
locust -f test_load.py --host=http://localhost:8000 --users 100 --spawn-rate 10
```

**Access Web UI:**
Open http://localhost:8089 in your browser

### 5. Integration Tests (`tests/integration/`)

Tests integration with third-party services:
- Redis cache
- Celery task queue
- Email services
- Face Plugin SDK (biometric)
- WebSocket connections
- Database transactions
- File storage

**Run:**
```bash
pytest tests/integration/test_third_party_integrations.py -v -s
```

### 6. Accessibility Tests (`frontend/src/__tests__/accessibility/`)

Tests WCAG 2.1 AA compliance:
- Automated accessibility scanning with axe-core
- Keyboard navigation
- Screen reader compatibility
- Color contrast
- Form labels and ARIA attributes
- Focus indicators
- Heading hierarchy
- Responsive design accessibility

**Run:**
```bash
cd frontend
npm run test:accessibility
```

### 7. Deployment Tests (`tests/deployment/`)

Tests production deployment health:
- Service availability
- Database connectivity
- Cache connectivity
- Celery workers
- WebSocket endpoints
- Security headers
- Performance benchmarks

**Run:**
```bash
pytest tests/deployment/test_deployment.py -v
```

## Coverage Reports

### Backend Coverage

After running backend tests, view coverage report:
```bash
open backend/htmlcov/index.html  # Mac
xdg-open backend/htmlcov/index.html  # Linux
start backend\htmlcov\index.html  # Windows
```

**Target Coverage:** 80%+ overall

### Frontend Coverage

After running frontend tests, view coverage report:
```bash
open frontend/coverage/lcov-report/index.html  # Mac
xdg-open frontend/coverage/lcov-report/index.html  # Linux
start frontend\coverage\lcov-report\index.html  # Windows
```

**Target Coverage:** 70%+ overall

## CI/CD Integration

The test suite is integrated with GitHub Actions via `.github/workflows/test-pipeline.yml`.

### Automated Testing

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Daily scheduled runs at 2 AM UTC

### Pipeline Stages

1. **Backend Unit Tests** - Runs all backend unit tests with coverage
2. **Frontend Unit Tests** - Runs all frontend unit tests with coverage
3. **E2E Tests** - Runs end-to-end workflow tests
4. **Performance Tests** - Validates performance benchmarks
5. **Security Tests** - Checks for security vulnerabilities
6. **Accessibility Tests** - Validates WCAG compliance
7. **Coverage Report** - Generates combined coverage report

### Artifacts

Test results and coverage reports are uploaded as artifacts:
- `backend-coverage-report`
- `frontend-coverage-report`
- `e2e-test-results`
- `performance-test-results`
- `security-test-results`
- `accessibility-test-results`

## Best Practices

### Writing Tests

1. **Follow AAA Pattern:**
   - Arrange: Set up test data
   - Act: Execute the operation
   - Assert: Verify the result

2. **Use Descriptive Names:**
   ```python
   def test_employee_creation_with_valid_data():
       # Clear test purpose from name
   ```

3. **Keep Tests Independent:**
   - Each test should run independently
   - Use fixtures for setup/teardown
   - Don't rely on test execution order

4. **Test Edge Cases:**
   - Empty inputs
   - Boundary values
   - Invalid data
   - Error conditions

5. **Mock External Services:**
   - Use mocks for external APIs
   - Mock time-dependent operations
   - Isolate unit tests from external dependencies

### Performance Testing

1. **Set Realistic Thresholds:**
   - Based on actual usage patterns
   - Consider network latency
   - Account for database size

2. **Test Under Load:**
   - Simulate concurrent users
   - Test peak load scenarios
   - Monitor resource usage

### Security Testing

1. **Test All Input Points:**
   - API endpoints
   - Form inputs
   - URL parameters
   - File uploads

2. **Verify Authentication:**
   - Test with invalid tokens
   - Test expired tokens
   - Test missing authentication

3. **Check Authorization:**
   - Test RBAC enforcement
   - Test multi-tenant isolation
   - Test privilege escalation

### Accessibility Testing

1. **Automated + Manual:**
   - Use automated tools (axe-core)
   - Perform manual testing with screen readers
   - Test keyboard navigation

2. **Test All Components:**
   - Forms and inputs
   - Navigation
   - Modals and dialogs
   - Data tables
   - Charts and visualizations

## Troubleshooting

### Common Issues

**Tests fail with database errors:**
```bash
# Reset test database
dropdb admire_hrms_test
createdb admire_hrms_test
cd backend
python manage.py migrate
```

**Redis connection errors:**
```bash
# Start Redis
redis-server
# Or use Docker
docker run -d -p 6379:6379 redis:7
```

**Celery worker not running:**
```bash
cd backend
celery -A admire_hrms worker -l info
```

**Frontend tests fail:**
```bash
cd frontend
rm -rf node_modules
npm install
npm test
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Update test documentation
5. Add integration tests for new services

## Support

For issues or questions:
- Check existing test documentation
- Review test output and error messages
- Consult the main project README
- Contact the development team

## License

This test suite is part of the Admire HRMS project and follows the same license.
