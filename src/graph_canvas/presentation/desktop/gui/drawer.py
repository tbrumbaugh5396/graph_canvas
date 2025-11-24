"""
Drawer for drawing the graph canvas.
"""


import math
from contextlib import contextmanager
import wx

# Handle imports for both module and direct execution
import sys
import os

# Add the parent directory to the path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try relative imports first (when running as module)
    from . import graph_canvas as m_graph_canvas
    from . import main_window as m_main_window
    from ..models import node as m_node
    from ..models import edge as m_edge
    from ..utils import commands as m_commands
except ImportError:
    # Fall back to absolute imports (when running directly)
    import graph_canvas.presentation.desktop.gui.graph_canvas as m_graph_canvas
    import graph_canvas.presentation.desktop.gui.main_window as m_main_window
    import graph_canvas.presentation.desktop.models.node as m_node
    import graph_canvas.presentation.desktop.models.edge as m_edge
    import graph_canvas.presentation.desktop.utils.commands as m_commands


def draw_arrow(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_adjusted, target_adjusted, edge, source_node, target_node, 
            normalized_pos: float = None, segment_start: float = 0.0, segment_end: float = 1.0):
    """
    Draw an arrow on a directed edge, including the draggable position control.
    
    Args:
        graph_canvas: The graph canvas
        dc: The device context to draw on
        source_adjusted: The adjusted start point (x, y) of the edge
        target_adjusted: The adjusted end point (x, y) of the edge
        edge: The edge to draw the arrow for
        source_node: The source node
        target_node: The target node
        normalized_pos: Optional normalized position (0-1) for hyperedge segments
        segment_start: Start position of the segment (for hyperedges)
        segment_end: End position of the segment (for hyperedges)
    """
    # Calculate arrow position along the edge
    dx = target_adjusted[0] - source_adjusted[0]
    dy = target_adjusted[1] - source_adjusted[1]
    
    # Get arrow position
    if normalized_pos is not None:
        # Use provided normalized position for hyperedge segments
        arrow_pos = normalized_pos
    else:
        # Use edge's arrow position, scaled to segment if needed
        arrow_pos = getattr(edge, 'arrow_position', 0.5)
        if segment_start != 0.0 or segment_end != 1.0:
            # Scale position to segment
            arrow_pos = (arrow_pos - segment_start) / (segment_end - segment_start)
    
    # Clamp arrow position to valid range
    arrow_pos = max(0.1, min(0.9, arrow_pos))
    
    # Calculate arrow center point
    arrow_x = source_adjusted[0] + dx * arrow_pos
    arrow_y = source_adjusted[1] + dy * arrow_pos
    
    # Calculate arrow direction
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1:  # Avoid division by zero
        return
        
    dx = dx / length
    dy = dy / length
    
    # Arrow dimensions
    arrow_size = max(8, min(20, edge.width * 3 * graph_canvas.zoom))  # Scale with edge width and zoom
    arrow_width = arrow_size * 0.5
    
    # Calculate arrow points
    # Main arrow
    points = [
        (arrow_x, arrow_y),  # Tip
        (arrow_x - arrow_size * dx + arrow_width * dy,  # Back left
         arrow_y - arrow_size * dy - arrow_width * dx),
        (arrow_x - arrow_size * dx * 0.5,  # Middle indent
         arrow_y - arrow_size * dy * 0.5),
        (arrow_x - arrow_size * dx - arrow_width * dy,  # Back right
         arrow_y - arrow_size * dy + arrow_width * dx),
    ]
    
    # Save current DC settings
    old_pen = dc.GetPen()
    old_brush = dc.GetBrush()
    
    # Draw filled arrow
    dc.SetBrush(wx.Brush(edge.color))
    dc.SetPen(wx.Pen(edge.color, 1))
    dc.DrawPolygon(points)
    
    # Draw draggable control point
    control_radius = max(4, min(8, edge.width * graph_canvas.zoom))
    dc.SetBrush(wx.Brush(wx.Colour(255, 255, 0)))  # Yellow fill
    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))  # Black border
    dc.DrawCircle(arrow_x, arrow_y, control_radius)
    
    # Restore DC settings
    dc.SetPen(old_pen)
    dc.SetBrush(old_brush)


def draw_selection_rect(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """
    Draw the selection rectangle when dragging to select multiple items.
    
    Args:
        graph_canvas: The graph canvas containing selection state
        dc: The device context to draw on
    """
    if not graph_canvas.selection_rect:
        return

    # Save current DC settings
    old_pen = dc.GetPen()
    old_brush = dc.GetBrush()

    # Temporarily exit world transforms to draw in screen coordinates
    restore_state = False
    gc = dc.GetGraphicsContext() if hasattr(dc, 'GetGraphicsContext') else None
    if gc:
        try:
            gc.PopState()
            restore_state = True
        except Exception:
            restore_state = False

    # Create selection rectangle style (screen space)
    dc.SetPen(wx.Pen(wx.Colour(0, 120, 215), 2, wx.PENSTYLE_SOLID))
    dc.SetBrush(wx.Brush(wx.Colour(0, 120, 215, 96)))

    # Draw rectangle in screen coordinates
    rect = graph_canvas.selection_rect
    dc.DrawRectangle(rect.GetX(), rect.GetY(), rect.GetWidth(), rect.GetHeight())

    # Restore DC settings
    dc.SetPen(old_pen)
    dc.SetBrush(old_brush)

    # Restore world transforms for subsequent drawing
    if restore_state and gc:
        gc.PushState()
        # Apply Scale then Translate to match world_to_screen math
        gc.Scale(graph_canvas.zoom, graph_canvas.zoom)
        gc.Translate(graph_canvas.pan_x, graph_canvas.pan_y)
        # Reapply world rotation about screen center
        if graph_canvas.world_rotation != 0.0:
            size = graph_canvas.GetSize()
            screen_center_x = size.width / 2.0
            screen_center_y = size.height / 2.0
            transformed_center_x = (screen_center_x - graph_canvas.pan_x) / graph_canvas.zoom
            transformed_center_y = (screen_center_y - graph_canvas.pan_y) / graph_canvas.zoom
            gc.Translate(transformed_center_x, transformed_center_y)
            gc.Rotate(math.radians(graph_canvas.world_rotation))
            gc.Translate(-transformed_center_x, -transformed_center_y)


def draw_temp_edge(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """Draw temporary edge while creating (not affected by world rotation)."""

    if not graph_canvas.edge_start_node:
        return

    # Temporarily exit the rotated world transformation if needed
    restore_state = False
    if graph_canvas.world_rotation != 0.0 and hasattr(dc, 'GetGraphicsContext'):
        gc = dc.GetGraphicsContext()
        if gc:
            gc.PopState()  # Temporarily exit the rotated world
            restore_state = True

    mouse_pos = graph_canvas.ScreenToClient(wx.GetMousePosition())
    
    # Check if mouse is over a connection point
    connection_info = graph_canvas.get_connection_point_at_position(mouse_pos.x, mouse_pos.y)
    if connection_info:
        edge, point_type, _ = connection_info
        source_node = graph_canvas.graph.get_node(edge.source_id)
        target_node = graph_canvas.graph.get_node(edge.target_id)
        if source_node and target_node:
            source_screen = graph_canvas.world_to_screen(source_node.x, source_node.y)
            target_screen = graph_canvas.world_to_screen(target_node.x, target_node.y)
            source_adjusted = graph_canvas.calculate_line_endpoint(source_node, target_node,
                                                        source_screen, target_screen, True, edge)
            target_adjusted = graph_canvas.calculate_line_endpoint(target_node, source_node,
                                                        target_screen, source_screen, False, edge)
            dx = target_adjusted[0] - source_adjusted[0]
            dy = target_adjusted[1] - source_adjusted[1]
            if point_type == 'from':
                mouse_pos.x = source_adjusted[0] + dx * edge.from_connection_point
                mouse_pos.y = source_adjusted[1] + dy * edge.from_connection_point
            else:  # 'to'
                mouse_pos.x = source_adjusted[0] + dx * edge.to_connection_point
                mouse_pos.y = source_adjusted[1] + dy * edge.to_connection_point
    
    # Calculate start position accounting for current world rotation
    # Since we're outside the rotation transformation, we need to manually apply it
    raw_start_pos = graph_canvas.world_to_screen(graph_canvas.edge_start_node.x, graph_canvas.edge_start_node.y)
    
    if graph_canvas.world_rotation != 0.0:
        # Apply the rotation transformation to the start position
        size = graph_canvas.GetSize()
        center_x = size.width // 2
        center_y = size.height // 2
        
        # Convert rotation to radians
        rotation_rad = math.radians(graph_canvas.world_rotation)
        cos_angle = math.cos(rotation_rad)
        sin_angle = math.sin(rotation_rad)
        
        # Translate to origin (center of screen)
        temp_x = raw_start_pos[0] - center_x
        temp_y = raw_start_pos[1] - center_y
        
        # Apply rotation
        rotated_x = temp_x * cos_angle - temp_y * sin_angle
        rotated_y = temp_x * sin_angle + temp_y * cos_angle
        
        # Translate back
        start_pos = (int(rotated_x + center_x), int(rotated_y + center_y))
    else:
        start_pos = raw_start_pos

    dc.SetPen(wx.Pen(wx.Colour(50, 50, 50), 3,
                        wx.PENSTYLE_DOT))  # Dark temporary edge
                        
    if graph_canvas.edge_rendering_type == "freeform" and graph_canvas.temp_edge and graph_canvas.temp_path_points:
        # Draw the freeform path
        screen_points = []
        for point in graph_canvas.temp_path_points:
            screen_pos = graph_canvas.world_to_screen(point[0], point[1])
            if graph_canvas.world_rotation != 0.0:
                # Apply the same rotation transformation
                size = graph_canvas.GetSize()
                center_x = size.width // 2
                center_y = size.height // 2
                rotation_rad = math.radians(graph_canvas.world_rotation)
                cos_angle = math.cos(rotation_rad)
                sin_angle = math.sin(rotation_rad)
                temp_x = screen_pos[0] - center_x
                temp_y = screen_pos[1] - center_y
                rotated_x = temp_x * cos_angle - temp_y * sin_angle
                rotated_y = temp_x * sin_angle + temp_y * cos_angle
                screen_pos = (int(rotated_x + center_x), int(rotated_y + center_y))
            screen_points.append(screen_pos)
        
        # Draw lines connecting all points
        for i in range(len(screen_points) - 1):
            dc.DrawLine(
                screen_points[i][0], screen_points[i][1],
                screen_points[i + 1][0], screen_points[i + 1][1]
            )
        # Draw line from last point to current mouse position
        if screen_points:
            dc.DrawLine(
                screen_points[-1][0], screen_points[-1][1],
                mouse_pos.x, mouse_pos.y
            )
    else:
        # Draw temporary straight line for other edge types
        dc.DrawLine(start_pos[0], start_pos[1], mouse_pos.x, mouse_pos.y)
    
    # Restore the rotation transformation if we temporarily removed it
    if restore_state and hasattr(dc, 'GetGraphicsContext'):
        gc = dc.GetGraphicsContext()
        if gc:
            size = graph_canvas.GetSize()
            center_x = size.width // 2
            center_y = size.height // 2
            gc.PushState()
            gc.Translate(center_x, center_y)
            gc.Rotate(math.radians(graph_canvas.world_rotation))
            gc.Translate(-center_x, -center_y)

 
def draw_edge_endpoint_dragging(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """Draw visual feedback while dragging edge endpoints (not affected by world rotation)."""

    if not graph_canvas.dragging_edge or not graph_canvas.dragging_endpoint:
        return
        
    # Temporarily exit the rotated world transformation if needed
    restore_state = False
    if graph_canvas.world_rotation != 0.0 and hasattr(dc, 'GetGraphicsContext'):
        gc = dc.GetGraphicsContext()
        if gc:
            gc.PopState()  # Temporarily exit the rotated world
            restore_state = True
        
    source_node = graph_canvas.graph.get_node(graph_canvas.dragging_edge.source_id)
    target_node = graph_canvas.graph.get_node(graph_canvas.dragging_edge.target_id)
    
    if not source_node or not target_node:
        return
        
    mouse_pos = graph_canvas.ScreenToClient(wx.GetMousePosition())
    
    # Get the positions
    source_screen = graph_canvas.world_to_screen(source_node.x, source_node.y)
    target_screen = graph_canvas.world_to_screen(target_node.x, target_node.y)
    
    # Draw the edge with one endpoint following the mouse
    dc.SetPen(wx.Pen(wx.Colour(255, 100, 100), 3, wx.PENSTYLE_DOT))  # Red dashed line
    
    if graph_canvas.dragging_endpoint == 'source':
        # Mouse position -> target
        dc.DrawLine(mouse_pos.x, mouse_pos.y, target_screen[0], target_screen[1])
    else:  # target
        # Source -> mouse position  
        dc.DrawLine(source_screen[0], source_screen[1], mouse_pos.x, mouse_pos.y)
    
    # Restore the rotation transformation if we temporarily removed it
    if restore_state and hasattr(dc, 'GetGraphicsContext'):
        gc = dc.GetGraphicsContext()
        if gc:
            size = graph_canvas.GetSize()
            center_x = size.width // 2
            center_y = size.height // 2
            gc.PushState()
            gc.Translate(center_x, center_y)
            gc.Rotate(math.radians(graph_canvas.world_rotation))
            gc.Translate(-center_x, -center_y)


def draw_rotation_center_dot(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """Draw a dot at the rotation center during rotation."""
    print("DEBUG: Drawing rotation center dot")
    
    # For world rotation, ALWAYS use screen center - this is the fixed rotation point
    size = graph_canvas.GetSize()
    center_x = size.width / 2.0  # Use float for precision
    center_y = size.height / 2.0  # Use float for precision
    print(f"DEBUG: World rotation center fixed at screen center: ({center_x}, {center_y})")
    
    # Scale dot size with zoom
    base_radius = 8
    dot_radius = max(4, int(base_radius * graph_canvas.zoom))
    print(f"DEBUG: Dot radius: {dot_radius} (zoom: {graph_canvas.zoom})")
    
    # Draw the dot using regular DC (simpler and more reliable)
    color = graph_canvas.rotation_center_color if hasattr(graph_canvas, 'rotation_center_color') else (255, 0, 0)
    print(f"DEBUG: Using color: {color}")
    
    # Set up drawing style
    dc.SetBrush(wx.Brush(wx.Colour(*color)))
    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))  # Black border
    
    # Draw the dot
    dc.DrawCircle(int(center_x), int(center_y), dot_radius)
    
    print(f"DEBUG: 🔴 Drew rotation center dot at ({center_x}, {center_y})")
    print("DEBUG: Finished drawing rotation center dot")


def draw_element_rotation_center_dot(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """Draw a red dot at the center of the rotating element."""

    if not graph_canvas.rotating_element:
        return
    # Temporarily exit world transforms to draw in screen coordinates
    restore_state = False
    gc = dc.GetGraphicsContext() if hasattr(dc, 'GetGraphicsContext') else None
    if gc:
        try:
            gc.PopState()
            restore_state = True
        except Exception as e:
            print(f"DEBUG: Could not pop state for element rotation dot: {e}")

    # Get element center in screen coordinates via world_to_screen (already includes rotation)
    center_pos = graph_canvas.world_to_screen(graph_canvas.rotating_element.x, graph_canvas.rotating_element.y)
    center_x = int(center_pos[0])
    center_y = int(center_pos[1])

    # Draw red dot
    dc.SetPen(wx.Pen(wx.Colour(255, 0, 0), 3))  # Red pen
    dc.SetBrush(wx.Brush(wx.Colour(255, 0, 0)))  # Red fill
    dot_radius = 8
    dc.DrawCircle(center_x, center_y, dot_radius)
    print(f"DEBUG: Drew element rotation center dot at ({center_x}, {center_y}) for node {graph_canvas.rotating_element.id}")

    # Restore world transforms for subsequent drawing
    if restore_state and gc:
        try:
            gc.PushState()
            # Apply Scale then Translate to match draw order
            gc.Scale(graph_canvas.zoom, graph_canvas.zoom)
            gc.Translate(graph_canvas.pan_x, graph_canvas.pan_y)
            # Reapply world rotation about screen center
            if graph_canvas.world_rotation != 0.0:
                size = graph_canvas.GetSize()
                screen_center_x = size.width / 2.0
                screen_center_y = size.height / 2.0
                transformed_center_x = (screen_center_x - graph_canvas.pan_x) / graph_canvas.zoom
                transformed_center_y = (screen_center_y - graph_canvas.pan_y) / graph_canvas.zoom
                gc.Translate(transformed_center_x, transformed_center_y)
                gc.Rotate(math.radians(graph_canvas.world_rotation))
                gc.Translate(-transformed_center_x, -transformed_center_y)
        except Exception as e:
            print(f"DEBUG: Could not restore state after element rotation dot: {e}")


def on_paint(graph_canvas: "m_graph_canvas.GraphCanvas", event):
    """Handle paint events. If MVU adapter is present, route through MVU-aware draw."""

    dc = wx.PaintDC(graph_canvas)
    model = None
    try:
        main_window = getattr(graph_canvas, 'main_window', None)
        if main_window is not None and hasattr(main_window, 'mvu_adapter'):
            model = main_window.mvu_adapter.model
    except Exception:
        model = None

    if model is not None:
        draw_mvu(graph_canvas, dc, model)
    else:
        draw(graph_canvas, dc)


@contextmanager
def world_transform(gc, graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Context manager to apply the unified world transform.

    Order (effective on points): Scale -> Rotate -> Translate(center + pan).
    """
    gc.PushState()
    try:
        size = graph_canvas.GetSize()
        center_x = size.width / 2.0
        center_y = size.height / 2.0
        # Align with desired world_to_screen transform: Translate(center+pan) -> Rotate -> Scale
        gc.Translate(center_x + graph_canvas.pan_x, center_y + graph_canvas.pan_y)
        if graph_canvas.world_rotation != 0.0:
            gc.Rotate(math.radians(graph_canvas.world_rotation))
        gc.Scale(graph_canvas.zoom, graph_canvas.zoom)
        yield
    finally:
        gc.PopState()


def draw(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """Draw the graph on the device context."""
    print("DEBUG: Starting draw function")

    # Track if we've pushed a state
    state_pushed = False

    try:
        # Determine background color based on grid visibility
        if graph_canvas.grid_style != "none":
            spacing = graph_canvas.grid_spacing * graph_canvas.zoom
            if spacing < 5:  # Grid too small to see, use grid color as background
                background = graph_canvas.grid_color
            else:
                background = graph_canvas.background_color
        else:
            background = graph_canvas.background_color
        
        # Always clear background with solid color first
        dc.SetBackground(wx.Brush(wx.Colour(*background)))
        dc.Clear()
        print("DEBUG: Cleared background")
        
        # Draw background images right after clearing, before any transformations
        if hasattr(graph_canvas, 'background_manager') and graph_canvas.background_manager:
            try:
                print("DEBUG: Drawing background layers")
                graph_canvas.background_manager.draw_layers(dc)
            except Exception as e:
                print(f"DEBUG: Error drawing background layers: {e}")

        # Enable antialiasing if requested
        if graph_canvas.antialias:
            try:
                dc = wx.GCDC(dc)
                print("DEBUG: Created GCDC for antialiasing")
            except Exception as e:
                print(f"DEBUG: Failed to create GCDC: {e}")
                return

        # Get graphics context
        gc = dc.GetGraphicsContext() if hasattr(dc, 'GetGraphicsContext') else None
        if not gc:
            print("DEBUG: No graphics context available for drawing")
            return
        print("DEBUG: Got graphics context")
        
        # Apply unified world transform for world-space drawing
        gc.PushState()
        state_pushed = True
        print("DEBUG: Pushed initial state")
        with world_transform(gc, graph_canvas):
            print(f"DEBUG: Applied world_transform: pan=({graph_canvas.pan_x:.1f},{graph_canvas.pan_y:.1f}) zoom={graph_canvas.zoom:.6f} rot={graph_canvas.world_rotation}°")
        
        # Draw grid-aligned visuals (checkerboard and grid) under the world transform
        with world_transform(gc, graph_canvas):
            # Draw checkboard background if enabled (rotates/moves/scales with world)
            if graph_canvas.checkerboard_background:
                # Check if checkboard has been temporarily disabled due to crashes
                if not hasattr(graph_canvas, '_checkboard_crash_disabled'):
                    graph_canvas._checkboard_crash_disabled = False
                if not graph_canvas._checkboard_crash_disabled:
                    try:
                        result = draw_checkboard_aligned_with_grid(graph_canvas, dc)
                        if isinstance(result, tuple):
                            squares_drawn, c1, c2 = result
                            if squares_drawn < 0:
                                print(f"DEBUG: 🏁 Checkerboard blended fill path used, color={c1}")
                            else:
                                print(f"DEBUG: 🏁 Drew checkerboard: {squares_drawn} squares, color1={c1}, color2={c2}")
                        else:
                            print("DEBUG: 🏁 Drew checkerboard (no return info)")
                    except Exception as e:
                        print(f"DEBUG: 🔴 Checkboard drawing failed: {e}")
                        # Temporarily disable checkboard to prevent repeated crashes
                        print("DEBUG: 🛑 TEMPORARILY disabling checkboard due to crash - restart app to re-enable")
                        graph_canvas._checkboard_crash_disabled = True
                        graph_canvas.checkerboard_background = False
                        # Update UI to reflect this change
                        if hasattr(graph_canvas, 'main_window') and hasattr(graph_canvas.main_window, 'checkboard_bg_cb'):
                            try:
                                graph_canvas.main_window.checkboard_bg_cb.SetValue(False)
                            except:
                                pass  # Ignore UI update errors
        
        # Draw grid/dots using the main grid drawing function
        print(f"DEBUG: Grid check - style: '{graph_canvas.grid_style}', spacing: {graph_canvas.grid_spacing}")
        if graph_canvas.grid_style != "none":
            print("DEBUG: Grid enabled, drawing with proper bounds calculation")
            draw_grid(graph_canvas, dc, gc)
            print("DEBUG: Called draw_grid")
        else:
            print("DEBUG: Grid disabled (style is 'none')")
            
        # Duplicate checkerboard and grid drawing removed; handled inside world transform above
        
        # Draw zoom center crosshair for zoom feedback in SCREEN coordinates (stays at zoom center)
        if hasattr(graph_canvas, 'current_mouse_pos') and graph_canvas.current_mouse_pos:
            # Ensure we are in screen space for the crosshair
            if state_pushed:
                try:
                    gc.PopState()
                    state_pushed = False
                except Exception as e:
                    print(f"DEBUG: Could not pop world state before crosshair: {e}")
            gc.PushState()
            
            # Use locked zoom center if available, otherwise use current mouse position
            if hasattr(graph_canvas, 'zoom_center_locked') and graph_canvas.zoom_center_locked and graph_canvas.zoom_center_screen_pos:
                # Use the locked screen position directly (no conversion needed)
                zoom_center_screen = graph_canvas.zoom_center_screen_pos
                print(f"DEBUG: 🎯 CROSSHAIR DRAWN AT: screen=({zoom_center_screen[0]}, {zoom_center_screen[1]}) - FIXED POSITION")
                print(f"DEBUG: 🔒 LOCKED WORLD POS: ({graph_canvas.zoom_center_world_pos[0]:.1f}, {graph_canvas.zoom_center_world_pos[1]:.1f})")
            else:
                # Use current mouse position (for when not zooming)
                zoom_center_screen = (graph_canvas.current_mouse_pos.x, graph_canvas.current_mouse_pos.y)
                # Convert mouse position to world coordinates for debugging
                mouse_world = graph_canvas.screen_to_world(graph_canvas.current_mouse_pos.x, graph_canvas.current_mouse_pos.y)
                print(f"DEBUG: 🖱️ CROSSHAIR DRAWN AT: world=({mouse_world[0]:.1f}, {mouse_world[1]:.1f}) -> screen=({zoom_center_screen[0]:.0f}, {zoom_center_screen[1]:.0f})")
            
            # Draw crosshair at the screen position of the world position
            crosshair_size = 20  # Fixed size in screen pixels
            dc.SetPen(wx.Pen(wx.Colour(255, 0, 0), 2))  # Red crosshair
            dc.DrawLine(
                int(zoom_center_screen[0] - crosshair_size), 
                int(zoom_center_screen[1]), 
                int(zoom_center_screen[0] + crosshair_size), 
                int(zoom_center_screen[1])
            )
            dc.DrawLine(
                int(zoom_center_screen[0]), 
                int(zoom_center_screen[1] - crosshair_size), 
                int(zoom_center_screen[0]), 
                int(zoom_center_screen[1] + crosshair_size)
            )
            
            # Draw a circle at the center
            dc.SetBrush(wx.Brush(wx.Colour(255, 0, 0)))
            dc.DrawCircle(int(zoom_center_screen[0]), int(zoom_center_screen[1]), 5)
            print(f"DEBUG: Drew zoom center crosshair at SCREEN position ({zoom_center_screen[0]}, {zoom_center_screen[1]}) - {'locked' if hasattr(graph_canvas, 'zoom_center_locked') and graph_canvas.zoom_center_locked else 'current'}")
            
            # Done with crosshair; nothing to restore here as edges will manage their own state
            gc.PopState()

        # Draw edges first (so they appear behind nodes, only visible ones)
        # Edges are drawn in SCREEN coordinates; temporarily exit world transforms
        # Edges are drawn in SCREEN coordinates; no world transform applied

        # Draw edges in world coordinates under the unified transform
        edge_count = 0
        with world_transform(gc, graph_canvas):
            for edge in graph_canvas.graph.get_all_edges():
                if hasattr(edge, 'visible') and edge.visible:
                    draw_edge(graph_canvas, dc, edge)
                    edge_count += 1
                elif not hasattr(edge, 'visible'):
                    # Default to visible if no visible property
                    draw_edge(graph_canvas, dc, edge)
                    edge_count += 1
        print(f"DEBUG: Drew {edge_count} edges")

        # Draw nodes (only visible ones) under world transform
        visible_count = 0
        total_count = 0
        with world_transform(gc, graph_canvas):
            for node in graph_canvas.graph.get_all_nodes():
                total_count += 1
                if node.visible:
                    visible_count += 1
                    draw_node(graph_canvas, dc, node)
        print(f"DEBUG: Drew {visible_count}/{total_count} nodes")
        
        # Debug: Report if any nodes are invisible
        if visible_count < total_count:
            invisible_count = total_count - visible_count
            print(f"DEBUG: 👻 Drawing phase - {invisible_count} of {total_count} nodes are invisible")

        # Draw edge endpoint dots on top of connection points for selected edges (screen space)
        for edge in graph_canvas.graph.get_all_edges():
            if edge.selected and (hasattr(edge, 'visible') and edge.visible or not hasattr(edge, 'visible')):
                source_node = graph_canvas.graph.get_node(edge.source_id)
                target_node = graph_canvas.graph.get_node(edge.target_id)
                if source_node and target_node:
                    # Use connection-point adjusted endpoints for accurate dot placement
                    source_screen = graph_canvas.world_to_screen(source_node.x, source_node.y)
                    target_screen = graph_canvas.world_to_screen(target_node.x, target_node.y)
                    source_adjusted = graph_canvas.calculate_line_endpoint(source_node, target_node, source_screen, target_screen, True, edge)
                    target_adjusted = graph_canvas.calculate_line_endpoint(target_node, source_node, target_screen, source_screen, False, edge)
                    draw_edge_endpoint_dots(graph_canvas, dc, source_adjusted, target_adjusted, edge)

        # Draw control points and connection points
        if graph_canvas.control_points_enabled or graph_canvas.tool == "edge":
            for edge in graph_canvas.graph.get_all_edges():
                # Show control points only for selected edges
                # Show connection points for all edges when using edge tool, otherwise only for selected edges
                if (edge.selected or (graph_canvas.tool == "edge")) and (hasattr(edge, 'visible') and edge.visible or not hasattr(edge, 'visible')):
                    source_node = graph_canvas.graph.get_node(edge.source_id)
                    target_node = graph_canvas.graph.get_node(edge.target_id)
                    if source_node and target_node:
                        source_screen = graph_canvas.world_to_screen(source_node.x, source_node.y)
                        target_screen = graph_canvas.world_to_screen(target_node.x, target_node.y)
                        source_adjusted = graph_canvas.calculate_line_endpoint(source_node, target_node,
                                                                    source_screen, target_screen, True, edge)
                        target_adjusted = graph_canvas.calculate_line_endpoint(target_node, source_node,
                                                                    target_screen, source_screen, False, edge)
                        # Draw connection points for all edges in edge tool mode or selected edges
                        draw_edge_endpoint_dots(graph_canvas, dc, source_adjusted, target_adjusted, edge)
                    # Draw control points only for selected edges
                    if edge.selected:
                        draw_control_points(graph_canvas, dc, edge)
                    draw_arrow_position_control(graph_canvas, dc, edge)

        # Draw selection rectangle
        if graph_canvas.selection_rect:
            draw_selection_rect(graph_canvas, dc)

        # Draw temporary edge
        if graph_canvas.edge_start_node and graph_canvas.tool == "edge":
            draw_temp_edge(graph_canvas, dc)
            
        # Draw edge endpoint dragging feedback
        if graph_canvas.dragging_edge_endpoint and graph_canvas.dragging_edge:
            draw_edge_endpoint_dragging(graph_canvas, dc)
        
        # Note: Do not PopState here; UI elements manage their own temporary state pops/pushes.
        
        # Draw drag-into-container visual feedback (in screen coordinates)
        if graph_canvas.dragging_into_container and graph_canvas.container_target:
            draw_container_target_feedback(graph_canvas, dc)
            
        # Draw containment drag visual feedback
        if graph_canvas.dragging_into_container:
            draw_drag_into_feedback(graph_canvas, dc)
        
        # Draw UI elements in screen coordinates (not affected by world rotation)
        # Draw rotation center dot if rotating
        if graph_canvas.show_rotation_center:
            draw_rotation_center_dot(graph_canvas, dc)
        
        # Draw element rotation center dot if element rotation tool is active
        if graph_canvas.show_element_rotation_center and graph_canvas.rotating_element:
            draw_element_rotation_center_dot(graph_canvas, dc)
                            
    except Exception as e:
        print(f"DEBUG: Error during drawing: {e}")
    finally:
        # Only pop state if we have pushed one and haven't already popped it
        if state_pushed and gc:
            try:
                gc.PopState()
                state_pushed = False  # Mark as popped
                print("DEBUG: Popped graphics context state in finally block")
            except Exception as e:
                print(f"DEBUG: Error popping state in finally: {e}")
                # Reset state flag to avoid future issues
                state_pushed = False


def draw_mvu(graph_canvas: "m_graph_canvas.GraphCanvas", dc, model):
    """MVU-aware drawing. Ensures canvas reflects MVU model before delegating to draw()."""
    try:
        # Keep canvas rotation in sync with MVU model
        if hasattr(model, 'rotation_deg') and hasattr(graph_canvas, 'set_world_rotation'):
            try:
                # Do not override interactive rotation while dragging via tool
                dragging = bool(getattr(graph_canvas, 'dragging_rotation', False))
                # Optionally skip a couple frames after release if requested by canvas
                skip_frames = int(getattr(graph_canvas, 'rotation_sync_skip_frames', 0) or 0)
                current_rot = float(getattr(graph_canvas, 'world_rotation', 0.0) or 0.0)
                new_rot = float(model.rotation_deg)
                if skip_frames > 0:
                    try:
                        setattr(graph_canvas, 'rotation_sync_skip_frames', skip_frames - 1)
                    except Exception:
                        pass
                elif not dragging and abs(current_rot - new_rot) > 1e-9:
                    # If model looks stale (e.g., 0) but canvas has a meaningful angle, prefer canvas -> model
                    if abs(current_rot) > 1e-6 and abs(new_rot) < 1e-6:
                        try:
                            mw = getattr(graph_canvas, 'main_window', None) or graph_canvas.GetParent().GetParent()
                            if hasattr(mw, 'mvu_adapter'):
                                from mvc_mvu.messages import make_message
                                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                                mw.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ROTATION, angle=current_rot))
                                print(f"DEBUG: draw_mvu reconciled model rotation -> {current_rot}°")
                        except Exception:
                            pass
                    else:
                        graph_canvas.set_world_rotation(new_rot)
            except Exception:
                pass

        # Grid visibility
        if hasattr(model, 'grid_visible'):
            try:
                graph_canvas.grid_style = 'grid' if bool(model.grid_visible) else 'none'
            except Exception:
                pass

        # Snapping
        if hasattr(model, 'snap_enabled'):
            try:
                enabled = bool(model.snap_enabled)
                if hasattr(graph_canvas, 'grid_snapping_enabled'):
                    graph_canvas.grid_snapping_enabled = enabled
                if hasattr(graph_canvas, 'snap_to_grid'):
                    graph_canvas.snap_to_grid = enabled
            except Exception:
                pass
    except Exception:
        # Non-fatal pre-sync issues shouldn't block drawing
        pass

    draw(graph_canvas, dc)

def draw_grid(graph_canvas: "m_graph_canvas.GraphCanvas", dc, gc):
    """Draw the grid or dots based on the current style."""
    print(f"DEBUG: ===== DRAW_GRID START =====")
    print(f"DEBUG: Grid style: '{graph_canvas.grid_style}'")
    print(f"DEBUG: Grid spacing: {graph_canvas.grid_spacing}")
    print(f"DEBUG: Current zoom: {graph_canvas.zoom}")
    print(f"DEBUG: DC type: {type(dc)}")

    if graph_canvas.grid_style == "none":
        print("DEBUG: Grid style is none, skipping")
        return

    # Get graphics context for world coordinate drawing (same as nodes)
    gc = dc.GetGraphicsContext() if hasattr(dc, 'GetGraphicsContext') else None
    if not gc:
        print("DEBUG: No graphics context available, falling back to screen coordinate drawing")
        # Fallback to the old method if no graphics context
        draw_grid_screen_coordinates(graph_canvas, dc)
        return

    # Use the configured grid colors
    grid_color = graph_canvas.grid_color
    pen_width = 1  # Normal line width
    
    print(f"DEBUG: Using configured grid color: {grid_color}")
    print(f"DEBUG: Using pen width: {pen_width}")
    
    # Set up graphics context for grid drawing
    gc.SetPen(wx.Pen(wx.Colour(*grid_color), pen_width))
    
    # Create and set pen
    pen = wx.Pen(wx.Colour(*grid_color), pen_width)
    dc.SetPen(pen)
    print(f"DEBUG: Set pen with color {grid_color} and width {pen_width}")
    
    # Also set brush for dots
    brush = wx.Brush(wx.Colour(*grid_color))
    dc.SetBrush(brush)
    print(f"DEBUG: Set brush with color {grid_color}")

    # Grid draws in world coordinates, so it transforms with world rotation/pan
    world_spacing = graph_canvas.grid_spacing
    
    print(f"DEBUG: Drawing grid in world coordinates with spacing {world_spacing}")
    
    # Calculate world bounds of visible area with rotation consideration
    size = graph_canvas.GetSize()
    
    # For rotation, we need to calculate a larger bounding box to ensure grid coverage
    if graph_canvas.world_rotation != 0.0:
        # Calculate the diagonal of the screen to ensure full coverage under rotation
        diagonal = math.sqrt(size.width**2 + size.height**2)
        # Use diagonal as both width and height for safe coverage, with extra margin
        extended_size = diagonal * 1.5  # Extra margin for safety
        
        # Center the extended area around current view
        center_x = size.width / 2.0
        center_y = size.height / 2.0
        
        # Calculate extended screen bounds
        screen_left = center_x - extended_size / 2
        screen_right = center_x + extended_size / 2
        screen_top = center_y - extended_size / 2
        screen_bottom = center_y + extended_size / 2
        
        print(f"DEBUG: Extended screen bounds for rotation: ({screen_left:.1f}, {screen_top:.1f}) to ({screen_right:.1f}, {screen_bottom:.1f})")
    else:
        # No rotation, use very generous screen bounds to ensure full coverage
        # Use a much more aggressive approach to ensure grid covers entire visible world
        # Calculate world dimensions based on current zoom
        world_width = size.width / graph_canvas.zoom
        world_height = size.height / graph_canvas.zoom
        
        # Use very generous margins - at least 2x the world dimensions to ensure full coverage
        # This ensures we always have enough grid coverage regardless of zoom level
        margin_x = world_width * 2.0  # 2x world width on each side
        margin_y = world_height * 2.0  # 2x world height on top/bottom
        
        screen_left = -margin_x
        screen_right = size.width + margin_x
        screen_top = -margin_y
        screen_bottom = size.height + margin_y
        
        print(f"DEBUG: Screen bounds with margin: ({screen_left:.1f}, {screen_top:.1f}) to ({screen_right:.1f}, {screen_bottom:.1f})")
        print(f"DEBUG: Margin calculation: world_width={world_width:.1f}, world_height={world_height:.1f}, margin_x={margin_x:.1f}, margin_y={margin_y:.1f}")
    
    # Convert screen corners to world coordinates using proper screen_to_world transformation
    # This properly handles rotation, zoom, and pan
    world_corners = [
        graph_canvas.screen_to_world(int(screen_left), int(screen_top)),
        graph_canvas.screen_to_world(int(screen_right), int(screen_top)),
        graph_canvas.screen_to_world(int(screen_right), int(screen_bottom)),
        graph_canvas.screen_to_world(int(screen_left), int(screen_bottom))
    ]
    
    # Find bounding box of all world corners
    world_left = min(corner[0] for corner in world_corners)
    world_right = max(corner[0] for corner in world_corners)
    world_top = min(corner[1] for corner in world_corners)
    world_bottom = max(corner[1] for corner in world_corners)
    
    print(f"DEBUG: World bounds (rotation={graph_canvas.world_rotation:.1f}°): ({world_left:.1f}, {world_top:.1f}) to ({world_right:.1f}, {world_bottom:.1f})")
    
    if graph_canvas.grid_style == "grid":
        print(f"DEBUG: Drawing grid lines in world coordinates...")
        
        # Find grid lines that intersect the visible world area
        # Add extra spacing to ensure full coverage
        extra_spacing = world_spacing * 2
        
        with world_transform(gc, graph_canvas):
            # Vertical lines - draw in world coordinates using graphics context (same as nodes)
            line_count = 0
            # Align to world origin (0,0) by using modulo to find the first grid line
            first_vertical_x = math.floor((world_left - extra_spacing) / world_spacing) * world_spacing
            # Ensure we start from a grid line that's aligned to world origin
            if first_vertical_x < 0:
                first_vertical_x = math.floor(first_vertical_x / world_spacing) * world_spacing
            x = first_vertical_x
            while x <= world_right + extra_spacing:
                # Draw in world coordinates using graphics context (same coordinate system as nodes)
                gc.StrokeLine(x, world_top - extra_spacing, x, world_bottom + extra_spacing)
                line_count += 1
                x += world_spacing
            print(f"DEBUG: Drew {line_count} vertical grid lines starting from {first_vertical_x}")
            
            # Horizontal lines - draw in world coordinates using graphics context (same as nodes)
            line_count = 0
            # Align to world origin (0,0) by using modulo to find the first grid line
            first_horizontal_y = math.floor((world_top - extra_spacing) / world_spacing) * world_spacing
            # Ensure we start from a grid line that's aligned to world origin
            if first_horizontal_y < 0:
                first_horizontal_y = math.floor(first_horizontal_y / world_spacing) * world_spacing
            y = first_horizontal_y
            while y <= world_bottom + extra_spacing:
                # Draw in world coordinates using graphics context (same coordinate system as nodes)
                gc.StrokeLine(world_left - extra_spacing, y, world_right + extra_spacing, y)
                line_count += 1
                y += world_spacing
            print(f"DEBUG: Drew {line_count} horizontal grid lines starting from {first_horizontal_y}")
        
    elif graph_canvas.grid_style == "dots":
        print(f"DEBUG: Drawing dots in world coordinates...")
        # Draw dots at grid intersections in world coordinates
        dot_count = 0
        dot_radius = max(1, int(graph_canvas.dot_size if hasattr(graph_canvas, 'dot_size') else 2))
        
        # Add extra spacing to ensure full coverage
        extra_spacing = world_spacing * 2
        
        with world_transform(gc, graph_canvas):
            # Find grid intersections in visible world area with extra coverage
            first_y = math.floor((world_top - extra_spacing) / world_spacing) * world_spacing
            y = first_y
            while y <= world_bottom + extra_spacing:
                first_x = math.floor((world_left - extra_spacing) / world_spacing) * world_spacing
                x = first_x
                while x <= world_right + extra_spacing:
                    # Draw in world coordinates using graphics context (same coordinate system as nodes)
                    gc.DrawEllipse(x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2)
                    dot_count += 1
                    x += world_spacing
                y += world_spacing
        print(f"DEBUG: Drew {dot_count} dots")

    print("DEBUG: ===== DRAW_GRID END =====")
    print("DEBUG: If you don't see grid lines or test rectangles, there may be an issue with the DC or drawing order")


def draw_grid_screen_coordinates(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """Fallback grid drawing using screen coordinates (old method)."""
    print("DEBUG: Using fallback screen coordinate grid drawing")
    
    # Use the configured grid colors
    grid_color = graph_canvas.grid_color
    pen_width = 1
    
    # Create and set pen
    pen = wx.Pen(wx.Colour(*grid_color), pen_width)
    dc.SetPen(pen)
    
    # Get canvas size
    size = graph_canvas.GetSize()
    world_spacing = graph_canvas.grid_spacing
    
    # Calculate world bounds (same logic as main function)
    if graph_canvas.world_rotation != 0.0:
        # Calculate the rotated bounding box for full coverage
        angle_rad = math.radians(graph_canvas.world_rotation)
        cos_a = abs(math.cos(angle_rad))
        sin_a = abs(math.sin(angle_rad))
        
        rotated_width = size.width * cos_a + size.height * sin_a
        rotated_height = size.width * sin_a + size.height * cos_a
        
        x_extension = int((rotated_width - size.width) / 2) + 100
        y_extension = int((rotated_height - size.height) / 2) + 100
        
        screen_left = -x_extension
        screen_right = size.width + x_extension
        screen_top = -y_extension
        screen_bottom = size.height + y_extension
    else:
        # No rotation, use very generous screen bounds
        world_width = size.width / graph_canvas.zoom
        world_height = size.height / graph_canvas.zoom
        
        margin_x = world_width * 2.0
        margin_y = world_height * 2.0
        
        screen_left = -margin_x
        screen_right = size.width + margin_x
        screen_top = -margin_y
        screen_bottom = size.height + margin_y
    
    # Convert screen corners to world coordinates
    world_corners = [
        graph_canvas.screen_to_world(int(screen_left), int(screen_top)),
        graph_canvas.screen_to_world(int(screen_right), int(screen_top)),
        graph_canvas.screen_to_world(int(screen_right), int(screen_bottom)),
        graph_canvas.screen_to_world(int(screen_left), int(screen_bottom))
    ]
    
    # Find bounding box of all world corners
    world_left = min(corner[0] for corner in world_corners)
    world_right = max(corner[0] for corner in world_corners)
    world_top = min(corner[1] for corner in world_corners)
    world_bottom = max(corner[1] for corner in world_corners)
    
    # Add extra spacing
    extra_spacing = world_spacing * 2
    
    if graph_canvas.grid_style == "lines":
        # Vertical lines
        first_vertical_x = math.floor((world_left - extra_spacing) / world_spacing) * world_spacing
        x = first_vertical_x
        while x <= world_right + extra_spacing:
            start_screen = graph_canvas.world_to_screen(x, world_top - extra_spacing)
            end_screen = graph_canvas.world_to_screen(x, world_bottom + extra_spacing)
            dc.DrawLine(start_screen[0], start_screen[1], end_screen[0], end_screen[1])
            x += world_spacing
        
        # Horizontal lines
        first_horizontal_y = math.floor((world_top - extra_spacing) / world_spacing) * world_spacing
        y = first_horizontal_y
        while y <= world_bottom + extra_spacing:
            start_screen = graph_canvas.world_to_screen(world_left - extra_spacing, y)
            end_screen = graph_canvas.world_to_screen(world_right + extra_spacing, y)
            dc.DrawLine(start_screen[0], start_screen[1], end_screen[0], end_screen[1])
            y += world_spacing
    
    elif graph_canvas.grid_style == "dots":
        # Draw dots at grid intersections
        dot_radius = max(1, int(graph_canvas.dot_size if hasattr(graph_canvas, 'dot_size') else 2))
        first_y = math.floor((world_top - extra_spacing) / world_spacing) * world_spacing
        y = first_y
        while y <= world_bottom + extra_spacing:
            first_x = math.floor((world_left - extra_spacing) / world_spacing) * world_spacing
            x = first_x
            while x <= world_right + extra_spacing:
                screen_pos = graph_canvas.world_to_screen(x, y)
                dc.DrawCircle(screen_pos[0], screen_pos[1], dot_radius)
                x += world_spacing
            y += world_spacing


def draw_grid_relative_to_reference_points(graph_canvas, dc):
    """
    Draw grid lines or dots relative to reference points (crosshair and rotation center).
    This ensures grid intersections stay under the reference points during zoom/rotation.
    """
    print("DEBUG: ===== DRAW_GRID_RELATIVE_TO_REFERENCE_POINTS START =====")
    
    if not graph_canvas or not dc:
        print("DEBUG: No graph_canvas or dc provided")
        return

    if graph_canvas.grid_style == "none":
        print("DEBUG: Grid style is none, skipping")
        return

    # Use the configured grid colors
    grid_color = graph_canvas.grid_color
    pen_width = 1  # Normal line width
    
    print(f"DEBUG: Using configured grid color: {grid_color}")
    print(f"DEBUG: Using pen width: {pen_width}")
    
    # Create and set pen
    pen = wx.Pen(wx.Colour(*grid_color), pen_width)
    dc.SetPen(pen)
    print(f"DEBUG: Set pen with color {grid_color} and width {pen_width}")
    
    # Also set brush for dots
    brush = wx.Brush(wx.Colour(*grid_color))
    dc.SetBrush(brush)
    print(f"DEBUG: Set brush with color {grid_color}")

    # Get reference points
    size = graph_canvas.GetSize()
    screen_center_x = size.width / 2.0
    screen_center_y = size.height / 2.0
    
    # Get cursor position if available
    cursor_x = screen_center_x
    cursor_y = screen_center_y
    if hasattr(graph_canvas, 'current_mouse_pos') and graph_canvas.current_mouse_pos:
        cursor_x = graph_canvas.current_mouse_pos.x
        cursor_y = graph_canvas.current_mouse_pos.y
    
    print(f"DEBUG: Reference points - Cursor: ({cursor_x:.1f}, {cursor_y:.1f}), Center: ({screen_center_x:.1f}, {screen_center_y:.1f})")
    
    # Convert reference points to world coordinates
    cursor_world_x, cursor_world_y = graph_canvas.screen_to_world(cursor_x, cursor_y)
    center_world_x, center_world_y = graph_canvas.screen_to_world(screen_center_x, screen_center_y)
    
    print(f"DEBUG: World reference points - Cursor: ({cursor_world_x:.1f}, {cursor_world_y:.1f}), Center: ({center_world_x:.1f}, {center_world_y:.1f})")
    
    # Calculate grid spacing in world coordinates
    world_spacing = graph_canvas.grid_spacing
    
    # Find the grid intersections closest to the reference points
    cursor_grid_x = round(cursor_world_x / world_spacing) * world_spacing
    cursor_grid_y = round(cursor_world_y / world_spacing) * world_spacing
    center_grid_x = round(center_world_x / world_spacing) * world_spacing
    center_grid_y = round(center_world_y / world_spacing) * world_spacing
    
    print(f"DEBUG: Grid intersections - Cursor: ({cursor_grid_x:.1f}, {cursor_grid_y:.1f}), Center: ({center_grid_x:.1f}, {center_grid_y:.1f})")
    
    # Calculate visible area with margin based on actual canvas size
    # Convert screen dimensions to world coordinates for proper margin calculation
    screen_width = size.width
    screen_height = size.height
    
    # Calculate world dimensions based on current zoom
    world_width = screen_width / graph_canvas.zoom
    world_height = screen_height / graph_canvas.zoom
    
    # Use a margin that's proportional to the visible area
    margin_x = world_width * 0.5  # 50% margin on each side
    margin_y = world_height * 0.5  # 50% margin on top/bottom
    
    world_left = min(cursor_grid_x, center_grid_x) - margin_x
    world_right = max(cursor_grid_x, center_grid_x) + margin_x
    world_top = min(cursor_grid_y, center_grid_y) - margin_y
    world_bottom = max(cursor_grid_y, center_grid_y) + margin_y
    
    print(f"DEBUG: Grid bounds: ({world_left:.1f}, {world_top:.1f}) to ({world_right:.1f}, {world_bottom:.1f})")
    
    if graph_canvas.grid_style == "grid":
        print(f"DEBUG: Drawing grid lines relative to reference points...")
        
        # Draw vertical lines
        line_count = 0
        x = world_left
        while x <= world_right:
            # Convert world coordinates to screen coordinates before drawing
            start_screen = graph_canvas.world_to_screen(x, world_top)
            end_screen = graph_canvas.world_to_screen(x, world_bottom)
            dc.DrawLine(start_screen[0], start_screen[1], end_screen[0], end_screen[1])
            line_count += 1
            x += world_spacing
        print(f"DEBUG: Drew {line_count} vertical grid lines")
        
        # Draw horizontal lines
        line_count = 0
        y = world_top
        while y <= world_bottom:
            # Convert world coordinates to screen coordinates before drawing
            start_screen = graph_canvas.world_to_screen(world_left, y)
            end_screen = graph_canvas.world_to_screen(world_right, y)
            dc.DrawLine(start_screen[0], start_screen[1], end_screen[0], end_screen[1])
            line_count += 1
            y += world_spacing
        print(f"DEBUG: Drew {line_count} horizontal grid lines")
        
    elif graph_canvas.grid_style == "dots":
        print(f"DEBUG: Drawing grid dots relative to reference points...")
        
        # Draw dots
        dot_count = 0
        x = world_left
        while x <= world_right:
            y = world_top
            while y <= world_bottom:
                # Convert world coordinates to screen coordinates before drawing
                screen_pos = graph_canvas.world_to_screen(x, y)
                dc.DrawCircle(screen_pos[0], screen_pos[1], 2)
                dot_count += 1
                y += world_spacing
            x += world_spacing
        print(f"DEBUG: Drew {dot_count} grid dots")
    
    print("DEBUG: ===== DRAW_GRID_RELATIVE_TO_REFERENCE_POINTS END =====")


def draw_checkboard_background(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """Draw checkboard background pattern aligned with the grid (in world coordinates)."""

    size = graph_canvas.GetSize()
    spacing = graph_canvas.grid_spacing * graph_canvas.zoom

    if spacing < 2:  # Don't draw checkboard if too small
        return

    # Calculate color based on zoom level - blend at max zoom out
    if graph_canvas.zoom <= graph_canvas.min_zoom * 1.1:  # At or near max zoom out
        # Blend the two checker colors with safe fallbacks
        try:
            if isinstance(graph_canvas.checker_color1, wx.Colour) and isinstance(graph_canvas.checker_color2, wx.Colour):
                r1, g1, b1 = graph_canvas.checker_color1.Red(), graph_canvas.checker_color1.Green(), graph_canvas.checker_color1.Blue()
                r2, g2, b2 = graph_canvas.checker_color2.Red(), graph_canvas.checker_color2.Green(), graph_canvas.checker_color2.Blue()
            else:
                # Fallback to safe default colors
                r1, g1, b1 = 240, 240, 240  # Light gray
                r2, g2, b2 = graph_canvas.background_color[0], graph_canvas.background_color[1], graph_canvas.background_color[2]
            
            blended_r = int((r1 + r2) / 2)
            blended_g = int((g1 + g2) / 2) 
            blended_b = int((b1 + b2) / 2)
        except:
            # Ultimate fallback
            blended_r, blended_g, blended_b = 247, 247, 247  # Very light gray
            
        # Fill entire screen with blended color
        try:
            blended_color = wx.Colour(blended_r, blended_g, blended_b)
            if blended_color.IsOk():
                dc.SetBrush(wx.Brush(blended_color))
                dc.SetPen(wx.Pen(blended_color))
                dc.DrawRectangle(-size.width, -size.height, size.width * 3, size.height * 3)
            else:
                print("DEBUG: 🔴 Blended color is not OK, skipping checkboard")
        except Exception as e:
            print(f"DEBUG: 🔴 Error drawing blended checkboard: {e}")
        return

    # Calculate extended bounds for rotation (same logic as grid)
    if graph_canvas.world_rotation != 0.0:
        angle_rad = math.radians(graph_canvas.world_rotation)
        cos_a = abs(math.cos(angle_rad))
        sin_a = abs(math.sin(angle_rad))
        
        rotated_width = size.width * cos_a + size.height * sin_a
        rotated_height = size.width * sin_a + size.height * cos_a
        
        x_extension = int((rotated_width - size.width) / 2) + int(spacing)
        y_extension = int((rotated_height - size.height) / 2) + int(spacing)
        
        left = -x_extension
        right = size.width + x_extension
        top = -y_extension
        bottom = size.height + y_extension
    else:
        left = 0
        right = size.width
        top = 0
        bottom = size.height

    # Use exact same offset calculation as grid for perfect alignment
    offset_x = graph_canvas.pan_x % spacing
    offset_y = graph_canvas.pan_y % spacing

    # Draw checkboard pattern with same size as grid
    checker_size = int(spacing)
    
    # Start positions exactly like the grid
    start_x = int(offset_x)
    while start_x > left:
        start_x -= checker_size
    
    start_y = int(offset_y)
    while start_y > top:
        start_y -= checker_size

    # Draw checkboard squares without borders
    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 0))  # Invisible pen (no borders)
    
    # Create fresh color objects to avoid any corruption issues
    try:
        # Always create new wx.Colour objects to avoid any reference issues
        if hasattr(graph_canvas, 'checker_color1') and isinstance(graph_canvas.checker_color1, wx.Colour):
            r1, g1, b1 = graph_canvas.checker_color1.Red(), graph_canvas.checker_color1.Green(), graph_canvas.checker_color1.Blue()
            color1 = wx.Colour(r1, g1, b1)
        else:
            color1 = wx.Colour(240, 240, 240)  # Default light gray
            
        if hasattr(graph_canvas, 'checker_color2') and isinstance(graph_canvas.checker_color2, wx.Colour):
            r2, g2, b2 = graph_canvas.checker_color2.Red(), graph_canvas.checker_color2.Green(), graph_canvas.checker_color2.Blue()
            color2 = wx.Colour(r2, g2, b2)
        else:
            # Use background color as fallback
            try:
                bg_r, bg_g, bg_b = graph_canvas.background_color
                color2 = wx.Colour(bg_r, bg_g, bg_b)
            except:
                color2 = wx.Colour(255, 255, 255)  # White fallback
    except Exception as e:
        print(f"DEBUG: 🔴 Error creating checker colors: {e}")
        # Ultimate fallback colors
        color1 = wx.Colour(240, 240, 240)
        color2 = wx.Colour(255, 255, 255)
        
    # Validate colors are properly created
    if not color1.IsOk():
        print("DEBUG: 🔴 color1 is not OK, using safe fallback")
        color1 = wx.Colour(240, 240, 240)
    if not color2.IsOk():
        print("DEBUG: 🔴 color2 is not OK, using safe fallback")
        color2 = wx.Colour(255, 255, 255)
    
    y = start_y
    row = 0
    while y < bottom:
        x = start_x
        col = 0
        while x < right:
            # Determine which color to use (alternating pattern)
            try:
                if (row + col) % 2 == 0:
                    brush = wx.Brush(color1)
                else:
                    brush = wx.Brush(color2)
                
                dc.SetBrush(brush)
                
                # Only draw squares that intersect the visible area
                if x + checker_size > left and x < right and y + checker_size > top and y < bottom:
                    dc.DrawRectangle(int(x), int(y), checker_size, checker_size)
            except Exception as e:
                print(f"DEBUG: 🔴 Error drawing checkboard square at ({x}, {y}): {e}")
                # Skip this square and continue
            
            x += checker_size
            col += 1
        y += checker_size
        row += 1


def draw_checkboard_background_safe(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """Ultra-minimal checkboard with exhaustive debug logging to isolate crash location."""

    print("DEBUG: 🏁 Step 1: Starting ultra-safe checkboard")
    
    try:
        # Calculate spacing early so we can use it in zoom condition
        print("DEBUG: 🏁 Step 1.5: Calculating grid size for zoom condition")
        size = graph_canvas.GetSize()
        spacing = graph_canvas.grid_spacing * graph_canvas.zoom
        print(f"DEBUG: 🏁 Step 1.6: spacing = {graph_canvas.graph.spacing} * {graph_canvas.zoom} = {spacing}")
        
        print("DEBUG: 🏁 Step 2: Getting color attributes - trying multiple safe extraction methods")
        
        # Start with safe defaults
        color1_rgb = (240, 240, 240)  # Light gray default
        color2_rgb = graph_canvas.background_color  # Background color tuple (always safe)
        
        # Method 1: Try to get colors from UI buttons (safest method)
        print("DEBUG: 🏁 Step 2a: Trying to get colors from UI buttons")
        if hasattr(graph_canvas, 'main_window') and hasattr(graph_canvas.main_window, 'checker_color1_btn'):
            try:
                btn_color = graph_canvas.main_window.checker_color1_btn.GetBackgroundColour()
                if btn_color and btn_color.IsOk():
                    # Try the .Get() method first (safest)
                    try:
                        color1_tuple = btn_color.Get()
                        if len(color1_tuple) >= 3:
                            color1_rgb = color1_tuple[:3]  # Get RGB, ignore alpha
                            print(f"DEBUG: 🏁 Step 2b: Got color1 from button via Get(): {color1_rgb}")
                    except Exception as e:
                        print(f"DEBUG: 🔴 Step 2b Get() method failed: {e}")
                        # Try individual property access as fallback
                        try:
                            color1_rgb = (btn_color.red, btn_color.green, btn_color.blue)
                            print(f"DEBUG: 🏁 Step 2c: Got color1 from button properties: {color1_rgb}")
                        except Exception as e2:
                            print(f"DEBUG: 🔴 Step 2c Properties method failed: {e2}")
            except Exception as e:
                print(f"DEBUG: 🔴 Step 2a Button access failed: {e}")
        
        # Method 2: If UI extraction failed, try direct wx.Colour access with extreme caution
        if color1_rgb == (240, 240, 240):  # Still using default, try direct access
            print("DEBUG: 🏁 Step 2d: UI method failed, trying direct wx.Colour access")
            if hasattr(graph_canvas, 'checker_color1') and graph_canvas.checker_color1:
                try:
                    # Try .Get() method on the stored color object
                    color1_tuple = graph_canvas.checker_color1.Get()
                    if len(color1_tuple) >= 3:
                        color1_rgb = color1_tuple[:3]
                        print(f"DEBUG: 🏁 Step 2e: Got color1 via stored wx.Colour.Get(): {color1_rgb}")
                except Exception as e:
                    print(f"DEBUG: 🔴 Step 2e Direct wx.Colour access failed: {e}")
                    # Keep the safe default
                    
        print(f"DEBUG: 🎨 Step 3: Final colors chosen: color1={color1_rgb}, color2={color2_rgb}")
        
        print("DEBUG: 🏁 Step 4: Checking zoom level")
        # For max zoom-out: blend background color with first checkboard color only
        # Use the SAME condition as the grid: when spacing < 5, the grid disappears
        if spacing < 5:
            print(f"DEBUG: 🏁 Step 4a: Grid disappears (spacing={spacing} < 5) - blending background with first checkboard color")
            
            # Blend background color (color2) with first checkboard color (color1)
            # This creates a color between the background and the checkboard pattern
            blended_r = int((graph_canvas.background_color[0] + color1_rgb[0]) / 2)
            blended_g = int((graph_canvas.background_color[1] + color1_rgb[1]) / 2) 
            blended_b = int((graph_canvas.background_color[2] + color1_rgb[2]) / 2)
            
            print(f"DEBUG: 🏁 Step 4b: Blending background {graph_canvas.background_color} + checkboard {color1_rgb} = ({blended_r}, {blended_g}, {blended_b})")
            
            print(f"DEBUG: 🏁 Step 4c: Canvas size: {size.width}x{size.height}")
            
            print("DEBUG: 🏁 Step 4e: Creating brush and pen")
            try:
                brush = wx.Brush(wx.Colour(blended_r, blended_g, blended_b))
                pen = wx.Pen(wx.Colour(blended_r, blended_g, blended_b))
                print("DEBUG: 🏁 Step 4f: Created brush and pen successfully")
            except Exception as e:
                print(f"DEBUG: 🔴 Step 4f failed: {e}")
                raise e
            
            print("DEBUG: 🏁 Step 4g: Setting DC brush and pen")
            try:
                dc.SetBrush(brush)
                dc.SetPen(pen)
                print("DEBUG: 🏁 Step 4h: Set DC brush and pen successfully")
            except Exception as e:
                print(f"DEBUG: 🔴 Step 4h failed: {e}")
                raise e
            
            print("DEBUG: 🏁 Step 4i: Drawing blended solid fill")
            try:
                margin = max(size.width, size.height)
                dc.DrawRectangle(-margin, -margin, size.width + 2*margin, size.height + 2*margin)
                print("DEBUG: 🏁 Step 4j: Drew background+checkboard blended color successfully")
                return
            except Exception as e:
                print(f"DEBUG: 🔴 Step 4i failed: {e}")
                raise e
        
        print("DEBUG: 🏁 Step 5: Normal zoom checkboard pattern")
        print(f"DEBUG: 🏁 Step 5a: Canvas size: {size.width}x{size.height}")
        print(f"DEBUG: 🏁 Step 5b: Using spacing: {spacing}")
        
        # Ensure minimum grid size for drawing
        drawing_spacing = max(int(spacing), 10)
        print(f"DEBUG: 🏁 Step 5c: Drawing grid size: {spacing} -> {drawing_spacing}")
        
        if drawing_spacing < 10:  # Too small to draw safely
            print("DEBUG: 🏁 Step 5e: Grid too small, using solid fallback")
            try:
                dc.SetBrush(wx.Brush(wx.Colour(*color2_rgb)))
                dc.SetPen(wx.Pen(wx.Colour(*color2_rgb)))
                dc.DrawRectangle(0, 0, size.width, size.height)
                print("DEBUG: 🏁 Step 5f: Drew solid fallback successfully")
                return
            except Exception as e:
                print(f"DEBUG: 🔴 Step 5f failed: {e}")
                raise e
                
        print("DEBUG: 🏁 Step 6: Drawing checkboard pattern with full coverage and grid alignment")
        
        # Calculate proper bounds for full coverage (same logic as the grid)
        if graph_canvas.world_rotation != 0.0:
            # Calculate the rotated bounding box for full coverage
            angle_rad = math.radians(graph_canvas.world_rotation)
            cos_a = abs(math.cos(angle_rad))
            sin_a = abs(math.sin(angle_rad))
            
            rotated_width = size.width * cos_a + size.height * sin_a
            rotated_height = size.width * sin_a + size.height * cos_a
            
            x_extension = int((rotated_width - size.width) / 2) + drawing_spacing
            y_extension = int((rotated_height - size.height) / 2) + drawing_spacing
            
            left = -x_extension
            right = size.width + x_extension
            top = -y_extension
            bottom = size.height + y_extension
            print(f"DEBUG: 🏁 Step 6a: Extended bounds for rotation: {left} to {right}, {top} to {bottom}")
        else:
            # Normal bounds with margin
            margin = drawing_spacing
            left = -margin
            right = size.width + margin
            top = -margin
            bottom = size.height + margin
            print(f"DEBUG: 🏁 Step 6a: Normal bounds with margin: {left} to {right}, {top} to {bottom}")
        
        # Use proper grid alignment (same as the actual grid)
        offset_x = graph_canvas.pan_x % drawing_spacing
        offset_y = graph_canvas.pan_y % drawing_spacing
        print(f"DEBUG: 🏁 Step 6b: Grid offsets: x={offset_x}, y={offset_y}")
        
        # Start positions (same logic as the grid)
        start_x = offset_x
        while start_x > left - drawing_spacing:
            start_x -= drawing_spacing
        
        start_y = offset_y  
        while start_y > top - drawing_spacing:
            start_y -= drawing_spacing
            
        print(f"DEBUG: 🏁 Step 6c: Start positions: ({start_x}, {start_y})")
        
        # Draw checkboard with full coverage - no artificial square limits
        squares_drawn = 0
        consecutive_failures = 0
        max_failures = 10
        
        # Calculate expected squares for debugging (optional)
        expected_cols = max(int((right - left) // drawing_spacing), 1)
        expected_rows = max(int((bottom - top) // drawing_spacing), 1)
        expected_squares = expected_cols * expected_rows
        print(f"DEBUG: 🏁 Step 7: Expected coverage: ~{expected_cols}x{expected_rows} = {expected_squares} squares")
        
        y = start_y
        row = 0
        rows_drawn = 0
        
        print(f"DEBUG: 🏁 Step 7a: Starting loop from y={y}, will go to y<={bottom + drawing_spacing}")
        
        # Draw all squares needed - only stop on bounds or failures, not square count
        while y <= bottom + drawing_spacing and consecutive_failures < max_failures:
            x = start_x
            col = 0
            squares_in_row = 0
            
            print(f"DEBUG: 🏁 Step 7b: Row {rows_drawn}: y={y}, x range {start_x} to {right + drawing_spacing}")
            
            while x <= right + drawing_spacing and consecutive_failures < max_failures:
                # Draw squares that overlap with visible area
                if x + drawing_spacing >= left - 1 and y + drawing_spacing >= top - 1:
                    try:
                        # Select color based on checkerboard pattern
                        if (row + col) % 2 == 0:
                            brush = wx.Brush(wx.Colour(*color1_rgb))
                            pen = wx.Pen(wx.Colour(*color1_rgb))
                        else:
                            brush = wx.Brush(wx.Colour(*color2_rgb))
                            pen = wx.Pen(wx.Colour(*color2_rgb))
                        
                        dc.SetBrush(brush)
                        dc.SetPen(pen)
                        dc.DrawRectangle(int(x), int(y), drawing_spacing, drawing_spacing)
                        squares_drawn += 1
                        squares_in_row += 1
                        consecutive_failures = 0  # Reset on success
                        
                    except Exception as e:
                        consecutive_failures += 1
                        print(f"DEBUG: 🔴 Square draw failed at ({x},{y}): {e} (failure {consecutive_failures})")
                        if consecutive_failures >= max_failures:
                            print("DEBUG: 🛑 Too many consecutive failures, stopping")
                            raise e
                
                x += drawing_spacing
                col += 1
            
            print(f"DEBUG: 🏁 Step 7c: Row {rows_drawn} complete: drew {squares_in_row} squares at y={y}")
            y += drawing_spacing
            row += 1
            rows_drawn += 1
            
            # Check if we're still within bounds
            if y > bottom + drawing_spacing:
                print(f"DEBUG: 🏁 Step 7d: Reached bottom boundary: y={y} > bottom+grid={bottom + drawing_spacing}")
                break
                
        print(f"DEBUG: 🏁 Step 8: Drew {rows_drawn} rows, {squares_drawn} total squares")
        print(f"DEBUG: 🏁 Step 8a: Final y position: {y}, bottom boundary was: {bottom + drawing_spacing}")
        
        # Double check coverage - make sure we're drawing to the actual screen bottom  
        actual_screen_bottom = size.height
        if y < actual_screen_bottom:
            print(f"DEBUG: ⚠️  WARNING: Checkboard may not reach screen bottom! Final y={y}, screen height={actual_screen_bottom}")
            
            # Add extra rows if needed to ensure full coverage
            print("DEBUG: 🏁 Step 8b: Adding extra rows to ensure full screen coverage")
            extra_rows = 0
            while y <= actual_screen_bottom + drawing_spacing and extra_rows < 20:  # Keep row limit for safety
                x = start_x
                col = 0
                squares_in_row = 0
                
                while x <= right + drawing_spacing:
                    if x + drawing_spacing >= left - 1 and y + drawing_spacing >= top - 1:
                        try:
                            if (row + col) % 2 == 0:
                                brush = wx.Brush(wx.Colour(*color1_rgb))
                                pen = wx.Pen(wx.Colour(*color1_rgb))
                            else:
                                brush = wx.Brush(wx.Colour(*color2_rgb))
                                pen = wx.Pen(wx.Colour(*color2_rgb))
                            
                            dc.SetBrush(brush)
                            dc.SetPen(pen)
                            dc.DrawRectangle(int(x), int(y), drawing_spacing, drawing_spacing)
                            squares_drawn += 1
                            squares_in_row += 1
                        except:
                            break
                    
                    x += drawing_spacing
                    col += 1
                
                print(f"DEBUG: 🏁 Extra row {extra_rows}: y={y}, drew {squares_in_row} squares")
                y += drawing_spacing
                row += 1
                extra_rows += 1
                
            print(f"DEBUG: 🏁 Added {extra_rows} extra rows for full coverage")
            
        print(f"DEBUG: 🏁 Step 8c: Final total: {squares_drawn} checkboard squares covering full view")
        
    except Exception as e:
        print(f"DEBUG: 🔴 Ultra-safe checkboard failed at unknown step: {e}")
        print(f"DEBUG: 🔴 Exception type: {type(e).__name__}")
        print(f"DEBUG: 🔴 Exception details: {str(e)}")
        import traceback
        print(f"DEBUG: 🔴 Full traceback: {traceback.format_exc()}")
        # Complete fallback - solid background
        print("DEBUG: 🏁 Step 9: Attempting solid color fallback")
        try:
            print("DEBUG: 🏁 Step 9a: Getting canvas size for fallback")
            size = graph_canvas.GetSize()
            print(f"DEBUG: 🏁 Step 9b: Size: {size.width}x{size.height}")
            
            print("DEBUG: 🏁 Step 9c: Creating fallback brush and pen")
            brush = wx.Brush(wx.Colour(*color2_rgb))
            pen = wx.Pen(wx.Colour(*color2_rgb))
            
            print("DEBUG: 🏁 Step 9d: Setting fallback brush and pen")
            dc.SetBrush(brush)
            dc.SetPen(pen)
            
            print("DEBUG: 🏁 Step 9e: Drawing fallback rectangle")
            dc.DrawRectangle(0, 0, size.width, size.height)
            print("DEBUG: 🏁 Step 9f: Solid color fallback successful")
        except Exception as e2:
            print(f"DEBUG: 🔴 Step 9 even solid fallback failed: {e2}")
            # Give up completely
            raise e2


def draw_checkboard_aligned_with_grid(graph_canvas: "m_graph_canvas.GraphCanvas", dc):
    """Draw checkboard pattern that aligns perfectly with the grid.
    Returns (squares_drawn, color1_rgb, color2_rgb) where squares_drawn < 0 indicates blended fill path.
    """

    print("DEBUG: 🏁 Drawing checkboard aligned with grid")
    try:
        print("DEBUG: CB STEP 1: fetching size")
        size = graph_canvas.GetSize()
        print(f"DEBUG: CB STEP 2: size=({size.width},{size.height})")
    except Exception as e:
        print(f"DEBUG: CB STEP 1/2 FAILED: {e}")
        raise

    try:
        print("DEBUG: CB STEP 3: computing spacing")
        spacing = graph_canvas.grid_spacing * graph_canvas.zoom
        print(f"DEBUG: CB STEP 4: spacing={spacing}, grid_spacing={graph_canvas.grid_spacing}, zoom={graph_canvas.zoom}")
    except Exception as e:
        print(f"DEBUG: CB STEP 3/4 FAILED: {e}")
        raise
    
    # Use the SAME condition as the grid: when spacing < 2, blend colors instead (draw squares when larger)
    if spacing < 2:
        print(f"DEBUG: 🏁 Grid too small (spacing={spacing} < 5) - using blended color")
        
        # Get colors safely
        color1_rgb = (240, 240, 240)  # Default
        
        # Try to extract user's checkboard color 1
        if hasattr(graph_canvas, 'main_window') and hasattr(graph_canvas.main_window, 'checker_color1_btn'):
            try:
                btn_color = graph_canvas.main_window.checker_color1_btn.GetBackgroundColour()
                if btn_color and btn_color.IsOk():
                    color1_tuple = btn_color.Get()
                    if len(color1_tuple) >= 3:
                        color1_rgb = color1_tuple[:3]
            except:
                pass
        
        # Blend background with checkboard color 1
        blended_r = int((graph_canvas.background_color[0] + color1_rgb[0]) / 2)
        blended_g = int((graph_canvas.background_color[1] + color1_rgb[1]) / 2) 
        blended_b = int((graph_canvas.background_color[2] + color1_rgb[2]) / 2)
        
        print(f"DEBUG: 🏁 Blending background {graph_canvas.background_color} + checkboard {color1_rgb} = ({blended_r}, {blended_g}, {blended_b})")
        
        # Fill entire screen with blended color (same logic as grid)
        margin = max(size.width, size.height)
        dc.SetBrush(wx.Brush(wx.Colour(blended_r, blended_g, blended_b)))
        dc.SetPen(wx.Pen(wx.Colour(blended_r, blended_g, blended_b)))
        dc.DrawRectangle(-margin, -margin, size.width + 2*margin, size.height + 2*margin)
        print("DEBUG: 🏁 Drew blended solid fill")
        return (-1, color1_rgb, color1_rgb)
    
    # Get colors safely - color1 = background, color2 = canvas.checker_color2 (store as tuples to avoid wx lifetime issues)
    try:
        print("DEBUG: CB STEP 5: computing colors")
        color1_rgb = tuple(graph_canvas.background_color) if isinstance(graph_canvas.background_color, (list, tuple)) else (240, 240, 240)
        c2 = getattr(graph_canvas, 'checker_color2', None)
        if isinstance(c2, (list, tuple)):
            color2_rgb = tuple(c2)
            print(f"DEBUG: CB STEP 6: color2 from tuple={color2_rgb}")
        elif isinstance(c2, wx.Colour):
            # Convert to tuple immediately; do not keep wx.Colour references
            color2_rgb = (c2.Red(), c2.Green(), c2.Blue())
            print(f"DEBUG: CB STEP 6: color2 from wx.Colour converted={color2_rgb}")
        else:
            color2_rgb = (180, 180, 180)
            print("DEBUG: CB STEP 6: color2 defaulted")
    except Exception as e:
        print(f"DEBUG: CB STEP 5/6 FAILED: {e}")
        raise

    # If colors are identical (or nearly), auto-derive a contrasting color2 for visibility
    if abs(color1_rgb[0]-color2_rgb[0]) + abs(color1_rgb[1]-color2_rgb[1]) + abs(color1_rgb[2]-color2_rgb[2]) < 10:
        inv = (255 - color1_rgb[0], 255 - color1_rgb[1], 255 - color1_rgb[2])
        color2_rgb = inv
        print(f"DEBUG: 🎨 color1 and color2 too similar, using auto-contrast color2: {color2_rgb}")
    
    print(f"DEBUG: 🎨 Checkboard colors: {color1_rgb} (background/color1), {color2_rgb} (alternating/color2)")
    
    # Calculate world bounds first, then convert to screen for drawing
    # This ensures consistent checkboard pattern regardless of zoom
    
    # Convert screen bounds to world coordinates
    try:
        print("DEBUG: CB STEP 7: computing world bounds from screen")
        world_left = (0 - graph_canvas.pan_x) / graph_canvas.zoom
        world_right = (size.width - graph_canvas.pan_x) / graph_canvas.zoom  
        world_top = (0 - graph_canvas.pan_y) / graph_canvas.zoom
        world_bottom = (size.height - graph_canvas.pan_y) / graph_canvas.zoom
        print(f"DEBUG: CB STEP 8: world bounds initial=({world_left:.1f},{world_top:.1f}) to ({world_right:.1f},{world_bottom:.1f})")
    except Exception as e:
        print(f"DEBUG: CB STEP 7/8 FAILED: {e}")
        raise
    
    # Extend world bounds for rotation if needed
    if graph_canvas.world_rotation != 0.0:
        # Calculate extra margin in world coordinates
        world_width = world_right - world_left
        world_height = world_bottom - world_top
        
        angle_rad = math.radians(graph_canvas.world_rotation)
        cos_a = abs(math.cos(angle_rad))
        sin_a = abs(math.sin(angle_rad))
        
        # Calculate rotated bounding box size
        rotated_world_width = world_width * cos_a + world_height * sin_a
        rotated_world_height = world_width * sin_a + world_height * cos_a
        
        # Use generous extension to ensure full coverage under rotation
        # Base extension from rotation calculation plus substantial safety margin
        base_x_extension = (rotated_world_width - world_width) / 2
        base_y_extension = (rotated_world_height - world_height) / 2
        
        # Add generous safety margin (at least 5 grid sizes or 50% of view diagonal)
        diagonal = math.sqrt(world_width * world_width + world_height * world_height)
        safety_margin = max(5 * graph_canvas.grid_spacing, diagonal * 0.5)
        
        world_x_extension = base_x_extension + safety_margin
        world_y_extension = base_y_extension + safety_margin
        
        world_left -= world_x_extension
        world_right += world_x_extension
        world_top -= world_y_extension
        world_bottom += world_y_extension
        
        print(f"DEBUG: 🏁 Extended world bounds for rotation: ({world_left:.1f}, {world_top:.1f}) to ({world_right:.1f}, {world_bottom:.1f}) with safety margin {safety_margin:.1f}")
    
    print(f"DEBUG: 🏁 World bounds: ({world_left:.1f}, {world_top:.1f}) to ({world_right:.1f}, {world_bottom:.1f})")
    
    # Calculate world grid boundaries that need to be drawn (use canvas grid spacing)
    try:
        print("DEBUG: CB STEP 9: computing world grid indices")
        gs = graph_canvas.grid_spacing
        world_grid_left = int(math.floor(world_left / gs))
        world_grid_right = int(math.ceil(world_right / gs))
        world_grid_top = int(math.floor(world_top / gs))
        world_grid_bottom = int(math.ceil(world_bottom / gs))
        print(f"DEBUG: CB STEP 10: world grid range=({world_grid_left},{world_grid_top}) to ({world_grid_right},{world_grid_bottom})")
    except Exception as e:
        print(f"DEBUG: CB STEP 9/10 FAILED: {e}")
        raise
    
    print(f"DEBUG: 🏁 World grid range: ({world_grid_left}, {world_grid_top}) to ({world_grid_right}, {world_grid_bottom})")
    
    # Prepare safe screen size and precreate pens/brushes (helps avoid excessive allocations)
    try:
        screen_size = int(max(1, gs * graph_canvas.zoom))
        print(f"DEBUG: CB STEP 11: screen_size={screen_size}")
        if screen_size < 1:
            print("DEBUG: CB STEP 11a: screen_size < 1, early return")
            return
    except Exception as e:
        print(f"DEBUG: CB STEP 11 FAILED: {e}")
        raise

    try:
        print("DEBUG: CB STEP 12: creating pens/brushes")
        color1_col = wx.Colour(*color1_rgb)
        color2_col = wx.Colour(*color2_rgb)
        pen1 = wx.Pen(color1_col)
        pen2 = wx.Pen(color2_col)
        brush1 = wx.Brush(color1_col)
        brush2 = wx.Brush(color2_col)
        print("DEBUG: CB STEP 13: pens/brushes ready")
    except Exception as e:
        print(f"DEBUG: CB STEP 12/13 FAILED: {e}")
        raise

    # Draw checkboard squares in world coordinate system
    squares_drawn = 0
    max_squares = 200000  # safety cap
    
    print("DEBUG: CB STEP 14: starting tile loops")
    loop_counter = 0
    for world_grid_y in range(world_grid_top, world_grid_bottom + 1):
        for world_grid_x in range(world_grid_left, world_grid_right + 1):
            try:
                # Calculate world position of this grid square
                world_x = world_grid_x * gs
                world_y = world_grid_y * gs
                if loop_counter < 5:
                    print(f"DEBUG: CB STEP 14a: tile world=({world_x},{world_y}) idx=({world_grid_x},{world_grid_y})")
                # With world transforms already applied to the GC, draw in WORLD coordinates
                
                # Draw all squares within the calculated world bounds (no additional screen filtering)
                # The world bounds already account for rotation, so we don't need extra screen bounds checking
                if True:  # Always draw squares within calculated world bounds
                    
                    # Determine color based on world grid position (always consistent)
                    if (world_grid_x + world_grid_y) % 2 == 0:
                        dc.SetBrush(brush1)
                        dc.SetPen(pen1)
                    else:
                        dc.SetBrush(brush2)
                        dc.SetPen(pen2)
                    
                    # Draw rectangle in world units so GC transforms position/size
                    gc = dc.GetGraphicsContext()
                    if gc:
                        if loop_counter < 5:
                            print("DEBUG: CB STEP 15: creating GC path")
                        path = gc.CreatePath()
                        if loop_counter < 5:
                            print("DEBUG: CB STEP 16: adding rectangle to path")
                        path.AddRectangle(world_x, world_y, gs, gs)
                        if loop_counter < 5:
                            print("DEBUG: CB STEP 17: filling path")
                        gc.FillPath(path)
                    else:
                        if loop_counter < 5:
                            print("DEBUG: CB STEP 15b: GC not available; drawing via DC fallback")
                        # Fallback: draw via DC using precomputed screen size/coords
                        dc.DrawRectangle(int(world_x * graph_canvas.zoom + graph_canvas.pan_x),
                                         int(world_y * graph_canvas.zoom + graph_canvas.pan_y),
                                         screen_size, screen_size)
                    squares_drawn += 1
                    loop_counter += 1
                    if squares_drawn >= max_squares:
                        print(f"DEBUG: 🏁 Reached max checkerboard squares limit: {max_squares}")
                        raise StopIteration
                    
            except Exception as e:
                print(f"DEBUG: 🔴 Square draw failed at world grid ({world_grid_x},{world_grid_y}): {e}")
                # Continue with other squares
        
    print(f"DEBUG: 🏁 Drew {squares_drawn} checkboard squares aligned with grid")
    return (squares_drawn, color1_rgb, color2_rgb)


def draw_pie_chart_node(graph_canvas: "m_graph_canvas.GraphCanvas", dc, node, edges):
    """Draw a node as a pie chart showing hyperedge membership."""

    # Get screen position
    screen_x, screen_y = graph_canvas.world_to_screen(node.x, node.y)
    radius = max(20, int(15 * graph_canvas.zoom))
    
    # Calculate total angle for each edge
    total_edges = len(edges)
    if total_edges == 0:
        return
        
    angle_per_edge = 360.0 / total_edges
    start_angle = 0
    
    # Draw each pie slice
    for edge in edges:
        # Get edge color
        if edge.selected:
            color = wx.Colour(255, 255, 0)  # Yellow for selected
        else:
            color = wx.Colour(*edge.color)
        
        # Create path for pie slice
        gc = dc.GetGraphicsContext()
        path = gc.CreatePath()
        path.MoveToPoint(screen_x, screen_y)
        
        # Calculate end angle
        end_angle = start_angle + angle_per_edge
        
        # Add arc
        # Convert angles to radians and adjust for wxPython's coordinate system
        start_rad = math.radians(-start_angle)  # Negative because wxPython uses clockwise angles
        end_rad = math.radians(-end_angle)
        
        # Create arc using center point, radius, and angles
        path.AddArcToPoint(screen_x, screen_y,  # Center point
                            screen_x + radius * math.cos(start_rad),  # End point x
                            screen_y + radius * math.sin(start_rad),  # End point y
                            radius)  # Radius
        
        # Add line back to center
        path.AddLineToPoint(screen_x, screen_y)
        
        # Fill slice
        alpha = 128 if edge.selected else 64
        fill_color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)
        gc.SetBrush(wx.Brush(fill_color))
        gc.FillPath(path)
        
        # Draw outline
        gc.SetPen(wx.Pen(color, 1))
        gc.StrokePath(path)
        
        start_angle = end_angle
    
    # Draw node text
    if node.text and graph_canvas.show_node_labels:
        dc.SetTextForeground(wx.Colour(*node.text_color))
        dc.SetFont(wx.Font(node.font_size, wx.FONTFAMILY_DEFAULT,
                            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        text_width, text_height = dc.GetTextExtent(node.text)
        dc.DrawText(node.text,
                    screen_x - text_width/2,
                    screen_y - text_height/2)


def draw_node(graph_canvas: "m_graph_canvas.GraphCanvas", dc, node: "m_node.Node"):
    """Draw a node."""
    print(f"DEBUG: Drawing node {node.id} at world coords ({node.x}, {node.y})")

    # Check if we need to draw as pie chart
    if any(edge.is_hyperedge and edge.hyperedge_visualization == "pie_chart" 
            for edge in graph_canvas.graph.get_all_edges() if edge.visible):
        # Collect all hyperedges this node belongs to
        edges = []
        for edge in graph_canvas.graph.get_all_edges():
            if not edge.visible or not edge.is_hyperedge:
                continue
            if (edge.source_id == node.id or 
                edge.target_id == node.id or
                node.id in edge.source_ids or
                node.id in edge.target_ids):
                edges.append(edge)
        
        if edges:
            draw_pie_chart_node(graph_canvas, dc, node, edges)
            return
    if not node.visible:
        return

    # Get graphics context to draw in world coordinates (same as grid)
    gc = dc.GetGraphicsContext() if hasattr(dc, 'GetGraphicsContext') else None
    if not gc:
        print("DEBUG: No graphics context for node, falling back to screen coordinates")
        # Fallback to screen coordinate drawing
        screen_x, screen_y = graph_canvas.world_to_screen(node.x, node.y)
        width = int(node.width * graph_canvas.zoom)
        height = int(node.height * graph_canvas.zoom)
        rect = wx.Rect(screen_x - width // 2, screen_y - height // 2, width, height)
        
        # Set colors and draw
        if node.selected:
            fill_color = wx.Colour(50, 120, 255)
            border_color = wx.Colour(0, 60, 180)
        else:
            fill_color = wx.Colour(*node.color)
            border_color = wx.Colour(*node.border_color)
        
        dc.SetBrush(wx.Brush(fill_color))
        dc.SetPen(wx.Pen(border_color, max(1, int(node.border_width))))
        dc.DrawRoundedRectangle(rect, 5)
        return

    print("DEBUG: Drawing node in world coordinates using graphics context")

    # Set colors
    if node.selected:
        fill_color = wx.Colour(50, 120, 255)  # Bright blue for selected
        border_color = wx.Colour(0, 60, 180)  # Dark blue border
    else:
        fill_color = wx.Colour(*node.color)
        border_color = wx.Colour(*node.border_color)

    # Set up drawing style
    gc.SetBrush(wx.Brush(fill_color))
    gc.SetPen(wx.Pen(border_color, max(1, int(node.border_width))))

    # Compute effective node rotation (individual node rotation; optionally counter-rotate text via auto-readable separately)
    has_individual_rotation = hasattr(node, 'rotation') and node.rotation != 0.0
    effective_rotation = node.rotation if has_individual_rotation else 0.0

    # Apply node rotation around its center in world coordinates
    rotation_applied = False
    if effective_rotation != 0.0:
        gc.PushState()
        gc.Translate(node.x, node.y)
        gc.Rotate(math.radians(effective_rotation))
        gc.Translate(-node.x, -node.y)
        rotation_applied = True

    # Create path for the node shape in world coordinates
    path = gc.CreatePath()
    
    # Calculate node bounds in world coordinates (no zoom scaling needed - handled by transform)
    half_width = node.width / 2
    half_height = node.height / 2
    
    # Draw as rounded rectangle in world space
    radius = 5  # Fixed radius in world coordinates
    path.AddRoundedRectangle(
        node.x - half_width,
        node.y - half_height,
        node.width,
        node.height,
        radius
    )
    
    # Draw node shape
    gc.FillPath(path)
    gc.StrokePath(path)
    print(f"DEBUG: Drew node shape in world coords at ({node.x}, {node.y}) size {node.width}x{node.height}")

    # Draw text (use container label if this is a container)
    if graph_canvas.show_node_labels and graph_canvas.zoom > 0.3:
        # Get appropriate text (container label or regular text)
        display_text = node.get_container_label() if node.is_container else node.text
        
        if display_text:
            # Set text color and font (size in world coordinates)
            font = wx.Font(int(node.font_size), wx.FONTFAMILY_DEFAULT, 
                          wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            gc.SetFont(font, wx.Colour(0, 0, 0))  # Black text
            
            # Get text dimensions and center it in world coordinates
            text_width, text_height = gc.GetTextExtent(display_text)
            text_x = node.x - text_width / 2
            text_y = node.y - text_height / 2
            
            # Draw text (inherits node rotation if applied)
            gc.DrawText(display_text, text_x, text_y)
            print(f"DEBUG: Drew node text '{display_text}' in world coords at ({text_x}, {text_y})")
            
    # Draw container visual indicators
    if node.is_container:
        # Draw a small border indicator for containers
        gc.SetPen(wx.Pen(wx.Colour(0, 100, 200), 2))  # Blue indicator
        gc.SetBrush(wx.Brush(wx.Colour(0, 100, 200, 50)))  # Semi-transparent blue
        indicator_size = 8  # Fixed size in world coordinates
        
        # Draw indicator in world coordinates (inherits node rotation if applied)
        indicator_x = node.x + node.width/2 - indicator_size
        indicator_y = node.y - node.height/2
        
        # Create path for indicator circle
        indicator_path = gc.CreatePath()
        indicator_path.AddCircle(indicator_x, indicator_y, indicator_size/2)
        gc.FillPath(indicator_path)
        gc.StrokePath(indicator_path)
        print(f"DEBUG: Drew container indicator in world coords at ({indicator_x}, {indicator_y})")

    # Restore node rotation transform
    if rotation_applied:
        gc.PopState()

    print(f"DEBUG: Finished drawing node {node.id} in world coordinates")
        
    # Show parent container info if this node is contained
    if node.parent_id and graph_canvas.zoom > 0.5:
        parent_node = graph_canvas.graph.get_node(node.parent_id)
        if parent_node:
            # Draw a small label showing which container this belongs to
            dc.SetTextForeground(wx.Colour(100, 100, 100))  # Gray text
            font = wx.Font(max(8, int(8 * graph_canvas.zoom)),
                            wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_NORMAL)
            dc.SetFont(font)
            
            parent_label = f"∈ {parent_node.text}"
            label_size = dc.GetTextExtent(parent_label)
            label_x = screen_x - label_size.width // 2
            label_y = screen_y + height // 2 + 5
            dc.DrawText(parent_label, label_x, label_y)
    
    # No rotation state to restore for regular DC drawing


def draw_node_anchor_points(graph_canvas: "m_graph_canvas.GraphCanvas", dc, node):
    """Draw pink anchor points on a node to show connection positions."""

    # Get node screen position and size
    screen_pos = graph_canvas.world_to_screen(node.x, node.y)
    width = int(node.width * graph_canvas.zoom) // 2
    height = int(node.height * graph_canvas.zoom) // 2
    
    # Check if we need to apply individual node rotation (same logic as draw_node)
    has_individual_rotation = hasattr(node, 'rotation') and node.rotation != 0.0
    has_auto_readable = graph_canvas.auto_readable_nodes and graph_canvas.world_rotation != 0.0
    
    effective_rotation = 0.0
    if has_individual_rotation:
        effective_rotation += node.rotation
    if has_auto_readable:
        # Counter-rotate to keep text readable when world is rotated
        effective_rotation -= graph_canvas.world_rotation

    # Apply individual node rotation if needed
    rotation_applied = False
    if effective_rotation != 0.0 and hasattr(dc, 'GetGraphicsContext'):
        gc = dc.GetGraphicsContext()
        if gc:
            gc.PushState()
            gc.Translate(screen_pos[0], screen_pos[1])
            gc.Rotate(math.radians(effective_rotation))
            gc.Translate(-screen_pos[0], -screen_pos[1])
            rotation_applied = True
    
    # Calculate anchor point positions (9 total)
    anchor_points = [
        ("center", screen_pos[0], screen_pos[1]),
        ("left_center", screen_pos[0] - width, screen_pos[1]),
        ("right_center", screen_pos[0] + width, screen_pos[1]),
        ("top_center", screen_pos[0], screen_pos[1] - height),
        ("bottom_center", screen_pos[0], screen_pos[1] + height),
        ("top_left", screen_pos[0] - width, screen_pos[1] - height),
        ("top_right", screen_pos[0] + width, screen_pos[1] - height),
        ("bottom_left", screen_pos[0] - width, screen_pos[1] + height),
        ("bottom_right", screen_pos[0] + width, screen_pos[1] + height),
    ]
    
    # Draw small pink circles for each anchor point
    anchor_radius = max(3, int(2 * graph_canvas.zoom))
    dc.SetBrush(wx.Brush(wx.Colour(255, 105, 180)))  # Hot pink
    dc.SetPen(wx.Pen(wx.Colour(255, 20, 147), 1))    # Deep pink border
    
    for name, x, y in anchor_points:
        dc.DrawCircle(int(x), int(y), anchor_radius)
        
    # Restore rotation transformation state if we applied it
    if rotation_applied and hasattr(dc, 'GetGraphicsContext'):
        gc = dc.GetGraphicsContext()
        if gc:
            gc.PopState()


def draw_edge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge: "m_edge.Edge"):
    """Draw an edge."""

    if not edge.visible:
        return
        
    # Check if this edge is redirected due to container collapse
    is_redirected = graph_canvas.is_edge_redirected(edge)
    if not graph_canvas.show_nested_edges and is_redirected:
        return

    # For hyperedges, draw according to selected visualization, influenced by selected graph type
    if edge.is_hyperedge:
        # Handle non-line visualizations first
        hv = getattr(edge, 'hyperedge_visualization', 'lines') or 'lines'
        # Drive hv by current graph type: Ubergraph -> prefer ubergraph; Hypergraph -> prefer lines
        try:
            graph_type = getattr(graph_canvas, 'selected_graph_type', 3)
            # Assume 6/7 are Ubergraph variants per existing UI
            if graph_type in (6, 7):
                hv = 'ubergraph'
            # Optionally normalize back to lines for classic hypergraph
            elif graph_type == 4 and hv == 'ubergraph':
                hv = 'lines'
        except Exception:
            pass
        sel = edge.selected
        base = edge.color if hasattr(edge, 'color') else (40, 40, 40)
        color = wx.Colour(*(base if not sel else (min(base[0]+50,255), min(base[1]+50,255), min(base[2]+50,255))))

        if hv == 'ubergraph':
            # Draw uberedge as a node or edge-to-edge/node graph depending on view
            view = getattr(edge, 'hyperedge_view', 'standard') or 'standard'
            # If graph is in Ubergraph mode and view not explicitly set, prefer line_graph
            try:
                if getattr(graph_canvas, 'selected_graph_type', 3) in (6, 7) and view == 'standard':
                    view = 'line_graph'
            except Exception:
                pass
            if view == 'line_graph':
                draw_line_graph_hyperedge(graph_canvas, dc, edge, color)
                return
            elif view == 'derivative_graph':
                draw_derivative_graph_hyperedge(graph_canvas, dc, edge, color)
                return
            else:
                draw_ubergraph_hyperedge(graph_canvas, dc, edge, color)
                return
        elif hv == 'curved_surface':
            # For curved surface we need connection endpoints; approximate with source/target centers
            source_node = graph_canvas.graph.get_node(edge.source_id)
            target_node = graph_canvas.graph.get_node(edge.target_id)
            if source_node and target_node:
                sp = graph_canvas.world_to_screen(source_node.x, source_node.y)
                tp = graph_canvas.world_to_screen(target_node.x, target_node.y)
                draw_curved_surface(graph_canvas, dc, sp, tp, edge, color)
            return
        elif hv == 'blob_boundary':
            draw_blob_boundary(graph_canvas, dc, edge, color)
            return
        elif hv == 'polygon':
            draw_polygon_hyperedge(graph_canvas, dc, edge, color)
            return
        elif hv == 'zykov':
            draw_zykov_hyperedge(graph_canvas, dc, edge, color)
            return
        elif hv == 'radial':
            draw_radial_hyperedge(graph_canvas, dc, edge, color)
            return
        # else: default to line-based visualization below
        # Resolve nodes
        source_nodes = [graph_canvas.graph.get_node(node_id) for node_id in edge.source_ids if graph_canvas.graph.get_node(node_id)]
        target_nodes = [graph_canvas.graph.get_node(node_id) for node_id in edge.target_ids if graph_canvas.graph.get_node(node_id)]
        if not source_nodes or not target_nodes:
            return
        source_node = source_nodes[0]
        target_node = target_nodes[0]
        
        # Compute anchor endpoints in WORLD coordinates (blue dots for main edge)
        if hasattr(graph_canvas, 'get_edge_anchor_endpoints_world'):
            (sxw, syw), (txw, tyw) = graph_canvas.get_edge_anchor_endpoints_world(edge, source_node, target_node)
        else:
            sxw, syw = source_node.x, source_node.y
            txw, tyw = target_node.x, target_node.y

        # Connection points in WORLD coords
        dxw = txw - sxw
        dyw = tyw - syw
        from_w = (sxw + dxw * edge.from_connection_point, syw + dyw * edge.from_connection_point)
        to_w = (sxw + dxw * edge.to_connection_point,   syw + dyw * edge.to_connection_point)

        gc = dc.GetGraphicsContext()
        if gc:
            # Pen
            gc.SetPen(wx.Pen(color, max(1, int(edge.width))))

            # Helper to anchor from node boundary toward a target world point (rectangle math)
            def anchor_from_node(node_obj, target_pt_w):
                nx, ny = float(node_obj.x), float(node_obj.y)
                tx, ty = float(target_pt_w[0]), float(target_pt_w[1])
                dx = tx - nx
                dy = ty - ny
                length = math.sqrt(dx*dx + dy*dy)
                if length == 0:
                    return (nx, ny)
                dx /= length
                dy /= length
                node_w = float(getattr(node_obj, 'width', 0))
                node_h = float(getattr(node_obj, 'height', 0))
                dist_v = (node_w / 2.0) / abs(dx) if abs(dx) > 1e-6 else float('inf')
                dist_h = (node_h / 2.0) / abs(dy) if abs(dy) > 1e-6 else float('inf')
                edge_dist = min(dist_v, dist_h)
                return (nx + dx * edge_dist, ny + dy * edge_dist)

            # Source branches: primary starts at (sxw, syw), others from their anchored perimeter
            for node in source_nodes:
                start_w = (sxw, syw) if node.id == getattr(edge, 'source_id', None) else anchor_from_node(node, from_w)
                path = gc.CreatePath()
                path.MoveToPoint(start_w[0], start_w[1])
                path.AddLineToPoint(from_w[0], from_w[1])
                gc.StrokePath(path)

            # Target branches
            for node in target_nodes:
                start_w = (txw, tyw) if node.id == getattr(edge, 'target_id', None) else anchor_from_node(node, to_w)
                path = gc.CreatePath()
                path.MoveToPoint(start_w[0], start_w[1])
                path.AddLineToPoint(to_w[0], to_w[1])
                gc.StrokePath(path)

            # Main segment
            path = gc.CreatePath()
            path.MoveToPoint(from_w[0], from_w[1])
            path.AddLineToPoint(to_w[0], to_w[1])
            gc.StrokePath(path)

            # Label at midpoint (world coords)
            if edge.text and getattr(graph_canvas, 'show_edge_labels', True):
                mxw = (from_w[0] + to_w[0]) / 2.0
                myw = (from_w[1] + to_w[1]) / 2.0
                gc.SetFont(wx.Font(max(8, int(edge.font_size)), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD), wx.Colour(*edge.text_color))
                gc.DrawText(edge.text, mxw, myw)

            return
        if not gc:
            # Fallback: use screen-space anchors derived from world anchors
            source_screen = graph_canvas.world_to_screen(source_node.x, source_node.y)
            target_screen = graph_canvas.world_to_screen(target_node.x, target_node.y)
            source_adjusted = graph_canvas.calculate_line_endpoint(source_node, target_node, source_screen, target_screen, True, edge)
            target_adjusted = graph_canvas.calculate_line_endpoint(target_node, source_node, target_screen, source_screen, False, edge)
            dx = target_adjusted[0] - source_adjusted[0]
            dy = target_adjusted[1] - source_adjusted[1]
            from_point = (source_adjusted[0] + dx * edge.from_connection_point, source_adjusted[1] + dy * edge.from_connection_point)
            to_point = (source_adjusted[0] + dx * edge.to_connection_point,   source_adjusted[1] + dy * edge.to_connection_point)
            for node in source_nodes:
                node_screen = graph_canvas.world_to_screen(node.x, node.y)
                node_adjusted = graph_canvas.calculate_line_endpoint(node, source_node, node_screen, source_screen, True, edge)
            draw_edge_segment(graph_canvas, dc, node_adjusted, from_point, edge)
            for node in target_nodes:
                node_screen = graph_canvas.world_to_screen(node.x, node.y)
                node_adjusted = graph_canvas.calculate_line_endpoint(node, target_node, node_screen, target_screen, True, edge)
                draw_edge_segment(graph_canvas, dc, node_adjusted, to_point, edge)
            draw_edge_segment(graph_canvas, dc, from_point, to_point, edge)
            return
        
        # Draw arrows for hyperedges
        if edge.directed:
            if edge.split_arrows and edge.arrow_position < edge.from_connection_point:
                # Draw arrows on source branches
                for node in source_nodes:
                    node_screen = graph_canvas.world_to_screen(node.x, node.y)
                    node_adjusted = graph_canvas.calculate_line_endpoint(node, source_node,
                                                                node_screen, source_screen, True, edge)
                    # Draw arrow on source branch with normalized position
                    normalized_pos = edge.arrow_position / edge.from_connection_point
                    draw_arrow(graph_canvas,dc, node_adjusted, from_point, edge, node, source_node,
                                normalized_pos, 0.0, edge.from_connection_point)
            elif edge.split_arrows and edge.arrow_position > edge.to_connection_point:
                # Draw arrows on target branches
                for node in target_nodes:
                    node_screen = graph_canvas.world_to_screen(node.x, node.y)
                    node_adjusted = graph_canvas.calculate_line_endpoint(node, target_node,
                                                                node_screen, target_screen, True, edge)
                    # Draw arrow on target branch with normalized position
                    normalized_pos = (edge.arrow_position - edge.to_connection_point) / (1.0 - edge.to_connection_point)
                    draw_arrow(graph_canvas, dc, to_point, node_adjusted, edge, target_node, node,
                                normalized_pos, edge.to_connection_point, 1.0)
            else:
                # Draw arrow on main segment with normalized position
                normalized_pos = (edge.arrow_position - edge.from_connection_point) / (edge.to_connection_point - edge.from_connection_point)
                draw_arrow(graph_canvas, dc, from_point, to_point, edge, source_node, target_node,
                            normalized_pos, edge.from_connection_point, edge.to_connection_point)
        
        # Draw text at midpoint of main segment
        if edge.text:
            text_x = (from_point[0] + to_point[0]) / 2
            text_y = (from_point[1] + to_point[1]) / 2
            dc.SetTextForeground(wx.Colour(*edge.text_color))
            dc.SetFont(wx.Font(edge.font_size, wx.FONTFAMILY_DEFAULT,
                            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            dc.DrawText(edge.text, text_x, text_y)
        
        return
        
    # Regular edge drawing
    source_node = graph_canvas.graph.get_node(edge.source_id)
    target_node = graph_canvas.graph.get_node(edge.target_id)

    if not source_node or not target_node:
        return

    gc = dc.GetGraphicsContext() if hasattr(dc, 'GetGraphicsContext') else None
    # Prefer world-coordinate straight-line drawing via GC only for straight edges;
    # for curves (bspline, bezier, curved, etc.) fall back to screen-space renderer below
    use_gc_straight = False
    if gc:
        try:
            rendering_type = edge.rendering_type if edge.rendering_type else graph_canvas.edge_rendering_type
            if rendering_type in (None, "straight") and not getattr(edge, 'is_composite', False) and (not getattr(edge, 'control_points', None)):
                use_gc_straight = True
        except Exception:
            use_gc_straight = True

    if gc and use_gc_straight:
        try:
            # Compute anchor endpoints in world space if helper available; else use node centers
            if hasattr(graph_canvas, 'get_edge_anchor_endpoints_world'):
                source_anchor_world, target_anchor_world = graph_canvas.get_edge_anchor_endpoints_world(edge, source_node, target_node)
                sxw, syw = source_anchor_world
                txw, tyw = target_anchor_world
            else:
                sxw, syw = source_node.x, source_node.y
                txw, tyw = target_node.x, target_node.y

            # Set pen using world units (transform handles zoom)
            if edge.selected:
                color = wx.Colour(255, 50, 50)
            else:
                color = wx.Colour(*edge.color)
            gc.SetPen(wx.Pen(color, max(1, int(edge.width))))

            # Draw straight path for now (respects rotation/pan/zoom under world_transform)
            path = gc.CreatePath()
            path.MoveToPoint(sxw, syw)
            path.AddLineToPoint(txw, tyw)
            gc.StrokePath(path)

            # Draw arrowhead in world coordinates if directed
            if getattr(edge, 'directed', True):
                dx = (txw - sxw)
                dy = (tyw - syw)
                seg_len = math.hypot(dx, dy)
                if seg_len > 1e-6:
                    ux = dx / seg_len
                    uy = dy / seg_len
                    # Arrow position normalized (clamped to avoid clipping at ends)
                    arrow_pos = getattr(edge, 'arrow_position', 0.5)
                    arrow_pos = max(0.1, min(0.9, arrow_pos))
                    ax = sxw + ux * seg_len * arrow_pos
                    ay = syw + uy * seg_len * arrow_pos

                    # Arrow size in world units; scale with edge width
                    arrow_size = max(8.0, float(edge.width) * 3.0) / max(1.0, 1.0)  # world units; transform scales visually
                    arrow_width = arrow_size * 0.5

                    # Perpendicular
                    px = -uy
                    py = ux

                    # Build arrow polygon path (tip, back-left, mid, back-right)
                    apath = gc.CreatePath()
                    tip_x = ax
                    tip_y = ay
                    bl_x = ax - arrow_size * ux + arrow_width * px
                    bl_y = ay - arrow_size * uy + arrow_width * py
                    mid_x = ax - (arrow_size * 0.5) * ux
                    mid_y = ay - (arrow_size * 0.5) * uy
                    br_x = ax - arrow_size * ux - arrow_width * px
                    br_y = ay - arrow_size * uy - arrow_width * py
                    apath.MoveToPoint(tip_x, tip_y)
                    apath.AddLineToPoint(bl_x, bl_y)
                    apath.AddLineToPoint(mid_x, mid_y)
                    apath.AddLineToPoint(br_x, br_y)
                    apath.CloseSubpath()

                    gc.SetBrush(wx.Brush(color))
                    gc.SetPen(wx.Pen(color, 1))
                    gc.FillPath(apath)
                    gc.StrokePath(apath)

                    # Draw draggable yellow control dot at arrow center
                    ctrl_r = max(3.0, min(8.0, float(edge.width) * 1.5))
                    gc.SetBrush(wx.Brush(wx.Colour(255, 255, 0)))
                    gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
                    gc.DrawEllipse(ax - ctrl_r, ay - ctrl_r, ctrl_r * 2.0, ctrl_r * 2.0)

            # Draw label at midpoint in world coords
            if graph_canvas.show_edge_labels and edge.text and graph_canvas.zoom > 0.5:
                mxw = (sxw + txw) / 2.0
                myw = (syw + tyw) / 2.0
                gc.SetFont(wx.Font(max(8, int(edge.font_size)), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD), wx.Colour(0, 0, 0))
                gc.DrawText(edge.text, mxw, myw)

            return
        except Exception as _e:
            # Fallback to screen-space method below
            pass

    # World-coordinate curved rendering is disabled; curves are drawn in screen space using
    # adjusted endpoints to ensure they connect at node connection points.

    # Set colors
    if edge.selected:
        color = wx.Colour(255, 50, 50)  # Bright red for selected
    else:
        color = wx.Colour(*edge.color)

    # Fallback path: screen-space drawing (neutralize GC world transform while drawing)
    source_screen = graph_canvas.world_to_screen(source_node.x, source_node.y)
    target_screen = graph_canvas.world_to_screen(target_node.x, target_node.y)
    source_adjusted = graph_canvas.calculate_line_endpoint(source_node, target_node, source_screen, target_screen, True, edge)
    target_adjusted = graph_canvas.calculate_line_endpoint(target_node, source_node, target_screen, source_screen, False, edge)

    # If we're using a GCDC (GC-backed DC) and a world transform is active, temporarily pop it
    popped = False
    gc_local = dc.GetGraphicsContext() if hasattr(dc, 'GetGraphicsContext') else None
    if gc_local:
        try:
            gc_local.PopState()  # exit world transform to draw in pure screen space
            popped = True
        except Exception:
            popped = False

    # Draw edge based on rendering type (functions expect screen-space endpoints)
    draw_edge_by_type(graph_canvas, dc, source_adjusted, target_adjusted, edge)

    # Draw arrow for directed edges only; project along curve for curved types
    if edge.directed:
        rendering_type = edge.rendering_type if edge.rendering_type else graph_canvas.edge_rendering_type
        control_points = getattr(edge, 'control_points', None)
        has_control_points = bool(control_points) and len(control_points) > 0
        # If no control points, treat as straight between adjusted endpoints so arrow aligns
        if rendering_type in ("straight", None) or not has_control_points:
            draw_arrow(graph_canvas, dc, source_adjusted, target_adjusted, edge, source_node, target_node)
        else:
            # Sample curve near arrow position to get local segment tangent
            try:
                t = float(getattr(edge, 'arrow_position', 0.5))
            except Exception:
                t = 0.5
            t = max(0.01, min(0.99, t))
            p_world = graph_canvas.calculate_position_on_curve(edge, source_node, target_node, t)
            p2_world = graph_canvas.calculate_position_on_curve(edge, source_node, target_node, min(0.999, t + 0.01))
            if p_world and p2_world:
                p_screen = graph_canvas.world_to_screen(p_world[0], p_world[1])
                p2_screen = graph_canvas.world_to_screen(p2_world[0], p2_world[1])
                # Pass normalized_pos=0.0 so arrow tip/yellow dot sit at p_screen and follow tangent to p2_screen
                draw_arrow(graph_canvas, dc, p_screen, p2_screen, edge, source_node, target_node, normalized_pos=0.0)
    # else: edge is undirected, no arrow needed

    # Re-enter the world transform after screen-space drawing if we popped it
    if popped and gc_local:
        try:
            size = graph_canvas.GetSize()
            center_x = size.width / 2.0
            center_y = size.height / 2.0
            gc_local.PushState()
            # Translate(center + pan) -> Rotate -> Scale (same as world_transform)
            gc_local.Translate(center_x + graph_canvas.pan_x, center_y + graph_canvas.pan_y)
            if getattr(graph_canvas, 'world_rotation', 0.0) != 0.0:
                gc_local.Rotate(math.radians(graph_canvas.world_rotation))
            gc_local.Scale(graph_canvas.zoom, graph_canvas.zoom)
        except Exception:
            pass

    # Draw text
    if graph_canvas.show_edge_labels and edge.text and graph_canvas.zoom > 0.5:
        dc.SetTextForeground(wx.Colour(0, 0, 0))  # Black text
        font = wx.Font(max(8, int(edge.font_size * graph_canvas.zoom)),
                        wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_BOLD)  # Bold text for better contrast
        dc.SetFont(font)

        # Calculate text position using adjusted line endpoints
        text_pos = edge.get_text_position(source_node.get_2d_position(),
                                            target_node.get_2d_position())
        text_screen = graph_canvas.world_to_screen(text_pos[0], text_pos[1])

        text_size = dc.GetTextExtent(edge.text)
        text_x = text_screen[0] - text_size.width // 2
        text_y = text_screen[1] - text_size.height // 2
        dc.DrawText(edge.text, text_x, text_y)
        
    # Endpoint dots are now drawn after anchor points in the main draw() method for proper z-order
        
    # Draw special indicators for nested/redirected edges
    if is_redirected and graph_canvas.show_nested_edge_indicators:
        graph_canvas.draw_nested_edge_indicator(dc, source_adjusted, target_adjusted, edge)
        
    # Control points are now drawn after nodes in the main draw() method for proper z-order


def draw_edge_endpoint_dots(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge=None):
    """Draw draggable dots at edge endpoints for selected edges."""

    dot_radius = max(6, int(4 * graph_canvas.zoom))  # Scale with zoom
    
    # Set up blue dot style
    dc.SetBrush(wx.Brush(wx.Colour(50, 50, 200)))  # Blue for endpoints
    dc.SetPen(wx.Pen(wx.Colour(0, 0, 150), 2))     # Dark blue border
    
    if edge and edge.is_hyperedge:
        # For ubergraph, draw blue anchor dots for segment endpoints based on anchor math
        if getattr(edge, 'hyperedge_visualization', '') == 'ubergraph' and edge.selected:
            try:
                # Compute anchor endpoints for the main edge in screen space
                source_node = graph_canvas.graph.get_node(edge.source_id) if edge.source_id else None
                target_node = graph_canvas.graph.get_node(edge.target_id) if edge.target_id else None
                if source_node and target_node:
                    ss = graph_canvas.world_to_screen(source_node.x, source_node.y)
                    ts = graph_canvas.world_to_screen(target_node.x, target_node.y)
                    sa = graph_canvas.calculate_line_endpoint(source_node, target_node, ss, ts, True, edge)
                    ta = graph_canvas.calculate_line_endpoint(target_node, source_node, ts, ss, False, edge)
                else:
                    sa = source_pos
                    ta = target_pos

                # Uberedge box-side anchor based on anchor mode: project center toward each attached node
                def box_anchor_screen(toward_world):
                    cx, cy = float(edge.uber_x), float(edge.uber_y)
                    w2 = float(getattr(edge, 'uber_width', 60.0)) / 2.0
                    h2 = float(getattr(edge, 'uber_height', 40.0)) / 2.0
                    vx = float(toward_world[0]) - cx
                    vy = float(toward_world[1]) - cy
                    if abs(vx) < 1e-9 and abs(vy) < 1e-9:
                        return graph_canvas.world_to_screen(cx, cy)
                    if getattr(edge, 'uber_shape', 'rectangle') == 'ellipse':
                        rx, ry = w2, h2
                        t = 1.0 / math.sqrt((vx*vx)/(rx*rx) + (vy*vy)/(ry*ry))
                        return graph_canvas.world_to_screen(cx + vx * t, cy + vy * t)
                    # rectangle intersection
                    dx = vx; dy = vy
                    t_vals = []
                    if abs(dx) > 1e-9:
                        t_vals.append(( w2 - 0.0) / dx)
                        t_vals.append((-w2 - 0.0) / dx)
                    if abs(dy) > 1e-9:
                        t_vals.append(( h2 - 0.0) / dy)
                        t_vals.append((-h2 - 0.0) / dy)
                    candidates = []
                    for t in t_vals:
                        if t <= 0: continue
                        px = cx + dx * t; py = cy + dy * t
                        if abs(px - cx) <= w2 + 1e-6 and abs(py - cy) <= h2 + 1e-6:
                            candidates.append((px, py, t))
                    if not candidates:
                        return graph_canvas.world_to_screen(cx, cy)
                    candidates.sort(key=lambda p: p[2])
                    return graph_canvas.world_to_screen(candidates[0][0], candidates[0][1])

                # For primary source/target
                ex1 = box_anchor_screen((source_node.x, source_node.y)) if source_node else None
                ex2 = box_anchor_screen((target_node.x, target_node.y)) if target_node else None

                # Draw anchors for node↔uberedge segments: blue at node anchor and blue at uberedge box anchor(s)
                dc.DrawCircle(int(sa[0]), int(sa[1]), dot_radius)
                dc.DrawCircle(int(ta[0]), int(ta[1]), dot_radius)
                if ex1:
                    dc.DrawCircle(int(ex1[0]), int(ex1[1]), dot_radius)
                if ex2:
                    dc.DrawCircle(int(ex2[0]), int(ex2[1]), dot_radius)
            except Exception:
                pass
            return
        # Draw dots for all source node connections
        source_node = graph_canvas.graph.get_node(edge.source_id)
        target_node = graph_canvas.graph.get_node(edge.target_id)
        if source_node and target_node:
            source_screen = graph_canvas.world_to_screen(source_node.x, source_node.y)
            target_screen = graph_canvas.world_to_screen(target_node.x, target_node.y)
            
            # Calculate connection points
            dx = target_pos[0] - source_pos[0]
            dy = target_pos[1] - source_pos[1]
            from_point = (source_pos[0] + dx * edge.from_connection_point,
                        source_pos[1] + dy * edge.from_connection_point)
            to_point = (source_pos[0] + dx * edge.to_connection_point,
                        source_pos[1] + dy * edge.to_connection_point)
            
            # Draw dots for source nodes
            for node in [source_node] + [graph_canvas.graph.get_node(nid) for nid in edge.source_ids]:
                if not node:
                    continue
                node_screen = graph_canvas.world_to_screen(node.x, node.y)
                node_adjusted = graph_canvas.calculate_line_endpoint(node, source_node,
                                                            node_screen, source_screen, True, edge)
                dc.DrawCircle(node_adjusted[0], node_adjusted[1], dot_radius)
            
            # Draw dots for target nodes
            for node in [target_node] + [graph_canvas.graph.get_node(nid) for nid in edge.target_ids]:
                if not node:
                    continue
                node_screen = graph_canvas.world_to_screen(node.x, node.y)
                node_adjusted = graph_canvas.calculate_line_endpoint(node, target_node,
                                                            node_screen, target_screen, True, edge)
                dc.DrawCircle(node_adjusted[0], node_adjusted[1], dot_radius)
    else:
        # Regular edge - draw source and target dots
        dc.DrawCircle(source_pos[0], source_pos[1], dot_radius)
    dc.DrawCircle(target_pos[0], target_pos[1], dot_radius)
    
    # Draw hyperedge connection points if edge is provided
    if edge:
        # Calculate positions along the straight connection (screen space)
        dx = target_pos[0] - source_pos[0]
        dy = target_pos[1] - source_pos[1]
        
        # Draw cyan (from) connection point
        from_x = source_pos[0] + dx * edge.from_connection_point
        from_y = source_pos[1] + dy * edge.from_connection_point
        dc.SetBrush(wx.Brush(wx.Colour(0, 255, 255)))  # Cyan
        dc.SetPen(wx.Pen(wx.Colour(0, 200, 200), 2))   # Darker cyan border
        dc.DrawCircle(from_x, from_y, dot_radius)
        
        # Draw purple (to) connection point
        to_x = source_pos[0] + dx * edge.to_connection_point
        to_y = source_pos[1] + dy * edge.to_connection_point
        dc.SetBrush(wx.Brush(wx.Colour(255, 0, 255)))  # Purple
        dc.SetPen(wx.Pen(wx.Colour(200, 0, 200), 2))   # Darker purple border
        dc.DrawCircle(to_x, to_y, dot_radius)

        # Draw yellow dot at arrow position between nodes (straight segment), for intuitive click target
        try:
            arrow_pos = float(getattr(edge, 'arrow_position', 0.5))
        except Exception:
            arrow_pos = 0.5
        arrow_pos = max(0.0, min(1.0, arrow_pos))
        arrow_x = source_pos[0] + dx * arrow_pos
        arrow_y = source_pos[1] + dy * arrow_pos
        dc.SetBrush(wx.Brush(wx.Colour(255, 255, 0)))  # Yellow
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))       # Black border
        dc.DrawCircle(arrow_x, arrow_y, dot_radius)


def draw_nested_edge_indicator(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge):
    """Draw special indicators for nested/redirected edges."""

    # Calculate midpoint of the edge
    mid_x = (source_pos[0] + target_pos[0]) / 2
    mid_y = (source_pos[1] + target_pos[1]) / 2
    
    # Draw dashed line overlay to indicate it's redirected
    dash_pen = wx.Pen(wx.Colour(255, 165, 0), max(2, int(2 * graph_canvas.zoom)), wx.PENSTYLE_SHORT_DASH)  # Orange dashed
    dc.SetPen(dash_pen)
    dc.DrawLine(source_pos[0], source_pos[1], target_pos[0], target_pos[1])
    
    # Draw small diamond indicator at midpoint
    indicator_size = max(6, int(4 * graph_canvas.zoom))
    dc.SetBrush(wx.Brush(wx.Colour(255, 165, 0)))  # Orange fill
    dc.SetPen(wx.Pen(wx.Colour(200, 100, 0), 2))   # Darker orange border
    
    # Create diamond shape
    diamond_points = [
        wx.Point(int(mid_x), int(mid_y - indicator_size)),  # Top
        wx.Point(int(mid_x + indicator_size), int(mid_y)),  # Right
        wx.Point(int(mid_x), int(mid_y + indicator_size)),  # Bottom  
        wx.Point(int(mid_x - indicator_size), int(mid_y))   # Left
    ]
    dc.DrawPolygon(diamond_points)

   
def draw_line_graph_hyperedge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge, color):
    """Draw a line graph representation of the hyperedge (edges connected if they share nodes).
    Adds support for parallel uberedges (offsets) and self-loops (ellipse).
    """

    # Build connections ONLY from explicit metadata; do not auto-link by shared nodes
    connected_edges = []
    explicit_list = []
    if hasattr(edge, 'metadata') and edge.metadata:
        try:
            explicit_list = list(edge.metadata.get('connected_uberedges', []))
        except Exception:
            explicit_list = []
    # Map target IDs to edge objects (preserve duplicates for parallel links)
    for target_id in explicit_list:
        oe = None
        for cand in graph_canvas.graph.get_all_edges():
            if cand.id == target_id and cand.is_hyperedge:
                oe = cand
                break
        if oe is not None:
            connected_edges.append(oe)

    gc = dc.GetGraphicsContext()
    if gc:
        def _draw_world_arrow(x1, y1, x2, y2, pen_color, width):
            dx = float(x2) - float(x1)
            dy = float(y2) - float(y1)
            seg_len = math.hypot(dx, dy)
            if seg_len <= 1e-6:
                return
            ux = dx / seg_len
            uy = dy / seg_len
            px = -uy
            py = ux
            arrow_size = max(8.0, float(width) * 3.0)
            arrow_width = arrow_size * 0.5
            tip_x = float(x2)
            tip_y = float(y2)
            bl_x = tip_x - arrow_size * ux + arrow_width * px
            bl_y = tip_y - arrow_size * uy + arrow_width * py
            br_x = tip_x - arrow_size * ux - arrow_width * px
            br_y = tip_y - arrow_size * uy - arrow_width * py
            ap = gc.CreatePath()
            ap.MoveToPoint(tip_x, tip_y)
            ap.AddLineToPoint(bl_x, bl_y)
            ap.AddLineToPoint(br_x, br_y)
            ap.CloseSubpath()
            gc.SetBrush(wx.Brush(pen_color))
            gc.SetPen(wx.Pen(pen_color, 1))
            gc.FillPath(ap)
            gc.StrokePath(ap)

        # Track counts to offset parallel links consistently
        pair_total = {}
        for oe in connected_edges:
            pair = tuple(sorted([edge.id, oe.id]))
            pair_total[pair] = pair_total.get(pair, 0) + 1

        def _box_anchor_world(ebox, toward_x, toward_y):
            cx, cy = float(ebox.uber_x), float(ebox.uber_y)
            w2 = float(getattr(ebox, 'uber_width', 60.0)) / 2.0
            h2 = float(getattr(ebox, 'uber_height', 40.0)) / 2.0
            vx = float(toward_x) - cx
            vy = float(toward_y) - cy
            if abs(vx) < 1e-9 and abs(vy) < 1e-9:
                return cx, cy
            if getattr(ebox, 'uber_shape', 'rectangle') == 'ellipse':
                # Ellipse boundary intersection
                rx, ry = w2, h2
                t = 1.0 / math.sqrt((vx*vx)/(rx*rx) + (vy*vy)/(ry*ry))
                return cx + vx * t, cy + vy * t
            # Rectangle intersection
            dx = vx; dy = vy
            t_vals = []
            if abs(dx) > 1e-9:
                t_vals.append(( w2 - 0.0) / dx)
                t_vals.append((-w2 - 0.0) / dx)
            if abs(dy) > 1e-9:
                t_vals.append(( h2 - 0.0) / dy)
                t_vals.append((-h2 - 0.0) / dy)
            candidates = []
            for t in t_vals:
                if t <= 0:
                    continue
                px = cx + dx * t
                py = cy + dy * t
                if abs(px - cx) <= w2 + 1e-6 and abs(py - cy) <= h2 + 1e-6:
                    candidates.append((px, py, t))
            if not candidates:
                return cx, cy
            candidates.sort(key=lambda p: p[2])
            return candidates[0][0], candidates[0][1]

        pair_seen = {}
    for other_edge in connected_edges:
        # Self-loop: draw ellipse around this uberedge center
        if other_edge.id == edge.id:
            continue

        pair = tuple(sorted([edge.id, other_edge.id]))
        seen = pair_seen.get(pair, 0)
        total = pair_total.get(pair, 1)
        pair_seen[pair] = seen + 1

        # Pen color blending
        blend_color = wx.Colour((color.Red() + other_edge.color[0]) // 2, (color.Green() + other_edge.color[1]) // 2, (color.Blue() + other_edge.color[2]) // 2)
        gc.SetPen(wx.Pen(blend_color, max(1, int(edge.width * graph_canvas.zoom))))

        # Self-loop case (explicit connection to self recorded separately, handled below)
        if other_edge.id == edge.id:
            continue

        # Compute offset for parallel edges
        dx = float(other_edge.uber_x) - float(edge.uber_x)
        dy = float(other_edge.uber_y) - float(edge.uber_y)
        length = math.hypot(dx, dy)
        nx, ny = (0.0, 1.0)
        if length > 1e-6:
            ux, uy = dx / length, dy / length
            nx, ny = -uy, ux
        offset_step = max(6.0, float(edge.width))
        # Center offsets around zero for multiple parallels
        offset_index = seen - (total - 1) / 2.0
        ox = nx * offset_step * offset_index
        oy = ny * offset_step * offset_index

        # Compute anchors on each uberedge box toward the other
        ax1, ay1 = _box_anchor_world(edge, float(other_edge.uber_x) + ox, float(other_edge.uber_y) + oy)
        ax2, ay2 = _box_anchor_world(other_edge, float(edge.uber_x) + ox, float(edge.uber_y) + oy)
        # Draw segment honoring rendering type (screen space); use per-link control points if present
        s1 = graph_canvas.world_to_screen(ax1, ay1)
        s2 = graph_canvas.world_to_screen(ax2, ay2)
        # Temporarily pop world transform for screen-space helpers
        popped = False
        try:
            gc.PopState()
            popped = True
        except Exception:
            popped = False
        try:
            seg_cp = []
            try:
                if hasattr(edge, 'metadata') and isinstance(edge.metadata, dict):
                    cp_map = edge.metadata.get('segment_cp_edges', {}) or {}
                    seg_cp = cp_map.get(str(other_edge.id), []) or []
            except Exception:
                seg_cp = []
            original_cp = getattr(edge, 'control_points', None)
            if seg_cp:
                edge.control_points = seg_cp
            draw_edge_by_type(graph_canvas, dc, (int(s1[0]), int(s1[1])), (int(s2[0]), int(s2[1])), edge, pen_color=wx.Colour((color.Red() + other_edge.color[0]) // 2, (color.Green() + other_edge.color[1]) // 2, (color.Blue() + other_edge.color[2]) // 2))
        finally:
            if popped:
                try:
                    size = graph_canvas.GetSize()
                    center_x = size.width / 2.0
                    center_y = size.height / 2.0
                    gc.PushState()
                    gc.Translate(center_x + graph_canvas.pan_x, center_y + graph_canvas.pan_y)
                    if getattr(graph_canvas, 'world_rotation', 0.0) != 0.0:
                        gc.Rotate(math.radians(graph_canvas.world_rotation))
                    gc.Scale(graph_canvas.zoom, graph_canvas.zoom)
                except Exception:
                    pass
            # Restore edge control points
            try:
                edge.control_points = original_cp
            except Exception:
                pass
        if getattr(edge, 'directed', True):
            _draw_world_arrow(ax1, ay1, ax2, ay2, blend_color, max(1, int(edge.width * graph_canvas.zoom)))

        # Draw explicit self-loop(s) as ellipses around the uberedge
        self_loops = [tid for tid in explicit_list if tid == edge.id]
        if self_loops:
            loop_count = len(self_loops)
            base_r = max(10.0, float(edge.uber_width) * 0.45)
            for i in range(loop_count):
                scale = 1.0 + i * 0.2  # nested loops slightly larger
                rx = base_r * scale
                ry = base_r * 1.2 * scale
                ex = float(edge.uber_x)
                ey = float(edge.uber_y)
                path = gc.CreatePath()
                path.AddEllipse(ex - rx, ey - ry, rx * 2.0, ry * 2.0)
                loop_pen = wx.Colour(150, 150, 150)
                gc.SetPen(wx.Pen(loop_pen, max(1, int(edge.width * graph_canvas.zoom))))
                gc.StrokePath(path)
                # Arrow/yellow dot position along ellipse can be extended later (kept at top for now)
                if getattr(edge, 'directed', True):
                    theta = -math.pi / 2.0
                    tip_x = ex + rx * math.cos(theta)
                    tip_y = ey + ry * math.sin(theta)
                    tx = -rx * math.sin(theta)
                    ty =  ry * math.cos(theta)
                    tlen = math.hypot(tx, ty)
                    if tlen > 1e-6:
                        ux = tx / tlen
                        uy = ty / tlen
                        base_x = tip_x - ux * 1.0
                        base_y = tip_y - uy * 1.0
                        _draw_world_arrow(base_x, base_y, tip_x, tip_y, loop_pen, max(1, int(edge.width * graph_canvas.zoom)))
                # force refresh if there were self loops (to show immediately after creation)
                try:
                    graph_canvas.graph_modified.emit()
                except Exception:
                    pass
    else:
        # Fallback: draw in screen space if no GC
        # Simple straight line without parallel offsets
        for other_edge in connected_edges:
            if other_edge.id == edge.id:
                continue
            s1 = graph_canvas.world_to_screen(edge.uber_x, edge.uber_y)
            s2 = graph_canvas.world_to_screen(other_edge.uber_x, other_edge.uber_y)
            dc.SetPen(wx.Pen(color, max(1, int(edge.width * graph_canvas.zoom))))
            dc.DrawLine(int(s1[0]), int(s1[1]), int(s2[0]), int(s2[1]))
    
    # Draw the edge as a node (reuse ubergraph node drawing)
    draw_ubergraph_hyperedge(graph_canvas, dc, edge, color)


def draw_derivative_graph_hyperedge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge, color):
    """Draw a derivative graph representation (nodes connected if in same hyperedge)."""

    # Draw lines between all pairs of nodes in this hyperedge
    gc = dc.GetGraphicsContext()
    
    # Collect all nodes
    nodes = []
    if edge.source_id:
        source_node = graph_canvas.graph.get_node(edge.source_id)
        if source_node:
            nodes.append(source_node)
    
    for node_id in edge.source_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            nodes.append(node)
    
    if edge.target_id:
        target_node = graph_canvas.graph.get_node(edge.target_id)
        if target_node:
            nodes.append(target_node)
    
    for node_id in edge.target_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            nodes.append(node)
    
    # Draw lines between all pairs of nodes
    for i, node1 in enumerate(nodes):
        for node2 in nodes[i+1:]:
            # Draw line between nodes
            pos1 = graph_canvas.world_to_screen(node1.x, node1.y)
            pos2 = graph_canvas.world_to_screen(node2.x, node2.y)
            
            path = gc.CreatePath()
            path.MoveToPoint(pos1[0], pos1[1])
            path.AddLineToPoint(pos2[0], pos2[1])
            
            # Use edge color with some transparency
            alpha = 128 if edge.selected else 64
            line_color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)
            gc.SetPen(wx.Pen(line_color, max(1, int(edge.width * graph_canvas.zoom))))
            gc.StrokePath(path)


def draw_ubergraph_hyperedge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge, color):
    """Draw a hyperedge as a node with connections to its nodes (WORLD coords)."""

    gc = dc.GetGraphicsContext()
    if gc:
        def _draw_world_arrow(x1, y1, x2, y2, pen_color, width):
            dx = float(x2) - float(x1)
            dy = float(y2) - float(y1)
            seg_len = math.hypot(dx, dy)
            if seg_len <= 1e-6:
                return
            ux = dx / seg_len
            uy = dy / seg_len
            px = -uy
            py = ux
            arrow_size = max(8.0, float(width) * 3.0)
            arrow_width = arrow_size * 0.5
            tip_x = float(x2)
            tip_y = float(y2)
            bl_x = tip_x - arrow_size * ux + arrow_width * px
            bl_y = tip_y - arrow_size * uy + arrow_width * py
            br_x = tip_x - arrow_size * ux - arrow_width * px
            br_y = tip_y - arrow_size * uy - arrow_width * py
            ap = gc.CreatePath()
            ap.MoveToPoint(tip_x, tip_y)
            ap.AddLineToPoint(bl_x, bl_y)
            ap.AddLineToPoint(br_x, br_y)
            ap.CloseSubpath()
            gc.SetBrush(wx.Brush(pen_color))
            gc.SetPen(wx.Pen(pen_color, 1))
            gc.FillPath(ap)
            gc.StrokePath(ap)
        # Fill and stroke setup
        if edge.selected:
            gc.SetBrush(wx.Brush(wx.Colour(255, 255, 0)))  # Yellow for selected
        else:
            alpha = 128
            fill_color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)
            gc.SetBrush(wx.Brush(fill_color))
        gc.SetPen(wx.Pen(color, max(1, int(edge.width * graph_canvas.zoom))))

        xw, yw = float(edge.uber_x), float(edge.uber_y)
        w, h = float(edge.uber_width), float(edge.uber_height)

        # Draw shape in world coords
        if edge.uber_shape == "rectangle":
            path = gc.CreatePath()
            path.AddRectangle(xw - w/2.0, yw - h/2.0, w, h)
            gc.FillPath(path)
            gc.StrokePath(path)
        else:
            path = gc.CreatePath()
            path.AddEllipse(xw - w/2.0, yw - h/2.0, w, h)
            gc.FillPath(path)
            gc.StrokePath(path)

        # Label at center
        if edge.text:
            gc.SetFont(wx.Font(max(8, int(edge.font_size)), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL), wx.Colour(*edge.text_color))
            gc.DrawText(edge.text, xw, yw)

        # Helpers for anchor placement
        def _box_anchor_world(ebox, toward_x, toward_y):
            cx, cy = float(ebox.uber_x), float(ebox.uber_y)
            w2 = float(getattr(ebox, 'uber_width', 60.0)) / 2.0
            h2 = float(getattr(ebox, 'uber_height', 40.0)) / 2.0
            vx = float(toward_x) - cx
            vy = float(toward_y) - cy
            if abs(vx) < 1e-9 and abs(vy) < 1e-9:
                return cx, cy
            if getattr(ebox, 'uber_shape', 'rectangle') == 'ellipse':
                rx, ry = w2, h2
                t = 1.0 / math.sqrt((vx*vx)/(rx*rx) + (vy*vy)/(ry*ry))
                return cx + vx * t, cy + vy * t
            dx = vx; dy = vy
            t_vals = []
            if abs(dx) > 1e-9:
                t_vals.append(( w2 - 0.0) / dx)
                t_vals.append((-w2 - 0.0) / dx)
            if abs(dy) > 1e-9:
                t_vals.append(( h2 - 0.0) / dy)
                t_vals.append((-h2 - 0.0) / dy)
            candidates = []
            for t in t_vals:
                if t <= 0: continue
                px = cx + dx * t; py = cy + dy * t
                if abs(px - cx) <= w2 + 1e-6 and abs(py - cy) <= h2 + 1e-6:
                    candidates.append((px, py, t))
            if not candidates:
                return cx, cy
            candidates.sort(key=lambda p: p[2])
            return candidates[0][0], candidates[0][1]

        def _node_anchor_world(node_obj, toward_x, toward_y):
            nx, ny = float(node_obj.x), float(node_obj.y)
            node_w = float(getattr(node_obj, 'width', 0.0))
            node_h = float(getattr(node_obj, 'height', 0.0))
            vx = float(toward_x) - nx
            vy = float(toward_y) - ny
            if abs(vx) < 1e-9 and abs(vy) < 1e-9:
                return nx, ny
            # Rectangle intersection from node center toward target
            dx = vx; dy = vy
            w2 = node_w / 2.0; h2 = node_h / 2.0
            t_vals = []
            if abs(dx) > 1e-9:
                t_vals.append(( w2 - 0.0) / dx)
                t_vals.append((-w2 - 0.0) / dx)
            if abs(dy) > 1e-9:
                t_vals.append(( h2 - 0.0) / dy)
                t_vals.append((-h2 - 0.0) / dy)
            candidates = []
            for t in t_vals:
                if t <= 0: continue
                px = nx + dx * t; py = ny + dy * t
                if abs(px - nx) <= w2 + 1e-6 and abs(py - ny) <= h2 + 1e-6:
                    candidates.append((px, py, t))
            if not candidates:
                return nx, ny
            candidates.sort(key=lambda p: p[2])
            return candidates[0][0], candidates[0][1]

        # Connections to nodes
        def _stroke_to(node_obj, from_center):
            # Compute anchors on node and box according to anchor setting/direction
            box_ax, box_ay = _box_anchor_world(edge, float(node_obj.x), float(node_obj.y))
            node_ax, node_ay = _node_anchor_world(node_obj, box_ax, box_ay)
            sx, sy = (node_ax, node_ay) if from_center else (box_ax, box_ay)
            ex, ey = (box_ax, box_ay) if from_center else (node_ax, node_ay)
            # Draw the segment honoring edge rendering type using screen-space helper
            s1 = graph_canvas.world_to_screen(sx, sy)
            s2 = graph_canvas.world_to_screen(ex, ey)
            popped = False
            try:
                gc.PopState()
                popped = True
            except Exception:
                popped = False
            try:
                # Use per-segment control points if present for this node
                seg_cp = []
                try:
                    if hasattr(edge, 'metadata') and isinstance(edge.metadata, dict):
                        cp_map = edge.metadata.get('segment_cp_nodes', {}) or {}
                        seg_cp = cp_map.get(str(node_obj.id), []) or []
                except Exception:
                    seg_cp = []
                original_cp = getattr(edge, 'control_points', None)
                if seg_cp:
                    edge.control_points = seg_cp
                draw_edge_by_type(graph_canvas, dc, (int(s1[0]), int(s1[1])), (int(s2[0]), int(s2[1])), edge)
            finally:
                if popped:
                    try:
                        size = graph_canvas.GetSize()
                        center_x = size.width / 2.0
                        center_y = size.height / 2.0
                        gc.PushState()
                        gc.Translate(center_x + graph_canvas.pan_x, center_y + graph_canvas.pan_y)
                        if getattr(graph_canvas, 'world_rotation', 0.0) != 0.0:
                            gc.Rotate(math.radians(graph_canvas.world_rotation))
                        gc.Scale(graph_canvas.zoom, graph_canvas.zoom)
                    except Exception:
                        pass
                # Restore edge control points
                try:
                    edge.control_points = original_cp
                except Exception:
                    pass
            # Arrow/dot position t from metadata (default 0.5)
            t_val = 0.5
            try:
                if hasattr(edge, 'metadata') and isinstance(edge.metadata, dict):
                    tmap = edge.metadata.get('arrow_pos_nodes', {}) or {}
                    t_val = float(tmap.get(str(node_obj.id), 0.5))
            except Exception:
                t_val = 0.5
            t_val = max(0.0, min(1.0, t_val))
            ax = sx + (ex - sx) * t_val
            ay = sy + (ey - sy) * t_val
            if getattr(edge, 'directed', True):
                _draw_world_arrow(sx, sy, ax, ay, color, max(1, int(edge.width * graph_canvas.zoom)))
            # Yellow control dot
            try:
                gc.SetBrush(wx.Brush(wx.Colour(255, 255, 0)))
                gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
                r = max(3.0, float(edge.width))
                gc.DrawEllipse(ax - r, ay - r, r * 2.0, r * 2.0)
            except Exception:
                pass

        if edge.source_id:
            n = graph_canvas.graph.get_node(edge.source_id)
            if n:
                _stroke_to(n, True)
        for nid in edge.source_ids:
            n = graph_canvas.graph.get_node(nid)
            if n:
                _stroke_to(n, True)

        if edge.target_id:
            n = graph_canvas.graph.get_node(edge.target_id)
            if n:
                _stroke_to(n, False)
        for nid in edge.target_ids:
            n = graph_canvas.graph.get_node(nid)
            if n:
                _stroke_to(n, False)
    else:
        # Fallback to prior screen-space implementation if GC unavailable
        screen_x = graph_canvas.world_to_screen(edge.uber_x, edge.uber_y)
        width = int(edge.uber_width * graph_canvas.zoom)
        height = int(edge.uber_height * graph_canvas.zoom)
        if edge.selected:
            dc.SetBrush(wx.Brush(wx.Colour(255, 255, 0)))
        else:
            alpha = 128
            fill_color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)
            dc.SetBrush(wx.Brush(fill_color))
        dc.SetPen(wx.Pen(color, max(1, int(edge.width * graph_canvas.zoom))))
        if edge.uber_shape == "rectangle":
            dc.DrawRectangle(screen_x[0] - width//2, screen_x[1] - height//2, width, height)
        else:
            dc.DrawEllipse(screen_x[0] - width//2, screen_x[1] - height//2, width, height)
    
        # Draw node↔uberedge connections honoring anchor settings (screen space)
        def _rect_anchor_screen(cx, cy, w, h, tx, ty):
            w2 = w / 2.0; h2 = h / 2.0
            vx = tx - cx; vy = ty - cy
            if abs(vx) < 1e-9 and abs(vy) < 1e-9:
                return cx, cy
            t_vals = []
            if abs(vx) > 1e-9:
                t_vals.append(( w2) / vx)
                t_vals.append((-w2) / vx)
            if abs(vy) > 1e-9:
                t_vals.append(( h2) / vy)
                t_vals.append((-h2) / vy)
            candidates = []
            for t in t_vals:
                if t <= 0: continue
                px = cx + vx * t; py = cy + vy * t
                if abs(px - cx) <= w2 + 1e-6 and abs(py - cy) <= h2 + 1e-6:
                    candidates.append((px, py, t))
            if not candidates:
                return cx, cy
            candidates.sort(key=lambda p: p[2])
            return candidates[0][0], candidates[0][1]

        box_cx, box_cy = float(screen_x[0]), float(screen_x[1])
        box_w, box_h = float(width), float(height)

        def _stroke_screen_to(node_obj, as_source):
            ns = graph_canvas.world_to_screen(node_obj.x, node_obj.y)
            node_w = int(node_obj.width * graph_canvas.zoom)
            node_h = int(node_obj.height * graph_canvas.zoom)
            # Node anchor toward box
            nax, nay = _rect_anchor_screen(float(ns[0]), float(ns[1]), float(node_w), float(node_h), box_cx, box_cy)
            # Box anchor toward node
            bax, bay = _rect_anchor_screen(box_cx, box_cy, box_w, box_h, float(ns[0]), float(ns[1]))
            dc.DrawLine(int(nax), int(nay), int(bax), int(bay))
            if edge.selected:
                dc.DrawCircle(int(nax), int(nay), max(6, int(4 * graph_canvas.zoom)))
                dc.DrawCircle(int(bax), int(bay), max(6, int(4 * graph_canvas.zoom)))

        if edge.source_id:
            n = graph_canvas.graph.get_node(edge.source_id)
            if n:
                _stroke_screen_to(n, True)
        for nid in edge.source_ids:
            n = graph_canvas.graph.get_node(nid)
            if n:
                _stroke_screen_to(n, True)
        if edge.target_id:
            n = graph_canvas.graph.get_node(edge.target_id)
            if n:
                _stroke_screen_to(n, False)
        for nid in edge.target_ids:
            n = graph_canvas.graph.get_node(nid)
            if n:
                _stroke_screen_to(n, False)


def draw_radial_hyperedge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge, color):
    """Draw a radial layout visualization of the hyperedge with nodes arranged in a circle."""

    # Collect all node positions
    nodes = []
    if edge.source_id:
        source_node = graph_canvas.graph.get_node(edge.source_id)
        if source_node:
            pos = graph_canvas.world_to_screen(source_node.x, source_node.y)
            nodes.append(pos)
    
    for node_id in edge.source_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            pos = graph_canvas.world_to_screen(node.x, node.y)
            nodes.append(pos)
    
    if edge.target_id:
        target_node = graph_canvas.graph.get_node(edge.target_id)
        if target_node:
            pos = graph_canvas.world_to_screen(target_node.x, target_node.y)
            nodes.append(pos)
    
    for node_id in edge.target_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            pos = graph_canvas.world_to_screen(node.x, node.y)
            nodes.append(pos)
    
    if len(nodes) < 2:
        return
        
    # Calculate center and radius
    center_x = sum(x for x, y in nodes) / len(nodes)
    center_y = sum(y for x, y in nodes) / len(nodes)
    
    # Calculate radius as average distance from center
    radius = sum(math.sqrt((x - center_x)**2 + (y - center_y)**2) for x, y in nodes) / len(nodes)
    
    # Create arc path
    gc = dc.GetGraphicsContext()
    path = gc.CreatePath()
    
    # Calculate angles for each node
    node_angles = []
    for x, y in nodes:
        angle = math.atan2(y - center_y, x - center_x)
        node_angles.append(angle)
    
    # Sort angles
    node_angles.sort()
    
    # Add first point
    start_x = center_x + radius * math.cos(node_angles[0])
    start_y = center_y + radius * math.sin(node_angles[0])
    path.MoveToPoint(start_x, start_y)
    
    # Draw arcs between consecutive points
    for i in range(len(node_angles)):
        next_angle = node_angles[(i + 1) % len(node_angles)]
        end_x = center_x + radius * math.cos(next_angle)
        end_y = center_y + radius * math.sin(next_angle)
        
        # Calculate control points for smooth arc
        mid_angle = (node_angles[i] + next_angle) / 2
        if next_angle < node_angles[i]:  # Handle wrap-around
            mid_angle += math.pi
        
        # Control point distance factor (adjust for smoother/tighter curves)
        ctrl_dist = radius * 0.5
        
        # Control point
        ctrl_x = center_x + ctrl_dist * math.cos(mid_angle)
        ctrl_y = center_y + ctrl_dist * math.sin(mid_angle)
        
        # Add quadratic curve
        path.AddQuadCurveToPoint(ctrl_x, ctrl_y, end_x, end_y)
    
    # Fill the path
    alpha = 128 if edge.selected else 64
    fill_color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)
    gc.SetBrush(wx.Brush(fill_color))
    gc.FillPath(path)
    
    # Draw the outline
    gc.SetPen(wx.Pen(color, max(1, int(edge.width * graph_canvas.zoom))))
    gc.StrokePath(path)


def draw_zykov_hyperedge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge, color):
    """Draw a Zykov visualization of the hyperedge (nodes connected to a central point)."""

    # Collect all node positions
    nodes = []
    if edge.source_id:
        source_node = graph_canvas.graph.get_node(edge.source_id)
        if source_node:
            pos = graph_canvas.world_to_screen(source_node.x, source_node.y)
            nodes.append(pos)
    
    for node_id in edge.source_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            pos = graph_canvas.world_to_screen(node.x, node.y)
            nodes.append(pos)
    
    if edge.target_id:
        target_node = graph_canvas.graph.get_node(edge.target_id)
        if target_node:
            pos = graph_canvas.world_to_screen(target_node.x, target_node.y)
            nodes.append(pos)
    
    for node_id in edge.target_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            pos = graph_canvas.world_to_screen(node.x, node.y)
            nodes.append(pos)
    
    if len(nodes) < 2:
        return
        
    # Calculate centroid
    center_x = sum(x for x, y in nodes) / len(nodes)
    center_y = sum(y for x, y in nodes) / len(nodes)
    
    # Draw lines from center to each node
    dc.GetGraphicsContext().SetPen(wx.Pen(color, max(1, int(edge.width * graph_canvas.zoom))))
    
    # Draw central point
    radius = max(6, int(4 * graph_canvas.zoom))
    dc.GetGraphicsContext().SetBrush(wx.Brush(color))
    dc.GetGraphicsContext().DrawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
    
    # Draw lines to nodes
    for node_pos in nodes:
        gc = dc.GetGraphicsContext()
        path = gc.CreatePath()
        path.MoveToPoint(center_x, center_y)
        path.AddLineToPoint(node_pos[0], node_pos[1])
        gc.StrokePath(path)


def draw_polygon_hyperedge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge, color):
    """Draw a polygon-based visualization of the hyperedge."""

    # Collect all node positions
    nodes = []
    if edge.source_id:
        source_node = graph_canvas.graph.get_node(edge.source_id)
        if source_node:
            pos = graph_canvas.world_to_screen(source_node.x, source_node.y)
            nodes.append(pos)
    
    for node_id in edge.source_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            pos = graph_canvas.world_to_screen(node.x, node.y)
            nodes.append(pos)
    
    if edge.target_id:
        target_node = graph_canvas.graph.get_node(edge.target_id)
        if target_node:
            pos = graph_canvas.world_to_screen(target_node.x, target_node.y)
            nodes.append(pos)
    
    for node_id in edge.target_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            pos = graph_canvas.world_to_screen(node.x, node.y)
            nodes.append(pos)
    
    if len(nodes) < 3:
        return
        
    # Calculate convex hull
    hull = graph_canvas.graham_scan(nodes)
    
    # Create polygon path
    gc = dc.GetGraphicsContext()
    path = gc.CreatePath()
    path.MoveToPoint(hull[0][0], hull[0][1])
    
    # Add straight lines between hull points
    for i in range(1, len(hull)):
        path.AddLineToPoint(hull[i][0], hull[i][1])
    path.AddLineToPoint(hull[0][0], hull[0][1])  # Close the polygon
    
    # Fill the polygon
    alpha = 128 if edge.selected else 64
    fill_color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)
    dc.GetGraphicsContext().SetBrush(wx.Brush(fill_color))
    dc.GetGraphicsContext().FillPath(path)
    
    # Draw the outline
    dc.GetGraphicsContext().SetPen(wx.Pen(color, max(1, int(edge.width * graph_canvas.zoom))))
    dc.GetGraphicsContext().StrokePath(path)


def draw_blob_boundary(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge, color):
    """Draw a blob-like boundary that encompasses all nodes in the hyperedge."""

    # Collect all node positions
    nodes = []
    if edge.source_id:
        source_node = graph_canvas.graph.get_node(edge.source_id)
        if source_node:
            pos = graph_canvas.world_to_screen(source_node.x, source_node.y)
            nodes.append(pos)
    
    for node_id in edge.source_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            pos = graph_canvas.world_to_screen(node.x, node.y)
            nodes.append(pos)
    
    if edge.target_id:
        target_node = graph_canvas.graph.get_node(edge.target_id)
        if target_node:
            pos = graph_canvas.world_to_screen(target_node.x, target_node.y)
            nodes.append(pos)
    
    for node_id in edge.target_ids:
        node = graph_canvas.graph.get_node(node_id)
        if node:
            pos = graph_canvas.world_to_screen(node.x, node.y)
            nodes.append(pos)
    
    if not nodes:
        return
        
    # Calculate convex hull of nodes
    hull = graph_canvas.graham_scan(nodes)
    if len(hull) < 3:
        return
        
    # Create a smooth path around the hull points with padding
    padding = max(20, int(15 * graph_canvas.zoom))
    gc = dc.GetGraphicsContext()
    path = gc.CreatePath()
    
    # Start with the first hull point
    first_point = hull[0]
    path.MoveToPoint(first_point[0], first_point[1])
    
    # Add curved segments between hull points
    for i in range(len(hull)):
        p1 = hull[i]
        p2 = hull[(i + 1) % len(hull)]
        p3 = hull[(i + 2) % len(hull)]
        
        # Calculate control points for smooth curve
        v1x = p2[0] - p1[0]
        v1y = p2[1] - p1[1]
        v2x = p3[0] - p2[0]
        v2y = p3[1] - p2[1]
        
        # Normalize vectors
        v1_len = math.sqrt(v1x * v1x + v1y * v1y)
        v2_len = math.sqrt(v2x * v2x + v2y * v2y)
        if v1_len == 0 or v2_len == 0:
            continue
            
        v1x /= v1_len
        v1y /= v1_len
        v2x /= v2_len
        v2y /= v2_len
        
        # Calculate perpendicular vectors for padding
        perp1x = -v1y * padding
        perp1y = v1x * padding
        perp2x = -v2y * padding
        perp2y = v2x * padding
        
        # Calculate control points
        cp1 = (p2[0] - v1x * padding + perp1x,
                p2[1] - v1y * padding + perp1y)
        cp2 = (p2[0] + v2x * padding + perp2x,
                p2[1] + v2y * padding + perp2y)
        
        # Add curve segment
        path.AddCurveToPoint(cp1[0], cp1[1], cp2[0], cp2[1],
                            p3[0] + perp2x, p3[1] + perp2y)
    
    # Fill the path
    alpha = 128 if edge.selected else 64
    fill_color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)
    dc.GetGraphicsContext().SetBrush(wx.Brush(fill_color))
    dc.GetGraphicsContext().FillPath(path)
    
    # Draw the outline
    dc.GetGraphicsContext().SetPen(wx.Pen(color, max(1, int(edge.width * graph_canvas.zoom))))
    dc.GetGraphicsContext().StrokePath(path)


def draw_curved_surface(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge, color):
    """Draw a curved surface between two points for hyperedge visualization."""

    # Calculate control points for the curved surface
    dx = target_pos[0] - source_pos[0]
    dy = target_pos[1] - source_pos[1]
    dist = math.sqrt(dx * dx + dy * dy)
    
    # Calculate perpendicular vector for curve control points
    perp_x = -dy / dist * edge.width * 4
    perp_y = dx / dist * edge.width * 4
    
    # Create curved path using 4 control points
    gc = dc.GetGraphicsContext()
    path = gc.CreatePath()
    path.MoveToPoint(source_pos[0], source_pos[1])
    
    # Upper curve
    cp1 = (source_pos[0] + dx/3 + perp_x, source_pos[1] + dy/3 + perp_y)
    cp2 = (source_pos[0] + 2*dx/3 + perp_x, source_pos[1] + 2*dy/3 + perp_y)
    path.AddCurveToPoint(cp1[0], cp1[1], cp2[0], cp2[1], target_pos[0], target_pos[1])
    
    # Lower curve
    cp3 = (source_pos[0] + 2*dx/3 - perp_x, source_pos[1] + 2*dy/3 - perp_y)
    cp4 = (source_pos[0] + dx/3 - perp_x, source_pos[1] + dy/3 - perp_y)
    path.AddCurveToPoint(cp3[0], cp3[1], cp4[0], cp4[1], source_pos[0], source_pos[1])
    
    # Fill the path
    alpha = 128 if edge.selected else 64
    fill_color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)
    dc.GetGraphicsContext().SetBrush(wx.Brush(fill_color))
    dc.GetGraphicsContext().FillPath(path)
    
    # Draw the outline
    dc.GetGraphicsContext().SetPen(wx.Pen(color, max(1, int(edge.width * graph_canvas.zoom))))
    dc.GetGraphicsContext().StrokePath(path)


def draw_edge_segment(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge):
    """Draw a single edge segment with the edge's visual properties."""

    # Set up the pen
    color = wx.Colour(*edge.color)
    if edge.selected:
        # Brighten color for selected edges
        color = wx.Colour(min(color.Red() + 50, 255),
                        min(color.Green() + 50, 255),
                        min(color.Blue() + 50, 255))
    
    # For hyperedges, check visualization type
    if edge.is_hyperedge:
        if edge.hyperedge_visualization == "curved_surface":
            # Draw curved surface between nodes
            draw_curved_surface(graph_canvas, dc, source_pos, target_pos, edge, color)
            return
        elif edge.hyperedge_visualization == "blob_boundary":
            # Draw blob-like boundary around nodes
            draw_blob_boundary(graph_canvas, dc, edge, color)
            return
        elif edge.hyperedge_visualization == "polygon":
            # Draw polygon-based visualization
            draw_polygon_hyperedge(graph_canvas, dc, edge, color)
            return
        elif edge.hyperedge_visualization == "zykov":
            # Draw Zykov visualization
            draw_zykov_hyperedge(graph_canvas, dc, edge, color)
            return
        elif edge.hyperedge_visualization == "radial":
            # Draw radial layout visualization
            draw_radial_hyperedge(graph_canvas, dc, edge, color)
            return
        elif edge.hyperedge_visualization == "ubergraph":
            # Draw edge as a node with connections
            if edge.hyperedge_view == "line_graph":
                draw_line_graph_hyperedge(graph_canvas, dc, edge, color)
            elif edge.hyperedge_view == "derivative_graph":
                draw_derivative_graph_hyperedge(graph_canvas, dc, edge, color)
            else:  # standard view
                draw_ubergraph_hyperedge(graph_canvas, dc, edge, color)
            return
        
    # Set line style
    if edge.line_style == "dashed":
        pen_style = wx.PENSTYLE_LONG_DASH
    elif edge.line_style == "dotted":
        pen_style = wx.PENSTYLE_DOT
    else:
        pen_style = wx.PENSTYLE_SOLID
        
    # Resolve pen color: explicit override > edge.color > default color param > black
    try:
        if pen_color is not None:
            c = pen_color
        elif hasattr(edge, 'color') and edge.color is not None:
            c = wx.Colour(edge.color[0], edge.color[1], edge.color[2])
        else:
            c = color if isinstance(color, wx.Colour) else wx.Colour(0, 0, 0)
    except Exception:
        c = wx.Colour(0, 0, 0)
    dc.SetPen(wx.Pen(c, max(1, int(edge.width * graph_canvas.zoom)), pen_style))
    
    # Draw the line
    dc.DrawLine(int(source_pos[0]), int(source_pos[1]),
                int(target_pos[0]), int(target_pos[1]))

   
def draw_edge_by_type(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge, pen_color=None):
    """Draw edge based on the selected rendering type.
    pen_color allows callers to enforce a specific pen color (e.g., for blended links)
    while keeping thickness logic consistent.
    """

    # Check for composite curve first
    if edge and getattr(edge, 'is_composite', False) and getattr(edge, 'curve_segments', None):
        graph_canvas.draw_composite_edge(dc, source_pos, target_pos, edge)
        return
    
    # Check if this is a graph_canvas-loop
    source_node = graph_canvas.graph.get_node(edge.source_id)
    target_node = graph_canvas.graph.get_node(edge.target_id)
    is_graph_canvas_loop = source_node and target_node and source_node.id == target_node.id
    
    # Use edge-specific rendering type if set, otherwise use global
    rendering_type = edge.rendering_type if edge.rendering_type else graph_canvas.edge_rendering_type
    
    if rendering_type == "straight":
        if is_graph_canvas_loop:
            # For graph_canvas-loops with straight rendering, use control points to draw a visible loop
            if edge.control_points and len(edge.control_points) >= 1:
                try:
                    # Draw from node center to control point and back
                    cp = edge.control_points[0]
                    cp_screen = graph_canvas.world_to_screen(cp[0], cp[1])
                    dc.DrawLine(source_pos[0], source_pos[1], cp_screen[0], cp_screen[1])
                    dc.DrawLine(cp_screen[0], cp_screen[1], target_pos[0], target_pos[1])
                except (IndexError, TypeError, ValueError) as e:
                    print(f"DEBUG: ⚠️ Error drawing graph_canvas-loop with control point: {e}, using fallback")
                    # Fallback: draw a simple circle above the node
                    circle_radius = 20
                    dc.DrawCircle(source_pos[0], source_pos[1] - circle_radius, circle_radius)
            else:
                # Fallback: draw a simple circle above the node
                circle_radius = 20
                dc.DrawCircle(source_pos[0], source_pos[1] - circle_radius, circle_radius)
        else:
            # Draw straight line for normal edges
            dc.DrawLine(source_pos[0], source_pos[1], target_pos[0], target_pos[1])
        
    elif rendering_type == "curved":
        # Draw curved arc 
        draw_curved_edge(graph_canvas, dc, source_pos, target_pos, edge)
        
    elif rendering_type == "bspline":
        # Draw B-spline curve
        draw_bspline_edge(graph_canvas, dc, source_pos, target_pos, edge)
        
    elif rendering_type == "bezier":
        # Draw Bézier curve
        draw_bezier_edge(graph_canvas, dc, source_pos, target_pos, edge)
        
    elif rendering_type == "cubic_spline":
        # Draw cubic spline
        draw_cubic_spline_edge(graph_canvas, dc, source_pos, target_pos, edge)
        
    elif rendering_type == "nurbs":
        # Draw NURBS curve
        draw_nurbs_edge(graph_canvas, dc, source_pos, target_pos, edge)
        
    elif rendering_type == "polyline":
        # Draw polyline (segmented line)
        draw_polyline_edge(graph_canvas, dc, source_pos, target_pos, edge)
        
    elif rendering_type == "composite":
        # Force composite mode for this edge
        if edge and not getattr(edge, 'is_composite', False):
            edge.is_composite = True
            
    elif rendering_type == "freeform":
        # Draw freeform path
        if edge and edge.freeform_points and len(edge.freeform_points) >= 2:
            # Convert world coordinates to screen coordinates
            screen_points = []
            for point in edge.freeform_points:
                screen_pos = graph_canvas.world_to_screen(point[0], point[1])
                screen_points.append((screen_pos[0], screen_pos[1]))
            
            # Draw lines connecting all points
            for i in range(len(screen_points) - 1):
                dc.DrawLine(
                    screen_points[i][0], screen_points[i][1],
                    screen_points[i + 1][0], screen_points[i + 1][1]
                )
        
    else:
        # Default to straight line
        dc.DrawLine(source_pos[0], source_pos[1], target_pos[0], target_pos[1])


def draw_curved_edge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge=None):
    """Draw a curved arc edge using control points if available."""

    if edge and edge.control_points and len(edge.control_points) >= 1:
        try:
            # Use actual control point from edge
            control_screen = graph_canvas.world_to_screen(edge.control_points[0][0], edge.control_points[0][1])
            control_x, control_y = control_screen[0], control_screen[1]
        except (IndexError, TypeError, ValueError) as e:
            print(f"DEBUG: ⚠️ Error accessing curved edge control point: {e}, using default")
            # Calculate default control point position
            mid_x = (source_pos[0] + target_pos[0]) / 2
            mid_y = (source_pos[1] + target_pos[1]) / 2 - 30
            control_x, control_y = mid_x, mid_y
    else:
        # Calculate default control point for arc (offset perpendicular to the line)
        dx = target_pos[0] - source_pos[0]
        dy = target_pos[1] - source_pos[1]
        length = max(1, math.sqrt(dx*dx + dy*dy))
        
        # Create arc with control point offset perpendicular to line
        mid_x = (source_pos[0] + target_pos[0]) / 2
        mid_y = (source_pos[1] + target_pos[1]) / 2
        
        # Perpendicular offset (25% of distance)
        offset = length * 0.25
        perp_x = -dy / length * offset
        perp_y = dx / length * offset
        
        control_x = mid_x + perp_x
        control_y = mid_y + perp_y
    
    # Draw quadratic curve using multiple line segments
    segments = 20
    prev_x, prev_y = source_pos[0], source_pos[1]
    
    for i in range(1, segments + 1):
        t = i / segments
        t2 = t * t
        
        # Quadratic Bézier formula: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
        x = (1-t)**2 * source_pos[0] + 2*(1-t)*t * control_x + t2 * target_pos[0]
        y = (1-t)**2 * source_pos[1] + 2*(1-t)*t * control_y + t2 * target_pos[1]
        
        dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
        prev_x, prev_y = x, y


def draw_bspline_edge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge=None):
    """Draw a B-spline edge using actual control points with source and target as fixed endpoints."""

    if edge and edge.control_points and len(edge.control_points) >= 1:
        print(f"DEBUG: 🌊 B-spline using {len(edge.control_points)} edge control points")
        
        # For B-spline interpolation, we need to ensure curve passes through source and target
        # Use a different approach: interpolating B-spline through all points
        segments = 50
        prev_x, prev_y = source_pos[0], source_pos[1]
        
        # Convert control points from world coordinates to screen coordinates
        control_points_screen = []
        for control_point in edge.control_points:
            screen_pos = graph_canvas.world_to_screen(control_point[0], control_point[1])
            control_points_screen.append(screen_pos)
        
        # Create interpolation points: source -> control points -> target
        interpolation_points = [source_pos] + control_points_screen + [target_pos]
        
        for i in range(1, segments + 1):
            t = i / segments
            
            # Use interpolating spline through all points
            x, y = graph_canvas.evaluate_interpolating_spline(interpolation_points, t)
                
            dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x, prev_y = x, y
            
    else:
        print(f"DEBUG: 🌊 B-spline with 0 control points - drawing straight line")
        # With 0 control points, B-spline should be a straight line
        dc.DrawLine(int(source_pos[0]), int(source_pos[1]), int(target_pos[0]), int(target_pos[1]))


def draw_bezier_edge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge=None):
    """Draw a Bézier curve edge using variable control points."""

    # Create the full control points list: source + control points + target
    if edge and edge.control_points and len(edge.control_points) >= 1:
        print(f"DEBUG: 📐 Bézier using {len(edge.control_points)} edge control points")
        # Convert control points from world coordinates to screen coordinates
        control_points_screen = []
        for control_point in edge.control_points:
            screen_pos = graph_canvas.world_to_screen(control_point[0], control_point[1])
            control_points_screen.append(screen_pos)
        control_points = [source_pos] + control_points_screen + [target_pos]
    else:
        print(f"DEBUG: 📐 Bézier with 0 control points - drawing straight line")
        # With 0 control points, Bézier should be a straight line
        dc.DrawLine(int(source_pos[0]), int(source_pos[1]), int(target_pos[0]), int(target_pos[1]))
        return
    
    # Draw Bézier curve using line segments
    segments = 50
    prev_x, prev_y = source_pos[0], source_pos[1]
    
    for i in range(1, segments + 1):
        t = i / segments
        x, y = graph_canvas.evaluate_bezier_curve(control_points, t)
        
        dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
        prev_x, prev_y = x, y


def draw_cubic_spline_edge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge=None):
    """Draw a natural cubic spline edge using actual control points."""

    # Use edge's control points if available, otherwise draw straight line
    if (edge and hasattr(edge, 'control_points') and isinstance(edge.control_points, list) and len(edge.control_points) >= 1):
        try:
            print(f"DEBUG: 🔗 Cubic Spline using edge control points: {edge.control_points}")
            # Convert control points from world coordinates to screen coordinates
            control_points_screen = []
            for control_point in edge.control_points:
                screen_pos = graph_canvas.world_to_screen(control_point[0], control_point[1])
                control_points_screen.append(screen_pos)
            # Create points list: source -> control points -> target
            points = [source_pos] + control_points_screen + [target_pos]
        except (IndexError, TypeError, ValueError) as e:
            print(f"DEBUG: ⚠️ Error processing cubic spline control points: {e}, drawing straight line")
            dc.DrawLine(int(source_pos[0]), int(source_pos[1]), int(target_pos[0]), int(target_pos[1]))
            return
    else:
        print(f"DEBUG: 🔗 Cubic Spline with insufficient control points - drawing straight line")
        # With 0 or 1 control points, cubic spline should be a straight line
        dc.DrawLine(int(source_pos[0]), int(source_pos[1]), int(target_pos[0]), int(target_pos[1]))
        return
    
    # Draw a Catmull-Rom spline through all points for a smooth cubic-like path
    def catmull_rom(p0, p1, p2, p3, t):
        t2 = t * t
        t3 = t2 * t
        x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
        y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
        return x, y

    pts = points
    # Duplicate endpoints for boundary conditions
    if len(pts) == 2:
        pts = [pts[0], pts[0], pts[1], pts[1]]
    elif len(pts) == 3:
        pts = [pts[0], pts[0], pts[1], pts[2]]
    else:
        pts = [pts[0]] + pts + [pts[-1]]

    segments = 12
    prev_x, prev_y = pts[1][0], pts[1][1]
    for i in range(0, len(pts) - 3):
        p0, p1, p2, p3 = pts[i], pts[i+1], pts[i+2], pts[i+3]
        for j in range(1, segments + 1):
            t = j / segments
            x, y = catmull_rom(p0, p1, p2, p3, t)
            dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x, prev_y = x, y


def draw_nurbs_edge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge=None):
    """Draw a NURBS edge (simplified as rational Bézier) using variable control points."""

    # Use edge's control points if available, otherwise use defaults
    if edge and edge.control_points and len(edge.control_points) >= 1:
        print(f"DEBUG: ⚡ NURBS using {len(edge.control_points)} edge control points")
        # Create weighted control points: source -> edge control points -> target
        # Use higher weights for intermediate control points to make their influence more visible
        ctrl_points = [(source_pos[0], source_pos[1], 1.0)]  # Start with source
        
        # Convert control points from world coordinates to screen coordinates
        for cp in edge.control_points:
            screen_pos = graph_canvas.world_to_screen(cp[0], cp[1])
            ctrl_points.append((screen_pos[0], screen_pos[1], 3.0))  # Higher weight for control points
        
        ctrl_points.append((target_pos[0], target_pos[1], 1.0))  # End with target
    else:
        print(f"DEBUG: ⚡ NURBS with 0 control points - drawing straight line")
        # With 0 control points, NURBS should be a straight line
        dc.DrawLine(int(source_pos[0]), int(source_pos[1]), int(target_pos[0]), int(target_pos[1]))
        return
    
    # Draw rational Bézier with more segments for smoother curve
    segments = 40
    prev_x, prev_y = source_pos[0], source_pos[1]
    
    for i in range(1, segments + 1):
        t = i / segments
        try:
            x, y = graph_canvas.evaluate_rational_bezier_variable(ctrl_points, t)
            # Ensure we got valid coordinates
            if x is not None and y is not None:
                dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
                prev_x, prev_y = x, y
            else:
                # Fallback: draw straight line segment
                x = source_pos[0] + t * (target_pos[0] - source_pos[0])
                y = source_pos[1] + t * (target_pos[1] - source_pos[1])
                dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
                prev_x, prev_y = x, y
        except:
            # Fallback: draw straight line segment if evaluation fails
            x = source_pos[0] + t * (target_pos[0] - source_pos[0])
            y = source_pos[1] + t * (target_pos[1] - source_pos[1])
            dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x, prev_y = x, y


def draw_polyline_edge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge=None):
    """Draw a polyline edge (segmented) using actual control points."""

    # Use edge's control points if available, otherwise use defaults
    if edge and edge.control_points and len(edge.control_points) >= 1:
        # Convert control points from world coordinates to screen coordinates
        control_points_screen = []
        for control_point in edge.control_points:
            screen_pos = graph_canvas.world_to_screen(control_point[0], control_point[1])
            control_points_screen.append(screen_pos)
        
        # Draw lines connecting all points: source -> control points -> target
        prev_x, prev_y = source_pos[0], source_pos[1]
        for screen_point in control_points_screen + [target_pos]:
            x, y = screen_point[0], screen_point[1]
            dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x, prev_y = x, y
    else:
        print(f"DEBUG: 📊 Polyline with 0 control points - drawing straight line")
        # With 0 control points, polyline should be a straight line
        dc.DrawLine(int(source_pos[0]), int(source_pos[1]), int(target_pos[0]), int(target_pos[1]))


def draw_composite_edge(graph_canvas: "m_graph_canvas.GraphCanvas", dc, source_pos, target_pos, edge):
    """Draw a composite curve made of multiple curve segments."""

    if not edge or not edge.curve_segments:
        # Fallback to straight line
        dc.DrawLine(int(source_pos[0]), int(source_pos[1]), int(target_pos[0]), int(target_pos[1]))
        return
    
    print(f"DEBUG: 🔗 Drawing composite edge with {len(edge.curve_segments)} segments")
    
    # Calculate intermediate points for each segment
    num_segments = len(edge.curve_segments)
    segment_points = [source_pos]  # Start with source
    
    # Calculate intermediate points between segments
    for i in range(1, num_segments):
        t = i / num_segments
        x = source_pos[0] + t * (target_pos[0] - source_pos[0])
        y = source_pos[1] + t * (target_pos[1] - source_pos[1])
        segment_points.append((x, y))
    
    segment_points.append(target_pos)  # End with target
    
    # Draw each segment
    for i, segment in enumerate(edge.curve_segments):
        start_pos = segment_points[i]
        end_pos = segment_points[i + 1]
        
        segment_type = segment["type"]
        control_points = segment.get("control_points", [])
        weight = segment.get("weight", 1.0)
        
        print(f"DEBUG: 🔗 Drawing segment {i+1}: {segment_type} with {len(control_points)} control points")
        
        # Draw the segment using the appropriate method
        if segment_type == "straight":
            dc.DrawLine(int(start_pos[0]), int(start_pos[1]), int(end_pos[0]), int(end_pos[1]))
        elif segment_type == "curved":
            graph_canvas.draw_curved_segment(dc, start_pos, end_pos, control_points)
        elif segment_type == "bezier":
            graph_canvas.draw_bezier_segment(dc, start_pos, end_pos, control_points)
        elif segment_type == "bspline":
            graph_canvas.draw_bspline_segment(dc, start_pos, end_pos, control_points)
        elif segment_type == "cubic_spline":
            graph_canvas.draw_cubic_spline_segment(dc, start_pos, end_pos, control_points)
        elif segment_type == "nurbs":
            graph_canvas.draw_nurbs_segment(dc, start_pos, end_pos, control_points, weight)
        elif segment_type == "polyline":
            graph_canvas.draw_polyline_segment(dc, start_pos, end_pos, control_points)
        else:
            # Fallback to straight line
            dc.DrawLine(int(start_pos[0]), int(start_pos[1]), int(end_pos[0]), int(end_pos[1]))


def draw_curved_segment(graph_canvas: "m_graph_canvas.GraphCanvas", dc, start_pos, end_pos, control_points):
    """Draw a curved segment (quadratic Bézier)."""

    if control_points and len(control_points) >= 1:
        # Convert control point from world coordinates to screen coordinates
        cp_world = control_points[0]
        cp_screen = graph_canvas.world_to_screen(cp_world[0], cp_world[1])
        cp = (cp_screen[0], cp_screen[1])
    else:
        # Default control point
        mid_x = (start_pos[0] + end_pos[0]) / 2
        mid_y = (start_pos[1] + end_pos[1]) / 2
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = max(1, math.sqrt(dx*dx + dy*dy))
        offset = length * 0.25
        perp_x = -dy / length * offset
        perp_y = dx / length * offset
        cp = (mid_x + perp_x, mid_y + perp_y)
    
    # Draw quadratic Bézier
    segments = 20
    prev_x, prev_y = start_pos[0], start_pos[1]
    for i in range(1, segments + 1):
        t = i / segments
        x = (1-t)**2 * start_pos[0] + 2*(1-t)*t * cp[0] + t**2 * end_pos[0]
        y = (1-t)**2 * start_pos[1] + 2*(1-t)*t * cp[1] + t**2 * end_pos[1]
        dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
        prev_x, prev_y = x, y


def draw_bezier_segment(graph_canvas: "m_graph_canvas.GraphCanvas", dc, start_pos, end_pos, control_points):
    """Draw a Bézier curve segment."""

    if control_points and len(control_points) >= 1:
        # Convert control points from world coordinates to screen coordinates
        control_points_screen = []
        for cp in control_points:
            cp_screen = graph_canvas.world_to_screen(cp[0], cp[1])
            control_points_screen.append((cp_screen[0], cp_screen[1]))
        full_control_points = [start_pos] + control_points_screen + [end_pos]
    else:
        # Default cubic Bézier
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        ctrl1 = (start_pos[0] + dx * 0.3, start_pos[1] + dy * 0.3 - 20)
        ctrl2 = (start_pos[0] + dx * 0.7, start_pos[1] + dy * 0.7 + 20)
        full_control_points = [start_pos, ctrl1, ctrl2, end_pos]
    
    # Draw using the general Bézier evaluation
    segments = 30
    prev_x, prev_y = start_pos[0], start_pos[1]
    for i in range(1, segments + 1):
        t = i / segments
        x, y = graph_canvas.evaluate_bezier_curve(full_control_points, t)
        dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
        prev_x, prev_y = x, y


def draw_bspline_segment(graph_canvas: "m_graph_canvas.GraphCanvas", dc, start_pos, end_pos, control_points):
    """Draw a B-spline segment."""

    if control_points and len(control_points) >= 1:
        # Convert control points from world coordinates to screen coordinates
        control_points_screen = []
        for cp in control_points:
            cp_screen = graph_canvas.world_to_screen(cp[0], cp[1])
            control_points_screen.append((cp_screen[0], cp_screen[1]))
        points = [start_pos] + control_points_screen + [end_pos]
    else:
        # Default B-spline
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        ctrl1 = (start_pos[0] + dx * 0.33, start_pos[1] + dy * 0.33 - 15)
        ctrl2 = (start_pos[0] + dx * 0.67, start_pos[1] + dy * 0.67 + 15)
        points = [start_pos, ctrl1, ctrl2, end_pos]
    
    # Use interpolating spline
    segments = 30
    prev_x, prev_y = start_pos[0], start_pos[1]
    for i in range(1, segments + 1):
        t = i / segments
        x, y = graph_canvas.evaluate_interpolating_spline(points, t)
        dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
        prev_x, prev_y = x, y


def draw_cubic_spline_segment(graph_canvas: "m_graph_canvas.GraphCanvas", dc, start_pos, end_pos, control_points):
    """Draw a cubic spline segment."""

    if control_points and len(control_points) >= 1:
        # Convert control points from world coordinates to screen coordinates
        control_points_screen = []
        for cp in control_points:
            cp_screen = graph_canvas.world_to_screen(cp[0], cp[1])
            control_points_screen.append((cp_screen[0], cp_screen[1]))
        points = [start_pos] + control_points_screen + [end_pos]
    else:
        # Default cubic spline points
        points = [start_pos, end_pos]
    
    # Draw using interpolating spline
    segments = 20
    prev_x, prev_y = start_pos[0], start_pos[1]
    for i in range(1, segments + 1):
        t = i / segments
        x, y = graph_canvas.evaluate_interpolating_spline(points, t)
        dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
        prev_x, prev_y = x, y


def draw_nurbs_segment(graph_canvas: "m_graph_canvas.GraphCanvas", dc, start_pos, end_pos, control_points, weight=1.0):
    """Draw a NURBS segment."""

    if control_points and len(control_points) >= 1:
        # Create weighted control points
        ctrl_points = [(start_pos[0], start_pos[1], 1.0)]
        # Convert control points from world coordinates to screen coordinates
        for cp in control_points:
            cp_screen = graph_canvas.world_to_screen(cp[0], cp[1])
            ctrl_points.append((cp_screen[0], cp_screen[1], weight * 3.0))  # Higher weight
        ctrl_points.append((end_pos[0], end_pos[1], 1.0))
    else:
        # Default NURBS
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        ctrl_points = [
            (start_pos[0], start_pos[1], 1.0),
            (start_pos[0] + dx * 0.3, start_pos[1] + dy * 0.3 - 25, weight * 3.0),
            (start_pos[0] + dx * 0.7, start_pos[1] + dy * 0.7 + 25, weight * 3.0),
            (end_pos[0], end_pos[1], 1.0)
        ]
    
    # Draw using rational Bézier evaluation
    segments = 25
    prev_x, prev_y = start_pos[0], start_pos[1]
    for i in range(1, segments + 1):
        t = i / segments
        try:
            x, y = graph_canvas.evaluate_rational_bezier_variable(ctrl_points, t)
            dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x, prev_y = x, y
        except:
            # Fallback to linear interpolation
            x = start_pos[0] + t * (end_pos[0] - start_pos[0])
            y = start_pos[1] + t * (end_pos[1] - start_pos[1])
            dc.DrawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x, prev_y = x, y


def draw_polyline_segment(graph_canvas: "m_graph_canvas.GraphCanvas", dc, start_pos, end_pos, control_points):
    """Draw a polyline segment."""

    if control_points and len(control_points) >= 1:
        # Convert control points from world coordinates to screen coordinates
        control_points_screen = []
        for cp in control_points:
            cp_screen = graph_canvas.world_to_screen(cp[0], cp[1])
            control_points_screen.append((cp_screen[0], cp_screen[1]))
        points = [start_pos] + control_points_screen + [end_pos]
    else:
        # Default polyline with 2 intermediate points
        points = [
            start_pos,
            (start_pos[0] + (end_pos[0] - start_pos[0]) * 0.33, start_pos[1] + (end_pos[1] - start_pos[1]) * 0.33 + 10),
            (start_pos[0] + (end_pos[0] - start_pos[0]) * 0.67, start_pos[1] + (end_pos[1] - start_pos[1]) * 0.67 - 10),
            end_pos
        ]
        control_points_screen = points[1:-1]  # Use the default points as screen coordinates
    
    # Draw straight lines between all points
    prev_pos = start_pos
    for point in control_points_screen + [end_pos]:
        dc.DrawLine(int(prev_pos[0]), int(prev_pos[1]), int(point[0]), int(point[1]))
        prev_pos = point


def draw_control_points(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge):
    """Draw visual control points for an edge that can be dragged to modify curves."""

    source_node = graph_canvas.graph.get_node(edge.source_id)
    target_node = graph_canvas.graph.get_node(edge.target_id)
    
    if not source_node or not target_node:
        return
        
    # Initialize control points if edge doesn't have any yet
    if not edge.control_points:
        graph_canvas.initialize_control_points(edge, source_node, target_node)
        print(f"DEBUG: 🎛️ Control points initialized in draw_control_points for edge {edge.id}")
        
    # Get rendering type to determine how to show control structure
    rendering_type = edge.rendering_type if edge.rendering_type else graph_canvas.edge_rendering_type
    print(f"DEBUG: 🎛️ Control points for edge {edge.id}, type: {rendering_type}, points: {len(edge.control_points)} points")
    
    # For composite curves, show control points of the currently selected segment
    if rendering_type == "composite" and getattr(edge, 'is_composite', False):
        segment_index = getattr(graph_canvas, 'current_composite_segment', 0)
        if hasattr(edge, 'curve_segments') and segment_index < len(edge.curve_segments):
            segment = edge.curve_segments[segment_index]
            segment_type = segment.get("type", "bezier")
            segment_control_points = segment.get("control_points", [])
            
            print(f"DEBUG: 🔗 Drawing composite segment {segment_index} control points: {segment_type} with {len(segment_control_points)} points")
            
            # Draw control lines for this segment type
            if segment_type in ["bspline", "bezier", "cubic_spline", "nurbs", "polyline"] and segment_control_points:
                dc.SetPen(wx.Pen(wx.Colour(120, 120, 120), 2, wx.PENSTYLE_SHORT_DASH))
                
                if segment_type == "bezier" and len(segment_control_points) >= 2:
                    # Calculate segment endpoints for composite curve
                    total_segments = len(edge.curve_segments)
                    t_start = segment_index / total_segments
                    t_end = (segment_index + 1) / total_segments
                    
                    # Approximate segment start and end positions
                    start_pos = graph_canvas.calculate_position_on_curve(edge, source_node, target_node, t_start)
                    end_pos = graph_canvas.calculate_position_on_curve(edge, source_node, target_node, t_end)
                    
                    if start_pos and end_pos:
                        start_screen = graph_canvas.world_to_screen(start_pos[0], start_pos[1])
                        end_screen = graph_canvas.world_to_screen(end_pos[0], end_pos[1])
                        
                        # Draw control lines for bezier segment
                        cp1_screen = graph_canvas.world_to_screen(segment_control_points[0][0], segment_control_points[0][1])
                        cp2_screen = graph_canvas.world_to_screen(segment_control_points[1][0], segment_control_points[1][1])
                        
                        # Start to first control point
                        dc.DrawLine(int(start_screen[0]), int(start_screen[1]), 
                                    int(cp1_screen[0]), int(cp1_screen[1]))
                        # End to second control point  
                        dc.DrawLine(int(end_screen[0]), int(end_screen[1]), 
                                    int(cp2_screen[0]), int(cp2_screen[1]))
            
            # Draw segment control point dots
            control_radius = max(8, int(6 * graph_canvas.zoom))
            print(f"DEBUG: 🔗 Drawing {len(segment_control_points)} control points for composite segment {segment_index}")
            for i, control_point in enumerate(segment_control_points):
                screen_pos = graph_canvas.world_to_screen(control_point[0], control_point[1])
                print(f"DEBUG: 🔗 Composite segment {segment_index} control point {i}: world({control_point[0]:.1f}, {control_point[1]:.1f}) -> screen({screen_pos[0]:.1f}, {screen_pos[1]:.1f})")
                
                # Color based on control point index
                if i % 2 == 0:
                    color = wx.Colour(255, 100, 100)  # Red for even control points
                    border_color = wx.Colour(200, 50, 50)
                else:
                    color = wx.Colour(100, 255, 100)  # Green for odd control points
                    border_color = wx.Colour(50, 200, 50)
                
                dc.SetBrush(wx.Brush(color))
                dc.SetPen(wx.Pen(border_color, 2))
                dc.DrawCircle(int(screen_pos[0]), int(screen_pos[1]), control_radius)
        return  # Skip regular control point drawing for composite curves
    
    # Draw control lines (dashed lines showing control polygon) for specific curve types
    if rendering_type in ["bspline", "bezier", "cubic_spline", "nurbs", "polyline"]:
        print(f"DEBUG: 🎛️ Drawing {rendering_type} control lines")
        # Use a more visible dashed line style
        dc.SetPen(wx.Pen(wx.Colour(120, 120, 120), 2, wx.PENSTYLE_SHORT_DASH))
        
        if rendering_type == "bspline":
            # B-spline: Show control polygon connecting ALL control points including anchor endpoints
            # Get proper anchor points instead of node centers
            source_anchor_world, target_anchor_world = graph_canvas.get_edge_anchor_endpoints_world(edge, source_node, target_node)
            source_screen = graph_canvas.world_to_screen(source_anchor_world[0], source_anchor_world[1])
            target_screen = graph_canvas.world_to_screen(target_anchor_world[0], target_anchor_world[1])
            
            # Create complete control polygon: source -> all control points -> target
            all_points_screen = [source_screen]
            for control_point in edge.control_points:
                screen_pos = graph_canvas.world_to_screen(control_point[0], control_point[1])
                all_points_screen.append(screen_pos)
            all_points_screen.append(target_screen)
            
            # Draw dashed lines connecting all points in sequence
            for i in range(len(all_points_screen) - 1):
                p1 = all_points_screen[i]
                p2 = all_points_screen[i + 1]
                dc.DrawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
        
        elif rendering_type in ["bezier", "cubic_spline", "nurbs"]:
            # Bézier/Cubic/NURBS: Show control lines from anchor endpoints to control points
            # Get proper anchor points instead of node centers
            source_anchor_world, target_anchor_world = graph_canvas.get_edge_anchor_endpoints_world(edge, source_node, target_node)
            source_screen = graph_canvas.world_to_screen(source_anchor_world[0], source_anchor_world[1])
            target_screen = graph_canvas.world_to_screen(target_anchor_world[0], target_anchor_world[1])
            
            if (hasattr(edge, 'control_points') and edge.control_points and 
                isinstance(edge.control_points, list) and len(edge.control_points) >= 2):
                try:
                    cp1_screen = graph_canvas.world_to_screen(edge.control_points[0][0], edge.control_points[0][1])
                    cp2_screen = graph_canvas.world_to_screen(edge.control_points[1][0], edge.control_points[1][1])
                except (IndexError, TypeError, ValueError) as e:
                    print(f"DEBUG: ⚠️ Error accessing control points for handle lines: {e}")
                    return  # Skip drawing handles if control points are invalid
                
                print(f"DEBUG: 🎛️ Drawing {rendering_type} handle lines")
                # Source to first control point
                dc.DrawLine(int(source_screen[0]), int(source_screen[1]), 
                            int(cp1_screen[0]), int(cp1_screen[1]))
                # Target to second control point  
                dc.DrawLine(int(target_screen[0]), int(target_screen[1]), 
                            int(cp2_screen[0]), int(cp2_screen[1]))
            else:
                print(f"DEBUG: ⚠️ {rendering_type} needs 2+ control points, has {len(edge.control_points)}")
        
        elif rendering_type == "polyline":
            # Polyline: Show straight lines connecting all segments
            # Get proper anchor points instead of node centers
            source_anchor_world, target_anchor_world = graph_canvas.get_edge_anchor_endpoints_world(edge, source_node, target_node)
            source_screen = graph_canvas.world_to_screen(source_anchor_world[0], source_anchor_world[1])
            prev_screen = source_screen
            
            for control_point in edge.control_points:
                screen_pos = graph_canvas.world_to_screen(control_point[0], control_point[1])
                dc.DrawLine(int(prev_screen[0]), int(prev_screen[1]), 
                            int(screen_pos[0]), int(screen_pos[1]))
                prev_screen = screen_pos
            
            # Connect to target anchor
            target_screen = graph_canvas.world_to_screen(target_anchor_world[0], target_anchor_world[1])
            dc.DrawLine(int(prev_screen[0]), int(prev_screen[1]), 
                        int(target_screen[0]), int(target_screen[1]))
        
    # Draw control point dots - use same radius as hit detection
    control_radius = max(10, int(8 * graph_canvas.zoom))  # Match hit detection radius
    
    print(f"DEBUG: 🎛️ Drawing {len(edge.control_points)} control points for {rendering_type} edge {edge.id} with radius {control_radius}")
    
    for i, control_point in enumerate(edge.control_points):
        screen_pos = graph_canvas.world_to_screen(control_point[0], control_point[1])
        
        print(f"DEBUG: 🎛️ Drawing control point {i}: world({control_point[0]:.1f}, {control_point[1]:.1f}) -> screen({screen_pos[0]:.1f}, {screen_pos[1]:.1f})")
        
        # Color based on control point index for better visibility
        if i % 2 == 0:
            color = wx.Colour(255, 100, 100)  # Red for even control points
            border_color = wx.Colour(200, 50, 50)
        else:
            color = wx.Colour(100, 255, 100)  # Green for odd control points
            border_color = wx.Colour(50, 200, 50)
        
        dc.SetBrush(wx.Brush(color))
        dc.SetPen(wx.Pen(border_color, 3))  # Thicker border for better visibility
        dc.DrawCircle(int(screen_pos[0]), int(screen_pos[1]), control_radius)

   
def draw_arrow_position_control(graph_canvas: "m_graph_canvas.GraphCanvas", dc, edge):
    """Draw a yellow dot that can be dragged to control arrow position along the edge."""

    source_node = graph_canvas.graph.get_node(edge.source_id)
    target_node = graph_canvas.graph.get_node(edge.target_id)
    
    if not source_node or not target_node:
        print(f"DEBUG: 🟡 Cannot draw arrow control - missing nodes for edge {edge.id}")
        return
    
    # Get arrow position along the curve (0.0 = source, 1.0 = target)
    arrow_pos = getattr(edge, 'arrow_position', 1.0)
    print(f"DEBUG: 🟡 Drawing arrow control for edge {edge.id} at position {arrow_pos:.2f}")
    
    # Calculate position on curve at arrow_pos using proper anchor points
    try:
        # Get the actual anchor endpoints for accurate curve calculation
        source_anchor_world, target_anchor_world = graph_canvas.get_edge_anchor_endpoints_world(edge, source_node, target_node)
        print(f"DEBUG: 🟡 Using anchor endpoints for yellow dot: source {source_anchor_world}, target {target_anchor_world}")
        
        # Calculate position using anchor-based curve calculation
        arrow_world_pos = graph_canvas.calculate_position_on_curve_with_anchors(edge, source_anchor_world, target_anchor_world, arrow_pos)
        if not arrow_world_pos:
            print(f"DEBUG: 🟡 Failed to calculate curve position for edge {edge.id}")
            return
            
        arrow_screen_pos = graph_canvas.world_to_screen(arrow_world_pos[0], arrow_world_pos[1])
        
        # Draw yellow control dot
        yellow_radius = max(6, int(5 * graph_canvas.zoom))
        dc.SetBrush(wx.Brush(wx.Colour(255, 255, 0)))  # Bright yellow
        dc.SetPen(wx.Pen(wx.Colour(200, 200, 0), 2))   # Darker yellow border
        dc.DrawCircle(int(arrow_screen_pos[0]), int(arrow_screen_pos[1]), yellow_radius)
        
        # Store for interaction
        edge._arrow_screen_pos = arrow_screen_pos
        edge._arrow_radius = yellow_radius
        
        print(f"DEBUG: 🟡 Drew yellow arrow control at world ({arrow_world_pos[0]:.1f}, {arrow_world_pos[1]:.1f}) -> screen ({arrow_screen_pos[0]:.1f}, {arrow_screen_pos[1]:.1f})")
        
    except Exception as e:
        print(f"DEBUG: 🏹 Error drawing arrow position control: {e}")
    
    # B-spline control points list is now handled in the sidebar properties panel

