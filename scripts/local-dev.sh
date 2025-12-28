#!/bin/bash
# Local development setup script

set -e

echo "🛠️  Setting up Real-Time Vision Platform for local development"
echo "=============================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

echo ""
echo -e "${BLUE}Installing backend dependencies...${NC}"

# API service
echo "Installing API service dependencies..."
cd backend/api
python3 -m pip install -r requirements.txt
cd ../..

# Streaming service
echo "Installing Streaming service dependencies..."
cd backend/streaming
python3 -m pip install -r requirements.txt
cd ../..

# Inference service
echo "Installing Inference service dependencies..."
cd backend/inference
python3 -m pip install -r requirements.txt
cd ../..

echo -e "${GREEN}✓ Backend dependencies installed${NC}"

echo ""
echo -e "${BLUE}Installing frontend dependencies...${NC}"
cd frontend
npm install
cd ..
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

echo ""
echo -e "${BLUE}Compiling protobuf definitions...${NC}"
cd backend/inference
chmod +x compile_protos.sh
./compile_protos.sh || echo "⚠️  Protobuf compilation skipped (grpc-tools may need to be installed)"
cd ../..

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo "To start development:"
echo ""
echo "Option 1: Docker Compose (recommended)"
echo "  docker-compose up"
echo ""
echo "Option 2: Individual services"
echo "  Terminal 1: cd backend/api && uvicorn main:app --reload"
echo "  Terminal 2: cd backend/streaming && python main.py"
echo "  Terminal 3: cd backend/inference && python server.py"
echo "  Terminal 4: cd frontend && npm run dev"
echo ""
echo "Access the app at: http://localhost:3000"

