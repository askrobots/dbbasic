#!/bin/bash

# DBBasic Deployment Script
# Deploy DBBasic with Presentation Layer

echo "======================================"
echo "🚀 DBBasic Deployment"
echo "======================================"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
echo "✓ Python version: $python_version"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Generate UI files
echo "Generating UI with Presentation Layer..."
python generate_all_ui.py

# Run tests
echo "Running tests..."
python -m pytest tests/ -v

# Start services
echo "Starting DBBasic services..."
python launch_dbbasic.py &

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "Services running at:"
echo "  • Dashboard: http://localhost:8004"
echo "  • Data Service: http://localhost:8005"
echo "  • AI Services: http://localhost:8003"
echo "  • Event Store: http://localhost:8006"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
wait
