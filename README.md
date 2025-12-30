# EOG Image Annotation Plugin

A native plugin for GNOME Image Viewer (Eye of GNOME / EOG) that provides comprehensive annotation tools for images.

## Features

- **Arrows**: Draw arrows with multiple styles (Standard, Open, Double, Small, Large)
- **Numbered Dots**: Place numbered counter dots for step-by-step annotations
- **Rectangle Tool**: Draw rectangles with adjustable line width
- **Circle Tool**: Draw circles with adjustable line width
- **Text Labels**: Add text annotations with formatting options (bold, italic, size)
- **Color Selection**: Choose annotation colors from a color picker
- **Line Width Control**: Adjustable line width (1px, 2px, 3px, 5px, 8px) for shapes
- **Undo/Redo**: Unlimited undo/redo history using memento pattern
- **Copy to Clipboard**: Copy the image with all annotations to clipboard
- **Save Annotated Image**: Save the original image with annotations (adds `-annotated` suffix)
- **Auto-Hide**: Toolbar automatically hides when zoomed in/out or in fullscreen mode
- **Smart Visibility**: Toolbar only appears at 100% zoom and when not in fullscreen

## Screenshots

The annotation toolbar integrates seamlessly into EOG's interface and provides all tools in a compact, icon-based toolbar.

## Requirements

- **OS**: Ubuntu 24.04 or similar GNOME-based Linux distribution
- **EOG**: Eye of GNOME image viewer (version 45+)
- **Python**: Python 3.6 or higher
- **Dependencies**:
  - `eog` - Eye of GNOME image viewer
  - `eog-dev` - EOG development headers (for Python bindings)
  - `python3-gi` - Python GObject Introspection bindings
  - `python3-gi-cairo` - Cairo bindings for Python
  - `gir1.2-gtk-3.0` - GTK+ 3.0 typelib
  - `gir1.2-rsvg-2.0` - librsvg bindings (optional, for custom icons)

## Installation

### Quick Install

1. **Install prerequisites**:
   ```bash
   sudo apt-get update
   sudo apt-get install eog eog-dev python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-rsvg-2.0
   ```

2. **Install the plugin**:
   ```bash
   ./install.sh
   ```

   Or manually:
   ```bash
   mkdir -p ~/.local/share/eog/plugins
   cp annotation.plugin ~/.local/share/eog/plugins/
   cp annotation.py ~/.local/share/eog/plugins/
   cp arrow-diagonal-symbolic.svg ~/.local/share/eog/plugins/ 2>/dev/null || true
   cp numbered-dot-symbolic.svg ~/.local/share/eog/plugins/ 2>/dev/null || true
   chmod +x ~/.local/share/eog/plugins/annotation.py
   ```

3. **Enable the plugin**:
   - Open EOG (Eye of GNOME)
   - Go to **Edit → Preferences → Plugins**
   - Check the box next to **Image Annotation Tool**
   - Close the preferences dialog
   - Restart EOG or open an image

## Usage

### Basic Workflow

1. **Open an image** in EOG
2. **Wait for 100% zoom** - The annotation toolbar will automatically appear when zoom is at 100% and not in fullscreen
3. **Select a tool** from the toolbar:
   - **Undo/Redo**: Navigate through annotation history
   - **Color Picker**: Select annotation color
   - **Line Width**: Choose line thickness (1px-8px)
   - **Arrow Tool**: Click start point, then click end point
   - **Arrow Style**: Select arrow head style
   - **Numbered Dot**: Click to place numbered dots (auto-increments)
   - **Rectangle**: Click bottom-left corner, then top-right corner
   - **Circle**: Click center, then edge point
   - **Text**: Click to open text dialog with formatting options
4. **Annotate your image** using the selected tools
5. **Save or copy** the annotated image using the toolbar buttons

### Tool Details

#### Arrow Tool
- **Usage**: Click once to set start point, move mouse to see preview, click again to finish
- **Styles**: Choose from 5 arrow head styles (Standard, Open, Double, Small, Large)
- **Line Width**: Adjustable from 1px to 8px

#### Numbered Dots
- **Usage**: Click anywhere on the image to place a numbered dot
- **Auto-numbering**: Numbers increment automatically (1, 2, 3, ...)
- **Color**: Uses selected color from color picker

#### Rectangle Tool
- **Usage**: Click bottom-left corner, move mouse to see preview, click top-right corner
- **Line Width**: Adjustable from 1px to 8px

#### Circle Tool
- **Usage**: Click center point, move mouse to see preview, click edge point
- **Line Width**: Adjustable from 1px to 8px

#### Text Tool
- **Usage**: Click on image to open text dialog
- **Features**:
  - Text input field
  - Bold checkbox
  - Italic checkbox
  - Font size selector (8-72pt)
  - Settings are remembered for next use

### Keyboard Shortcuts

- **Undo**: Click undo button (or use standard EOG shortcuts if available)
- **Redo**: Click redo button
- **Clear All**: Click clear button to remove all annotations

### Auto-Hide Behavior

The annotation toolbar automatically:
- **Hides** when:
  - Zoom level is not 100% (zoomed in or out)
  - Window is in fullscreen mode
- **Shows** when:
  - Zoom returns to 100%
  - Fullscreen mode is exited

This ensures annotations are only available when they make sense (at 100% zoom for accurate placement).

## File Structure

```
.
├── annotation.plugin          # Plugin metadata file
├── annotation.py              # Main plugin implementation
├── arrow-diagonal-symbolic.svg # Custom arrow icon
├── numbered-dot-symbolic.svg  # Custom numbered dot icon
├── install.sh                 # Installation script
├── README.md                  # This file
├── LICENSE                    # MIT License
└── .gitignore                # Git ignore file
```

## Troubleshooting

### Plugin doesn't appear in preferences

- Verify files are in `~/.local/share/eog/plugins/`
- Check that `annotation.plugin` and `annotation.py` have correct permissions
- Restart EOG completely after installation:
  ```bash
  pkill eog
  eog /path/to/image.png
  ```

### Toolbar doesn't appear

1. **Check zoom level**: Toolbar only appears at 100% zoom
2. **Check fullscreen**: Exit fullscreen mode if active
3. **Verify plugin is enabled**: Edit → Preferences → Plugins
4. **Check terminal output**: Start EOG from terminal to see debug messages:
   ```bash
   eog /path/to/image.png
   ```
   Look for messages starting with "EOG Annotation Plugin:"

### Import errors

If you see errors about missing EOG bindings:
```bash
sudo apt-get install eog eog-dev
```

The EOG Python bindings are included with the `eog` package. The plugin automatically locates them.

### Custom icons not showing

If the custom arrow or numbered dot icons don't appear:
```bash
sudo apt-get install gir1.2-rsvg-2.0
```

The plugin will fall back to theme icons if librsvg is not available.

### Annotations not visible

- Ensure you're at 100% zoom
- Check that a tool is selected (button should be highlighted)
- Verify the color is not the same as the image background
- Try using the "Clear All" button and start fresh

## Development

### Code Structure

- **`Annotation` class**: Represents individual annotations (arrow, dot, rectangle, circle, text)
- **`AnnotationManager` class**: Manages the collection of annotations and undo/redo stacks
- **`AnnotationToolbar` class**: Creates and manages the toolbar UI
- **`AnnotationPlugin` class**: Main plugin class that integrates with EOG

### Testing

1. Make changes to the plugin
2. Copy updated files to plugin directory:
   ```bash
   cp annotation.py ~/.local/share/eog/plugins/
   ```
3. Restart EOG - the plugin will reload automatically if already enabled

### Debugging

Start EOG from terminal to see debug output:
```bash
eog /path/to/image.png 2>&1 | grep "EOG Annotation Plugin"
```

## Contributing

Contributions are welcome! Please ensure:
- Code follows Python PEP 8 style guidelines
- New features maintain backward compatibility
- Documentation is updated for new features
- Test your changes before submitting

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Jan Sechovec**
- Website: flexer.cz

## Acknowledgments

- Built for GNOME/Ubuntu community
- Uses GTK+ 3.0, Cairo, and EOG plugin API
- Inspired by the need for simple, native image annotation tools
