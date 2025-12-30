#!/bin/bash
# Installation script for EOG Image Annotation Plugin
# This script installs the plugin to the user's local EOG plugins directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$HOME/.local/share/eog/plugins"

echo "========================================="
echo "EOG Image Annotation Plugin Installer"
echo "========================================="
echo ""

# Check if EOG is installed
if ! command -v eog &> /dev/null; then
    echo "❌ Error: EOG (Eye of GNOME) is not installed."
    echo ""
    echo "Please install it with:"
    echo "  sudo apt-get install eog"
    exit 1
fi

echo "✓ EOG found"

# Check for required packages
echo ""
echo "Checking for required packages..."
MISSING_PACKAGES=""
OPTIONAL_PACKAGES=""

# Required packages
for pkg in python3-gi python3-gi-cairo gir1.2-gtk-3.0; do
    # Check if package is installed using dpkg-query (more reliable)
    if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
        MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
    fi
done

# Optional packages
if ! dpkg-query -W -f='${Status}' gir1.2-rsvg-2.0 2>/dev/null | grep -q "install ok installed"; then
    OPTIONAL_PACKAGES="$OPTIONAL_PACKAGES gir1.2-rsvg-2.0"
fi

if [ -n "$MISSING_PACKAGES" ]; then
    echo "❌ Missing required packages:"
    echo "  $MISSING_PACKAGES"
    echo ""
    echo "Install them with:"
    echo "  sudo apt-get install$MISSING_PACKAGES"
    exit 1
fi

if [ -n "$OPTIONAL_PACKAGES" ]; then
    echo "⚠ Optional package not installed (custom icons may not work):"
    echo "  $OPTIONAL_PACKAGES"
    echo "  Install with: sudo apt-get install$OPTIONAL_PACKAGES"
    echo ""
fi

echo "✓ All required packages found"

# Verify plugin files exist
if [ ! -f "$SCRIPT_DIR/annotation.plugin" ]; then
    echo "❌ Error: annotation.plugin not found in $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/annotation.py" ]; then
    echo "❌ Error: annotation.py not found in $SCRIPT_DIR"
    exit 1
fi

echo "✓ Plugin files found"

# Create plugin directory
mkdir -p "$PLUGIN_DIR"
echo "✓ Plugin directory ready: $PLUGIN_DIR"

# Copy plugin files
echo ""
echo "Installing plugin files..."
cp "$SCRIPT_DIR/annotation.plugin" "$PLUGIN_DIR/"
cp "$SCRIPT_DIR/annotation.py" "$PLUGIN_DIR/"

# Copy custom icons if they exist
if [ -f "$SCRIPT_DIR/arrow-diagonal-symbolic.svg" ]; then
    cp "$SCRIPT_DIR/arrow-diagonal-symbolic.svg" "$PLUGIN_DIR/"
    echo "✓ Custom arrow icon installed"
fi
if [ -f "$SCRIPT_DIR/numbered-dot-symbolic.svg" ]; then
    cp "$SCRIPT_DIR/numbered-dot-symbolic.svg" "$PLUGIN_DIR/"
    echo "✓ Custom numbered dot icon installed"
fi

# Make annotation.py executable
chmod +x "$PLUGIN_DIR/annotation.py"
echo "✓ Set executable permissions"

echo ""
echo "========================================="
echo "✅ Plugin installed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Open EOG (Eye of GNOME)"
echo "2. Go to Edit → Preferences → Plugins"
echo "3. Check the box next to 'Image Annotation Tool'"
echo "4. Close preferences and open an image"
echo "5. The toolbar will appear when zoom is at 100%"
echo ""
echo "Plugin location: $PLUGIN_DIR"
echo ""
echo "For help, see README.md"

