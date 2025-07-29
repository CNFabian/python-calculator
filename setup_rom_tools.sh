#!/bin/bash

# Create tools directory
mkdir -p ~/vanguard-translation/tools
cd ~/vanguard-translation/tools

echo "🔧 Setting up 3DS ROM tools for Mac..."

# Download 3DS ROM tools (these should work on Mac)
echo "📥 Downloading ctrtool..."
curl -L -o ctrtool "https://github.com/3DSGuy/Project_CTR/releases/download/ctrtool-v1.2.0/ctrtool-v1.2.0-macos_x86_64"
chmod +x ctrtool

echo "📥 Downloading makerom..."  
curl -L -o makerom "https://github.com/3DSGuy/Project_CTR/releases/download/makerom-v0.18.3/makerom-v0.18.3-macos_x86_64"
chmod +x makerom

echo "📥 Downloading 3dstool..."
curl -L -o 3dstool "https://github.com/dnasdw/3dstool/releases/download/v1.2.6/3dstool-macos"
chmod +x 3dstool

echo "✅ ROM tools installed!"
echo "🔍 Verifying tools..."
./ctrtool --help | head -3
./makerom --help | head -3  
./3dstool --help | head -3

echo "🎯 Tools ready in: $(pwd)"
ls -la