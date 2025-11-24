#!/usr/bin/env python3
"""
Test just the color dialog functionality
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import wx

class ColorTestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Color Dialog Test")
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        btn1 = wx.Button(panel, label="Test Color Dialog")
        btn1.Bind(wx.EVT_BUTTON, self.on_color_test)
        
        sizer.Add(btn1, 0, wx.ALL, 10)
        panel.SetSizer(sizer)
        
        self.Show()
    
    def on_color_test(self, event):
        print("Testing color dialog...")
        
        color_data = wx.ColourData()
        color_data.SetColour(wx.Colour(255, 255, 0))  # Yellow
        
        dialog = wx.ColourDialog(self, color_data)
        dialog.CentreOnParent()
        
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            print(f"Selected color: R={color.Red()}, G={color.Green()}, B={color.Blue()}")
        else:
            print("Color dialog was cancelled")
            
        dialog.Destroy()

class ColorTestApp(wx.App):
    def OnInit(self):
        frame = ColorTestFrame()
        return True

if __name__ == "__main__":
    app = ColorTestApp()
    app.MainLoop()
