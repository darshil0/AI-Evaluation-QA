#!/bin/bash
# setup.sh - Automated setup script for AI-Evaluation-QA (v2.3.1)

set -e  # Exit on error

echo "🚀 AI Evaluation & QA Framework Setup"
echo "======================================"

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.8.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "❌ Error: Python $REQUIRED_VERSION or higher required"
    echo "   Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📥 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "❌ Error: requirements.txt not found"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p data/prompts
mkdir -p data/annotations
mkdir -p data/datasets
mkdir -p reports
mkdir -p logs
mkdir -p tests
echo "✅ Directories created"

# Copy environment template
echo "🔐 Setting up environment variables..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env file created from template"
        echo "⚠️  IMPORTANT: Please edit .env and add your API keys"
    else
        echo "⚠️  Warning: .env.example not found"
    fi
else
    echo "ℹ️  .env file already exists"
fi

# Validate configuration
echo "🔍 Validating configuration..."
if python3 -c "from config.config_loader import ConfigLoader; ConfigLoader.load()" 2>/dev/null; then
    echo "✅ Configuration valid"
else
    echo "⚠️  Configuration validation skipped (API keys may not be set)"
fi

# Run tests
echo "🧪 Running tests..."
if pytest tests/ --tb=short -q 2>/dev/null; then
    echo "✅ All tests passed"
else
    echo "⚠️  Some tests failed (this may be expected if API keys are not set)"
fi

# Setup complete
echo ""
echo "✨ Setup Complete! ✨"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   nano .env"
echo ""
echo "2. Review configuration:"
echo "   nano config/settings.yaml"
echo ""
echo "3. Run your first evaluation:"
echo "   make run"
echo ""
echo "4. View documentation:"
echo "   cat docs/evaluation_protocol.md"
echo ""
echo "For help, visit: https://github.com/darshil0/AI-Evaluation-QA"
