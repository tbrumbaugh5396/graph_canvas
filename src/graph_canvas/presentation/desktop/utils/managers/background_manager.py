"""
Manager for handling canvas background layers.
"""

import wx
import json
import math
from typing import List, Optional, Dict
from graph_canvas.presentation.desktop.models.background_layer import BackgroundLayer, BackgroundMode


class BackgroundManager:
    """Manages background layers and their rendering."""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.layers: List[BackgroundLayer] = []
        self.active_layer: Optional[BackgroundLayer] = None
        
    def add_layer(self, name: str = "New Layer") -> BackgroundLayer:
        """Add a new layer."""
        layer = BackgroundLayer(name)
        layer.z_index = len(self.layers)  # Put on top
        self.layers.append(layer)
        self.active_layer = layer
        return layer
        
    def remove_layer(self, layer: BackgroundLayer) -> bool:
        """Remove a layer."""
        if layer in self.layers:
            self.layers.remove(layer)
            if self.active_layer == layer:
                self.active_layer = self.layers[-1] if self.layers else None
            return True
        return False
        
    def move_layer(self, layer: BackgroundLayer, new_index: int) -> bool:
        """Move a layer to a new z-index."""
        if layer not in self.layers:
            return False
            
        old_index = self.layers.index(layer)
        if 0 <= new_index < len(self.layers):
            self.layers.pop(old_index)
            self.layers.insert(new_index, layer)
            
            # Update z-indices
            for i, l in enumerate(self.layers):
                l.z_index = i
                
            return True
        return False
        
    def draw_layers(self, dc: wx.DC):
        """Draw all visible layers in z-index order."""
        if not self.layers:
            return
            
        # Sort layers by z-index
        sorted_layers = sorted(self.layers, key=lambda l: l.z_index)
        
        # Get graphics context from the main DC
        gc = dc.GetGraphicsContext() if hasattr(dc, 'GetGraphicsContext') else None
        if not gc:
            print("DEBUG: No graphics context available for background drawing")
            return
            
        print("DEBUG: Got graphics context for background drawing")
        
        for layer in sorted_layers:
            if not layer.visible or not layer.bitmap:
                continue
                
            # Push state before drawing this layer
            gc.PushState()
            print(f"DEBUG: Pushed state for layer '{layer.name}'")

            if layer.fixed_position:
                # For fixed position layers, handle transform based on settings
                matrix = gc.CreateMatrix()
                print(f"DEBUG: Created transform matrix for layer '{layer.name}'")
                
                if layer.use_world_position:
                    # First apply zoom to maintain grid-relative positioning
                    matrix.Scale(self.canvas.zoom, self.canvas.zoom)
                    print(f"DEBUG: Applied zoom {self.canvas.zoom} to matrix")
                    
                    # Then apply inverse pan in world coordinates to move with grid
                    matrix.Translate(-self.canvas.pan_x * self.canvas.zoom, 
                                  -self.canvas.pan_y * self.canvas.zoom)
                    print(f"DEBUG: Applied pan ({-self.canvas.pan_x * self.canvas.zoom}, {-self.canvas.pan_y * self.canvas.zoom}) to matrix")
                
                if layer.follow_rotation and self.canvas.world_rotation != 0.0:
                    # Finally apply rotation around screen center
                    size = self.canvas.GetSize()
                    center_x = size.width / 2
                    center_y = size.height / 2
                    
                    # Move to center, rotate, move back
                    matrix.Translate(center_x, center_y)
                    matrix.Rotate(math.radians(self.canvas.world_rotation))
                    matrix.Translate(-center_x, -center_y)
                    print(f"DEBUG: Applied rotation {self.canvas.world_rotation}° around ({center_x}, {center_y})")
                
                gc.SetTransform(matrix)
                print("DEBUG: Applied transform matrix to graphics context")
            else:
                # For non-fixed position layers, apply transforms in order:
                # 1. Scale (zoom)
                gc.Scale(self.canvas.zoom, self.canvas.zoom)
                print(f"DEBUG: Applied zoom {self.canvas.zoom}")
                
                # 2. Translate (pan)
                gc.Translate(self.canvas.pan_x, self.canvas.pan_y)
                print(f"DEBUG: Applied translation ({self.canvas.pan_x}, {self.canvas.pan_y})")
                
                # 3. Rotate (if needed)
                if self.canvas.world_rotation != 0.0 and layer.follow_rotation:
                    size = self.canvas.GetSize()
                    center_x = size.width / 2
                    center_y = size.height / 2
                    gc.Translate(center_x, center_y)
                    gc.Rotate(math.radians(self.canvas.world_rotation))
                    gc.Translate(-center_x, -center_y)
                    print(f"DEBUG: Applied rotation {self.canvas.world_rotation}°")
            
            # Draw the layer based on its mode
            if layer.mode == BackgroundMode.SINGLE:
                print(f"DEBUG: Drawing single image layer '{layer.name}'")
                self._draw_single_image(layer, dc)
            elif layer.mode == BackgroundMode.TILED:
                print(f"DEBUG: Drawing tiled image layer '{layer.name}'")
                self._draw_tiled_images(layer, dc)
            elif layer.mode == BackgroundMode.POSITIONED:
                print(f"DEBUG: Drawing positioned image layer '{layer.name}'")
                self._draw_positioned_images(layer, dc)
            
            # Restore graphics context state
            gc.PopState()
            print(f"DEBUG: Popped graphics context state for layer '{layer.name}'")
            
    def _draw_single_image(self, layer: BackgroundLayer, dc: wx.DC):
        """Draw a single background image."""
        if not layer.bitmap:
            return
            
        dc_size = dc.GetSize()
        bmp_size = layer.bitmap.GetSize()
        
        if layer.stretch:
            if layer.maintain_aspect:
                # Calculate aspect-correct scaling
                dc_aspect = dc_size.width / dc_size.height
                bmp_aspect = bmp_size.width / bmp_size.height
                
                if dc_aspect > bmp_aspect:
                    # Fit to height
                    height = dc_size.height
                    width = height * bmp_aspect
                    x = (dc_size.width - width) / 2
                    y = 0
                else:
                    # Fit to width
                    width = dc_size.width
                    height = width / bmp_aspect
                    x = 0
                    y = (dc_size.height - height) / 2
                    
                scaled_bmp = layer.bitmap.ConvertToImage().Scale(
                    int(width), int(height), wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
                
                # Apply opacity if needed
                if layer.opacity < 1.0:
                    img = scaled_bmp.ConvertToImage()
                    img = img.AdjustChannels(1.0, 1.0, 1.0, layer.opacity)
                    scaled_bmp = img.ConvertToBitmap()
                
                dc.DrawBitmap(scaled_bmp, x, y, True)
            else:
                # Stretch to fill
                scaled_bmp = layer.bitmap.ConvertToImage().Scale(
                    dc_size.width, dc_size.height, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
                
                # Apply opacity if needed
                if layer.opacity < 1.0:
                    img = scaled_bmp.ConvertToImage()
                    img = img.AdjustChannels(1.0, 1.0, 1.0, layer.opacity)
                    scaled_bmp = img.ConvertToBitmap()
                
                dc.DrawBitmap(scaled_bmp, 0, 0, True)
        else:
            # Center without stretching
            x = (dc_size.width - bmp_size.width) / 2
            y = (dc_size.height - bmp_size.height) / 2
            
            # Apply opacity if needed
            current_bmp = layer.bitmap
            if layer.opacity < 1.0:
                img = current_bmp.ConvertToImage()
                img = img.AdjustChannels(1.0, 1.0, 1.0, layer.opacity)
                current_bmp = img.ConvertToBitmap()
            
            dc.DrawBitmap(current_bmp, x, y, True)
            
    def _draw_tiled_images(self, layer: BackgroundLayer, dc: wx.DC):
        """Draw tiled background images."""
        if not layer.bitmap:
            return
            
        dc_size = dc.GetSize()
        bmp_size = layer.bitmap.GetSize()
        
        # Calculate tile spacing
        x_spacing = bmp_size.width + layer.tile_spacing[0]
        y_spacing = bmp_size.height + layer.tile_spacing[1]
        
        # Calculate number of tiles needed (add extra for rotation coverage)
        x_tiles = int(dc_size.width / x_spacing) + 4
        y_tiles = int(dc_size.height / y_spacing) + 4
        
        # Calculate offset to center the grid
        x_offset = (dc_size.width - (x_tiles * x_spacing)) / 2
        y_offset = (dc_size.height - (y_tiles * y_spacing)) / 2
        
        # Apply opacity if needed
        current_bmp = layer.bitmap
        if layer.opacity < 1.0:
            img = current_bmp.ConvertToImage()
            img = img.AdjustChannels(1.0, 1.0, 1.0, layer.opacity)
            current_bmp = img.ConvertToBitmap()
        
        # Draw tiles
        for y in range(y_tiles):
            for x in range(x_tiles):
                pos_x = x_offset + (x * x_spacing)
                pos_y = y_offset + (y * y_spacing)
                dc.DrawBitmap(current_bmp, pos_x, pos_y, True)
                
    def _draw_positioned_images(self, layer: BackgroundLayer, dc: wx.DC):
        """Draw images at specific positions."""
        if not layer.bitmap or not layer.positions:
            return
            
        for pos in layer.positions:
            # Start with original bitmap
            current_bmp = layer.bitmap
            
            # Scale if needed
            if pos.scale != 1.0:
                orig_size = current_bmp.GetSize()
                new_width = int(orig_size.width * pos.scale)
                new_height = int(orig_size.height * pos.scale)
                
                img = current_bmp.ConvertToImage()
                if not img.IsOk():
                    continue
                    
                scaled_img = img.Scale(new_width, new_height, wx.IMAGE_QUALITY_HIGH)
                if not scaled_img.IsOk():
                    continue
                    
                current_bmp = scaled_img.ConvertToBitmap()
                if not current_bmp.IsOk():
                    continue
            
            # Rotate if needed
            if pos.rotation != 0.0:
                img = current_bmp.ConvertToImage()
                if not img.IsOk():
                    continue
                    
                rotated_img = img.Rotate(math.radians(pos.rotation), wx.Point(0, 0))
                if not rotated_img.IsOk():
                    continue
                    
                current_bmp = rotated_img.ConvertToBitmap()
                if not current_bmp.IsOk():
                    continue
            
            # Calculate drawing position
            if layer.use_world_position:
                # Use world coordinates directly
                draw_x = pos.x
                draw_y = pos.y
            else:
                # Convert to screen coordinates
                screen_x = pos.x * self.canvas.zoom
                screen_y = pos.y * self.canvas.zoom
                draw_x, draw_y = screen_x, screen_y
            
            # Apply opacity if needed
            if pos.opacity < 1.0:
                img = current_bmp.ConvertToImage()
                if img.IsOk():
                    img = img.AdjustChannels(1.0, 1.0, 1.0, pos.opacity)
                    current_bmp = img.ConvertToBitmap()
            
            # Draw the bitmap
            dc.DrawBitmap(current_bmp, draw_x, draw_y, True)
            
    def save_state(self) -> dict:
        """Save background state to dictionary."""
        return {
            "layers": [layer.to_dict() for layer in self.layers],
            "active_layer_index": self.layers.index(self.active_layer) if self.active_layer else -1
        }
        
    def load_state(self, state: dict):
        """Load background state from dictionary."""
        self.layers.clear()
        self.active_layer = None
        
        for layer_data in state.get("layers", []):
            layer = BackgroundLayer.from_dict(layer_data)
            self.layers.append(layer)
            
        active_index = state.get("active_layer_index", -1)
        if 0 <= active_index < len(self.layers):
            self.active_layer = self.layers[active_index]