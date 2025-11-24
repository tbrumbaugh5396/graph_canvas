#!/usr/bin/env python3
"""
Create macOS Application Icon for Graph Canvas (Graph Editor)
Generates a high-resolution icon with graph/dependency design
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    """Create a modern graph canvas icon"""

    # Create high-resolution image for icon (1024x1024 for macOS)
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background with rounded corners and gradient effect
    margin = 80
    bg_rect = [margin, margin, size - margin, size - margin]

    # Draw rounded rectangle background
    corner_radius = 120
    draw.rounded_rectangle(bg_rect, corner_radius,
                           fill=(45, 55, 72, 255))  # Dark blue-gray

    # Add subtle border
    border_margin = margin - 10
    border_rect = [
        border_margin, border_margin, size - border_margin,
        size - border_margin
    ]
    draw.rounded_rectangle(border_rect,
                           corner_radius + 10,
                           outline=(200, 200, 200, 100),
                           width=8)

    # Draw a stylized dependency graph: nodes and connecting edges
    center_x, center_y = size // 2, size // 2 + 40
    node_radius = 38

    # Define node positions (star-like layout)
    nodes = [
        (center_x, center_y - 220),
        (center_x - 200, center_y - 80),
        (center_x + 200, center_y - 80),
        (center_x - 160, center_y + 140),
        (center_x + 160, center_y + 140),
        (center_x, center_y + 40),
    ]

    # Edges as pairs of indices
    edges = [
        (0, 5), (1, 5), (2, 5), (5, 3), (5, 4), (1, 3), (2, 4)
    ]

    # Edge drawing
    for a, b in edges:
        ax, ay = nodes[a]
        bx, by = nodes[b]
        draw.line([(ax, ay), (bx, by)], fill=(140, 170, 255, 160), width=10)

    # Node colors
    node_colors = [
        (59, 130, 246, 255),  # blue
        (16, 185, 129, 255),  # emerald
        (245, 158, 11, 255),  # amber
        (139, 92, 246, 255),  # violet
        (236, 72, 153, 255),  # pink
        (34, 197, 94, 255),   # green
    ]

    # Draw nodes with subtle shadow
    for (x, y), color in zip(nodes, node_colors):
        draw.ellipse([x - node_radius - 4, y - node_radius + 4,
                      x + node_radius - 4, y + node_radius + 4],
                     fill=(0, 0, 0, 40))
        draw.ellipse([x - node_radius, y - node_radius,
                      x + node_radius, y + node_radius],
                     fill=color)

    # Add title text at the top
    try:
        # Try to use a nice font
        font_size = 80
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",
                                  font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    title = "Graph Canvas"
    title_bbox = draw.textbbox((0, 0), title, font=font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (size - title_width) // 2
    title_y = 180

    # Draw title with shadow
    draw.text((title_x + 3, title_y + 3),
              title,
              font=font,
              fill=(0, 0, 0, 100))
    draw.text((title_x, title_y), title, font=font, fill=(255, 255, 255, 255))

    return img


def create_icon_set():
    """Create a complete icon set for macOS"""

    base_icon = create_icon()

    # Icon sizes for macOS
    sizes = [16, 32, 64, 128, 256, 512, 1024]

    # Create icons directory
    if not os.path.exists("icons"):
        os.makedirs("icons")

    for size in sizes:
        # Resize image with high quality
        resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)

        # Save as PNG
        filename = f"icons/graph_canvas_{size}x{size}.png"
        resized.save(filename, "PNG")
        print(f"Created {filename}")

    # Save the main icon
    base_icon.save("icons/graph_canvas.png", "PNG")
    print("Created icons/graph_canvas.png")

    # Create ICO file for cross-platform compatibility
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128),
                 (256, 256)]
    ico_images = []

    for size in ico_sizes:
        resized = base_icon.resize(size, Image.Resampling.LANCZOS)
        ico_images.append(resized)

    # Save as ICO
    ico_images[0].save("icons/graph_canvas.ico", format="ICO", sizes=ico_sizes)
    print("Created icons/graph_canvas.ico")

    print("\nIcon set created successfully!")
    print("For macOS app bundle, use the PNG files.")
    print("For cross-platform compatibility, use the ICO file.")


if __name__ == "__main__":
    create_icon_set()
