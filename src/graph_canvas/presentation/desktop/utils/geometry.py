"""
Geometry utility functions for the graph editor.
"""


import math
from typing import List, Tuple, Optional


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate the Euclidean distance between two points."""

    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def angle(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate the angle from p1 to p2 in radians."""

    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])


def normalize_vector(vector: Tuple[float, float]) -> Tuple[float, float]:
    """Normalize a 2D vector to unit length."""

    x, y = vector
    length = math.sqrt(x * x + y * y)
    if length == 0:
        return (0, 0)
    return (x / length, y / length)


def rotate_point(
    point: Tuple[float, float],
    angle: float,
    center: Tuple[float, float] = (0, 0)) -> Tuple[float, float]:
    """Rotate a point around a center by the given angle in radians."""

    x, y = point
    cx, cy = center

    # Translate to origin
    x -= cx
    y -= cy

    # Rotate
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a

    # Translate back
    new_x += cx
    new_y += cy

    return (new_x, new_y)


def point_in_polygon(point: Tuple[float, float],
                     polygon: List[Tuple[float, float]]) -> bool:
    """Check if a point is inside a polygon using ray casting algorithm."""

    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def convex_hull(
        points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Calculate the convex hull of a set of points using Graham scan."""

    if len(points) < 3:
        return points

    # Find the bottom-most point (and left-most in case of tie)
    start = min(points, key=lambda p: (p[1], p[0]))

    # Sort points by polar angle with respect to start point
    def polar_angle(p):
        return math.atan2(p[1] - start[1], p[0] - start[0])

    sorted_points = sorted([p for p in points if p != start], key=polar_angle)

    # Build the hull
    hull = [start]

    for p in sorted_points:
        # Remove points that would create a clockwise turn
        while len(hull) > 1 and cross_product(hull[-2], hull[-1], p) <= 0:
            hull.pop()
        hull.append(p)

    return hull


def cross_product(o: Tuple[float, float], a: Tuple[float, float],
                  b: Tuple[float, float]) -> float:
    """Calculate the cross product of vectors OA and OB."""

    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def bounding_box(
        points: List[Tuple[float,
                           float]]) -> Tuple[float, float, float, float]:
    """Calculate the bounding box of a set of points."""

    if not points:
        return (0, 0, 0, 0)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    return (min(xs), min(ys), max(xs), max(ys))


def line_intersection(
    line1: Tuple[Tuple[float, float],
                 Tuple[float, float]], line2: Tuple[Tuple[float, float],
                                                    Tuple[float, float]]
) -> Optional[Tuple[float, float]]:
    """Find the intersection point of two lines."""

    (x1, y1), (x2, y2) = line1
    (x3, y3), (x4, y4) = line2

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None  # Lines are parallel

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom

    intersection_x = x1 + t * (x2 - x1)
    intersection_y = y1 + t * (y2 - y1)

    return (intersection_x, intersection_y)


def point_to_line_distance(point: Tuple[float, float],
                           line_start: Tuple[float, float],
                           line_end: Tuple[float, float]) -> float:
    """Calculate the distance from a point to a line segment."""

    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end

    # Calculate line length squared
    line_length_sq = (x2 - x1)**2 + (y2 - y1)**2

    if line_length_sq == 0:
        # Point case
        return distance(point, line_start)

    # Calculate projection parameter
    t = max(
        0,
        min(1,
            ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))

    # Calculate projection point
    projection_x = x1 + t * (x2 - x1)
    projection_y = y1 + t * (y2 - y1)

    # Return distance to projection
    return distance(point, (projection_x, projection_y))


def bezier_curve(control_points: List[Tuple[float, float]],
                 t: float) -> Tuple[float, float]:
    """Calculate a point on a Bezier curve at parameter t (0 to 1)."""

    if not control_points:
        return (0, 0)

    if len(control_points) == 1:
        return control_points[0]

    # De Casteljau's algorithm
    points = list(control_points)

    while len(points) > 1:
        new_points = []
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            new_x = x1 + t * (x2 - x1)
            new_y = y1 + t * (y2 - y1)
            new_points.append((new_x, new_y))

        points = new_points

    return points[0]


def circle_line_intersection(
        center: Tuple[float, float], radius: float, line_start: Tuple[float,
                                                                      float],
        line_end: Tuple[float, float]) -> List[Tuple[float, float]]:
    """Find intersection points between a circle and a line segment."""

    cx, cy = center
    x1, y1 = line_start
    x2, y2 = line_end

    # Vector from line start to line end
    dx = x2 - x1
    dy = y2 - y1

    # Vector from line start to circle center
    fx = x1 - cx
    fy = y1 - cy

    # Quadratic equation coefficients
    a = dx * dx + dy * dy
    b = 2 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - radius * radius

    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        return []  # No intersection

    discriminant = math.sqrt(discriminant)

    t1 = (-b - discriminant) / (2 * a)
    t2 = (-b + discriminant) / (2 * a)

    intersections = []

    # Check if intersections are within the line segment
    for t in [t1, t2]:
        if 0 <= t <= 1:
            x = x1 + t * dx
            y = y1 + t * dy
            intersections.append((x, y))

    return intersections
