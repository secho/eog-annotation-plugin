#!/usr/bin/env python3
"""
EOG Image Annotation Plugin

A plugin for Eye of GNOME (EOG) image viewer that provides annotation tools
for images including arrows, numbered dots, rectangles, circles, and text labels.

Features:
- Arrow tool with multiple styles
- Numbered counter dots
- Rectangle and circle drawing tools
- Text annotations with formatting (bold, italic, size)
- Color selection
- Line width control
- Undo/redo with unlimited history
- Copy to clipboard
- Save annotated images
- Auto-hide when zoomed or in fullscreen mode

Author: Jan Sechovec
Copyright: Copyright © 2025
License: MIT (see LICENSE file)
"""

import os
import sys
import copy
import math
import cairo
import traceback

# Debug mode - set to False to disable debug output
DEBUG = os.environ.get('EOG_ANNOTATION_DEBUG', '0') == '1'

def debug_print(message):
    """Print debug message if debug mode is enabled"""
    if DEBUG:
        print(f"EOG Annotation Plugin: {message}", file=sys.stderr)

# Add EOG typelib path if not already in GI_TYPELIB_PATH
# EOG typelib is typically in /usr/lib/x86_64-linux-gnu/eog/girepository-1.0
eog_typelib_path = '/usr/lib/x86_64-linux-gnu/eog/girepository-1.0'
if os.path.exists(eog_typelib_path):
    typelib_path = os.environ.get('GI_TYPELIB_PATH', '')
    if eog_typelib_path not in typelib_path.split(':'):
        os.environ['GI_TYPELIB_PATH'] = f"{eog_typelib_path}:{typelib_path}" if typelib_path else eog_typelib_path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Eog', '3.0')
from gi.repository import GObject, Gtk, Eog, Gdk, GdkPixbuf, GLib, Gio

class Annotation:
    """
    Represents a single annotation on an image.
    
    Attributes:
        tool_type: Type of annotation ('arrow', 'dot', 'rectangle', 'circle', 'text')
        x1, y1: First point coordinates
        x2, y2: Second point coordinates (for shapes)
        color: RGB color tuple (0.0-1.0 range)
        text: Text content (for text annotations)
        text_bold: Whether text is bold
        text_italic: Whether text is italic
        text_size: Font size in points
        line_width: Line width in pixels
        arrow_style: Arrow head style (0-4)
        counter: Number for numbered dots
    """
    def __init__(self, tool_type, x1, y1, x2=None, y2=None, color=(0.0, 0.0, 1.0), text="", 
                 text_bold=False, text_italic=False, text_size=14.0, line_width=2.0, arrow_style=0):
        self.tool_type = tool_type  # 'arrow', 'dot', 'rectangle', 'circle', 'text'
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color = color
        self.text = text
        self.counter = None  # For numbered dots
        # Text formatting
        self.text_bold = text_bold
        self.text_italic = text_italic
        self.text_size = text_size
        # Line properties
        self.line_width = line_width
        self.arrow_style = arrow_style  # 0-4 for different arrow head styles
        
    def draw(self, cr, scale_x=1.0, scale_y=1.0):
        """Draw the annotation on the Cairo context"""
        cr.set_source_rgb(*self.color)
        # Use stored line width, default to 2.0 if not set
        line_width = getattr(self, 'line_width', 2.0)
        cr.set_line_width(line_width)
        
        if self.tool_type == 'arrow':
            self._draw_arrow(cr, scale_x, scale_y)
        elif self.tool_type == 'dot':
            self._draw_dot(cr, scale_x, scale_y)
        elif self.tool_type == 'rectangle':
            self._draw_rectangle(cr, scale_x, scale_y)
        elif self.tool_type == 'circle':
            self._draw_circle(cr, scale_x, scale_y)
        elif self.tool_type == 'text':
            self._draw_text(cr, scale_x, scale_y)
    
    def _draw_arrow(self, cr, scale_x, scale_y):
        if self.x2 is None or self.y2 is None:
            return
            
        x1, y1 = self.x1 * scale_x, self.y1 * scale_y
        x2, y2 = self.x2 * scale_x, self.y2 * scale_y
        
        # Set color for both line and arrowhead
        cr.set_source_rgb(*self.color)
        line_width = getattr(self, 'line_width', 2.0)
        cr.set_line_width(line_width)
        
        # Draw line first
        cr.move_to(x1, y1)
        cr.line_to(x2, y2)
        cr.stroke()
        
        # Draw arrowhead based on style
        arrow_style = getattr(self, 'arrow_style', 0)
        angle = math.atan2(y2 - y1, x2 - x1)
        
        if arrow_style == 0:  # Standard filled triangle
            arrow_len = 15.0
            arrow_angle = math.pi / 6  # 30 degrees
            x3 = x2 - arrow_len * math.cos(angle - arrow_angle)
            y3 = y2 - arrow_len * math.sin(angle - arrow_angle)
            x4 = x2 - arrow_len * math.cos(angle + arrow_angle)
            y4 = y2 - arrow_len * math.sin(angle + arrow_angle)
            cr.move_to(x2, y2)
            cr.line_to(x3, y3)
            cr.line_to(x4, y4)
            cr.close_path()
            cr.fill()
        elif arrow_style == 1:  # Open triangle (outlined)
            arrow_len = 15.0
            arrow_angle = math.pi / 6
            x3 = x2 - arrow_len * math.cos(angle - arrow_angle)
            y3 = y2 - arrow_len * math.sin(angle - arrow_angle)
            x4 = x2 - arrow_len * math.cos(angle + arrow_angle)
            y4 = y2 - arrow_len * math.sin(angle + arrow_angle)
            cr.move_to(x3, y3)
            cr.line_to(x2, y2)
            cr.line_to(x4, y4)
            cr.stroke()
        elif arrow_style == 2:  # Double line (barbed)
            arrow_len = 12.0
            arrow_angle = math.pi / 5  # 36 degrees
            x3 = x2 - arrow_len * math.cos(angle - arrow_angle)
            y3 = y2 - arrow_len * math.sin(angle - arrow_angle)
            x4 = x2 - arrow_len * math.cos(angle + arrow_angle)
            y4 = y2 - arrow_len * math.sin(angle + arrow_angle)
            cr.move_to(x2, y2)
            cr.line_to(x3, y3)
            cr.stroke()
            cr.move_to(x2, y2)
            cr.line_to(x4, y4)
            cr.stroke()
        elif arrow_style == 3:  # Small filled
            arrow_len = 10.0
            arrow_angle = math.pi / 4  # 45 degrees
            x3 = x2 - arrow_len * math.cos(angle - arrow_angle)
            y3 = y2 - arrow_len * math.sin(angle - arrow_angle)
            x4 = x2 - arrow_len * math.cos(angle + arrow_angle)
            y4 = y2 - arrow_len * math.sin(angle + arrow_angle)
            cr.move_to(x2, y2)
            cr.line_to(x3, y3)
            cr.line_to(x4, y4)
            cr.close_path()
            cr.fill()
        elif arrow_style == 4:  # Large filled
            arrow_len = 20.0
            arrow_angle = math.pi / 7  # ~25.7 degrees
            x3 = x2 - arrow_len * math.cos(angle - arrow_angle)
            y3 = y2 - arrow_len * math.sin(angle - arrow_angle)
            x4 = x2 - arrow_len * math.cos(angle + arrow_angle)
            y4 = y2 - arrow_len * math.sin(angle + arrow_angle)
            cr.move_to(x2, y2)
            cr.line_to(x3, y3)
            cr.line_to(x4, y4)
            cr.close_path()
            cr.fill()
    
    def _draw_dot(self, cr, scale_x, scale_y):
        x, y = self.x1 * scale_x, self.y1 * scale_y
        radius = 15.0
        
        # Draw circle
        cr.arc(x, y, radius, 0, 2 * math.pi)
        cr.fill()
        
        # Draw number
        if self.counter is not None:
            cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(14.0)
            text = str(self.counter)
            
            # Center text
            extents = cr.text_extents(text)
            tx = x - (extents.width / 2 + extents.x_bearing)
            ty = y - (extents.height / 2 + extents.y_bearing)
            cr.move_to(tx, ty)
            cr.show_text(text)
    
    def _draw_rectangle(self, cr, scale_x, scale_y):
        """Draw rectangle - x1,y1 is bottom-left, x2,y2 is top-right"""
        if self.x2 is None or self.y2 is None:
            return
            
        x1 = min(self.x1, self.x2) * scale_x
        y1 = min(self.y1, self.y2) * scale_y
        x2 = max(self.x1, self.x2) * scale_x
        y2 = max(self.y1, self.y2) * scale_y
        
        width = x2 - x1
        height = y2 - y1
        
        cr.rectangle(x1, y1, width, height)
        cr.stroke()
    
    def _draw_circle(self, cr, scale_x, scale_y):
        """Draw circle - x1,y1 is center, x2,y2 determines radius"""
        if self.x2 is None or self.y2 is None:
            return
            
        cx = self.x1 * scale_x
        cy = self.y1 * scale_y
        # Calculate radius from center to second point
        dx = (self.x2 - self.x1) * scale_x
        dy = (self.y2 - self.y1) * scale_y
        radius = math.sqrt(dx * dx + dy * dy)
        
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.stroke()
    
    def _draw_text(self, cr, scale_x, scale_y):
        if not self.text:
            return
            
        x, y = self.x1 * scale_x, self.y1 * scale_y
        
        # Set font style based on annotation properties
        slant = cairo.FONT_SLANT_ITALIC if self.text_italic else cairo.FONT_SLANT_NORMAL
        weight = cairo.FONT_WEIGHT_BOLD if self.text_bold else cairo.FONT_WEIGHT_NORMAL
        font_size = self.text_size * scale_x  # Scale font size
        
        # Draw text background
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)
        cr.select_font_face("Sans", slant, weight)
        cr.set_font_size(font_size)
        extents = cr.text_extents(self.text)
        padding = 5.0
        cr.rectangle(
            x + extents.x_bearing - padding,
            y + extents.y_bearing - padding,
            extents.width + 2 * padding,
            extents.height + 2 * padding
        )
        cr.fill()
        
        # Draw text
        cr.set_source_rgb(*self.color)
        cr.select_font_face("Sans", slant, weight)
        cr.set_font_size(font_size)
        cr.move_to(x, y)
        cr.show_text(self.text)


class AnnotationManager:
    """Manages annotations and drawing with undo/redo support"""
    
    def __init__(self):
        self.annotations = []
        self.current_annotation = None
        self.draw_handler_id = None
        self.view = None
        # Undo/redo stacks (memento pattern)
        self.undo_stack = []  # Stack of previous states
        self.redo_stack = []  # Stack of states to redo
        self.max_history = 0  # 0 = unlimited
        
    def set_view(self, view):
        """Set the view widget to draw on"""
        import sys
        if self.draw_handler_id and self.view:
            self.view.disconnect(self.draw_handler_id)
        
        self.view = view
        if view:
            # Connect to draw signal to overlay annotations
            self.draw_handler_id = view.connect_after("draw", self._on_view_draw)
            debug_print(f"Connected draw handler (id={self.draw_handler_id})")
    
    def _on_view_draw(self, widget, cr):
        """Draw annotations overlay on the view"""
        try:
            # Draw all completed annotations
            for annotation in self.annotations:
                annotation.draw(cr, 1.0, 1.0)
            
            # Draw current annotation being created
            if self.current_annotation:
                self.current_annotation.draw(cr, 1.0, 1.0)
            
            # Draw shape preview if we have a start point (waiting for second click)
            if hasattr(self, 'plugin') and self.plugin and hasattr(self.plugin, 'shape_start_point') and self.plugin.shape_start_point and hasattr(self.plugin, 'shape_preview_end') and self.plugin.shape_preview_end and hasattr(self.plugin, 'shape_type') and self.plugin.shape_type:
                x1, y1 = self.plugin.shape_start_point
                x2, y2 = self.plugin.shape_preview_end
                # Get current color and settings from toolbar
                color = (0.0, 0.0, 1.0)  # Default blue
                line_width = 2.0
                arrow_style = 0
                if hasattr(self.plugin, 'toolbar') and self.plugin.toolbar:
                    color = self.plugin.toolbar.current_color
                    line_width = self.plugin.toolbar.current_line_width
                    if self.plugin.shape_type == "arrow":
                        arrow_style = self.plugin.toolbar.current_arrow_style
                
                # Draw preview shape (temporary annotation)
                temp_shape = Annotation(self.plugin.shape_type, x1, y1, x2, y2, color,
                                      line_width=line_width, arrow_style=arrow_style)
                temp_shape.draw(cr, 1.0, 1.0)
        except Exception as e:
            debug_print(f"Error in draw: {e}")
        
        return False  # Let other handlers process the draw event too
    
    def _save_state(self):
        """Save current state to undo stack (memento)"""
        # Deep copy the annotations list
        state = copy.deepcopy(self.annotations)
        self.undo_stack.append(state)
        # Clear redo stack when a new action is performed
        self.redo_stack = []
        # Limit undo stack size if needed (0 = unlimited)
        if self.max_history > 0 and len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
    
    def _restore_state(self, state):
        """Restore annotations from a saved state"""
        self.annotations = copy.deepcopy(state)
        if self.view:
            self.view.queue_draw()
    
    def can_undo(self):
        """Check if undo is possible"""
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """Check if redo is possible"""
        return len(self.redo_stack) > 0
    
    def undo(self):
        """Undo the last action"""
        if not self.can_undo():
            return False
        
        # Save current state to redo stack
        current_state = copy.deepcopy(self.annotations)
        self.redo_stack.append(current_state)
        
        # Restore previous state
        previous_state = self.undo_stack.pop()
        self._restore_state(previous_state)
        return True
    
    def redo(self):
        """Redo the last undone action"""
        if not self.can_redo():
            return False
        
        # Save current state to undo stack
        current_state = copy.deepcopy(self.annotations)
        self.undo_stack.append(current_state)
        
        # Restore redo state
        redo_state = self.redo_stack.pop()
        self._restore_state(redo_state)
        return True
    
    def add_annotation(self, annotation):
        """Add a completed annotation"""
        # Save state before adding
        self._save_state()
        self.annotations.append(annotation)
        if self.view:
            self.view.queue_draw()
    
    def clear(self):
        """Clear all annotations"""
        # Save state before clearing
        self._save_state()
        self.annotations = []
        self.current_annotation = None
        if self.view:
            self.view.queue_draw()


class AnnotationToolbar(Gtk.Toolbar):
    """
    Toolbar widget containing all annotation tools and controls.
    
    Provides:
    - Undo/redo buttons
    - Color picker
    - Line width selector
    - Arrow style selector
    - Annotation tool buttons (arrow, dot, rectangle, circle, text)
    - Action buttons (clear, copy, save)
    """
    
    __gsignals__ = {
        'tool-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'color-changed': (GObject.SignalFlags.RUN_FIRST, None, (float, float, float,)),
        'line-width-changed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'arrow-style-changed': (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        'undo-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'redo-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'clear-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'copy-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'save-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self):
        super().__init__()
        self.current_tool = None
        self.current_color = (0.0, 0.0, 1.0)  # Blue by default
        # Make toolbar more compact
        self.set_style(Gtk.ToolbarStyle.ICONS)
        
        # Set toolbar icon size to make it smaller
        self.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        
        # Undo button (at the very beginning)
        self.undo_btn = Gtk.ToolButton.new()
        self.undo_btn.set_icon_name("edit-undo-symbolic")
        self.undo_btn.set_tooltip_text("Undo")
        self.undo_btn.set_sensitive(False)  # Initially disabled
        self.undo_btn.connect("clicked", self._on_undo_clicked)
        self.insert(self.undo_btn, -1)
        
        # Redo button (right after undo)
        self.redo_btn = Gtk.ToolButton.new()
        self.redo_btn.set_icon_name("edit-redo-symbolic")
        self.redo_btn.set_tooltip_text("Redo")
        self.redo_btn.set_sensitive(False)  # Initially disabled
        self.redo_btn.connect("clicked", self._on_redo_clicked)
        self.insert(self.redo_btn, -1)
        
        # Separator after undo/redo
        separator = Gtk.SeparatorToolItem.new()
        self.insert(separator, -1)
        
        # Color button - move to beginning with square icon representation
        color_btn = Gtk.ColorButton.new()
        color_btn.set_rgba(Gdk.RGBA(0.0, 0.0, 1.0, 1.0))
        color_btn.set_tooltip_text("Annotation Color")
        color_btn.set_size_request(24, 24)  # Smaller color button
        color_btn.connect("color-set", self._on_color_changed)
        color_item = Gtk.ToolItem.new()
        color_item.add(color_btn)
        self.insert(color_item, -1)
        
        # Line width selector (combobox)
        self.line_width_store = Gtk.ListStore(int, str)
        widths = [(1, "1px"), (2, "2px"), (3, "3px"), (5, "5px"), (8, "8px")]
        for w, label in widths:
            self.line_width_store.append([w, label])
        
        self.line_width_combo = Gtk.ComboBox.new_with_model(self.line_width_store)
        renderer = Gtk.CellRendererText()
        self.line_width_combo.pack_start(renderer, True)
        self.line_width_combo.add_attribute(renderer, "text", 1)
        self.line_width_combo.set_active(1)  # Default to 2px
        self.line_width_combo.set_tooltip_text("Line Width")
        self.line_width_combo.connect("changed", self._on_line_width_changed)
        self.current_line_width = 2.0  # Default
        width_item = Gtk.ToolItem.new()
        width_item.add(self.line_width_combo)
        self.insert(width_item, -1)
        
        # Separator
        separator = Gtk.SeparatorToolItem.new()
        self.insert(separator, -1)
        
        # Arrow tool - diagonal arrow with arrowhead (custom icon)
        arrow_btn = Gtk.ToggleToolButton.new()
        # Try to load custom diagonal arrow icon, fallback to theme icon
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        custom_arrow_icon = os.path.join(plugin_dir, "arrow-diagonal-symbolic.svg")
        icon_loaded = False
        if os.path.exists(custom_arrow_icon):
            try:
                # Try to use rsvg to render SVG to pixbuf
                try:
                    gi.require_version('Rsvg', '2.0')
                    from gi.repository import Rsvg
                    # Render SVG to pixbuf at appropriate size
                    size = 16  # Small toolbar icon size
                    handle = Rsvg.Handle.new_from_file(custom_arrow_icon)
                    pixbuf = handle.get_pixbuf()
                    # Scale to desired size if needed
                    if pixbuf.get_width() != size or pixbuf.get_height() != size:
                        scaled_pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
                    else:
                        scaled_pixbuf = pixbuf
                    arrow_image = Gtk.Image.new_from_pixbuf(scaled_pixbuf)
                    arrow_btn.set_icon_widget(arrow_image)
                    icon_loaded = True
                except Exception as e:
                    # Fallback to theme icon if rsvg fails
                    pass
            except Exception as e:
                # Fallback to theme icon if custom icon fails
                pass
        if not icon_loaded:
            # Fallback to theme icon
            arrow_btn.set_icon_name("go-bottom-right-symbolic")
        arrow_btn.set_tooltip_text("Arrow Tool (click start, then click end)")
        self.insert(arrow_btn, -1)
        
        # Arrow style selector (combobox)
        self.arrow_style_store = Gtk.ListStore(int, str)
        styles = [(0, "Standard"), (1, "Open"), (2, "Double"), (3, "Small"), (4, "Large")]
        for s, label in styles:
            self.arrow_style_store.append([s, label])
        
        self.arrow_style_combo = Gtk.ComboBox.new_with_model(self.arrow_style_store)
        renderer = Gtk.CellRendererText()
        self.arrow_style_combo.pack_start(renderer, True)
        self.arrow_style_combo.add_attribute(renderer, "text", 1)
        self.arrow_style_combo.set_active(0)  # Default to Standard
        self.arrow_style_combo.set_tooltip_text("Arrow Style")
        self.arrow_style_combo.connect("changed", self._on_arrow_style_changed)
        self.current_arrow_style = 0  # Default
        arrow_style_item = Gtk.ToolItem.new()
        arrow_style_item.add(self.arrow_style_combo)
        self.insert(arrow_style_item, -1)
        
        # Counter dot tool (numbered dots) - custom circle with number icon
        dot_btn = Gtk.ToggleToolButton.new()
        # Try to load custom numbered dot icon, fallback to theme icon
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        custom_dot_icon = os.path.join(plugin_dir, "numbered-dot-symbolic.svg")
        icon_loaded = False
        if os.path.exists(custom_dot_icon):
            try:
                # Try to use rsvg to render SVG to pixbuf
                try:
                    gi.require_version('Rsvg', '2.0')
                    from gi.repository import Rsvg
                    # Render SVG to pixbuf at appropriate size
                    size = 16  # Small toolbar icon size
                    handle = Rsvg.Handle.new_from_file(custom_dot_icon)
                    pixbuf = handle.get_pixbuf()
                    # Scale to desired size if needed
                    if pixbuf.get_width() != size or pixbuf.get_height() != size:
                        scaled_pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
                    else:
                        scaled_pixbuf = pixbuf
                    dot_image = Gtk.Image.new_from_pixbuf(scaled_pixbuf)
                    dot_btn.set_icon_widget(dot_image)
                    icon_loaded = True
                except Exception as e:
                    # Fallback to theme icon if rsvg fails
                    pass
            except Exception as e:
                # Fallback to theme icon if custom icon fails
                pass
        if not icon_loaded:
            # Fallback to theme icon
            dot_btn.set_icon_name("format-list-numbered-symbolic")
        dot_btn.set_tooltip_text("Numbered Dot Tool (click to place)")
        self.insert(dot_btn, -1)
        
        # Rectangle tool - flat square (similar to circle icon)
        rect_btn = Gtk.ToggleToolButton.new()
        # Use checkbox icon style for flat square - try checkbox-symbolic or similar
        # Since radio-symbolic works for circle, try checkbox-symbolic for square
        rect_btn.set_icon_name("checkbox-symbolic")  # Flat square/rectangle (checkbox style)
        rect_btn.set_tooltip_text("Rectangle Tool (click bottom-left, then top-right)")
        self.insert(rect_btn, -1)
        
        # Circle tool - plain 2D circle
        circle_btn = Gtk.ToggleToolButton.new()
        # Use radio button icon as it's a plain circle outline
        circle_btn.set_icon_name("radio-symbolic")  # Radio button (plain circle)
        circle_btn.set_tooltip_text("Circle Tool (click center, then edge)")
        self.insert(circle_btn, -1)
        
        # Text tool - Aa letters icon
        text_btn = Gtk.ToggleToolButton.new()
        text_btn.set_icon_name("format-text-bold-symbolic")  # Aa letters
        text_btn.set_tooltip_text("Text Tool (click to add text)")
        self.insert(text_btn, -1)
        
        # Separator
        separator = Gtk.SeparatorToolItem.new()
        self.insert(separator, -1)
        
        # Clear button
        clear_btn = Gtk.ToolButton.new()
        clear_btn.set_icon_name("edit-clear-all-symbolic")
        clear_btn.set_tooltip_text("Clear All Annotations")
        clear_btn.connect("clicked", self._on_clear_clicked)
        self.insert(clear_btn, -1)
        
        # Separator
        separator = Gtk.SeparatorToolItem.new()
        self.insert(separator, -1)
        
        # Copy to clipboard button
        copy_btn = Gtk.ToolButton.new()
        copy_btn.set_icon_name("edit-copy-symbolic")
        copy_btn.set_tooltip_text("Copy Image with Annotations to Clipboard")
        copy_btn.connect("clicked", self._on_copy_clicked)
        self.insert(copy_btn, -1)
        
        # Save image button
        save_btn = Gtk.ToolButton.new()
        save_btn.set_icon_name("document-save-symbolic")
        save_btn.set_tooltip_text("Save Image with Annotations")
        save_btn.connect("clicked", self._on_save_clicked)
        self.insert(save_btn, -1)
        
        # Group toggle buttons - in GTK 3, we manually manage exclusivity
        # Store tool names with buttons
        self.tool_buttons = {
            "arrow": arrow_btn,
            "dot": dot_btn,
            "rectangle": rect_btn,
            "circle": circle_btn,
            "text": text_btn
        }
        
        # Connect each button with its tool name
        for tool_name, btn in self.tool_buttons.items():
            btn.connect("toggled", self._on_any_tool_toggled, tool_name)
    
    def _on_any_tool_toggled(self, button, tool_name):
        """Handle any tool button being toggled - ensures only one is active"""
        if button.get_active():
            # Deactivate all other buttons
            for name, btn in self.tool_buttons.items():
                if name != tool_name and btn.get_active():
                    btn.set_active(False)
            # Set current tool
            self.current_tool = tool_name
            self.emit("tool-changed", tool_name)
        else:
            # If all buttons are inactive, clear tool
            if not any(btn.get_active() for btn in self.tool_buttons.values()):
                self.current_tool = None
                self.emit("tool-changed", "")
    
    def _on_undo_clicked(self, button):
        """Handle undo button click"""
        self.emit("undo-clicked")
    
    def _on_redo_clicked(self, button):
        """Handle redo button click"""
        self.emit("redo-clicked")
    
    def update_undo_redo_state(self, can_undo, can_redo):
        """Update undo/redo button states"""
        self.undo_btn.set_sensitive(can_undo)
        self.redo_btn.set_sensitive(can_redo)
    
    def _on_color_changed(self, button):
        rgba = button.get_rgba()
        self.current_color = (rgba.red, rgba.green, rgba.blue)
        self.emit("color-changed", *self.current_color)
    
    def _on_line_width_changed(self, combo):
        """Handle line width change"""
        tree_iter = combo.get_active_iter()
        if tree_iter:
            model = combo.get_model()
            width = model[tree_iter][0]
            self.current_line_width = float(width)
            self.emit("line-width-changed", self.current_line_width)
    
    def _on_arrow_style_changed(self, combo):
        """Handle arrow style change"""
        tree_iter = combo.get_active_iter()
        if tree_iter:
            model = combo.get_model()
            style = model[tree_iter][0]
            self.current_arrow_style = style
            self.emit("arrow-style-changed", self.current_arrow_style)
    
    def _on_clear_clicked(self, button):
        self.emit("clear-clicked")
    
    def _on_copy_clicked(self, button):
        self.emit("copy-clicked")
    
    def _on_save_clicked(self, button):
        self.emit("save-clicked")


class AnnotationPlugin(GObject.Object, Eog.WindowActivatable):
    """Main plugin class
    
    Note: This class uses Eog.WindowActivatable interface which may only
    be properly available when loaded by EOG itself, not in standalone testing.
    """
    
    __gtype_name__ = 'AnnotationPlugin'
    window = GObject.Property(type=Eog.Window)
    
    def __init__(self):
        GObject.Object.__init__(self)
        self.toolbar = None
        self.annotation_manager = AnnotationManager()
        self.current_annotation = None
        self.drawing = False
        self.counter = 1
        self.image_view = None
        self.current_tool = None
        self.button_press_id = None
        self.button_release_id = None
        self.motion_id = None
        self.floating_toolbar = None
        # Shape drawing state - track if we're waiting for second click
        self.shape_start_point = None  # For arrow, rectangle, circle
        self.shape_preview_end = None  # Current mouse position for shape preview
        self.shape_type = None  # 'arrow', 'rectangle', 'circle'
        # Text formatting defaults (remembered)
        self.text_bold_default = False
        self.text_italic_default = False
        self.text_size_default = 14.0
        # Toolbar visibility state
        self.toolbar_visible = True
        self.toolbar_menu_item = None
        self.toolbar_toggle_button = None  # Button in headerbar to toggle toolbar
        self.menu_button = None  # Custom menu button widget
        self.menu_window = None  # Floating window for menu button if needed
        # Auto-hide state tracking
        self.current_zoom = 1.0  # 1.0 = 100%
        self.is_fullscreen = False
        self.zoom_handler_id = None
        self.fullscreen_handler_id = None
        
    def _try_integrate_toolbar(self, window):
        """Try to integrate toolbar into EOG window structure"""
        try:
            # Get the window's main content area
            content = window.get_child()
            if not content:
                return False
            
            # Check if content is a container (Box, Grid, etc.)
            if not isinstance(content, Gtk.Container):
                return False
            
            # Try to find a vertical box or similar container
            # EOG typically uses GtkBox for layout
            def find_vertical_box(widget, depth=0):
                if depth > 5:  # Limit recursion
                    return None
                if isinstance(widget, Gtk.Box) and widget.get_orientation() == Gtk.Orientation.VERTICAL:
                    return widget
                if isinstance(widget, Gtk.Container):
                    for child in widget.get_children():
                        result = find_vertical_box(child, depth + 1)
                        if result:
                            return result
                return None
            
            vbox = find_vertical_box(content)
            if vbox:
                # Find the first non-toolbar child to insert after it
                children = vbox.get_children()
                insert_pos = 1  # Default: insert after first child (main toolbar)
                
                # Look for the main toolbar or headerbar
                for i, child in enumerate(children):
                    if isinstance(child, (Gtk.Toolbar, Gtk.HeaderBar)):
                        insert_pos = i + 1
                        break
                
                # Insert toolbar after the main toolbar/headerbar
                vbox.pack_start(self.toolbar, False, False, 0)
                vbox.reorder_child(self.toolbar, insert_pos)
                self.toolbar.show_all()
                return True
            
            # Alternative: Try adding as first child to content
            if isinstance(content, Gtk.Box):
                # Try to insert after first child if it exists
                children = content.get_children()
                if children:
                    content.pack_start(self.toolbar, False, False, 0)
                    content.reorder_child(self.toolbar, 1)  # After first child
                else:
                    content.pack_start(self.toolbar, False, False, 0)
                self.toolbar.show_all()
                return True
                
        except Exception as e:
            # Integration failed
            debug_print(f"Toolbar integration error: {e}")
            pass
        
        return False
    
    def _add_toolbar_toggle_button(self, window):
        """Add a toggle button to the headerbar to show/hide annotation toolbar"""
        try:
            
            # Try to get the headerbar from the window
            headerbar = None
            
            # Method 1: Try direct access if available
            if hasattr(window, 'get_headerbar'):
                try:
                    headerbar = window.get_headerbar()
                    debug_print("Got headerbar via get_headerbar()")
                except Exception as e:
                    debug_print(f"get_headerbar() failed: {e}")
            
            # Method 2: Try get_titlebar (some GTK versions use this)
            if not headerbar and hasattr(window, 'get_titlebar'):
                try:
                    titlebar = window.get_titlebar()
                    if isinstance(titlebar, Gtk.HeaderBar):
                        headerbar = titlebar
                        debug_print("Got headerbar via get_titlebar()")
                except Exception as e:
                    debug_print(f"get_titlebar() failed: {e}")
            
            # Method 3: Search for HeaderBar in window hierarchy (deeper search)
            if not headerbar:
                def find_headerbar(widget, depth=0, path=""):
                    """Recursively search for HeaderBar widget"""
                    if depth > 20:  # Increased depth limit
                        return None
                    if isinstance(widget, Gtk.HeaderBar):
                        debug_print(f"Found HeaderBar at depth {depth}, path: {path}")
                        return widget
                    if isinstance(widget, Gtk.Container):
                        for i, child in enumerate(widget.get_children()):
                            child_path = f"{path}/{type(child).__name__}[{i}]"
                            result = find_headerbar(child, depth + 1, child_path)
                            if result:
                                return result
                    return None
                
                debug_print("Searching window hierarchy for HeaderBar...")
                headerbar = find_headerbar(window, 0, "Window")
                
                # Also try to find MenuButton or PopoverMenuButton which might be in the headerbar
                if not headerbar:
                    def find_menu_button(widget, depth=0):
                        """Find menu button or popover that we can add our item to"""
                        if depth > 20:
                            return None
                        # Look for MenuButton, PopoverMenu, or PopoverMenuButton
                        if isinstance(widget, (Gtk.MenuButton, Gtk.PopoverMenuButton)):
                            debug_print(f"Found menu button at depth {depth}: {type(widget)}")
                            return widget
                        if isinstance(widget, Gtk.Container):
                            for child in widget.get_children():
                                result = find_menu_button(child, depth + 1)
                                if result:
                                    return result
                        return None
                    
                    menu_button = find_menu_button(window)
                    if menu_button:
                        debug_print("Found menu button, will try to add item to its menu")
                        # Store for potential use
                        self.menu_button = menu_button
            
            if headerbar:
                debug_print(f"Found headerbar: {type(headerbar)}")
                # Create a toggle button for showing/hiding toolbar
                self.toolbar_toggle_button = Gtk.ToggleButton.new()
                # Use a more appropriate icon - try edit-annotate or similar
                self.toolbar_toggle_button.set_icon_name("edit-annotate-symbolic")  # Annotation/edit icon
                self.toolbar_toggle_button.set_tooltip_text("Show/Hide Annotation Toolbar")
                self.toolbar_toggle_button.set_active(True)  # Toolbar is visible by default
                self.toolbar_toggle_button.connect("toggled", self._on_toolbar_button_toggled)
                
                # Show the button
                self.toolbar_toggle_button.show()
                
                # Try to add to the end (right side) first
                try:
                    headerbar.pack_end(self.toolbar_toggle_button)
                    debug_print("Added toggle button to headerbar (right side)")
                except Exception as e:
                    debug_print(f"pack_end failed: {e}, trying pack_start...")
                    # Try alternative: pack_start (left side)
                    try:
                        headerbar.pack_start(self.toolbar_toggle_button)
                        debug_print("Added toggle button to headerbar (left side)")
                    except Exception as e2:
                        debug_print(f"pack_start also failed: {e2}")
                        self.toolbar_toggle_button = None
            else:
                debug_print("Could not find headerbar to add toggle button")
                print("EOG Annotation Plugin: Window type: " + str(type(window)), file=sys.stderr)
                # Try to print window structure for debugging
                try:
                    if hasattr(window, 'get_children'):
                        children = window.get_children()
                        debug_print(f"Window has {len(children)} direct children")
                        for i, child in enumerate(children):
                            debug_print(f"Child {i}: {type(child)}")
                except:
                    pass
                
        except Exception as e:
            debug_print(f"Error adding toggle button to headerbar: {e}")
            if DEBUG: traceback.print_exc(file=sys.stderr)
    
    def _create_custom_menu_button(self, window):
        """Create a custom menu button widget with toggle option"""
        try:
            
            # Create a menu button
            self.menu_button = Gtk.MenuButton.new()
            self.menu_button.set_icon_name("view-more-symbolic")  # Three dots icon
            self.menu_button.set_tooltip_text("Annotation Tools")
            self.menu_button.set_direction(Gtk.ArrowType.DOWN)
            
            # Create a menu model for our items
            menu = Gio.Menu.new()
            
            # Add toggle menu item - use a checkmark item that toggles
            # Since we can't use the action directly in menu model easily, we'll create a custom popover
            popover = Gtk.Popover.new(self.menu_button)
            
            # Create a box for menu items
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            vbox.set_border_width(10)
            
            # Create a check menu item for toggle
            toggle_item = Gtk.CheckMenuItem.new_with_label("Show Annotation Toolbar")
            toggle_item.set_active(self.toolbar_visible)
            toggle_item.connect("toggled", self._on_menu_toggle_toggled)
            vbox.pack_start(toggle_item, False, False, 0)
            
            # Store reference to menu item for state updates
            self.toolbar_menu_item = toggle_item
            
            vbox.show_all()
            popover.add(vbox)
            self.menu_button.set_popover(popover)
            
            # Try to add to window - find a good location
            # Method 1: Try to add to the Box child we found earlier (top area)
            try:
                if hasattr(window, 'get_children'):
                    children = window.get_children()
                    if children and isinstance(children[0], Gtk.Box):
                        box = children[0]
                        # Try to add to the start of the box (top area, before other content)
                        box.pack_start(self.menu_button, False, False, 0)
                        self.menu_button.show()
                        debug_print("Added custom menu button to window Box")
                        return
            except Exception as e:
                debug_print(f"Could not add menu button to Box: {e}")
            
            # Method 2: Try to find headerbar area and add there
            # Search for any container that might be a headerbar area
            def find_header_area(widget, depth=0):
                if depth > 10:
                    return None
                # Look for containers that might be header areas
                if isinstance(widget, Gtk.Container):
                    # Check if this looks like a header area (has buttons, etc.)
                    children = widget.get_children()
                    for child in children:
                        if isinstance(child, (Gtk.Button, Gtk.MenuButton, Gtk.HeaderBar)):
                            return widget
                    # Recursively search
                    for child in children:
                        result = find_header_area(child, depth + 1)
                        if result:
                            return result
                return None
            
            header_area = find_header_area(window)
            if header_area and isinstance(header_area, Gtk.Container):
                try:
                    header_area.pack_start(self.menu_button, False, False, 0)
                    self.menu_button.show()
                    debug_print("Added custom menu button to header area")
                    return
                except Exception as e:
                    debug_print(f"Could not add to header area: {e}")
            
            # Method 3: Create a floating menu button window (last resort)
            menu_window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
            menu_window.set_decorated(False)
            menu_window.set_resizable(False)
            menu_window.set_skip_taskbar_hint(True)
            menu_window.set_skip_pager_hint(True)
            menu_window.set_keep_above(True)
            menu_window.set_default_size(40, 40)
            menu_window.add(self.menu_button)
            menu_window.show_all()
            
            # Position it in top-right corner of main window
            try:
                window_x, window_y = window.get_position()
                window_width = window.get_size()[0]
                menu_window.move(window_x + window_width - 50, window_y + 5)
            except:
                pass
            
            self.menu_window = menu_window
            debug_print("Created floating menu button window")
            
        except Exception as e:
            debug_print(f"Error creating custom menu button: {e}")
            if DEBUG: traceback.print_exc(file=sys.stderr)
    
    def _on_menu_toggle_toggled(self, menu_item):
        """Handle menu toggle item"""
        self.toolbar_visible = menu_item.get_active()
        self.toggle_toolbar_visibility()
    
    def _on_toolbar_button_toggled(self, button):
        """Handle headerbar toggle button"""
        # The button state represents visibility (active = visible)
        self.toolbar_visible = button.get_active()
        self.toggle_toolbar_visibility()
    
    def _setup_auto_hide_monitoring(self, window):
        """Set up monitoring for zoom and fullscreen changes"""
        try:
            
            # Get the view to monitor zoom changes
            view = window.get_view()
            if not view:
                debug_print("Could not get view for zoom monitoring")
                return
            
            # Try to connect to zoom changed signal
            zoom_connected = False
            try:
                if hasattr(view, 'connect'):
                    # Try various possible signal names
                    zoom_signals = ['zoom-changed', 'notify::zoom', 'zoom-updated', 'notify::zoom-factor']
                    for signal_name in zoom_signals:
                        try:
                            self.zoom_handler_id = view.connect(signal_name, self._on_zoom_changed)
                            debug_print(f"Connected to {signal_name} signal")
                            zoom_connected = True
                            break
                        except:
                            pass
            except Exception as e:
                debug_print(f"Could not connect zoom signal: {e}")
            
            # If direct signal connection failed, use a timer to poll zoom level
            if not zoom_connected:
                debug_print("Using timer to poll zoom level")
                def poll_zoom():
                    old_zoom = self.current_zoom
                    self._update_zoom_level(view)
                    if abs(old_zoom - self.current_zoom) > 0.01:
                        self._update_toolbar_visibility()
                    return True  # Continue polling
                # Poll every 500ms
                GLib.timeout_add(500, poll_zoom)
            
            # Monitor window fullscreen state
            try:
                # Connect to window-state-event (most reliable)
                if hasattr(window, 'connect'):
                    try:
                        self.fullscreen_handler_id = window.connect("window-state-event", self._on_window_state_changed)
                        debug_print("Connected to window-state-event")
                    except:
                        # Try alternative signal
                        try:
                            self.fullscreen_handler_id = window.connect("notify::is-fullscreen", self._on_fullscreen_changed)
                            debug_print("Connected to notify::is-fullscreen")
                        except:
                            pass
            except Exception as e:
                debug_print(f"Could not connect fullscreen signal: {e}")
            
            # Get initial zoom level
            self._update_zoom_level(view)
            
            # Get initial fullscreen state
            try:
                if hasattr(window, 'is_fullscreen'):
                    self.is_fullscreen = window.is_fullscreen()
                elif hasattr(window, 'get_window'):
                    gdk_window = window.get_window()
                    if gdk_window:
                        state = gdk_window.get_state()
                        self.is_fullscreen = bool(state & Gdk.WindowState.FULLSCREEN)
            except:
                pass
            
            debug_print(f"Initial state - zoom={self.current_zoom}, fullscreen={self.is_fullscreen}")
            
            # Check initial visibility conditions
            self._update_toolbar_visibility()
            
        except Exception as e:
            debug_print(f"Error setting up auto-hide monitoring: {e}")
            if DEBUG: traceback.print_exc(file=sys.stderr)
    
    def _update_zoom_level(self, view):
        """Update current zoom level from view"""
        try:
            # Try different methods to get zoom
            zoom_found = False
            
            # Method 1: Direct method calls
            if hasattr(view, 'get_zoom'):
                try:
                    self.current_zoom = view.get_zoom()
                    zoom_found = True
                except:
                    pass
            
            if not zoom_found and hasattr(view, 'get_zoom_factor'):
                try:
                    self.current_zoom = view.get_zoom_factor()
                    zoom_found = True
                except:
                    pass
            
            # Method 2: Property access
            if not zoom_found:
                for prop_name in ['zoom', 'zoom-factor', 'zoom_factor']:
                    try:
                        if hasattr(view, 'get_property'):
                            self.current_zoom = view.get_property(prop_name)
                            zoom_found = True
                            break
                    except:
                        pass
            
            # Method 3: Try to get from window if view doesn't have it
            if not zoom_found and hasattr(self, 'window') and self.window:
                try:
                    if hasattr(self.window, 'get_zoom'):
                        self.current_zoom = self.window.get_zoom()
                        zoom_found = True
                except:
                    pass
            
            if not zoom_found:
                # Default to 1.0 if we can't determine zoom
                self.current_zoom = 1.0
                
        except Exception as e:
            debug_print(f"Could not get zoom level: {e}")
            self.current_zoom = 1.0  # Default to 100%
    
    def _on_zoom_changed(self, view, *args):
        """Handle zoom level change"""
        import sys
        self._update_zoom_level(view)
        debug_print(f"Zoom changed to {self.current_zoom}")
        self._update_toolbar_visibility()
    
    def _on_window_state_changed(self, window, event):
        """Handle window state change (fullscreen, etc.)"""
        import sys
        try:
            if event.changed_mask & Gdk.WindowState.FULLSCREEN:
                self.is_fullscreen = bool(event.new_window_state & Gdk.WindowState.FULLSCREEN)
                debug_print(f"Fullscreen changed to {self.is_fullscreen}")
                self._update_toolbar_visibility()
        except Exception as e:
            debug_print(f"Error handling window state: {e}")
        return False  # Let other handlers process
    
    def _on_fullscreen_changed(self, window, param):
        """Handle fullscreen property change"""
        import sys
        try:
            if hasattr(window, 'is_fullscreen'):
                self.is_fullscreen = window.is_fullscreen()
            debug_print(f"Fullscreen changed to {self.is_fullscreen}")
            self._update_toolbar_visibility()
        except Exception as e:
            debug_print(f"Error handling fullscreen change: {e}")
    
    def _update_toolbar_visibility(self):
        """Update toolbar visibility based on zoom and fullscreen conditions"""
        import sys
        # Show toolbar only if zoom is 100% (1.0) and not fullscreen
        should_show = (abs(self.current_zoom - 1.0) < 0.01) and not self.is_fullscreen
        
        if should_show != self.toolbar_visible:
            self.toolbar_visible = should_show
            debug_print(f"Updating toolbar visibility: {self.toolbar_visible} (zoom={self.current_zoom}, fullscreen={self.is_fullscreen})")
            
            if self.floating_toolbar:
                if self.toolbar_visible:
                    self.floating_toolbar.show()
                else:
                    self.floating_toolbar.hide()
            elif self.toolbar:
                if self.toolbar_visible:
                    self.toolbar.show()
                else:
                    self.toolbar.hide()
            
            # Update toggle button state if available
            if self.toolbar_toggle_button:
                try:
                    self.toolbar_toggle_button.handler_block_by_func(self._on_toolbar_button_toggled)
                    self.toolbar_toggle_button.set_active(self.toolbar_visible)
                    self.toolbar_toggle_button.handler_unblock_by_func(self._on_toolbar_button_toggled)
                except:
                    self.toolbar_toggle_button.set_active(self.toolbar_visible)
            
            # Update menu item state if available
            if self.toolbar_menu_item:
                try:
                    if isinstance(self.toolbar_menu_item, Gtk.CheckMenuItem):
                        self.toolbar_menu_item.handler_block_by_func(self._on_menu_toggle_toggled)
                        self.toolbar_menu_item.set_active(self.toolbar_visible)
                        self.toolbar_menu_item.handler_unblock_by_func(self._on_menu_toggle_toggled)
                except:
                    pass
    
    def _add_toolbar_menu_item(self, window):
        """Add a menu item to View menu to toggle toolbar visibility"""
        try:
            
            # Try to use GAction API (modern GTK/GNOME approach)
            try:
                # Create a toggle action for showing/hiding toolbar
                # Use "win." prefix for window-level actions (GNOME convention)
                self.toolbar_action = Gio.SimpleAction.new_stateful(
                    "toggle-annotation-toolbar",
                    None,
                    GLib.Variant.new_boolean(True)
                )
                self.toolbar_action.connect("change-state", self._on_toolbar_menu_toggled)
                
                # Try to add to window's action map
                if isinstance(window, Gio.ActionMap):
                    window.add_action(self.toolbar_action)
                    debug_print("Added toggle action to window (action: win.toggle-annotation-toolbar)")
                    debug_print("Note: Menu item may need to be manually added to EOG's menu structure")
                elif hasattr(window, 'add_action'):
                    window.add_action(self.toolbar_action)
                    debug_print("Added toggle action via add_action")
                else:
                    debug_print("Window does not support add_action")
                    self.toolbar_action = None
            except Exception as e:
                debug_print(f"Could not add action: {e}")
                self.toolbar_action = None
            
            # Try to find and modify the View menu
            # EOG might use GMenuModel or GtkPopoverMenu
            def find_and_modify_view_menu(widget, depth=0):
                """Try to find View menu and add our item"""
                if depth > 15:  # Limit recursion
                    return False
                
                # Check if this is a popover menu or menu
                if isinstance(widget, Gtk.PopoverMenu):
                    # Try to get menu model
                    try:
                        menu_model = widget.get_menu_model()
                        if menu_model and isinstance(menu_model, Gio.MenuModel):
                            # Try to find View section
                            n_items = menu_model.get_n_items()
                            for i in range(n_items):
                                item_label = menu_model.get_item_attribute_value(i, 'label', GLib.VariantType('s'))
                                if item_label and 'view' in item_label.get_string().lower():
                                    # Found View menu section
                                    debug_print(f"Found View menu section")
                                    # Unfortunately, GMenuModel is immutable, so we can't easily add items
                                    # This approach has limitations
                                    break
                    except:
                        pass
                
                # Recursively search children
                if isinstance(widget, Gtk.Container):
                    for child in widget.get_children():
                        if find_and_modify_view_menu(child, depth + 1):
                            return True
                
                return False
            
            # Try to find menu in window hierarchy
            find_and_modify_view_menu(window)
            
            debug_print("Menu item integration attempted (direct menu modification may not be possible)")
            
        except Exception as e:
            debug_print(f"Error adding menu item: {e}")
            if DEBUG: traceback.print_exc(file=sys.stderr)
    
    def _on_toolbar_menu_toggled(self, action, value):
        """Handle menu item toggle for toolbar visibility"""
        # Update action state
        action.set_state(value)
        # Toggle toolbar visibility
        self.toggle_toolbar_visibility()
    
    def toggle_toolbar_visibility(self):
        """Toggle toolbar visibility"""
        # If called without parameter, toggle the state
        if not hasattr(self, '_toggle_in_progress'):
            self.toolbar_visible = not self.toolbar_visible
        
        if self.floating_toolbar:
            # For floating toolbar window
            if self.toolbar_visible:
                self.floating_toolbar.show()
            else:
                self.floating_toolbar.hide()
        elif self.toolbar:
            # For integrated toolbar - hide/show the toolbar itself
            # But keep the toggle button visible if it's in the toolbar
            if self.toolbar_visible:
                self.toolbar.show()
            else:
                # If toggle button is in the toolbar, we need to keep it visible
                # So we'll hide all items except the toggle button
                if self.toolbar_toggle_button and self.toolbar_toggle_button.get_parent():
                    # Hide all toolbar items except the toggle button
                    for item in self.toolbar.get_children():
                        if isinstance(item, Gtk.ToolItem):
                            for child in item.get_children():
                                if child != self.toolbar_toggle_button:
                                    item.hide()
                else:
                    self.toolbar.hide()
        
        # Update button state if available
        if self.toolbar_toggle_button:
            try:
                # Temporarily block signal to avoid recursion
                self.toolbar_toggle_button.handler_block_by_func(self._on_toolbar_button_toggled)
                self.toolbar_toggle_button.set_active(self.toolbar_visible)
                self.toolbar_toggle_button.handler_unblock_by_func(self._on_toolbar_button_toggled)
            except:
                # If handler_block fails, just set the state
                self.toolbar_toggle_button.set_active(self.toolbar_visible)
        
        # Update menu item state if available
        if self.toolbar_menu_item:
            self.toolbar_menu_item.set_active(self.toolbar_visible)
        
    def _create_floating_toolbar(self, parent_window):
        """Create a floating toolbar window if toolbar integration fails"""
        import sys
        try:
            # Create a floating window with titlebar for visibility
            self.floating_toolbar = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
            self.floating_toolbar.set_title("Annotation Tools")
            self.floating_toolbar.set_transient_for(parent_window)
            self.floating_toolbar.set_decorated(True)  # Show titlebar so user can see it
            self.floating_toolbar.set_resizable(False)
            self.floating_toolbar.set_skip_taskbar_hint(True)
            self.floating_toolbar.set_default_size(-1, -1)
            # Make sure it's always on top initially
            self.floating_toolbar.set_keep_above(True)
            
            # Add toolbar to window in a frame
            frame = Gtk.Frame()
            frame.set_label("Annotation Tools")
            frame.set_shadow_type(Gtk.ShadowType.IN)
            
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            vbox.set_border_width(5)
            vbox.pack_start(self.toolbar, False, False, 0)
            frame.add(vbox)
            
            self.floating_toolbar.add(frame)
            self.floating_toolbar.show_all()
            
            # Position near the parent window
            try:
                parent_x, parent_y = parent_window.get_position()
                self.floating_toolbar.move(parent_x + 100, parent_y + 100)
            except Exception as e:
                # If get_position fails, just show it
                debug_print(f"Could not position toolbar: {e}")
                pass
                
            # Ensure it's visible
            self.floating_toolbar.present()
            debug_print("Floating toolbar window shown")
        except Exception as e:
            debug_print(f"ERROR creating floating toolbar: {e}")
            if DEBUG: traceback.print_exc(file=sys.stderr)
        
    def do_activate(self):
        """Called when plugin is activated"""
        try:
            # Debug output
            debug_print("Activating...")
            
            window = self.window
            if not window:
                debug_print("ERROR - window is None!")
                return
            
            # Get the image view widget
            self.image_view = window.get_view()
            if not self.image_view:
                debug_print("ERROR - could not get view!")
                return
                
            self.annotation_manager.set_view(self.image_view)
            # Store reference to plugin in annotation manager for arrow preview
            self.annotation_manager.plugin = self
            # Initialize undo/redo button states
            self._update_undo_redo_buttons()
            debug_print("View set successfully")
            
            # Create toolbar
            self.toolbar = AnnotationToolbar()
            self.toolbar.connect("tool-changed", self._on_tool_changed)
            self.toolbar.connect("color-changed", self._on_color_changed)
            self.toolbar.connect("line-width-changed", self._on_line_width_changed)
            self.toolbar.connect("arrow-style-changed", self._on_arrow_style_changed)
            self.toolbar.connect("undo-clicked", self._on_undo_clicked)
            self.toolbar.connect("redo-clicked", self._on_redo_clicked)
            self.toolbar.connect("clear-clicked", self._on_clear_clicked)
            self.toolbar.connect("copy-clicked", self._on_copy_clicked)
            self.toolbar.connect("save-clicked", self._on_save_clicked)
            # Store default values from toolbar
            self.line_width_default = self.toolbar.current_line_width
            self.arrow_style_default = self.toolbar.current_arrow_style
            debug_print("Toolbar created")
            
            # Try to integrate toolbar into EOG window
            toolbar_integrated = self._try_integrate_toolbar(window)
            debug_print(f"Toolbar integration result: {toolbar_integrated}")
            
            # If integration failed, use floating toolbar
            if not toolbar_integrated:
                debug_print("Creating floating toolbar...")
                self._create_floating_toolbar(window)
                debug_print("Floating toolbar created")
            
            # Monitor zoom and fullscreen changes for auto-hide
            self._setup_auto_hide_monitoring(window)
            
            # Connect mouse events
            if self.image_view:
                # Make sure the widget can receive events
                self.image_view.set_events(
                    self.image_view.get_events() |
                    Gdk.EventMask.BUTTON_PRESS_MASK |
                    Gdk.EventMask.BUTTON_RELEASE_MASK |
                    Gdk.EventMask.POINTER_MOTION_MASK |
                    Gdk.EventMask.BUTTON_MOTION_MASK
                )
                self.image_view.set_can_focus(True)
                debug_print("Mouse events configured")
                
                self.button_press_id = self.image_view.connect("button-press-event", self._on_button_press)
                self.button_release_id = self.image_view.connect("button-release-event", self._on_button_release)
                self.motion_id = self.image_view.connect("motion-notify-event", self._on_motion)
                debug_print("Mouse event handlers connected")
        except Exception as e:
            debug_print(f"ERROR in do_activate: {e}")
            if DEBUG: traceback.print_exc(file=sys.stderr)
    
    def do_deactivate(self):
        """Called when plugin is deactivated"""
        # Disconnect signals
        if self.image_view:
            if self.button_press_id:
                self.image_view.disconnect(self.button_press_id)
            if self.button_release_id:
                self.image_view.disconnect(self.button_release_id)
            if self.motion_id:
                self.image_view.disconnect(self.motion_id)
        
        # Disconnect zoom and fullscreen monitoring
        if self.zoom_handler_id and self.image_view:
            try:
                self.image_view.disconnect(self.zoom_handler_id)
            except:
                pass
        if self.fullscreen_handler_id and self.window:
            try:
                self.window.disconnect(self.fullscreen_handler_id)
            except:
                pass
        
        # Remove toolbar
        has_floating = self.floating_toolbar is not None
        if self.floating_toolbar:
            self.floating_toolbar.destroy()
            self.floating_toolbar = None
            
        if self.toolbar:
            try:
                if hasattr(self.window, 'get_plugin_toolbar'):
                    toolbar_container = self.window.get_plugin_toolbar()
                    if toolbar_container:
                        toolbar_container.remove(self.toolbar)
            except:
                pass
            # Don't destroy toolbar if it was in a floating window (already destroyed)
            if not has_floating:
                self.toolbar.destroy()
            self.toolbar = None
        
        # Remove toggle button from headerbar if added
        if self.toolbar_toggle_button:
            try:
                parent = self.toolbar_toggle_button.get_parent()
                if parent:
                    parent.remove(self.toolbar_toggle_button)
                self.toolbar_toggle_button.destroy()
                self.toolbar_toggle_button = None
            except:
                pass
        
        # Remove custom menu button if added
        if self.menu_button:
            try:
                parent = self.menu_button.get_parent()
                if parent:
                    parent.remove(self.menu_button)
                self.menu_button.destroy()
                self.menu_button = None
            except:
                pass
        
        # Remove menu window if created
        if hasattr(self, 'menu_window') and self.menu_window:
            try:
                self.menu_window.destroy()
                self.menu_window = None
            except:
                pass
        
        # Remove menu action if added
        if hasattr(self, 'window') and self.window and hasattr(self, 'toolbar_action') and self.toolbar_action:
            try:
                if isinstance(self.window, Gio.ActionMap):
                    self.window.remove_action("win.toggle-annotation-toolbar")
            except:
                pass
        
        # Clean up annotation manager
        self.annotation_manager.set_view(None)
        self.annotation_manager = None
        self.current_annotation = None
        self.image_view = None
    
    def _on_tool_changed(self, toolbar, tool):
        """Handle tool selection change"""
        self.current_tool = tool
        self.drawing = False
        self.current_annotation = None
        self.annotation_manager.current_annotation = None
        # Reset shape start point when switching tools
        self.shape_start_point = None
        self.shape_preview_end = None
        self.shape_type = None
    
    def _on_color_changed(self, toolbar, r, g, b):
        """Handle color change"""
        if self.current_annotation:
            self.current_annotation.color = (r, g, b)
            if self.image_view:
                self.image_view.queue_draw()
    
    def _on_line_width_changed(self, toolbar, width):
        """Handle line width change"""
        self.line_width_default = width
        if self.current_annotation:
            self.current_annotation.line_width = width
            if self.image_view:
                self.image_view.queue_draw()
    
    def _on_arrow_style_changed(self, toolbar, style):
        """Handle arrow style change"""
        self.arrow_style_default = style
        if self.current_annotation:
            self.current_annotation.arrow_style = style
            if self.image_view:
                self.image_view.queue_draw()
    
    def _on_undo_clicked(self, toolbar):
        """Handle undo button click"""
        if self.annotation_manager.undo():
            # Update button states
            self._update_undo_redo_buttons()
    
    def _on_redo_clicked(self, toolbar):
        """Handle redo button click"""
        if self.annotation_manager.redo():
            # Update button states
            self._update_undo_redo_buttons()
    
    def _update_undo_redo_buttons(self):
        """Update undo/redo button enabled states"""
        if self.toolbar:
            can_undo = self.annotation_manager.can_undo()
            can_redo = self.annotation_manager.can_redo()
            self.toolbar.update_undo_redo_state(can_undo, can_redo)
    
    def _on_clear_clicked(self, toolbar):
        """Handle clear button click"""
        self.annotation_manager.clear()
        self.counter = 1
        # Update button states
        self._update_undo_redo_buttons()
    
    def _on_button_press(self, widget, event):
        """Handle mouse button press"""
        import sys
        if not self.current_tool or not self.toolbar:
            return False  # Let other handlers process
        
        if event.button != 1:  # Left button only
            return False
        
        # Get coordinates relative to widget
        x = event.x
        y = event.y
        
        color = self.toolbar.current_color
        debug_print(f"Button press at ({x}, {y}) with tool '{self.current_tool}'")
        
        if self.current_tool in ["arrow", "rectangle", "circle"]:
            if self.shape_start_point is None:
                # First click - set start point
                self.shape_start_point = (x, y)
                self.shape_preview_end = (x, y)  # Initialize preview end point
                self.shape_type = self.current_tool
                debug_print(f"{self.current_tool} start point at ({x}, {y})")
                if self.image_view:
                    self.image_view.queue_draw()
                return True  # Stop event propagation
            else:
                # Second click - finish shape
                x1, y1 = self.shape_start_point
                shape_type = self.shape_type  # Save before clearing
                line_width = self.toolbar.current_line_width
                arrow_style = self.toolbar.current_arrow_style if shape_type == "arrow" else 0
                annotation = Annotation(shape_type, x1, y1, x, y, color, 
                                      line_width=line_width, arrow_style=arrow_style)
                self.annotation_manager.add_annotation(annotation)
                self._update_undo_redo_buttons()
                self.shape_start_point = None
                self.shape_preview_end = None
                self.shape_type = None
                debug_print(f"{shape_type} completed from ({x1}, {y1}) to ({x}, {y})")
                if self.image_view:
                    self.image_view.queue_draw()
                return True  # Stop event propagation
        elif self.current_tool == "dot":
            line_width = self.toolbar.current_line_width
            annotation = Annotation("dot", x, y, color=color, line_width=line_width)
            annotation.counter = self.counter
            self.counter += 1
            self.annotation_manager.add_annotation(annotation)
            self._update_undo_redo_buttons()
            debug_print(f"Added dot #{annotation.counter} at ({x}, {y})")
            if self.image_view:
                self.image_view.queue_draw()
            return True  # Stop event propagation
        elif self.current_tool == "text":
            # Show text entry dialog with formatting options
            dialog = Gtk.Dialog(title="Add Text Annotation", transient_for=self.window,
                              modal=True, destroy_with_parent=True)
            dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL,
                             "_OK", Gtk.ResponseType.OK)
            
            # Create content box
            content_area = dialog.get_content_area()
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(10)
            
            # Text entry
            entry = Gtk.Entry()
            entry.set_activates_default(True)
            entry.connect("activate", lambda e: dialog.response(Gtk.ResponseType.OK))
            entry_label = Gtk.Label(label="Text:")
            entry_label.set_xalign(0)
            vbox.pack_start(entry_label, False, False, 0)
            vbox.pack_start(entry, False, False, 0)
            
            # Formatting options
            format_frame = Gtk.Frame(label="Text Formatting")
            format_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            format_box.set_border_width(5)
            
            # Bold checkbox
            bold_check = Gtk.CheckButton(label="Bold")
            bold_check.set_active(self.text_bold_default)
            format_box.pack_start(bold_check, False, False, 0)
            
            # Italic checkbox
            italic_check = Gtk.CheckButton(label="Italic")
            italic_check.set_active(self.text_italic_default)
            format_box.pack_start(italic_check, False, False, 0)
            
            # Font size
            size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            size_label = Gtk.Label(label="Size:")
            size_spin = Gtk.SpinButton.new_with_range(8.0, 72.0, 1.0)
            size_spin.set_value(self.text_size_default)
            size_spin.set_digits(0)
            size_box.pack_start(size_label, False, False, 0)
            size_box.pack_start(size_spin, False, False, 0)
            format_box.pack_start(size_box, False, False, 0)
            
            format_frame.add(format_box)
            vbox.pack_start(format_frame, False, False, 0)
            
            content_area.add(vbox)
            dialog.set_default_response(Gtk.ResponseType.OK)
            vbox.show_all()
            
            response = dialog.run()
            text = entry.get_text()
            bold = bold_check.get_active()
            italic = italic_check.get_active()
            size = size_spin.get_value()
            dialog.destroy()
            
            if response == Gtk.ResponseType.OK and text:
                # Remember settings for next time
                self.text_bold_default = bold
                self.text_italic_default = italic
                self.text_size_default = size
                
                line_width = self.toolbar.current_line_width
                annotation = Annotation("text", x, y, color=color, text=text,
                                      text_bold=bold, text_italic=italic, text_size=size,
                                      line_width=line_width)
                self.annotation_manager.add_annotation(annotation)
                self._update_undo_redo_buttons()
                if self.image_view:
                    self.image_view.queue_draw()
            return True  # Stop event propagation
    
    def _on_button_release(self, widget, event):
        """Handle mouse button release"""
        # Shapes use click-click, not drag, so we don't handle release
        return False
    
    def _on_motion(self, widget, event):
        """Handle mouse motion"""
        x = event.x
        y = event.y
        
        # Handle shape preview - show shape while moving mouse after first click
        if self.shape_start_point is not None:
            self.shape_preview_end = (x, y)
            if self.image_view:
                self.image_view.queue_draw()
            return True  # Stop event propagation to prevent panning
        
        return False
    
    def _render_annotations_to_pixbuf(self):
        """Render annotations on top of the current image and return as GdkPixbuf"""
        try:
            # Get the current image from EOG
            image = self.window.get_image()
            if not image:
                return None
            
            # Get the pixbuf from the image
            pixbuf = image.get_pixbuf()
            if not pixbuf:
                return None
            
            # Get image dimensions
            img_width = pixbuf.get_width()
            img_height = pixbuf.get_height()
            
            # Get view dimensions for coordinate transformation
            if not self.image_view:
                return None
            view_alloc = self.image_view.get_allocation()
            view_width = view_alloc.width
            view_height = view_alloc.height
            
            # Calculate scale factors (view to image)
            scale_x = img_width / max(view_width, 1)
            scale_y = img_height / max(view_height, 1)
            
            # Create a surface from the pixbuf
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, img_width, img_height)
            cr = cairo.Context(surface)
            
            # Draw the original image
            Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
            cr.paint()
            
            # Draw all annotations with scaled coordinates
            for annotation in self.annotation_manager.annotations:
                annotation.draw(cr, scale_x, scale_y)
            
            # Convert surface back to pixbuf using PNG intermediate
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                surface.write_to_png(tmp_path)
                pixbuf_annotated = GdkPixbuf.Pixbuf.new_from_file(tmp_path)
                os.unlink(tmp_path)
                return pixbuf_annotated
        except Exception as e:
            debug_print(f"Error rendering annotations: {e}")
            if DEBUG: traceback.print_exc(file=sys.stderr)
            return None
    
    def _on_copy_clicked(self, toolbar):
        """Handle copy to clipboard button click"""
        import sys
        try:
            pixbuf = self._render_annotations_to_pixbuf()
            if pixbuf:
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_image(pixbuf)
                clipboard.store()
                debug_print("Image with annotations copied to clipboard")
            else:
                debug_print("Could not render image for clipboard")
        except Exception as e:
            debug_print(f"Error copying to clipboard: {e}")
    
    def _on_save_clicked(self, toolbar):
        """Handle save image button click"""
        import sys
        try:
            # Get the current image
            image = self.window.get_image()
            if not image:
                debug_print("No image to save")
                return
            
            file_info = image.get_file()
            if not file_info:
                debug_print("Could not get file info")
                return
            
            # Generate output filename with '-annotated' suffix
            file_path = file_info.get_path()
            if not file_path:
                debug_print("Could not get file path")
                return
            
            # Add -annotated suffix before extension
            import os
            base, ext = os.path.splitext(file_path)
            output_path = f"{base}-annotated{ext}"
            
            # Render annotations
            pixbuf = self._render_annotations_to_pixbuf()
            if not pixbuf:
                debug_print("Could not render annotations")
                return
            
            # Save pixbuf to file - determine format from extension
            ext_lower = ext.lower()
            if ext_lower in ['.jpg', '.jpeg']:
                pixbuf.savev(output_path, "jpeg", ["quality"], ["95"])
            elif ext_lower == '.png':
                pixbuf.savev(output_path, "png", [], [])
            else:
                # Default to PNG if format unknown
                base, _ = os.path.splitext(output_path)
                output_path = f"{base}.png"
                pixbuf.savev(output_path, "png", [], [])
            debug_print(f"Saved annotated image to {output_path}")
        except Exception as e:
            debug_print(f"Error saving image: {e}")
            if DEBUG: traceback.print_exc(file=sys.stderr)

