import wx
import wx.lib.plot as plot
import wx.lib.ogl as ogl
import json
from collections.abc import Sequence
from itertools import chain, count

CNTRYJSON = "./data/countries.json"

def flatten_nested_arr(l):
    # Flatten nested arrays of any depth
    # Treats arrays like a tree
    flat_arr = []
    for i in range(len(l)):
        # Move down the tree
        if isinstance(l[i], list):
            # Naive concat
            flat_arr += flatten_nested_arr(l[i])
        # Move to the next branch
        else:
            flat_arr.append(l[i])
    return flat_arr

def get_country(path):
    with open(path) as f:
        data = json.load(f)

    return data

def create_coors(flat_arr):
    result = []
    for i in range(1, len(flat_arr), 2):
        result.append([flat_arr[i - 1], flat_arr[i]])

    return result

class mainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='ProjPicker')
        panel = wx.Panel(self)

        # Add left size for layout
        main = wx.BoxSizer(wx.HORIZONTAL)
        left = wx.BoxSizer(wx.VERTICAL)
        right = wx.BoxSizer(wx.VERTICAL)

        #################################
        # LEFT
        st = wx.StaticText(panel, -1, "CRS List", pos=(0,0))
        left.Add(st, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

        # CRS Choice listbox
        lbox = wx.ListBox(panel,
                id=1,
                size=(300, 600),
                choices=['test1', 'test2'],
                )

        # Add CRS listbox to main left side
        left.Add(lbox, 1, wx.ALIGN_RIGHT| wx.ALL | wx.BOTTOM, 0)
        # Create bottom left sizer for buttons
        btm_left = wx.BoxSizer(wx.HORIZONTAL)
        # Ok button
        btn_ok = wx.Button(panel, label='Ok')
        # Cancel button
        btn_cancel = wx.Button(panel, label='Cancel')
        # Add buttons to bottom left
        btm_left.Add(btn_ok, 30, wx.LEFT | wx.RIGHT, 30)
        btm_left.Add(btn_cancel, 30, wx.LEFT | wx.RIGHT, 30)
        left.Add(btm_left, 0, wx.BOTTOM)

        # Add bottom left sizer to left side sizer
        main.Add(left, 0, wx.ALIGN_LEFT | wx.LEFT, 5)

        #################################
        # RIGHT

        # CRS INFO
        # Set static box
        crs_info_box = wx.StaticBox(panel, -1, "CRS Info")
        # Create sizer for the box
        crs_info_sizer = wx.StaticBoxSizer(crs_info_box, wx.VERTICAL)
        # Input text
        crs_info_text = wx.StaticText(panel, -1, "TEST\ntest1", style=wx.ALIGN_RIGHT)
        # Add text to correct sizer
        crs_info_sizer.Add(crs_info_text, 1, wx.EXPAND | wx.ALL | wx.CENTER, 200)
        # Create border
        # https://www.blog.pythonlibrary.org/2019/05/09/an-intro-to-staticbox-and-staticboxsizers/
        border = wx.BoxSizer()
        border.Add(crs_info_sizer, 1, wx.EXPAND | wx.ALL | wx.CENTER, 25)
        # Add to right column
        right.Add(border, 1, wx.ALIGN_RIGHT, 0)

        # CANVAS
        canvas = ogl.ShapeCanvas(panel)

        # test data
        c_json = get_country(CNTRYJSON)
        line = []
        for i in range(len(c_json['features'])):
            coors = c_json['features'][i]['geometry']['coordinates']
            flat_coors = flatten_nested_arr(coors)
            data = create_coors(flat_coors)
            #shape = ogl.PolygonShape()

            #line.append(plot.PolyLine(data, legend='', colour='pink', width=2))

        #gc = plot.PlotGraphics(line)
        #canvas.Draw(gc, xAxis=(-180,180), yAxis=(-90,90))

        # Create sizer for the box

        # Create border
        # https://www.blog.pythonlibrary.org/2019/05/09/an-intro-to-staticbox-and-staticboxsizers/
        right.Add(canvas, 1, wx.EXPAND | wx.ALL, 5)

        # Add right to main
        main.Add(right, wx.ALIGN_RIGHT)
        # Set sizer for main container
        panel.SetSizer(main)

        # Set size of window last otherwise sizers wont work.
        size = wx.Size(800, 800)
        self.SetSize(size)

        self.Show()


if __name__ == '__main__':
    app = wx.App()
    frame = mainFrame()
    app.MainLoop()
