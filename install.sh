#!/bin/bash

# DBBasic Installer
# From 0 to 402M rows/sec in 30 seconds

echo "==============================================="
echo "   DBBasic - This Isn't Development Anymore"
echo "   402 Million Rows/Second • No Code Required"
echo "==============================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install requirements
echo "📥 Installing DBBasic engine (this may take a minute)..."
pip install -r requirements.txt --quiet

# Create user data directory
echo "📁 Creating data directory..."
mkdir -p user_data

# Create the dbbasic command
echo "🔧 Creating dbbasic command..."
cat > dbbasic << 'EOF'
#!/bin/bash
# DBBasic CLI

source .venv/bin/activate 2>/dev/null

case "$1" in
    serve)
        echo "Starting DBBasic server..."
        echo "Open http://localhost:8000 in your browser"
        python core/server.py
        ;;
    demo)
        echo "Starting DBBasic demo..."
        echo "Opening mockups at http://localhost:8000/static/mockups.html"
        python core/server.py &
        sleep 2
        open http://localhost:8000/static/mockups.html 2>/dev/null || xdg-open http://localhost:8000/static/mockups.html 2>/dev/null
        wait
        ;;
    import)
        echo "Import feature coming soon!"
        echo "This will convert your Rails/Django/Excel into DBBasic config"
        ;;
    *)
        echo "DBBasic - Replace 50,000 lines with 50"
        echo ""
        echo "Usage:"
        echo "  ./dbbasic serve     - Start the DBBasic server"
        echo "  ./dbbasic demo      - See the interactive demos"
        echo "  ./dbbasic import    - Import from Rails/Django/Excel (soon)"
        echo ""
        echo "Examples:"
        echo "  ./dbbasic serve examples/simple_crm.dbbasic"
        echo ""
        ;;
esac
EOF

chmod +x dbbasic

echo ""
echo "✨ Installation complete!"
echo ""
echo "🚀 Quick Start:"
echo "   ./dbbasic demo      # See what DBBasic can do"
echo "   ./dbbasic serve     # Start building"
echo ""
echo "📚 Examples in: examples/"
echo "📖 Documentation: README.md"
echo ""
echo "Welcome to the post-code era. 🎉"
echo "==============================================="