#!/bin/bash

# Llama Stack Agent Chatbot Setup Script
# This script helps set up the environment for the Llama Stack Agent Chatbot

set -e

echo "🚀 Setting up Llama Stack Agent Chatbot..."
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ Error: pip is not installed. Please install pip."
    exit 1
fi

# Use pip3 if available, otherwise use pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

echo "✅ pip found: $PIP_CMD"

# Install requirements
echo ""
echo "📦 Installing Python dependencies..."
$PIP_CMD install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env configuration file..."
    cat > .env << 'EOF'
# Llama Stack Agent Chatbot Configuration
# Fill in your actual values

# Llama Stack Server Configuration
REMOTE_BASE_URL=https://llama-stack-example-llama-stack-example.apps.ocp.sandbox1951.opentlc.com
INFERENCE_MODEL_ID=llama-3-2-3b

# Client Configuration
LLAMA_STACK_API_TOKEN=
LLAMA_STACK_TIMEOUT=30
SKIP_SSL_VERIFY=false

# Sampling Parameters
TEMPERATURE=0.0
TOP_P=0.95
MAX_TOKENS=4096
STREAM=False

# API Keys for External Services
# Get your Tavily API key from https://tavily.com/
TAVILY_SEARCH_API_KEY=

# Get your Brave Search API key from https://api.search.brave.com/
BRAVE_SEARCH_API_KEY=

# OpenAI API key for enhanced features (optional)
OPENAI_API_KEY=

# MCP Server Endpoints
# OpenShift/Kubernetes MCP server endpoint
OPENSHIFT_MCP_URL=http://ocp-mcp-server:8000/sse

# Telemetry and Observability (Optional)
OTEL_SERVICE_NAME=llama-stack-chatbot
OTEL_TRACE_ENDPOINT=
SQLITE_DB_PATH=~/.llama/distributions/remote-vllm/trace_store.db
TELEMETRY_SINKS=console,sqlite
EOF
    echo "✅ Created .env file with default configuration"
else
    echo "ℹ️  .env file already exists, skipping creation"
fi

# Make the main script executable
chmod +x llama_agent_chatbot.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file and add your actual configuration values"
echo "2. Make sure your Llama Stack server is running at the configured URL"
echo "3. Run the chatbot with:"
echo "   python llama_agent_chatbot.py"
echo ""
echo "For the Kubernetes test query, run:"
echo "   python llama_agent_chatbot.py --test-kubernetes"
echo ""
echo "For more information, see the README.md file"
echo "=============================================="
