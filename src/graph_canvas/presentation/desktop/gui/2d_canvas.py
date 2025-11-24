import wx
import wx.glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

class Canvas2D(wx.glcanvas.GLCanvas):
    def __init__(self, parent):
        """Initialize the canvas."""
        super().__init__(parent, attribList=[wx.glcanvas.WX_GL_RGBA,
                                           wx.glcanvas.WX_GL_DOUBLEBUFFER,
                                           wx.glcanvas.WX_GL_DEPTH_SIZE, 24])
        
        self.context = wx.glcanvas.GLContext(self)
        self.SetMinSize((300, 300))
        
        # Initialize variables
        self.projection_vector = np.array([0.0, 0.0, 1.0])  # Default looking direction
        self.view_matrix = np.identity(4)
        
        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        
        # Initialize OpenGL
        self.init_gl()
    
    def init_gl(self):
        """Initialize OpenGL settings."""
        self.SetCurrent(self.context)
        
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Set clear color to white
        glClearColor(1.0, 1.0, 1.0, 1.0)
        
        self.setup_viewport()
    
    def setup_viewport(self):
        """Set up the viewport and projection matrix."""
        size = self.GetClientSize()
        glViewport(0, 0, size.width, size.height)
        
        # Set up orthographic projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = size.width / size.height if size.height != 0 else 1
        glOrtho(-2.0 * aspect, 2.0 * aspect, -2.0, 2.0, -10.0, 10.0)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def update_projection(self, vector, view_matrix):
        """Update the projection based on the sphere's view vector."""
        self.projection_vector = vector
        self.view_matrix = view_matrix
        self.Refresh()
    
    def draw_grid(self):
        """Draw a reference grid."""
        glColor3f(0.8, 0.8, 0.8)
        glBegin(GL_LINES)
        
        # Draw horizontal lines
        for i in range(-10, 11):
            glVertex3f(-10.0, i/5.0, 0.0)
            glVertex3f(10.0, i/5.0, 0.0)
        
        # Draw vertical lines
        for i in range(-10, 11):
            glVertex3f(i/5.0, -10.0, 0.0)
            glVertex3f(i/5.0, 10.0, 0.0)
        
        glEnd()
    
    def draw_axes(self):
        """Draw coordinate axes."""
        glBegin(GL_LINES)
        
        # X axis (red)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(1.0, 0.0, 0.0)
        
        # Y axis (green)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        
        glEnd()
    
    def draw_projection(self):
        """Draw the projected view from the sphere."""
        # Transform the projection vector using the view matrix
        transformed_vector = np.dot(self.view_matrix[:3, :3], self.projection_vector)
        
        # Draw the projection point
        glPointSize(5.0)
        glColor3f(0.0, 0.0, 1.0)
        glBegin(GL_POINTS)
        glVertex2f(transformed_vector[0], transformed_vector[1])
        glEnd()
        
        # Draw a direction indicator
        glColor3f(0.0, 0.0, 0.8)
        glBegin(GL_LINES)
        glVertex2f(0.0, 0.0)
        glVertex2f(transformed_vector[0], transformed_vector[1])
        glEnd()
    
    def on_paint(self, event):
        """Handle paint events."""
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glLoadIdentity()
        
        # Draw scene elements
        self.draw_grid()
        self.draw_axes()
        self.draw_projection()
        
        self.SwapBuffers()
    
    def on_size(self, event):
        """Handle resize events."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)
        self.setup_viewport()
        self.Refresh()
        event.Skip()

