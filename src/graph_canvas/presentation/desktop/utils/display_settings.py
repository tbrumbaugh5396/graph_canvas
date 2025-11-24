"""
Display settings container for UI-related preferences like checkerboard.
"""


import wx


class DisplaySettings:
    def __init__(self):

        # Background color
        self.background_color = wx.Colour(255, 255, 255)
        self.status_panel_background_color = wx.Colour(245, 245, 245)
        
        # Checkerboard visibility toggle
        self.checkerboard_background = False
        # Checkerboard colors
        self.checkerboard_color1 = wx.Colour(240, 240, 240)
        self.checkerboard_color2 = wx.Colour(180, 180, 180)

        # Common control colors
        self.button_background_color = wx.Colour(240, 240, 240)
        self.button_text_color = wx.Colour(0, 0, 0)
        self.label_text_color = wx.Colour(0, 0, 0)
        self.control_background_color = wx.Colour(255, 255, 255)

        # Fonts and sizing
        self.default_label_font_point_size = 9
        self.bold_label_font_point_size = 10
        self.spin_ctrl_font_point_size = 12
        self.small_button_font_point_size = 10

        # Spin control colors
        self.spin_ctrl_text_color = wx.Colour(0, 0, 0)
        self.spin_ctrl_background_color = wx.Colour(255, 255, 255)

