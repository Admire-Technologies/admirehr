@echo off
REM Comprehensive Test Runner for Admire HRMS (Windows)
REM This script runs all test suites and generates coverage reports

echo =========================================
echo Admire HRMS Comprehensive Test Suite
echo =========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [!] Virtual environment not found. Creating...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install test dependencies
echo [*] Installing test dependencies...
pip install -r tests\requirements.txt >nul 2>&1

REM Create results directory
if not exist "test-results" mkdir test-results

REM Run backend unit tests
echo.
echo =========================================
echo 1. Running Backend Unit Tests
echo =========================================
cd backend
pytest -v --cov=apps --cov-report=html --cov-report=term --cov-report=xml -n auto
if errorlevel 1 echo [X] Backend unit tests failed
move htmlcov ..\test-results\backend-coverage >nul 2>&1
move coverage.xml ..\test-results\backend-coverage.xml >nul 2>&1
cd ..
echo [+] Backend unit tests completed

REM Run frontend unit tests
echo.
echo =========================================
echo 2. Running Frontend Unit Tests
echo =========================================
cd frontend
call npm test -- --coverage --watchAll=false
if errorlevel 1 echo [X] Frontend unit tests failed
xcopy /E /I /Y coverage ..\test-results\frontend-coverage >nul 2>&1
cd ..
echo [+] Frontend unit tests completed

REM Run E2E tests
echo.
echo =========================================
echo 3. Running End-to-End Tests
echo =========================================
pytest tests\e2e\ -v -s
if errorlevel 1 echo [X] E2E tests failed
echo [+] E2E tests completed

REM Run performance tests
echo.
echo =========================================
echo 4. Running Performance Tests
echo =========================================
pytest tests\performance\ -v -s
if errorlevel 1 echo [X] Performance tests failed
echo [+] Performance tests completed

REM Run security tests
echo.
echo =========================================
echo 5. Running Security Tests
echo =========================================
pytest tests\security\ -v -s
if errorlevel 1 echo [X] Security tests failed
echo [+] Security tests completed

REM Run integration tests
echo.
echo =========================================
echo 6. Running Integration Tests
echo =========================================
pytest tests\integration\ -v -s
if errorlevel 1 echo [X] Integration tests failed
echo [+] Integration tests completed

REM Run accessibility tests
echo.
echo =========================================
echo 7. Running Accessibility Tests
echo =========================================
cd frontend
call npm run test:accessibility
if errorlevel 1 echo [!] Accessibility tests completed with warnings
cd ..
echo [+] Accessibility tests completed

REM Generate summary report
echo.
echo =========================================
echo Test Summary
echo =========================================
echo.
echo [+] All test suites completed!
echo.
echo Test results and coverage reports are available in:
echo   - test-results\backend-coverage\
echo   - test-results\frontend-coverage\
echo.
echo To view backend coverage report:
echo   start test-results\backend-coverage\index.html
echo.
echo To view frontend coverage report:
echo   start test-results\frontend-coverage\lcov-report\index.html
echo.

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

pause
