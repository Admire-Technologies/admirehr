#!/bin/bash

# Comprehensive Test Runner for Admire HRMS
# This script runs all test suites and generates coverage reports

set -e  # Exit on error

echo "========================================="
echo "Admire HRMS Comprehensive Test Suite"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || source venv/Scripts/activate

# Install test dependencies
print_status "Installing test dependencies..."
pip install -r tests/requirements.txt > /dev/null 2>&1

# Create results directory
mkdir -p test-results

# Run backend unit tests
echo ""
echo "========================================="
echo "1. Running Backend Unit Tests"
echo "========================================="
cd backend
pytest -v --cov=apps --cov-report=html --cov-report=term --cov-report=xml -n auto || print_error "Backend unit tests failed"
mv htmlcov ../test-results/backend-coverage
mv coverage.xml ../test-results/backend-coverage.xml
cd ..
print_status "Backend unit tests completed"

# Run frontend unit tests
echo ""
echo "========================================="
echo "2. Running Frontend Unit Tests"
echo "========================================="
cd frontend
npm test -- --coverage --watchAll=false || print_error "Frontend unit tests failed"
cp -r coverage ../test-results/frontend-coverage
cd ..
print_status "Frontend unit tests completed"

# Run E2E tests
echo ""
echo "========================================="
echo "3. Running End-to-End Tests"
echo "========================================="
pytest tests/e2e/ -v -s || print_error "E2E tests failed"
print_status "E2E tests completed"

# Run performance tests
echo ""
echo "========================================="
echo "4. Running Performance Tests"
echo "========================================="
pytest tests/performance/ -v -s || print_error "Performance tests failed"
print_status "Performance tests completed"

# Run security tests
echo ""
echo "========================================="
echo "5. Running Security Tests"
echo "========================================="
pytest tests/security/ -v -s || print_error "Security tests failed"
print_status "Security tests completed"

# Run integration tests
echo ""
echo "========================================="
echo "6. Running Integration Tests"
echo "========================================="
pytest tests/integration/ -v -s || print_error "Integration tests failed"
print_status "Integration tests completed"

# Run accessibility tests
echo ""
echo "========================================="
echo "7. Running Accessibility Tests"
echo "========================================="
cd frontend
npm run test:accessibility || print_warning "Accessibility tests completed with warnings"
cd ..
print_status "Accessibility tests completed"

# Generate summary report
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo ""
print_status "All test suites completed!"
echo ""
echo "Test results and coverage reports are available in:"
echo "  - test-results/backend-coverage/"
echo "  - test-results/frontend-coverage/"
echo ""
echo "To view backend coverage report:"
echo "  open test-results/backend-coverage/index.html"
echo ""
echo "To view frontend coverage report:"
echo "  open test-results/frontend-coverage/lcov-report/index.html"
echo ""

# Deactivate virtual environment
deactivate
