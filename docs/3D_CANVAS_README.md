# 3D Canvas Documentation

## Overview

The `gui/3d_canvas.py` file provides a comprehensive 3D canvas implementation with advanced camera system, perspective/orthographic projection, view limits, and full 3D navigation controls.

## Features

### 🎥 Camera System
- **Dual Projection Modes**: Perspective and Orthographic projection
- **View Limits**: Optional culling bounds to limit what gets rendered
- **Camera Position**: Full 3D positioning with x, y, z coordinates
- **Camera Orientation**: Pitch, yaw, and roll rotation
- **Camera Vectors**: Automatic forward, right, and up vector calculation

### 🎨 Grid Customization
- **Separate Grid Colors**: Independent color control for X, Y, and Z grid lines
- **Real-time Color Changes**: Interactive color pickers with immediate preview
- **Menubar Integration**: Easy access through View > 3D Grid submenu
- **Visual Feedback**: Grid colors displayed in real-time info panel

### 🌍 World Transformation
- **World Position**: Translate the entire world
- **World Rotation**: Rotate the entire world around its center
- **World Scale**: Scale the entire world uniformly or per-axis

### 🎮 Controls

#### Mouse Controls
- **Left Mouse + Drag**: Rotate camera/world (depends on control mode)
- **Middle Mouse + Drag**: Pan camera/world
- **Mouse Wheel**: Zoom camera/scale world

#### Keyboard Controls
- **WASD**: Move camera/world forward/back/left/right
- **QE**: Move camera/world up/down
- **TAB**: Toggle between camera and world control modes
- **P**: Toggle between perspective and orthographic projection
- **L**: Toggle view limits on/off
- **G**: Toggle grid display
- **F1**: Toggle coordinate axes display

### 📐 Projection Modes

#### Perspective Projection
- Field of View (FOV) control (10° - 120°)
- Near and far clipping planes
- Natural depth perception

#### Orthographic Projection
- Orthographic size control
- No perspective distortion
- Useful for technical drawings

### 🔍 View Limits
Optional culling system that only renders objects within specified bounds:
- X range: `x_min` to `x_max`
- Y range: `y_min` to `y_max` 
- Z range: `z_min` to `z_max`

Objects outside these bounds are not rendered, improving performance.

## Classes

### `Camera3D`
Main camera class with full 3D functionality:

```python
camera = Camera3D()

# Position and rotation
camera.position = np.array([0.0, 0.0, 5.0])
camera.rotation = np.array([0.0, 0.0, 0.0])  # pitch, yaw, roll

# Projection settings
camera.projection_mode = ProjectionMode.PERSPECTIVE
camera.fov = 60.0
camera.near_plane = 0.1
camera.far_plane = 1000.0

# View limits
camera.use_view_limits = True
camera.view_limits = {
    'x_min': -10.0, 'x_max': 10.0,
    'y_min': -10.0, 'y_max': 10.0,
    'z_min': -10.0, 'z_max': 10.0
}
```

### `Canvas3D`
Main 3D canvas widget:

```python
canvas = Canvas3D(parent)

# World transformation
canvas.world_position = np.array([0.0, 0.0, 0.0])
canvas.world_rotation = np.array([0.0, 0.0, 0.0])
canvas.world_scale = np.array([1.0, 1.0, 1.0])

# Control settings
canvas.control_mode = "camera"  # or "world"
canvas.mouse_sensitivity = 0.5
canvas.key_sensitivity = 0.1
```

## Methods

### Camera Methods
- `move_forward(amount)`: Move camera along forward vector
- `move_right(amount)`: Move camera along right vector
- `move_up(amount)`: Move camera along up vector
- `rotate_pitch(amount)`: Rotate camera pitch (up/down)
- `rotate_yaw(amount)`: Rotate camera yaw (left/right)
- `rotate_roll(amount)`: Rotate camera roll
- `zoom(amount)`: Change FOV (perspective) or size (orthographic)

### Canvas Methods
- `project_point(point_3d)`: Project 3D point to 2D screen coordinates
- `reset_camera()`: Reset camera to default position
- `reset_world()`: Reset world transformation
- `set_view_limits(x_range, y_range, z_range)`: Set view culling bounds
- `set_grid_color_x(color)`: Set color for X-direction grid lines
- `set_grid_color_y(color)`: Set color for Y-direction grid lines
- `set_grid_color_z(color)`: Set color for Z-direction grid lines
- `get_grid_colors()`: Get current grid colors as (x_color, y_color, z_color)

## Usage Example

```python
import wx
from graph_canvas.presentation.desktop.gui.3d_canvas import Canvas3D

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="3D Application")
        
        # Create 3D canvas
        self.canvas = Canvas3D(self)
        
        # Configure camera
        self.canvas.camera.projection_mode = ProjectionMode.PERSPECTIVE
        self.canvas.camera.position = np.array([5.0, 5.0, 5.0])
        
        # Set view limits
        self.canvas.set_view_limits((-20, 20), (-20, 20), (-20, 20))
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)

app = wx.App()
frame = MyFrame()
frame.Show()
app.MainLoop()
```

## Menubar Integration

For applications that need menubar integration with 3D canvas controls, use the provided event handlers:

```python
from event_handlers.3d_canvas_event_handler import (
    on_grid_color_x, on_grid_color_y, on_grid_color_z,
    on_toggle_3d_grid, on_toggle_3d_axes
)

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="My 3D App")
        self.canvas_3d = Canvas3D(self)
        self.create_menubar()
    
    def create_menubar(self):
        menubar = wx.MenuBar()
        view_menu = wx.Menu()
        
        # Grid color submenu
        grid_menu = wx.Menu()
        x_color_item = grid_menu.Append(wx.ID_ANY, "X Grid Color...")
        y_color_item = grid_menu.Append(wx.ID_ANY, "Y Grid Color...")
        z_color_item = grid_menu.Append(wx.ID_ANY, "Z Grid Color...")
        
        view_menu.AppendSubMenu(grid_menu, "3D Grid")
        menubar.Append(view_menu, "&View")
        self.SetMenuBar(menubar)
        
        # Bind events
        self.Bind(wx.EVT_MENU, lambda e: on_grid_color_x(self, e), x_color_item)
        self.Bind(wx.EVT_MENU, lambda e: on_grid_color_y(self, e), y_color_item)
        self.Bind(wx.EVT_MENU, lambda e: on_grid_color_z(self, e), z_color_item)
```

### Grid Color Features
- **X Grid Color**: Controls lines running parallel to Z-axis (east-west direction)
- **Y Grid Color**: Reserved for future Y-plane grid lines (up-down direction)
- **Z Grid Color**: Controls lines running parallel to X-axis (north-south direction)
- **Color Picker**: Standard wxPython color dialog with current color preview
- **Real-time Update**: Grid colors change immediately upon selection

## Dependencies

- **wxPython**: For GUI framework
- **NumPy**: For 3D mathematics and matrix operations

Install dependencies:
```bash
pip install wxpython numpy
```

## Test Applications

Run the basic 3D canvas test:
```bash
python test_3d_canvas.py
```

Run the 3D canvas with menubar integration:
```bash
python test_3d_canvas_with_menu.py
```

Or run the 3D canvas directly:
```bash
python gui/3d_canvas.py
```

## Architecture

### Coordinate Systems
1. **World Space**: Object coordinates before world transformation
2. **Camera Space**: Coordinates relative to camera (view transformation)
3. **Clip Space**: Coordinates after projection transformation
4. **Screen Space**: Final 2D pixel coordinates

### Transformation Pipeline
```
World Space → View Matrix → Camera Space → Projection Matrix → Clip Space → Screen Space
```

### Matrix Operations
- **View Matrix**: Created from camera position and orientation
- **Projection Matrix**: Perspective or orthographic projection
- **World Matrix**: Combines translation, rotation, and scale

## Rendering Features

- **Wireframe Objects**: Line-based 3D objects
- **Grid Display**: 3D grid for spatial reference
- **Coordinate Axes**: X (red), Y (green), Z (blue) axes
- **Real-time Information**: Camera and world state display
- **View Frustum Culling**: Only render objects in view
- **Depth Testing**: Basic front-face culling

## Performance Considerations

- View limits reduce rendering load for large scenes
- Simple wireframe rendering for fast performance
- Efficient matrix operations using NumPy
- Optional grid and axes display

## Extension Points

The 3D canvas is designed to be extensible:

1. **Add Custom Objects**: Extend the object rendering system
2. **Lighting System**: Add directional/point lights
3. **Solid Rendering**: Implement filled polygon rendering
4. **Texture Mapping**: Add texture support
5. **Animation System**: Add keyframe animation
6. **Physics Integration**: Add collision detection

This 3D canvas provides a solid foundation for any 3D application requiring camera control, world manipulation, and view management! 🚀
