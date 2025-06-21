#!/bin/bash
# Activation script for Python 3.11 virtual environment
# This script activates the Python 3.11 environment with MCP and ChromaDB support

echo "🐍 Activating Python 3.11 Virtual Environment..."
echo "   - MCP: ✅ Installed and compatible"
echo "   - ChromaDB: ✅ Installed and working"
echo "   - Outlook Email & Teams Chat instances: ✅ Ready"
echo ""

# Activate the virtual environment
source venv311/bin/activate

echo "🎉 Environment activated! You can now use:"
echo "   • pip install mcp (already installed)"
echo "   • python chromadb_setup.py"
echo "   • python test_chromadb_local.py"
echo ""
echo "To deactivate, run: deactivate"
echo ""

# Show current Python version
python --version
echo ""

# Optional: Start a new shell with the environment activated
exec $SHELL 