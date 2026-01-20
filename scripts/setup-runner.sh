#!/bin/bash

# GitHub Actions Self-Hosted Runner Setup Script
# Run this script on your server to set up the runner

set -e

echo "🚀 Setting up GitHub Actions Self-Hosted Runner for GymNow Backend"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root"
    exit 1
fi

# Variables
RUNNER_VERSION="2.311.0"
RUNNER_DIR="$HOME/actions-runner"
REPO_URL="https://github.com/YOUR_USERNAME/gym-now-back"

# Create runner directory
mkdir -p $RUNNER_DIR
cd $RUNNER_DIR

# Download runner
echo "📥 Downloading GitHub Actions Runner..."
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Extract runner
echo "📦 Extracting runner..."
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Install dependencies
echo "🔧 Installing dependencies..."
sudo ./bin/installdependencies.sh

# Configure runner (you'll need to provide token manually)
echo "⚙️  To configure the runner, run:"
echo "cd $RUNNER_DIR"
echo "./config.sh --url $REPO_URL --token YOUR_REGISTRATION_TOKEN"
echo ""
echo "Get your registration token from:"
echo "$REPO_URL/settings/actions/runners/new"
echo ""
echo "After configuration, install as service:"
echo "sudo ./svc.sh install"
echo "sudo ./svc.sh start"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "⚠️  Please log out and back in for Docker permissions to take effect"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install Python and pipenv if not present
if ! command -v python3.11 &> /dev/null; then
    echo "🐍 Installing Python 3.11..."
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3-pip
fi

if ! command -v pipenv &> /dev/null; then
    echo "📦 Installing pipenv..."
    pip3 install --user pipenv
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure the runner with your repository token"
echo "2. Install the runner as a service"
echo "3. Add required secrets to your GitHub repository"