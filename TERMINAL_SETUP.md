# Virtual Environment Setup for agent_quality_analyzer

## 🔍 Why AI Agent Terminal ≠ Manual Cursor Terminal

**The difference you noticed is real!** Here's why:

### AI Agent Terminal
- Runs in a **controlled environment** with the `.zshrc` properly loaded
- Automatically executes `source ~/.zshrc` with each session
- Has access to all shell functions and aliases

### Manual Cursor Terminal
- May start with a **minimal environment** or different shell initialization
- Might not load `.zshrc` automatically
- Could have different PATH or environment variables

## 🛠️ Solutions

### Option 1: Manual Activation Script (Recommended)
```bash
# In your Cursor terminal, run this:
source activate_venv.sh
```

This script will:
- ✅ Navigate to the project directory
- ✅ Activate the virtual environment
- ✅ Test Python and packages
- ✅ Show helpful status messages

### Option 2: Force .zshrc Reload
```bash
# In your Cursor terminal:
source ~/.zshrc
```

### Option 3: Direct Activation
```bash
# If you're already in the project directory:
source venv/bin/activate
```

## 🔧 Troubleshooting

### Problem: "python not found"
```bash
# Check if you're in the right directory:
pwd
# Should show: /Users/matthew/Documents/lib/agent_quality_analyzer

# Check if virtual environment is active:
echo $VIRTUAL_ENV
# Should show: /Users/matthew/Documents/lib/agent_quality_analyzer/venv

# If not, run:
source activate_venv.sh
```

### Problem: "deactivate command not found"
This happens when the auto-activation function tries to deactivate a non-existent virtual environment. The updated function now checks for this and should work properly.

### Problem: Cursor terminal vs AI agent terminal differences
- **AI Agent**: Always has full environment loaded
- **Manual Cursor**: May need manual activation
- **Solution**: Use `source activate_venv.sh` in manual terminals

## 🎯 Quick Start for Manual Terminal
```bash
# 1. Navigate to project (if not already there)
cd /Users/matthew/Documents/lib/agent_quality_analyzer

# 2. Activate virtual environment
source activate_venv.sh

# 3. Verify everything works
python --version
python -c "import pandas; print('Ready to go!')"
```

## 🔧 Troubleshooting Tools

### Quick Package Test
```bash
# Test if key packages are working
python quick_test.py
```

### Comprehensive Diagnosis
```bash
# Full diagnostic report
python diagnose_venv.py
```

### Nuclear Option (Complete Fix)
```bash
# Reinstall everything from scratch
source fix_venv.sh
```

## 📋 Package Testing

**Key packages to test:**
- `requests` - For HTTP requests
- `pandas` - For data manipulation
- `numpy` - For numerical operations
- `matplotlib` - For plotting
- `python-dotenv` - For environment variables
- `sqlite3` - For database operations

**Quick test commands:**
```bash
python -c "import requests; print('requests OK')"
python -c "import pandas; print('pandas OK')"
python -c "import numpy; print('numpy OK')"
python -c "import matplotlib; print('matplotlib OK')"
python -c "import dotenv; print('python-dotenv OK')"
```

## 🔄 Auto-activation Status
The `.zshrc` has been updated with a robust auto-activation function that:
- ✅ Automatically activates when entering the project directory
- ✅ Automatically deactivates when leaving
- ✅ Checks if `deactivate` command exists before using it
- ✅ Handles edge cases and errors gracefully

**Note**: New terminal windows should auto-activate, but existing terminals may need manual activation. 