#!/usr/bin/env python3
"""
Test script to verify plugin can be loaded
Run this to check for import errors before loading in EOG

Usage:
    python3 test_plugin.py
"""

import os
import sys

# Set up EOG typelib path
eog_typelib_path = '/usr/lib/x86_64-linux-gnu/eog/girepository-1.0'
if os.path.exists(eog_typelib_path):
    typelib_path = os.environ.get('GI_TYPELIB_PATH', '')
    if eog_typelib_path not in typelib_path.split(':'):
        os.environ['GI_TYPELIB_PATH'] = f"{eog_typelib_path}:{typelib_path}" if typelib_path else eog_typelib_path

print("Testing EOG plugin imports...")
print("")

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Eog', '3.0')
    print("✓ GTK and EOG typelibs found")
    
    from gi.repository import GObject, Gtk, Eog, Gdk
    print("✓ GObject, GTK, EOG, Gdk imported successfully")
    
    import cairo
    import math
    import copy
    print("✓ Cairo, math, copy imported")
    
    # Try to import the plugin module
    # NOTE: This will fail with "must be an interface" error because
    # Eog.WindowActivatable can only load in EOG's context, not standalone
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import annotation
        print("✓ Plugin module imported successfully")
        print("\n✓ All imports successful! Plugin should work in EOG.")
    except TypeError as e:
        if "must be an interface" in str(e) or "interface" in str(e).lower():
            print("⚠ Expected error when testing standalone:")
            print("   TypeError: must be an interface")
            print("")
            print("✓ This is normal - the plugin will work when loaded by EOG")
            print("  Eog.WindowActivatable can only be loaded in EOG's context")
        else:
            raise
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        raise
    
    print("\n" + "="*50)
    print("To test in EOG:")
    print("1. Make sure plugin is installed: ~/.local/share/eog/plugins/")
    print("2. Enable plugin in EOG: Edit → Preferences → Plugins")
    print("3. Start EOG from terminal: eog /path/to/image.png")
    print("4. Look for 'EOG Annotation Plugin:' messages in terminal")
    print("   (if EOG_ANNOTATION_DEBUG=1 is set)")
    print("="*50)
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nPlease install missing dependencies:")
    print("  sudo apt-get install eog eog-dev python3-gi python3-gi-cairo gir1.2-gtk-3.0")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
