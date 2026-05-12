#!/bin/bash

# Load Testing Script for Admire HRMS
# This script runs load tests with different scenarios

echo "========================================="
echo "Admire HRMS Load Testing"
echo "========================================="
echo ""

# Create results directory
mkdir -p results

# Function to run load test
run_load_test() {
    local scenario=$1
    local users=$2
    local spawn_rate=$3
    local duration=$4
    
    echo "Running $scenario scenario..."
    echo "  Users: $users"
    echo "  Spawn rate: $spawn_rate/s"
    echo "  Duration: $duration"
    echo ""
    
    locust -f test_load.py \
        --host=http://localhost:8000 \
        --users=$users \
        --spawn-rate=$spawn_rate \
        --run-time=$duration \
        --headless \
        --html=results/${scenario}-report.html \
        --csv=results/${scenario} \
        --loglevel=INFO
    
    echo ""
    echo "$scenario completed!"
    echo "Report: results/${scenario}-report.html"
    echo ""
}

# Scenario 1: Light Load
echo "========================================="
echo "Scenario 1: Light Load (10 users)"
echo "========================================="
run_load_test "light-load" 10 2 "2m"

# Scenario 2: Normal Load
echo "========================================="
echo "Scenario 2: Normal Load (50 users)"
echo "========================================="
run_load_test "normal-load" 50 5 "3m"

# Scenario 3: Peak Load
echo "========================================="
echo "Scenario 3: Peak Load (100 users)"
echo "========================================="
run_load_test "peak-load" 100 10 "5m"

# Scenario 4: Stress Test
echo "========================================="
echo "Scenario 4: Stress Test (200 users)"
echo "========================================="
run_load_test "stress-test" 200 20 "5m"

# Generate summary
echo "========================================="
echo "Load Testing Summary"
echo "========================================="
echo ""
echo "All load test scenarios completed!"
echo ""
echo "Reports available in results/ directory:"
ls -lh results/*.html
echo ""
echo "To view reports, open the HTML files in a browser:"
echo "  open results/light-load-report.html"
echo "  open results/normal-load-report.html"
echo "  open results/peak-load-report.html"
echo "  open results/stress-test-report.html"
echo ""
