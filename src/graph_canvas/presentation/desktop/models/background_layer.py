"""
Background layer model for managing canvas background images.
"""

import wx
import os
from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum


class BackgroundMode(Enum):
    """Background image display modes."""
    SINGLE = "single"  # Single image centered or stretched
    TILED = "tiled"    # Image tiled across canvas
    POSITIONED = "positioned"  # Multiple images at specific positions


@dataclass
class ImagePosition:
    """Position and properties for a background image."""
    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0


class BackgroundLayer:
    """A layer containing background image(s) with positioning and properties."""
    
    def __init__(self, name: str = "New Layer"):
        self.name = name
        self.visible = True
        self.opacity = 1.0  # Layer-wide opacity
        self.mode = BackgroundMode.SINGLE
        self.image_path: Optional[str] = None
        self.bitmap: Optional[wx.Bitmap] = None
        self.positions: List[ImagePosition] = []  # Used for POSITIONED mode
        self.tile_spacing: Tuple[float, float] = (0.0, 0.0)  # Used for TILED mode
        self.stretch = False  # Whether to stretch single image to fit canvas
        self.maintain_aspect = True  # Whether to maintain aspect ratio when stretching
        self.z_index = 0  # Layer ordering (higher numbers = more in front)
        self.fixed_position = False  # Whether the layer stays fixed in screen space
        self.fixed_width = None   # Fixed width in pixels (None = auto)
        self.fixed_height = None  # Fixed height in pixels (None = auto)
        self.follow_rotation = True  # Whether the layer rotates with the world
        self.use_world_position = False  # Whether to use world coordinates instead of screen coordinates
        
    def load_image(self, image_path: str) -> bool:
        """Load an image from a file path."""
        print(f"DEBUG: Loading image from {image_path}")
        if not os.path.exists(image_path):
            print(f"DEBUG: Image file does not exist: {image_path}")
            return False
            
        try:
            image = wx.Image(image_path)
            if not image.IsOk():
                print(f"DEBUG: Failed to load valid image from {image_path}")
                return False
                
            print(f"DEBUG: Successfully loaded image {image_path} ({image.GetWidth()}x{image.GetHeight()})")
            self.bitmap = wx.Bitmap(image)
            if not self.bitmap.IsOk():
                print(f"DEBUG: Failed to create valid bitmap from {image_path}")
                return False
                
            print(f"DEBUG: Successfully created bitmap ({self.bitmap.GetWidth()}x{self.bitmap.GetHeight()})")
            self.image_path = image_path
            return True
        except Exception as e:
            print(f"DEBUG: Failed to load image {image_path}: {e}")
            return False
            
    def add_position(self, x: float, y: float, scale: float = 1.0, 
                    rotation: float = 0.0, opacity: float = 1.0) -> ImagePosition:
        """Add a new image position for POSITIONED mode."""
        pos = ImagePosition(x, y, scale, rotation, opacity)
        self.positions.append(pos)
        return pos
        
    def remove_position(self, position: ImagePosition) -> bool:
        """Remove an image position."""
        if position in self.positions:
            self.positions.remove(position)
            return True
        return False
        
    def set_tile_spacing(self, x_spacing: float, y_spacing: float):
        """Set the spacing between tiled images."""
        self.tile_spacing = (x_spacing, y_spacing)
        
    def to_dict(self) -> dict:
        """Convert layer to dictionary for serialization."""
        return {
            "name": self.name,
            "visible": self.visible,
            "opacity": self.opacity,
            "mode": self.mode.value,
            "image_path": self.image_path,
            "positions": [(p.x, p.y, p.scale, p.rotation, p.opacity) 
                         for p in self.positions],
            "tile_spacing": self.tile_spacing,
            "stretch": self.stretch,
            "maintain_aspect": self.maintain_aspect,
            "z_index": self.z_index,
            "fixed_position": self.fixed_position,
            "fixed_width": self.fixed_width,
            "fixed_height": self.fixed_height,
            "follow_rotation": self.follow_rotation,
            "use_world_position": self.use_world_position
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'BackgroundLayer':
        """Create layer from dictionary."""
        layer = cls(data.get("name", "Unnamed Layer"))
        layer.visible = data.get("visible", True)
        layer.opacity = data.get("opacity", 1.0)
        layer.mode = BackgroundMode(data.get("mode", "single"))
        layer.image_path = data.get("image_path")
        if layer.image_path:
            layer.load_image(layer.image_path)
        layer.positions = [ImagePosition(*pos) for pos in data.get("positions", [])]
        layer.tile_spacing = tuple(data.get("tile_spacing", (0.0, 0.0)))
        layer.stretch = data.get("stretch", False)
        layer.maintain_aspect = data.get("maintain_aspect", True)
        layer.z_index = data.get("z_index", 0)
        layer.fixed_position = data.get("fixed_position", False)
        layer.fixed_width = data.get("fixed_width", None)
        layer.fixed_height = data.get("fixed_height", None)
        layer.follow_rotation = data.get("follow_rotation", True)
        layer.use_world_position = data.get("use_world_position", False)
        return layer
