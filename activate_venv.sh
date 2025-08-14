#!/bin/bash

# Simple script to activate virtual environment for agent_quality_analyzer
# Usage: source activate_venv.sh

PROJECT_DIR="/Users/matthew/Documents/lib/agent_quality_analyzer"
VENV_PATH="$PROJECT_DIR/venv"

# Check if we're in the right directory
if [[ "$PWD" != "$PROJECT_DIR"* ]]; then
    echo "⚠️  You're not in the project directory. Navigating to $PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Check if virtual environment exists
if [[ ! -f "$VENV_PATH/bin/activate" ]]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "🔄 Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    echo "✅ Virtual environment activated! You should see (venv) in your prompt."
elif [[ "$VIRTUAL_ENV" != "$VENV_PATH" ]]; then
    echo "🔄 Switching to project virtual environment..."
    if command -v deactivate &> /dev/null; then
        deactivate
    fi
    source "$VENV_PATH/bin/activate"
    echo "✅ Virtual environment activated!"
else
    echo "✅ Virtual environment already active!"
fi

# Test Python
echo "🧪 Testing Python:"
python --version
echo "📦 Testing packages:"
python -c "import pandas, requests, matplotlib; print('✅ All required packages available!')" 2>/dev/null || echo "❌ Some packages missing - run: pip install -r requirements.txt" 