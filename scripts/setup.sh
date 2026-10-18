#!/bin/bash
set -e

# Run from the repository root: ./scripts/setup.sh
cd "$(dirname "$0")/.."

MODEL="${OLLAMA_MODEL:-gemma3:4b}"

echo "🚀 Starting ZeroDay PS2 Setup..."

# 1. Environment Variables
echo "📝 Setting up environment..."
if [ ! -f .env ]; then
cat <<ENV > .env
LANGCHAIN_TRACING_V2=false
ANONYMIZED_TELEMETRY=false
OLLAMA_MODEL=${MODEL}
OLLAMA_BASE_URL=http://127.0.0.1:11434
ENV
fi
echo "NEXT_TELEMETRY_DISABLED=1" > apps/app/.env.local

# 2. Ollama Model Pull
if command -v ollama &> /dev/null; then
    echo "📦 Pulling Ollama model ${MODEL}..."
    ollama pull "${MODEL}"
else
    echo "❌ Ollama not found. Please install it from ollama.com"
    exit 1
fi

# 3. Backend Setup (Python 3.10+)
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r services/api/requirements.txt

# 4. Frontend Setup (Next.js)
echo "🌐 Installing frontend dependencies..."
(cd apps/app && npm install)

echo "✅ Setup complete!"
echo "   Backend:  source venv/bin/activate && python services/api/main.py"
echo "   Frontend: cd apps/app && npm run dev"
