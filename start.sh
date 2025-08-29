#!/bin/bash

# AI Local Chat Bot - Setup and Start Script

set -e

clear

echo "🚀 AI Local Chat Bot - Setup and Start"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Pull latest images
echo "🔄 Pulling Docker images..."
docker-compose pull

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."

# Wait for Ollama to be ready
echo "🔄 Waiting for Ollama..."
max_attempts=5
attempt=0
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ Ollama failed to start after $max_attempts attempts"
        echo "🔍 Checking Ollama logs:"
        docker-compose logs ollama
        exit 1
    fi
    sleep 3
    echo "   Still waiting for Ollama... (attempt $attempt/$max_attempts)"
done
echo "✅ Ollama is ready"

# Wait for qdrant to be ready
echo "🔄 Waiting for Qdrant..."
max_attempts=5
attempt=0
until curl -s http://localhost:6333/collections > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ Qdrant failed to start after $max_attempts attempts"
        echo "🔍 Checking Qdrant logs:"
        docker-compose logs qdrant
        exit 1
    fi
    sleep 3
    echo "   Still waiting for Qdrant... (attempt $attempt/$max_attempts)"
done
echo "✅ Qdrant is ready"

# Wait for n8n to be ready
echo "🔄 Waiting for n8n..."
max_attempts=5
attempt=0
until curl -s http://localhost:5678 > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ n8n failed to start after $max_attempts attempts"
        echo "🔍 Checking n8n logs:"
        docker-compose logs n8n
        exit 1
    fi
    sleep 3
    echo "   Still waiting for n8n... (attempt $attempt/$max_attempts)"
done
echo "✅ n8n is ready"

# Pull the AI model
echo "🤖 Pulling AI model (this may take a few minutes)..."
if ! docker-compose exec -T ollama ollama pull llama3.2; then
    echo "❌ Failed to pull llama3.2"
    exit 1
fi

# Pull the Embedding
echo "🤖 Pulling AI model (this may take a few minutes)..."
if ! docker-compose exec -T ollama ollama pull mxbai-embed-large; then
    echo "❌ Failed to pull mxbai-embed-large"
    exit 1
fi

echo ""
echo "🎉 AI Local Chat Bot is now running!"
echo ""
echo "> n8n: http://localhost:5678"
echo "> Ollama: http://localhost:11434"
echo "> Qdrant: http://localhost:6333"
echo ""
echo "➡️ Access n8n UI"
echo "    - Open http://localhost:5678 in your browser."
echo "    - Sign up for the first time."
echo ""
echo "➡️ n8n Workflows"
echo "    - The workflow in 'n8n-workflows/ai-chat-assistant.json' handles PDF ingestion and chat bot."
echo "    - Import it via UI to make use of it."
echo ""
echo "➡️ (optional) To download Confluence documents as PDFs, follow the prompts or set these environment variables:"
echo "    - CONFLUENCE_URL"
echo "    - CONFLUENCE_USERNAME"
echo "    - CONFLUENCE_API_TOKEN"
echo "    - CONFLUENCE_SPACE_KEY"
echo "  And then run:"
echo "    cd helper-scripts"
echo "    pip install -r requirements.txt"
echo "    python confluence_pdf_downloader.py"
echo ""
echo "➡️ Data Ingestion"
echo "    - Upload PDFs via the n8n form trigger from the n8n UI appeared after workflow import."
echo ""
echo "➡️ Ask"
echo "    - Ask your question to the chat bot and wait for the answer."
echo ""
echo "📖 For detailed instructions, see README.md"
echo ""
echo "🛑 To stop the application: docker-compose down"
echo "🔄 To view logs: docker-compose logs -f"
