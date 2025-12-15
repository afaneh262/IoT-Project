#!/bin/bash
# Startup script for running Smart Home IoT Application in Docker
# Supports Linux and macOS

set -e

echo "=========================================="
echo "Smart Home IoT - Docker Startup"
echo "=========================================="
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "Detected OS: $MACHINE"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Docker
if ! command_exists docker; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker from https://www.docker.com/get-started"
    exit 1
fi

# Check Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose"
    exit 1
fi

echo "✓ Docker is installed"
echo "✓ Docker Compose is available"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
else
    echo "✓ .env file exists"
fi
echo ""

# Setup X11 for GUI
if [ "$MACHINE" = "Linux" ]; then
    echo "Setting up X11 for Linux..."
    
    # Allow X server connections
    xhost +local:docker >/dev/null 2>&1 || echo "⚠️  Warning: Could not run xhost (GUI may not work)"
    
    # Set DISPLAY if not set
    if [ -z "$DISPLAY" ]; then
        export DISPLAY=:0
    fi
    
    echo "✓ X11 configured for Linux"
    echo "  DISPLAY=$DISPLAY"
    
elif [ "$MACHINE" = "Mac" ]; then
    echo "Setting up X11 for macOS..."
    
    # Check if XQuartz is installed
    if [ ! -d "/Applications/Utilities/XQuartz.app" ] && [ ! -d "/Applications/XQuartz.app" ]; then
        echo "⚠️  Warning: XQuartz not found"
        echo "   For GUI support, install XQuartz from https://www.xquartz.org/"
        echo "   Then run: xhost + 127.0.0.1"
        echo ""
        echo "   Continuing without GUI support..."
    else
        # Get IP address
        IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
        if [ -z "$IP" ]; then
            IP="127.0.0.1"
        fi
        
        export DISPLAY="$IP:0"
        
        # Allow connections
        xhost + "$IP" >/dev/null 2>&1 || echo "⚠️  Warning: Could not run xhost (start XQuartz first)"
        
        echo "✓ X11 configured for macOS"
        echo "  DISPLAY=$DISPLAY"
        echo "  Make sure XQuartz is running!"
    fi
else
    echo "⚠️  Warning: Unknown OS - GUI may not work"
fi
echo ""

# Build and start containers
echo "Building and starting Docker containers..."
echo "This may take a few minutes on first run..."
echo ""

# Use docker compose or docker-compose based on availability
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Build the application
echo "Building application image..."
$COMPOSE_CMD build smart-home-app

# Start all services
echo ""
echo "Starting services..."
$COMPOSE_CMD up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to be ready..."
sleep 5

# Check service status
echo ""
echo "Service Status:"
$COMPOSE_CMD ps

echo ""
echo "=========================================="
echo "✓ Smart Home IoT Application Started!"
echo "=========================================="
echo ""
echo "Services:"
echo "  • Smart Home App: Running in container"
echo "  • MongoDB: http://localhost:27017"
echo "  • Mongo Express: http://localhost:8081 (admin/pass)"
echo ""
echo "To view logs:"
echo "  $COMPOSE_CMD logs -f smart-home-app"
echo ""
echo "To stop:"
echo "  $COMPOSE_CMD stop"
echo ""
echo "To stop and remove:"
echo "  $COMPOSE_CMD down"
echo ""

# Show application logs
echo "Application logs (Ctrl+C to exit):"
echo "=========================================="
$COMPOSE_CMD logs -f smart-home-app
