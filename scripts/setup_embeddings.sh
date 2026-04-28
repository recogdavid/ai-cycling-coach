#!/bin/bash
# Setup script for embedding generation

echo "Setting up embedding generation environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Installing required packages..."
pip install psycopg2-binary requests python-dotenv tqdm

echo "Setup complete!"
echo ""
echo "To generate embeddings:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run: python scripts/generate_embeddings.py"
echo ""
echo "To deactivate virtual environment: deactivate"
