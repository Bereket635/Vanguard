#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    python -m venv .venv
fi
source .venv/bin/activate

# Skip install if everything's already importable
if ! python -c "import flask, sqlalchemy, networkx, yaml" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet flask sqlalchemy networkx pyyaml
fi

echo "Vanguard running on http://127.0.0.1:8000"
echo "Open that URL in your browser. Ctrl+C to stop."
exec python -c "from backend.main import run; run()"
