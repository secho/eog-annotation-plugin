# Building the .deb Package

This document explains how to build the `.deb` package for eog-annotation-plugin.

## Prerequisites

Install the required build tools:

```bash
sudo apt-get install build-essential devscripts debhelper
```

## Building the Package

### Using the build script (recommended):

```bash
./build-deb.sh
```

This will:
1. Check for required build tools
2. Clean previous build artifacts
3. Build the `.deb` package

### Manual build:

```bash
dpkg-buildpackage -b -uc -us
```

Options:
- `-b`: Build binary-only package (no source package)
- `-uc`: Don't sign the .changes file
- `-us`: Don't sign the source package

## Installing the Package

After building, install the package:

```bash
sudo dpkg -i ../eog-annotation-plugin_1.0.0-1_all.deb
```

If there are dependency issues, fix them with:

```bash
sudo apt-get install -f
```

## Package Contents

The package installs the following files to `/usr/share/eog/plugins/`:
- `annotation.py` - Main plugin code
- `annotation.plugin` - Plugin metadata
- `arrow-diagonal-symbolic.svg` - Custom arrow icon
- `numbered-dot-symbolic.svg` - Custom numbered dot icon

## Dependencies

The package depends on:
- `eog` - Eye of GNOME image viewer
- `python3-gi` - Python GObject Introspection bindings
- `python3-gi-cairo` - Cairo bindings for Python
- `gir1.2-gtk-3.0` - GTK+ 3.0 typelib
- `gir1.2-rsvg-2.0` - librsvg bindings (for custom icons)

These dependencies will be automatically installed when installing the package.

## Enabling the Plugin

After installation:
1. Open EOG (Eye of GNOME)
2. Go to **Edit → Preferences → Plugins**
3. Check the box next to **Image Annotation Tool**
4. Close preferences and open an image
5. The toolbar will appear when zoom is at 100%

## Package Structure

The Debian package structure:
```
debian/
├── changelog      # Package version history
├── compat         # debhelper compatibility level
├── control        # Package metadata and dependencies
├── copyright      # License information
├── install        # File installation mapping
├── rules          # Build rules
└── source/
    └── format     # Source package format
```


