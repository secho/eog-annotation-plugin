#!/bin/bash
# Build script for eog-annotation-plugin .deb package

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Building eog-annotation-plugin .deb package"
echo "========================================="
echo ""

# Check for required build tools
REQUIRED_TOOLS="dpkg-buildpackage"
MISSING_TOOLS=""

for tool in $REQUIRED_TOOLS; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done

# Check for debhelper package
if ! dpkg -l | grep -q "^ii.*debhelper"; then
    MISSING_TOOLS="$MISSING_TOOLS debhelper"
fi

if [ -n "$MISSING_TOOLS" ]; then
    echo "❌ Missing required build tools:$MISSING_TOOLS"
    echo ""
    echo "Install them with:"
    echo "  sudo apt-get install build-essential devscripts debhelper"
    exit 1
fi

echo "✓ Build tools found"
echo ""

# Clean previous build artifacts
echo "Cleaning previous build artifacts..."
rm -rf ../eog-annotation-plugin_*.*.*_*.deb
rm -rf ../eog-annotation-plugin_*.*.*_*.buildinfo
rm -rf ../eog-annotation-plugin_*.*.*_*.changes
rm -rf debian/eog-annotation-plugin
rm -rf debian/.debhelper
rm -rf debian/files
rm -rf debian/debhelper.log
rm -rf debian/eog-annotation-plugin.substvars
echo "✓ Cleaned"
echo ""

# Build the package
echo "Building .deb package..."
echo ""

# Use dpkg-buildpackage to build the package
# -b = binary-only build (no source package)
# -uc = don't sign the .changes file
# -us = don't sign the source package
dpkg-buildpackage -b -uc -us

echo ""
echo "========================================="
echo "✅ Package built successfully!"
echo "========================================="
echo ""
echo "The .deb package can be found in the parent directory:"
echo "  ../eog-annotation-plugin_1.0.0-1_all.deb"
echo ""
echo "To install it:"
echo "  sudo dpkg -i ../eog-annotation-plugin_1.0.0-1_all.deb"
echo ""
echo "If there are dependency issues, run:"
echo "  sudo apt-get install -f"
echo ""

